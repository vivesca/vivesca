#!/usr/bin/env python3
from __future__ import annotations

"""Tests for effectors/wewe-rss-health.py — Wechat2RSS health monitor."""


import json
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

EFFECTOR_PATH = Path(__file__).resolve().parents[1] / "effectors" / "wewe-rss-health.py"


def _load_module() -> dict:
    """Load wewe-rss-health via exec (effector pattern, not importable)."""
    source = EFFECTOR_PATH.read_text(encoding="utf-8")
    ns: dict = {"__name__": "wewe_rss_health", "__file__": str(EFFECTOR_PATH)}
    exec(source, ns)
    return ns


_mod = _load_module()


# ── File-level tests ────────────────────────────────────────────────────────


class TestFileBasics:
    def test_file_exists(self):
        assert EFFECTOR_PATH.exists()

    def test_is_python_script(self):
        assert EFFECTOR_PATH.read_text().split("\n")[0].startswith("#!/usr/bin/env python")

    def test_has_docstring(self):
        assert "Wechat2RSS health" in EFFECTOR_PATH.read_text()


# ── load_state tests ────────────────────────────────────────────────────────


class TestLoadState:
    def test_returns_state_when_file_exists(self, tmp_path, monkeypatch):
        state_file = tmp_path / "state.json"
        state_file.write_text(json.dumps({"last_status": "failing"}))
        monkeypatch.setitem(_mod, "STATE_FILE", state_file)
        assert _mod["load_state"]() == {"last_status": "failing"}

    def test_returns_default_when_file_missing(self, tmp_path, monkeypatch):
        state_file = tmp_path / "nonexistent.json"
        monkeypatch.setitem(_mod, "STATE_FILE", state_file)
        assert _mod["load_state"]() == {"last_status": "ok"}

    def test_empty_file_returns_default(self, tmp_path, monkeypatch):
        state_file = tmp_path / "state.json"
        state_file.write_text("")
        monkeypatch.setitem(_mod, "STATE_FILE", state_file)
        assert _mod["load_state"]() == {"last_status": "ok"}


# ── save_state tests ────────────────────────────────────────────────────────


class TestSaveState:
    def test_writes_json(self, tmp_path, monkeypatch):
        state_file = tmp_path / "state.json"
        monkeypatch.setitem(_mod, "STATE_FILE", state_file)
        _mod["save_state"]({"last_status": "ok"})
        assert json.loads(state_file.read_text()) == {"last_status": "ok"}

    def test_overwrites_existing(self, tmp_path, monkeypatch):
        state_file = tmp_path / "state.json"
        state_file.write_text(json.dumps({"last_status": "old"}))
        monkeypatch.setitem(_mod, "STATE_FILE", state_file)
        _mod["save_state"]({"last_status": "new"})
        assert json.loads(state_file.read_text()) == {"last_status": "new"}


# ── check_service tests ─────────────────────────────────────────────────────


class TestCheckService:
    def test_healthy_with_active_feeds(self, monkeypatch):
        data = {"err": None, "data": [{"paused": False}, {"paused": False}]}
        monkeypatch.setattr("urllib.request.Request", lambda url: None)
        monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout=10: None)
        monkeypatch.setattr("json.load", lambda f: data)
        healthy, detail = _mod["check_service"]()
        assert healthy is True
        assert "2 feed(s) active" in detail

    def test_unreachable_api(self, monkeypatch):
        def fail(*a, **kw):
            raise Exception("Connection refused")
        monkeypatch.setattr("urllib.request.Request", lambda url: None)
        monkeypatch.setattr("urllib.request.urlopen", fail)
        healthy, detail = _mod["check_service"]()
        assert healthy is False
        assert "API unreachable" in detail

    def test_api_error(self, monkeypatch):
        data = {"err": "invalid key", "data": []}
        monkeypatch.setattr("urllib.request.Request", lambda url: None)
        monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout=10: None)
        monkeypatch.setattr("json.load", lambda f: data)
        healthy, detail = _mod["check_service"]()
        assert healthy is False
        assert "API error" in detail

    def test_no_feeds(self, monkeypatch):
        data = {"err": None, "data": []}
        monkeypatch.setattr("urllib.request.Request", lambda url: None)
        monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout=10: None)
        monkeypatch.setattr("json.load", lambda f: data)
        healthy, detail = _mod["check_service"]()
        assert healthy is False
        assert "no feeds configured" in detail

    def test_paused_feeds(self, monkeypatch):
        data = {"err": None, "data": [{"paused": True}, {"paused": False}]}
        monkeypatch.setattr("urllib.request.Request", lambda url: None)
        monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout=10: None)
        monkeypatch.setattr("json.load", lambda f: data)
        healthy, detail = _mod["check_service"]()
        assert healthy is False
        assert "1/2 feeds paused" in detail


