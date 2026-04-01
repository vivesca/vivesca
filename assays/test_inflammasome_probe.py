#!/usr/bin/env python3
from __future__ import annotations

"""Tests for inflammasome-probe effector — mocks all external file I/O and subprocess."""


import json
import pytest
import subprocess
import sys
from unittest.mock import MagicMock, mock_open, patch, PropertyMock
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Get reference to current module for patching
current_module = sys.modules[__name__]

# Execute the inflammasome-probe file directly into the current module
inflammasome_probe_code = Path(str(Path.home() / "germline/effectors/inflammasome-probe")).read_text()
exec(inflammasome_probe_code, globals())

# ---------------------------------------------------------------------------
# Test cooldown handling
# ---------------------------------------------------------------------------

def test_load_cooldown_file_missing():
    """Test _load_cooldown returns empty dict when file missing."""
    with patch.object(type(_COOLDOWN_PATH), 'exists', return_value=False):
        result = _load_cooldown()
        assert result == {}

def test_load_cooldown_valid_file():
    """Test _load_cooldown correctly loads valid cooldown data."""
    mock_data = {
        "probe1": "2026-03-30T10:00:00",
        "probe2": "2026-03-31T10:00:00"
    }
    with patch.object(type(_COOLDOWN_PATH), 'exists', return_value=True):
        with patch.object(type(_COOLDOWN_PATH), 'read_text', return_value=json.dumps(mock_data)):
            result = _load_cooldown()
            assert result == mock_data

def test_load_cooldown_corrupted_file():
    """Test _load_cooldown returns empty dict on corrupted JSON."""
    with patch.object(type(_COOLDOWN_PATH), 'exists', return_value=True):
        with patch.object(type(_COOLDOWN_PATH), 'read_text', return_value="not valid json"):
            result = _load_cooldown()
            assert result == {}

def test_save_cooldown_creates_parent_dirs():
    """Test _save_cooldown creates parent directories."""
    with patch('pathlib.Path.mkdir') as mock_mkdir:
        with patch('pathlib.Path.write_text') as mock_write:
            _save_cooldown({"probe": "2026-03-31"})
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
            mock_write.assert_called_once()

def test_save_cooldown_handles_errors_gracefully():
    """Test _save_cooldown doesn't throw exceptions on write error."""
    with patch('pathlib.Path.mkdir'):
        with patch('pathlib.Path.write_text', side_effect=Exception("permission denied")):
            # Should not raise
            _save_cooldown({"probe": "2026-03-31"})

def test_is_on_cooldown_not_in_cooldown():
    """Test _is_on_cooldown returns False when probe not on cooldown."""
    cooldown = {"other": "2026-03-31"}
    assert _is_on_cooldown("probe", cooldown) is False

def test_is_on_cooldown_within_cooldown_period():
    """Test _is_on_cooldown returns True when within 24h cooldown."""
    recent = datetime.now(UTC) - timedelta(hours=12)
    cooldown = {"probe": recent.isoformat()}
    assert _is_on_cooldown("probe", cooldown) is True

def test_is_on_cooldown_after_cooldown_period():
    """Test _is_on_cooldown returns False after cooldown period."""
    old = datetime.now(UTC) - timedelta(days=2)
    cooldown = {"probe": old.isoformat()}
    assert _is_on_cooldown("probe", cooldown) is False

def test_is_on_cooldown_invalid_timestamp():
    """Test _is_on_cooldown returns False for invalid timestamps."""
    cooldown = {"probe": "not a timestamp"}
    assert _is_on_cooldown("probe", cooldown) is False

# ---------------------------------------------------------------------------
# Test novel failure detection
# ---------------------------------------------------------------------------

def test_is_novel_failure_import_error_returns_true():
    """Test _is_novel_failure returns True when import fails (conservative)."""
    with patch('metabolon.metabolism.infection.recall_infections', side_effect=ImportError("no module")):
        assert _is_novel_failure("probe") is True

def test_is_novel_failure_few_unhealed_returns_true():
    """Test _is_novel_failure returns True when fewer than 3 unhealed."""
    mock_recall = MagicMock()
    mock_recall.return_value = [
        {"tool": "self_test_failure:probe", "healed": False},
        {"tool": "self_test_failure:probe", "healed": True},  # healed doesn't count
    ]
    
    with patch('metabolon.metabolism.infection.recall_infections', mock_recall):
        assert _is_novel_failure("probe") is True

def test_is_novel_failure_enough_unhealed_returns_false():
    """Test _is_novel_failure returns False when >= 3 unhealed."""
    mock_recall = MagicMock()
    mock_recall.return_value = [
        {"tool": "self_test_failure:probe", "healed": False},
        {"tool": "self_test_failure:probe", "healed": False},
        {"tool": "self_test_failure:probe", "healed": False},
    ]
    
    with patch('metabolon.metabolism.infection.recall_infections', mock_recall):
        assert _is_novel_failure("probe") is False

# ---------------------------------------------------------------------------
# Test repair model routing
# ---------------------------------------------------------------------------

