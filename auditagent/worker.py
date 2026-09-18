import os
import datetime
import requests
from redis import Redis
from rq import Worker, Queue
from dotenv import load_dotenv

from auditagent.db import SessionLocal
from auditagent.models import ScanJob
from auditagent.graph import build_graph
from auditagent.utils.repo import clone_repo, cleanup_repo

load_dotenv()

redis_conn = Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379))
)

def execute_scan_job(job_id: str, repo_url: str):
    """
    Background task to run the LangGraph scan and update the SQLite DB.
    """
    db = SessionLocal()
    job = db.query(ScanJob).filter(ScanJob.id == job_id).first()
    
    if not job:
        db.close()
        return

    try:
        job.status = "cloning"
        db.commit()
        
        repo_path = None
        is_remote = repo_url.startswith("http://") or repo_url.startswith("https://") or repo_url.startswith("git@")
        
        if is_remote:
            repo_path = clone_repo(repo_url)
        else:
            repo_path = repo_url
            
        job.status = "running_agents"
        db.commit()
        
        workflow = build_graph()
        initial_state = {
            "repository_path": repo_path,
            "metadata": {},
            "findings": [],
            "verified_findings": [],
            "final_report": "",
            "errors": []
        }
        
        final_state = workflow.invoke(initial_state)
        
        job.status = "completed"
        job.report_text = final_state.get("final_report", "")
        job.completed_at = datetime.datetime.utcnow()
        db.commit()
        
    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        job.completed_at = datetime.datetime.utcnow()
        db.commit()
    finally:
        if job and job.webhook_url:
            try:
                payload = {
                    "job_id": job.id,
                    "status": job.status,
                    "report": job.report_text,
                    "error": job.error_message
                }
                requests.post(job.webhook_url, json=payload, timeout=10)
            except Exception as e:
                print(f"Webhook delivery failed: {e}")
        db.close()
        
        # Security Hardening: Cleanup sandbox
        if repo_path and is_remote:
            cleanup_repo(repo_path)

if __name__ == '__main__':
    worker = Worker(['audit_queue'], connection=redis_conn)
    worker.work()
