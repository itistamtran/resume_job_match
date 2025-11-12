import re
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

def extract_keywords(text):
    """Extract key terms from text for interpretability."""
    text = text.lower()
    text = re.sub(r'[^a-z\s]', '', text)
    words = [w for w in text.split() if w not in ENGLISH_STOP_WORDS and len(w) > 2]
    return set(words)

def explain_match(resume_text, job_text, max_terms=20):
    """Provide an explanation layer showing skill overlap."""
    resume_keywords = extract_keywords(resume_text)
    job_keywords = extract_keywords(job_text)

    overlap = resume_keywords & job_keywords
    missing_in_resume = job_keywords - resume_keywords
    extra_in_resume = resume_keywords - job_keywords

    return {
        "shared_skills": sorted(list(overlap))[:max_terms],
        "missing_skills": sorted(list(missing_in_resume))[:max_terms],
        "extra_skills": sorted(list(extra_in_resume))[:max_terms]
    }
