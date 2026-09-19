import os
from typing import Dict, Any
from auditagent.state import AuditState, RepositoryMetadata

def planner_node(state: AuditState) -> Dict[str, Any]:
    """
    Analyzes the repository to detect languages and package managers,
    and updates the state metadata.
    """
    repo_path = state.repository_path
    
    # Basic heuristic-based detection
    has_requirements = os.path.exists(os.path.join(repo_path, "requirements.txt"))
    has_pyproject = os.path.exists(os.path.join(repo_path, "pyproject.toml"))
    has_package_json = os.path.exists(os.path.join(repo_path, "package.json"))
    has_cargo = os.path.exists(os.path.join(repo_path, "Cargo.toml"))
    
    languages = []
    package_managers = []
    
    if has_requirements or has_pyproject:
        languages.append("python")
        if has_requirements:
            package_managers.append("pip")
        if has_pyproject:
            package_managers.append("poetry") # simplified
            
    if has_package_json:
        languages.append("javascript")
        package_managers.append("npm")
        
    if has_cargo:
        languages.append("rust")
        package_managers.append("cargo")
        
    metadata = RepositoryMetadata(
        path=repo_path,
        languages=languages if languages else ["unknown"],
        package_managers=package_managers if package_managers else ["unknown"]
    )
    
    return {"metadata": metadata}
