from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import uuid
from typing import Dict

from auditagent.graph import build_graph
from auditagent.utils.repo import clone_repo

app = FastAPI(title="AuditAgent API")

# In-memory store for Stage 1 (Stage 3 uses Postgres)
jobs: Dict[str, dict] = {}

class ScanRequest(BaseModel):
    repo_url: str

def run_scan_job(job_id: str, repo_url: str):
    """Background task to run the LangGraph scan."""
    try:
        jobs[job_id]["status"] = "cloning"
        if repo_url.startswith("http://") or repo_url.startswith("https://") or repo_url.startswith("git@"):
            repo_path = clone_repo(repo_url)
        else:
            repo_path = repo_url
            
        jobs[job_id]["status"] = "running_agents"
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
        
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["report"] = final_state.get("final_report", "")
        
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)

@app.post("/api/v1/scan")
def trigger_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "pending", "repo": request.repo_url}
    
    background_tasks.add_task(run_scan_job, job_id, request.repo_url)
    
    return {"job_id": job_id, "status": "pending"}

@app.get("/api/v1/scan/{job_id}")
def get_scan_status(job_id: str):
    if job_id not in jobs:
        return {"error": "Job not found"}, 404
    return jobs[job_id]
