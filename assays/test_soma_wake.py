from __future__ import annotations

"""Tests for effectors/soma-wake — start soma Fly.io machine."""

import json
import sys
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ── Load effector via exec ──────────────────────────────────────────────────

def _load():
    source = (Path.home() / "germline" / "effectors" / "soma-wake").read_text()
    ns: dict = {"__name__": "soma_wake"}
    exec(source, ns)
    return ns


_mod = _load()
_token = _mod["_token"]
_api = _mod["_api"]
get_machine = _mod["get_machine"]
wake = _mod["wake"]
status = _mod["status"]
main = _mod["main"]
API_BASE = _mod["API_BASE"]
APP_NAME = _mod["APP_NAME"]

MOCK_MACHINE = {
    "id": "m-abc123",
    "state": "stopped",
    "region": "sjc",
    "config": {"guest": {"cpus": 2, "memory_mb": 512}},
}


# ── Helpers ─────────────────────────────────────────────────────────────────


def _mock_urlopen(response_body: bytes, status: int = 200):
    """Return a context-manager mock for urllib.request.urlopen."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = response_body
    mock_resp.__enter__ = lambda s: mock_resp
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_resp.status = status
    return mock_resp


# ── _token tests ────────────────────────────────────────────────────────────


def test_soma_wake_token_returns_env_value(monkeypatch):
    """_token returns FLY_API_TOKEN from environment."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok123")
    assert _token() == "tok123"


def test_soma_wake_token_missing_exits(monkeypatch, capsys):
    """_token prints error and exits when FLY_API_TOKEN not set."""
    monkeypatch.delenv("FLY_API_TOKEN", raising=False)
    with pytest.raises(SystemExit) as exc:
        _token()
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "FLY_API_TOKEN not set" in err


def test_token_empty_exits(monkeypatch, capsys):
    """_token exits when FLY_API_TOKEN is empty string."""
    monkeypatch.setenv("FLY_API_TOKEN", "")
    with pytest.raises(SystemExit):
        _token()


# ── _api tests ──────────────────────────────────────────────────────────────


def test_api_get_sends_request(monkeypatch):
    """_api sends GET request with correct headers and returns parsed JSON."""
    body = json.dumps([{"id": "m-1"}]).encode()
    mock_urlopen_fn = MagicMock(return_value=_mock_urlopen(body))

    monkeypatch.setenv("FLY_API_TOKEN", "tok")
    monkeypatch.setitem(_mod, "urlopen", mock_urlopen_fn)

    result = _api("GET", "/v1/test/path")
    assert result == [{"id": "m-1"}]

    # Verify the Request was built correctly
    call_args = mock_urlopen_fn.call_args
    req = call_args[0][0]
    assert req.full_url == f"{API_BASE}/v1/test/path"
    assert req.method == "GET"
    assert req.get_header("Authorization") == "Bearer tok"
    assert req.get_header("Content-type") == "application/json"


def test_api_post_sends_request(monkeypatch):
    """_api sends POST request correctly."""
    body = json.dumps({"ok": True}).encode()
    mock_urlopen_fn = MagicMock(return_value=_mock_urlopen(body))

    monkeypatch.setenv("FLY_API_TOKEN", "tok")
    monkeypatch.setitem(_mod, "urlopen", mock_urlopen_fn)

    result = _api("POST", "/v1/apps/soma/machines/m-1/start")
    assert result == {"ok": True}

    call_args = mock_urlopen_fn.call_args
    req = call_args[0][0]
    assert req.method == "POST"


def test_soma_wake_api_empty_response(monkeypatch):
    """_api returns empty dict when response body is empty bytes."""
    mock_urlopen_fn = MagicMock(return_value=_mock_urlopen(b""))

    monkeypatch.setenv("FLY_API_TOKEN", "tok")
    monkeypatch.setitem(_mod, "urlopen", mock_urlopen_fn)

    result = _api("GET", "/v1/empty")
    assert result == {}


# ── get_machine tests ───────────────────────────────────────────────────────


