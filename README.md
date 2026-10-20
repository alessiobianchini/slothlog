# 🦥 SlothLog

> **AI-Powered Developer Timesheets for the Lazy & Steady.**  
> Turn scattered git commits into polished, executive timesheet entries with one click.  
> *100% offline, privacy-first, zero manual logging.*

---

## 🌟 Why SlothLog?

Every developer knows the dreaded Friday afternoon ritual: opening Jira, Azure DevOps, or your company's internal time-tracking tool, and staring blankly into space trying to remember:
* *"What on earth did I work on Tuesday morning?"*
* *"Which ticket ID was that branch addressing?"*
* *"How many hours did that PR review and bugfix actually take?"*

Writing timesheets is tedious, subjective, and prone to guessing.  
**SlothLog** solves this by letting your version control do the remembering:
1. **Inspects** local git repositories for the commits you made today (or any date).
2. **Clusters** commits by ticket identifier (Azure DevOps `AB#`, Jira `PROJ-`, GitHub `#`, or fallback to `General Maintenance`).
3. **Calculates** realistic working hours based on commit timestamp burst intervals and session clustering.
4. **Synthesizes** clean, executive-ready accomplishment bullets using **Google Gemma 2 2B** running locally on your machine via **Ollama**.
5. **Observes** AI inference performance and cost with **Sentry Agent Tracing** (`gen_ai.chat` spans, tokens, latency, and \$0.00 cost tracking).
6. **Exports** directly to CSV or lets you copy formatted ticket notes with a single click.

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
                 |  (git log author + iso date)|
                 +--------------+--------------+
                                |
                                v
                 +-----------------------------+
                 |    Ticket & Time Clustering |
                 | (90-min gap session windows)|
                 +--------------+--------------+
                                |
                                v
+------------------+     +-----------------------------+     +----------------------+
|  Sentry Agent    |<--->|   Ollama / Gemma 2 2B       |<--->|   FastAPI Web Server |
|  Tracing Span    |     |   Local Open-Weight Model   |     |   & SQLite DB (WAL)  |
+------------------+     +-----------------------------+     +----------+-----------+
                                                                        |
                                                 +----------------------+----------------------+
                                                 |                                             |
                                                 v                                             v
                                  +-----------------------------+               +-----------------------------+
                                  |    Utilitarian Web UI       |               |     Standalone CLI Tool     |
                                  | (One-click copy to Jira/ADO)|               | (slothlog scan / export)    |
                                  +-----------------------------+               +-----------------------------+
```

---

## 🏆 Hacktoberfest 2026 Categories Targeted

SlothLog is engineered specifically for **Hacktoberfest Open-Source AI Challenge Week 3: Slow and Steady**:

| Category | Implementation in SlothLog |
| :--- | :--- |
| **Best Use of Gemma ($200)** | Uses local **Gemma 2 2B** via Ollama to transform fragmented git messages into concise, executive-grade timesheet summaries without leaking enterprise code or secrets to external cloud LLM APIs. |
| **Best Use of Render ($200)** | Includes ready-to-deploy `render.yaml` blueprint with automatic demo data seeding and cloud environment detection (`RENDER=true`). |
| **Best Use of Sentry Agent Tracing ($100)** | Full OpenTelemetry-compatible `gen_ai.chat` spans tracing prompt tokens, completion tokens, latency, model parameters, and \$0.00 cost tracking. |

---

## 🚀 Quickstart

### Prerequisites
- Python 3.10+
- Git installed on your system
- (Optional, for local AI synthesis) [Ollama](https://ollama.ai) with Gemma 2 2B:
  ```bash
  ollama pull gemma2:2b
  ```
  *(Note: If Ollama is not installed or offline, SlothLog seamlessly falls back to a clean deterministic rule-based summarizer without crashing!)*

### Installation
```bash
git clone https://github.com/alessiobianchini/slothlog.git
cd slothlog
pip install -r requirements.txt
```

---

## 💻 CLI Usage

SlothLog includes a standalone command-line tool that requires zero server setup:

### 1. Register your local repositories
```bash
python cli.py repos add /path/to/billing-service --name billing-service
python cli.py repos add /path/to/portal-frontend --name portal-frontend
python cli.py repos list
```

### 2. Scan and generate timesheets
```bash
# Scan today's commits across all tracked repositories
python cli.py scan

# Or scan a specific date
python cli.py scan --date 2026-10-20
```

### 3. Export to CSV
```bash
python cli.py export --date 2026-10-20 -o timesheet_2026-10-20.csv
```

---

## 🌐 Web Dashboard

Start the local server:
```bash
python run.py
```
Open [http://localhost:8000](http://localhost:8000) in your browser:
- **Utilitarian Dark Mode**: Clean, distraction-free interface built with native system typography.
- **Interactive Hour Stepper**: Quickly adjust estimated hours with `+` / `-` buttons.
- **One-Click Clipboard Copy**: Instantly copy lines formatted for Jira worklogs (`[PROJ-104] 2.50h: Implemented OAuth2 PKCE login callback...`) or Azure DevOps.
- **CSV Download**: One-click export for HR or payroll tools.

---

## 🔍 Sentry Agent Tracing

Every AI synthesis request creates an instrumented Sentry span under `gen_ai.chat`:
- `ai.model_id`: `gemma2:2b`
- `ai.model_provider`: `ollama`
- `ai.prompt_tokens`: Token count from Ollama prompt evaluation
- `ai.completion_tokens`: Token count from Ollama generation
- `ai.cost`: `0.0` (open-source local inference is completely free!)
- Error tracking & `/sentry-debug` route to verify live event telemetry.

---

## 🧪 Testing

SlothLog maintains a comprehensive test suite covering all modules:
```bash
python -m pytest tests/ -v
```

---

## 📄 License

MIT License. Crafted with 🦥 care for developers who value steady progress and uninterrupted weekends.
