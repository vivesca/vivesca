"""Tests for gemmule-scale — Fly.io machine resizer."""
from __future__ import annotations

import json
import os
import sys
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest


# ── Load effector via exec (scripts aren't importable modules) ───────

def _load_module():
    """Load gemmule-scale by exec-ing, mocking urllib.request.urlopen."""
    source = open("/home/terry/germline/effectors/gemmule-scale").read()
    # We mock urlopen by injecting a fake into the module's urllib.request namespace.
    # The effector does `from urllib.request import Request, urlopen` so we need
    # to provide those at exec time.
    from urllib.request import Request
    mock_urlopen = MagicMock()
    ns: dict = {
        "__name__": "gemmule_scale",
        "__builtins__": __builtins__,
    }
    # Let the exec use real imports except we'll override after
    exec(source, ns)
    # Replace urlopen in the module namespace
    ns["urlopen"] = mock_urlopen
    return ns


_mod = _load_module()
_token = _mod["_token"]
_headers = _mod["_headers"]
_request = _mod["_request"]
list_machines = _mod["list_machines"]
get_primary = _mod["get_primary"]
stop_machine = _mod["stop_machine"]
start_machine = _mod["start_machine"]
update_config = _mod["update_config"]
fmt_config = _mod["fmt_config"]
cmd_status = _mod["cmd_status"]
cmd_resize = _mod["cmd_resize"]
main = _mod["main"]
PROFILES = _mod["PROFILES"]
API_BASE = _mod["API_BASE"]
APP_NAME = _mod["APP_NAME"]
mock_urlopen = _mod["urlopen"]


# ── helpers ──────────────────────────────────────────────────────────

def _mock_response(body: dict | None = None, status: int = 200):
    """Create a fake urllib response object."""
    resp = MagicMock()
    raw = json.dumps(body).encode() if body else b""
    resp.read.return_value = raw
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=False)
    resp.status = status
    return resp


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


# ── _headers ─────────────────────────────────────────────────────────


def test_headers_contains_bearer():
    """_headers returns Authorization: Bearer header."""
    h = _headers("mytoken")
    assert h["Authorization"] == "Bearer mytoken"
    assert h["Content-Type"] == "application/json"


# ── _request ─────────────────────────────────────────────────────────


def test_request_get_success():
    """_request parses JSON response from urlopen."""
    mock_urlopen.return_value = _mock_response({"id": "m1"})
    result = _request("GET", "/v1/apps/gemmule/machines", "tok")
    assert result == {"id": "m1"}


def test_request_post_empty_response():
    """_request returns {} when response body is empty."""
    mock_urlopen.return_value = _mock_response(None)
    result = _request("POST", "/v1/apps/gemmule/machines/m1/stop", "tok")
    assert result == {}


# ── list_machines ────────────────────────────────────────────────────


def test_list_machines_calls_correct_path():
    """list_machines GETs /v1/apps/gemmule/machines."""
    mock_urlopen.return_value = _mock_response([{"id": "m1"}])
    result = list_machines("tok")
    assert result == [{"id": "m1"}]
    # Verify the URL passed to Request
    call_args = mock_urlopen.call_args
    req = call_args[0][0]
    assert "/v1/apps/gemmule/machines" in req.full_url


# ── get_primary ──────────────────────────────────────────────────────


def test_get_primary_prefers_non_autostopped():
    """get_primary returns first non-autostop machine."""
    machines = [
        {"id": "a", "autostop": True},
        {"id": "b"},
        {"id": "c"},
    ]
    assert get_primary(machines) == {"id": "b"}


def test_get_primary_all_autostop_returns_first():
    """get_primary falls back to first when all have autostop."""
    machines = [
        {"id": "a", "autostop": True},
        {"id": "b", "autostop": True},
    ]
    assert get_primary(machines) == machines[0]


def test_get_primary_empty_returns_none():
    """get_primary returns None for empty list."""
    assert get_primary([]) is None


# ── fmt_config ───────────────────────────────────────────────────────


def test_fmt_config_formats_cpus_and_gb():
    """fmt_config renders cpus and GB."""
    assert fmt_config(8, 32768) == "8 CPU, 32 GB RAM"
    assert fmt_config(2, 8192) == "2 CPU, 8 GB RAM"


# ── update_config ────────────────────────────────────────────────────


def test_update_config_sends_correct_payload():
    """update_config PATCHes with guest cpus and memory_mb."""
    mock_urlopen.return_value = _mock_response({})
    update_config("tok", "mid123", 8, 32768)
    req = mock_urlopen.call_args[0][0]
    assert req.method == "PATCH"
    assert "/machines/mid123" in req.full_url
    body = json.loads(req.data)
    assert body == {"config": {"guest": {"cpus": 8, "cpu_kind": "shared", "memory_mb": 32768}}}


# ── stop_machine / start_machine ─────────────────────────────────────


def test_stop_machine_posts_to_stop():
    """stop_machine POSTs to /machines/<id>/stop."""
    mock_urlopen.return_value = _mock_response({})
    stop_machine("tok", "mid1")
    req = mock_urlopen.call_args[0][0]
    assert req.method == "POST"
    assert "/machines/mid1/stop" in req.full_url


