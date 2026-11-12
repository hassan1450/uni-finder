import unittest
from unittest.mock import Mock, patch

from requests import Timeout

from app import app
from university_api import UniversityAPIError, fetch_universities


SAMPLE_UNIVERSITY = {
    "name": "University of Toronto",
    "country": "Canada",
    "web_pages": ["https://www.utoronto.ca/"],
    "domains": ["utoronto.ca"],
}


class UniversityAppTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_homepage_renders_search_and_comparison(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Find your", response.data)
        self.assertIn(b"Compare countries", response.data)

    def test_search_requires_a_name_or_country(self):
        response = self.client.get("/api/search")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json["success"])

    @patch("app.fetch_universities", return_value=[SAMPLE_UNIVERSITY])
    def test_search_returns_live_university_records(self, fetch):
        response = self.client.get("/api/search?name=Toronto&country=Canada")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["total"], 1)
        self.assertEqual(response.json["universities"][0]["name"], "University of Toronto")
        fetch.assert_called_once_with(name="Toronto", country="Canada")

    @patch("app.fetch_universities", side_effect=UniversityAPIError("The live service is unavailable."))
    def test_upstream_errors_are_reported(self, _fetch):
        response = self.client.get("/api/search?country=Canada")
        self.assertEqual(response.status_code, 502)
        self.assertIn("unavailable", response.json["message"])

    def test_comparison_rejects_duplicate_or_unknown_countries(self):
        duplicate = self.client.post(
            "/api/compare", json={"countries": ["Canada", "Canada"]}
        )
        unknown = self.client.post(
            "/api/compare", json={"countries": ["Canada", "Narnia"]}
        )
        self.assertEqual(duplicate.status_code, 400)
        self.assertEqual(unknown.status_code, 400)

    @patch(
        "app.compare_countries",
        return_value=[
            {"country": "Canada", "total": 20},
            {"country": "Australia", "total": 15},
        ],
    )
    def test_comparison_returns_country_counts(self, compare):
        response = self.client.post(
            "/api/compare", json={"countries": ["Canada", "Australia"]}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json["results"]), 2)
        compare.assert_called_once_with(["Canada", "Australia"])

    @patch("app.fetch_universities", return_value=[SAMPLE_UNIVERSITY])
    def test_csv_export_includes_university_details(self, _fetch):
        response = self.client.get("/api/export?country=Canada&type=csv")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"University of Toronto", response.data)
        self.assertIn(b"utoronto.ca", response.data)
        self.assertIn("attachment", response.headers["Content-Disposition"])

    @patch("university_api.requests.get")
    def test_api_client_sends_search_parameters_and_timeout(self, get):
        response = Mock()
        response.json.return_value = [SAMPLE_UNIVERSITY]
        get.return_value = response
        universities = fetch_universities(name="Toronto", country="Canada")
        self.assertEqual(universities, [SAMPLE_UNIVERSITY])
        response.raise_for_status.assert_called_once_with()
        get.assert_called_once_with(
            "https://universities.hipolabs.com/search",
            params={"name": "Toronto", "country": "Canada"},
            timeout=12,
        )

    @patch("university_api.requests.get", side_effect=Timeout)
    def test_api_client_reports_network_failures(self, _get):
        with self.assertRaisesRegex(UniversityAPIError, "could not be reached"):
            fetch_universities(country="Canada")


if __name__ == "__main__":
    unittest.main()
