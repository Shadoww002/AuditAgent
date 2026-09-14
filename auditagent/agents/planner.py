import os
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from auditagent.state import AuditState, RepositoryMetadata

def planner_node(state: dict) -> Dict[str, Any]:
    """
    Analyzes the repository to detect languages and package managers,
    and updates the state metadata.
    """
    repo_path = state.get("repository_path", "")
    
    # Basic heuristic-based detection
    has_requirements = os.path.exists(os.path.join(repo_path, "requirements.txt"))
    has_pyproject = os.path.exists(os.path.join(repo_path, "pyproject.toml"))
    has_package_json = os.path.exists(os.path.join(repo_path, "package.json"))
    has_cargo = os.path.exists(os.path.join(repo_path, "Cargo.toml"))
    
    language = "unknown"
    package_manager = "unknown"
    
    if has_requirements or has_pyproject:
        language = "python"
        package_manager = "pip" if has_requirements else "poetry" # simplified
    elif has_package_json:
        language = "javascript"
        package_manager = "npm"
    elif has_cargo:
        language = "rust"
        package_manager = "cargo"
        
    metadata = {
        "path": repo_path,
        "language": language,
        "package_manager": package_manager
    }
    
    return {"metadata": metadata}