# ── send_alert tests ────────────────────────────────────────────────────────


class TestSendAlert:
    def test_calls_tg_script_when_exists(self, tmp_path, monkeypatch):
        tg = tmp_path / "tg-notify.sh"
        tg.write_text("#!/bin/bash\necho $1")
        monkeypatch.setitem(_mod, "TG_SCRIPT", tg)
        with patch("subprocess.run") as mock_run:
            _mod["send_alert"]("test message")
        mock_run.assert_called_once_with([str(tg), "test message"], timeout=10)

    def test_prints_to_stderr_when_no_script(self, tmp_path, monkeypatch, capsys):
        tg = tmp_path / "nonexistent.sh"
        monkeypatch.setitem(_mod, "TG_SCRIPT", tg)
        _mod["send_alert"]("emergency!")
        captured = capsys.readouterr()
        assert "emergency!" in captured.err


# ── main() tests ────────────────────────────────────────────────────────────


class TestMain:
    def test_alerts_on_transition_to_failing(self, tmp_path, monkeypatch):
        state_file = tmp_path / "state.json"
        state_file.write_text(json.dumps({"last_status": "ok"}))
        monkeypatch.setitem(_mod, "STATE_FILE", state_file)
        monkeypatch.setitem(_mod, "check_service", lambda: (False, "API unreachable"))
        monkeypatch.setattr("sys.argv", ["wewe-rss-health.py"])

        alerts = []
        monkeypatch.setitem(_mod, "send_alert", lambda msg: alerts.append(msg))
        _mod["main"]()

        assert len(alerts) == 1
        assert "unhealthy" in alerts[0].lower()

    def test_alerts_on_recovery(self, tmp_path, monkeypatch):
        state_file = tmp_path / "state.json"
        state_file.write_text(json.dumps({"last_status": "failing"}))
        monkeypatch.setitem(_mod, "STATE_FILE", state_file)
        monkeypatch.setitem(_mod, "check_service", lambda: (True, "5 feed(s) active"))
        monkeypatch.setattr("sys.argv", ["wewe-rss-health.py"])

        alerts = []
        monkeypatch.setitem(_mod, "send_alert", lambda msg: alerts.append(msg))
        _mod["main"]()

        assert len(alerts) == 1
        assert "recovered" in alerts[0].lower()

    def test_no_alert_when_stable_ok(self, tmp_path, monkeypatch):
        state_file = tmp_path / "state.json"
        state_file.write_text(json.dumps({"last_status": "ok"}))
        monkeypatch.setitem(_mod, "STATE_FILE", state_file)
        monkeypatch.setitem(_mod, "check_service", lambda: (True, "3 feed(s) active"))
        monkeypatch.setattr("sys.argv", ["wewe-rss-health.py"])

        alerts = []
        monkeypatch.setitem(_mod, "send_alert", lambda msg: alerts.append(msg))
        _mod["main"]()

        assert alerts == []

    def test_no_alert_when_stable_failing(self, tmp_path, monkeypatch):
        state_file = tmp_path / "state.json"
        state_file.write_text(json.dumps({"last_status": "failing"}))
        monkeypatch.setitem(_mod, "STATE_FILE", state_file)
        monkeypatch.setitem(_mod, "check_service", lambda: (False, "down"))
        monkeypatch.setattr("sys.argv", ["wewe-rss-health.py"])

        alerts = []
        monkeypatch.setitem(_mod, "send_alert", lambda msg: alerts.append(msg))
        _mod["main"]()

        assert alerts == []

    def test_saves_state_after_check(self, tmp_path, monkeypatch):
        state_file = tmp_path / "state.json"
        state_file.write_text(json.dumps({"last_status": "ok"}))
        monkeypatch.setitem(_mod, "STATE_FILE", state_file)
        monkeypatch.setitem(_mod, "check_service", lambda: (True, "ok"))
        monkeypatch.setattr("sys.argv", ["wewe-rss-health.py"])

        alerts = []
        monkeypatch.setitem(_mod, "send_alert", lambda msg: alerts.append(msg))
        _mod["main"]()

        saved = json.loads(state_file.read_text())
        assert saved["last_status"] == "ok"
        assert "checked" in saved
