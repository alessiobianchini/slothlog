import subprocess
import tempfile
from pathlib import Path
import pytest

import git_inspector


@pytest.fixture
def mock_git_repo():
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_dir = Path(tmpdir)
        # Initialize git repo
        subprocess.run(["git", "init", "-b", "main"], cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test Developer"], cwd=repo_dir, check=True)
        subprocess.run(["git", "config", "user.email", "dev@example.com"], cwd=repo_dir, check=True)

        # Commit 1 on 2026-10-20
        f1 = repo_dir / "file1.txt"
        f1.write_text("hello 1")
        subprocess.run(["git", "add", "file1.txt"], cwd=repo_dir, check=True)
        env1 = {"GIT_AUTHOR_DATE": "2026-10-20T09:15:00+02:00", "GIT_COMMITTER_DATE": "2026-10-20T09:15:00+02:00"}
        subprocess.run(["git", "commit", "-m", "feat(PROJ-101): initial commit"], cwd=repo_dir, check=True, env={**subprocess.os.environ, **env1})

        # Commit 2 on 2026-10-20
        f2 = repo_dir / "file2.txt"
        f2.write_text("hello 2")
        subprocess.run(["git", "add", "file2.txt"], cwd=repo_dir, check=True)
        env2 = {"GIT_AUTHOR_DATE": "2026-10-20T11:30:00+02:00", "GIT_COMMITTER_DATE": "2026-10-20T11:30:00+02:00"}
        subprocess.run(["git", "commit", "-m", "fix(PROJ-101): resolve login edge case"], cwd=repo_dir, check=True, env={**subprocess.os.environ, **env2})

        # Commit 3 on 2026-10-19 (previous day)
        f3 = repo_dir / "file3.txt"
        f3.write_text("hello 3")
        subprocess.run(["git", "add", "file3.txt"], cwd=repo_dir, check=True)
        env3 = {"GIT_AUTHOR_DATE": "2026-10-19T16:00:00+02:00", "GIT_COMMITTER_DATE": "2026-10-19T16:00:00+02:00"}
        subprocess.run(["git", "commit", "-m", "chore: setup repo yesterday"], cwd=repo_dir, check=True, env={**subprocess.os.environ, **env3})

        yield repo_dir


def test_get_default_author(mock_git_repo):
    author = git_inspector.get_default_author(mock_git_repo)
    assert author == "dev@example.com" or author == "Test Developer"


def test_inspect_repo_filter_date(mock_git_repo):
    commits_today = git_inspector.inspect_repo(mock_git_repo, target_date="2026-10-20")
    assert len(commits_today) == 2
    assert commits_today[0]["message"] == "fix(PROJ-101): resolve login edge case"
    assert commits_today[1]["message"] == "feat(PROJ-101): initial commit"
    assert "PROJ-101" in commits_today[0]["message"]

    commits_yesterday = git_inspector.inspect_repo(mock_git_repo, target_date="2026-10-19")
    assert len(commits_yesterday) == 1
    assert "yesterday" in commits_yesterday[0]["message"]


def test_inspect_repo_author_filter(mock_git_repo):
    # Match author
    commits = git_inspector.inspect_repo(mock_git_repo, target_date="2026-10-20", author="dev@example.com")
    assert len(commits) == 2

    # Unmatched author
    empty = git_inspector.inspect_repo(mock_git_repo, target_date="2026-10-20", author="other@example.com")
    assert len(empty) == 0
