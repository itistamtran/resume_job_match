import requests
import pandas as pd
import time
import streamlit as st
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
ADZUNA_APP_ID = st.secrets["adzuna"]["app_id"]
ADZUNA_APP_KEY = st.secrets["adzuna"]["app_key"]
USAJOBS_API_KEY = st.secrets["usajobs"]["api_key"]
USER_AGENT_EMAIL = "itistamtran@gmail.com"
SAVE_PATH = "data/jobs_raw_data_full_desc.csv"


import requests
import time
import pandas as pd
from bs4 import BeautifulSoup
import streamlit as st

# ============================================================
# HELPERS — Fetch full Adzuna job description
# ============================================================
def fetch_full_adzuna_description(job_id):
    """Try Adzuna's /view endpoint first, return long text if available."""
    try:
        url = f"https://api.adzuna.com/v1/api/jobs/us/view/{job_id}"
        params = {"app_id": ADZUNA_APP_ID, "app_key": ADZUNA_APP_KEY}
        r = requests.get(url, params=params, timeout=8)
        if r.status_code == 200:
            data = r.json()
            desc = data.get("description", "")
            if desc and len(desc) > 200:
                return desc
        # ignore 404, others are logged below
        elif r.status_code not in (404,):
            print(f"/view failed ({r.status_code}) for {job_id}")
    except requests.exceptions.Timeout:
        pass
    except Exception as e:
        print(f"/view error for {job_id}: {e}")
    return ""


def fetch_full_from_redirect(url):
    """Fallback: scrape redirect page text."""
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            paragraphs = soup.find_all(["p", "li"])
            text = " ".join(p.get_text(strip=True) for p in paragraphs)
            return " ".join(text.split())[:8000]
    except Exception:
        pass
    return ""


# ============================================================
# FETCH FROM ADZUNA — Automatic pagination & logging
# ============================================================
def fetch_adzuna_jobs():
    all_jobs = []
    keywords = [
        "developer", "engineer", "scientist", "analyst", "manager",
        "technician", "designer", "assistant", "intern", "consultant",
        "teacher", "sales", "marketing", "finance", "healthcare", "nurse",
        "driver", "operator", "administrator", "coordinator", "specialist",
        "supervisor", "director", "executive", "clerk", "representative",
        "hr", "recruiter", "accountant", "architect", "planner",
        "researcher", "writer", "editor", "producer", "chef", "cook",
        "warehouse", "logistics", "customer service", "support", "retail",
    ]
    seen_ids = set()
    max_pages = 5              # cap per keyword
    consecutive_empty = 0      # track consecutive empty or timeout pages
    MAX_EMPTY_LIMIT = 2        # stop after two consecutive empties/timeouts

    st.write("Fetching jobs from Adzuna...")

    for kw in keywords:
        st.write(f"Searching '{kw}'...")
        consecutive_empty = 0

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
                    print(f"Adzuna request failed ({r.status_code}) for '{kw}' page {page}")
                    break

                results = r.json().get("results", [])
                if not results:
                    consecutive_empty += 1
                    if consecutive_empty >= MAX_EMPTY_LIMIT:
                        print(f"No more results for '{kw}' after page {page-1}")
                        break
                    continue
                else:
                    consecutive_empty = 0

                for job in results:
                    job_id = job.get("id")
                    if not job_id or job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)

                    desc = fetch_full_adzuna_description(job_id)
                    if not desc or len(desc) < 200:
                        desc = fetch_full_from_redirect(job.get("redirect_url"))
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

                st.write(f"{len(results)} jobs fetched for '{kw}' page {page}")
                time.sleep(1)

            except requests.exceptions.ReadTimeout:
                print(f"Timeout on '{kw}' page {page}, skipping...")
                consecutive_empty += 1
                if consecutive_empty >= MAX_EMPTY_LIMIT:
                    break
                continue
            except Exception as e:
                st.warning(f"Error fetching Adzuna jobs for '{kw}' page {page}: {e}")
                break

    df = pd.DataFrame(all_jobs)
    st.success(f"Total Adzuna jobs fetched: {len(df)}")
    return df

# ============================================================
# FETCH FROM USAJOBS
# ============================================================
def fetch_usajobs():
    BASE_URL = "https://data.usajobs.gov/api/Search"
    HEADERS = {
        "Host": "data.usajobs.gov",
        "User-Agent": "itistamtran@gmail.com",  
        "Authorization-Key": USAJOBS_API_KEY,
    }

    all_jobs = []
    total_found = 0
    page = 1
    max_pages = 10  
    consecutive_empty = 0
    MAX_EMPTY_LIMIT = 2

    st.write("Fetching jobs from USAJOBS...")

    while page <= max_pages:
        params = {
            "ResultsPerPage": 25,
            "Page": page,
        }

        try:
            r = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=20)
            print(f"DEBUG: USAJOBS page {page} → status {r.status_code}")

            if r.status_code == 403:
                st.error("Invalid USAJOBS API key or User-Agent email not registered.")
                print("Response:", r.text[:300])
                break

            if r.status_code != 200:
                st.warning(f"USAJOBS request failed ({r.status_code}) on page {page}")
                print("Response snippet:", r.text[:300])
                break

            root = r.json()
            results = root.get("SearchResult", {}).get("SearchResultItems", [])
            if not results:
                consecutive_empty += 1
                if consecutive_empty >= MAX_EMPTY_LIMIT:
                    st.info(f"🔚 No more results after page {page - 1}")
                    break
                page += 1
                continue
            else:
                consecutive_empty = 0

            count = len(results)
            total_found += count

            for item in results:
                job = item.get("MatchedObjectDescriptor", {})
                details = job.get("UserArea", {}).get("Details", {})

                description = " ".join([
                    details.get("JobSummary", ""),
                    details.get("MajorDuties", ""),
                ]).strip()

                all_jobs.append({
                    "source": "USAJOBS",
                    "id": job.get("PositionID"),
                    "title": job.get("PositionTitle"),
                    "company": job.get("OrganizationName"),
                    "location": job.get("PositionLocationDisplay"),
                    "description": description,
                    "url": job.get("PositionURI"),
                    "salary_min": (job.get("PositionRemuneration") or [{}])[0].get("MinimumRange"),
                    "salary_max": (job.get("PositionRemuneration") or [{}])[0].get("MaximumRange"),
                    "date_posted": job.get("PublicationStartDate"),
                })

            st.write(f"USAJOBS: {count} jobs fetched from page {page}")
            time.sleep(1)
            page += 1

        except requests.exceptions.Timeout:
            st.warning(f"Timeout on USAJOBS page {page}, skipping...")
            consecutive_empty += 1
            if consecutive_empty >= MAX_EMPTY_LIMIT:
                break
            page += 1
            continue
        except Exception as e:
            st.error(f"Error fetching USAJOBS page {page}: {e}")
            break

    df = pd.DataFrame(all_jobs)
    st.success(f"Total USAJOBS jobs fetched: {len(df)}")
    return df


# ============================================================
# COMBINE AND SAVE
# ============================================================
adzuna_df = fetch_adzuna_jobs()
usajobs_df = fetch_usajobs()

combined_df = pd.concat([adzuna_df, usajobs_df], ignore_index=True)
combined_df.drop_duplicates(subset=["title", "company", "location"], inplace=True)
combined_df.to_csv(SAVE_PATH, index=False)

st.success(f"Saved {len(combined_df)} total jobs to {SAVE_PATH}")
