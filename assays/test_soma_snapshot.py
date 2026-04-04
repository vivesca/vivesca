from __future__ import annotations

"""Tests for soma-snapshot — Fly.io volume snapshot effector."""

import json
from pathlib import Path

import pytest


def _load_soma_snapshot():
    """Load the soma-snapshot module by exec-ing its Python body."""
    source = open(Path.home() / "germline/effectors/soma-snapshot").read()
    ns: dict = {"__name__": "soma_snapshot"}
    exec(source, ns)
    return ns


_mod = _load_soma_snapshot()
_token = _mod["_token"]
_api = _mod["_api"]
_get_machine = _mod["_get_machine"]
_get_volumes = _mod["_get_volumes"]
cmd_volume = _mod["cmd_volume"]
cmd_list = _mod["cmd_list"]
cmd_snapshot = _mod["cmd_snapshot"]
main = _mod["main"]
API_BASE = _mod["API_BASE"]
APP_NAME = _mod["APP_NAME"]


# ── helpers ────────────────────────────────────────────────────────────


class FakeResponse:
    """Minimal file-like object returned by urlopen."""

    def __init__(self, data: bytes = b""):
        self._data = data

    def read(self):
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def _make_urlopen(responses):
    """Return a mock urlopen that returns responses in order.

    Each element in *responses* is either bytes, a dict, or a list (auto-json-encoded).
    """
    it = iter(responses)

    def _urlopen(req, timeout=30):
        data = next(it)
        raw = json.dumps(data).encode() if isinstance(data, (dict, list)) else data
        return FakeResponse(raw)

    return _urlopen


class patch_urlopen:
    """Context manager that replaces urlopen in the exec namespace."""

    def __init__(self, mock_fn):
        self._mock = mock_fn
        self._original = None

    def __enter__(self):
        self._original = _mod["urlopen"]
        _mod["urlopen"] = self._mock
        return self._mock

    def __exit__(self, *args):
        _mod["urlopen"] = self._original


# ── _token tests ───────────────────────────────────────────────────────


def test_token_returns_env_var(monkeypatch):
    """_token returns the FLY_API_TOKEN value."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok_abc123")
    assert _token() == "tok_abc123"


def test_token_exits_without_env(monkeypatch):
    """_token calls sys.exit(1) when FLY_API_TOKEN is missing."""
    monkeypatch.delenv("FLY_API_TOKEN", raising=False)
    with pytest.raises(SystemExit) as exc_info:
        _token()
    assert exc_info.value.code == 1


# ── _api tests ─────────────────────────────────────────────────────────


def test_api_get_sends_correct_request(monkeypatch):
    """_api GET sends request with Bearer token and returns parsed JSON."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok_xyz")
    fake_data = {"id": "vol_123", "state": "attached"}

    with patch_urlopen(_make_urlopen([fake_data])):
        result = _api("GET", "/v1/apps/soma/volumes")

    assert result == fake_data


def test_api_post_sends_body(monkeypatch):
    """_api POST encodes body dict as JSON."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok_post")
    response = {"snapshot_id": "snap_abc"}
    calls = []

    def _urlopen(req, timeout=30):
        calls.append(req)
        return FakeResponse(json.dumps(response).encode())

    body = {"name": "test-snap"}

    with patch_urlopen(_urlopen):
        result = _api("POST", "/v1/apps/soma/volumes/vol_1/snapshots", body)

    assert result == response
    assert calls[0].method == "POST"
    assert calls[0].data == json.dumps(body).encode()


def test_soma_snapshot_api_empty_response(monkeypatch):
    """_api returns {} for empty response body."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok_empty")

    with patch_urlopen(lambda req, timeout=30: FakeResponse(b"")):
        result = _api("DELETE", "/v1/test")

    assert result == {}


# ── _get_machine tests ────────────────────────────────────────────────


def test_soma_snapshot_get_machine_returns_first(monkeypatch):
    """_get_machine returns the first machine from the API."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok_m")
    machines = [{"id": "m1", "state": "started"}, {"id": "m2", "state": "stopped"}]

    with patch_urlopen(_make_urlopen([machines])):
        m = _get_machine()

    assert m["id"] == "m1"


def test_get_machine_exits_on_empty(monkeypatch):
    """_get_machine exits when no machines found."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok_m")

    with patch_urlopen(_make_urlopen([[]])):
        with pytest.raises(SystemExit) as exc_info:
            _get_machine()
    assert exc_info.value.code == 1


# ── _get_volumes tests ────────────────────────────────────────────────


def test_get_volumes_returns_list(monkeypatch):
    """_get_volumes returns the volumes list."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok_v")
    vols = [{"id": "vol_1"}, {"id": "vol_2"}]

    with patch_urlopen(_make_urlopen([vols])):
        result = _get_volumes()

    assert result == vols


# ── cmd_volume tests ──────────────────────────────────────────────────


def test_cmd_volume_prints_info(monkeypatch, capsys):
    """cmd_volume prints volume details for each volume."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok_cv")
    vols = [
        {"id": "vol_abc", "size_gb": 10, "state": "attached", "region": "sjc", "name": "data"},
    ]

    with patch_urlopen(_make_urlopen([vols])):
        cmd_volume()

    out = capsys.readouterr().out
    assert "vol_abc" in out
    assert "10GB" in out
    assert "attached" in out
    assert "sjc" in out
    assert "data" in out


