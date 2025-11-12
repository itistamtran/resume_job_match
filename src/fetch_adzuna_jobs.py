import os
import requests
import pandas as pd
import time
from bs4 import BeautifulSoup

# Try to import Streamlit if available
try:
    import streamlit as st
    STREAMLIT_MODE = True
    ADZUNA_APP_ID = st.secrets["adzuna"]["app_id"]
    ADZUNA_APP_KEY = st.secrets["adzuna"]["app_key"]
except Exception:
    STREAMLIT_MODE = False
    ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
    ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")

SAVE_PATH = "data/adzunajobs_raw_data_3.csv"


def log(msg):
    """Print or Streamlit-write based on mode."""
    if STREAMLIT_MODE:
        st.write(msg)
    else:
        print(msg)


# ============================================================
# Fetch full job description
# ============================================================
def fetch_full_adzuna(job_id):
    try:
        url = f"https://api.adzuna.com/v1/api/jobs/us/view/{job_id}"
        params = {"app_id": ADZUNA_APP_ID, "app_key": ADZUNA_APP_KEY}
        r = requests.get(url, params=params, timeout=8)
        if r.status_code == 200:
            data = r.json()
            desc = data.get("description", "")
            if desc and len(desc) > 200:
                return desc
    except Exception as e:
        log(f"❌ /view error for {job_id}: {e}")
    return ""


def fetch_from_redirect(url):
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            text = " ".join(p.get_text(strip=True) for p in soup.find_all(["p", "li"]))
            return " ".join(text.split())[:8000]
    except Exception:
        pass
    return ""


# ============================================================
# Fetch HR-related jobs
# ============================================================
def fetch_jobs():
    all_jobs = []
    keywords = ["hr", "human resources", "recruiter", "talent acquisition", "people operations"]
    seen_ids = set()

    max_pages = 5
    log("Fetching jobs from Adzuna...")

    for kw in keywords:
        log(f"Searching '{kw}'...")
        empty_pages = 0

        for page in range(1, max_pages + 1):
            url = f"https://api.adzuna.com/v1/api/jobs/us/search/{page}"
            params = {
                "app_id": ADZUNA_APP_ID,
                "app_key": ADZUNA_APP_KEY,
                "results_per_page": 50,
                "what": kw,
                "content-type": "application/json",
            }

            try:
                r = requests.get(url, params=params, timeout=15)
                if r.status_code != 200:
                    log(f"Request failed ({r.status_code}) for '{kw}' page {page}")
                    break

                results = r.json().get("results", [])
                if not results:
                    empty_pages += 1
                    if empty_pages >= 2:
                        log(f"🔚 No more results for '{kw}' after page {page-1}")
                        break
                    continue

                for job in results:
                    job_id = job.get("id")
                    if not job_id or job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)

                    desc = fetch_full_adzuna(job_id) or fetch_from_redirect(job.get("redirect_url"))
                    if not desc:
                        desc = job.get("description", "") or job.get("adref", "")

                    all_jobs.append({
                        "source": "Adzuna",
                        "id": job_id,
                        "title": job.get("title"),
                        "company": job.get("company", {}).get("display_name"),
                        "location": job.get("location", {}).get("display_name"),
                        "description": desc,
                        "url": job.get("redirect_url"),
                        "salary_min": job.get("salary_min"),
                        "salary_max": job.get("salary_max"),
                        "date_posted": job.get("created"),
                    })

                log(f"{len(results)} jobs fetched for '{kw}' page {page}")
                time.sleep(1)

            except Exception as e:
                log(f"Error fetching '{kw}' page {page}: {e}")
                break

    df = pd.DataFrame(all_jobs)
    log(f"Total Adzuna jobs fetched: {len(df)}")
    return df


# ============================================================
# Run directly
# ============================================================
if __name__ == "__main__":
    df = fetch_jobs()
    if not df.empty:
        df.to_csv(SAVE_PATH, index=False)
        log(f"Saved {len(df)} jobs to {SAVE_PATH}")
    else:
        log("No jobs fetched. Check your API key or query.")
