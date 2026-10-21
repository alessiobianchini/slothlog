---
title: "SlothLog: Why I Built an Offline, AI-Powered Timesheet Generator for Lazy Developers"
published: false
description: "Turn fragmented git commits into honest, sensible timesheets with one click using local Gemma 2 2B, Sentry Agent Tracing, and zero cloud leaks."
tags: devchallenge, hf26challenge, gemma, render
cover_image: ""
canonical_url: ""
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 3: Slow and Steady](https://dev.to/challenges/hacktoberfest-week3-2026-10-19)*

---

## What I Built

Every Friday afternoon at 4:30 PM, an invisible cloud of collective dread descends upon software engineering teams: **logging our hours into Jira, Azure DevOps, or corporate time trackers.**

You open your tracking tool, stare at a blank grid of empty days, and begin the painful archaeological dig through your week:
* *"What on earth was I committing at 10:15 AM on Tuesday?"*
* *"Which ticket ID corresponded to that subtle CORS regression?"*
* *"How can I explain three hours of debugging a race condition to a non-technical project manager without sounding defensive?"*

The result? Developers either spend 45 minutes of precious Friday time reconstructing history, or they guess haphazardly, slapping `8.0h - General Development` across every day of the week.

I wanted to be **completely, unapologetically lazy**. 

So I built **SlothLog** (🦥): an offline, privacy-first developer utility that inspects your local git commits across multiple repositories, clusters activity by ticket identifier, estimates work session duration, and synthesizes executive-ready timesheet summaries using **Google Gemma 2 2B** running locally via **Ollama**.

With SlothLog:
1. You click one button or run `python cli.py scan`.
2. It detects ticket IDs (`AB#4920`, `PROJ-104`, `#12`) and session bursts.
3. Gemma 2 turns messy commits (`"fix bug"`, `"wip typo"`, `"more changes"`) into clean, professional work notes (`"Refactored invoice calculation engine and added VAT reverse charge support"`).
4. You click **Copy for Jira / DevOps** and paste it directly into your tracker. You are done in 10 seconds.

---

## Demo

Here is SlothLog in action running locally with its utilitarian dark dashboard:

### 1. The SlothLog Dashboard
The web dashboard features an interactive date selector, hour stepper (`+` / `-` 0.25h), tracked repository manager, and single-click copy buttons with instant toast confirmations:

```
+---------------------------------------------------------------------------------------+
| 🦥 SlothLog    Offline AI Timesheets for Lazy Developers    [Gemma 2 2B] [Sentry Active]|
+---------------------------------------------------------------------------------------+
| [ Total Logged: 7.00 h ]    [ Clustered Tickets: 3 ]    [ Effort Saved: ~45 mins ]    |
+---------------------------------------------------------------------------------------+
| [AB#4920] billing-service                                             [-] 3.25h [+]  |
| "Refactored invoice calculation engine, added VAT reverse charge support for European |
|  B2B invoices, and implemented idempotency tests."                                    |
| [ 3 underlying commits ]                                                              |
| [📋 Copy for Jira / DevOps]   [📄 Copy Summary]                                       |
+---------------------------------------------------------------------------------------+
| [PROJ-104] portal-frontend                                            [-] 2.50h [+]  |
| "Implemented OAuth2 PKCE login flow callback and added refresh token rotation."       |
| [📋 Copy for Jira / DevOps]   [📄 Copy Summary]                                       |
+---------------------------------------------------------------------------------------+
```

### 2. Standalone CLI Flow
If you prefer staying in the terminal:
```bash
$ python cli.py scan --date 2026-10-20

Scanning 2 repositories for date: 2026-10-20...

Generated Timesheet:
Date       | Repo            | Ticket              | Hours | Summary
-----------+-----------------+---------------------+-------+------------------------------------------------------------
2026-10-20 | billing-service | AB#4920             | 3.25h | Refactored invoice calculation engine, added VAT reverse...
2026-10-20 | portal-frontend | PROJ-104            | 2.50h | Implemented OAuth2 PKCE login flow callback...
2026-10-20 | billing-service | General Maintenance | 1.25h | Upgraded dependencies, cleaned up unused imports...

Total Hours: 7.00h
```

You can also export to standard CSV with `python cli.py export -o timesheet.csv` for HR and payroll imports.

---

## Code

{% github alessiobianchini/slothlog %}

The full open-source codebase is hosted on GitHub:  
👉 **[https://github.com/alessiobianchini/slothlog](https://github.com/alessiobianchini/slothlog)**

---

## How I Built It

SlothLog was designed with a strict **anti-overengineering** philosophy: no heavy orchestrators (no LangChain, no LlamaIndex), no external cloud dependencies, and zero telemetry bloat.

### 1. Git Inspection & Ticket Clustering
The core engine inspects local git histories using native `git log --format=%H|%aI|%an|%ae|%s --date-order`. Commits are grouped by ticket identifier:
- **Azure DevOps**: Regex matching `AB#\d+` or `#\d+`
- **Jira**: Regex matching `[A-Z]+-\d+`
- **GitHub**: Regex matching `gh-\d+`
- **Untagged**: Fallback to `General Maintenance`

To estimate time accurately without snooping or spyware, SlothLog uses a **session clustering algorithm**:
- Commits within **90 minutes** of each other are grouped into a continuous work session.
- An initial **30-minute burst buffer** is added per session to account for active reading, debugging, and coding prior to the first commit.
- Hours are snapped to realistic quarter-hour increments (0.25h) with a minimum 0.5h threshold.

### 2. Local Open-Weight Synthesis with Gemma 2 2B
Enterprise developers cannot send proprietary commit messages, internal function names, or company ticket contents to third-party closed AI APIs. Privacy is paramount.

SlothLog queries **Google Gemma 2 2B** via Ollama on `localhost:11434`. Gemma 2 2B is the ideal model for this task: ultra-lightweight, extremely fast on standard laptops, and remarkably proficient at concise extractive summarization without conversational filler.

Here is the exact prompt that produces crisp results:
```python
prompt = f"""You are a concise engineering assistant. Summarize these git commit messages into a single professional timesheet accomplishment bullet (1-2 sentences max).
Do not mention commit hashes, dates, or conversational filler. Focus on what was delivered or solved.

Ticket: {ticket_id}
Commits:
{formatted_commits}

Executive Summary:"""
```

If Ollama is not running or offline, SlothLog activates a **graceful deterministic fallback**, generating clean formatted summaries from the raw commits so you are never blocked.

### 3. Sentry Agent Tracing
To monitor the local AI execution and observe system health, I instrumented SlothLog with **Sentry SDK's Agent & GenAI Tracing**:

```python
with sentry_sdk.start_span(op="gen_ai.chat", description=f"Ollama synthesis: {ticket_id}") as span:
    span.set_data("ai.model_id", "gemma2:2b")
    span.set_data("ai.model_provider", "ollama")
    span.set_data("ai.prompt_tokens", res.get("prompt_eval_count", 0))
    span.set_data("ai.completion_tokens", res.get("eval_count", 0))
    span.set_data("ai.total_tokens", total_tokens)
    span.set_data("ai.cost", 0.0) # Local open-source inference is free!
```

Every synthesis run tracks token throughput, inference latency, and error states. Even better: Sentry confirms that our AI cost is **\$0.00**.

---

## Why Does Open Innovation Matter?

Open innovation is the entire reason SlothLog can exist.

In a corporate environment, developer codebases are strictly confidential. Proprietary APIs from closed vendors pose serious privacy, compliance, and IP risks:
- You cannot legally pipe commit diffs or commit messages referencing confidential client algorithms or internal infrastructure through external cloud endpoints without strict enterprise agreements.
- Reliance on closed APIs introduces vendor lock-in, API rate limits, unpredictable pricing changes, and sudden deprecations.

With open-weight models like **Google Gemma 2**, the paradigm shifts:
1. **Total Sovereignty**: You can run Gemma 2 2B on an airplane, in an air-gapped corporate intranet, or during an internet outage. Your code never leaves your RAM.
2. **Deterministic Stability**: The model weights don't change overnight without your consent.
3. **Zero Marginal Cost**: Logging 10 tickets a day or 10,000 tickets a month costs exactly the same: zero dollars.

Open-weight AI gives power back to individual builders.

---

## My Agent Session

This entire project — from architecture design and specification to TDD implementation, Sentry tracing, and frontend build — was developed using **Antigravity** pair-programming.

You can inspect the complete design spec and step-by-step TDD verification transcript in the project repository:
- Design Spec: [`docs/superpowers/specs/2026-10-20-slothlog-design.md`](https://github.com/alessiobianchini/slothlog/blob/main/docs/superpowers/specs/2026-10-20-slothlog-design.md)
- Implementation Plan: [`docs/superpowers/plans/2026-10-20-slothlog.md`](https://github.com/alessiobianchini/slothlog/blob/main/docs/superpowers/plans/2026-10-20-slothlog.md)

---

## The Lazy Payoff

Let's calculate the sloth economics:

- **Manual Timesheet Archaeologist**:
  - Finding git logs across 3 repos: ~10 minutes
  - Calculating start/end times and rounding: ~10 minutes
  - Writing creative prose for Jira/Azure DevOps: ~15 minutes
  - Form-filling and double-checking: ~10 minutes
  - **Total: ~45 minutes every Friday (~39 hours per year per engineer)**

- **With SlothLog**:
  - Run `python cli.py scan` or click *Scan Commits*: ~3 seconds
  - Review and click *Copy for Jira / DevOps*: ~10 seconds
  - Paste into tracker: ~15 seconds
  - **Total: ~30 seconds**

That's **98.8% time saved**, 39 extra hours per year spent building actual software (or taking a well-deserved nap). Sloths everywhere rejoice.

---

## Prize Categories

I am officially entering SlothLog into the following categories for **Hacktoberfest Open-Source AI Challenge Week 3**:

* **Best Use of Gemma ($200)**: Local inference using `gemma2:2b` via Ollama for privacy-preserving, offline commit summarization without API fees.
* **Best Use of Render ($200)**: Full cloud blueprint (`render.yaml`) with auto-detected environment variables and demo data seeding for instant one-click deployment.
* **Best Use of Sentry Agent Tracing ($100)**: Full OpenTelemetry-compatible `gen_ai.chat` spans measuring prompt/completion token metrics, latency, and \$0.00 cost telemetry.
