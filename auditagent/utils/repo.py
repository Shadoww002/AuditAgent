import os
import subprocess
import tempfile
import shutil

def clone_repo(url: str, dest_dir: str = None) -> str:
    """
    Clones a git repository to a secure isolated temporary directory.
    Returns the path to the cloned repository.
    """
    # Force a temporary sandbox directory for safety
    if not dest_dir:
        dest_dir = tempfile.mkdtemp(prefix="auditagent_sandbox_")
    else:
        sandbox = tempfile.mkdtemp(prefix="auditagent_sandbox_")
        dest_dir = os.path.join(sandbox, os.path.basename(dest_dir))
        
    try:
        subprocess.run(["git", "clone", url, dest_dir], check=True, capture_output=True, text=True)
        return dest_dir
    except subprocess.CalledProcessError as e:
        shutil.rmtree(dest_dir, ignore_errors=True)
        raise RuntimeError(f"Failed to clone repository: {e.stderr}")

def cleanup_repo(repo_path: str):
    """Securely wipe the sandboxed repository after analysis."""
    if repo_path and os.path.exists(repo_path) and "auditagent_sandbox" in repo_path:
        shutil.rmtree(repo_path, ignore_errors=True)

def get_repo_files(repo_path: str) -> list[str]:
    """
    Returns a list of all files in the repository, excluding .git folder.
    """
    files = []
    for root, _, filenames in os.walk(repo_path):
        if '.git' in root:
            continue
        for filename in filenames:
            files.append(os.path.join(root, filename))
    return files
