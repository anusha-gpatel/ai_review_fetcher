# AI Review Fetcher

This project fetches papers and reviews from ICLR conferences using the [OpenReview API](https://openreview.net). It supports both a CLI-based script and a REST API built with FastAPI.

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

## Project Structure
```
├── api.py                 # FastAPI application
├── main.py                # CLI script
├── src/
│   └── fetch_data.py      # OpenReview data collector class
├── output/                # Folder for CSV outputs
├── requirements.txt
└── README.md
```
