#!/usr/bin/env python3
"""Tests for gemmule-scale effector — mocked HTTP via urlopen, no real Fly API calls."""
from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Load effector via exec (effectors are scripts, not importable packages)
_effector_path = Path(__file__).parent.parent / "effectors" / "gemmule-scale"
_ns: dict = {"__name__": "gemmule_scale", "__file__": str(_effector_path)}
exec(open(_effector_path).read(), _ns)  # noqa: S102

# Pull symbols from the exec namespace
main = _ns["main"]
cmd_status = _ns["cmd_status"]
cmd_resize = _ns["cmd_resize"]
get_primary = _ns["get_primary"]
fmt_config = _ns["fmt_config"]
PROFILES = _ns["PROFILES"]
_request = _ns["_request"]
_token = _ns["_token"]

# urlopen lives in the exec namespace; we patch it there.
_URLOPEN = "gemmule_scale.urlopen"


def _mock_resp(body: dict | list | None = None) -> MagicMock:
    """Context-manager mock that returns JSON body from urlopen."""
    resp = MagicMock()
    resp.read.return_value = json.dumps(body).encode() if body is not None else b""
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


TOK = "flytest-token-abc123"
MOCK_MACHINE = {
    "id": "m-abc123",
    "state": "started",
    "region": "sjc",
    "config": {
        "guest": {"cpus": 2, "cpu_kind": "shared", "memory_mb": 8192},
        "image": "ghcr.io/example/gemmule:latest",
    },
}
MOCK_MACHINE_UP = {
    "id": "m-abc123",
    "state": "started",
    "region": "sjc",
    "config": {
        "guest": {"cpus": 8, "cpu_kind": "shared", "memory_mb": 32768},
        "image": "ghcr.io/example/gemmule:latest",
    },
}


# ── fmt_config ────────────────────────────────────────────────────────────────

class TestFmtConfig:
    def test_normal(self):
        assert fmt_config(8, 32768) == "8 CPU, 32 GB RAM"

    def test_small(self):
        assert fmt_config(2, 8192) == "2 CPU, 8 GB RAM"


# ── get_primary ───────────────────────────────────────────────────────────────

class TestGetPrimary:
    def test_picks_first_non_autostop(self):
        machines = [
            {"id": "m1", "autostop": True},
            {"id": "m2"},
            {"id": "m3"},
        ]
        assert get_primary(machines)["id"] == "m2"

    def test_falls_back_to_first(self):
        machines = [{"id": "m1", "autostop": True}]
        assert get_primary(machines)["id"] == "m1"

    def test_empty_returns_none(self):
        assert get_primary([]) is None


# ── _token guard ──────────────────────────────────────────────────────────────

class TestToken:
    def test_missing_token_exits(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(SystemExit):
                _token()

    def test_valid_token(self):
        with patch.dict(os.environ, {"FLY_API_TOKEN": "ok"}, clear=True):
            assert _token() == "ok"


# ── cmd_status ────────────────────────────────────────────────────────────────

class TestStatus:
    def test_prints_machine_info(self, capsys):
        with patch(_URLOPEN, return_value=_mock_resp([MOCK_MACHINE])):
            cmd_status(TOK)
        out = capsys.readouterr().out
        assert "m-abc123" in out
        assert "started" in out
        assert "2 CPU" in out
        assert "8 GB RAM" in out

    def test_no_machines(self, capsys):
        with patch(_URLOPEN, return_value=_mock_resp([])):
            cmd_status(TOK)
        out = capsys.readouterr().out
        assert "no machines found" in out


# ── cmd_resize ────────────────────────────────────────────────────────────────

class TestResize:
    def test_scale_up(self, capsys):
        with patch(_URLOPEN, return_value=_mock_resp([MOCK_MACHINE])):
            cmd_resize(TOK, "up")
        out = capsys.readouterr().out
        assert "stopping" in out
        assert "starting" in out
        assert "2 CPU, 8 GB RAM" in out
        assert "8 CPU, 32 GB RAM" in out

    def test_scale_down(self, capsys):
        with patch(_URLOPEN, return_value=_mock_resp([MOCK_MACHINE_UP])):
            cmd_resize(TOK, "down")
        out = capsys.readouterr().out
        assert "8 CPU, 32 GB RAM" in out
        assert "2 CPU, 8 GB RAM" in out

    def test_already_at_target(self, capsys):
        with patch(_URLOPEN, return_value=_mock_resp([MOCK_MACHINE])):
            cmd_resize(TOK, "down")
        out = capsys.readouterr().out
        assert "already at" in out

    def test_no_machines_exits(self):
        with patch(_URLOPEN, return_value=_mock_resp([])):
            with pytest.raises(SystemExit):
                cmd_resize(TOK, "up")

    def test_update_sends_correct_body(self, capsys):
        captured: list[dict] = []

        def _capture(req, **kw):
            if req.method == "PATCH":
                captured.append(json.loads(req.data))
            return _mock_resp([MOCK_MACHINE])

        with patch(_URLOPEN, side_effect=_capture):
            cmd_resize(TOK, "up")

        assert len(captured) == 1
        body = captured[0]
        guest = body["config"]["guest"]
        assert guest["cpus"] == 8
        assert guest["memory_mb"] == 32768
        assert guest["cpu_kind"] == "shared"


# ── main() CLI dispatch ──────────────────────────────────────────────────────

class TestMain:
    @patch.dict(os.environ, {"FLY_API_TOKEN": TOK}, clear=True)
    def test_main_status(self, capsys):
        with patch(_URLOPEN, return_value=_mock_resp([MOCK_MACHINE])):
            main(["status"])
        out = capsys.readouterr().out
        assert "m-abc123" in out

    @patch.dict(os.environ, {"FLY_API_TOKEN": TOK}, clear=True)
    def test_main_up(self, capsys):
        with patch(_URLOPEN, return_value=_mock_resp([MOCK_MACHINE])):
            main(["up"])
        out = capsys.readouterr().out
        assert "32 GB RAM" in out

    @patch.dict(os.environ, {"FLY_API_TOKEN": TOK}, clear=True)
    def test_main_down(self, capsys):
        with patch(_URLOPEN, return_value=_mock_resp([MOCK_MACHINE_UP])):
            main(["down"])
        out = capsys.readouterr().out
        assert "8 GB RAM" in out

    def test_main_no_args_exits(self):
        with pytest.raises(SystemExit):
            main([])

    def test_main_bad_command_exits(self):
        with pytest.raises(SystemExit):
            main(["sideways"])


# ── profiles ──────────────────────────────────────────────────────────────────

class TestProfiles:
    def test_up(self):
        assert PROFILES["up"] == {"cpus": 8, "memory": 32768}

    def test_down(self):
        assert PROFILES["down"] == {"cpus": 2, "memory": 8192}
