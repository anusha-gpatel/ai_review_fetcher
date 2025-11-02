from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import pandas as pd
import os
from fetch_data import ICLRDataCollector
import asyncio
import openreview

app = FastAPI(title="ICLR Data Collector API - Simplified")
collector = ICLRDataCollector()

# Initialize OpenReview API v2 client for 2024-2026
client_v2 = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

class YearRequest(BaseModel):
    years: List[int]


def get_papers_by_invitation(year: int):
    """Fetch ALL papers using OpenReview API v2 for 2024-2026"""
    venue_id = f"ICLR.cc/{year}/Conference"
    invitation = f"{venue_id}/-/Submission"
    
    print(f"Fetching papers for {venue_id}...")
    
    try:
        all_notes = list(client_v2.get_all_notes(
            invitation=invitation,
            details='directReplies'
        ))
        
        print(f"Found {len(all_notes)} total submissions")
        return all_notes
        
    except Exception as e:
        print(f"Error fetching papers: {e}")
        return []


def extract_paper_from_note(note, year: int):
    """Extract paper information from OpenReview note object"""
    content = note.content if hasattr(note, 'content') else {}
    
    def get_value(field):
        val = content.get(field, '')
        if isinstance(val, dict):
            return val.get('value', '')
        return val
    
    def get_list_value(field):
        val = content.get(field, [])
        if isinstance(val, dict):
            return val.get('value', [])
        return val if isinstance(val, list) else []
    
    return {
        'paper_id': note.id,
        'title': get_value('title'),
        'abstract': get_value('abstract'),
        'authors': ", ".join(get_list_value('authors')),
        'authorids': ", ".join(get_list_value('authorids')),
        'keywords': ", ".join(get_list_value('keywords')),
        'primary_area': get_value('primary_area'),
        'venue': get_value('venue'),
        'year': year,
        'pdf_url': f"https://openreview.net/pdf?id={note.id}",
        'forum_url': f"https://openreview.net/forum?id={note.id}",
    }


def get_reviews_from_note(note, year: int):
    """Extract reviews from note's direct replies"""
    reviews = []
    
    if not (hasattr(note, 'details') and 'directReplies' in note.details):
        return reviews
    
    direct_replies = note.details['directReplies']
    
    for reply in direct_replies:
        invitation = reply.get('invitation', '')
        
        if 'Official_Review' in invitation:
            content = reply.get('content', {})
            
            def get_value(field):
                val = content.get(field, '')
                if isinstance(val, dict):
                    return val.get('value', '')
                return val if val else ''
            
            review_sections = {
                'summary': get_value('summary'),
                'strengths': get_value('strengths'),
                'weaknesses': get_value('weaknesses'),
                'questions': get_value('questions'),
                'limitations': get_value('limitations')
            }
            
            full_text = "\n\n".join(
                f"{section.upper()}: {text}"
                for section, text in review_sections.items() if text
            )
            
            reviews.append({
                'review_id': reply.get('id', ''),
                'paper_id': note.id,
                'year': year,
                'reviewer': reply.get('signatures', ['Anonymous'])[0],
                'full_review_text': full_text.strip(),
                'rating': get_value('rating'),
                'confidence': get_value('confidence'),
                'summary': get_value('summary'),
                'strengths': get_value('strengths'),
                'weaknesses': get_value('weaknesses'),
                'questions': get_value('questions'),
                'limitations': get_value('limitations'),
                'soundness': get_value('soundness'),
                'presentation': get_value('presentation'),
                'contribution': get_value('contribution'),
                'review_date': reply.get('cdate', None),
            })
    
    return reviews


# ============================================================================
# Fetch Papers Only for 2024-2026
# ============================================================================
@app.post("/fetch_papers_2024_2026/", tags=["2024-2026"])
def fetch_papers_2024_2026(request: YearRequest):
    """
    Endpoint 1: Fetch ONLY papers for years 2024, 2025, 2026
    """
    results = {}
    
    for year in request.years:
        if year < 2024:
            results[year] = {"error": "Use /fetch_papers_pre_2024/ for years before 2024"}
            continue
        
        print(f"\n{'='*60}")
        print(f"Fetching papers for ICLR {year}")
        print(f"{'='*60}")
        
        notes = get_papers_by_invitation(year)
        
        if not notes:
            results[year] = {"error": f"No papers found for {year}", "total_papers": 0}
            continue
        
        papers_data = [extract_paper_from_note(note, year) for note in notes]
        
        os.makedirs("output", exist_ok=True)
        papers_file = f"output/ICLR_{year}_papers.csv"
        pd.DataFrame(papers_data).to_csv(papers_file, index=False)
        
        print(f"Saved {len(papers_data)} papers to {papers_file}")
        
        results[year] = {
            "total_papers": len(papers_data),
            "papers_file": papers_file
        }
    
    return {"status": "success", "results": results}


