import os
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

from auditagent.state import AuditState, Finding, VerifiedFinding
from auditagent.tools.retrieval import retriever

class CriticDecision(BaseModel):
    status: str = Field(description="Must be 'verified', 'needs_manual_review', or 'false_positive'")
    justification: str = Field(description="Explanation of why this status was chosen")

def critic_agent_node(state: dict) -> Dict[str, Any]:
    """
    Verifies each finding by examining the actual code and context.
    """
    verified_findings = list(state.get("verified_findings", []))
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

    for finding in state.get("findings", []):
        # Retrieve context
        context = retriever.retrieve_context(finding.title + " " + finding.description)
        
        # In a full system, you would read the lines around finding.line_number
        snippet = finding.snippet or "No specific snippet provided."
        
        prompt = (
            f"Finding: {finding.title}\n"
            f"Description: {finding.description}\n"
            f"Code Snippet:\n{snippet}\n\n"
            f"Context (OWASP/CVE):\n{context}\n"
        )
        
        try:
            if structured_llm:
                decision = structured_llm.invoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=prompt)
                ])
                status = decision.status
                justification = decision.justification
            else:
                status = "needs_manual_review"
                justification = "LLM verification bypassed because GROQ_API_KEY is not set in the environment."
                
            verified_findings.append(
                VerifiedFinding(
                    original_finding=finding,
                    status=status,
                    justification=justification,
                    citations=[context.split('\n')[0]] # First line of context as citation
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
