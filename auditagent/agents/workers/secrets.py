import os
import re
import uuid
from typing import Dict, Any
from auditagent.state import AuditState, Finding
from auditagent.utils.repo import get_repo_files

# Simplified regex for demo purposes. Real-world uses much more.
SECRET_PATTERNS = {
    "AWS Access Key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "Generic Secret": re.compile(r"(?i)(password|secret|api_key|apikey|token)[ \t]*[:=][ \t]*['\"]([^'\"]{10,})['\"]")
}

def secrets_agent_node(state: dict) -> Dict[str, Any]:
    """
    Scans files in the repository for hardcoded secrets.
    """
    repo_path = state.get("repository_path", "")
    files = get_repo_files(repo_path)
    findings = []
    
    for file_path in files:
        # Skip binary files or large files to prevent memory issues
        if not file_path.endswith(('.py', '.js', '.json', '.txt', '.md', '.yml', '.yaml', '.toml')):
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            for line_no, line in enumerate(content.splitlines(), start=1):
                for secret_type, pattern in SECRET_PATTERNS.items():
                    match = pattern.search(line)
                    if match:
                        rel_path = os.path.relpath(file_path, repo_path)
                        findings.append(Finding(
                            id=str(uuid.uuid4()),
                            title=f"Hardcoded {secret_type}",
                            description=f"Found potential hardcoded secret matching {secret_type}",
                            severity="CRITICAL",
                            file_path=rel_path,
                            line_number=line_no,
                            source="secrets_agent",
                            snippet=line.strip()
                        ))
        except Exception:
            # Ignore read errors for individual files
            continue
            
    return {"findings": findings}
