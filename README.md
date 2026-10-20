<div align="center">

# 🦥 SlothLog

**Automated Git-backed worklogs & executive timesheets for developers who value steady progress.**  
*100% offline &bull; Privacy-first &bull; Google Gemma 2 2B via Ollama &bull; Sentry Agent Tracing &bull; Zero cloud leaks*

[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg?style=flat-square)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg?style=flat-square)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-21%20passed-success.svg?style=flat-square)](tests/)
[![AI Inference](https://img.shields.io/badge/AI-Gemma%202%202B%20%28Local%29-orange.svg?style=flat-square)](https://ollama.ai)
[![Telemetry](https://img.shields.io/badge/telemetry-Sentry%20GenAI%20Tracing-purple.svg?style=flat-square)](https://sentry.io)
[![Deploy](https://img.shields.io/badge/deploy-Render%20Ready-black.svg?style=flat-square)](render.yaml)

</div>

---

## 💡 The Problem

Every Friday afternoon, software engineers face the same frustrating archaeological dig:
> *"What did I actually work on Tuesday morning?"*  
> *"Which ticket was that subtle auth fix addressing?"*  
> *"How do I explain 3 hours of debugging race conditions to a non-technical PM?"*

Manual timesheet tracking wastes **~45 minutes every week** per engineer. Most developers end up guessing haphazardly, while corporate confidentiality prevents piping internal commit messages or proprietary diffs into third-party cloud LLM APIs.

**SlothLog** automates the entire loop locally:
1. **Inspects** local git repositories for commits you made on any given day.
2. **Clusters** activity by ticket identifier (`AB#` for Azure DevOps, `PROJ-` for Jira, `#` for GitHub, or `General Maintenance`).
3. **Calculates** realistic working hours based on commit timestamp burst intervals and session clustering algorithms.
4. **Synthesizes** clean, executive-ready accomplishment bullets using **Google Gemma 2 2B** running 100% locally via **Ollama**.
5. **Instruments** every AI request with **Sentry GenAI Agent Tracing** (`gen_ai.chat` spans, tokens, latency, and \$0.00 cost tracking).
6. **Exports** directly to CSV or gives you one-click formatted lines for instant pasting into Jira or Azure DevOps.

---

## 🖥️ Dashboard Preview

SlothLog features a **Linear-grade utilitarian interface** with real-time scan feedback, skeleton loaders, and instant clipboard actions:

```
+-----------------------------------------------------------------------------------------------+
|  [S] SlothLog v1.0   Git-backed worklogs & timesheet clustering   (● Gemma 2 Local) (● Sentry) |
+-----------------------------------------------------------------------------------------------+
|  Date: [ 2026-10-20 ]  [✓] Active only   [⚡ Scan Commits]   [Tracked Repos (2)]   [Export CSV] |
+-----------------------------------------------------------------------------------------------+
|  [ Logged Hours: 7.00 h ]      [ Clustered Tickets: 3 ]      [ Estimated Time Saved: ~45 mins]|
+-----------------------------------------------------------------------------------------------+
|                                                                                               |
|  [AB#4920]  billing-service                                                 [ - ]  3.25h  [ + ]|
|  "Refactored invoice calculation engine, added VAT reverse charge support for European B2B     |
|   invoices, and implemented idempotency tests."                                               |
|  ▸ 3 underlying commits                                                                       |
|  [Copy for Jira / ADO]  [Copy Summary]                                                        |
|                                                                                               |
|  [PROJ-104]  portal-frontend                                                [ - ]  2.50h  [ + ]|
|  "Implemented OAuth2 PKCE login flow callback, added refresh token rotation interceptor, and  |
|   improved session expiry modal."                                                             |
|  ▸ 3 underlying commits                                                                       |
|  [Copy for Jira / ADO]  [Copy Summary]                                                        |
+-----------------------------------------------------------------------------------------------+
```

---

## ⚡ Key Features

- **🔒 100% Offline & Private**: Proprietary commit messages and enterprise ticket content never leave your machine.
- **🏷️ Multi-Platform Ticket Detection**: Native regex resolvers for:
  - **Azure DevOps**: `AB#1234`, `#1234`
  - **Jira**: `PROJ-104`, `CORE-99`
  - **GitHub**: `gh-42`, `#42`
  - **Untagged Commits**: Automatically grouped under `General Maintenance`.
- **⏱️ Algorithmic Time Clustering**: Groups commits within **90-minute intervals** into continuous work sessions, applying a 30-minute burst buffer per session with minimum 0.5h rounding.
- **🎛️ Active / Inactive Repository Management**: Enable or disable repositories from scanning and results with a single toggle, without losing configuration.
- **📊 Real-time Visual Scan Feedback**: Dual-stage progress bar and animated skeleton loaders so you always know what the engine is processing.
- **🔍 Full Sentry Agent Tracing**: OpenTelemetry-compatible `gen_ai.chat` spans capturing prompt evaluation tokens, completion tokens, latency, and cost telemetry.
- **📋 One-Click Jira / Azure DevOps Formatting**: Click to copy pre-formatted worklog strings (e.g. `[AB#4920] 3.25h: Refactored invoice engine...`).
- **💻 Dual Interface**: Standalone, scriptable CLI tool + sleek web dashboard.

---

## 🏗️ Architecture

```
                          +-----------------------------+
                          |    Local Git Repositories   |
                          +--------------+--------------+
                                         |
                                         v
                          +-----------------------------+
                          |     Git Inspector Module    |
                          | (Author & ISO date filter)  |
                          +--------------+--------------+
                                         |
                                         v
                          +-----------------------------+
                          |    Ticket & Time Clustering |
                          | (90-min burst window engine)|
                          +--------------+--------------+
                                         |
                                         v
+------------------+              +-----------------------------+              +----------------------+
|  Sentry Agent    |<------------>|   Ollama / Gemma 2 2B       |<------------>|   FastAPI REST API   |
|  Tracing Span    | (gen_ai.chat)|   Local Open-Weight Model   |              |   & SQLite DB (WAL)  |
+------------------+              +-----------------------------+              +----------+-----------+
                                                                                          |
                                                          +-------------------------------+-------------------------------+
                                                          |                                                               |
                                                          v                                                               v
                                           +-----------------------------+                                 +-----------------------------+
                                           |   Linear-Style Dashboard    |                                 |     Standalone CLI Tool     |
                                           |  (Live scan & 1-click copy) |                                 |  (slothlog scan / export)   |
                                           +-----------------------------+                                 +-----------------------------+
```

---

## 🚀 Getting Started

### Prerequisites

1. **Python 3.10+**
2. **Git** installed on your system PATH
3. *(Optional, for local AI inference)* **[Ollama](https://ollama.ai)** with Google Gemma 2 2B:
   ```bash
   ollama pull gemma2:2b
   ```
   > **Note**: If Ollama is offline or not installed, SlothLog activates a **graceful deterministic fallback**, extracting clean accomplishment notes from commit subjects without failing.

### Installation

```bash
git clone https://github.com/alessiobianchini/slothlog.git
cd slothlog
pip install -r requirements.txt
```

---

## 🌐 Running the Web Dashboard

Start the application:
```bash
python run.py
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.

- **Add Repositories**: Click `Tracked Repos` to register local git directories.
- **Run Scan**: Click `Scan Commits` to trigger git inspection, clustering, and Gemma 2 synthesis with live progress feedback.
- **Adjust Hours**: Use `-` and `+` steppers to fine-tune session time.
- **Export**: Click `Export CSV` to download the active timesheet.

---

## 💻 CLI Usage

SlothLog provides a full-featured, zero-server command-line utility:

### Track Repositories
```bash
# Add repositories
python cli.py repos add "D:/Work/billing-service" --name billing-service
python cli.py repos add "D:/Work/portal-frontend" --name portal-frontend

# List active repositories
python cli.py repos list

# List all repositories (including deactivated ones)
python cli.py repos list --all

# Deactivate or reactivate a repository
python cli.py repos toggle <repo_id> --disable
python cli.py repos toggle <repo_id>
```

### Scan & Generate Timesheets
```bash
# Scan today's commits across all active repositories
python cli.py scan

# Scan a specific date
python cli.py scan --date 2026-10-20
```

### Export to CSV
```bash
python cli.py export --date 2026-10-20 -o timesheet_2026-10-20.csv
```

---

## 🔍 Sentry GenAI Telemetry

Every local AI synthesis request is instrumented with Sentry's `gen_ai.chat` span:
- `ai.model_id`: `gemma2:2b`
- `ai.model_provider`: `ollama`
- `ai.prompt_tokens`: Evaluation token count from Ollama
- `ai.completion_tokens`: Completion token count from Ollama
- `ai.cost`: `0.0` (Local open-source inference is completely free!)
- Error tracking & `/sentry-debug` route to verify telemetry health.

---

## 🧪 Test Suite

SlothLog is engineered with strict Test-Driven Development (TDD):

```bash
python -m pytest tests/ -v
```

All 21 unit and integration tests cover:
- SQLite connection pooling, WAL mode, deduplication, and active repo filtering
- Git inspection with author and exact ISO timestamp matching
- Azure DevOps, Jira, and GitHub ticket regex resolution
- 90-minute session clustering and buffer math
- Gemma 2 prompt evaluation and offline fallback
- REST endpoints (`/api/ping`, `/api/repos`, `/api/scan`, `/api/timeslots`, `/api/export`, `/sentry-debug`)
- CLI command invocation and CSV generation

---

## 🏆 Hacktoberfest 2026 Submission

SlothLog is officially submitted to **[Hacktoberfest Open-Source AI Challenge Week 3: Slow and Steady](https://dev.to/challenges/hacktoberfest-week3-2026-10-19)**.

| Partner Category | How SlothLog Qualifies |
| :--- | :--- |
| **Best Use of Gemma ($200)** | Uses local **Gemma 2 2B** via Ollama to transform fragmented git messages into concise, executive-grade timesheet summaries without leaking enterprise code or secrets to external cloud LLM APIs. |
| **Best Use of Render ($200)** | Fully configured `render.yaml` blueprint with environment autodetection (`RENDER=true`) and automatic sample data seeding for live cloud demo deployments. |
| **Best Use of Sentry Agent Tracing ($100)** | OpenTelemetry-compatible `gen_ai.chat` spans tracing prompt tokens, completion tokens, latency, and \$0.00 cost tracking. |

The complete submission article is available in [`DEV_ARTICLE.md`](DEV_ARTICLE.md).

---

## 📄 License

Distributed under the **MIT License**. Built with care for developers who value deep work and peaceful weekends.
