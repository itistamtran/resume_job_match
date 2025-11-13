import streamlit as st
import pandas as pd
import numpy as np
import sys
import time
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
import os
import base64

# --- Page Configuration ---
st.set_page_config(page_title="Resume-to-Job Match", page_icon="💼", layout="wide")

# --- Load custom CSS ---
def load_custom_css(file_name: str):
    # Automatically find the CSS file path relative to this file
    css_path = os.path.join(os.path.dirname(__file__), file_name)
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Load CSS file
load_custom_css("style.css")

# --- Encode GIF as base64 ---
def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()


# --- Header ---
gif_base64 = get_base64_image("assets/briefcase.gif")

st.markdown(
    f"""
    <div style="text-align:center; margin-bottom: 0px;">
        <!--force refresh-->
        <img src="data:image/gif;base64,{gif_base64}"
             width="60"
             style="display:block; margin: 0 auto;" />
        <h1>Resume-to-Job Match Recommendation System</h1>
    </div>
    """,
    unsafe_allow_html=True
)
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
upload_container = st.container()

if uploaded_file:
    resume_text = extract_resume_text(uploaded_file)
    st.session_state["resume_file"] = uploaded_file
    st.session_state["resume_text"] = resume_text

    st.markdown(
    """
    <div style="
        display: inline-block;
        background: linear-gradient(90deg, #6ac5fe, #daf0ff);
        background-clip: text;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
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

else:
    # If user clicked X (deleted resume)
    if "resume_file" in st.session_state:
        # Clear resume data
        st.session_state.pop("resume_file", None)
        st.session_state.pop("resume_text", None)

        # Clear job matches too
        st.session_state.pop("recommendations", None)

        # Just visually refresh by clearing the container, not rerunning
        upload_container.empty()
        st.toast("Resume deleted.", icon="🗑️")

# --- Job matching section ---
if st.button("Find Matching Jobs", type="primary", use_container_width=True):
    if resume_text.strip():
        with st.spinner("🔍 Finding your best matches..."):
            # Use the recommender to get matches
            results_df = recommender.recommend(resume_text, embedder, top_k=50)
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
        job_url = getattr(row, 'url', '')

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

                # Apply job button
                if job_url and job_url.strip():
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown(
                        f"""
                        <style>
                        .apply-btn {{
                            background: linear-gradient(90deg, #6ac5fe, #daf0ff);
                            color: black !important;
                            border: none;
                            border-radius: 8px;
                            padding: 8px 18px;
                            font-size: 1em;
                            font-weight: 600;
                            cursor: pointer;
                            transition: all 0.3s ease;
                            box-shadow: 0 2px 8px rgba(106, 197, 254, 0.3);
                            text-decoration: none !important;
                            display: inline-block;
                        }}
                        .apply-btn:hover {{
                            background: linear-gradient(90deg, #daf0ff, #6ac5fe);
                            box-shadow: 0 4px 12px rgba(106, 197, 254, 0.5);
                            transform: translateY(-2px);
                            color: black !important;
                            text-decoration: none !important;
                        }}
                        </style>
                        <a href="{job_url}" target="_blank" class="apply-btn">Apply Now</a>
                        """,
                        unsafe_allow_html=True,
                    )

        st.markdown("<hr>", unsafe_allow_html=True)

    # --- Load more button or end message ---
    if visible_jobs < total_jobs:
        st.markdown("<br>", unsafe_allow_html=True)
        left, mid, right = st.columns([2, 1, 2])
        with mid:
            if st.button("Load more jobs ⤵", type="secondary", use_container_width=True):
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