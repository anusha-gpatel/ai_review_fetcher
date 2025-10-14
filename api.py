from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Literal
import pandas as pd
import os
from bs4 import BeautifulSoup
from src.fetch_data import ICLRDataCollector
import asyncio

app = FastAPI(title="ICLR Data Collector API")
collector = ICLRDataCollector()


class YearRequest(BaseModel):
    years: List[int]


class AuthorProfileRequest(BaseModel):
    emails: List[str]


@app.get("/fetch/{year}/{filter_type}", tags=["Fetch Papers by Year and Type"])
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


@app.post("/collect_filtered/", tags=["Fetch Papers by Type"])
def collect_filtered(request: YearRequest, filter_type: str = "oral"):
    results = {}
    for year in request.years:
        data = collector.collect_filtered(year, filter_type)
        results[year] = len(data)
    return {"status": "success", "counts": results}


# To Collect papers only
@app.post("/collect_data/", tags=["Fetch Papers and Reviews Year Wise"])
def collect_data(request: YearRequest):
    all_papers_info = []
    all_reviews_info = []
    for year in request.years:
        venue = f"ICLR.cc/{year}/Conference"
        print(f"\nCollecting data for year {year}")
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
        papers_file = f"output/ICLR_{year}_papers.csv"
        reviews_file = f"output/ICLR_{year}_reviews.csv"
        pd.DataFrame(papers_data).to_csv(papers_file, index=False)
        pd.DataFrame(reviews_data).to_csv(reviews_file, index=False)
        print(f"Saved CSVs for ICLR {year}")

    return {
        "status": "success",
        "total_papers": len(all_papers_info),
        "papers": all_papers_info,
        "papers_file": papers_file,
        "reviews_file": reviews_file
    }


#To Collect papers and author profiles YEAR Wise
async def fetch_author_profile(session, author_id):
    url = f"https://openreview.net/profile?id={author_id}"
    try:
        async with session.get(url) as resp:
            if resp.status != 200:
                print(f"Profile page not found for {author_id}")
                return {"author_id": author_id}

            text = await resp.text()
            soup = BeautifulSoup(text, "html.parser")

            # --- Extract General Info ---
            profile_header = soup.find('div', class_='title-container')
            name = profile_header.find('h1').text.strip() if profile_header and profile_header.find('h1') else ''
            affiliation = profile_header.find('h3').text.strip() if profile_header and profile_header.find('h3') else ''

            # --- Personal Links Section ---
            links = {}
            links_section = soup.find('section', class_='links')
            if links_section:
                link_elements = links_section.find_all('a', href=True)
                for a in link_elements:
                    link_text = a.text.strip().lower().replace(" ", "_")
                    links[link_text] = a['href']

            # --- Career & Education History Section ---
            career_education_history = []
            history_section = soup.find('section', class_='history')
            if history_section:
                for row in history_section.find_all('div', class_='table-row'):
                    position = row.find('div', class_='position')
                    institution = row.find('div', class_='institution')
                    timeframe = row.find('div', class_='timeframe')
                    career_education_history.append({
                        "position": position.text.strip() if position else '',
                        "institution": institution.text.strip() if institution else '',
                        "timeframe": timeframe.text.strip().replace('–', '-') if timeframe else ''
                    })

            # --- Advisors, Relations & Conflicts Section ---
            advisors_relations = []
            relations_section = soup.find('section', class_='relations')
            if relations_section:
                for row in relations_section.find_all('div', class_='table-row'):
                    children = row.find_all('div')
                    if len(children) >= 4:
                        relation_type = children[0].text.strip()
                        related_person = children[1].text.strip()
                        timeframe = children[3].text.strip().replace('–', '-')
                        advisors_relations.append({
                            "type": relation_type,
                            "name": related_person,
                            "timeframe": timeframe
                        })

            # --- Expertise Section ---
            expertise_areas = []
            expertise_section = soup.find('section', class_='expertise')
            if expertise_section:
                for row in expertise_section.find_all('div', class_='table-row'):
                    children = row.find_all('div')
                    if len(children) >= 2:
                        area = children[0].text.strip()
                        timeframe = children[1].text.strip().replace('–', '-')
                        expertise_areas.append({
                            "area": area,
                            "timeframe": timeframe
                        })

            return {
                "author_id": author_id,
                "name": name,
                "affiliation": affiliation,
                "joined_date": soup.find('span', class_='glyphicon-calendar').next_sibling.next_sibling.strip() if soup.find('span', class_='glyphicon-calendar') else None,
                "personal_links": links,
                "career_and_education_history": career_education_history,  # keep as list
                "advisors": advisors_relations,
                "expertise": expertise_areas
            }

    except Exception as e:
        print(f"Error fetching {author_id}: {e}")
        return {"author_id": author_id, "error": str(e)}



