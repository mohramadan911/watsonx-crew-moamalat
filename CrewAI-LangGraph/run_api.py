#!/usr/bin/env python
"""
Run script for the Email Processing API service.
This is a simple wrapper to start the API service.
"""

import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def main():
    """Run the API service"""
    print("Starting Email Processing API service...")
    
    # Get port from environment variable or use default
    port = int(os.getenv("API_PORT", 8000))
    
    # Run the API with uvicorn - note the src.api instead of just api
    uvicorn.run(
        "src.api:app", 
        host="0.0.0.0", 
        port=port, 
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()