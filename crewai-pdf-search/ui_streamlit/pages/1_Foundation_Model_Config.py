import streamlit as st
import os
import json
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

st.title("🧠 Foundation Models Configuration")

model_provider = st.selectbox("Select model provider", ["ollama", "watsonx.ai"])

# Default values from .env or fallback
if model_provider == "ollama":
    default_model = os.getenv("OLLAMA_MODEL", "ollama/gemma2:27b")
    default_api_base = os.getenv("API_BASE", "http://10.0.0.40:11434")
    default_apikey = ""
    default_project_id = ""
    default_params = {"temperature": 0.8, "max_tokens": 1000}
elif model_provider == "watsonx.ai":
    default_model = os.getenv("WATSONX_MODEL", "watsonx/meta-llama/llama-3-1-70b-instruct")
    default_api_base = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
    default_apikey = os.getenv("WATSONX_API_KEY", "")
    default_project_id = os.getenv("WATSONX_PROJECT_ID", "")
    default_params = json.loads(os.getenv("WATSONX_MODEL_PARAMS", 
        '{"decoding_method":"sample", "max_new_tokens":500, "temperature":0.5}'))

# Input fields
model_name = st.text_input("Model name", value=default_model)
api_base = st.text_input("API base URL", value=default_api_base)
api_key = st.text_input("API key (if needed)", value=default_apikey, type="password")
project_id = st.text_input("Project ID (if needed)", value=default_project_id)

# Model parameters (shown in editable JSON format)
st.markdown("#### Model Parameters (JSON)")
model_params = st.text_area(
    "Advanced parameters", 
    value=json.dumps(default_params, indent=2),
    height=150
)

# Save logic
if st.button("Save Model Config"):
    try:
        parsed_params = json.loads(model_params)

        st.session_state["model_config"] = {
            "provider": model_provider,
            "model": model_name,
            "api_base": api_base,
            "api_key": api_key,
            "project_id": project_id,
            "params": parsed_params
        }

        st.success("✅ Model configuration saved and cached in session.")
    except json.JSONDecodeError:
        st.error("❌ Invalid JSON in model parameters.")