def test_start_machine_posts_to_start():
    """start_machine POSTs to /machines/<id>/start."""
    mock_urlopen.return_value = _mock_response({})
    start_machine("tok", "mid1")
    req = mock_urlopen.call_args[0][0]
    assert req.method == "POST"
    assert "/machines/mid1/start" in req.full_url


# ── cmd_status ───────────────────────────────────────────────────────


def test_cmd_status_prints_machine_info(capsys):
    """cmd_status prints machine id, state, cpus, and RAM."""
    mock_urlopen.return_value = _mock_response([
        {
            "id": "m_abc",
            "state": "started",
            "config": {"guest": {"cpus": 2, "memory_mb": 8192}},
        }
    ])
    cmd_status("tok")
    out = capsys.readouterr().out
    assert "m_abc" in out
    assert "state=started" in out
    assert "2 CPU, 8 GB RAM" in out


def test_cmd_status_no_machines(capsys):
    """cmd_status handles empty machine list."""
    mock_urlopen.return_value = _mock_response([])
    cmd_status("tok")
    out = capsys.readouterr().out
    assert "no machines" in out


# ── cmd_resize ───────────────────────────────────────────────────────


def test_cmd_resize_up(capsys):
    """cmd_resize up: stop → patch(8,32768) → start, prints old→new."""
    mock_urlopen.return_value = _mock_response([
        {
            "id": "m_scale",
            "state": "started",
            "config": {"guest": {"cpus": 2, "memory_mb": 8192}},
        }
    ])

    cmd_resize("tok", "up")

    out = capsys.readouterr().out
    assert "stopping m_scale" in out
    assert "2 CPU, 8 GB RAM → 8 CPU, 32 GB RAM" in out
    assert "starting m_scale" in out
    assert "done:" in out

    # Verify 3 urlopen calls: list, stop, update, start = 4 total
    assert mock_urlopen.call_count == 4
    # Check PATCH payload
    # Calls: list(GET), stop(POST), update(PATCH), start(POST)
    methods = []
    for call in mock_urlopen.call_args_list:
        req = call[0][0]
        methods.append(req.method)
    assert methods == ["GET", "POST", "PATCH", "POST"]


def test_cmd_resize_down(capsys):
    """cmd_resize down: scales from 8→2 CPU, 32→8 GB."""
    mock_urlopen.return_value = _mock_response([
        {
            "id": "m_big",
            "state": "started",
            "config": {"guest": {"cpus": 8, "memory_mb": 32768}},
        }
    ])

    cmd_resize("tok", "down")

    out = capsys.readouterr().out
    assert "8 CPU, 32 GB RAM → 2 CPU, 8 GB RAM" in out


def test_cmd_resize_no_change(capsys):
    """cmd_resize skips when already at target config."""
    mock_urlopen.return_value = _mock_response([
        {
            "id": "m_same",
            "state": "started",
            "config": {"guest": {"cpus": 8, "memory_mb": 32768}},
        }
    ])

    cmd_resize("tok", "up")

    out = capsys.readouterr().out
    assert "already at 8 CPU, 32 GB RAM" in out
    assert "nothing to do" in out
    # Only 1 urlopen call (list machines), no stop/update/start
    assert mock_urlopen.call_count == 1


def test_cmd_resize_no_machines_exits():
    """cmd_resize exits when no machines found."""
    mock_urlopen.return_value = _mock_response([])
    with pytest.raises(SystemExit):
        cmd_resize("tok", "up")


# ── main (CLI dispatch) ─────────────────────────────────────────────


def test_main_no_args_exits():
    """main exits with usage when no command given."""
    with pytest.raises(SystemExit):
        main([])


def test_main_unknown_command_exits():
    """main exits for unknown commands."""
    with pytest.raises(SystemExit):
        main(["explode"])


def test_main_status_dispatches(capsys):
    """main 'status' invokes cmd_status."""
    mock_urlopen.return_value = _mock_response([
        {
            "id": "m1",
            "state": "started",
            "config": {"guest": {"cpus": 2, "memory_mb": 8192}},
        }
    ])
    with patch.dict(os.environ, {"FLY_API_TOKEN": "tok"}):
        main(["status"])
    out = capsys.readouterr().out
    assert "m1" in out


def test_main_up_dispatches(capsys):
    """main 'up' invokes cmd_resize."""
    mock_urlopen.return_value = _mock_response([
        {
            "id": "m1",
            "state": "started",
            "config": {"guest": {"cpus": 2, "memory_mb": 8192}},
        }
    ])
    with patch.dict(os.environ, {"FLY_API_TOKEN": "tok"}):
        main(["up"])
    out = capsys.readouterr().out
    assert "8 CPU, 32 GB RAM" in out


# ── PROFILES constants ───────────────────────────────────────────────


def test_profiles_values():
    """PROFILES has correct up/down specs."""
    assert PROFILES["up"] == {"cpus": 8, "memory": 32768}
    assert PROFILES["down"] == {"cpus": 2, "memory": 8192}
