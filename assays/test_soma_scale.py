from __future__ import annotations

"""Tests for soma-scale — Fly.io machine resizer."""

import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest


# ── Load effector via exec (scripts aren't importable modules) ───────

def _load_module():
    """Load soma-scale by exec-ing, with urlopen mocked."""
    source = open(str(Path.home() / "germline/effectors/soma-scale")).read()
    mock_urlopen = MagicMock()
    ns: dict = {"__name__": "soma_scale", "__builtins__": __builtins__}
    exec(source, ns)
    # Replace urlopen in the module namespace
    ns["urlopen"] = mock_urlopen
    return ns


_mod = _load_module()
_token = _mod["_token"]
_api = _mod["_api"]
_fmt_guest = _mod["_fmt_guest"]
build_parser = _mod["build_parser"]
cmd_status = _mod["cmd_status"]
cmd_resize = _mod["cmd_resize"]
main = _mod["main"]
PROFILES = _mod["PROFILES"]
API_BASE = _mod["API_BASE"]
APP_NAME = _mod["APP_NAME"]
mock_urlopen = _mod["urlopen"]


# ── reset mock before each test ──────────────────────────────────────

@pytest.fixture(autouse=True)
def _reset_urlopen():
    mock_urlopen.reset_mock()
    yield


# ── helpers ──────────────────────────────────────────────────────────

def _mock_response(body):
    """Create a fake urllib response usable as context manager."""
    resp = MagicMock()
    raw = json.dumps(body).encode() if body else b""
    resp.read.return_value = raw
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def _machine_resp(**overrides):
    """Build a machine dict for API responses."""
    m = {
        "id": "m_abc",
        "state": "started",
        "region": "sjc",
        "config": {"guest": {"cpus": 2, "cpu_kind": "shared", "memory_mb": 8192}},
    }
    m.update(overrides)
    return m


# ── _token ───────────────────────────────────────────────────────────


def test_token_returns_env_value():
    """_token returns the FLY_API_TOKEN from env."""
    with patch.dict(os.environ, {"FLY_API_TOKEN": "tok_abc"}):
        assert _token() == "tok_abc"


def test_token_missing_exits():
    """_token exits when FLY_API_TOKEN is not set."""
    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("FLY_API_TOKEN", None)
        with pytest.raises(SystemExit):
            _token()


# ── _api ─────────────────────────────────────────────────────────────


def test_api_get_parses_json():
    """_api GETs and parses JSON response."""
    mock_urlopen.return_value = _mock_response({"id": "m1"})
    with patch.dict(os.environ, {"FLY_API_TOKEN": "tok"}):
        result = _api("GET", "/v1/apps/soma/machines")
    assert result == {"id": "m1"}
    req = mock_urlopen.call_args[0][0]
    assert req.method == "GET"
    assert "/v1/apps/soma/machines" in req.full_url


def test_api_post_empty_body():
    """_api POST with no body returns empty dict."""
    mock_urlopen.return_value = _mock_response({})
    with patch.dict(os.environ, {"FLY_API_TOKEN": "tok"}):
        result = _api("POST", "/v1/apps/soma/machines/m1/stop")
    assert result == {}


def test_api_sets_auth_header():
    """_api sets Authorization: Bearer header."""
    mock_urlopen.return_value = _mock_response({})
    with patch.dict(os.environ, {"FLY_API_TOKEN": "secret"}):
        _api("GET", "/v1/apps/soma/machines")
    req = mock_urlopen.call_args[0][0]
    # Request._headers is a list of (name, value) tuples
    assert any("Authorization" in h and "Bearer secret" in v
               for h, v in req.header_items()), \
        f"Auth header not found in {list(req.header_items())}"


# ── _fmt_guest ───────────────────────────────────────────────────────


def test_fmt_guest_standard():
    """_fmt_guest renders cpus, kind, and memory."""
    assert _fmt_guest({"cpus": 8, "cpu_kind": "shared", "memory_mb": 32768}) == "8 CPU (shared), 32768 MB"


def test_fmt_guest_missing_fields():
    """_fmt_guest handles missing fields with '?'."""
    assert _fmt_guest({}) == "? CPU (?), ? MB"


# ── PROFILES ─────────────────────────────────────────────────────────


def test_profiles_up():
    """PROFILES['up'] has 8 shared CPUs and 32 GB."""
    assert PROFILES["up"]["guest"]["cpus"] == 8
    assert PROFILES["up"]["guest"]["memory_mb"] == 32768
    assert PROFILES["up"]["guest"]["cpu_kind"] == "shared"


def test_profiles_down():
    """PROFILES['down'] has 2 shared CPUs and 8 GB."""
    assert PROFILES["down"]["guest"]["cpus"] == 2
    assert PROFILES["down"]["guest"]["memory_mb"] == 8192


# ── cmd_status ───────────────────────────────────────────────────────


def test_cmd_status_prints_info(capsys):
    """cmd_status prints machine id, state, region, and guest config."""
    mock_urlopen.return_value = _mock_response([_machine_resp()])
    with patch.dict(os.environ, {"FLY_API_TOKEN": "tok"}):
        cmd_status()
    out = capsys.readouterr().out
    assert "m_abc" in out
    assert "state=started" in out
    assert "region=sjc" in out
    assert "2 CPU (shared), 8192 MB" in out


