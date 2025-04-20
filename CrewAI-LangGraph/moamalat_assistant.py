import streamlit as st
import requests
import json
import os
from io import BytesIO

# Backend base URL (update if deployed externally)
API_BASE_URL = "http://localhost:8000"

st.set_page_config(page_title="Moamalat Assistant 🤖", layout="centered")
st.title("📥 Moamalat Assistant")
st.markdown("Chat with your email integration assistant. Dry-run email payloads or test file attachments.")

# Chat history state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Show messages
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Input from user
prompt = st.chat_input("Ask the assistant (e.g., dry-run test, attach a file)...")

def send_test_payload(fake_attachment: bool = False, uploaded_file=None):
    url = f"{API_BASE_URL}/test-integration"
    payload = None

    if fake_attachment:
        url = f"{API_BASE_URL}/test-integration-with-attachment"
    elif uploaded_file:
        # Convert file content to base64
        file_bytes = uploaded_file.read()
        encoded_file = file_bytes.encode('base64') if hasattr(file_bytes, 'encode') else BytesIO(file_bytes).getvalue()
        payload = {
            "subject": "Test Email with Real Uploaded Attachment",
            "confidentialityId": "0",
            "externalNo": "197",
            "remarks": "Payload test with real uploaded file.",
            "externalUnit": "1",
            "attachment": encoded_file
        }

    try:
        if payload:
            res = requests.post(url, json=payload)
        else:
            res = requests.post(url)
        return res.json()
    except Exception as e:
        return {"error": str(e)}

if prompt:
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    lower_prompt = prompt.lower()

    # Determine action
    if "fake" in lower_prompt:
        response = send_test_payload(fake_attachment=True)
        result_text = f"✅ Fake attachment test sent.\n\n```json\n{json.dumps(response, indent=2)}\n```"
    elif "file" in lower_prompt:
        uploaded_file = st.file_uploader("📎 Upload a file", type=None)
        if uploaded_file:
            response = send_test_payload(uploaded_file=uploaded_file)
            result_text = f"📤 Uploaded file sent.\n\n```json\n{json.dumps(response, indent=2)}\n```"
        else:
            result_text = "⚠️ Please upload a file first."
    else:
        response = send_test_payload()
        result_text = f"✅ Dry-run test executed.\n\n```json\n{json.dumps(response, indent=2)}\n```"

    st.chat_message("assistant").markdown(result_text)
    st.session_state.messages.append({"role": "assistant", "content": result_text})
