from __future__ import annotations

"""Tests for gemmule-wake — Fly.io machine starter."""

import json
import sys
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest


def _load_gemmule_wake():
    """Load the gemmule-wake module by exec-ing its Python body."""
    source = open("/home/terry/germline/effectors/gemmule-wake").read()
    ns: dict = {"__name__": "gemmule_wake"}
    exec(source, ns)
    return ns


_mod = _load_gemmule_wake()
_token = _mod["_token"]
_api = _mod["_api"]
get_machine = _mod["get_machine"]
wake = _mod["wake"]
status = _mod["status"]
main = _mod["main"]
API_BASE = _mod["API_BASE"]
APP_NAME = _mod["APP_NAME"]


def _mock_response(data: dict | list, status_code: int = 200) -> MagicMock:
    """Build a fake urlopen context-manager response."""
    resp = MagicMock()
    resp.read.return_value = json.dumps(data).encode()
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    resp.status = status_code
    return resp


# ── _token tests ───────────────────────────────────────────────────────


def test_token_returns_env_value(monkeypatch):
    """_token returns the FLY_API_TOKEN environment variable."""
    monkeypatch.setenv("FLY_API_TOKEN", "test-token-123")
    assert _token() == "test-token-123"


def test_token_missing_exits(monkeypatch):
    """_token calls sys.exit(1) when FLY_API_TOKEN is not set."""
    monkeypatch.delenv("FLY_API_TOKEN", raising=False)
    with pytest.raises(SystemExit) as exc_info:
        _token()
    assert exc_info.value.code == 1


def test_token_empty_exits(monkeypatch):
    """_token exits when FLY_API_TOKEN is empty string."""
    monkeypatch.setenv("FLY_API_TOKEN", "")
    with pytest.raises(SystemExit) as exc_info:
        _token()
    assert exc_info.value.code == 1


def test_token_error_message(monkeypatch, capsys):
    """_token prints error to stderr when token is missing."""
    monkeypatch.delenv("FLY_API_TOKEN", raising=False)
    with pytest.raises(SystemExit):
        _token()
    assert "FLY_API_TOKEN not set" in capsys.readouterr().err


# ── _api tests ─────────────────────────────────────────────────────────


def test_api_get_machines(monkeypatch):
    """_api sends GET request with correct URL and auth header."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok-abc")
    resp = _mock_response([{"id": "m1", "state": "started"}])
    _mod["urlopen"] = MagicMock(return_value=resp)

    result = _api("GET", f"/v1/apps/{APP_NAME}/machines")

    assert result == [{"id": "m1", "state": "started"}]
    call_args = _mod["urlopen"].call_args
    req = call_args[0][0]
    assert req.method == "GET"
    assert req.full_url == f"{API_BASE}/v1/apps/{APP_NAME}/machines"
    assert req.get_header("Authorization") == "Bearer tok-abc"
    assert req.get_header("Content-type") == "application/json"


def test_api_post_start_machine(monkeypatch):
    """_api sends POST request to start a machine."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok-abc")
    resp = _mock_response({})
    _mod["urlopen"] = MagicMock(return_value=resp)

    result = _api("POST", f"/v1/apps/{APP_NAME}/machines/m123/start")

    assert result == {}
    call_args = _mod["urlopen"].call_args
    req = call_args[0][0]
    assert req.method == "POST"


def test_api_empty_response(monkeypatch):
    """_api returns empty dict when response body is empty."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok-abc")
    resp = MagicMock()
    resp.read.return_value = b""
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    _mod["urlopen"] = MagicMock(return_value=resp)

    result = _api("GET", "/v1/apps/gemmule/machines")

    assert result == {}


# ── get_machine tests ──────────────────────────────────────────────────


def test_get_machine_returns_first(monkeypatch):
    """get_machine returns the first machine from the API."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok")
    machines = [
        {"id": "m1", "state": "started"},
        {"id": "m2", "state": "stopped"},
    ]
    _mod["urlopen"] = MagicMock(return_value=_mock_response(machines))

    result = get_machine()

    assert result == {"id": "m1", "state": "started"}


def test_get_machine_none_when_empty(monkeypatch):
    """get_machine returns None when no machines exist."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok")
    _mod["urlopen"] = MagicMock(return_value=_mock_response([]))

    result = get_machine()

    assert result is None


# ── wake tests ─────────────────────────────────────────────────────────


def test_wake_already_running(monkeypatch, capsys):
    """wake returns 0 and prints message when machine is already started."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok")
    _mod["urlopen"] = MagicMock(
        return_value=_mock_response([{"id": "m1", "state": "started"}])
    )

    rc = wake()

    assert rc == 0
    out = capsys.readouterr().out
    assert "already running" in out
    assert "m1" in out


