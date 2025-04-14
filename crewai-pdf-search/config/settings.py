"""
Configuration settings for the CrewAI project.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Ollama settings
OLLAMA_MODEL = os.getenv("MODEL", "ollama/gemma3:27b")
OLLAMA_API_BASE = os.getenv("API_BASE", "http://10.0.0.40:11434")

# Directory paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
OUTPUT_DIR = os.path.join(BASE_DIR, "output-files")

# PDF file path
PDF_FILE_PATH = os.path.join(DATASET_DIR, "sample.pdf")
PDF_URL = "https://www.hhs.gov/sites/default/files/sample-ce-notice-arabic.pdf"

# Ensure directories exist
os.makedirs(DATASET_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# LLM settings
DEFAULT_TEMPERATURE = 0.8
DEFAULT_MODEL = "gpt-4o"  # Change as needed
MAX_RPM = 100
MAX_ITERATIONS = 3

# Agent settings
VERBOSE = True