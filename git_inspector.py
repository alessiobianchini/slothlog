import subprocess
from pathlib import Path


def get_default_author(repo_path: Path | str) -> str:
    path = Path(repo_path)
    try:
        res = subprocess.run(
            ["git", "config", "user.email"],
            cwd=path,
            capture_output=True,
            text=True,
            check=True
        )
        email = res.stdout.strip()
        if email:
            return email
    except Exception:
        pass

    try:
        res = subprocess.run(
            ["git", "config", "user.name"],
            cwd=path,
            capture_output=True,
            text=True,
            check=True
        )
        return res.stdout.strip()
    except Exception:
        return ""


def get_current_branch(repo_path: Path | str) -> str:
    path = Path(repo_path)
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=path,
            capture_output=True,
            text=True,
            check=True
        )
        return res.stdout.strip()
    except Exception:
        return "main"


def inspect_repo(repo_path: Path | str, target_date: str, author: str | None = None) -> list[dict]:
    path = Path(repo_path)
    if not (path / ".git").exists() and not path.is_dir():
        return []

    branch = get_current_branch(path)

    cmd = [
        "git",
        "log",
        "-n",
        "500",
        "--format=%H|%aI|%an|%ae|%s",
        "--all",
        "--date-order"
    ]
    if author:
        cmd.append(f"--author={author}")

    try:
        res = subprocess.run(
            cmd,
            cwd=path,
            capture_output=True,
            text=True
        )
        if res.returncode != 0:
            return []
    except Exception:
        return []

    commits = []
    for line in res.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("|", 4)
        if len(parts) < 5:
            continue
        commit_hash, timestamp, author_name, author_email, message = parts
        
        # Exact date match on author ISO timestamp YYYY-MM-DD
        if timestamp.startswith(target_date):
            commits.append({
                "hash": commit_hash,
                "timestamp": timestamp,
                "author": author_name,
                "email": author_email,
                "branch": branch,
                "message": message,
                "repo": path.name
            })

    return commits
