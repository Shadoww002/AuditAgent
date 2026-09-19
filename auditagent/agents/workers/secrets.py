import os
import re
import uuid
import math
import subprocess
from typing import Dict, Any
from auditagent.state import AuditState, Finding
from auditagent.utils.repo import get_repo_files

# Simplified regex for demo purposes. Real-world uses much more.
SECRET_PATTERNS = {
    "AWS Access Key": {"pattern": re.compile(r"AKIA[0-9A-Z]{16}"), "severity": "CRITICAL"},
    "Generic Secret": {"pattern": re.compile(r"(?i)(password|secret|api_key|apikey|token)[ \t]*[:=][ \t]*['\"]([^'\"]{10,})['\"]"), "severity": "HIGH"}
}

def shannon_entropy(data: str) -> float:
    """Calculates the Shannon entropy of a string."""
    if not data:
        return 0
    entropy = 0
    for x in set(data):
        p_x = float(data.count(x)) / len(data)
        entropy += - p_x * math.log2(p_x)
    return entropy

def check_line(line: str, file_path: str, line_no: int, source: str) -> list:
    findings = []
    for secret_type, config in SECRET_PATTERNS.items():
        pattern = config["pattern"]
        severity = config["severity"]
        match = pattern.search(line)
        if match:
            # For "Generic Secret", the actual secret is in group(2). For AWS, group(0)
            secret_str = match.group(2) if len(match.groups()) > 1 else match.group(0)
            
            # Entropy check to reduce false positives
            if shannon_entropy(secret_str) < 3.5:
                continue
                
            findings.append(Finding(
                id=str(uuid.uuid4()),
                title=f"Hardcoded {secret_type}",
                description=f"Found potential hardcoded secret matching {secret_type}",
                severity=severity,
                file_path=file_path,
                line_number=line_no,
                source=source,
                snippet=line.strip()
            ))
    return findings

def secrets_agent_node(state: AuditState) -> Dict[str, Any]:
    """
    Scans files and git history in the repository for hardcoded secrets.
    """
    repo_path = state.repository_path
    files = get_repo_files(repo_path)
    findings = []
    
    # Scan working tree
    for file_path in files:
        # Skip binary files or large files to prevent memory issues
        if not file_path.endswith(('.py', '.js', '.json', '.txt', '.md', '.yml', '.yaml', '.toml')):
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            for line_no, line in enumerate(content.splitlines(), start=1):
                rel_path = os.path.relpath(file_path, repo_path)
                findings.extend(check_line(line, rel_path, line_no, "secrets_agent_working_tree"))
        except Exception:
            # Ignore read errors for individual files
            continue
            
    # Scan git history
    try:
        # Run git log -p to get all patches in history
        result = subprocess.run(
            ["git", "log", "-p", "--all"],
            cwd=repo_path, capture_output=True, text=True, errors="replace"
        )
        if result.returncode == 0 and result.stdout:
            current_file = "Unknown"
            for line in result.stdout.splitlines():
                if line.startswith("+++ b/"):
                    current_file = line[6:]
                elif line.startswith("+") and not line.startswith("+++"):
                    # This is an added line in history
                    added_line = line[1:]
                    findings.extend(check_line(added_line, current_file, 0, "secrets_agent_git_history"))
    except Exception as e:
        return {"findings": findings, "errors": [f"Git history scan failed: {e}"]}
            
    return {"findings": findings}
