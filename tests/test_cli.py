import csv
import subprocess
import sys
import tempfile
from pathlib import Path
import pytest

import db


@pytest.fixture
def clean_db(monkeypatch):
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        test_db_path = Path(tmpdir) / "cli_test_sloth.db"
        monkeypatch.setattr(db, "DB_FILE", test_db_path)
        monkeypatch.setenv("SLOTHLOG_DB", str(test_db_path))
        db.init_db()
        yield test_db_path


def test_cli_repos_flow(clean_db):
    # Test repos add
    res_add = subprocess.run(
        [sys.executable, "cli.py", "repos", "add", "D:/Git/Ale/slothlog", "--name", "slothlog"],
        capture_output=True,
        text=True,
        check=True
    )
    assert "Added" in res_add.stdout or "slothlog" in res_add.stdout

    # Test repos list
    res_list = subprocess.run(
        [sys.executable, "cli.py", "repos", "list"],
        capture_output=True,
        text=True,
        check=True
    )
    assert "slothlog" in res_list.stdout
    assert "Active" in res_list.stdout

    # Get repo ID from list
    repo = db.list_repos()[0]

    # Deactivate repo
    res_toggle = subprocess.run(
        [sys.executable, "cli.py", "repos", "toggle", repo["id"], "--disable"],
        capture_output=True,
        text=True,
        check=True
    )
    assert "Deactivated" in res_toggle.stdout

    # Active list should be empty
    res_active = subprocess.run(
        [sys.executable, "cli.py", "repos", "list"],
        capture_output=True,
        text=True,
        check=True
    )
    assert "No repositories found" in res_active.stdout

    # List all should show it as Inactive
    res_all = subprocess.run(
        [sys.executable, "cli.py", "repos", "list", "--all"],
        capture_output=True,
        text=True,
        check=True
    )
    assert "Inactive" in res_all.stdout



def test_cli_export(clean_db, tmp_path):
    # Seed data
    db.seed_demo_data()
    csv_file = tmp_path / "test_out.csv"

    subprocess.run(
        [sys.executable, "cli.py", "export", "--date", "2026-10-20", "--output", str(csv_file)],
        capture_output=True,
        text=True,
        check=True
    )

    assert csv_file.exists()
    content = csv_file.read_text(encoding="utf-8")
    assert "Date,Repo,Ticket,Hours,Summary" in content
    assert "PROJ-104" in content


def test_cli_scan_empty(clean_db):
    res_scan = subprocess.run(
        [sys.executable, "cli.py", "scan"],
        capture_output=True,
        text=True,
        check=True
    )
    assert "No active repositories configured" in res_scan.stdout

