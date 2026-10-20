import pytest
import cluster


def test_extract_ticket_id():
    assert cluster.extract_ticket_id("feat(AB#4920): add reverse charge") == "AB#4920"
    assert cluster.extract_ticket_id("fix: #1029 resolve null pointer") == "#1029"
    assert cluster.extract_ticket_id("feat: PROJ-104 add PKCE exchange") == "PROJ-104"
    assert cluster.extract_ticket_id("feature/JIRA-8812-new-auth") == "JIRA-8812"
    assert cluster.extract_ticket_id("gh-42: handle timeout") == "gh-42"
    assert cluster.extract_ticket_id("chore: bump fastapi to 0.110.0") is None


def test_cluster_commits_single_session():
    commits = [
        {
            "hash": "hash1",
            "timestamp": "2026-10-20T09:00:00+02:00",
            "author": "Alessio",
            "branch": "feature/PROJ-101",
            "message": "feat(PROJ-101): setup auth flow",
            "repo": "billing-service"
        },
        {
            "hash": "hash2",
            "timestamp": "2026-10-20T10:30:00+02:00",
            "author": "Alessio",
            "branch": "feature/PROJ-101",
            "message": "feat(PROJ-101): add callback handler",
            "repo": "billing-service"
        }
    ]

    clusters = cluster.cluster_commits(commits)
    assert len(clusters) == 1
    c = clusters[0]
    assert c["ticket_id"] == "PROJ-101"
    assert c["repo"] == "billing-service"
    assert len(c["commit_messages"]) == 2
    # 9:00 to 10:30 = 1.5h + 0.5h buffer = 2.0h
    assert c["estimated_hours"] == 2.0


def test_cluster_commits_untagged_fallback():
    commits = [
        {
            "hash": "hash3",
            "timestamp": "2026-10-20T14:00:00+02:00",
            "author": "Alessio",
            "branch": "main",
            "message": "chore: clean up dockerfile",
            "repo": "portal-frontend"
        }
    ]

    clusters = cluster.cluster_commits(commits)
    assert len(clusters) == 1
    c = clusters[0]
    assert c["ticket_id"] == "General Maintenance"
    assert c["repo"] == "portal-frontend"
    assert c["estimated_hours"] == 0.5  # minimum default
