import json
import logging
import os
import re
import urllib.request
from typing import List
import sentry_sdk

log = logging.getLogger("slothlog.parser")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
DEFAULT_MODEL = os.getenv("SLOTH_MODEL", "gemma2:2b")

SYSTEM_PROMPT = """You are an engineering work-log assistant. Your job is to transform a developer's granular, raw git commit messages for a specific task into a single, concise, professional 1-2 sentence executive summary for their timesheet work log.

Rules:
1. Write in active past tense in English (e.g. "Implemented OAuth token exchange, resolved token refresh bug, and added unit tests.").
2. Combine related work into coherent business-value accomplishments.
3. Do NOT include markdown bolding, code fences, greetings, or preamble like "Here is the summary:".
4. Output ONLY the executive summary sentence(s).
"""


def _sanitize_commit_message(msg: str) -> str:
    # Remove ticket IDs like AB#1234, PROJ-101, conventional commit prefixes like feat:, fix:
    cleaned = re.sub(r'^(feat|fix|chore|docs|refactor|test|ci|style)(\([^\)]+\))?:\s*', '', msg, flags=re.IGNORECASE)
    cleaned = re.sub(r'\b(AB#\d+|[A-Z][A-Z0-9]+-\d+|#\d+)\b:?\s*', '', cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def _fallback_summary(ticket_id: str, commit_messages: List[str]) -> str:
    cleaned_items = []
    for m in commit_messages:
        s = _sanitize_commit_message(m)
        if s and s.lower() not in {"wip", "test", "commit", "update"}:
            cleaned_items.append(s)

    if not cleaned_items:
        return f"Development and maintenance work on {ticket_id}."

    # Join cleaned items with semicolons
    capitalized = [item[0].upper() + item[1:] if len(item) > 1 else item for item in cleaned_items]
    return "; ".join(capitalized[:4]) + "."


def synthesize_summary(ticket_id: str, commit_messages: List[str], model: str = DEFAULT_MODEL) -> str:
    if not commit_messages:
        return f"Routine development and maintenance on {ticket_id}."

    prompt_body = f"Task: {ticket_id}\nGit Commits:\n" + "\n".join(f"- {m}" for m in commit_messages)

    payload = {
        "model": model,
        "prompt": f"{SYSTEM_PROMPT}\n\n{prompt_body}\n\nExecutive Summary:",
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 256
        }
    }

    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    with sentry_sdk.start_span(op="gen_ai.chat", name=f"SlothLog Summary ({ticket_id})") as span:
        span.set_data("gen_ai.system", "ollama")
        span.set_data("gen_ai.request.model", model)
        span.set_data("gen_ai.ticket_id", ticket_id)

        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                text = res.get("response", "").strip()

                prompt_tokens = res.get("prompt_eval_count", 0)
                completion_tokens = res.get("eval_count", 0)
                duration_sec = round(res.get("total_duration", 0) / 1e9, 2)

                span.set_data("gen_ai.usage.prompt_tokens", prompt_tokens)
                span.set_data("gen_ai.usage.completion_tokens", completion_tokens)
                span.set_data("gen_ai.usage.total_tokens", prompt_tokens + completion_tokens)
                span.set_data("gen_ai.cost", 0.0)
                span.set_data("gen_ai.duration_sec", duration_sec)

                if text:
                    # Clean any accidental outer quotes
                    if text.startswith('"') and text.endswith('"'):
                        text = text[1:-1].strip()
                    return text
        except Exception as e:
            log.warning(f"Ollama synthesis unavailable ({e}), using deterministic fallback")
            span.set_data("error", str(e))

    return _fallback_summary(ticket_id, commit_messages)