def test_cmd_volume_no_volumes(monkeypatch, capsys):
    """cmd_volume prints 'no volumes found' when list is empty."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok_cv2")

    with patch_urlopen(_make_urlopen([[]])):
        cmd_volume()

    out = capsys.readouterr().out
    assert "no volumes found" in out


# ── cmd_list tests ────────────────────────────────────────────────────


def test_cmd_list_with_snapshots(monkeypatch, capsys):
    """cmd_list prints snapshots for each volume."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok_cl")
    vols = [{"id": "vol_1"}]
    snaps = [
        {"id": "snap_a", "created_at": "2026-03-15T10:00:00Z", "size": 5368709120},
    ]

    with patch_urlopen(_make_urlopen([vols, snaps])):
        cmd_list()

    out = capsys.readouterr().out
    assert "snap_a" in out
    assert "2026-03-15T10:00:00Z" in out


def test_cmd_list_no_snapshots(monkeypatch, capsys):
    """cmd_list reports no snapshots for a volume with none."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok_cl2")
    vols = [{"id": "vol_2"}]

    with patch_urlopen(_make_urlopen([vols, []])):
        cmd_list()

    out = capsys.readouterr().out
    assert "no snapshots" in out


def test_cmd_list_no_volumes(monkeypatch, capsys):
    """cmd_list handles no volumes gracefully."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok_cl3")

    with patch_urlopen(_make_urlopen([[]])):
        cmd_list()

    out = capsys.readouterr().out
    assert "no volumes" in out


# ── cmd_snapshot tests ────────────────────────────────────────────────


def test_cmd_snapshot_running_machine(monkeypatch, capsys):
    """cmd_snapshot stops a running machine, snapshots, then restarts."""
    import time as time_mod
    from unittest.mock import patch as um_patch

    monkeypatch.setenv("FLY_API_TOKEN", "tok_snap")
    machines = [{"id": "m_1", "state": "started"}]
    vols = [{"id": "vol_data"}]
    stopped_machines = [{"id": "m_1", "state": "stopped"}]
    snap_result = {"id": "snap_new"}

    responses = [
        machines,  # _get_machine (initial) -> list
        vols,  # _get_volumes -> list
        {},  # stop API call
        stopped_machines,  # _get_machine (poll: stopped) -> list
        snap_result,  # snapshot creation
        {},  # start API call
    ]

    with (
        patch_urlopen(_make_urlopen(responses)),
        um_patch.object(time_mod, "sleep", lambda s: None),
    ):
        cmd_snapshot()

    out = capsys.readouterr().out
    assert "stopping machine m_1" in out
    assert "creating snapshot of volume vol_data" in out
    assert "snapshot created" in out
    assert "restarting machine m_1" in out
    assert "done" in out


def test_cmd_snapshot_stopped_machine(monkeypatch, capsys):
    """cmd_snapshot skips stop/start when machine is already stopped."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok_snap2")
    machines = [{"id": "m_2", "state": "stopped"}]
    vols = [{"id": "vol_off"}]
    snap_result = {"id": "snap_off"}

    responses = [
        machines,  # _get_machine
        vols,  # _get_volumes
        snap_result,  # snapshot creation
    ]

    with patch_urlopen(_make_urlopen(responses)):
        cmd_snapshot()

    out = capsys.readouterr().out
    assert "stopping" not in out
    assert "restarting" not in out
    assert "creating snapshot of volume vol_off" in out
    assert "done" in out


def test_cmd_snapshot_no_volumes(monkeypatch):
    """cmd_snapshot exits when there are no volumes."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok_snap3")
    machines = [{"id": "m_3", "state": "stopped"}]

    responses = [
        machines,  # _get_machine
        [],  # _get_volumes -> empty
    ]

    with patch_urlopen(_make_urlopen(responses)):
        with pytest.raises(SystemExit) as exc_info:
            cmd_snapshot()
    assert exc_info.value.code == 1


def test_cmd_snapshot_slow_stop_proceeds_anyway(monkeypatch, capsys):
    """cmd_snapshot proceeds after 30 polls even if machine doesn't reach 'stopped'."""
    import time as time_mod
    from unittest.mock import patch as um_patch

    monkeypatch.setenv("FLY_API_TOKEN", "tok_snap4")
    machines = [{"id": "m_4", "state": "started"}]
    vols = [{"id": "vol_slow"}]
    still_running = [{"id": "m_4", "state": "started"}]
    snap_result = {"id": "snap_slow"}

    responses = [
        machines,  # _get_machine (initial)
        vols,  # _get_volumes
        {},  # stop call
    ]
    responses.extend([still_running] * 30)  # 30 polls, never stops
    responses.append(snap_result)  # snapshot creation
    responses.append({})  # start call

    with (
        patch_urlopen(_make_urlopen(responses)),
        um_patch.object(time_mod, "sleep", lambda s: None),
    ):
        cmd_snapshot()

    out = capsys.readouterr().out
    assert "warning" in out.lower()
    assert "done" in out


