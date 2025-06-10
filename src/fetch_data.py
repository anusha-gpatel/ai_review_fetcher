# import openreview

# class ICLRDataCollector:
#     def __init__(self):
#         self.client = openreview.Client(baseurl='https://api.openreview.net')
#         print("🔌 Connected to OpenReview API")

#     def get_conference_papers(self, year):
#         print(f"📥 Searching ICLR invitations for {year}...")
#         try:
#             invitations = self.client.get_all_invitations()
#             matching = [i.id for i in invitations if f"ICLR.cc/{year}" in i.id and "Blind_Submission" in i.id]

#             all_submissions = []
#             for invitation in matching:
#                 print(f"🔎 Fetching from: {invitation}")
#                 submissions = list(self.client.get_all_notes(invitation=invitation, details='replies'))
#                 print(f"📄 Found {len(submissions)} papers")
#                 all_submissions.extend(submissions)

#             return all_submissions

#         except Exception as e:
#             print(f"❌ Error fetching papers for {year}: {e}")
#             return []

#     def extract_paper_info(self, paper, year, venue):
#         content = paper.content if hasattr(paper, 'content') else {}
#         return {
#             'paper_id': paper.id,
#             'title': content.get('title', ''),
#             'abstract': content.get('abstract', ''),
#             'authors': ", ".join(content.get('authors', [])),
#             'author_ids': ", ".join(content.get('authorids', [])),
#             'keywords': ", ".join(content.get('keywords', [])),
#             'primary_area': content.get('primary_area', ''),
#             'year': year,
#             'venue': venue,
#             'pdf': content.get('pdf', '')
#         }

import openreview
import time

class ICLRDataCollector:
    def __init__(self):
        self.client = openreview.Client(baseurl='https://api.openreview.net')
        print("🔌 Connected to OpenReview API")

    def get_all_blind_notes(self, year):
        print(f"📥 Fetching Blind Submissions for ICLR {year}...")
        try:
            blind_invitation = f"ICLR.cc/{year}/Conference/-/Blind_Submission"
            notes = list(self.client.get_all_notes(invitation=blind_invitation))
            print(f"📄 Found {len(notes)} blind submissions")
            return notes
        except Exception as e:
            print(f"❌ Failed to fetch blind notes for {year}: {e}")
            return []

    def extract_paper_info_with_reviews(self, paper, year, venue):
        content = paper.content if hasattr(paper, 'content') else {}
        paper_id = paper.id
        reviews = []

        try:
            time.sleep(0.5)  # Small delay to avoid hitting rate limits
            replies = list(self.client.get_notes(forum=paper_id))
            for reply in replies:
                if 'Official_Review' in reply.invitation:
                    reviews.append(reply.content.get('review', ''))
        except Exception as e:
            print(f"⚠️ Error fetching reviews for paper {paper_id}: {e}")

        return {
            'paper_id': paper_id,
            'title': content.get('title', ''),
            'abstract': content.get('abstract', ''),
            'authors': ", ".join(content.get('authors', [])),
            'author_ids': ", ".join(content.get('authorids', [])),
            'keywords': ", ".join(content.get('keywords', [])),
            'primary_area': content.get('primary_area', ''),
            'year': year,
            'venue': venue,
            'pdf': content.get('pdf', ''),
            'reviews': " ||| ".join(reviews)
        }