def test_soma_wake_get_machine_returns_first(monkeypatch):
    """get_machine returns the first machine from the API."""
    machines = [{"id": "m-1", "state": "started"}, {"id": "m-2", "state": "stopped"}]
    mock_urlopen_fn = MagicMock(return_value=_mock_urlopen(json.dumps(machines).encode()))

    monkeypatch.setenv("FLY_API_TOKEN", "tok")
    monkeypatch.setitem(_mod, "urlopen", mock_urlopen_fn)

    result = get_machine()
    assert result == {"id": "m-1", "state": "started"}


def test_get_machine_no_machines(monkeypatch):
    """get_machine returns None when no machines found."""
    mock_urlopen_fn = MagicMock(return_value=_mock_urlopen(json.dumps([]).encode()))

    monkeypatch.setenv("FLY_API_TOKEN", "tok")
    monkeypatch.setitem(_mod, "urlopen", mock_urlopen_fn)

    result = get_machine()
    assert result is None


# ── wake tests ──────────────────────────────────────────────────────────────


def test_wake_already_running(monkeypatch, capsys):
    """wake returns 0 and prints message when machine is already started."""
    machines = [{"id": "m-1", "state": "started"}]
    mock_urlopen_fn = MagicMock(return_value=_mock_urlopen(json.dumps(machines).encode()))

    monkeypatch.setenv("FLY_API_TOKEN", "tok")
    monkeypatch.setitem(_mod, "urlopen", mock_urlopen_fn)

    rc = wake()
    assert rc == 0
    out = capsys.readouterr().out
    assert "already running" in out
    assert "m-1" in out


def test_wake_starts_stopped_machine(monkeypatch, capsys):
    """wake sends start request when machine is stopped."""
    machines_data = [{"id": "m-1", "state": "stopped"}]
    start_response = {"ok": True}

    call_count = 0
    def fake_urlopen(req, **kw):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _mock_urlopen(json.dumps(machines_data).encode())
        else:
            return _mock_urlopen(json.dumps(start_response).encode())

    monkeypatch.setenv("FLY_API_TOKEN", "tok")
    monkeypatch.setitem(_mod, "urlopen", fake_urlopen)

    rc = wake()
    assert rc == 0
    out = capsys.readouterr().out
    assert "starting machine m-1" in out
    assert "start request sent" in out


def test_wake_starts_suspended_machine(monkeypatch, capsys):
    """wake sends start request when machine is suspended."""
    machines_data = [{"id": "m-2", "state": "suspended"}]

    call_count = 0
    def fake_urlopen(req, **kw):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _mock_urlopen(json.dumps(machines_data).encode())
        else:
            return _mock_urlopen(json.dumps({"ok": True}).encode())

    monkeypatch.setenv("FLY_API_TOKEN", "tok")
    monkeypatch.setitem(_mod, "urlopen", fake_urlopen)

    rc = wake()
    assert rc == 0
    out = capsys.readouterr().out
    assert "suspended" in out
    assert "start request sent" in out


def test_wake_no_machines(monkeypatch, capsys):
    """wake returns 1 when no machines found."""
    mock_urlopen_fn = MagicMock(return_value=_mock_urlopen(json.dumps([]).encode()))

    monkeypatch.setenv("FLY_API_TOKEN", "tok")
    monkeypatch.setitem(_mod, "urlopen", mock_urlopen_fn)

    rc = wake()
    assert rc == 1
    out = capsys.readouterr().out
    assert "no machines found" in out


def test_wake_unexpected_state(monkeypatch, capsys):
    """wake returns 1 for unexpected machine state."""
    machines = [{"id": "m-1", "state": "destroying"}]
    mock_urlopen_fn = MagicMock(return_value=_mock_urlopen(json.dumps(machines).encode()))

    monkeypatch.setenv("FLY_API_TOKEN", "tok")
    monkeypatch.setitem(_mod, "urlopen", mock_urlopen_fn)

    rc = wake()
    assert rc == 1
    out = capsys.readouterr().out
    assert "unexpected state" in out
    assert "destroying" in out


# ── status tests ────────────────────────────────────────────────────────────


