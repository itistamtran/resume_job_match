import streamlit as st
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path to import from src
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from progress_circle import render_progress_circle
from description_toggle import render_job_description
from src.embedder import ResumeJobEmbedder
from src.recommender import JobRecommender
import pdfplumber
import fitz  # PyMuPDF
import docx2txt

# --- Page Configuration ---
st.set_page_config(page_title="Resume-to-Job Match", page_icon="💼", layout="wide")

# Custom button style
st.markdown(
    """
    <style>
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #6ac5fe, #daf0ff);
        color: black;
        border-radius: 10px;
        height: 3rem;
        font-weight: 600;
        border: none;
    }
    div.stButton > button:hover {
        background: linear-gradient(90deg, #daf0ff, #6ac5fe);
        color: black;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Custom CSS for a modern UI ---
st.markdown(
    """
    <style>
    body {
        background-color: #0e1117;
        color: #fafafa;
    }
    .centered-title {
        text-align: center;
        font-size: 2.3em;
        font-weight: 700;
        color: #f5f5f5;
        margin-bottom: 0.3em;
    }
    .subtext {
        text-align: center;
        color: #bbb;
        font-size: 1.1em;
        margin-bottom: 2em;
    }
    .footer {
        text-align: center;
        color: #777;
        font-size: 0.9em;
    }
    .job-description ul li {
        position: relative !important;
        padding-left: 14px !important;
        color: #f0f0f0 !important;
        margin-bottom: 0.6em !important;
        list-style: none !important;
    }
    .job-description ul li::before {
        content: "" !important;
        position: absolute !important;
        left: -1.2em !important;
        top: 0.55em !important;
        width: 0.55em !important;
        height: 0.55em !important;
        border-radius: 50% !important;
        background: linear-gradient(90deg, #6ac5fe, #daf0ff) !important;
        box-shadow: 0 0 6px rgba(106, 197, 254, 0.6) !important;
    }
    .job-description span[style*="color:#6ac5fe"],
    span[style*="color: rgb(91, 180, 80)"] {
        color: #6ac5fe !important;
    }
    .section-title {
        font-size: 1.1em;
        font-weight: 700;
        margin-top: 1.2em;
        margin-bottom: 0.8em;
        background: linear-gradient(90deg, #6ac5fe, #daf0ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    strong {
        background: linear-gradient(90deg, #6ac5fe, #daf0ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 1.1em;
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# CSS for vertical centering inside columns
st.markdown("""
    <style>
        .circle-wrapper {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100%;
            position: relative;
            top: 50%;
            transform: translateY(-50%);
        }
    </style>
""", unsafe_allow_html=True)


# --- Header ---
st.markdown('<h1 class="centered-title">💼 Resume-to-Job Match Recommendation System</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtext">Upload your resume and get job recommendations based on semantic similarity.</p>', unsafe_allow_html=True)

# --- Load data and models ---
@st.cache_data
def load_jobs_data():
    """Load job data from CSV files"""
    jobs_model = pd.read_csv("data/cleaned_jobs_for_model.csv")
    jobs_display = pd.read_csv("data/cleaned_jobs_full.csv")

    assert len(jobs_model) == len(jobs_display), "Model and display job files must have the same length."

    jobs = jobs_model.copy()

    # Determine which column to use for display
    if "description" in jobs_display.columns:
        jobs["job_description"] = jobs_display["description"]
    elif "job_description" in jobs_display.columns:
        jobs["job_description"] = jobs_display["job_description"]
    elif "clean_job_display" in jobs_display.columns:
        jobs["job_description"] = jobs_display["clean_job_display"]
    else:
        jobs["job_description"] = jobs_display.get("clean_job", "")

    jobs.replace("N/A", "", inplace=True)
    jobs.fillna("", inplace=True)

    return jobs

@st.cache_resource
def load_model_and_embeddings():
    """Load job data and pre-computed embeddings"""
    job_data = load_jobs_data()
    job_embeddings = np.load('data/job_embeddings.npy')
    return job_data, job_embeddings

def extract_resume_text(uploaded_file):
    """Extract text from uploaded resume file"""
    if uploaded_file is None:
        return ""
    
    if uploaded_file.name.endswith(".pdf"):
        text = ""
        try:
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception:
            text = ""

        if len(text.strip()) < 100:
            try:
                uploaded_file.seek(0)
                with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
                    text = "\n".join(page.get_text("text") for page in doc)
            except Exception as e:
                st.error(f"Error reading PDF: {str(e)}")
                return ""
        return text
    
    elif uploaded_file.name.endswith(".docx"):
        try:
            return docx2txt.process(uploaded_file)
        except Exception as e:
            st.error(f"Error reading DOCX: {str(e)}")
            return ""
            
    elif uploaded_file.name.endswith(".txt"):
        try:
            return uploaded_file.read().decode("utf-8")
        except Exception as e:
            st.error(f"Error reading TXT: {str(e)}")
            return ""
    else:
        st.warning("Unsupported file format. Please upload a PDF, DOCX, or TXT file.")
        return ""

@st.cache_resource
def initialize_system():
    """Load all necessary components"""
    embedder = ResumeJobEmbedder(model_name='all-MiniLM-L6-v2')
    job_data, job_embeddings = load_model_and_embeddings()
    recommender = JobRecommender(job_embeddings, job_data)
    return embedder, job_data, recommender

embedder, job_data, recommender = initialize_system()

# --- Initialize session state ---
if "resume_text" not in st.session_state:
    st.session_state["resume_text"] = ""
if "recommendations" not in st.session_state:
    st.session_state["recommendations"] = None

# --- Upload resume section ---
st.markdown("---")
uploaded_file = st.file_uploader(
    "📄 **Upload your resume (PDF, DOCX, or TXT)**",
    type=["pdf", "docx", "txt"],
    help="Max file size: 200MB"
)
st.markdown("---")

# --- Handle upload ---
resume_text = ""
if uploaded_file:
    resume_text = extract_resume_text(uploaded_file)
    st.markdown(
    """
    <div style="
        color:#6ac5fe;
        font-weight:500;
        margin-top:10px;
        margin-bottom:10px;
    ">
        ✓ Resume uploaded and processed successfully.
    </div>
    """,
    unsafe_allow_html=True,
)

    with st.expander("View Extracted Resume Text"):
        st.text_area(
            "Extracted Resume Text:",
            resume_text[:10000] + ("..." if len(resume_text) > 10000 else ""),
            height=400
        )

# --- Job matching section ---
if st.button("Find Matching Jobs", type="primary", use_container_width=True):
    if resume_text.strip():
        with st.spinner("🔍 Finding your best matches..."):
            # Use the recommender to get matches
            results_df = recommender.recommend(resume_text, embedder, top_k=30)
            st.session_state['recommendations'] = results_df
    else:
        st.warning("ᵎ!ᵎ Please upload a valid resume file first.")

# --- Display recommendations from session state ---
if 'recommendations' in st.session_state and st.session_state['recommendations'] is not None:
    results_df = st.session_state['recommendations']

    # Ensure cached object is a DataFrame
    if isinstance(results_df, list):
        results_df = pd.DataFrame(results_df)
        st.session_state['recommendations'] = results_df

    st.markdown("## ⋆.˚🦋༘⋆ Top Matches")

    # --- Pagination setup ---
    jobs_per_page = 5
    if 'visible_jobs' not in st.session_state:
        st.session_state.visible_jobs = jobs_per_page

    total_jobs = len(results_df)
    visible_jobs = min(st.session_state.visible_jobs, total_jobs)
    display_df = results_df.head(visible_jobs)

    # --- Display jobs ---
    for idx, row in enumerate(display_df.itertuples(), 1):
        percent = round(float(row.match_percentage), 2)

        # Match level + color
        if percent >= 80:
            match_label, color = "STRONG MATCH", "#6ac5fe"
        elif percent >= 60:
            match_label, color = "GOOD MATCH", "#f1c40f"
        else:
            match_label, color = "FAIR MATCH", "#e67e22"

        # Get job details
        company = getattr(row, 'company', 'Unknown Company')
        title = getattr(row, 'title', 'Untitled Job')
        location = getattr(row, 'location', 'Unspecified Location')
        salary_min = getattr(row, 'salary_min', 0)
        salary_max = getattr(row, 'salary_max', 0)
        date_posted = getattr(row, 'date_posted', 'Unknown Date')
        display_job = getattr(row, 'job_description', getattr(row, 'description', ''))

        # Salary info
        salary_info = ""
        if salary_min > 0 or salary_max > 0:
            salary_info = f"${int(salary_min):,} - ${int(salary_max):,}"

        # --- add line before the first job ---
        if idx == 1:
            st.markdown("<hr style='margin-top: 30px; margin-bottom: 25px;'>", unsafe_allow_html=True)

        # --- Job container ---
        with st.container():
            col1, col2 = st.columns([1, 4])

            with col1:
                st.markdown('<div class="center-container">', unsafe_allow_html=True)
                render_progress_circle(percent, color, match_label)
                st.markdown('</div>', unsafe_allow_html=True)

            with col2:
                st.markdown(
                    f"""
                    <div style="margin-top:10px;">
                        <h3 style="color:white; font-size:1.4em; margin:0; font-weight:700;">{title}</h3>
                        <p style="margin:4px 0 10px 0; font-size:1.05em; color:#cccccc;">
                            <span style="color:{color}; font-weight:600;">{company}</span>
                            &nbsp;·&nbsp; {location}
                            {f"&nbsp;·&nbsp; 💰 {salary_info}" if salary_info else ""}
                            &nbsp;·&nbsp; 🗓 {date_posted}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                render_job_description(display_job, idx)

            st.markdown("<hr>", unsafe_allow_html=True)

    # --- Load more button or end message ---
    if visible_jobs < total_jobs:
        st.markdown("<br>", unsafe_allow_html=True)
        left, mid, right = st.columns([2, 1, 2])
        with mid:
            if st.button("Load more jobs ⤵", use_container_width=True):
                st.session_state.visible_jobs += jobs_per_page
                st.rerun()

    else:
        st.markdown(
            "<p style='text-align:center; color:gray; margin-top:20px;'>All jobs loaded.</p>",
            unsafe_allow_html=True,
        )


# --- Footer ---
st.markdown(
    '<div class="footer">Built with Streamlit • Powered by Sentence Transformers</div>',
    unsafe_allow_html=True
)