"""Tests for gemmule-scale — Fly.io machine resizer."""
from __future__ import annotations

import os
import sys
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest


# ── Load effector via exec (scripts aren't importable modules) ───────

def _load_module():
    """Load gemmule-scale by exec-ing, with requests mocked."""
    mock_requests = MagicMock()
    ns: dict = {"__name__": "gemmule_scale", "requests": mock_requests}
    source = open("/home/terry/germline/effectors/gemmule-scale").read()
    exec(source, ns)
    ns["_requests"] = mock_requests
    return ns


_mod = _load_module()
_requests = _mod["_requests"]
_headers = _mod["_headers"]
_list_machines = _mod["_list_machines"]
_pick_machine = _mod["_pick_machine"]
_machine_config = _mod["_machine_config"]
_stop = _mod["_stop"]
_update = _mod["_update"]
_start = _mod["_start"]
cmd_status = _mod["cmd_status"]
cmd_scale = _mod["cmd_scale"]
main = _mod["main"]
PROFILES = _mod["PROFILES"]


# ── _headers ─────────────────────────────────────────────────────────


def test_headers_returns_auth_bearer():
    """_headers includes Authorization: Bearer <token>."""
    with patch.dict(os.environ, {"FLY_API_TOKEN": "tok123"}):
        h = _headers()
    assert h["Authorization"] == "Bearer tok123"
    assert h["Content-Type"] == "application/json"


def test_headers_missing_token_exits():
    """_headers prints error and exits when FLY_API_TOKEN is unset."""
    with patch.dict(os.environ, {}, clear=True):
        # Remove FLY_API_TOKEN if present
        os.environ.pop("FLY_API_TOKEN", None)
        with pytest.raises(SystemExit):
            _headers()


# ── _list_machines ───────────────────────────────────────────────────


def test_list_machines_calls_correct_url():
    """_list_machines GETs /v1/apps/gemmule/machines."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = [{"id": "m1"}]
    mock_resp.raise_for_status = MagicMock()
    _requests.get.reset_mock(return_value=True)
    _requests.get.return_value = mock_resp

    with patch.dict(os.environ, {"FLY_API_TOKEN": "tok"}):
        result = _list_machines()

    _requests.get.assert_called_once()
    call_url = _requests.get.call_args[0][0]
    assert "/v1/apps/gemmule/machines" in call_url
    assert result == [{"id": "m1"}]


# ── _pick_machine ────────────────────────────────────────────────────


def test_pick_machine_prefers_non_leased():
    """_pick_machine returns first machine without a lease."""
    machines = [
        {"id": "leased", "lease": {"foo": "bar"}},
        {"id": "free"},
        {"id": "also_free"},
    ]
    assert _pick_machine(machines) == {"id": "free"}


def test_pick_machine_falls_back_to_first():
    """If all machines are leased, return the first one."""
    machines = [
        {"id": "a", "lease": {"x": 1}},
        {"id": "b", "lease": {"x": 2}},
    ]
    assert _pick_machine(machines) == machines[0]


# ── _machine_config ──────────────────────────────────────────────────


def test_machine_config_extracts_cpus_memory():
    """_machine_config pulls cpus and memory_mb from guest dict."""
    machine = {
        "id": "m1",
        "config": {"guest": {"cpus": 4, "memory_mb": 16384}},
    }
    cfg = _machine_config(machine)
    assert cfg == {"cpus": 4, "memory": 16384}


def test_machine_config_missing_guest():
    """_machine_config returns zeros when guest is absent."""
    assert _machine_config({"id": "m1"}) == {"cpus": 0, "memory": 0}


# ── _stop ────────────────────────────────────────────────────────────


def test_stop_posts_to_stop_endpoint():
    """_stop POSTs to /machines/<id>/stop."""
    mock_resp = MagicMock()
    _requests.post.return_value = mock_resp

    with patch.dict(os.environ, {"FLY_API_TOKEN": "tok"}):
        _stop("abc123")

    call_url = _requests.post.call_args[0][0]
    assert "/machines/abc123/stop" in call_url
    mock_resp.raise_for_status.assert_called_once()


# ── _update ──────────────────────────────────────────────────────────


def test_update_patches_machine_config():
    """_update PATCHes guest cpus and memory_mb."""
    mock_resp = MagicMock()
    _requests.patch.return_value = mock_resp

    with patch.dict(os.environ, {"FLY_API_TOKEN": "tok"}):
        _update("abc123", 8, 32768)

    call_url = _requests.patch.call_args[0][0]
    assert "/machines/abc123" in call_url
    payload = _requests.patch.call_args[1]["json"]
    assert payload == {"config": {"guest": {"cpus": 8, "memory_mb": 32768}}}
    mock_resp.raise_for_status.assert_called_once()


# ── _start ───────────────────────────────────────────────────────────


def test_start_posts_to_start_endpoint():
    """_start POSTs to /machines/<id>/start."""
    mock_resp = MagicMock()
    _requests.post.return_value = mock_resp

    with patch.dict(os.environ, {"FLY_API_TOKEN": "tok"}):
        _start("abc123")

    call_url = _requests.post.call_args[0][0]
    assert "/machines/abc123/start" in call_url
    mock_resp.raise_for_status.assert_called_once()


# ── cmd_status ───────────────────────────────────────────────────────


def test_cmd_status_prints_machine_info(capsys):
    """cmd_status prints machine id, state, cpus, and memory."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = [
        {
            "id": "m_abc",
            "state": "started",
            "config": {"guest": {"cpus": 2, "memory_mb": 8192}},
        }
    ]
    mock_resp.raise_for_status = MagicMock()
    _requests.get.return_value = mock_resp

    with patch.dict(os.environ, {"FLY_API_TOKEN": "tok"}):
        cmd_status()

    out = capsys.readouterr().out
    assert "m_abc" in out
    assert "cpus=2" in out
    assert "memory=8192" in out


