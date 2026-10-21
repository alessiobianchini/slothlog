# 🦥 SlothLog

> Turn your git commits into honest, sensible timesheets — without leaking company code to the cloud.

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg?style=flat-square)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-emerald.svg?style=flat-square)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-21%20passing-success.svg?style=flat-square)](tests/)
[![Local AI](https://img.shields.io/badge/model-Gemma%202%202B%20(Local)-orange.svg?style=flat-square)](https://ollama.ai)

---

## Why this exists

Every Friday at 4:30 PM, the same ritual happens across engineering teams:
- You open Jira, Azure DevOps, or whatever timesheet tool your company uses.
- You stare at the blank week grid and wonder: *"What on earth was I doing on Tuesday morning?"*
- You open your terminal, run `git log`, scroll frantically through branch names, and end up roughly guessing numbers to hit 8 hours a day.

Most of us waste 30 to 45 minutes every week doing this archaeological reconstruction. And while modern AI tools can summarize text, **pasting internal commit messages and proprietary code into third-party cloud APIs is a fast track to an unpleasant chat with Infosec**.

**SlothLog** fixes this by staying completely local:
1. It scans your local git repos for commits made on a specific day.
2. It detects ticket IDs automatically (`AB#1234` for Azure DevOps, `PROJ-42` for Jira, `#123` for GitHub) and falls back to `General Maintenance` for untagged commits.
3. It estimates realistic working hours based on commit timestamp gaps (no more wild guessing).
4. It drafts a short, plain-English summary using a local **Gemma 2 2B** model running via **Ollama** (or a clean rule-based fallback if Ollama isn't running).
5. You click one button to copy the formatted worklog line directly into your ticket. Done in 30 seconds.

---

## What it looks like

SlothLog gives you a dark-mode web dashboard (and a scriptable CLI):

```text
+-----------------------------------------------------------------------------------------------+
|  SlothLog              Git-backed worklogs & session clustering          (Local Gemma) (Sentry) |
+-----------------------------------------------------------------------------------------------+
|  Date: [ 2026-10-20 ]  [x] Active only   [⚡ Scan Commits]   [Tracked Repos (2)]   [Export CSV] |
+-----------------------------------------------------------------------------------------------+
|  Logged Hours: 5.75h      Clustered Tickets: 2      Estimated Time Saved: ~30 mins            |
+-----------------------------------------------------------------------------------------------+
|                                                                                               |
|  [AB#4920]  billing-service                                                 [ - ]  3.25h  [ + ]|
|  "Refactored invoice calculation engine, added VAT reverse charge support for European B2B     |
|   invoices, and implemented idempotency tests."                                               |
|  ▸ 3 underlying commits (da13fd1, 7i8j9k0, e4f5g6h)                                           |
|  [Copy for Jira / ADO]  [Copy Summary]  [Delete]                                              |
|                                                                                               |
|  [PROJ-104]  portal-frontend                                                [ - ]  2.50h  [ + ]|
|  "Implemented OAuth2 PKCE login flow callback, added refresh token rotation interceptor, and  |
|   improved session expiry modal."                                                             |
|  ▸ 3 underlying commits (c01a23b, f45e67d, 8901abc)                                           |
|  [Copy for Jira / ADO]  [Copy Summary]  [Delete]                                              |
+-----------------------------------------------------------------------------------------------+
```

---

## Features that make everyday work easier

- **Privacy by default**: Runs 100% on your machine. No telemetry of your commit content, no external API keys required.
- **Smart ticket grouping**:
  - **Azure DevOps**: detects `AB#1234`, `#1234`
  - **Jira**: detects `PROJ-104`, `BACK-99`, etc.
  - **GitHub**: detects `gh-42`, `#42`
  - **Untagged**: neatly grouped under `General Maintenance`.
- **Reasonable time estimation**: Groups commits into sessions based on a **90-minute inactivity threshold**, adding a reasonable buffer (minimum 0.5h, rounded to nearest 15 mins). You can always tweak the final hours with the `+` / `-` steppers.
- **Commit hash inspection**: Expand the underlying commits accordion to see the exact short SHA (`da13fd1`) and commit message for full transparency.
- **Repo toggles**: Temporarily disable repos you don't want in today's scan without having to delete them from your list.
- **One-click copy**: Formatted ready-to-paste strings like `[AB#4920] 3.25h: Refactored invoice engine...`.
- **Export to CSV**: For people who still have to email an Excel sheet to their manager.
- **Works offline**: If Ollama isn't running, SlothLog doesn't crash — it switches to a deterministic fallback that cleans up conventional commit prefixes into clean readable sentences.

---

## Quickstart

### Prerequisites
- Python 3.10 or newer
- Git installed on your machine
- *(Optional)* [Ollama](https://ollama.ai) with `gemma2:2b`:
  ```bash
  ollama pull gemma2:2b
  ```
  *(If you don't have Ollama, SlothLog still works completely fine using its built-in rule summarizer).*

### Install & Run

```bash
# Clone the repository
git clone https://github.com/alessiobianchini/slothlog.git
cd slothlog

# Install Python dependencies
pip install -r requirements.txt

# Start the web app
python run.py
```

Then open **http://localhost:8000** in your browser:
1. Click **Tracked Repos** to add the path of your local git folders.
2. Pick a date and hit **⚡ Scan Commits**.
3. Adjust any hours or summaries as needed.
4. Copy the lines directly into Jira or Azure DevOps.

---

## Prefer the command line?

SlothLog also comes with a standalone CLI:

```bash
# Add your local repositories
python cli.py repos add "D:/Projects/backend" --name backend
python cli.py repos add "D:/Projects/frontend" --name frontend

# See all configured repos
python cli.py repos list

# Scan today's commits across all active repos
python cli.py scan

# Scan a past date
python cli.py scan --date 2026-10-20

# Export directly to a CSV file
python cli.py export --date 2026-10-20 -o timesheet.csv
```

---

## How SlothLog estimates your time

Real engineering work isn't evenly spaced commits every 10 minutes. Sometimes you make three commits in 15 minutes, then spend two hours reading docs or debugging before the next commit.

SlothLog handles this with a simple time-gap rule:
- Commits within **90 minutes** of each other belong to the same work session.
- An isolated single commit gets a baseline 30-minute block (0.5h).
- Extended sessions take the difference between your first and last commit in that window, plus a 30-minute buffer for wrap-up/testing.
- All totals round to the nearest quarter-hour (`0.25h`), with a minimum of `0.5h`.
- If the estimate doesn't match your actual day, the `+` / `-` buttons on each card let you adjust it in one click.

---

## Tech Stack & Observability

- **Backend**: FastAPI + Uvicorn
- **Storage**: SQLite in WAL mode (`sloth.db`) with zero external database dependencies
- **Inference**: Google Gemma 2 2B via local Ollama endpoint (`http://localhost:11434`)
- **Telemetry**: Instrumented with **Sentry Agent Tracing** using standard OpenTelemetry `gen_ai.chat` spans:
  - Tracks model, latency, and input/output tokens.
  - Reports `$0.00` cost because running open-weights models locally is free.
- **Frontend**: Lightweight vanilla HTML/CSS/JS — no heavy build steps, no node_modules required.

---

## Tests

SlothLog has a complete test suite covering the database layer, git parsing, session clustering, REST endpoints, and CLI:

```bash
python -m pytest tests/ -v
```

---

## Hacktoberfest 2026

Built for **[Hacktoberfest Open-Source AI Challenge Week 3: Slow and Steady](https://dev.to/challenges/hacktoberfest-week3-2026-10-19)**.

| Track | Implementation |
| :--- | :--- |
| **Best Use of Gemma** | Uses **Gemma 2 2B** running locally to synthesize concise task accomplishments from granular git commits without cloud API privacy risks. |
| **Best Use of Render** | Production-ready `render.yaml` blueprint with automated sample data seeding for live cloud demo deployments. |
| **Best Use of Sentry Agent Tracing** | Fully instrumented `gen_ai.chat` spans capturing latency, token counts, and zero-cost local inference metrics. |

Full submission writeup is available in [`DEV_ARTICLE.md`](DEV_ARTICLE.md).

---

## License

MIT License. Free to use, fork, and adapt. Built for developers who'd rather write code than spend their Friday afternoons guessing timesheets.