def test_wake_starts_stopped_machine(monkeypatch, capsys):
    """wake sends start request when machine is stopped."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok")
    call_count = 0

    def fake_urlopen(req, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _mock_response([{"id": "m1", "state": "stopped"}])
        return _mock_response({})

    _mod["urlopen"] = fake_urlopen

    rc = wake()

    assert rc == 0
    out = capsys.readouterr().out
    assert "stopped" in out
    assert "start request sent" in out
    assert call_count == 2  # GET machines + POST start


def test_wake_starts_suspended_machine(monkeypatch, capsys):
    """wake sends start request when machine is suspended."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok")
    call_count = 0

    def fake_urlopen(req, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _mock_response([{"id": "m1", "state": "suspended"}])
        return _mock_response({})

    _mod["urlopen"] = fake_urlopen

    rc = wake()

    assert rc == 0
    out = capsys.readouterr().out
    assert "suspended" in out
    assert "start request sent" in out


def test_wake_no_machines(monkeypatch, capsys):
    """wake returns 1 when no machines found."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok")
    _mod["urlopen"] = MagicMock(return_value=_mock_response([]))

    rc = wake()

    assert rc == 1
    out = capsys.readouterr().out
    assert "no machines found" in out


def test_wake_unexpected_state(monkeypatch, capsys):
    """wake returns 1 for unexpected machine state."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok")
    _mod["urlopen"] = MagicMock(
        return_value=_mock_response([{"id": "m1", "state": "destroying"}])
    )

    rc = wake()

    assert rc == 1
    out = capsys.readouterr().out
    assert "unexpected state" in out
    assert "destroying" in out


# ── status tests ───────────────────────────────────────────────────────


def test_status_shows_machine_info(monkeypatch, capsys):
    """status prints machine id, state, region, cpu, and memory."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok")
    machine = {
        "id": "m1",
        "state": "started",
        "region": "sjc",
        "config": {"guest": {"cpus": 2, "memory_mb": 512}},
    }
    _mod["urlopen"] = MagicMock(return_value=_mock_response([machine]))

    rc = status()

    assert rc == 0
    out = capsys.readouterr().out
    assert "m1" in out
    assert "started" in out
    assert "sjc" in out
    assert "2CPU" in out
    assert "512MB" in out


def test_status_defaults_when_config_missing(monkeypatch, capsys):
    """status shows '?' for cpu/memory when config.guest is absent."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok")
    machine = {"id": "m2", "state": "stopped", "region": "ord"}
    _mod["urlopen"] = MagicMock(return_value=_mock_response([machine]))

    rc = status()

    assert rc == 0
    out = capsys.readouterr().out
    assert "?CPU" in out
    assert "?MB" in out


def test_status_no_machines(monkeypatch, capsys):
    """status returns 1 when no machines found."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok")
    _mod["urlopen"] = MagicMock(return_value=_mock_response([]))

    rc = status()

    assert rc == 1
    out = capsys.readouterr().out
    assert "no machines found" in out


def test_status_missing_state(monkeypatch, capsys):
    """status handles machine dict without state key."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok")
    machine = {"id": "m3", "region": "sea"}
    _mod["urlopen"] = MagicMock(return_value=_mock_response([machine]))

    rc = status()

    assert rc == 0
    out = capsys.readouterr().out
    assert "state=?" in out


# ── main dispatch tests ────────────────────────────────────────────────


def test_main_status_flag(monkeypatch):
    """main calls status() when --status flag is present."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok")
    monkeypatch.setattr(sys, "argv", ["gemmule-wake", "--status"])
    _mod["urlopen"] = MagicMock(
        return_value=_mock_response(
            [{"id": "m1", "state": "started", "region": "sjc"}]
        )
    )

    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0


def test_main_status_bare_word(monkeypatch):
    """main calls status() when 'status' is a positional arg."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok")
    monkeypatch.setattr(sys, "argv", ["gemmule-wake", "status"])
    _mod["urlopen"] = MagicMock(
        return_value=_mock_response(
            [{"id": "m1", "state": "started", "region": "sjc"}]
        )
    )

    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0


def test_main_default_wake(monkeypatch):
    """main calls wake() when no flags are present."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok")
    monkeypatch.setattr(sys, "argv", ["gemmule-wake"])
    _mod["urlopen"] = MagicMock(
        return_value=_mock_response([{"id": "m1", "state": "started"}])
    )

    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0


def test_main_wake_failure_exits_nonzero(monkeypatch):
    """main exits with wake's return code on failure."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok")
    monkeypatch.setattr(sys, "argv", ["gemmule-wake"])
    _mod["urlopen"] = MagicMock(return_value=_mock_response([]))

    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


# ── constants tests ────────────────────────────────────────────────────


def test_api_base_is_machines_dev():
    """API_BASE points to the Fly machines API."""
    assert API_BASE == "https://api.machines.dev"


def test_app_name_is_gemmule():
    """APP_NAME is set to 'gemmule'."""
    assert APP_NAME == "gemmule"


# ── _api timeout and error handling ────────────────────────────────────


def test_api_passes_timeout(monkeypatch):
    """_api passes timeout=15 to urlopen."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok")
    mock_urlopen = MagicMock(return_value=_mock_response({}))
    _mod["urlopen"] = mock_urlopen

    _api("GET", "/test")

    call_kwargs = mock_urlopen.call_args
    assert call_kwargs[1].get("timeout") == 15 or "timeout" in str(call_kwargs)
