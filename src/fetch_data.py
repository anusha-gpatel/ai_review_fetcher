import openreview
import pandas as pd
import os
import time
import requests  

class ICLRDataCollector:
    def __init__(self):
        """Initialize OpenReview client for data collection"""
        self.client = openreview.Client(baseurl='https://api.openreview.net')
        print("✅ Connected to OpenReview API")

    def get_conference_papers(self, venue, year):
        """Get all papers from a specific ICLR conference"""
        print(f"🔍 Fetching papers from {venue}...")

        try:
            submissions = list(self.client.get_all_notes(
                invitation=f'{venue}/-/Blind_Submission',
                details='replies'  # Include reviews
            ))
            print(f"📄 Found {len(submissions)} papers for {year}")
            return submissions
        except Exception as e:
            print(f"❌ Error fetching papers: {e}")
            return []

    def extract_paper_info(self, paper, year, venue):
        """Extract paper metadata"""
        content = paper.content if hasattr(paper, 'content') else {}
        return {
            'paper_id': paper.id,
            'title': content.get('title', ''),
            'abstract': content.get('abstract', ''),
            'authors': ", ".join(content.get('authors', [])),
            'author_ids': ", ".join(content.get('authorids', [])),
            'keywords': ", ".join(content.get('keywords', [])),
            'primary_area': content.get('primary_area', ''),
            'year': year,
            'venue': venue,
            'pdf_url': f"https://openreview.net/pdf?id={paper.id}",
            'submission_date': getattr(paper, 'cdate', None),
        }

    def extract_reviews(self, paper, year, venue):
        """Extract all reviews for a paper"""
        reviews = []
        if hasattr(paper, 'details') and 'replies' in paper.details:
            for reply in paper.details['replies']:
                try:
                    invitation = reply.get('invitation', '')
                    if 'Official_Review' in invitation or 'Review' in invitation:
                        content = reply.get('content', {})
                        review_sections = ['summary', 'strengths', 'weaknesses', 'questions', 'limitations', 'review']
                        full_text = "\n\n".join(
                            f"{section.upper()}: {content.get(section, '')}"
                            for section in review_sections if content.get(section)
                        )
                        reviews.append({
                            'review_id': reply.get('id', ''),
                            'paper_id': paper.id,
                            'year': year,
                            'venue': venue,
                            'reviewer': reply.get('signatures', ['Anonymous'])[0],
                            'full_review_text': full_text.strip(),
                            'rating': content.get('rating', ''),
                            'confidence': content.get('confidence', ''),
                            'summary': content.get('summary', ''),
                            'strengths': content.get('strengths', ''),
                            'weaknesses': content.get('weaknesses', ''),
                            'questions': content.get('questions', ''),
                            'limitations': content.get('limitations', ''),
                            'recommendation': content.get('recommendation', ''),
                            'review_date': reply.get('cdate', None),
                        })
                except Exception as e:
                    print(f"⚠️ Error processing reply: {str(e)[:60]}...")
        return reviews

    def collect_oral_accepts(self, year, venue=None):
        """Collect only oral accepted papers for a given year"""
        venue = venue or f'ICLR.cc/{year}/Conference'
        print(f"🎤 Collecting oral acceptances for {year}...")
        subs = list(self.client.get_all_notes(
            invitation=f'{venue}/-/Blind_Submission',
            details='directReplies'
        ))
        oral = []
        for sub in subs:
            for rep in sub.details.get('directReplies', []):
                if rep.get('invitation', '').endswith('/-/Decision') and rep.get('content', {}).get('decision') == 'Accept (Oral)':
                    info = self.extract_paper_info(sub, year, venue)
                    info['decision_date'] = rep['cdate']
                    oral.append(info)
        os.makedirs("output", exist_ok=True)
        pd.DataFrame(oral).to_csv(f'output/ICLR_{year}_orals.csv', index=False)
        print(f"✅ Saved {len(oral)} oral papers to output/ICLR_{year}_orals.csv")

    def collect_spotlight_accepts(self, year, venue=None):
        """Collect spotlight accepted papers for a given year"""
        venue = venue or f'ICLR.cc/{year}/Conference'
        print(f"💡 Collecting spotlight acceptances for {year}...")
        subs = list(self.client.get_all_notes(
            invitation=f'{venue}/-/Blind_Submission',
            details='directReplies'
        ))
        spotlight = []
        for sub in subs:
            for rep in sub.details.get('directReplies', []):
                if rep.get('invitation', '').endswith('/-/Decision') and rep.get('content', {}).get('decision') == 'Accept (Spotlight)':
                    info = self.extract_paper_info(sub, year, venue)
                    info['decision_date'] = rep['cdate']
                    spotlight.append(info)
        os.makedirs("output", exist_ok=True)
        pd.DataFrame(spotlight).to_csv(f'output/ICLR_{year}_spotlight.csv', index=False)
        print(f"✅ Saved {len(spotlight)} spotlight papers to output/ICLR_{year}_spotlight.csv")

    def collect_yearwise_data(self, year, venue=None):
        """Full paper + review collection for a year"""
        venue = venue or f'ICLR.cc/{year}/Conference'
        print(f"\n📥 Collecting ICLR {year} full data...")
        papers = self.get_conference_papers(venue, year)
        papers_data, reviews_data = [], []

        for i, paper in enumerate(papers):
            if i % 20 == 0:
                print(f"📝 Processing paper {i+1}/{len(papers)}")
            papers_data.append(self.extract_paper_info(paper, year, venue))
            reviews_data.extend(self.extract_reviews(paper, year, venue))
            time.sleep(0.01)

        os.makedirs("output", exist_ok=True)
        pd.DataFrame(papers_data).to_csv(f'output/ICLR_{year}_papers.csv', index=False)
        pd.DataFrame(reviews_data).to_csv(f'output/ICLR_{year}_reviews.csv', index=False)
        print(f"📁 Saved papers and reviews to 'output/'")

    def collect_multiple_years(self, years):
        """Run full data collection for multiple years"""
        for year in years:
            self.collect_yearwise_data(year)

    def fetch_filtered_notes(self, filter_type, year=2024):
        base_api = "https://api2.openreview.net/notes"
        domain = f"ICLR.cc/{year}/Conference"
        offset = 0
        batch_size = 1000
        all_notes = []

        # Define base query parameters (without offset and limit)
        filter_params_map = {
            "oral": {
                "content.venue": f"ICLR {year} oral",
                "domain": domain,
                "details": "replyCount,presentation,writable",
            },
            "spotlight": {
                "content.venue": f"ICLR {year} spotlight",
                "domain": domain,
                "details": "replyCount,presentation,writable",
            },
            "poster": {
                "content.venue": f"ICLR {year} poster",
                "domain": domain,
                "details": "replyCount,presentation,writable",
            },
            "submitted": {
                "content.venue": f"Submitted to ICLR {year}",
                "domain": domain,
                "details": "replyCount,presentation,writable",
            },
            "reject": {
                "content.venueid": f"ICLR.cc/{year}/Conference/Desk_Rejected_Submission",
                "domain": domain,
                "details": "replyCount,presentation,writable",
            },
            "withdrawn": {
                "content.venueid": f"ICLR.cc/{year}/Conference/Withdrawn_Submission",
                "domain": domain,
                "details": "replyCount,presentation,writable",
            }
        }

        if filter_type not in filter_params_map:
            raise ValueError(f"Filter '{filter_type}' is not supported.")

        base_params = filter_params_map[filter_type]
        print(f"📥 Fetching all '{filter_type}' papers from ICLR {year}...")

        while True:
            # Add pagination controls
            params = base_params.copy()
            params["limit"] = batch_size
            params["offset"] = offset

            response = requests.get(base_api, params=params)
            response.raise_for_status()
            data = response.json()

            notes = data.get("notes", [])
            if not notes:
                break

            all_notes.extend(notes)
            offset += batch_size
            print(f"🔄 Fetched {len(all_notes)} notes so far...")

        print(f"✅ Total fetched: {len(all_notes)} notes for '{filter_type}'")
        return all_notes

    def save_filtered_papers_csv(self, notes, year, filter_type):
        papers_data = []
        for note in notes:
            content = note.get('content', {})
            papers_data.append({
                'paper_id': note.get('id', ''),
                'title': content.get('title', ''),
                'abstract': content.get('abstract', ''),
                'authors': ", ".join(content.get('authors', [])),
                'pdf_url': f"https://openreview.net/pdf?id={note.get('id', '')}",
                'venue': f'ICLR.cc/{year}/Conference',
                'year': year
            })
        filename = f'output/ICLR_{year}_{filter_type}_papers.csv'
        pd.DataFrame(papers_data).to_csv(filename, index=False)
        print(f"Saved {len(papers_data)} papers to {filename}")

        
    def collect_filtered(self, year, filter_type):
   
        venue = f'ICLR.cc/{year}/Conference'
        filter_map = {
            "oral": "ICLR 2024 oral",
            "spotlight": "ICLR 2024 spotlight",
            "poster": "ICLR 2024 poster",
            "reject": "ICLR 2024 reject",
            "withdrawn": "ICLR 2024 withdrawn submission",
            "desk_rejected": "ICLR 2024 desk rejected submission"
        }
        venue_content = filter_map.get(filter_type.lower())
        if not venue_content:
            print(f"Unknown filter type: {filter_type}")
            return []

        print(f"Fetching filtered notes for {year} with filter: {filter_type}")

        notes = self.fetch_filtered_notes(filter_type, year)

        papers_data = []
        for note in notes:
            papers_data.append({
                'paper_id': note.get('id', ''),
                'title': note.get('content', {}).get('title', ''),
                'abstract': note.get('content', {}).get('abstract', ''),
                'authors': ", ".join(note.get('content', {}).get('authors', [])),
                'pdf_url': f"https://openreview.net/pdf?id={note.get('id', '')}",
                'venue': venue,
                'year': year
            })

        filename = f'output/ICLR_{year}_{filter_type}_papers.csv'
        pd.DataFrame(papers_data).to_csv(filename, index=False)
        print(f"Saved filtered papers to {filename}")
        return papers_data



