from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class RepositoryMetadata(BaseModel):
    path: str
    language: Optional[str] = None
    package_manager: Optional[str] = None
    framework: Optional[str] = None

class Finding(BaseModel):
    id: str
    title: str
    description: str
    severity: str # e.g., LOW, MEDIUM, HIGH, CRITICAL
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    source: str # e.g., "dependency_agent", "secrets_agent"
    raw_output: Optional[str] = None
    snippet: Optional[str] = None

class VerifiedFinding(BaseModel):
    original_finding: Finding
    status: str # "verified", "needs_manual_review", "false_positive"
    justification: str
    citations: List[str] = Field(default_factory=list)

class AuditState(BaseModel):
    repository_path: str
    metadata: Optional[RepositoryMetadata] = None
    findings: List[Finding] = Field(default_factory=list)
    verified_findings: List[VerifiedFinding] = Field(default_factory=list)
    final_report: Optional[str] = None
    errors: List[str] = Field(default_factory=list)

    # For LangGraph state merging (dict representation might be needed depending on graph setup)
