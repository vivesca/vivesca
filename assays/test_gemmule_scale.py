#!/usr/bin/env python3
"""Tests for gemmule-scale effector — mocked HTTP, no real Fly API calls."""
from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Load effector via exec (effectors are scripts, not importable packages)
_effector_path = Path(__file__).parent.parent / "effectors" / "gemmule-scale"
_ns: dict = {"__name__": "effectors.gemmule_scale", "__file__": str(_effector_path)}
exec(open(_effector_path).read(), _ns)  # noqa: S102

# Pull symbols from exec namespace
main = _ns["main"]
build_parser = _ns["build_parser"]
cmd_status = _ns["cmd_status"]
cmd_resize = _ns["cmd_resize"]
_fmt_guest = _ns["_fmt_guest"]
PROFILES = _ns["PROFILES"]


def _mock_api(return_value: dict | list | None = None) -> MagicMock:
    """Return a mock that replaces _api in the exec namespace."""
    m = MagicMock()
    m.return_value = return_value if return_value is not None else []
    return m


MOCK_MACHINES = [
    {
        "id": "m-abc123",
        "state": "started",
        "region": "sjc",
        "config": {
            "guest": {"cpus": 2, "cpu_kind": "shared", "memory_mb": 8192},
            "image": "ghcr.io/example/gemmule:latest",
        },
    }
]

MOCK_UP_MACHINES = [
    {
        "id": "m-xyz789",
        "state": "started",
        "region": "sjc",
        "config": {
            "guest": {"cpus": 8, "cpu_kind": "shared", "memory_mb": 32768},
            "image": "ghcr.io/example/gemmule:latest",
        },
    }
]


# ── _fmt_guest ────────────────────────────────────────────────────────────────

class TestFmtGuest:
    def test_full_guest(self):
        assert _fmt_guest({"cpus": 8, "cpu_kind": "shared", "memory_mb": 32768}) == "8 CPU (shared), 32768 MB"

    def test_minimal_guest(self):
        assert _fmt_guest({}) == "? CPU (?), ? MB"


# ── argparser ─────────────────────────────────────────────────────────────────

class TestParser:
    def test_up(self):
        args = build_parser().parse_args(["up"])
        assert args.command == "up"

    def test_down(self):
        args = build_parser().parse_args(["down"])
        assert args.command == "down"

    def test_status(self):
        args = build_parser().parse_args(["status"])
        assert args.command == "status"

    def test_invalid_exits(self):
        with pytest.raises(SystemExit):
            build_parser().parse_args(["explode"])


# ── cmd_status ────────────────────────────────────────────────────────────────

class TestStatus:
    def test_prints_machine_info(self, capsys):
        mock = _mock_api(MOCK_MACHINES)
        with patch.dict(_ns, {"_api": mock}):
            cmd_status()
        out = capsys.readouterr().out
        assert "m-abc123" in out
        assert "started" in out
        assert "sjc" in out
        assert "2 CPU (shared), 8192 MB" in out
        mock.assert_called_once_with("GET", "/v1/apps/gemmule/machines")

    def test_no_machines(self, capsys):
        with patch.dict(_ns, {"_api": _mock_api([])}):
            cmd_status()
        out = capsys.readouterr().out
        assert "no machines found" in out


# ── cmd_resize ────────────────────────────────────────────────────────────────

class TestResize:
    def test_scale_up(self, capsys):
        mock = _mock_api(MOCK_MACHINES)
        with patch.dict(_ns, {"_api": mock}):
            cmd_resize("up")
        out = capsys.readouterr().out

        assert "8192 MB" in out
        assert "32768 MB" in out
        assert "8 CPU" in out

        # Call sequence: list, stop, patch, start
        assert mock.call_count == 4
        calls = mock.call_args_list
        assert calls[0] == (("GET", "/v1/apps/gemmule/machines"),)
        assert calls[1] == (("POST", "/v1/apps/gemmule/machines/m-abc123/stop"),)
        assert calls[2][0][0] == "PATCH"
        assert calls[2][0][1] == "/v1/apps/gemmule/machines/m-abc123"
        patch_body = calls[2][1]["body"]
        assert patch_body["guest"]["cpus"] == 8
        assert patch_body["guest"]["memory_mb"] == 32768
        assert calls[3] == (("POST", "/v1/apps/gemmule/machines/m-abc123/start"),)

    def test_scale_down(self, capsys):
        mock = _mock_api(MOCK_UP_MACHINES)
        with patch.dict(_ns, {"_api": mock}):
            cmd_resize("down")
        out = capsys.readouterr().out

        assert "32768 MB" in out
        assert "8192 MB" in out
        assert "2 CPU" in out

    def test_no_machines_exits(self):
        with patch.dict(_ns, {"_api": _mock_api([])}):
            with pytest.raises(SystemExit):
                cmd_resize("up")

    def test_preserves_other_config(self, capsys):
        machines = [
            {
                "id": "m-keep",
                "state": "started",
                "region": "sjc",
                "config": {
                    "guest": {"cpus": 2, "cpu_kind": "shared", "memory_mb": 8192},
                    "image": "ghcr.io/example/gemmule:v2",
                    "env": {"FOO": "bar"},
                    "services": [{"port": 443}],
                },
            }
        ]
        mock = _mock_api(machines)
        with patch.dict(_ns, {"_api": mock}):
            cmd_resize("up")

        # The PATCH call (3rd call) should preserve image, env, services
        patch_call = mock.call_args_list[2]
        body = patch_call[1]["body"]
        assert body["guest"]["cpus"] == 8
        assert body["guest"]["memory_mb"] == 32768
        assert body["image"] == "ghcr.io/example/gemmule:v2"
        assert body["env"] == {"FOO": "bar"}
        assert body["services"] == [{"port": 443}]


# ── main() CLI dispatch ──────────────────────────────────────────────────────

class TestMain:
    def test_main_status(self, capsys):
        with patch.dict(_ns, {"_api": _mock_api(MOCK_MACHINES)}):
            main(["status"])
        out = capsys.readouterr().out
        assert "m-abc123" in out

    def test_main_up(self, capsys):
        with patch.dict(_ns, {"_api": _mock_api(MOCK_MACHINES)}):
            main(["up"])
        out = capsys.readouterr().out
        assert "32768 MB" in out

    def test_main_down(self, capsys):
        with patch.dict(_ns, {"_api": _mock_api(MOCK_UP_MACHINES)}):
            main(["down"])
        out = capsys.readouterr().out
        assert "8192 MB" in out


# ── env var guard ─────────────────────────────────────────────────────────────

class TestToken:
    def test_missing_token_exits(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(SystemExit):
                _ns["_token"]()


# ── profiles constant ─────────────────────────────────────────────────────────

class TestProfiles:
    def test_up_profile(self):
        assert PROFILES["up"]["guest"]["cpus"] == 8
        assert PROFILES["up"]["guest"]["memory_mb"] == 32768

    def test_down_profile(self):
        assert PROFILES["down"]["guest"]["cpus"] == 2
        assert PROFILES["down"]["guest"]["memory_mb"] == 8192