def test_repair_model_fallback_on_import_error():
    """Test _repair_model falls back to 'sonnet' when import fails."""
    with patch('metabolon.organelles.tissue_routing.route', side_effect=ImportError("no module")):
        assert _repair_model() == "sonnet"

# ---------------------------------------------------------------------------
# Test dispatch diagnosis
# ---------------------------------------------------------------------------

def test_dispatch_diagnosis_success():
    """Test _dispatch_diagnosis returns output on successful run."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "FIXED: fixed permissions on data directory"
    mock_result.stderr = ""
    
    with patch(f"{current_module.__name__}._repair_model", return_value="sonnet"):
        with patch('subprocess.run', return_value=mock_result):
            with patch(f"{current_module.__name__}._record_mitophagy") as mock_record:
                output = _dispatch_diagnosis("probe", "test message")
                assert output.startswith("FIXED:")
                assert "fixed permissions" in output
                mock_record.assert_called_once()

def test_dispatch_diagnosis_timeout():
    """Test _dispatch_diagnosis handles timeout and returns UNFIXED."""
    with patch(f"{current_module.__name__}._repair_model", return_value="sonnet"):
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired(["cmd"], 120)):
            with patch(f"{current_module.__name__}._record_mitophagy") as mock_record:
                output = _dispatch_diagnosis("probe", "test message")
                assert output.startswith("UNFIXED:")
                assert "timed out" in output.lower()
                mock_record.assert_called_once()

def test_dispatch_diagnosis_exception():
    """Test _dispatch_diagnosis handles exceptions and returns UNFIXED."""
    with patch(f"{current_module.__name__}._repair_model", return_value="sonnet"):
        with patch('subprocess.run', side_effect=Exception("network error")):
            with patch(f"{current_module.__name__}._record_mitophagy") as mock_record:
                output = _dispatch_diagnosis("probe", "test message")
                assert output.startswith("UNFIXED:")
                assert "dispatch error" in output
                mock_record.assert_called_once()

# ---------------------------------------------------------------------------
# Test log methylation candidate
# ---------------------------------------------------------------------------

def test_log_methylation_candidate_creates_dirs():
    """Test _log_methylation_candidate creates parent directories."""
    with patch('pathlib.Path.mkdir') as mock_mkdir:
        with patch('pathlib.Path.open', mock_open()):
            _log_methylation_candidate("probe", "failure", "fixed")
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

def test_log_methylation_candidate_handles_errors():
    """Test _log_methylation_candidate doesn't throw on errors."""
    with patch('pathlib.Path.mkdir', side_effect=Exception("perm denied")):
        # Should not raise
        _log_methylation_candidate("probe", "failure", "fixed")

# ---------------------------------------------------------------------------
# Test novel_failure_repair filtering
# ---------------------------------------------------------------------------

def test_novel_failure_repair_skips_passed_probes():
    """Test novel_failure_repair skips probes that already passed."""
    results = [{"name": "probe1", "passed": True}]
    cooldown = {}
    
    with patch(f"{current_module.__name__}._load_cooldown", return_value=cooldown):
        with patch(f"{current_module.__name__}._is_novel_failure", return_value=True):
            with patch(f"{current_module.__name__}._is_on_cooldown", return_value=False):
                with patch('subprocess.run') as mock_run:
                    novel_failure_repair(results, "test")
                    mock_run.assert_not_called()

def test_novel_failure_repair_skips_already_repaired():
    """Test novel_failure_repair skips probes that already had repair attempted."""
    results = [{"name": "probe1", "passed": False, "repair_attempted": "adaptive"}]
    
    with patch(f"{current_module.__name__}._load_cooldown", return_value={}):
        with patch('subprocess.run') as mock_run:
            novel_failure_repair(results, "test")
            mock_run.assert_not_called()

def test_novel_failure_repair_skips_rheotaxis_not_set():
    """Test novel_failure_repair skips rheotaxis with 'not set' message (known issue)."""
    results = [{"name": "rheotaxis", "passed": False, "repair_attempted": None, "message": "env not set"}]
    
    with patch(f"{current_module.__name__}._load_cooldown", return_value={}):
        with patch('subprocess.run') as mock_run:
            novel_failure_repair(results, "2026-03-31T00:00:00Z")
            mock_run.assert_not_called()

def test_novel_failure_repair_skips_non_novel():
    """Test novel_failure_repair skips non-novel failures."""
    results = [{"name": "probe1", "passed": False, "repair_attempted": None}]
    
    with patch(f"{current_module.__name__}._load_cooldown", return_value={}):
        with patch(f"{current_module.__name__}._is_novel_failure", return_value=False):
            with patch('subprocess.run') as mock_run:
                novel_failure_repair(results, "test")
                mock_run.assert_not_called()

def test_novel_failure_repair_skips_cooldown():
    """Test novel_failure_repair skips on 24h cooldown."""
    results = [{"name": "probe1", "passed": False, "repair_attempted": None}]
    
    with patch(f"{current_module.__name__}._load_cooldown", return_value={}):
        with patch(f"{current_module.__name__}._is_novel_failure", return_value=True):
            with patch(f"{current_module.__name__}._is_on_cooldown", return_value=True):
                with patch('subprocess.run') as mock_run:
                    novel_failure_repair(results, "test")
                    mock_run.assert_not_called()

