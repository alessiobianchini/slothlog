import json
from unittest.mock import patch, MagicMock
import pytest

import parser


def test_fallback_summary_when_ollama_offline():
    messages = [
        "feat(PROJ-101): add login callback",
        "fix(PROJ-101): resolve null pointer on token",
        "wip tests"
    ]
    with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
        summary = parser.synthesize_summary("PROJ-101", messages)
        assert len(summary) > 0
        assert "login callback" in summary.lower()
        assert "null pointer" in summary.lower()


def test_ollama_synthesis_success():
    messages = ["feat: setup oauth flow", "fix: token refresh"]
    response_data = json.dumps({
        "response": "Implemented OAuth2 authentication flow and added token refresh handling.",
        "prompt_eval_count": 180,
        "eval_count": 45,
        "total_duration": 1800000000
    }).encode("utf-8")

    mock_resp = MagicMock()
    mock_resp.read.return_value = response_data
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_cm):
        summary = parser.synthesize_summary("AB#4920", messages, model="gemma2:2b")
        assert summary == "Implemented OAuth2 authentication flow and added token refresh handling."
