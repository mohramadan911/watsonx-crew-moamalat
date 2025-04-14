import streamlit as st
import boto3
import os
from dotenv import load_dotenv
from botocore.exceptions import BotoCoreError, NoCredentialsError, ClientError

# Load env vars
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

st.title("☁️ File Storage Configuration")

# Preload values from .env or use fallback
default_access_key = os.getenv("AWS_ACCESS_KEY_ID", "")
default_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "")
default_region = os.getenv("AWS_REGION", "eu-central-1")

# UI Inputs
access_key = st.text_input("AWS Access Key ID", value=default_access_key)
secret_key = st.text_input("AWS Secret Access Key", type="password", value=default_secret_key)
region = st.text_input("AWS Region", value=default_region)

bucket_list = []
buckets_loaded = False

# Attempt to list buckets only if keys are provided
if access_key and secret_key and region:
    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        bucket_response = s3.list_buckets()
        bucket_list = [bucket['Name'] for bucket in bucket_response['Buckets']]
        buckets_loaded = True
    except (BotoCoreError, ClientError, NoCredentialsError) as e:
        st.warning("⚠️ Could not load buckets. Check your AWS credentials and region.")

# Show dropdown if loaded, otherwise fallback
if buckets_loaded and bucket_list:
    bucket = st.selectbox("Select a Bucket", bucket_list)
else:
    bucket = st.text_input("Bucket Name (manual entry)")

# Save button
if st.button("Save S3 Settings"):
    st.session_state["s3_config"] = {
        "aws_access_key_id": access_key,
        "aws_secret_access_key": secret_key,
        "region": region,
        "bucket": bucket
    }
    st.success("✅ File Storage Configuration saved.")
