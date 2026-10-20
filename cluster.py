import re
from datetime import datetime
from typing import List, Dict, Optional

# Regex patterns for ticket identification
TICKET_PATTERNS = [
    re.compile(r'\b(AB#\d+)\b', re.IGNORECASE),
    re.compile(r'\b([A-Z][A-Z0-9]+-\d+)\b'),
    re.compile(r'\b(gh-\d+)\b', re.IGNORECASE),
    re.compile(r'(?<![A-Za-z0-9])(#\d{2,6})\b'),
]


def extract_ticket_id(text: str) -> Optional[str]:
    if not text:
        return None
    for pattern in TICKET_PATTERNS:
        match = pattern.search(text)
        if match:
            raw = match.group(1)
            # Normalize Jira keys to uppercase
            if "-" in raw and not raw.lower().startswith("gh-"):
                return raw.upper()
            if raw.lower().startswith("ab#"):
                return "AB#" + raw[3:]
            return raw
    return None


def _parse_iso_ts(ts_str: str) -> datetime:
    # Handles ISO timestamps like 2026-10-20T09:15:00+02:00
    return datetime.fromisoformat(ts_str)


def _round_to_quarter(hours: float) -> float:
    # Rounds to nearest 0.25 hours, minimum 0.5h
    rounded = round(hours * 4) / 4
    return max(0.5, rounded)


def cluster_commits(commits: List[Dict], gap_threshold_minutes: int = 90) -> List[Dict]:
    if not commits:
        return []

    # 1. Group commits by (repo, ticket_id)
    groups = {}
    for c in commits:
        ticket = extract_ticket_id(c.get("message", "")) or extract_ticket_id(c.get("branch", "")) or "General Maintenance"
        repo = c.get("repo", "Unknown")
        key = (repo, ticket)
        if key not in groups:
            groups[key] = []
        groups[key].append(c)

    clusters = []

    # 2. Process each group
    for (repo, ticket_id), group_commits in groups.items():
        # Sort chronologically
        sorted_commits = sorted(group_commits, key=lambda x: _parse_iso_ts(x["timestamp"]))
        
        # Calculate session time with gap clustering
        sessions = []
        current_session = [sorted_commits[0]]

        for next_commit in sorted_commits[1:]:
            prev_ts = _parse_iso_ts(current_session[-1]["timestamp"])
            next_ts = _parse_iso_ts(next_commit["timestamp"])
            diff_minutes = (next_ts - prev_ts).total_seconds() / 60.0

            if diff_minutes <= gap_threshold_minutes:
                current_session.append(next_commit)
            else:
                sessions.append(current_session)
                current_session = [next_commit]

        if current_session:
            sessions.append(current_session)

        # Sum durations across all sessions for this ticket
        total_hours = 0.0
        for s in sessions:
            if len(s) == 1:
                total_hours += 0.5  # default 30 min burst per isolated commit
            else:
                first = _parse_iso_ts(s[0]["timestamp"])
                last = _parse_iso_ts(s[-1]["timestamp"])
                diff_hours = (last - first).total_seconds() / 3600.0
                total_hours += diff_hours + 0.5  # span + 30 min wrapping buffer

        estimated_hours = _round_to_quarter(total_hours)
        messages = [c["message"] for c in sorted_commits]
        branch = sorted_commits[-1].get("branch", "main")

        clusters.append({
            "ticket_id": ticket_id,
            "repo": repo,
            "branch": branch,
            "first_commit": sorted_commits[0]["timestamp"],
            "last_commit": sorted_commits[-1]["timestamp"],
            "hours": estimated_hours,
            "estimated_hours": estimated_hours,
            "commits": sorted_commits,
            "commit_messages": messages,
            "commits_count": len(sorted_commits)
        })

    # Sort clusters: specific tickets first, General Maintenance last
    clusters.sort(key=lambda x: (x["ticket_id"] == "General Maintenance", x["ticket_id"]))
    return clusters
