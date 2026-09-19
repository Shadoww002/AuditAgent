import requests
import time
import sys

API_URL = "http://localhost:8000/api/v1/scan"
REPO_URL = "https://github.com/octocat/Hello-World.git" 

print(f"Triggering scan for {REPO_URL}...")
try:
    response = requests.post(API_URL, json={"repo_url": REPO_URL})
    response.raise_for_status()
    data = response.json()
    job_id = data.get("job_id")
    print(f"Job started with ID: {job_id}")
except Exception as e:
    print(f"Failed to start job: {e}")
    sys.exit(1)

print("Polling for job completion...")
while True:
    try:
        status_response = requests.get(f"{API_URL}/{job_id}")
        status_data = status_response.json()
        status = status_data.get("status")
        print(f"Current status: {status}")
        
        if status in ["completed", "failed"]:
            print("\n" + "="*50)
            print("FINAL REPORT:")
            print("="*50)
            print(status_data.get("report") or status_data.get("error"))
            break
    except Exception as e:
        print(f"Error polling status: {e}")
    
    time.sleep(5)
