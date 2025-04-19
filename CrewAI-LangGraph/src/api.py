from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sqlite3
import os
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

# Import your existing components
from src.graph import WorkFlow
from src.nodes import Nodes

# Initialize FastAPI app
app = FastAPI(
    title="Email Processing API",
    description="API for processing emails using CrewAI and LangGraph",
    version="0.1.0"
)

# Global variables to track processing status
processing_status = {
    "is_running": False,
    "last_run": None,
    "processed_count": 0,
    "current_batch": []
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
        status TEXT
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

# Function to get job history - thread-safe version
def get_job_history():
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, start_time, end_time, emails_processed, status FROM api_runs ORDER BY id DESC LIMIT 5"
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
        
        # Create and run workflow
        workflow = WorkFlow()
        result = workflow.app.invoke({})
        
        # Extract processed emails
        emails_processed = 0
        if "emails" in result:
            emails_processed = len(result["emails"])
            processing_status["processed_count"] += emails_processed
            processing_status["current_batch"] = result["emails"]
        
        # Update job status
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE api_runs SET status = ?, end_time = CURRENT_TIMESTAMP, emails_processed = ? WHERE id = ?",
            ("completed", emails_processed, job_id)
        )
        conn.commit()
        conn.close()
        
    except Exception as e:
        # Update job status on error
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
        job_history=job_history
    )

# Add a root endpoint for better user experience
@app.get("/")
async def root():
    return {
        "message": "Email Processing API is running",
        "documentation": "/docs",
        "endpoints": [
            {"path": "/process-emails", "method": "POST", "description": "Start email processing"},
            {"path": "/status", "method": "GET", "description": "Check processing status"}
        ]
    }

# Run the API with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)