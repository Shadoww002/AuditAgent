import os
import json
import subprocess
import uuid
from typing import Dict, Any
from auditagent.state import AuditState, Finding

def dependency_agent_node(state: dict) -> Dict[str, Any]:
    """
    Runs dependency scanning tools based on the detected package manager.
    """
    metadata = state.get("metadata", {})
    repo_path = state.get("repository_path", "")
    findings = []
    
    if metadata and metadata.get("package_manager") == "pip":
        # Run pip-audit
        try:
            req_file = os.path.join(repo_path, "requirements.txt")
            if os.path.exists(req_file):
                result = subprocess.run(
                    ["pip-audit", "-r", req_file, "-f", "json"],
                    capture_output=True,
                    text=True,
                    cwd=repo_path
                )
                
                # Even if pip-audit finds vulns (exit code != 0), it usually prints valid JSON to stdout
                if result.stdout:
                    try:
                        audit_data = json.loads(result.stdout)
                        for dep in audit_data.get("dependencies", []):
                            for vuln in dep.get("vulns", []):
                                findings.append(Finding(
                                    id=str(uuid.uuid4()),
                                    title=f"{vuln.get('id')} in {dep.get('name')}",
                                    description=vuln.get("fix_versions", "No fix available"),
                                    severity="HIGH", # pip-audit json doesn't always have severity, default to HIGH
                                    file_path="requirements.txt",
                                    source="dependency_agent",
                                    raw_output=json.dumps(vuln)
                                ))
                    except json.JSONDecodeError:
                        pass
        except FileNotFoundError:
            # pip-audit not installed
            pass

    return {"findings": findings}
