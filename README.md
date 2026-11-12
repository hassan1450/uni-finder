# UniFinder

UniFinder is a small Python and Flask website for discovering universities around the world. Search by institution name, browse by country, compare live university counts in up to four countries, and download search results as CSV or JSON.

University information is fetched in real time by Python's `requests` library from the open [Hipolabs university dataset](https://github.com/Hipo/university-domains-list). The app tries the original API endpoint first and falls back to the maintained GitHub mirror if the service is unavailable, so the site keeps working even when one source is down. Search results are not saved or replaced with sample data.

## Features

- Search the live directory by university name, country, or both.
- Compare university counts across two to four countries.
- Download matching results as CSV or JSON.
- Responsive interface for desktop and mobile.

## Requirements

- Python 3.10 or later
- Internet access for live university data

## Install and run

From the project directory, create and activate a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the requirements and start the website:

```powershell
python -m pip install -r requirements.txt
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser. Use `Ctrl+C` in the terminal to stop the server.

## Example

Search for “University of Toronto” and choose “Canada”. The website calls its Flask search endpoint, which requests current matching records from the public API:

```text
GET /api/search?name=University%20of%20Toronto&country=Canada
```

Example response:

```json
{
  "success": true,
  "total": 1,
  "universities": [
    {
      "name": "University of Toronto",
      "country": "Canada",
      "web_pages": ["https://www.utoronto.ca/"],
      "domains": ["utoronto.ca"]
    }
  ]
}
```

The precise matches and totals depend on the live API data. Use the CSV and JSON buttons after a search to download its complete result set.

## API endpoints

| Endpoint | Purpose |
| --- | --- |
| `GET /api/search?name=Oxford&country=United%20Kingdom` | Search universities. Either `name` or `country` is required. |
| `POST /api/compare` | Compare counts for 2–4 different countries. JSON body: `{"countries":["Canada","Australia"]}` |
| `GET /api/export?country=Canada&type=csv` | Download matching data as `csv` or `json`. |

The upstream API is open source and documented in the [Hipolabs university-domains-list repository](https://github.com/Hipo/university-domains-list).

## Run the tests

The test suite uses Python's built-in `unittest` and mocks API responses, so it does not need network access:

```powershell
python -m unittest discover -s tests -v
```
