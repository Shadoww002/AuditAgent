import os
import json
import subprocess
import uuid
from typing import Dict, Any
from auditagent.state import AuditState, Finding

def dependency_agent_node(state: AuditState) -> Dict[str, Any]:
    """
    Runs dependency scanning tools based on the detected package manager.
    """
    metadata = state.metadata
    repo_path = state.repository_path
    findings = []
    
    if metadata and "pip" in metadata.package_managers:
        # Run pip-audit
        try:
            req_file = os.path.join(repo_path, "requirements.txt")
            if os.path.exists(req_file):
                result = subprocess.run(
                    ["pip-audit", "-r", req_file, "-f", "json", "--no-deps"],
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
                                try:
                                    fix_versions = vuln.get("fix_versions")
                                    if isinstance(fix_versions, list):
                                        fix_str = "Fix versions: " + ", ".join(fix_versions) if fix_versions else "No fix available"
                                    else:
                                        fix_str = str(fix_versions) if fix_versions else "No fix available"
                                        
                                    severity = vuln.get("severity", "HIGH")
                                    
                                    findings.append(Finding(
                                        id=str(uuid.uuid4()),
                                        title=f"{vuln.get('id')} in {dep.get('name')}",
                                        description=fix_str,
                                        severity=severity,
                                        file_path="requirements.txt",
                                        source="dependency_agent",
                                        raw_output=json.dumps(vuln)
                                    ))
                                except Exception as ve:
                                    pass # LangGraph reducers add to errors instead, but wait state is passed by value in LangGraph. Just return the error
                                    # state.errors.append(...) doesn't work well with dict reducers. It's better to just return the error.
                                    return {"errors": [f"Validation error in finding: {ve}"]}
                    except json.JSONDecodeError:
                        pass
        except FileNotFoundError:
            # pip-audit not installed
            pass

    return {"findings": findings}
