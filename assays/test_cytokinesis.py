import json
import subprocess
from unittest.mock import patch
from metabolon.enzymes.cytokinesis import cytokinesis_gather, GatherResult


def test_cytokinesis_gather_success_no_warnings():
    mock_data = {
        "repos": {"germline": {"clean": True}},
        "skills": {},
        "memory": {"lines": 100, "limit": 150},
        "now": {"age_label": "fresh"},
        "rfts": [],
        "deps": [],
        "peira": None,
        "reflect": [],
        "methylation": [],
    }
    with patch("metabolon.enzymes.cytokinesis.subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = json.dumps(mock_data)
        result = cytokinesis_gather()
    
    assert isinstance(result, GatherResult)
    assert result.status == "ok"
    assert result.message == "clean"
    assert result.repos == mock_data["repos"]
    assert result.skills == mock_data["skills"]
    assert result.memory == mock_data["memory"]
    assert result.tonus == mock_data["now"]
    assert result.rfts == mock_data["rfts"]


def test_cytokinesis_gather_success_with_warnings():
    mock_data = {
        "repos": {"germline": {"clean": False}, "other": {"clean": True}},
        "skills": {},
        "memory": {"lines": 200, "limit": 150},
        "now": {"age_label": "stale"},
        "rfts": [1, 2, 3],
        "deps": ["dep1"],
        "peira": "test_peira",
        "reflect": ["reflect1"],
        "methylation": ["methyl1"],
    }
    with patch("metabolon.enzymes.cytokinesis.subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = json.dumps(mock_data)
        result = cytokinesis_gather()
    
    assert result.status == "warning"
    assert "MEMORY.md 200/150" in result.message
    assert "tonus stale" in result.message
    assert "3 stale marks" in result.message
    assert "dirty: germline" in result.message
    assert result.deps == ["dep1"]
    assert result.peira == "test_peira"
    assert result.reflect == ["reflect1"]
    assert result.methylation == ["methyl1"]


def test_cytokinesis_gather_non_zero_exit():
    with patch("metabolon.enzymes.cytokinesis.subprocess.run") as mock_run:
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = ""
        result = cytokinesis_gather()
    
    assert result.status == "error"
    assert "exit 1" in result.message


def test_cytokinesis_gather_json_decode_error():
    with patch("metabolon.enzymes.cytokinesis.subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "not valid json"
        result = cytokinesis_gather()
    
    assert result.status == "error"
    assert "failed" in result.message


def test_cytokinesis_gather_timeout_expired():
    with patch("metabolon.enzymes.cytokinesis.subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(["cytokinesis"], 90)
        result = cytokinesis_gather()
    
    assert result.status == "error"
    assert "failed" in result.message


def test_cytokinesis_gather_command_not_found():
    with patch("metabolon.enzymes.cytokinesis.subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError("cytokinesis not found")
        result = cytokinesis_gather()
    
    assert result.status == "error"
    assert "failed" in result.message
