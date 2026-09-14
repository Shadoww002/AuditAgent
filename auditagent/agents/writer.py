from typing import Dict, Any
from auditagent.state import AuditState

def writer_agent_node(state: dict) -> Dict[str, Any]:
    """
    Takes the verified findings and generates a markdown report.
    """
    metadata = state.get("metadata", {})
    report_lines = [
        "# AuditAgent Security & Compliance Report",
        "",
        f"**Repository:** `{state.get('repository_path', '')}`",
        f"**Language:** `{metadata.get('language') if isinstance(metadata, dict) else metadata.language if metadata else 'Unknown'}`",
        "---",
        "## Verified Findings",
        ""
    ]
    
    verified_count = 0
    for vf in state.get("verified_findings", []):
        if vf.status == "verified":
            verified_count += 1
            f = vf.original_finding
            report_lines.append(f"### 🔴 [{f.severity}] {f.title}")
            report_lines.append(f"**Source:** {f.source} | **File:** `{f.file_path}:{f.line_number or ''}`")
            report_lines.append(f"\n**Description:** {f.description}")
            report_lines.append(f"\n**Auditor Justification:** {vf.justification}")
            if vf.citations:
                report_lines.append(f"\n**Reference:** *{vf.citations[0]}*")
            report_lines.append("\n---\n")
            
    if verified_count == 0:
        report_lines.append("No verified vulnerabilities found! 🎉")
        
    report_lines.append("## Needs Manual Review")
    report_lines.append("The following items could not be automatically verified by the Critic agent:\n")
    
    manual_count = 0
    for vf in state.get("verified_findings", []):
        if vf.status == "needs_manual_review":
            manual_count += 1
            f = vf.original_finding
            report_lines.append(f"- **{f.title}** in `{f.file_path}`: {vf.justification}")
            
    if manual_count == 0:
        report_lines.append("*None*")
        
    final_report = "\n".join(report_lines)
    return {"final_report": final_report}
