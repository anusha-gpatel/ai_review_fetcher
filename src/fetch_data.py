import openreview
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

class ICLRDataCollector:
    def __init__(self):
        """Initialize OpenReview client for data collection"""
        self.client = openreview.Client(baseurl='https://api.openreview.net')
        print("Connected to OpenReview API")
        print("Ready to collect ICLR conference data")

    def get_conference_papers(self, venue, year):
        """Get all papers from a specific ICLR conference"""
        print(f" Fetching papers from {venue}...")

        try:
            submissions = list(self.client.get_all_notes(
                invitation=f'{venue}/-/Blind_Submission',
                details='replies'  # Include reviews
            ))

            print(f" Found {len(submissions)} papers for {year}")
            return submissions

        except Exception as e:
            print(f" Error fetching papers: {e}")
            return []

    def extract_paper_info(self, paper, year, venue):
        """Extract complete paper information"""
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
                    if isinstance(reply, dict):
                        invitation = reply.get('invitation', '')
                        reply_id = reply.get('id', '')
                        signatures = reply.get('signatures', [])
                        cdate = reply.get('cdate', None)
                        content = reply.get('content', {})
                    else:
                        invitation = getattr(reply, 'invitation', '')
                        reply_id = getattr(reply, 'id', '')
                        signatures = getattr(reply, 'signatures', [])
                        cdate = getattr(reply, 'cdate', None)
                        content = getattr(reply, 'content', {}) if hasattr(reply, 'content') else {}

                    if 'Official_Review' in invitation or 'Review' in invitation:
                        review_sections = ['summary', 'strengths', 'weaknesses', 'questions', 'limitations', 'review']
                        full_text = ""
                        for section in review_sections:
                            if section in content and content[section]:
                                full_text += f"{section.upper()}: {content[section]}\n\n"

                        reviews.append({
                            'review_id': reply_id,
                            'paper_id': paper.id,
                            'year': year,
                            'venue': venue,
                            'reviewer': signatures[0] if signatures else 'Anonymous',
                            'full_review_text': full_text.strip(),
                            'rating': content.get('rating', ''),
                            'confidence': content.get('confidence', ''),
                            'summary': content.get('summary', ''),
                            'strengths': content.get('strengths', ''),
                            'weaknesses': content.get('weaknesses', ''),
                            'questions': content.get('questions', ''),
                            'limitations': content.get('limitations', ''),
                            'recommendation': content.get('recommendation', ''),
                            'review_date': cdate,
                        })

                except Exception as e:
                    print(f"Error processing reply: {str(e)[:50]}...")

        return reviews


    def collect_yearwise_data(self, year, venue=None):
        if venue is None:
            venue = f'ICLR.cc/{year}/Conference'

        print(f"\n Collecting ICLR {year} data from {venue}")
        papers = self.get_conference_papers(venue, year)

        papers_data = []
        reviews_data = []

        for i, paper in enumerate(papers):
            if i % 20 == 0:
                print(f"  Processing paper {i+1}/{len(papers)}")

            papers_data.append(self.extract_paper_info(paper, year, venue))
            reviews_data.extend(self.extract_reviews(paper, year, venue))
            time.sleep(0.01)  # polite delay

        # Save to CSV
        pd.DataFrame(papers_data).to_csv(f'output/ICLR_{year}_papers.csv', index=False)
        pd.DataFrame(reviews_data).to_csv(f'output/ICLR_{year}_reviews.csv', index=False)
        print(f" Saved ICLR {year} papers and reviews to CSV.")



    def collect_multiple_years(self, years):
        """Collect data for multiple ICLR years"""
        for year in years:
            self.collect_yearwise_data(year)

# Initialize the collector
collector = ICLRDataCollector()
print("Data collector initialized and ready!")