def test_cmd_status_no_machines(capsys):
    """cmd_status handles empty machine list."""
    mock_urlopen.return_value = _mock_response([])
    with patch.dict(os.environ, {"FLY_API_TOKEN": "tok"}):
        cmd_status()
    out = capsys.readouterr().out
    assert "no machines" in out


# ── cmd_resize ───────────────────────────────────────────────────────


def test_cmd_resize_up_full_flow(capsys):
    """cmd_resize up: stop → patch → start, prints old→new."""
    mock_urlopen.return_value = _mock_response([_machine_resp()])
    with patch.dict(os.environ, {"FLY_API_TOKEN": "tok"}):
        cmd_resize("up")

    out = capsys.readouterr().out
    assert "stopping m_abc" in out
    assert "2 CPU (shared), 8192 MB → 8 CPU (shared), 32768 MB" in out
    assert "starting m_abc" in out
    assert "done:" in out

    # 4 calls: GET list, POST stop, PATCH config, POST start
    assert mock_urlopen.call_count == 4
    methods = [call[0][0].method for call in mock_urlopen.call_args_list]
    assert methods == ["GET", "POST", "PATCH", "POST"]


def test_cmd_resize_down(capsys):
    """cmd_resize down: scales from 8→2 CPU."""
    machine = _machine_resp(
        config={"guest": {"cpus": 8, "cpu_kind": "shared", "memory_mb": 32768}},
    )
    mock_urlopen.return_value = _mock_response([machine])
    with patch.dict(os.environ, {"FLY_API_TOKEN": "tok"}):
        cmd_resize("down")

    out = capsys.readouterr().out
    assert "8 CPU (shared), 32768 MB → 2 CPU (shared), 8192 MB" in out


def test_cmd_resize_skips_when_already_there(capsys):
    """cmd_resize skips stop/start when already at target config."""
    machine = _machine_resp(
        config={"guest": {"cpus": 8, "cpu_kind": "shared", "memory_mb": 32768}},
    )
    mock_urlopen.return_value = _mock_response([machine])
    with patch.dict(os.environ, {"FLY_API_TOKEN": "tok"}):
        cmd_resize("up")

    out = capsys.readouterr().out
    assert "already at" in out
    assert "nothing to do" in out
    # Only the list call, no stop/update/start
    assert mock_urlopen.call_count == 1


def test_cmd_resize_no_machines_exits():
    """cmd_resize exits when no machines found."""
    mock_urlopen.return_value = _mock_response([])
    with patch.dict(os.environ, {"FLY_API_TOKEN": "tok"}):
        with pytest.raises(SystemExit):
            cmd_resize("up")


def test_cmd_resize_patch_preserves_config():
    """PATCH body preserves existing config keys, swaps guest."""
    machine = _machine_resp(
        config={
            "guest": {"cpus": 2, "cpu_kind": "shared", "memory_mb": 8192},
            "image": "some-image",
            "env": {"FOO": "bar"},
        },
    )
    mock_urlopen.return_value = _mock_response([machine])
    with patch.dict(os.environ, {"FLY_API_TOKEN": "tok"}):
        cmd_resize("up")

    # Find the PATCH call (3rd urlopen call)
    patch_call = mock_urlopen.call_args_list[2]
    req = patch_call[0][0]
    assert req.method == "PATCH"
    body = json.loads(req.data)
    # Should preserve image and env, swap guest
    assert body["image"] == "some-image"
    assert body["env"] == {"FOO": "bar"}
    assert body["guest"]["cpus"] == 8
    assert body["guest"]["memory_mb"] == 32768


# ── main (CLI dispatch) ─────────────────────────────────────────────


def test_main_no_args_exits():
    """main exits with error when no args given."""
    with pytest.raises(SystemExit):
        main([])


def test_main_unknown_command_exits():
    """main exits for unknown commands."""
    with pytest.raises(SystemExit):
        main(["explode"])


def test_main_status(capsys):
    """main status dispatches to cmd_status."""
    mock_urlopen.return_value = _mock_response([_machine_resp()])
    with patch.dict(os.environ, {"FLY_API_TOKEN": "tok"}):
        main(["status"])
    out = capsys.readouterr().out
    assert "m_abc" in out


def test_main_up(capsys):
    """main up dispatches to cmd_resize."""
    mock_urlopen.return_value = _mock_response([_machine_resp()])
    with patch.dict(os.environ, {"FLY_API_TOKEN": "tok"}):
        main(["up"])
    out = capsys.readouterr().out
    assert "8 CPU (shared), 32768 MB" in out


# ── build_parser ─────────────────────────────────────────────────────


def test_build_parser_accepts_valid_commands():
    """build_parser accepts up, down, status."""
    p = build_parser()
    for cmd in ("up", "down", "status"):
        ns = p.parse_args([cmd])
        assert ns.command == cmd


def test_build_parser_rejects_invalid():
    """build_parser rejects unknown commands."""
    p = build_parser()
    with pytest.raises(SystemExit):
        p.parse_args(["explode"])