# ============================================================================
# Fetch Papers + Reviews + Authors for 2024-2026
# ============================================================================
@app.post("/fetch_all_data_2024_2026/", tags=["2024-2026"])
def fetch_all_data_2024_2026(request: YearRequest):
    """
    Fetch papers + reviews + authors for years 2024, 2025, 2026
    """
    all_author_ids = set()
    results = {}
    
    for year in request.years:
        if year < 2024:
            results[year] = {"error": "Use /fetch_all_data_pre_2024/ for years before 2024"}
            continue
        
        print(f"\n{'='*60}")
        print(f"Fetching papers + reviews + authors for ICLR {year}")
        print(f"{'='*60}")
        
        notes = get_papers_by_invitation(year)
        
        if not notes:
            results[year] = {
                "error": f"No papers found for {year}",
                "total_papers": 0,
                "total_reviews": 0
            }
            continue
        
        papers_data = []
        all_reviews = []
        
        print(f"Processing {len(notes)} submissions...")
        for i, note in enumerate(notes):
            if i % 500 == 0 and i > 0:
                print(f"  Processed {i}/{len(notes)} papers...")
            
            paper = extract_paper_from_note(note, year)
            papers_data.append(paper)
            
            reviews = get_reviews_from_note(note, year)
            all_reviews.extend(reviews)
            
            # Collect author IDs
            if paper.get('authorids'):
                for aid in str(paper['authorids']).split(','):
                    aid = aid.strip()
                    if aid:
                        all_author_ids.add(aid)
        
        # Save papers and reviews
        os.makedirs("output", exist_ok=True)
        papers_file = f"output/ICLR_{year}_papers.csv"
        reviews_file = f"output/ICLR_{year}_reviews.csv"
        
        pd.DataFrame(papers_data).to_csv(papers_file, index=False)
        pd.DataFrame(all_reviews).to_csv(reviews_file, index=False)
        
        print(f"Saved {len(papers_data)} papers to {papers_file}")
        print(f"Saved {len(all_reviews)} reviews to {reviews_file}")
        
        results[year] = {
            "total_papers": len(papers_data),
            "total_reviews": len(all_reviews),
            "papers_file": papers_file,
            "reviews_file": reviews_file
        }
    
    # Fetch author profiles
    if all_author_ids:
        print(f"\n{'='*60}")
        print(f"Fetching profiles for {len(all_author_ids)} unique authors")
        print(f"{'='*60}")
        
        authors_file = f"output/ICLR_2024_2026_author_profiles.csv"
        
        profiles = asyncio.run(collector.fetch_all_author_profiles(list(all_author_ids)))
        
        flattened_profiles = []
        for p in profiles:
            author_id = p.get("author_id", "")
            name = p.get("name", "")
            affiliation = p.get("affiliation", "")
            joined_date = p.get("joined_date", "")
            links_str = ", ".join([f"{k}: {v}" for k, v in p.get("personal_links", {}).items() if v])
            advisors_str = "; ".join([f"{a.get('type', '')}: {a.get('name', '')} ({a.get('timeframe', '')})" for a in p.get("advisors_relations_and_conflicts", [])])
            expertise_str = "; ".join([f"{e.get('area', '')} ({e.get('timeframe', '')})" for e in p.get("expertise", [])])
            
            career_history = p.get("career_and_education_history", [])
            positions = []
            institutions = []
            timeframes = []
            
            for entry in career_history:
                positions.append(entry.get("position", ""))
                institutions.append(entry.get("institution", ""))
                timeframes.append(entry.get("timeframe", ""))
            
            flattened_profiles.append({
                "author_id": author_id,
                "name": name,
                "affiliation": affiliation,
                "joined_date": joined_date,
                "personal_links": links_str,
                "positions": "; ".join(positions) if positions else "",
                "institutions": "; ".join(institutions) if institutions else "",
                "timeframes": "; ".join(timeframes) if timeframes else "",
                "advisors": advisors_str,
                "expertise": expertise_str
            })
        
        df = pd.DataFrame(flattened_profiles)
        df.to_csv(authors_file, index=False, encoding='utf-8')
        print(f"✓ Saved {len(all_author_ids)} author profiles to {authors_file}")
        
        results["author_profiles"] = {
            "author_count": len(all_author_ids),
            "file": authors_file
        }
    
    return {"status": "success", "results": results}


