import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

import db


@pytest.fixture
def clean_db(monkeypatch):
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        test_db_path = Path(tmpdir) / "server_test_sloth.db"
        monkeypatch.setattr(db, "DB_FILE", test_db_path)
        monkeypatch.setenv("SLOTHLOG_DB", str(test_db_path))
        db.init_db()
        yield test_db_path


def test_ping_endpoint():
    from server import app
    client = TestClient(app)
    response = client.get("/api/ping")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "app": "slothlog"}


def test_root_serves_html():
    from server import app
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "SlothLog" in response.text


def test_repos_api(clean_db):
    from server import app
    client = TestClient(app)

    # List repos (should be empty initially)
    resp = client.get("/api/repos")
    assert resp.status_code == 200
    assert resp.json() == []

    # Add repo
    resp_add = client.post("/api/repos", json={"path": "D:/Git/Ale/slothlog", "name": "slothlog"})
    assert resp_add.status_code == 200
    data = resp_add.json()
    assert data["name"] == "slothlog"
    repo_id = data["id"]

    # List again
    resp_list = client.get("/api/repos")
    assert len(resp_list.json()) == 1

    # Toggle active to false
    resp_toggle = client.patch(f"/api/repos/{repo_id}", json={"active": False})
    assert resp_toggle.status_code == 200
    assert resp_toggle.json()["active"] is False

    # List active only should be 0
    resp_active = client.get("/api/repos")
    assert len(resp_active.json()) == 0

    # List including inactive should be 1
    resp_all = client.get("/api/repos?include_inactive=true")
    assert len(resp_all.json()) == 1

    # Toggle back to true
    resp_toggle_back = client.patch(f"/api/repos/{repo_id}", json={"active": True})
    assert resp_toggle_back.status_code == 200
    assert len(client.get("/api/repos").json()) == 1

    # Remove repo
    resp_del = client.delete(f"/api/repos/{repo_id}")
    assert resp_del.status_code == 200
    assert resp_del.json()["ok"] is True



def test_timeslots_and_export(clean_db):
    from server import app
    client = TestClient(app)

    # Seed demo data
    db.seed_demo_data()

    # Get timeslots
    resp = client.get("/api/timeslots?date=2026-10-20")
    assert resp.status_code == 200
    slots = resp.json()["timeslots"]
    assert len(slots) >= 3
    first_id = slots[0]["id"]

    # Update timeslot
    resp_up = client.put(f"/api/timeslots/{first_id}", json={"hours": 4.5, "summary": "Updated summary text"})
    assert resp_up.status_code == 200

    # Verify update persisted
    resp_after = client.get("/api/timeslots?date=2026-10-20")
    matching = [s for s in resp_after.json()["timeslots"] if s["id"] == first_id]
    assert matching[0]["hours"] == 4.5
    assert matching[0]["summary"] == "Updated summary text"

    # Export CSV
    resp_csv = client.get("/api/export?date=2026-10-20")
    assert resp_csv.status_code == 200
    assert "text/csv" in resp_csv.headers["content-type"]
    assert "Date,Repo,Ticket,Hours,Summary" in resp_csv.text
    assert "PROJ-104" in resp_csv.text

    # Delete timeslot endpoint
    resp_del_slot = client.delete(f"/api/timeslots/{first_id}")
    assert resp_del_slot.status_code == 200
    assert resp_del_slot.json()["ok"] is True



def test_sentry_debug_route():
    from server import app
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/sentry-debug")
    assert resp.status_code == 500


def test_scan_endpoint_flow(clean_db, monkeypatch):
    import git_inspector
    from server import app
    client = TestClient(app)

    # Register a repo
    client.post("/api/repos", json={"path": "D:/dummy/repo", "name": "dummy-repo"})

    # Mock inspect_repo to return commits
    fake_commits = [
        {
            "hash": "abc123",
            "timestamp": "2026-10-20T10:00:00+02:00",
            "author": "Alessio",
            "branch": "main",
            "message": "feat(AB#5555): initial commit",
            "repo": "dummy-repo"
        }
    ]
    monkeypatch.setattr(git_inspector, "inspect_repo", lambda *args, **kwargs: fake_commits)

    resp = client.get("/api/scan?date=2026-10-20")
    assert resp.status_code == 200
    data = resp.json()
    assert data["generated_timeslots"] >= 1
    tickets = [t["ticket_id"] for t in data["timeslots"]]
    assert "AB#5555" in tickets

