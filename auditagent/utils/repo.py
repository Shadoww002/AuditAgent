import os
import subprocess
import tempfile
import shutil
import urllib.parse
import socket
import ipaddress

MAX_REPO_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
ALLOWED_HOSTS = os.getenv("ALLOWED_REPO_HOSTS", "github.com,gitlab.com,bitbucket.org").split(",")

def is_safe_url(url: str) -> bool:
    if url.startswith("-"):
        return False
        
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https":
            return False
            
        if parsed.hostname not in ALLOWED_HOSTS:
            return False
            
        ip = socket.gethostbyname(parsed.hostname)
        ip_obj = ipaddress.ip_address(ip)
        
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local:
            return False
            
        return True
    except Exception:
        return False

def get_dir_size(path='.'):
    total = 0
    for entry in os.scandir(path):
        if entry.is_file():
            total += entry.stat().st_size
        elif entry.is_dir():
            total += get_dir_size(entry.path)
    return total

def clone_repo(url: str, dest_dir: str = None) -> str:
    """
    Clones a git repository to a secure isolated temporary directory.
    Returns the path to the cloned repository.
    """
    if not is_safe_url(url):
        raise ValueError("Invalid or unsafe repository URL.")
        
    # Force a temporary sandbox directory for safety
    if not dest_dir:
        dest_dir = tempfile.mkdtemp(prefix="auditagent_sandbox_")
    else:
        sandbox = tempfile.mkdtemp(prefix="auditagent_sandbox_")
        dest_dir = os.path.join(sandbox, os.path.basename(dest_dir))
        
    try:
        subprocess.run([
            "git", "clone", 
            "-c", "protocol.ext.allow=never", 
            "-c", "core.hooksPath=/dev/null", 
            "--depth", "1", 
            "--", url, dest_dir
        ], check=True, capture_output=True, text=True, timeout=30)
        
        size = get_dir_size(dest_dir)
        if size > MAX_REPO_SIZE_BYTES:
            raise RuntimeError("Repository exceeds maximum allowed size.")
            
        return dest_dir
    except subprocess.TimeoutExpired:
        shutil.rmtree(dest_dir, ignore_errors=True)
        raise RuntimeError("Clone timed out.")
    except (subprocess.CalledProcessError, RuntimeError) as e:
        shutil.rmtree(dest_dir, ignore_errors=True)
        raise RuntimeError(f"Failed to clone repository: {e}")

def cleanup_repo(repo_path: str):
    """Securely wipe the sandboxed repository after analysis."""
    if repo_path and os.path.exists(repo_path) and "auditagent_sandbox" in repo_path:
        shutil.rmtree(repo_path, ignore_errors=True)

def get_repo_files(repo_path: str) -> list[str]:
    """
    Returns a list of all files in the repository, excluding sensitive or large generated folders.
    """
    files = []
    skip_dirs = {'.git', 'node_modules', 'venv', '.venv', 'dist', 'build', '__pycache__'}
    for root, dirs, filenames in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for filename in filenames:
            files.append(os.path.join(root, filename))
    return files
