"""Client for the university dataset used by UniFinder."""

import requests

API_URLS = (
    "https://universities.hipolabs.com/search",
    "https://raw.githubusercontent.com/Hipo/university-domains-list/master/world_universities_and_domains.json",
)


class UniversityAPIError(Exception):
    """Raised when the university data provider cannot return valid data."""


def _matches_filters(university: dict, name: str, country: str) -> bool:
    if country and university.get("country", "").lower() != country.lower():
        return False
    if name:
        name_query = name.lower()
        university_name = str(university.get("name", "")).lower()
        if name_query not in university_name:
            return False
    return True


def _fetch_from_url(url: str, params: dict | None = None) -> list[dict]:
    response = requests.get(url, params=params or {}, timeout=12)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, list) or any(not isinstance(item, dict) for item in data):
        raise UniversityAPIError(
            "The university data service returned data in an unexpected format."
        )
    return data


def fetch_universities(name: str = "", country: str = "") -> list[dict]:
    """Fetch universities matching a name and/or country from the live dataset."""
    params = {}
    if name:
        params["name"] = name
    if country:
        params["country"] = country

    last_error = None
    for url in API_URLS:
        try:
            data = _fetch_from_url(url, params if url.endswith("/search") else None)
            if not url.endswith("/search"):
                data = [
                    university for university in data if _matches_filters(university, name, country)
                ]
            return data
        except ValueError as error:
            last_error = UniversityAPIError(
                "The university data service returned an unreadable response."
            )
        except requests.RequestException as error:
            last_error = UniversityAPIError(
                "The live university data service could not be reached. Please try again."
            )

    if isinstance(last_error, UniversityAPIError):
        raise last_error
    raise UniversityAPIError(
        "The live university data service could not be reached. Please try again."
    )


def compare_countries(countries: list[str]) -> list[dict]:
    """Return live university counts for each requested country."""
    return [
        {"country": country, "total": len(fetch_universities(country=country))}
        for country in countries
    ]