def test_novel_failure_repair_respects_max_repairs_cap():
    """Test novel_failure_repair caps repairs at _MAX_REPAIRS_PER_CYCLE."""
    # Create 3 failed probes but cap is 2
    results = [
        {"name": "probe1", "passed": False, "repair_attempted": None},
        {"name": "probe2", "passed": False, "repair_attempted": None},
        {"name": "probe3", "passed": False, "repair_attempted": None},
    ]
    
    def mock_import(name, *args, **kwargs):
        if name == "metabolon.organelles.crispr" or name.startswith("metabolon.organelles.crispr."):
            raise ImportError("no crispr")
        return __import__(name, *args, **kwargs)
    
    with patch(f"{current_module.__name__}._load_cooldown", return_value={}):
        with patch(f"{current_module.__name__}._is_novel_failure", return_value=True):
            with patch(f"{current_module.__name__}._is_on_cooldown", return_value=False):
                with patch('builtins.__import__', side_effect=mock_import):
                    with patch(f"{current_module.__name__}._dispatch_diagnosis", return_value="FIXED: test"):
                        with patch(f"{current_module.__name__}._save_cooldown"):
                            with patch(f"{current_module.__name__}._log_methylation_candidate"):
                                # Allow import of infection
                                novel_failure_repair(results, "test")
                                # First two get repair_attempted set, third doesn't
                                assert results[0]["repair_attempted"] == "agent:fixed"
                                assert results[1]["repair_attempted"] == "agent:fixed"
                                assert results[2]["repair_attempted"] is None

def test_novel_failure_repair_handles_fixed_result():
    """Test novel_failure_repair correctly handles FIXED result from agent."""
    results = [{"name": "probe1", "passed": False, "repair_attempted": None, "message": "test failure"}]
    
    def mock_import(name, *args, **kwargs):
        if name == "metabolon.organelles.crispr" or name.startswith("metabolon.organelles.crispr."):
            raise ImportError("no crispr")
        return __import__(name, *args, **kwargs)
    
    # Just verify that repair_attempted is correctly set - record_infection is best effort
    with patch(f"{current_module.__name__}._load_cooldown", return_value={}):
        with patch(f"{current_module.__name__}._is_novel_failure", return_value=True):
            with patch(f"{current_module.__name__}._is_on_cooldown", return_value=False):
                with patch('builtins.__import__', side_effect=mock_import):
                    with patch(f"{current_module.__name__}._dispatch_diagnosis", return_value="FIXED: fixed the issue"):
                        with patch(f"{current_module.__name__}._save_cooldown"):
                            with patch(f"{current_module.__name__}._log_methylation_candidate") as mock_log:
                                novel_failure_repair(results, "test")
                                assert results[0]["repair_attempted"] == "agent:fixed"
                                mock_log.assert_called_once()

def test_novel_failure_repair_handles_unfixed_result():
    """Test novel_failure_repair correctly handles UNFIXED result from agent."""
    results = [{"name": "probe1", "passed": False, "repair_attempted": None, "message": "test failure"}]
    
    def mock_import(name, *args, **kwargs):
        if name == "metabolon.organelles.crispr" or name.startswith("metabolon.organelles.crispr."):
            raise ImportError("no crispr")
        return __import__(name, *args, **kwargs)
    
    with patch(f"{current_module.__name__}._load_cooldown", return_value={}):
        with patch(f"{current_module.__name__}._is_novel_failure", return_value=True):
            with patch(f"{current_module.__name__}._is_on_cooldown", return_value=False):
                with patch('builtins.__import__', side_effect=mock_import):
                    with patch(f"{current_module.__name__}._dispatch_diagnosis", return_value="UNFIXED: could not reproduce"):
                        with patch(f"{current_module.__name__}._save_cooldown"):
                            novel_failure_repair(results, "test")
                            assert results[0]["repair_attempted"] == "agent:unfixed"

# ---------------------------------------------------------------------------
# Test that script can be executed without errors (basic smoke test)
# ---------------------------------------------------------------------------

def test_script_executable():
    """Test that the script is marked executable and can be parsed."""
    probe_path = Path(str(Path.home() / "germline/effectors/inflammasome-probe"))
    assert probe_path.exists()
    assert (probe_path.stat().st_mode & 0o111) != 0  # Has executable bit

def test_script_entry_point_exists():
    """Test that main function exists and is callable."""
    assert 'main' in globals()
    assert callable(main)

# ---------------------------------------------------------------------------
# Test record_mitophagy (it's best-effort, must not throw)
# ---------------------------------------------------------------------------

def test_record_mitophagy_import_error_no_throw():
    """Test _record_mitophagy doesn't throw when import fails."""
    # Should not raise
    with patch('builtins.__import__', side_effect=ImportError("no module")):
        _record_mitophagy("model", "task", True, 1000)
