# from src.fetch_data import ICLRDataCollector
# import pandas as pd
# import os
# import concurrent.futures

# def fetch_and_extract(year):
#     collector = ICLRDataCollector()
#     papers = collector.get_conference_papers(year)
#     return [collector.extract_paper_info(paper, year, "ICLR") for paper in papers]

# if __name__ == "__main__":
#     os.makedirs("output", exist_ok=True)

#     all_years = list(range(2018, 2025))
#     all_papers = []

#     with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
#         results = executor.map(fetch_and_extract, all_years)
#         for year_papers in results:
#             all_papers.extend(year_papers)

#     df = pd.DataFrame(all_papers)
#     df.to_csv("output/iclr_all_years_papers.csv", index=False)
#     print("✅ Data saved to output/iclr_all_years_papers.csv")

from src.fetch_data import ICLRDataCollector
import pandas as pd
import os

if __name__ == "__main__":
    os.makedirs("output", exist_ok=True)
    collector = ICLRDataCollector()

    all_papers = []
    for year in range(2018, 2025):
        papers = collector.get_all_blind_notes(year)
        for paper in papers:
            extracted = collector.extract_paper_info_with_reviews(paper, year, "ICLR")
            all_papers.append(extracted)

    df = pd.DataFrame(all_papers)
    df.to_csv("output/iclr_all_years_papers.csv", index=False)
    print("✅ Data saved to output/iclr_all_years_papers.csv")