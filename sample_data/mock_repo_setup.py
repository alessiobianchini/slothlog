"""Helper script to generate a sample local git repository with realistic commits for testing SlothLog.
"""
import os
import subprocess
import tempfile
from pathlib import Path


def create_mock_git_repo(dest_path: str):
    p = Path(dest_path).resolve()
    p.mkdir(parents=True, exist_ok=True)

    def run(cmd):
        subprocess.run(cmd, cwd=str(p), shell=True, check=True, capture_output=True)

    run("git init")
    run("git config user.name \"Demo Developer\"")
    run("git config user.email \"demo@example.com\"")

    commits = [
        ("feat(AB#4920): implement VAT calculation engine", "src/vat.py", "def calc_vat(amt): return amt * 0.22\n"),
        ("test(AB#4920): add unit test for reverse charge", "tests/test_vat.py", "def test_vat(): assert True\n"),
        ("fix(AB#4920): handle zero percent tax exemption", "src/vat.py", "def calc_vat(amt, zero=False): return 0 if zero else amt * 0.22\n"),
        ("chore: upgrade dependencies in pyproject", "pyproject.toml", "[tool.poetry]\nname = 'mock'\n"),
    ]

    for msg, rel_file, content in commits:
        file_path = p / rel_file
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        run(f"git add \"{rel_file}\"")
        run(f"git commit -m \"{msg}\"")

    print(f"Mock git repository successfully created at: {p}")
    print("You can now track it in SlothLog using:")
    print(f"  python cli.py repos add \"{p}\" --name mock-billing")


if __name__ == "__main__":
    target = Path(__file__).parent / "mock_git_repo"
    create_mock_git_repo(str(target))
