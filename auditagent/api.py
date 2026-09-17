from fastapi import FastAPI, Depends, HTTPException
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

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AuditAgent API")

redis_conn = Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379))
)
q = Queue('audit_queue', connection=redis_conn)

class ScanRequest(BaseModel):
    repo_url: str
    webhook_url: Optional[str] = None

@app.post("/api/v1/scan")
def trigger_scan(request: ScanRequest, db: Session = Depends(get_db)):
    job_id = str(uuid.uuid4())
    
    # Create job in database
    new_job = ScanJob(id=job_id, repo_url=request.repo_url, webhook_url=request.webhook_url, status="pending")
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