# ============================================================================
# Fetch Papers Only for Pre-2024
# ============================================================================
@app.post("/fetch_papers_pre_2024/", tags=["Pre-2024"])
def fetch_papers_pre_2024(request: YearRequest):
    """
    Fetch ONLY papers for years before 2024

    """
    results = {}
    
    for year in request.years:
        if year >= 2024:
            results[year] = {"error": "Use /fetch_papers_2024_2026/ for years 2024 and later"}
            continue
        
        venue = f"ICLR.cc/{year}/Conference"
        print(f"\n{'='*60}")
        print(f"Fetching papers for ICLR {year}")
        print(f"{'='*60}")
        
        papers = collector.get_conference_papers(venue, year)
        papers_data = []
        
        for paper in papers:
            paper_info = collector.extract_paper_info(paper, year, venue)
            papers_data.append(paper_info)
        
        os.makedirs("output", exist_ok=True)
        papers_file = f"output/ICLR_{year}_papers.csv"
        pd.DataFrame(papers_data).to_csv(papers_file, index=False)
        
        print(f"✓ Saved {len(papers_data)} papers to {papers_file}")
        
        results[year] = {
            "total_papers": len(papers_data),
            "papers_file": papers_file
        }
    
    return {"status": "success", "results": results}


# ============================================================================
#Fetch Papers + Reviews + Authors for Pre-2024
# ============================================================================
@app.post("/fetch_all_data_pre_2024/", tags=["Pre-2024"])
def fetch_all_data_pre_2024(request: YearRequest):
    """
    Fetch papers + reviews + authors for years before 2024
    """
    all_author_ids = set()
    results = {}
    
    for year in request.years:
        if year >= 2024:
            results[year] = {"error": "Use /fetch_all_data_2024_2026/ for years 2024 and later"}
            continue
        
        venue = f"ICLR.cc/{year}/Conference"
        print(f"\n{'='*60}")
        print(f"Fetching papers + reviews + authors for ICLR {year}")
        print(f"{'='*60}")
        
        papers = collector.get_conference_papers(venue, year)
        papers_data = []
        reviews_data = []
        
        for paper in papers:
            paper_info = collector.extract_paper_info(paper, year, venue)
            review_info = collector.extract_reviews(paper, year, venue)
            papers_data.append(paper_info)
            reviews_data.extend(review_info)
            
            # Collect author IDs
            if "author_ids" in paper_info and paper_info["author_ids"]:
                for aid in str(paper_info["author_ids"]).split(","):
                    all_author_ids.add(aid.strip())
        
        os.makedirs("output", exist_ok=True)
        papers_file = f"output/ICLR_{year}_papers.csv"
        reviews_file = f"output/ICLR_{year}_reviews.csv"
        
        pd.DataFrame(papers_data).to_csv(papers_file, index=False)
        pd.DataFrame(reviews_data).to_csv(reviews_file, index=False)
        
        print(f"✓ Saved {len(papers_data)} papers to {papers_file}")
        print(f"✓ Saved {len(reviews_data)} reviews to {reviews_file}")
        
        results[year] = {
            "total_papers": len(papers_data),
            "total_reviews": len(reviews_data),
            "papers_file": papers_file,
            "reviews_file": reviews_file
        }
    
    # Fetch author profiles
    if all_author_ids:
        print(f"\n{'='*60}")
        print(f"Fetching profiles for {len(all_author_ids)} unique authors")
        print(f"{'='*60}")
        
        authors_file = f"output/ICLR_{year}_author_profiles.csv"
        
        profiles = asyncio.run(collector.fetch_all_author_profiles(list(all_author_ids)))
        
        flattened_profiles = []
        for p in profiles:
            author_id = p.get("author_id", "")
            name = p.get("name", "")
            affiliation = p.get("affiliation", "")
            joined_date = p.get("joined_date", "")
            links_str = ", ".join([f"{k}: {v}" for k, v in p.get("personal_links", {}).items() if v])
            advisors_str = "; ".join([f"{a.get('type', '')}: {a.get('name', '')} ({a.get('timeframe', '')})" for a in p.get("advisors_relations_and_conflicts", [])])
            expertise_str = "; ".join([f"{e.get('area', '')} ({e.get('timeframe', '')})" for e in p.get("expertise", [])])
            
            career_history = p.get("career_and_education_history", [])
            positions = []
            institutions = []
            timeframes = []
            
            for entry in career_history:
                positions.append(entry.get("position", ""))
                institutions.append(entry.get("institution", ""))
                timeframes.append(entry.get("timeframe", ""))
            
            flattened_profiles.append({
                "author_id": author_id,
                "name": name,
                "affiliation": affiliation,
                "joined_date": joined_date,
                "personal_links": links_str,
                "positions": "; ".join(positions) if positions else "",
                "institutions": "; ".join(institutions) if institutions else "",
                "timeframes": "; ".join(timeframes) if timeframes else "",
                "advisors": advisors_str,
                "expertise": expertise_str
            })
        
        df = pd.DataFrame(flattened_profiles)
        df.to_csv(authors_file, index=False, encoding='utf-8')
        print(f"Saved {len(all_author_ids)} author profiles to {authors_file}")
        
        results["author_profiles"] = {
            "author_count": len(all_author_ids),
            "file": authors_file
        }
    
    return {"status": "success", "results": results}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)