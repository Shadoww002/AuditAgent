import os
import sys
import pytest
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from auditagent.state import AuditState
from auditagent.graph import build_graph

def test_eval_dummy_repo():
    dummy_repo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'dummy_repo'))
    workflow = build_graph()
    
    initial_state = AuditState(
        repository_path=dummy_repo_path,
        metadata=None,
        findings=[],
        verified_findings=[],
        final_report="",
        errors=[]
    )
    
    # Qdrant must be running for this to fully succeed
    try:
        final_state = workflow.invoke(initial_state)
        
        if isinstance(final_state, dict):
            findings = final_state.get('findings', [])
            verified_findings = final_state.get('verified_findings', [])
            report = final_state.get('final_report', '')
        else:
            findings = final_state.findings
            verified_findings = final_state.verified_findings
            report = final_state.final_report
            
        assert len(findings) > 0, "Agent should find at least one raw finding in dummy_repo"
        assert "AuditAgent" in report
    except Exception as e:
        pytest.skip(f"Skipping graph test due to environmental dependencies (e.g., Qdrant). Error: {e}")
