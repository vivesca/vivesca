#!/usr/bin/env python3
from __future__ import annotations

"""Tests for mitosis-checkpoint.py effector."""


import pytest
import sys
from unittest.mock import MagicMock, patch
from pathlib import Path

# Execute the mitosis-checkpoint file directly
mitosis_path = Path(str(Path.home() / "germline/effectors/mitosis-checkpoint.py"))
mitosis_code = mitosis_path.read_text()
namespace = {}
exec(mitosis_code, namespace)

# Extract module
mitosis_checkpoint = type('mitosis_checkpoint_module', (), {})()
for key, value in namespace.items():
    if not key.startswith('__'):
        setattr(mitosis_checkpoint, key, value)


def test_venv_added_to_sys_path():
    """Test that venv site-packages is added to sys.path if it exists."""
    venv = Path.home() / "germline" / ".venv" / "lib"
    if venv.exists():
        site_packages = list(venv.glob("python*/site-packages"))
        for sp in site_packages:
            assert str(sp) in sys.path


def test_check_and_heal_all_healthy_silent():
    """Test when everything is healthy, nothing is alerted."""
    mock_status = MagicMock()
    mock_status.return_value = {
        "reachable": True,
        "targets": {
            "repo1": {"state": "ok"},
            "repo2": {"state": "ok"},
        }
    }

    with patch('metabolon.organelles.mitosis.status', mock_status):
        with patch('metabolon.organelles.mitosis.sync') as mock_sync:
            with patch.dict(namespace, {'_alert': MagicMock()}):
                namespace['check_and_heal']()
                mock_sync.assert_not_called()
                namespace['_alert'].assert_not_called()


def test_check_and_heal_unreachable_alerts():
    """Test when soma is unreachable after retry, it alerts."""
    mock_status = MagicMock()
    mock_status.return_value = {
        "reachable": False,
        "targets": {}
    }

    with patch('metabolon.organelles.mitosis.status', mock_status):
        with patch('time.sleep'):
            with patch.dict(namespace, {'_alert': MagicMock()}):
                namespace['check_and_heal']()
                namespace['_alert'].assert_called_once()
                assert "UNREACHABLE" in namespace['_alert'].call_args[0][0]
                assert mock_status.call_count == 2


def test_check_and_heal_self_heal_failure_alerts():
    """Test when self-heal fails it alerts."""
    mock_status = MagicMock()
    mock_status.return_value = {
        "reachable": True,
        "targets": {
            "sick-repo": {"state": "stale"},
        }
    }

    mock_report = MagicMock()
    mock_report.ok = True
    mock_result = MagicMock()
    mock_result.target = "sick-repo"
    mock_result.success = False
    mock_result.message = "Connection timeout"
    mock_report.results = [mock_result]

    with patch('metabolon.organelles.mitosis.status', mock_status):
        with patch('metabolon.organelles.mitosis.sync', return_value=mock_report):
            with patch.dict(namespace, {'_alert': MagicMock()}):
                namespace['check_and_heal']()
                namespace['_alert'].assert_called_once()
                assert "Connection timeout" in namespace['_alert'].call_args[0][0]


def test_check_and_heal_still_sick_after_sync_alerts():
    """Test when still sick after sync it alerts."""
    status_responses = [
        {"reachable": True, "targets": {"sick-repo": {"state": "stale"}}},
        {"reachable": True, "targets": {"sick-repo": {"state": "stale"}}},
    ]

    mock_report = MagicMock()
    mock_report.ok = True
    mock_result = MagicMock()
    mock_result.target = "sick-repo"
    mock_result.success = True
    mock_report.results = [mock_result]

    with patch('metabolon.organelles.mitosis.status', side_effect=status_responses):
        with patch('metabolon.organelles.mitosis.sync', return_value=mock_report):
            with patch.dict(namespace, {'_alert': MagicMock()}):
                namespace['check_and_heal']()
                namespace['_alert'].assert_called_once()
                assert "still degraded" in namespace['_alert'].call_args[0][0]


def test_main_handles_crash():
    """Test that main alerts on crash and exits with 1."""
    with patch.dict(namespace, {'check_and_heal': MagicMock(side_effect=RuntimeError("boom"))}):
        with patch.dict(namespace, {'_alert': MagicMock()}):
            with patch('sys.argv', ['mitosis-checkpoint']):
                with pytest.raises(SystemExit) as excinfo:
                    namespace['main']()
                namespace['_alert'].assert_called_once()
                assert "crashed" in namespace['_alert'].call_args[0][0]
                assert excinfo.value.code == 1


def test_alert_passes_cooldown_to_transport():
    """Test that _alert passes cooldown_key to secrete_text."""
    with patch('metabolon.organelles.secretory_vesicle.secrete_text', return_value="sent") as mock_secrete:
        with patch('builtins.print'):
            namespace['_alert']("test message", cooldown_key="test-key")
            mock_secrete.assert_called_once()
            call_kwargs = mock_secrete.call_args[1]
            assert call_kwargs["cooldown_key"] == "test-key"
            assert call_kwargs["cooldown_seconds"] == 24 * 3600


def test_alert_reports_throttled():
    """Test that _alert prints THROTTLED when transport returns throttled."""
    with patch('metabolon.organelles.secretory_vesicle.secrete_text', return_value="throttled"):
        with patch('builtins.print') as mock_print:
            namespace['_alert']("test message", cooldown_key="test-key")
            calls = [str(c) for c in mock_print.call_args_list]
            assert any("THROTTLED" in c for c in calls)


def test_alert_prints_to_stderr():
    """Test that alert always prints to stderr."""
    with patch('builtins.print') as mock_print:
        with patch('metabolon.organelles.secretory_vesicle.secrete_text', side_effect=Exception("down")):
            namespace['_alert']("Test message")
            mock_print.assert_called()
            call_args = mock_print.call_args_list[0]
            assert "ALERT:" in call_args[0][0]
            assert call_args[1]['file'] == sys.stderr
