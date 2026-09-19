from typing import List, Dict, Any, Optional, Annotated
import operator
from pydantic import BaseModel, Field

def reduce_list(left: list | None, right: list | None) -> list:
    if not left:
        left = []
    if not right:
        right = []
    return left + right

class RepositoryMetadata(BaseModel):
    path: str
    languages: List[str] = Field(default_factory=list)
    package_managers: List[str] = Field(default_factory=list)
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
    repository_path: str = ""
    metadata: Optional[RepositoryMetadata] = None
    findings: Annotated[List[Finding], reduce_list] = Field(default_factory=list)
    verified_findings: Annotated[List[VerifiedFinding], reduce_list] = Field(default_factory=list)
    final_report: str = ""
    errors: Annotated[List[str], reduce_list] = Field(default_factory=list)
