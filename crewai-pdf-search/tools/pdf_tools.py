from crewai_tools import PDFSearchTool
from config.settings import PDF_FILE_PATH, OLLAMA_MODEL, OLLAMA_API_BASE
import os

from crewai_tools import PDFSearchTool
from config.settings import PDF_FILE_PATH
import os

def initialize_pdf_search_tool(pdf_path=None):
    """
    Initialize the PDFSearchTool with a specific PDF path or use the default path.
    """
    # Get model name and API base from environment
    model_name = os.getenv("MODEL", "gemma3:27b").replace("ollama/", "")
    api_base = os.getenv("API_BASE", "http://10.0.0.40:11434")
    
    # Configure the tool to use Ollama for embeddings and LLM
    config = {
        "embedder": {
            "provider": "ollama",
            "config": {
                "model": model_name,
                "base_url": api_base
            }
        },
        "llm": {
            "provider": "ollama",
            "config": {
                "model": model_name,
                "base_url": api_base
            }
        }
    }
    
    if pdf_path:
        return PDFSearchTool(pdf=pdf_path, config=config)
    return PDFSearchTool(pdf=PDF_FILE_PATH, config=config)

# Default instance with the configured PDF path
pdf_search_tool = initialize_pdf_search_tool()