def test_cmd_status_no_machines(capsys):
    """cmd_status handles empty machine list gracefully."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = []
    mock_resp.raise_for_status = MagicMock()
    _requests.get.return_value = mock_resp

    with patch.dict(os.environ, {"FLY_API_TOKEN": "tok"}):
        cmd_status()

    out = capsys.readouterr().out
    assert "No machines" in out


# ── cmd_scale ────────────────────────────────────────────────────────


def test_cmd_scale_up_full_flow(capsys):
    """cmd_scale up: stop → update(8,32768) → start, prints old→new."""
    list_resp = MagicMock()
    list_resp.json.return_value = [
        {
            "id": "m_scale",
            "state": "started",
            "config": {"guest": {"cpus": 2, "memory_mb": 8192}},
        }
    ]
    list_resp.raise_for_status = MagicMock()
    _requests.get.return_value = list_resp

    stop_resp = MagicMock()
    update_resp = MagicMock()
    start_resp = MagicMock()
    _requests.post.return_value = stop_resp  # first post = stop
    _requests.patch.return_value = update_resp
    # We need post to return stop_resp first, then start_resp
    _requests.post.side_effect = [stop_resp, start_resp]

    with patch.dict(os.environ, {"FLY_API_TOKEN": "tok"}):
        cmd_scale("up")

    out = capsys.readouterr().out
    assert "cpus 2->8" in out
    assert "memory 8192MB->32768" in out
    # Verify PATCH was called with up profile
    payload = _requests.patch.call_args[1]["json"]
    assert payload["config"]["guest"]["cpus"] == 8
    assert payload["config"]["guest"]["memory_mb"] == 32768


def test_cmd_scale_down_full_flow(capsys):
    """cmd_scale down: stop → update(2,8192) → start, prints old→new."""
    list_resp = MagicMock()
    list_resp.json.return_value = [
        {
            "id": "m_scale",
            "state": "started",
            "config": {"guest": {"cpus": 8, "memory_mb": 32768}},
        }
    ]
    list_resp.raise_for_status = MagicMock()
    _requests.get.return_value = list_resp
    _requests.post.side_effect = [MagicMock(), MagicMock()]
    _requests.patch.return_value = MagicMock()

    with patch.dict(os.environ, {"FLY_API_TOKEN": "tok"}):
        cmd_scale("down")

    out = capsys.readouterr().out
    assert "cpus 8->2" in out
    assert "memory 32768MB->8192" in out
    payload = _requests.patch.call_args[1]["json"]
    assert payload["config"]["guest"]["cpus"] == 2
    assert payload["config"]["guest"]["memory_mb"] == 8192


def test_cmd_scale_no_machines_exits():
    """cmd_scale exits when no machines found."""
    list_resp = MagicMock()
    list_resp.json.return_value = []
    list_resp.raise_for_status = MagicMock()
    _requests.get.return_value = list_resp

    with patch.dict(os.environ, {"FLY_API_TOKEN": "tok"}):
        with pytest.raises(SystemExit):
            cmd_scale("up")


# ── main (CLI dispatch) ─────────────────────────────────────────────


def test_main_no_args_exits():
    """main exits with usage when no command given."""
    with patch.object(sys, "argv", ["gemmule-scale"]):
        with pytest.raises(SystemExit):
            main()


def test_main_unknown_command_exits():
    """main exits for unknown commands."""
    with patch.object(sys, "argv", ["gemmule-scale", "explode"]):
        with pytest.raises(SystemExit):
            main()


def test_main_status_dispatches(capsys):
    """main 'status' invokes cmd_status."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = [
        {
            "id": "m1",
            "state": "started",
            "config": {"guest": {"cpus": 2, "memory_mb": 8192}},
        }
    ]
    mock_resp.raise_for_status = MagicMock()
    _requests.get.return_value = mock_resp
    _requests.post.side_effect = None

    with patch.dict(os.environ, {"FLY_API_TOKEN": "tok"}):
        with patch.object(sys, "argv", ["gemmule-scale", "status"]):
            main()

    out = capsys.readouterr().out
    assert "m1" in out


# ── PROFILES constants ───────────────────────────────────────────────


def test_profiles_values():
    """PROFILES has correct up/down specs."""
    assert PROFILES["up"] == {"cpus": 8, "memory": 32768}
    assert PROFILES["down"] == {"cpus": 2, "memory": 8192}
