import requests
import pandas as pd
from typing import List, Dict
import streamlit as st

def fetch_adzuna_jobs_with_direct_links(
    app_id: str,
    app_key: str,
    country: str = "us",
    what: str = "",
    where: str = "",
    results_per_page: int = 50,
    max_pages: int = 5
) -> List[Dict]:
    """
    Fetch jobs from Adzuna with DIRECT apply links (not Adzuna redirect)
    
    Args:
        app_id: Adzuna App ID
        app_key: Adzuna API Key
        country: Country code (us, gb, ca, etc.)
        what: Job title/keywords
        where: Location
        results_per_page: Number of results per page (max 50)
        max_pages: Maximum number of pages to fetch
    
    Returns:
        List of job dictionaries with direct apply URLs
    """
    
    base_url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1.json"
    jobs = []
    
    for page in range(1, max_pages + 1):
        url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"
        params = {
            "app_id": app_id,
            "app_key": app_key,
            "results_per_page": results_per_page,
            "what": what,
            "where": where,
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if "results" not in data or len(data["results"]) == 0:
                print(f"No more results found at page {page}")
                break
            
            for job in data["results"]:
                adzuna_id = job.get("id")
                # IMPORTANT: Use redirect.url instead of just url
                # redirect.url takes you DIRECTLY to the employer's application page
                direct_url = job.get("redirect_url", job.get("url", ""))

                # Try to fetch real employer link from details API
                if adzuna_id:
                    details_url = f"https://api.adzuna.com/v1/api/jobs/{country}/details/{adzuna_id}"
                    detail_params = {
                        "app_id": app_id,
                        "app_key": app_key
                    }
                    try:
                        detail_response = requests.get(details_url, params=detail_params)
                        if detail_response.status_code == 200:
                            detail_data = detail_response.json()
                            direct_url = detail_data.get("redirect_url", direct_url)
                    except Exception as e:
                        print(f"Error fetching details for {adzuna_id}: {e}")
                
                job_data = {
                    "title": job.get("title", ""),
                    "company": job.get("company", {}).get("display_name", "Unknown"),
                    "location": job.get("location", {}).get("display_name", ""),
                    "description": job.get("description", ""),
                    "salary_min": job.get("salary_min", 0),
                    "salary_max": job.get("salary_max", 0),
                    "contract_type": job.get("contract_type", ""),
                    "category": job.get("category", {}).get("label", ""),
                    "date_posted": job.get("created", ""),
                    "job_url": direct_url,  # This is the DIRECT link!
                    "adzuna_url": job.get("url", ""),  # Keep Adzuna URL as backup
                }
                
                jobs.append(job_data)
            
            print(f"Fetched {len(data['results'])} jobs from page {page}")
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching page {page}: {str(e)}")
            break
    
    return jobs


def get_direct_apply_url(adzuna_job_id: str, app_id: str, app_key: str, country: str = "us") -> str:
    """
    Alternative method: Get direct apply URL for a specific Adzuna job
    
    Args:
        adzuna_job_id: The Adzuna job ID
        app_id: Adzuna App ID
        app_key: Adzuna API Key
        country: Country code
    
    Returns:
        Direct apply URL
    """
    url = f"https://api.adzuna.com/v1/api/jobs/{country}/details/{adzuna_job_id}"
    
    params = {
        "app_id": app_id,
        "app_key": app_key
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # The redirect_url field contains the direct link
        return data.get("redirect_url", data.get("url", ""))
    
    except requests.exceptions.RequestException as e:
        print(f"Error getting job details: {str(e)}")
        return ""


# Example usage:
if __name__ == "__main__":
    # Replace with your Adzuna credentials
    APP_ID = st.secrets["adzuna"]["app_id"]
    APP_KEY = st.secrets["adzuna"]["app_key"]

    keywords = [
    "developer", "engineer", "scientist", "analyst", "manager",
    "technician", "designer", "assistant", "intern", "consultant",
    "teacher", "sales", "marketing", "finance", "healthcare", "nurse",
    "driver", "operator", "administrator", "coordinator", "specialist",
    "supervisor", "director", "executive", "clerk", "representative",
    "hr", "recruiter", "accountant", "architect", "planner",
    "researcher", "writer", "editor", "producer", "chef", "cook",
    "warehouse", "logistics", "customer service", "support", "retail",
    "software engineer", "data scientist", "product manager", "marketing manager",
    "sales representative", "financial analyst", "graphic designer", "human resources manager",
    "business analyst", "project manager", "accountant", "network administrator",
    "web developer", "content writer", "operations manager", "quality assurance analyst",
    "social media manager", "customer service representative", "logistics coordinator",
    "research assistant", "executive assistant", "data analyst", "it support specialist",
    "digital marketing specialist", "software developer intern", "financial advisor",
    "ux designer", "technical writer", "supply chain manager", "event coordinator",
    "public relations specialist", "medical assistant", "nursing assistant",
    "account manager", "sales manager", "marketing coordinator",
    "data engineer", "cybersecurity analyst", "it manager", "business development manager",
]

    all_jobs = []
    
    # Fetch jobs with direct links
    for kw in keywords:
        print(f"\nFetching jobs for keyword: {kw}")
        jobs = fetch_adzuna_jobs_with_direct_links(
            app_id=APP_ID,
            app_key=APP_KEY,
            country="us",
            what=kw,
            where="california",
            results_per_page=50,
            max_pages=5
        )
    all_jobs.extend(jobs)
    
    if not all_jobs:
        print("No jobs fetched, check your API parameters or credentials.")
    else:
        df = pd.DataFrame(all_jobs)
        print(f"\nTotal jobs fetched: {len(df)}")
        print(f"\nJobs with direct URLs: {df['job_url'].notna().sum()}")

        # Save to CSV
        df.to_csv("data/adzuna_jobs_with_direct_links.csv", index=False)
        print("Saved to data/adzuna_jobs_with_direct_links.csv")

        # Show sample URLs
        print("\nSample direct URLs:")
        for idx, row in df.head(3).iterrows():
            print(f"\nJob: {row['title']}")
            print(f"Company: {row['company']}")
            print(f"Direct URL: {row['job_url']}")

