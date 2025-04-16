import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# Check and set environment variables explicitly
langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
if langsmith_api_key:
    # Set environment variables for langchain v2 tracing
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"  # Default endpoint
    os.environ["LANGCHAIN_API_KEY"] = langsmith_api_key
    os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "email-automation")
    
    print(f"LangSmith API key configured (length: {len(langsmith_api_key)})")
    print(f"LangSmith project: {os.environ['LANGCHAIN_PROJECT']}")
    print(f"LangSmith tracing: {os.environ['LANGCHAIN_TRACING_V2']}")
else:
    print("Warning: No LangSmith API key found in environment variables")

# Your existing imports
from src.graph import WorkFlow

# Initialize and run your workflow
app = WorkFlow().app
app.invoke({}, config={"recursion_limit": 100})