# ── main dispatch tests ───────────────────────────────────────────────


def test_soma_snapshot_main_help():
    """main with --help prints docstring and exits."""
    with pytest.raises(SystemExit) as exc_info:
        with patch_urlopen(lambda *a, **kw: FakeResponse()):
            _mod["sys"].argv = ["soma-snapshot", "--help"]
            try:
                main()
            finally:
                pass
    assert exc_info.value.code == 0


def test_main_dispatches_list(monkeypatch, capsys):
    """main dispatches to cmd_list when --list is passed."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok_disp")
    vols = [{"id": "vol_x"}]
    original_argv = _mod["sys"].argv

    _mod["sys"].argv = ["soma-snapshot", "--list"]
    try:
        with patch_urlopen(_make_urlopen([vols, []])):
            main()
    finally:
        _mod["sys"].argv = original_argv

    out = capsys.readouterr().out
    assert "vol_x" in out


def test_main_dispatches_volume(monkeypatch, capsys):
    """main dispatches to cmd_volume when --volume is passed."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok_disp2")
    vols = [{"id": "vol_y", "size_gb": 5, "state": "attached", "region": "ewr", "name": "pv"}]
    original_argv = _mod["sys"].argv

    _mod["sys"].argv = ["soma-snapshot", "--volume"]
    try:
        with patch_urlopen(_make_urlopen([vols])):
            main()
    finally:
        _mod["sys"].argv = original_argv

    out = capsys.readouterr().out
    assert "vol_y" in out


def test_main_dispatches_snapshot_by_default(monkeypatch, capsys):
    """main dispatches to cmd_snapshot when no flags are given."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok_disp3")
    machines = [{"id": "m_d", "state": "stopped"}]
    vols = [{"id": "vol_d"}]
    snap = {"id": "snap_d"}
    original_argv = _mod["sys"].argv

    _mod["sys"].argv = ["soma-snapshot"]
    try:
        with patch_urlopen(_make_urlopen([machines, vols, snap])):
            main()
    finally:
        _mod["sys"].argv = original_argv

    out = capsys.readouterr().out
    assert "done" in out


def test_main_dispatches_bare_list_subcommand(monkeypatch, capsys):
    """main dispatches to cmd_list when 'list' (no dashes) is passed."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok_disp4")
    vols = [{"id": "vol_z"}]
    original_argv = _mod["sys"].argv

    _mod["sys"].argv = ["soma-snapshot", "list"]
    try:
        with patch_urlopen(_make_urlopen([vols, []])):
            main()
    finally:
        _mod["sys"].argv = original_argv

    out = capsys.readouterr().out
    assert "vol_z" in out


def test_main_dispatches_bare_volume_subcommand(monkeypatch, capsys):
    """main dispatches to cmd_volume when 'volume' (no dashes) is passed."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok_disp5")
    vols = [{"id": "vol_bv", "size_gb": 1, "state": "ok", "region": "lax", "name": "bk"}]
    original_argv = _mod["sys"].argv

    _mod["sys"].argv = ["soma-snapshot", "volume"]
    try:
        with patch_urlopen(_make_urlopen([vols])):
            main()
    finally:
        _mod["sys"].argv = original_argv

    out = capsys.readouterr().out
    assert "vol_bv" in out


# ── constants tests ───────────────────────────────────────────────────


def test_soma_snapshot_constants():
    """API_BASE and APP_NAME have expected values."""
    assert API_BASE == "https://api.machines.dev"
    assert APP_NAME == "soma"


# ── _api handles list response ────────────────────────────────────────


def test_api_returns_list(monkeypatch):
    """_api correctly returns a list from JSON response."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok_list")
    data = [{"id": "a"}, {"id": "b"}]

    with patch_urlopen(_make_urlopen([data])):
        result = _api("GET", "/v1/test")

    assert isinstance(result, list)
    assert len(result) == 2


# ── cmd_snapshot with multiple volumes ────────────────────────────────


def test_cmd_snapshot_uses_first_volume(monkeypatch, capsys):
    """cmd_snapshot snapshots the first volume when multiple exist."""
    monkeypatch.setenv("FLY_API_TOKEN", "tok_mv")
    machines = [{"id": "m_mv", "state": "stopped"}]
    vols = [{"id": "vol_first"}, {"id": "vol_second"}]
    snap = {"id": "snap_mv"}

    responses = [machines, vols, snap]

    with patch_urlopen(_make_urlopen(responses)):
        cmd_snapshot()

    out = capsys.readouterr().out
    assert "creating snapshot of volume vol_first" in out
    assert "vol_second" not in out