@app.post("/collect_data_with_authors/", tags=["Fetch Authors and Papers Year Wise"])
def collect_data_with_authors(request: YearRequest):
    all_papers_info = []
    all_author_ids = set()
    papers_file = reviews_file = authors_file = None

    for year in request.years:
        venue = f"ICLR.cc/{year}/Conference"
        print(f"\nCollecting data for year {year}")
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

            if "author_ids" in paper_info and paper_info["author_ids"]:
                for aid in str(paper_info["author_ids"]).split(","):
                    all_author_ids.add(aid.strip())

        os.makedirs("output", exist_ok=True)
        papers_file = f"output/ICLR_{year}_papers.csv"
        reviews_file = f"output/ICLR_{year}_reviews.csv"
        pd.DataFrame(papers_data).to_csv(papers_file, index=False)
        pd.DataFrame(reviews_data).to_csv(reviews_file, index=False)
        print(f"Saved CSVs for ICLR {year}")

    # --- Fetch all author profiles asynchronously ---
    if all_author_ids:
        authors_file = f"output/ICLR_author_profiles.csv"
        profiles = asyncio.run(fetch_all_author_profiles(list(all_author_ids)))

        flattened_profiles = []
        for p in profiles:
            career_roles = []
            institutions = []
            timeframes = []
            for entry in p.get("career_and_education_history", []):
                career_roles.append(entry.get("position", ""))
                institutions.append(entry.get("institution", ""))
                timeframes.append(entry.get("timeframe", ""))

            positions_str = "; ".join(career_roles)
            institutions_str = "; ".join(institutions)
            timeframes_str = "; ".join(timeframes)

            links_str = ", ".join([f"{k}: {v}" for k, v in p.get("personal_links", {}).items() if v])
            advisors_str = "; ".join([
                f"{a.get('type', '')}: {a.get('name', '')} ({a.get('timeframe', '')})" for a in p.get("advisors", [])
            ])
            expertise_str = "; ".join([
                f"{e.get('area', '')} ({e.get('timeframe', '')})" for e in p.get("expertise", [])
            ])

            flat_p = {
                "author_id": p.get("author_id", ""),
                "name": p.get("name", ""),
                "preferred_name": p.get("preferred_name", ""),
                "career_roles": positions_str,
                "institutions": institutions_str,
                "timeframes": timeframes_str,
                "advisors": advisors_str,
                "affiliation": p.get("affiliation", ""),
                "joined_date": p.get("joined_date", ""),
                "personal_links": links_str,
                "expertise": expertise_str
            }
            flattened_profiles.append(flat_p)

        df = pd.DataFrame(flattened_profiles)
        df.to_csv(authors_file, index=False, encoding='utf-8')
        print(f"Saved all author details to {authors_file}")

    else:
        print("No author IDs found, skipping author profile fetch.")

    return {
        "status": "success",
        "total_papers": len(all_papers_info),
        "author_count": len(all_author_ids),
        "papers_file": papers_file,
        "reviews_file": reviews_file,
        "author_profiles_file": authors_file
    }
