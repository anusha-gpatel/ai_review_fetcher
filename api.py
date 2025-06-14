
# http://localhost:8000/docs

from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
from typing import List, Literal
import pandas as pd
import os
import openreview
from src.fetch_data import ICLRDataCollector

app = FastAPI()
collector = ICLRDataCollector()

class YearRequest(BaseModel):
    years: List[int]

@app.get("/")
def read_root():
    return {"message": "ICLR Collector API is running!"}

@app.get("/fetch/{year}/{filter_type}")
def fetch_filtered(
    year: int,
    filter_type: Literal["oral", "spotlight", "poster", "submitted", "reject", "withdrawn"]
):
    try:
        notes = collector.fetch_filtered_notes(filter_type=filter_type, year=year)
        collector.save_filtered_papers_csv(notes, year, filter_type)
        return {
            "status": "success",
            "year": year,
            "filter_type": filter_type,
            "note_count": len(notes),
            "file_saved": f"output/ICLR_{year}_{filter_type}_papers.csv"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/collect_filtered/")
def collect_filtered(request: YearRequest, filter_type: str = "oral"):
    results = {}
    for year in request.years:
        data = collector.collect_filtered(year, filter_type)
        results[year] = len(data)
    return {"status": "success", "counts": results}




@app.post("/collect/")
def collect_data(request: YearRequest):
    all_papers_info = []
    all_reviews_info = []

    for year in request.years:
        venue = f"ICLR.cc/{year}/Conference"
        print(f"\n🔍 Collecting data for year {year}")
        papers = collector.get_conference_papers(venue, year)

        papers_data = []
        reviews_data = []

        for paper in papers:
            paper_info = collector.extract_paper_info(paper, year, venue)
            review_info = collector.extract_reviews(paper, year, venue)

            papers_data.append(paper_info)
            reviews_data.extend(review_info)

            all_papers_info.append({
                "paper_id": paper_info["paper_id"],
                "title": paper_info["title"]
            })

        os.makedirs("output", exist_ok=True)
        pd.DataFrame(papers_data).to_csv(f"output/ICLR_{year}_papers.csv", index=False)
        pd.DataFrame(reviews_data).to_csv(f"output/ICLR_{year}_reviews.csv", index=False)
        print(f"✅ Saved CSVs for ICLR {year}")

    return {
        "status": "success",
        "total_papers": len(all_papers_info),
        "papers": all_papers_info
    }

