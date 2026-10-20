# SlothLog Design Document
**Date:** 2026-10-20  
**Status:** Draft  
**Target:** Hacktoberfest 2026 Open-Source AI Challenge Week 3 ("Slow and Steady")

---

## 1. Intent & The Why

Software developers, consultants, and agency engineers universally dread manual timesheet logging. At the end of every day or week, engineers are forced to reconstruct their work by searching through terminal logs, git commit histories, and task boards to guess where their hours went.

**SlothLog** channels the philosophy of *International Sloth Day / Slow and Steady*: it automates the tedious chore of timesheet reporting so developers can be effortlessly lazy. 

Instead of manual guesswork, SlothLog inspects local Git activity across user-selected repositories, extracts Azure DevOps and Jira ticket references, calculates time allocations from commit intervals, and uses local open-weight AI (Google Gemma 2 2B via Ollama) to synthesize cryptic commit messages into clean, executive-ready work summaries.

Because it runs 100% locally with open-weight models, it guarantees zero data leakage: company code, branch names, and confidential ticket summaries never leave `localhost`.

---

## 2. Goals, Non-Goals & Anti-Goals

### Goals
1. **Multi-Repo Tracking**: Allow developers to register and manage multiple local git project directories.
2. **Automated Ticket Parsing**: Detect task identifiers in branch names and commit messages using heuristics for:
   - Azure DevOps (`AB#1234`, `#1234`)
   - Jira (`PROJ-123`, `TASK-99`)
   - GitHub Issues (`#45`)
   - Untagged commits (grouped under a fallback bucket).
3. **Session & Hour Estimation**: Cluster commit timestamps into work intervals with customizable session gap thresholds (default: 90 min) to produce realistic hour estimations.
4. **AI Summary Synthesis (Gemma 2 2B)**: Turn low-level commit messages (e.g. `wip`, `fix typo`, `refactor auth`) into professional, structured bullet points for timesheet submissions.
5. **Utilitarian Web UI & CLI**: Provide a fast, high-density dashboard with single-click "Copy" buttons (Task ID, Hours, Description), inline hour tweaking, and CSV/JSON export.
6. **Contest Alignment & Observability**:
   - Primary: Hacktoberfest Week 3 theme (*Slow and Steady*).
   - Partner Category: **Best Use of Gemma** (Ollama + `gemma2:2b`).
   - Partner Category: **Best Use of Render** (`render.yaml` for live web demo with pre-seeded sample git activity).
   - Partner Category: **Best Use of Sentry Agent Tracing** (`sentry-sdk` with `gen_ai.chat` spans for token tracking, latency, and zero-cost local verification).

### Non-Goals
- Two-way live sync with proprietary internal corporate ERPs or VPN-locked enterprise software (keeping SlothLog portable and accessible to any developer).
- Automated timesheet auto-submission without human verification (the developer must retain full control before copying or submitting).

### Anti-Goals
- Employee monitoring spyware: SlothLog does NOT record keystrokes, active window titles, or webcam/screenshots. It exclusively parses git commit histories that the developer has already intentionally committed.

---

## 3. Constraints
- **Language & Comments**: All code, variables, and documentation must be in English.
- **Git Commit Author**: All repository commits must use `--author="Alessio Bianchini <alessio.bianchini@doit.it>"`.
- **Runtime & Inference**: Python 3.10+, FastAPI backend, native SQLite database, Ollama running `gemma2:2b`.
- **Dependencies**: Lean dependencies (`fastapi`, `uvicorn`, `sentry-sdk`, `pydantic`). No heavy orchestration frameworks (LangChain, LlamaIndex).
- **Offline First**: Fully functional without internet access. Cloud deployment on Render acts as an interactive preview with mock sample data.

---

## 4. User Decisions & Architectural Choices

1. **Repository Selection**: The user configures specific repositories to track (saved in SQLite or a local config), rather than scanning all directories indiscriminately.
2. **Decoupled Workflow**: Independent of any specific corporate time-tracking tool. It provides ready-to-paste text, quick clipboard copy, and standard CSV export.
3. **Model Selection**: Google Gemma 2 2B (`gemma2:2b`) as default for speed (<2s per summary) and low memory footprint (~1.6GB VRAM/RAM).

---

## 5. System Architecture & Components

```
                   +---------------------------+
                   |  Selected Git Repositories |
                   +-------------+-------------+
                                 | (git log)
                                 v
+--------------------------------------------------------------+
|                      SlothLog Engine                          |
|                                                              |
|  1. Git Inspector: Extracts commits, authors, dates, branches |
|  2. Ticket Resolver: Regex extraction (Azure DevOps / Jira)  |
|  3. Time Clustered Estimator: Intervals & durations           |
|  4. AI Synthesizer: Gemma 2 2B via Ollama                    |
|  5. Sentry Tracing: gen_ai.chat span instrumentation         |
|  6. SQLite Storage: Configured repos & timeslot history      |
+------------------------------+-------------------------------+
                               |
         +---------------------+---------------------+
         v                                           v
+------------------+                       +-------------------+
| Web UI (FastAPI) |                       | Terminal CLI      |
| Single-click copy|                       | scan, list, export|
| Inline edits     |                       |                   |
+------------------+                       +-------------------+
```

### Core Modules:
- `git_inspector.py`: Reads git commit logs between dates for given paths using `git log` command. Automatically filters by author using `git config user.email` (or an explicit `--author` override) so only the developer's own work is pulled from shared team repositories.
- `parser.py`: Regex extraction of ticket keys (`AB#\d+`, `[A-Z]+-\d+`), grouping commits by ticket, and prompting Ollama `gemma2:2b` to generate executive task notes.
- `db.py`: SQLite layer storing tracked repo paths, cached timeslots, and settings. Operates with WAL mode for safe concurrent access between CLI and Web UI.
- `server.py`: FastAPI application serving REST endpoints (`/api/repos`, `/api/scan`, `/api/timesheet`, `/api/export`, `/api/ping`, `/sentry-debug`) and the static frontend. On Render (`RENDER=true`), auto-seeds realistic sample timeslots for the cloud preview.
- `cli.py`: Standalone CLI tool (`python cli.py scan --date today`, `python cli.py export`, `python cli.py repos add <path>`) that directly accesses `db.py` and core modules without requiring a background server process.
- `static/index.html`: Utilitarian, fast dashboard with system fonts and copy buttons.
- `render.yaml`: Blueprint for cloud demo on Render with pre-seeded demo git data and zero setup.

---

## 6. Resolved Architectural Decisions (Builder Calls)
1. **Author Identity**: SlothLog inspects `git config user.email` (and `user.name`) by default to automatically isolate the developer's own commits in team repositories, with an optional `--author` flag or UI input for custom overrides.
2. **Cloud Demo on Render**: To keep the Render service free and lightweight, Render hosts the FastAPI server and database with pre-seeded demo timeslots. Real-time local inference is clearly highlighted as running locally via Ollama for data confidentiality.
3. **CLI Independence**: `cli.py` is standalone (imports core modules directly) for zero-latency terminal workflows without needing to run `uvicorn`.
4. **Synthesis Lifecycle**: Commits are clustered instantly by ticket, then Gemma 2 generates the task summaries. Summaries are cached in SQLite so repeated views don't re-trigger inference unless the user clicks "Regenerate".

