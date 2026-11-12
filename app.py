"""Flask application for UniFinder."""

import csv
import io
import json

from flask import Flask, Response, jsonify, render_template, request

from university_api import UniversityAPIError, compare_countries, fetch_universities

app = Flask(__name__)

COUNTRIES = [
    "Australia",
    "Brazil",
    "Canada",
    "China",
    "France",
    "Germany",
    "India",
    "Italy",
    "Japan",
    "Malaysia",
    "Netherlands",
    "New Zealand",
    "Pakistan",
    "Saudi Arabia",
    "Singapore",
    "South Korea",
    "Spain",
    "Sweden",
    "Turkey",
    "United Arab Emirates",
    "United Kingdom",
    "United States",
]


def _search_parameters():
    name = request.args.get("name", "").strip()
    country = request.args.get("country", "").strip()
    if not name and not country:
        return None, (jsonify(success=False, message="Enter a university name or choose a country."), 400)
    if len(name) > 100 or len(country) > 100:
        return None, (jsonify(success=False, message="Search terms must be 100 characters or fewer."), 400)
    if country and country not in COUNTRIES:
        return None, (jsonify(success=False, message="Choose a country from the list."), 400)
    return (name, country), None


def _api_error(error: UniversityAPIError):
    return jsonify(success=False, message=str(error)), 502


def _csv_values(value):
    if not isinstance(value, list):
        return ""
    return ", ".join(item for item in value if isinstance(item, str) and item)


@app.get("/")
def home():
    return render_template("index.html", countries=COUNTRIES)


@app.get("/api/search")
def search():
    parameters, error_response = _search_parameters()
    if error_response:
        return error_response

    name, country = parameters
    try:
        universities = fetch_universities(name=name, country=country)
    except UniversityAPIError as error:
        return _api_error(error)

    return jsonify(success=True, total=len(universities), universities=universities)


@app.post("/api/compare")
def compare():
    data = request.get_json(silent=True)
    countries = data.get("countries") if isinstance(data, dict) else None
    if (
        not isinstance(countries, list)
        or not 2 <= len(countries) <= 4
        or any(not isinstance(country, str) or country not in COUNTRIES for country in countries)
        or len(set(countries)) != len(countries)
    ):
        return jsonify(
            success=False,
            message="Choose 2–4 different countries from the list.",
        ), 400

    try:
        results = compare_countries(countries)
    except UniversityAPIError as error:
        return _api_error(error)
    return jsonify(success=True, results=results)


@app.get("/api/export")
def export():
    parameters, error_response = _search_parameters()
    if error_response:
        return error_response

    name, country = parameters
    file_type = request.args.get("type", "csv").lower()
    if file_type not in {"csv", "json"}:
        return jsonify(success=False, message="Choose CSV or JSON format."), 400

    try:
        universities = fetch_universities(name=name, country=country)
    except UniversityAPIError as error:
        return _api_error(error)
    if not universities:
        return jsonify(success=False, message="There are no results to export."), 404

    if file_type == "json":
        content = json.dumps(universities, indent=2, ensure_ascii=False)
        mimetype, filename = "application/json", "universities.json"
    else:
        output = io.StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(["University", "Country", "Website", "Domains"])
        for university in universities:
            writer.writerow(
                [
                    university.get("name", ""),
                    university.get("country", ""),
                    _csv_values(university.get("web_pages")),
                    _csv_values(university.get("domains")),
                ]
            )
        content = "\ufeff" + output.getvalue()
        mimetype, filename = "text/csv; charset=utf-8", "universities.csv"

    return Response(
        content,
        mimetype=mimetype,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


if __name__ == "__main__":
    app.run(debug=False)
