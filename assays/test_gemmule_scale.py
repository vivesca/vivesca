#!/usr/bin/env python3
"""Tests for gemmule-scale effector — mocked HTTP via urlopen, no real Fly API calls."""
from __future__ import annotations

import json
import os
from io import BytesIO
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

# The effector uses urllib.request.urlopen inside _api.  Because the code was
# loaded via exec(), patching a module-attribute name won't intercept the
# function calls — we must mock at the point where the stdlib function is
# *looked up*, which is the effector namespace's copy of urlopen.
_URLOPEN_TARGET = "effectors.gemmule_scale.urlopen"


def _mock_urlopen(body: dict | list | None = None, status: int = 200) -> MagicMock:
    """Build a mock suitable for use as urlopen return value (context manager)."""
    resp = MagicMock()
    raw = json.dumps(body).encode() if body is not None else b""
    resp.read.return_value = raw
    resp.status = status
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
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


@pytest.fixture(autouse=True)
def _set_token():
    """Ensure FLY_API_TOKEN is set for every test."""
    with patch.dict(os.environ, {"FLY_API_TOKEN": "test-token"}, clear=False):
        yield


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
        with patch(_URLOPEN_TARGET, return_value=_mock_urlopen(MOCK_MACHINES)):
            cmd_status()
        out = capsys.readouterr().out
        assert "m-abc123" in out
        assert "started" in out
        assert "sjc" in out
        assert "2 CPU (shared), 8192 MB" in out

    def test_no_machines(self, capsys):
        with patch(_URLOPEN_TARGET, return_value=_mock_urlopen([])):
            cmd_status()
        out = capsys.readouterr().out
        assert "no machines found" in out


# ── cmd_resize ────────────────────────────────────────────────────────────────

class TestResize:
    def test_scale_up(self, capsys):
        with patch(_URLOPEN_TARGET, return_value=_mock_urlopen(MOCK_MACHINES)):
            cmd_resize("up")
        out = capsys.readouterr().out

        # Should print old -> new
        assert "8192 MB" in out
        assert "32768 MB" in out
        assert "8 CPU" in out

    def test_scale_down(self, capsys):
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
        with patch(_URLOPEN_TARGET, return_value=_mock_urlopen(up_machines)):
            cmd_resize("down")
        out = capsys.readouterr().out

        assert "32768 MB" in out
        assert "8192 MB" in out
        assert "2 CPU" in out

    def test_no_machines_exits(self):
        with patch(_URLOPEN_TARGET, return_value=_mock_urlopen([])):
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
        # We need to intercept the PATCH call to verify its body.
        # urlopen is called 4 times: list, stop, patch, start.
        # Use side_effect to capture the PATCH request body.
        captured_bodies: list[dict] = []

        def _fake_urlopen(req, **kw):
            if req.method == "PATCH":
                captured_bodies.append(json.loads(req.data))
            return _mock_urlopen(machines)

        with patch(_URLOPEN_TARGET, side_effect=_fake_urlopen):
            cmd_resize("up")

        assert len(captured_bodies) == 1
        body = captured_bodies[0]
        assert body["guest"]["cpus"] == 8
        assert body["guest"]["memory_mb"] == 32768
        assert body["image"] == "ghcr.io/example/gemmule:v2"
        assert body["env"] == {"FOO": "bar"}
        assert body["services"] == [{"port": 443}]


# ── main() CLI dispatch ──────────────────────────────────────────────────────

class TestMain:
    def test_main_status(self):
        with patch(_URLOPEN_TARGET, return_value=_mock_urlopen(MOCK_MACHINES)):
            main(["status"])

    def test_main_up(self, capsys):
        with patch(_URLOPEN_TARGET, return_value=_mock_urlopen(MOCK_MACHINES)):
            main(["up"])
        out = capsys.readouterr().out
        assert "32768 MB" in out

    def test_main_down(self, capsys):
        with patch(_URLOPEN_TARGET, return_value=_mock_urlopen(MOCK_MACHINES)):
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
