from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sqlite3
import os
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request

CREW_LOGS = []
templates = Jinja2Templates(directory="src/templates")




# Import your existing components
from src.graph import WorkFlow
from src.nodes import Nodes

# Initialize FastAPI app
app = FastAPI(
    title="Email Processing API",
    description="API for processing emails using CrewAI and LangGraph",
    version="0.1.0"
)

from fastapi import APIRouter

@app.post("/test-integration")
def test_integration():
    test_email = {
        "id": "test-id",
        "threadId": "test-thread-id",
        "subject": "Test Email for Dry Run",
        "body": "This is a dry-run payload to validate integration logic and external API behavior.",
        "attachments": []  # no file
    }

    from src.integration import EmailIntegration
    integration = EmailIntegration()
    result = integration.send_to_external_api(test_email)
    return result

@app.get("/status/ui", response_class=HTMLResponse)
async def view_status(request: Request):
    return templates.TemplateResponse("status.html", {
        "request": request,
        "crew_logs": CREW_LOGS,
        "payload": processing_status.get("final_payload", {})
    })

# Global variables to track processing status
processing_status = {
    "is_running": False,
    "last_run": None,
    "processed_count": 0,
    "current_batch": [],
    "integration_results": None  # Added field to track integration results
}

# Initialize database
db_path = "email_processing.db"
nodes = Nodes()  # Assuming this initializes the database

# Create thread tracking table if not exists
def init_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS api_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_time TIMESTAMP,
        emails_processed INTEGER DEFAULT 0,
        status TEXT,
        integration_success INTEGER DEFAULT 0
    )
    ''')
    conn.commit()
    conn.close()

init_db()

# Models for API
class ProcessingResponse(BaseModel):
    job_id: int
    status: str
    start_time: str
    message: str

class StatusResponse(BaseModel):
    is_running: bool
    last_run: Optional[str] = None
    processed_count: int
    current_batch: List[Dict[str, Any]] = []
    job_history: List[Dict[str, Any]] = []
    integration_results: Optional[Dict[str, Any]] = None  # Added field

# Function to get job history - thread-safe version
def get_job_history():
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, start_time, end_time, emails_processed, status, integration_success FROM api_runs ORDER BY id DESC LIMIT 5"
        )
        return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error fetching job history: {str(e)}")
        return []
    finally:
        if conn:
            conn.close()

# Function to run the email processing workflow
def process_emails_task():
    global processing_status
    
    # Create new run record
    conn = None
    job_id = None
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO api_runs (status) VALUES (?)", 
            ("running",)
        )
        job_id = cursor.lastrowid
        conn.commit()
    except Exception as e:
        print(f"Error creating job record: {str(e)}")
        if conn:
            conn.close()
        return
    finally:
        if conn:
            conn.close()
    
    try:
        # Update status
        processing_status["is_running"] = True
        processing_status["last_run"] = datetime.now().isoformat()
        processing_status["current_batch"] = []
        processing_status["integration_results"] = None
        
        # Create and run workflow with empty initial state
        # The workflow will check for emails internally
        workflow = WorkFlow()
        
        # Pass an empty dictionary as the initial state
        # and set a reasonable recursion limit
        result = workflow.app.invoke({}, config={"recursion_limit": 100})
        
        CREW_LOGS.clear()
        CREW_LOGS.extend(result.get("crew_logs", ["No logs found"]))
        processing_status["final_payload"] = result.get("final_payload", {})
        # Extract processed emails
        emails_processed = 0
        if result and "emails" in result:
            emails_processed = len(result.get("emails", []))
            processing_status["processed_count"] += emails_processed
            processing_status["current_batch"] = result.get("emails", [])
        
        # Extract integration results if available
        integration_results = result.get("integration_results", None)
        # Simulate capturing CrewAI agent logs & payload
        processing_status["crew_logs"] = result.get("crew_logs", ["Log not available"])  # Example
        processing_status["final_payload"] = result.get("final_payload", {})  # Example

        processing_status["integration_results"] = integration_results
        
        # Determine integration success
        integration_success = 0
        if integration_results and integration_results.get("success", False):
            integration_success = 1
        
        # Update job status
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE api_runs SET status = ?, end_time = CURRENT_TIMESTAMP, emails_processed = ?, integration_success = ? WHERE id = ?",
            ("completed", emails_processed, integration_success, job_id)
        )
        conn.commit()
        conn.close()
        
        print(f"Job completed. Processed {emails_processed} emails. Integration success: {integration_success}")
        
    except Exception as e:
        # Update job status on error
        print(f"Error in process_emails_task: {str(e)}")
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE api_runs SET status = ?, end_time = CURRENT_TIMESTAMP WHERE id = ?",
                (f"error: {str(e)}", job_id)
            )
            conn.commit()
            conn.close()
        except Exception as db_error:
            print(f"Error updating job status: {str(db_error)}")
        
    finally:
        # Reset running state
        processing_status["is_running"] = False


# API endpoints
@app.post("/process-emails", response_model=ProcessingResponse)
async def start_processing(background_tasks: BackgroundTasks):
    # Check if already running
    if processing_status["is_running"]:
        raise HTTPException(status_code=409, detail="Email processing task is already running")
    
    # Start processing in background
    background_tasks.add_task(process_emails_task)
    
    # Get the job ID
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, start_time FROM api_runs ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        job_id = row[0] if row else 0
        start_time = row[1] if row else datetime.now().isoformat()
    except Exception as e:
        print(f"Error fetching job ID: {str(e)}")
        job_id = 0
        start_time = datetime.now().isoformat()
    finally:
        if conn:
            conn.close()
    
    return ProcessingResponse(
        job_id=job_id,
        status="started",
        start_time=start_time,
        message="Email processing has been started in the background"
    )

@app.get("/status", response_model=StatusResponse)
async def get_status():
    # Get job history in a thread-safe way
    job_history = get_job_history()
    
    return StatusResponse(
        is_running=processing_status["is_running"],
        last_run=processing_status["last_run"],
        processed_count=processing_status["processed_count"],
        current_batch=processing_status["current_batch"],
        job_history=job_history,
        integration_results=processing_status["integration_results"]  # Include integration results
    )

# Add an endpoint to get just the integration results
@app.get("/integration-results")
async def get_integration_results():
    """Get the results of the most recent integration"""
    
    if processing_status["integration_results"] is None:
        return {
            "message": "No integration results available",
            "results": None
        }
    
    return {
        "message": "Integration results retrieved successfully",
        "results": processing_status["integration_results"]
    }

# Add a root endpoint for better user experience
@app.get("/")
async def root():
    return {
        "message": "Email Processing API is running",
        "documentation": "/docs",
        "endpoints": [
            {"path": "/process-emails", "method": "POST", "description": "Start email processing"},
            {"path": "/status", "method": "GET", "description": "Check processing status (JSON)"},
            {"path": "/status/ui", "method": "GET", "description": "View logs and payload in browser"},
            {"path": "/integration-results", "method": "GET", "description": "Get integration results"}
        ]
    }


# Run the API with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)