#!/usr/bin/env python3
"""Tests for gemmule-scale effector — mocked HTTP, no real Fly API calls."""
from __future__ import annotations

import json
import types
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Load effector via exec (effectors are scripts, not importable packages)
_effector_path = Path(__file__).parent.parent / "effectors" / "gemmule-scale"
_ns: dict = {"__name__": "effectors.gemmule_scale", "__file__": str(_effector_path)}
exec(open(_effector_path).read(), _ns)  # noqa: S102

# Register as a real module so @patch works
_mod = types.ModuleType("effectors.gemmule_scale")
_mod.__dict__.update(_ns)
import sys
sys.modules["effectors.gemmule_scale"] = _mod

main = _ns["main"]
build_parser = _ns["build_parser"]
cmd_status = _ns["cmd_status"]
cmd_resize = _ns["cmd_resize"]
_fmt_guest = _ns["_fmt_guest"]
PROFILES = _ns["PROFILES"]

_API_TARGET = "effectors.gemmule_scale._api"


def _mock_response(body: dict | list, status: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.read.return_value = json.dumps(body).encode()
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    resp.status = status
    return resp


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


class TestFmtGuest:
    def test_full_guest(self):
        assert _fmt_guest({"cpus": 8, "cpu_kind": "shared", "memory_mb": 32768}) == "8 CPU (shared), 32768 MB"

    def test_minimal_guest(self):
        assert _fmt_guest({}) == "? CPU (?), ? MB"


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


class TestStatus:
    @patch(_API_TARGET, return_value=MOCK_MACHINES)
    def test_prints_machine_info(self, mock_api, capsys):
        cmd_status()
        out = capsys.readouterr().out
        assert "m-abc123" in out
        assert "started" in out
        assert "sjc" in out
        assert "2 CPU (shared), 8192 MB" in out
        mock_api.assert_called_once_with("GET", "/v1/apps/gemmule/machines")

    @patch(_API_TARGET, return_value=[])
    def test_no_machines(self, mock_api, capsys):
        cmd_status()
        out = capsys.readouterr().out
        assert "no machines found" in out


class TestResize:
    @patch(_API_TARGET)
    def test_scale_up(self, mock_api, capsys):
        mock_api.return_value = MOCK_MACHINES
        cmd_resize("up")
        out = capsys.readouterr().out

        # Should print old -> new
        assert "8192 MB" in out
        assert "32768 MB" in out
        assert "8 CPU" in out

        # Call sequence: list, stop, patch, start
        assert mock_api.call_count == 4
        calls = mock_api.call_args_list
        assert calls[0] == (("GET", "/v1/apps/gemmule/machines"),)
        assert calls[1] == (("POST", "/v1/apps/gemmule/machines/m-abc123/stop"),)
        assert calls[2][0][0] == "PATCH"
        assert calls[2][0][1] == "/v1/apps/gemmule/machines/m-abc123"
        patch_body = calls[2][1].get("body", calls[2][0][2] if len(calls[2][0]) > 2 else None)
        assert patch_body["guest"]["cpus"] == 8
        assert patch_body["guest"]["memory_mb"] == 32768
        assert calls[3] == (("POST", "/v1/apps/gemmule/machines/m-abc123/start"),)

    @patch(_API_TARGET)
    def test_scale_down(self, mock_api, capsys):
        up_machines = [
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
        mock_api.return_value = up_machines
        cmd_resize("down")
        out = capsys.readouterr().out

        assert "32768 MB" in out
        assert "8192 MB" in out
        assert "2 CPU" in out

    @patch(_API_TARGET, return_value=[])
    def test_no_machines_exits(self, mock_api):
        with pytest.raises(SystemExit):
            cmd_resize("up")

    @patch(_API_TARGET)
    def test_preserves_other_config(self, mock_api, capsys):
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
        mock_api.return_value = machines
        cmd_resize("up")

        # The PATCH call should preserve image, env, services
        patch_call = mock_api.call_args_list[2]
        body = patch_call[1]["body"]
        assert body["image"] == "ghcr.io/example/gemmule:v2"
        assert body["env"] == {"FOO": "bar"}
        assert body["services"] == [{"port": 443}]
        assert body["guest"]["cpus"] == 8


class TestMain:
    @patch("effectors.gemmule_scale.cmd_status")
    def test_main_status(self, mock_status):
        main(["status"])
        mock_status.assert_called_once()

    @patch("effectors.gemmule_scale.cmd_resize")
    def test_main_up(self, mock_resize):
        main(["up"])
        mock_resize.assert_called_once_with("up")

    @patch("effectors.gemmule_scale.cmd_resize")
    def test_main_down(self, mock_resize):
        main(["down"])
        mock_resize.assert_called_once_with("down")
