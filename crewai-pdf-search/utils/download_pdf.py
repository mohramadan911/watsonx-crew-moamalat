"""
Utility to download the sample PDF.
"""
import os
import requests
from config.settings import DATASET_DIR, PDF_URL, PDF_FILE_PATH

def download_sample_pdf(url=PDF_URL, file_path=PDF_FILE_PATH):
    """
    Download a sample PDF file from the specified URL.
    
    Args:
        url (str, optional): URL of the PDF file. Defaults to PDF_URL from settings.
        file_path (str, optional): Path to save the PDF file. Defaults to PDF_FILE_PATH from settings.
        
    Returns:
        str: Path to the downloaded PDF file.
    """
    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Check if the file already exists
    if os.path.exists(file_path):
        print(f"PDF file already exists at: {file_path}")
        return file_path
    
    # Download the PDF file
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for HTTP errors
    
    # Save the PDF file
    with open(file_path, 'wb') as file:
        file.write(response.content)
    
    print(f"PDF file downloaded and saved to: {file_path}")
    return file_path

if __name__ == "__main__":
    download_sample_pdf()