import streamlit as st
import os
from PIL import Image
from dotenv import load_dotenv

# Load .env from parent directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

email_logo = Image.open("assets/ms.png")
logo_left, logo_right = st.columns([1, 1])

with logo_left:
    st.image(email_logo, width=160, caption="Email")

st.title("📧 Email (MS365) Settings")


# Load from .env or fallback
default_email = os.getenv("MS_USER_EMAIL", "")
default_client_id = os.getenv("MS_CLIENT_ID", "")
default_client_secret = os.getenv("MS_CLIENT_SECRET", "")
default_tenant_id = os.getenv("MS_TENANT_ID", "")
default_interval = 5

# UI inputs
email_user = st.text_input("Email address", value=default_email)
client_id = st.text_input("Client ID", value=default_client_id)
client_secret = st.text_input("Client Secret", type="password", value=default_client_secret)
tenant_id = st.text_input("Tenant ID", value=default_tenant_id)
scan_sender = st.text_input("Sender to filter (e.g. compliance@example.com)")
interval = st.number_input("Scan interval (mins)", min_value=1, value=default_interval)

# Save button
if st.button("Save Email Settings"):
    st.session_state["email_config"] = {
        "user_email": email_user,
        "client_id": client_id,
        "client_secret": client_secret,
        "tenant_id": tenant_id,
        "scan_sender": scan_sender,
        "interval_minutes": interval
    }
    st.success("✅ Email settings saved.")
