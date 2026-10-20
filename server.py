import csv
from contextlib import asynccontextmanager
from datetime import datetime
import io
import logging
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import sentry_sdk

import cluster
import db
import git_inspector
import parser

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("slothlog")

# Initialize Sentry Agent Tracing
SENTRY_DSN = os.getenv(
    "SENTRY_DSN",
    "https://d1119d5c1aba5b3a09053e8ff629f481@o4512266577575936.ingest.de.sentry.io/4512266587471952"
)
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=1.0,
        send_default_pii=False,
        environment=os.getenv("ENVIRONMENT", "production" if os.getenv("RENDER") else "development"),
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    # On Render cloud deployments or if empty, auto-seed realistic sample data
    if os.getenv("RENDER") == "true" or not db.get_timeslots("2026-10-20"):
        db.seed_demo_data()
    yield


app = FastAPI(title="SlothLog API", lifespan=lifespan)

# Mount static folder if it exists
STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class AddRepoRequest(BaseModel):
    path: str
    name: Optional[str] = None


class ToggleRepoRequest(BaseModel):
    active: bool


class UpdateTimeslotRequest(BaseModel):
    hours: float
    summary: str


@app.get("/")
def get_root():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return PlainTextResponse("SlothLog is running. Static dashboard not yet mounted.")


@app.get("/api/ping")
def ping():
    return {"status": "ok", "app": "slothlog"}


@app.get("/api/repos")
def list_repositories(include_inactive: bool = False):
    return db.list_repos(active_only=not include_inactive)


@app.post("/api/repos")
def add_repository(req: AddRepoRequest):
    repo = db.add_repo(req.path, name=req.name)
    return repo


@app.patch("/api/repos/{repo_id}")
def toggle_repository(repo_id: str, req: ToggleRepoRequest):
    ok = db.toggle_repo_active(repo_id, req.active)
    if not ok:
        raise HTTPException(status_code=404, detail="Repository not found")
    return {"ok": True, "id": repo_id, "active": req.active}


@app.delete("/api/repos/{repo_id}")
def remove_repository(repo_id: str):
    ok = db.remove_repo(repo_id)
    return {"ok": ok, "id": repo_id}


@app.get("/api/timeslots")
def get_timeslots(date: Optional[str] = None, active_only: bool = True):
    target_date = date or datetime.now().strftime("%Y-%m-%d")
    slots = db.get_timeslots(target_date, active_only=active_only)
    return {"date": target_date, "timeslots": slots}


@app.put("/api/timeslots/{slot_id}")
def update_timeslot(slot_id: str, req: UpdateTimeslotRequest):
    ok = db.update_timeslot(slot_id, req.hours, req.summary)
    if not ok:
        raise HTTPException(status_code=404, detail="Timeslot not found")
    return {"ok": True, "id": slot_id, "hours": req.hours, "summary": req.summary}


@app.get("/api/scan")
def scan_repositories(date: Optional[str] = None, author: Optional[str] = None):
    target_date = date or datetime.now().strftime("%Y-%m-%d")
    repos = db.list_repos(active_only=True)

    # If running on Render or without repos, ensure demo data is present
    if not repos and os.getenv("RENDER") == "true":
        db.seed_demo_data()
        repos = db.list_repos(active_only=True)

    logger.info("Scanning %d active repositories for date %s", len(repos), target_date)
    generated_count = 0

    for repo in repos:
        repo_path = repo["path"]
        repo_name = repo["name"]
        auth = author or git_inspector.get_default_author(repo_path)
        try:
            commits = git_inspector.inspect_repo(repo_path, target_date=target_date, author=auth)
        except Exception as err:
            logger.warning("Skipping repo '%s' due to inspection error: %s", repo_name, err)
            continue

        if not commits:
            continue

        try:
            clusters = cluster.cluster_commits(commits)
            for c in clusters:
                messages = c.get("commit_messages") or [commit["message"] for commit in c.get("commits", [])]
                hours = c.get("hours", c.get("estimated_hours", 0.5))
                summary = parser.synthesize_summary(c["ticket_id"], messages)
                db.save_timeslot({
                    "date": target_date,
                    "repo_path": repo_path,
                    "repo_name": repo_name,
                    "ticket_id": c["ticket_id"],
                    "hours": hours,
                    "summary": summary,
                    "raw_commits": messages,
                })
                generated_count += 1
            logger.info("Repo '%s': created %d timeslots from %d commits", repo_name, len(clusters), len(commits))
        except Exception as err:
            logger.error("Error processing commits for repo '%s': %s", repo_name, err, exc_info=True)

    return {
        "date": target_date,
        "scanned_repos": len(repos),
        "generated_timeslots": generated_count,
        "timeslots": db.get_timeslots(target_date, active_only=True)
    }


@app.get("/api/export")
def export_csv(date: Optional[str] = None, active_only: bool = True):
    target_date = date or datetime.now().strftime("%Y-%m-%d")
    slots = db.get_timeslots(target_date, active_only=active_only)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Repo", "Ticket", "Hours", "Summary"])
    for s in slots:
        writer.writerow([
            s["date"],
            s.get("repo_name", ""),
            s["ticket_id"],
            f"{s['hours']:.2f}",
            s.get("summary", ""),
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="timesheet_{target_date}.csv"'}
    )


@app.get("/sentry-debug")
def trigger_sentry_error():
    # Deliberate error to verify Sentry event capture
    division_by_zero = 1 / 0
    return {"result": division_by_zero}
