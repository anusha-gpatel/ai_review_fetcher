# AI Review Fetcher

This project fetches papers, reviews and author profiles from ICLR conferences using the OpenReview API(https://openreview.net).

It also collects author demographic details such as position, institution, affiliation, career history, advisors, and expertise, and saves them in CSV format.

---

## Setup

1.Clone the repository

```
git clone https://github.com/your-username/ai-review-fetcher.git
cd ai-review-fetcher
```

2.Install dependencies
```
pip install -r requirements.txt
```

3. Running via CLI
```
python main.py
```

4.Running as API (FastAPI)
```
uvicorn api:app --reload
```

5. Testing the API
POST /collect
Collects data for specified years.
```
 POST http://127.0.0.1:8000/collect
Content-Type: application/json

{
  "years": [2022, 2023]
}
```

Response Example:
```
json

{
  "papers": [
    {
      "paper_id": "abc123",
      "title": "A Deep Learning Approach to Something"
    },
    ...
  ],
  "total_papers": 200
}
```

6. Fetch Author Profiles : This API fetches author profiles using fetch_authors (asynchronous):

Author profiles include:
1. Name
2. Affiliation
3. Position(s) and Institution(s) (saved in separate rows for multiple entries)
4. Career history
5. Advisors and relations
6. Expertise areas
7. Personal links

#### Profiles are fetched asynchronously using aiohttp for efficiency.
#### All demographic details are saved automatically to the output folder as a CSV: output/ICLR_author_profiles.csv


Each row contains:
```
| author_id | name | affiliation | position | institution | timeframe | advisors | expertise | personal_links | joined_date |
```
Multiple positions/institutions for a single author appear as separate rows in the CSV.

Advisors and expertise are aggregated as semicolon-separated strings per author.



## Project Structure
```
├── api.py                 # FastAPI application
├── src/
│   └── fetch_data.py      # OpenReview data collector class
├── output/                # Folder for CSV outputs
├── requirements.txt       #Libraries
└── README.md
```
