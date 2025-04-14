import streamlit as st
from PIL import Image
import os

# Set page config early
st.set_page_config(page_title="MOAMALATX Agent", layout="wide")

# === Sidebar Branding ===
with st.sidebar:
    moamalat_logo = Image.open("assets/moamalat.png")
    st.image(moamalat_logo, width=200, caption="معاملات")
    st.markdown("---")

# === Load WatsonX logo ===
watsonx_logo = Image.open("assets/watsonx.png")

# === Header Section ===
st.title("🤖 MOAMALATX Agent")
st.markdown("<hr>", unsafe_allow_html=True)

# === PDF Upload + Prompt Input ===
uploaded_file = st.file_uploader(
    "Upload a PDF to analyze", 
    type="pdf", 
    help="Only PDF files supported (max 200MB)"
)

prompt = st.text_area(
    "Enter your question or prompt about the document", 
    help="This prompt will guide the agent's analysis"
)

# === Run Analysis Button ===
if st.button("Run Analysis", disabled=not uploaded_file or not prompt):
    st.success(f"✅ Uploaded `{uploaded_file.name}` successfully.")
    st.info("Running CrewAI agents...")

    # Placeholder result
    st.markdown(f"""
    ## Analysis of `{uploaded_file.name}`
    - Prompt: **{prompt}**
    - 🧠 Agent Output: _(Markdown report coming soon...)_
    """)

# === Footer Logo ===
st.markdown("---")
footer_col = st.columns([3, 1])
with footer_col[1]:
    st.image(watsonx_logo, width=180, caption="Powered by WatsonX™")
