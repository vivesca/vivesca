"""Tests for cytokinesis enzyme."""
from unittest.mock import patch, MagicMock
import json
import subprocess
import pytest


def test_gather_clean_result():
    from metabolon.enzymes.cytokinesis import cytokinesis_gather

    clean_data = {
        "repos": {"germline": {"clean": True}},
        "memory": {"lines": 50, "limit": 150},
        "now": {"age_label": "fresh"},
        "rfts": [],
        "skills": {},
        "deps": [],
        "peira": None,
        "reflect": [],
        "methylation": [],
    }
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=json.dumps(clean_data))
        result = cytokinesis_gather()
        assert result.status == "ok"
        assert result.message == "clean"


def test_gather_dirty_repo_warning():
    from metabolon.enzymes.cytokinesis import cytokinesis_gather

    data = {
        "repos": {"germline": {"clean": False}},
        "memory": {"lines": 50, "limit": 150},
        "now": {"age_label": "fresh"},
        "rfts": [],
    }
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=json.dumps(data))
        result = cytokinesis_gather()
        assert result.status == "warning"
        assert "dirty" in result.message


def test_gather_memory_over_limit_warning():
    from metabolon.enzymes.cytokinesis import cytokinesis_gather

    data = {
        "repos": {},
        "memory": {"lines": 200, "limit": 150},
        "now": {"age_label": "fresh"},
        "rfts": [],
    }
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=json.dumps(data))
        result = cytokinesis_gather()
        assert result.status == "warning"
        assert "MEMORY.md" in result.message


def test_gather_stale_tonus_warning():
    from metabolon.enzymes.cytokinesis import cytokinesis_gather

    data = {
        "repos": {},
        "memory": {"lines": 50, "limit": 150},
        "now": {"age_label": "stale"},
        "rfts": [],
    }
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=json.dumps(data))
        result = cytokinesis_gather()
        assert result.status == "warning"
        assert "tonus stale" in result.message


def test_gather_nonzero_exit():
    from metabolon.enzymes.cytokinesis import cytokinesis_gather

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        result = cytokinesis_gather()
        assert result.status == "error"


def test_gather_timeout():
    from metabolon.enzymes.cytokinesis import cytokinesis_gather

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="cytokinesis", timeout=90)
        result = cytokinesis_gather()
        assert result.status == "error"


def test_gather_file_not_found():
    from metabolon.enzymes.cytokinesis import cytokinesis_gather

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError("cytokinesis not found")
        result = cytokinesis_gather()
        assert result.status == "error"


def test_gather_bad_json():
    from metabolon.enzymes.cytokinesis import cytokinesis_gather

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="not json")
        result = cytokinesis_gather()
        assert result.status == "error"
