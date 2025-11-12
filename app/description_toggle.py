import streamlit as st
from formatter import format_job_description
import re

def remove_ellipsis_sentences(text: str) -> str:
    """
    Remove any sentence-like chunk that contains '...' or '…'.
    Works for bullets or line breaks too.
    """
    # Split on sentence boundaries, line breaks, or bullets
    chunks = re.split(r'(?<=[.!?])\s+|[\r\n]+|•\s*', text)

    # Keep only sentences that do not contain three dots or unicode ellipsis
    kept = [c.strip() for c in chunks if c and not re.search(r'(?:\.{3,}|…)', c)]

    # Join back into a clean paragraph
    return ' '.join(kept).strip()



def render_job_description(display_job: str, idx: int):
    """
    Render the full job description
    """
    # Clean text to remove ellipsis fragments
    display_job = remove_ellipsis_sentences(display_job)

    # Format and render the full content
    formatted_content = format_job_description(display_job)
    st.markdown(formatted_content, unsafe_allow_html=True)