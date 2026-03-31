#!/usr/bin/env python3
"""Tests for effectors/wewe-rss-health.py — Wechat2RSS health monitor."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

EFFECTOR_PATH = Path(__file__).resolve().parents[1] / "effectors" / "wewe-rss-health.py"


def _load_module():
    """Load wewe-rss-health via exec (effector pattern, not importable)."""
    source = EFFECTOR_PATH.read_text(encoding="utf-8")
    ns: dict = {"__name__": "wewe_rss_health", "__file__": str(EFFECTOR_PATH)}
    exec(source, ns)
    return ns


_mod = _load_module()
load_state = _mod["load_state"]
save_state = _mod["save_state"]
send_alert = _mod["send_alert"]
check_service = _mod["check_service"]
main = _mod["main"]
STATE_FILE = _mod["STATE_FILE"]
API_URL = _mod["API_URL"]
TG_SCRIPT = _mod["TG_SCRIPT"]


# ── File-level tests ────────────────────────────────────────────────────────


class TestFileBasics:
    def test_file_exists(self):
        assert EFFECTOR_PATH.exists()
        assert EFFECTOR_PATH.is_file()

    def test_is_python_script(self):
        first_line = EFFECTOR_PATH.read_text().split("\n")[0]
        assert first_line.startswith("#!/usr/bin/env python")

    def test_has_docstring(self):
        source = EFFECTOR_PATH.read_text()
        assert "Wechat2RSS health" in source


# ── load_state tests ────────────────────────────────────────────────────────


class TestLoadState:
    def test_returns_state_when_file_exists(self, tmp_path, monkeypatch):
        state_file = tmp_path / "state.json"
        state_file.write_text(json.dumps({"last_status": "failing"}))
        monkeypatch.setitem(_mod, "STATE_FILE", state_file)
        result = load_state()
        assert result == {"last_status": "failing"}

    def test_returns_default_when_file_missing(self, tmp_path, monkeypatch):
        state_file = tmp_path / "nonexistent.json"
        monkeypatch.setitem(_mod, "STATE_FILE", state_file)
        result = load_state()
        assert result == {"last_status": "ok"}

    def test_raises_on_invalid_json(self, tmp_path, monkeypatch):
        state_file = tmp_path / "state.json"
        state_file.write_text("")
        monkeypatch.setitem(_mod, "STATE_FILE", state_file)
        with pytest.raises(json.JSONDecodeError):
            load_state()


# ── save_state tests ────────────────────────────────────────────────────────


class TestSaveState:
    def test_writes_json(self, tmp_path, monkeypatch):
        state_file = tmp_path / "state.json"
        monkeypatch.setitem(_mod, "STATE_FILE", state_file)
        save_state({"last_status": "ok"})
        assert json.loads(state_file.read_text()) == {"last_status": "ok"}

    def test_overwrites_existing(self, tmp_path, monkeypatch):
        state_file = tmp_path / "state.json"
        state_file.write_text(json.dumps({"last_status": "old"}))
        monkeypatch.setitem(_mod, "STATE_FILE", state_file)
        save_state({"last_status": "new"})
        assert json.loads(state_file.read_text()) == {"last_status": "new"}


# ── check_service tests ─────────────────────────────────────────────────────


class TestCheckService:
    def test_healthy_with_active_feeds(self):
        data = {"err": None, "data": [{"paused": False}, {"paused": False}]}
        with patch("urllib.request.Request"):
            with patch("urllib.request.urlopen") as mock_open:
                mock_resp = MagicMock()
                with patch("json.load", return_value=data):
                    mock_open.return_value = mock_resp
                    healthy, detail = check_service()
        assert healthy is True
        assert "2 feed(s) active" in detail

    def test_unreachable_api(self):
        with patch("urllib.request.Request"):
            with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
                healthy, detail = check_service()
        assert healthy is False
        assert "API unreachable" in detail

    def test_api_error(self):
        data = {"err": "invalid key", "data": []}
        with patch("urllib.request.Request"):
            with patch("urllib.request.urlopen") as mock_open:
                with patch("json.load", return_value=data):
                    mock_open.return_value = MagicMock()
                    healthy, detail = check_service()
        assert healthy is False
        assert "API error" in detail

    def test_no_feeds(self):
        data = {"err": None, "data": []}
        with patch("urllib.request.Request"):
            with patch("urllib.request.urlopen") as mock_open:
                with patch("json.load", return_value=data):
                    mock_open.return_value = MagicMock()
                    healthy, detail = check_service()
        assert healthy is False
        assert "no feeds configured" in detail

    def test_paused_feeds(self):
        data = {"err": None, "data": [{"paused": True}, {"paused": False}]}
        with patch("urllib.request.Request"):
            with patch("urllib.request.urlopen") as mock_open:
                with patch("json.load", return_value=data):
                    mock_open.return_value = MagicMock()
                    healthy, detail = check_service()
        assert healthy is False
        assert "1/2 feeds paused" in detail


# ── send_alert tests ────────────────────────────────────────────────────────


class TestSendAlert:
    def test_calls_tg_script_when_exists(self, tmp_path, monkeypatch):
        tg = tmp_path / "tg-notify.sh"
        tg.write_text("#!/bin/bash\necho $1")
        monkeypatch.setitem(_mod, "TG_SCRIPT", tg)
        with patch("subprocess.run") as mock_run:
            send_alert("test message")
        mock_run.assert_called_once_with([str(tg), "test message"], timeout=10)

    def test_prints_to_stderr_when_no_script(self, tmp_path, monkeypatch, capsys):
        tg = tmp_path / "nonexistent.sh"
        monkeypatch.setitem(_mod, "TG_SCRIPT", tg)
        send_alert("emergency!")
        captured = capsys.readouterr()
        assert "emergency!" in captured.err


# ── main() tests ────────────────────────────────────────────────────────────


class TestMain:
    def test_sends_alert_on_transition_to_failing(self, tmp_path, monkeypatch):
        """Alert sent when status goes from ok → failing."""
        state_file = tmp_path / "state.json"
        state_file.write_text(json.dumps({"last_status": "ok"}))
        monkeypatch.setitem(_mod, "STATE_FILE", state_file)
        monkeypatch.setitem(_mod, "check_service", MagicMock(return_value=(False, "API unreachable")))
        mock_alert = MagicMock()
        monkeypatch.setitem(_mod, "send_alert", mock_alert)

        main()

        mock_alert.assert_called_once()
        msg = mock_alert.call_args[0][0]
        assert "unhealthy" in msg.lower() or "API unreachable" in msg

    def test_sends_alert_on_recovery(self, tmp_path, monkeypatch):
        """Alert sent when status goes from failing → ok."""
        state_file = tmp_path / "state.json"
        state_file.write_text(json.dumps({"last_status": "failing"}))
        monkeypatch.setitem(_mod, "STATE_FILE", state_file)
        monkeypatch.setitem(_mod, "check_service", MagicMock(return_value=(True, "5 feed(s) active")))
        mock_alert = MagicMock()
        monkeypatch.setitem(_mod, "send_alert", mock_alert)

        main()

        mock_alert.assert_called_once()
        msg = mock_alert.call_args[0][0]
        assert "recovered" in msg.lower()

    def test_no_alert_when_stable_ok(self, tmp_path, monkeypatch):
        """No alert when status stays ok."""
        state_file = tmp_path / "state.json"
        state_file.write_text(json.dumps({"last_status": "ok"}))
        monkeypatch.setitem(_mod, "STATE_FILE", state_file)
        monkeypatch.setitem(_mod, "check_service", MagicMock(return_value=(True, "3 feed(s) active")))
        mock_alert = MagicMock()
        monkeypatch.setitem(_mod, "send_alert", mock_alert)

        main()

        mock_alert.assert_not_called()

    def test_no_alert_when_stable_failing(self, tmp_path, monkeypatch):
        """No alert when status stays failing (avoid spam)."""
        state_file = tmp_path / "state.json"
        state_file.write_text(json.dumps({"last_status": "failing"}))
        monkeypatch.setitem(_mod, "STATE_FILE", state_file)
        monkeypatch.setitem(_mod, "check_service", MagicMock(return_value=(False, "down")))
        mock_alert = MagicMock()
        monkeypatch.setitem(_mod, "send_alert", mock_alert)

        main()

        mock_alert.assert_not_called()

    def test_saves_state_after_check(self, tmp_path, monkeypatch):
        """State file is updated after each check."""
        state_file = tmp_path / "state.json"
        state_file.write_text(json.dumps({"last_status": "ok"}))
        monkeypatch.setitem(_mod, "STATE_FILE", state_file)
        monkeypatch.setitem(_mod, "check_service", MagicMock(return_value=(True, "ok")))
        monkeypatch.setitem(_mod, "send_alert", MagicMock())

        main()

        saved = json.loads(state_file.read_text())
        assert saved["last_status"] == "ok"
        assert "checked" in saved
