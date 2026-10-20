import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

DB_FILE = Path(__file__).parent / "sloth.db"


def get_db_path() -> Path:
    env_db = os.getenv("SLOTHLOG_DB")
    if env_db:
        return Path(env_db)
    return DB_FILE


@contextmanager
def get_conn():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS repos (
                id TEXT PRIMARY KEY,
                path TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS timeslots (
                id TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                repo_path TEXT NOT NULL,
                repo_name TEXT NOT NULL,
                ticket_id TEXT NOT NULL,
                hours REAL NOT NULL,
                summary TEXT NOT NULL,
                raw_commits TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_slots_date ON timeslots(date)")


def add_repo(path: str, name: str | None = None) -> dict:
    resolved_path = str(Path(path).expanduser().resolve())
    repo_name = name or Path(resolved_path).name or "Repository"
    now = datetime.now().isoformat()

    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, path, name, active, created_at FROM repos WHERE path = ?", (resolved_path,))
        row = cur.fetchone()
        if row:
            return dict(row)

        repo_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO repos (id, path, name, active, created_at) VALUES (?, ?, ?, 1, ?)",
            (repo_id, resolved_path, repo_name, now)
        )
        return {
            "id": repo_id,
            "path": resolved_path,
            "name": repo_name,
            "active": 1,
            "created_at": now
        }


def list_repos() -> list[dict]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, path, name, active, created_at FROM repos WHERE active = 1 ORDER BY name ASC")
        return [dict(r) for r in cur.fetchall()]


def remove_repo(repo_id: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM repos WHERE id = ?", (repo_id,))
        return cur.rowcount > 0


def save_timeslot(entry: dict) -> dict:
    now = datetime.now().isoformat()
    slot_id = entry.get("id") or str(uuid.uuid4())
    raw_commits_json = json.dumps(entry.get("raw_commits", []))

    with get_conn() as conn:
        conn.execute("""
            INSERT INTO timeslots (
                id, date, repo_path, repo_name, ticket_id, hours, summary, raw_commits, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                hours = excluded.hours,
                summary = excluded.summary,
                raw_commits = excluded.raw_commits,
                updated_at = excluded.updated_at
        """, (
            slot_id,
            entry["date"],
            entry["repo_path"],
            entry.get("repo_name", Path(entry["repo_path"]).name),
            entry["ticket_id"],
            float(entry["hours"]),
            entry.get("summary", ""),
            raw_commits_json,
            now,
            now
        ))

    entry["id"] = slot_id
    entry["created_at"] = now
    entry["updated_at"] = now
    return entry


def get_timeslots(target_date: str) -> list[dict]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM timeslots WHERE date = ? ORDER BY ticket_id ASC", (target_date,))
        rows = []
        for r in cur.fetchall():
            d = dict(r)
            if d.get("raw_commits"):
                try:
                    d["raw_commits"] = json.loads(d["raw_commits"])
                except Exception:
                    d["raw_commits"] = []
            rows.append(d)
        return rows


def update_timeslot(slot_id: str, hours: float, summary: str) -> bool:
    now = datetime.now().isoformat()
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE timeslots SET hours = ?, summary = ?, updated_at = ? WHERE id = ?",
            (hours, summary, now, slot_id)
        )
        return cur.rowcount > 0


def seed_demo_data():
    if get_timeslots("2026-10-20"):
        return

    add_repo("/work/billing-service", "billing-service")
    add_repo("/work/portal-frontend", "portal-frontend")

    samples = [
        {
            "date": "2026-10-20",
            "repo_path": str(Path("/work/billing-service").resolve()),
            "repo_name": "billing-service",
            "ticket_id": "AB#4920",
            "hours": 3.25,
            "summary": "Refactored invoice calculation engine, added VAT reverse charge support for European B2B invoices, and implemented idempotency tests.",
            "raw_commits": [
                "feat(AB#4920): add VAT reverse charge handler",
                "test(AB#4920): verify zero tax for intra-EU enterprise customers",
                "fix(AB#4920): handle currency rounding edge cases"
            ]
        },
        {
            "date": "2026-10-20",
            "repo_path": str(Path("/work/portal-frontend").resolve()),
            "repo_name": "portal-frontend",
            "ticket_id": "PROJ-104",
            "hours": 2.50,
            "summary": "Implemented OAuth2 PKCE login flow callback, added refresh token rotation interceptor, and improved session expiry modal.",
            "raw_commits": [
                "feat: PROJ-104 add PKCE exchange helper",
                "feat: PROJ-104 add token refresh axios interceptor",
                "wip PROJ-104 styling session timeout prompt"
            ]
        },
        {
            "date": "2026-10-20",
            "repo_path": str(Path("/work/billing-service").resolve()),
            "repo_name": "billing-service",
            "ticket_id": "General Maintenance",
            "hours": 1.25,
            "summary": "Upgraded dependencies, cleaned up unused imports, and updated docker-compose dev environment.",
            "raw_commits": [
                "chore: bump fastapi to 0.110.0",
                "ci: clean up cache steps in github actions"
            ]
        }
    ]

    for s in samples:
        save_timeslot(s)
