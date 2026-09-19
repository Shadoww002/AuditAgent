import os
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

from auditagent.state import AuditState, Finding, VerifiedFinding
from auditagent.tools.retrieval import retriever
from auditagent.utils.cache import get_cache_key, get_from_cache, set_in_cache

class CriticDecision(BaseModel):
    status: str = Field(description="Must be 'verified', 'needs_manual_review', or 'false_positive'")
    justification: str = Field(description="Explanation of why this status was chosen")

def get_surrounding_code(repo_path: str, file_path: str, line_number: int, context_lines: int = 15) -> str:
    """Read surrounding code lines given a file path and line number."""
    if not repo_path or not file_path or not line_number:
        return "No specific snippet provided."
        
    full_path = os.path.join(repo_path, file_path)
    try:
        if not os.path.exists(full_path):
            return "File not found."
        with open(full_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        start = max(0, line_number - 1 - context_lines)
        end = min(len(lines), line_number + context_lines)
        return "".join(lines[start:end])
    except Exception as e:
        return f"Could not read snippet: {str(e)}"

def critic_agent_node(state: AuditState) -> Dict[str, Any]:
    """
    Verifies each finding by examining the actual code and context.
    """
    verified_findings = []
    repo_path = state.repository_path
    api_key = os.environ.get("GROQ_API_KEY")
    if api_key and api_key != "your_groq_api_key_here":
        llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0) # Using GPT OSS on Groq
        structured_llm = llm.with_structured_output(CriticDecision)
    else:
        structured_llm = None
        
    system_prompt = (
        "You are a senior security auditor. Your job is to verify a security finding.\n"
        "You will be given the finding details, the actual code snippet, and context about the vulnerability.\n"
        "1. If the finding is clearly valid based on the code, output 'verified'.\n"
        "2. If it looks like a test key, example code, or a false positive, output 'false_positive'.\n"
        "3. If you don't have enough context, output 'needs_manual_review'.\n"
        "Provide a clear justification."
    )

    for finding in state.findings:
        # Retrieve context
        retrieved_items = retriever.retrieve_context(finding.title + " " + finding.description)
        context_str = ""
        citations = []
        for i, item in enumerate(retrieved_items):
            context_str += f"[Source {i+1} - {item['source']}]: {item['content']}\n\n"
            citations.append(item['source'])
        
        # Get surrounding code
        if finding.line_number:
            snippet = get_surrounding_code(repo_path, finding.file_path, finding.line_number)
        else:
            snippet = finding.snippet or "No specific snippet provided."
            
        # Create fingerprint for caching
        fingerprint_content = f"{finding.source}|{finding.title}|{finding.file_path}|{snippet}"
        cache_key = get_cache_key("critic_decision", fingerprint_content)
        
        cached_decision = get_from_cache(cache_key)
        if cached_decision:
            verified_findings.append(
                VerifiedFinding(
                    original_finding=finding,
                    status=cached_decision["status"],
                    justification=cached_decision["justification"] + " (Cached)",
                    citations=citations
                )
            )
            continue
            
        prompt = (
            f"Finding: {finding.title}\n"
            f"Description: {finding.description}\n"
            f"Code Snippet:\n{snippet}\n\n"
            f"Context (OWASP/CVE):\n{context_str}\n"
        )
        
        try:
            if structured_llm:
                @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
                def _call_llm():
                    return structured_llm.invoke([
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=prompt)
                    ])
                
                decision = _call_llm()
                status = decision.status
                justification = decision.justification
                
                # Cache successful LLM decisions
                set_in_cache(cache_key, {"status": status, "justification": justification})
            else:
                status = "needs_manual_review"
                justification = "LLM verification bypassed because GROQ_API_KEY is not set in the environment."
                
            verified_findings.append(
                VerifiedFinding(
                    original_finding=finding,
                    status=status,
                    justification=justification,
                    citations=citations
                )
            )
        except Exception as e:
            # Fallback if LLM fails
            verified_findings.append(
                VerifiedFinding(
                    original_finding=finding,
                    status="needs_manual_review",
                    justification=f"LLM verification failed: {str(e)}"
                )
            )

    return {"verified_findings": verified_findings}
