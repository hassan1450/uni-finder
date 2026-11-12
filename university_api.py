"""Client for the open Hipolabs Universities API."""

import requests

API_URL = "https://universities.hipolabs.com/search"


class UniversityAPIError(Exception):
    """Raised when the university data provider cannot return valid data."""


def fetch_universities(name: str = "", country: str = "") -> list[dict]:
    """Fetch universities matching a name and/or country from the live API."""
    params = {}
    if name:
        params["name"] = name
    if country:
        params["country"] = country

    try:
        response = requests.get(API_URL, params=params, timeout=12)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as error:
        raise UniversityAPIError(
            "The live university data service could not be reached. Please try again."
        ) from error
    except ValueError as error:
        raise UniversityAPIError(
            "The university data service returned an unreadable response."
        ) from error

    if not isinstance(data, list) or any(not isinstance(item, dict) for item in data):
        raise UniversityAPIError(
            "The university data service returned data in an unexpected format."
        )
    return data


def compare_countries(countries: list[str]) -> list[dict]:
    """Return live university counts for each requested country."""
    return [
        {"country": country, "total": len(fetch_universities(country=country))}
        for country in countries
    ]
