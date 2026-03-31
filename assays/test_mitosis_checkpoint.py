#!/usr/bin/env python3
"""Tests for mitosis-checkpoint.py effector."""

from __future__ import annotations

import pytest
import sys
from unittest.mock import MagicMock, patch
from pathlib import Path

# Execute the mitosis-checkpoint file directly
mitosis_path = Path("/home/terry/germline/effectors/mitosis-checkpoint.py")
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
    # This already ran during exec, but check it logic works
    venv = Path.home() / "germline" / ".venv" / "lib"
    if venv.exists():
        # Should have found site-packages and added it
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
            with patch.object(mitosis_checkpoint, '_alert') as mock_alert:
                mitosis_checkpoint.check_and_heal()
                # Should not call sync or alert
                mock_sync.assert_not_called()
                mock_alert.assert_not_called()


def test_check_and_heal_unreachable_alerts():
    """Test when gemmule is unreachable, it alerts immediately."""
    mock_status = MagicMock()
    mock_status.return_value = {
        "reachable": False,
        "targets": {}
    }

    with patch('metabolon.organelles.mitosis.status', mock_status):
        with patch.dict(namespace, {'_alert': MagicMock()}) as mock_alert:
            # Update the module object with the mocked version
            setattr(mitosis_checkpoint, '_alert', namespace['_alert'])
            mitosis_checkpoint.check_and_heal()
            namespace['_alert'].assert_called_once()
            assert "UNREACHABLE" in namespace['_alert'].call_args[0][0]


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

    mock_sync = MagicMock()
    mock_sync.return_value = mock_report

    with patch('metabolon.organelles.mitosis.status', mock_status):
        with patch('metabolon.organelles.mitosis.sync', mock_sync):
            with patch.dict(namespace, {'_alert': MagicMock()}):
                setattr(mitosis_checkpoint, '_alert', namespace['_alert'])
                mitosis_checkpoint.check_and_heal()
                namespace['_alert'].assert_called_once()
                assert "Connection timeout" in namespace['_alert'].call_args[0][0]


def test_check_and_heal_still_sick_after_sync_alerts():
    """Test when still sick after sync it alerts."""
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
    mock_result.success = True
    mock_report.results = [mock_result]

    mock_sync = MagicMock()
    mock_sync.return_value = mock_report

    # Still sick after recheck
    mock_status2 = MagicMock()
    mock_status2.return_value = {
        "reachable": True,
        "targets": {
            "sick-repo": {"state": "stale"},
        }
    }

    with patch('metabolon.organelles.mitosis.status') as mock_status_call:
        mock_status_call.side_effect = [mock_status.return_value, mock_status2.return_value]
        with patch('metabolon.organelles.mitosis.sync', mock_sync):
            with patch.dict(namespace, {'_alert': MagicMock()}):
                setattr(mitosis_checkpoint, '_alert', namespace['_alert'])
                mitosis_checkpoint.check_and_heal()
                namespace['_alert'].assert_called_once()
                assert "still degraded" in namespace['_alert'].call_args[0][0]


def test_main_handles_crash():
    """Test that main alerts on crash and exits with 1."""
    with patch.dict(namespace, {'check_and_heal': MagicMock()}):
        namespace['check_and_heal'].side_effect = RuntimeError("Something went wrong")
        setattr(mitosis_checkpoint, 'check_and_heal', namespace['check_and_heal'])
        with patch.dict(namespace, {'_alert': MagicMock()}):
            setattr(mitosis_checkpoint, '_alert', namespace['_alert'])
            with pytest.raises(SystemExit) as excinfo:
                mitosis_checkpoint.main()
            namespace['_alert'].assert_called_once()
            assert "crashed" in namespace['_alert'].call_args[0][0]
            assert excinfo.value.code == 1


def test_alert_prints_to_stderr():
    """Test that alert always prints to stderr."""
    with patch('builtins.print') as mock_print:
        with patch('metabolon.organelles.secretory_vesicle.secrete_text', side_effect=Exception("Telegram down")):
            mitosis_checkpoint._alert("Test message")
            # Check that print was called with stderr
            mock_print.assert_called()
            call_args = mock_print.call_args_list[0]
            assert "ALERT: Test message" in call_args[0][0]
            assert call_args[1]['file'] == sys.stderr
