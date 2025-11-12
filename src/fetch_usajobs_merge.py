import requests
import pandas as pd
import time
import streamlit as st
from pathlib import Path

# =========================================================
# CONFIGURATION
# =========================================================
ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
USAJOBS_API_KEY = st.secrets["usajobs"]["api_key"]
USAJOBS_PATH = DATA_DIR / "usajobs_raw_data.csv"

# =========================================================
# FETCH USAJOBS 
# =========================================================
def fetch_usajobs():
    BASE_URL = "https://data.usajobs.gov/api/Search"
    HEADERS = {
        "Host": "data.usajobs.gov",
        "User-Agent": "itistamtran@gmail.com",  
        "Authorization-Key": "977bofnaa/8kWg0WaGgByERdbqPcX9kMqj+d+Ol55eA=",
    }

    all_jobs = []
    page = 1
    max_pages = 50  

    print("Fetching jobs from USAJOBS...")

    while page <= max_pages:
        params = {"ResultsPerPage": 25, "Page": page}

        try:
            r = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=20)
            print(f"DEBUG page {page}: status {r.status_code}")

            if r.status_code != 200:
                print("Response text:", r.text[:400])
                break

            root = r.json()
            results = root.get("SearchResult", {}).get("SearchResultItems", [])
            print(f"Page {page}: {len(results)} results")

            if not results:
                break

            for item in results:
                job = item.get("MatchedObjectDescriptor", {})
                remuneration = job.get("PositionRemuneration", [{}])[0]

                all_jobs.append({
                    "source": "USAJOBS",
                    "id": job.get("PositionID"),
                    "title": job.get("PositionTitle"),
                    "company": job.get("OrganizationName"),
                    "location": ", ".join(
                        [loc.get("LocationName", "") for loc in job.get("PositionLocation", [])]
                    ),
                    "description": job.get("UserArea", {}).get("Details", {}).get("JobSummary", ""),
                    "url": job.get("PositionURI"),
                    "salary_min": remuneration.get("MinimumRange"),
                    "salary_max": remuneration.get("MaximumRange"),
                    "date_posted": job.get("PublicationStartDate"),
                })

            print(f"Page {page}: {len(results)} jobs fetched, total so far: {len(all_jobs)}")
            time.sleep(1)
            page += 1

        except Exception as e:
            print(f"Exception on page {page}: {e}")
            break

    df = pd.DataFrame(all_jobs)
    print(f"TOTAL JOBS FETCHED: {len(df)}")
    if not df.empty:
        print(df.head(3))
    return df


# =========================================================
# RUN FETCH AND SAVE
# =========================================================
if __name__ == "__main__":
    df = fetch_usajobs()
    df.to_csv(USAJOBS_PATH, index=False)
    print(f"USAJOBS data saved to {USAJOBS_PATH}")
