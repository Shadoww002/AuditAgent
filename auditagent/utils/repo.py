import os
import subprocess
import tempfile

def clone_repo(url: str, dest_dir: str = None) -> str:
    """
    Clones a git repository to a local directory.
    If dest_dir is not provided, creates a temporary directory.
    Returns the path to the cloned repository.
    """
    if not dest_dir:
        dest_dir = tempfile.mkdtemp(prefix="auditagent_repo_")
        
    try:
        subprocess.run(["git", "clone", url, dest_dir], check=True, capture_output=True, text=True)
        return dest_dir
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to clone repository: {e.stderr}")

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
