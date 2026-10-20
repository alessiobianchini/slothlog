import os
import tempfile
from pathlib import Path
import pytest

import db


@pytest.fixture(autouse=True)
def temp_db(monkeypatch):
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        test_db_path = Path(tmpdir) / "test_sloth.db"
        monkeypatch.setattr(db, "DB_FILE", test_db_path)
        db.init_db()
        yield test_db_path


def test_init_db():
    assert db.DB_FILE.exists()
    assert db.list_repos() == []
    assert db.get_timeslots("2026-10-20") == []


def test_repo_crud():
    raw_path = "/path/to/repo1"
    expected_path = str(Path(raw_path).resolve())
    r1 = db.add_repo(raw_path, "Project Alpha")
    assert r1["name"] == "Project Alpha"
    assert r1["path"] == expected_path
    assert "id" in r1

    repos = db.list_repos()
    assert len(repos) == 1
    assert repos[0]["id"] == r1["id"]

    # Deduplicate add
    r2 = db.add_repo(raw_path)
    assert r2["id"] == r1["id"]
    assert len(db.list_repos()) == 1

    # Toggle active
    assert db.toggle_repo_active(r1["id"], False) is True
    assert len(db.list_repos(active_only=True)) == 0
    assert len(db.list_repos(active_only=False)) == 1

    assert db.toggle_repo_active(r1["id"], True) is True
    assert len(db.list_repos(active_only=True)) == 1

    # Remove
    deleted = db.remove_repo(r1["id"])
    assert deleted is True
    assert db.list_repos() == []



def test_timeslot_crud():
    slot_data = {
        "date": "2026-10-20",
        "repo_path": "/path/to/repo1",
        "repo_name": "Project Alpha",
        "ticket_id": "AB#4920",
        "hours": 3.5,
        "summary": "Implemented OAuth callback handler and token refresh",
        "raw_commits": ["commit 1", "commit 2"]
    }
    saved = db.save_timeslot(slot_data)
    assert saved["ticket_id"] == "AB#4920"
    assert saved["hours"] == 3.5

    slots = db.get_timeslots("2026-10-20")
    assert len(slots) == 1
    assert slots[0]["ticket_id"] == "AB#4920"

    # Update
    updated = db.update_timeslot(saved["id"], hours=4.0, summary="Updated summary notes")
    assert updated is True

    slots_after = db.get_timeslots("2026-10-20")
    assert slots_after[0]["hours"] == 4.0

    # Add repo and deactivate it
    repo = db.add_repo("/path/to/repo1", "Project Alpha")
    db.toggle_repo_active(repo["id"], False)

    # When active_only=True, timeslots from inactive repos are excluded
    assert len(db.get_timeslots("2026-10-20", active_only=True)) == 0
    assert len(db.get_timeslots("2026-10-20", active_only=False)) == 1

    # Reactivate
    db.toggle_repo_active(repo["id"], True)
    assert len(db.get_timeslots("2026-10-20", active_only=True)) == 1

    # Rescanning/saving same date, repo, ticket updates existing without duplicate
    slot_duplicate = {
        "date": "2026-10-20",
        "repo_path": "/path/to/repo1",
        "ticket_id": "AB#4920",
        "hours": 5.0,
        "summary": "Updated hours and new commit",
        "raw_commits": ["commit 1", "commit 2", "commit 3"]
    }
    db.save_timeslot(slot_duplicate)
    slots_dedup = db.get_timeslots("2026-10-20", active_only=True)
    assert len(slots_dedup) == 1
    assert slots_dedup[0]["hours"] == 5.0

    # Delete timeslot
    assert db.delete_timeslot(slots_dedup[0]["id"]) is True
    assert len(db.get_timeslots("2026-10-20")) == 0



def test_seed_demo_data():
    db.seed_demo_data()
    slots = db.get_timeslots("2026-10-20")
    assert len(slots) >= 3
    assert any(s["ticket_id"] == "PROJ-104" for s in slots)
