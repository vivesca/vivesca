"""Tests for effectors/gemmule-scale — Fly.io machine resizer."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Load the effector as an importable module via exec
_SCRIPT = Path(__file__).resolve().parent.parent / "effectors" / "gemmule-scale"
_NS: dict = {"__name__": "gemmule_scale", "__file__": str(_SCRIPT)}
exec(compile(_SCRIPT.read_text(), _SCRIPT, "exec"), _NS)  # noqa: S102

# Pull symbols into module scope for convenience
cmd_status = _NS["cmd_status"]
cmd_scale = _NS["cmd_scale"]
cmd_main = _NS["main"]
_BASE = _NS["BASE"]
_APP = _NS["APP"]
_PROFILES = _NS["PROFILES"]

# ── Fixtures ──────────────────────────────────────────────────────────────────

MACHINE_ID = "abc123456789"
HEADERS = {"Authorization": "Bearer tok", "Content-Type": "application/json"}


def _machine_json(cpus: int = 4, memory: int = 16384, state: str = "started", leased: bool = False):
    return {
        "id": MACHINE_ID,
        "state": state,
        "config": {"guest": {"cpus": cpus, "memory_mb": memory}},
        **({"lease": {"nonce": "x"}} if leased else {}),
    }


def _mock_response(json_data=None, status_code=200):
    mock = MagicMock()
    mock.json.return_value = json_data or []
    mock.status_code = status_code
    mock.raise_for_status.return_value = None
    return mock


# ── cmd_status tests ──────────────────────────────────────────────────────────

@patch.dict(os.environ, {"FLY_API_TOKEN": "tok"}, clear=True)
@patch("requests.get")
def test_status_prints_config(mock_get, capsys):
    mock_get.return_value = _mock_response([_machine_json(cpus=4, memory=16384)])
    cmd_status()
    out = capsys.readouterr().out
    assert MACHINE_ID in out
    assert "cpus=4" in out
    assert "memory=16384MB" in out
    assert "state=started" in out
    mock_get.assert_called_once_with(
        f"{_BASE}/apps/{_APP}/machines", headers=HEADERS, timeout=30,
    )


@patch.dict(os.environ, {"FLY_API_TOKEN": "tok"}, clear=True)
@patch("requests.get")
def test_status_no_machines(mock_get, capsys):
    mock_get.return_value = _mock_response([])
    cmd_status()
    out = capsys.readouterr().out
    assert "No machines" in out


# ── cmd_scale tests ───────────────────────────────────────────────────────────

@patch.dict(os.environ, {"FLY_API_TOKEN": "tok"}, clear=True)
@patch("requests.post")
@patch("requests.patch")
@patch("requests.get")
def test_scale_up(mock_get, mock_patch, mock_post, capsys):
    mock_get.return_value = _mock_response([_machine_json(cpus=2, memory=8192)])
    mock_patch.return_value = _mock_response()
    mock_post.return_value = _mock_response()

    cmd_scale("up")

    out = capsys.readouterr().out
    assert "cpus=2 memory=8192MB" in out
    assert "->" in out
    assert "cpus=8" in out

    # Verify API call sequence: stop, start (patch verified separately)
    post_urls = [c[0][0] for c in mock_post.call_args_list]
    assert any("/stop" in u for u in post_urls), f"Expected /stop call, got {post_urls}"
    assert any("/start" in u for u in post_urls), f"Expected /start call, got {post_urls}"

    # Verify PATCH payload
    patch_call = mock_patch.call_args
    patch_url = patch_call[0][0]
    assert f"/machines/{MACHINE_ID}" in patch_url
    patch_body = patch_call[1]["json"]
    assert patch_body["config"]["guest"]["cpus"] == 8
    assert patch_body["config"]["guest"]["memory_mb"] == 32768


@patch.dict(os.environ, {"FLY_API_TOKEN": "tok"}, clear=True)
@patch("requests.post")
@patch("requests.patch")
@patch("requests.get")
def test_scale_down(mock_get, mock_patch, mock_post, capsys):
    mock_get.return_value = _mock_response([_machine_json(cpus=8, memory=32768)])
    mock_patch.return_value = _mock_response()
    mock_post.return_value = _mock_response()

    cmd_scale("down")

    out = capsys.readouterr().out
    assert "cpus=8 memory=32768MB" in out
    assert "cpus=2" in out

    patch_body = mock_patch.call_args[1]["json"]
    assert patch_body["config"]["guest"]["cpus"] == 2
    assert patch_body["config"]["guest"]["memory_mb"] == 8192


@patch.dict(os.environ, {"FLY_API_TOKEN": "tok"}, clear=True)
@patch("requests.get")
def test_scale_no_machines(mock_get):
    mock_get.return_value = _mock_response([])
    with pytest.raises(SystemExit):
        cmd_scale("up")


# ── _pick_machine logic ───────────────────────────────────────────────────────

def test_pick_machine_prefers_non_leased():
    pick = _NS["_pick_machine"]
    machines = [
        _machine_json(leased=True),
        _machine_json(cpus=4, memory=16384, leased=False),
    ]
    chosen = pick(machines)
    assert chosen["id"] == MACHINE_ID
    assert "lease" not in chosen or not chosen.get("lease")


def test_pick_machine_falls_back_to_leased():
    pick = _NS["_pick_machine"]
    machines = [_machine_json(leased=True)]
    chosen = pick(machines)
    assert chosen["id"] == MACHINE_ID


# ── main() CLI dispatch ──────────────────────────────────────────────────────

@patch.dict(os.environ, {"FLY_API_TOKEN": "tok"}, clear=True)
@patch("requests.get")
def test_main_status(mock_get, capsys):
    mock_get.return_value = _mock_response([_machine_json()])
    with patch.object(sys, "argv", ["gemmule-scale", "status"]):
        cmd_main()
    out = capsys.readouterr().out
    assert MACHINE_ID in out


def test_main_no_args():
    with patch.object(sys, "argv", ["gemmule-scale"]):
        with pytest.raises(SystemExit):
            cmd_main()


def test_main_bad_command():
    with patch.object(sys, "argv", ["gemmule-scale", "sideways"]):
        with pytest.raises(SystemExit):
            cmd_main()


# ── env var guard ─────────────────────────────────────────────────────────────

@patch.dict(os.environ, {}, clear=True)
def test_missing_token():
    with pytest.raises(SystemExit):
        _NS["_headers"]()


# ── profiles constant ─────────────────────────────────────────────────────────

def test_profiles():
    assert _PROFILES["up"] == {"cpus": 8, "memory": 32768}
    assert _PROFILES["down"] == {"cpus": 2, "memory": 8192}
