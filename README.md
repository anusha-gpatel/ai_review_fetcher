# ICLR Data Collector API

This project fetches papers, reviews, and author profiles from ICLR conferences (2017-2026) using the OpenReview API (https://openreview.net).

It collects comprehensive data including:
- **Papers**: Title, abstract, authors, keywords, primary area, PDF links
- **Reviews**: Ratings, confidence, summary, strengths, weaknesses, questions, limitations
- **Author Profiles**: Name, affiliation, positions, institutions, career history, advisors, expertise, personal links

All data is saved in CSV format for easy analysis.

---

## Features

✅ **Unified API** - Works seamlessly across all ICLR years (2017-2026)  
✅ **Dual Format Support** - Handles both old (pre-2024) and new (2024-2026) OpenReview API formats  
✅ **Async Author Fetching** - Fast parallel fetching of author profiles using aiohttp  
✅ **Clean Data Structure** - One row per author with positions as semicolon-separated lists  
✅ **Full Review Text** - Formatted review sections included in CSV output  

---

## Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/iclr-data-collector.git
cd iclr-data-collector
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

**Required Libraries:**
```
fastapi
uvicorn
openreview-py
pandas
aiohttp
beautifulsoup4
pydantic
```

### 3. Run the API
```bash
uvicorn api:app --host 0.0.0.0 --port 8002 --reload
```

The API will be available at: `http://localhost:8002`

Access interactive docs at: `http://localhost:8002/docs`

---

## API Endpoints

The API has **4 main endpoints** divided by year range:

### **For Years 2024-2026** (New OpenReview API v2)

#### 1. Fetch Papers Only
Fetches all papers without reviews or author profiles.

**Endpoint:** `POST /fetch_papers_2024_2026/`

**Request:**
```json
{
  "years": [2024, 2025, 2026]
}
```

**Response:**
```json
{
  "status": "success",
  "results": {
    "2024": {
      "total_papers": 7404,
      "papers_file": "output/ICLR_2024_papers.csv"
    },
    "2025": {
      "total_papers": 8500,
      "papers_file": "output/ICLR_2025_papers.csv"
    }
  }
}
```

**Output Files:**
- `output/ICLR_2024_papers.csv`
- `output/ICLR_2025_papers.csv`

---

#### 2. Fetch Papers + Reviews + Authors
Fetches complete dataset including papers, reviews, and author profiles.

**Endpoint:** `POST /fetch_all_data_2024_2026/`

**Request:**
```json
{
  "years": [2024, 2025, 2026]
}
```

**Response:**
```json
{
  "status": "success",
  "results": {
    "2024": {
      "total_papers": 7404,
      "total_reviews": 29616,
      "papers_file": "output/ICLR_2024_papers.csv",
      "reviews_file": "output/ICLR_2024_reviews.csv"
    },
    "author_profiles": {
      "author_count": 25000,
      "file": "output/ICLR_2024_2026_author_profiles.csv"
    }
  }
}
```

**Output Files:**
- `output/ICLR_2024_papers.csv`
- `output/ICLR_2024_reviews.csv`
- `output/ICLR_2024_2026_author_profiles.csv`

---

### **For Years Before 2024** (OpenReview API v1)

#### 3. Fetch Papers Only
Fetches all papers for pre-2024 years.

**Endpoint:** `POST /fetch_papers_pre_2024/`

**Request:**
```json
{
  "years": [2020, 2021, 2022, 2023]
}
```

**Response:**
```json
{
  "status": "success",
  "results": {
    "2023": {
      "total_papers": 4966,
      "papers_file": "output/ICLR_2023_papers.csv"
    }
  }
}
```

---

#### 4. Fetch Papers + Reviews + Authors
Complete dataset for pre-2024 years.

**Endpoint:** `POST /fetch_all_data_pre_2024/`

**Request:**
```json
{
  "years": [2020, 2021, 2022, 2023]
}
```

**Response:**
```json
{
  "status": "success",
  "results": {
    "2023": {
      "total_papers": 4966,
      "total_reviews": 19864,
      "papers_file": "output/ICLR_2023_papers.csv",
      "reviews_file": "output/ICLR_2023_reviews.csv"
    },
    "author_profiles": {
      "author_count": 15000,
      "file": "output/ICLR_pre_2024_author_profiles.csv"
    }
  }
}
```

---

## CSV Output Structure

### Papers CSV
```
| paper_id | title | abstract | authors | authorids | keywords | primary_area | venue | year | pdf_url | forum_url |
```

### Reviews CSV
```
| review_id | paper_id | year | reviewer | full_review_text | rating | confidence | summary | strengths | weaknesses | questions | limitations | soundness | presentation | contribution | review_date |
```

### Author Profiles CSV
```
| author_id | name | affiliation | joined_date | personal_links | positions | institutions | timeframes | advisors | expertise |
```

**Note:** 
- **One row per author** - Multiple positions are combined as semicolon-separated values
- **Example positions:** `"PhD Student; Postdoc; Assistant Professor"`
- **Example institutions:** `"MIT; Stanford; UC Berkeley"`
- **Example timeframes:** `"2014-2018; 2018-2020; 2020-present"`

---

## Example Usage

### Using curl
```bash
# Fetch papers only for 2024-2025
curl -X POST "http://localhost:8002/fetch_papers_2024_2026/" \
  -H "Content-Type: application/json" \
  -d '{"years": [2024, 2025]}'

# Fetch complete data for 2023
curl -X POST "http://localhost:8002/fetch_all_data_pre_2024/" \
  -H "Content-Type: application/json" \
  -d '{"years": [2023]}'
```

### Using Python
```python
import requests

# Fetch papers + reviews + authors for 2024-2025
response = requests.post(
    "http://localhost:8002/fetch_all_data_2024_2026/",
    json={"years": [2024, 2025]}
)

result = response.json()
print(f"Status: {result['status']}")
print(f"Papers: {result['results']['2024']['total_papers']}")
print(f"Reviews: {result['results']['2024']['total_reviews']}")
```

---

## Project Structure
```
├── api.py                      # Main FastAPI application (4 endpoints)
├── src/
│   └── fetch_data.py          # OpenReview data collector class
├── output/                     # Generated CSV files
│   ├── ICLR_2024_papers.csv
│   ├── ICLR_2024_reviews.csv
│   └── ICLR_2024_2026_author_profiles.csv
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

---

## Key Implementation Details

### Dual API Support
- **Pre-2024**: Uses OpenReview API v1 with `details='replies'`
- **2024-2026**: Uses OpenReview API v2 with `details='directReplies'`

### Author Profile Fetching
- **Asynchronous**: Fetches profiles in parallel using `aiohttp` (50 concurrent connections)
- **Web Scraping**: Extracts data from OpenReview profile pages using BeautifulSoup
- **Robust Parsing**: Handles missing fields gracefully

### Data Aggregation
- **Papers**: Collected per year
- **Reviews**: Aggregated across all papers
- **Authors**: Deduplicated across all years with one row per author

---

## Troubleshooting

### Rate Limiting
If you encounter rate limiting errors:
1. Reduce the number of years in a single request
2. Add delays between requests
3. The API automatically handles retries with exponential backoff

### No Reviews Found
For 2024-2026, ensure you're using the correct endpoint (`/fetch_all_data_2024_2026/`). The new API structure stores reviews in `directReplies`.

### Author Profiles Not Fetching
Check if author IDs are present in papers. Some papers may have anonymous submissions.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.


## Acknowledgments

This project uses the [OpenReview API](https://openreview.net) to fetch conference data.
