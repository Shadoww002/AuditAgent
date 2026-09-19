from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from typing import Dict, Optional
import uuid
import os
from redis import Redis
from rq import Queue
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv() # Load environment variables

from auditagent.db import SessionLocal, engine, get_db
from auditagent.models import Base, ScanJob
from auditagent.worker import execute_scan_job
from auditagent.utils.repo import is_safe_url

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AuditAgent API")

redis_conn = Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379))
)
q = Queue('audit_queue', connection=redis_conn)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

def get_api_key(api_key: str = Security(api_key_header)):
    expected_api_key = os.getenv("AUDITAGENT_API_KEY", "default-dev-key")
    if api_key == expected_api_key:
        return api_key
    raise HTTPException(status_code=403, detail="Could not validate credentials")

class ScanRequest(BaseModel):
    repo_url: str
    webhook_url: Optional[str] = None

MAX_CONCURRENT_JOBS = int(os.getenv("MAX_CONCURRENT_JOBS", "5"))

@app.post("/api/v1/scan")
def trigger_scan(request: ScanRequest, db: Session = Depends(get_db), api_key: str = Depends(get_api_key)):
    if not is_safe_url(request.repo_url):
        raise HTTPException(status_code=400, detail="Invalid or unsafe repo_url")
        
    if request.webhook_url and not is_safe_url(request.webhook_url):
        raise HTTPException(status_code=400, detail="Invalid or unsafe webhook_url")
        
    # Check concurrent job cap
    active_jobs = db.query(ScanJob).filter(
        ScanJob.api_key == api_key,
        ScanJob.status.in_(["pending", "cloning", "running_agents"])
    ).count()
    
    if active_jobs >= MAX_CONCURRENT_JOBS:
        raise HTTPException(status_code=429, detail="Too many concurrent jobs running.")
        
    job_id = str(uuid.uuid4())
    
    # Create job in database
    new_job = ScanJob(id=job_id, repo_url=request.repo_url, webhook_url=request.webhook_url, status="pending", api_key=api_key)
    db.add(new_job)
    db.commit()
    
    # Enqueue task in Redis
    q.enqueue(execute_scan_job, job_id, request.repo_url, job_timeout='1h')
    
    return {"job_id": job_id, "status": "pending"}

@app.get("/api/v1/scan/{job_id}")
def get_scan_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(ScanJob).filter(ScanJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return {
        "job_id": job.id,
        "repo_url": job.repo_url,
        "status": job.status,
        "report": job.report_text,
        "error": job.error_message,
        "created_at": job.created_at,
        "completed_at": job.completed_at
    }