def test_status_shows_machine_info(monkeypatch, capsys):
    """status prints machine id, state, region, and resources."""
    machine = {
        "id": "m-abc",
        "state": "started",
        "region": "sjc",
        "config": {"guest": {"cpus": 4, "memory_mb": 1024}},
    }
    mock_urlopen_fn = MagicMock(return_value=_mock_urlopen(json.dumps([machine]).encode()))

    monkeypatch.setenv("FLY_API_TOKEN", "tok")
    monkeypatch.setitem(_mod, "urlopen", mock_urlopen_fn)

    rc = status()
    assert rc == 0
    out = capsys.readouterr().out
    assert "m-abc" in out
    assert "started" in out
    assert "sjc" in out
    assert "4CPU" in out
    assert "1024MB" in out


def test_status_missing_config_fields(monkeypatch, capsys):
    """status handles missing config/guest fields gracefully."""
    machine = {"id": "m-x", "state": "stopped", "region": "iad"}
    mock_urlopen_fn = MagicMock(return_value=_mock_urlopen(json.dumps([machine]).encode()))

    monkeypatch.setenv("FLY_API_TOKEN", "tok")
    monkeypatch.setitem(_mod, "urlopen", mock_urlopen_fn)

    rc = status()
    assert rc == 0
    out = capsys.readouterr().out
    assert "?CPU" in out
    assert "?MB" in out


def test_status_no_machines(monkeypatch, capsys):
    """status returns 1 when no machines found."""
    mock_urlopen_fn = MagicMock(return_value=_mock_urlopen(json.dumps([]).encode()))

    monkeypatch.setenv("FLY_API_TOKEN", "tok")
    monkeypatch.setitem(_mod, "urlopen", mock_urlopen_fn)

    rc = status()
    assert rc == 1
    out = capsys.readouterr().out
    assert "no machines found" in out


# ── main dispatch tests ─────────────────────────────────────────────────────


def test_main_calls_wake_by_default(monkeypatch, capsys):
    """main calls wake() when no --status flag is given."""
    machines = [{"id": "m-1", "state": "started"}]
    mock_urlopen_fn = MagicMock(return_value=_mock_urlopen(json.dumps(machines).encode()))

    monkeypatch.setenv("FLY_API_TOKEN", "tok")
    monkeypatch.setitem(_mod, "urlopen", mock_urlopen_fn)
    monkeypatch.setattr(sys, "argv", ["soma-wake"])

    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "already running" in out


def test_main_calls_status_with_flag(monkeypatch, capsys):
    """main calls status() when --status flag is given."""
    machine = {
        "id": "m-1",
        "state": "started",
        "region": "sjc",
        "config": {"guest": {"cpus": 2, "memory_mb": 512}},
    }
    mock_urlopen_fn = MagicMock(return_value=_mock_urlopen(json.dumps([machine]).encode()))

    monkeypatch.setenv("FLY_API_TOKEN", "tok")
    monkeypatch.setitem(_mod, "urlopen", mock_urlopen_fn)
    monkeypatch.setattr(sys, "argv", ["soma-wake", "--status"])

    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "m-1" in out


def test_main_calls_status_with_bare_status(monkeypatch, capsys):
    """main calls status() when 'status' is passed as a bare argument."""
    machine = {
        "id": "m-1",
        "state": "started",
        "region": "sjc",
        "config": {"guest": {"cpus": 2, "memory_mb": 512}},
    }
    mock_urlopen_fn = MagicMock(return_value=_mock_urlopen(json.dumps([machine]).encode()))

    monkeypatch.setenv("FLY_API_TOKEN", "tok")
    monkeypatch.setitem(_mod, "urlopen", mock_urlopen_fn)
    monkeypatch.setattr(sys, "argv", ["soma-wake", "status"])

    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "m-1" in out


# ── Constants tests ─────────────────────────────────────────────────────────


def test_soma_wake_constants():
    """Verify expected API base and app name constants."""
    assert API_BASE == "https://api.machines.dev"
    assert APP_NAME == "soma"
