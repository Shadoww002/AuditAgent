import os
import sys
import pprint

# Ensure auditagent is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from auditagent.graph import build_graph

def run_eval():
    print("Starting Eval Suite...")
    
    dummy_repo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'dummy_repo'))
    print(f"Testing against dummy repo at: {dummy_repo_path}")
    
    workflow = build_graph()
    
    initial_state = {
        "repository_path": dummy_repo_path,
        "metadata": {},
        "findings": [],
        "verified_findings": [],
        "final_report": "",
        "errors": []
    }
    
    try:
        final_state = workflow.invoke(initial_state)
        
        print("\n--- TEST RESULTS ---")
        print(f"Total Raw Findings: {len(final_state.get('findings', []))}")
        print(f"Total Verified Findings: {len(final_state.get('verified_findings', []))}")
        
        print("\n--- FINAL REPORT ---")
        print(final_state.get("final_report", ""))
        
    except Exception as e:
        print(f"Eval suite failed with error: {e}")

if __name__ == "__main__":
    run_eval()
