from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

EFFECTOR = Path(__file__).resolve().parent.parent / "effectors" / "proteostasis"


def _load_ns(argv=None):
    """Load proteostasis effector into a fresh namespace."""
    if argv is None:
        argv = ["proteostasis"]
    ns: dict = {"__name__": "proteostasis_test", "__file__": str(EFFECTOR)}
    with patch.object(sys, "argv", argv):
        exec(EFFECTOR.read_text(), ns)
    return ns


@pytest.fixture
def ns():
    return _load_ns()


@pytest.fixture
def dry_ns():
    return _load_ns(["proteostasis", "--dry-run"])


@pytest.fixture
def force_ns():
    return _load_ns(["proteostasis", "--force"])


# ── _ver_tuple ──────────────────────────────────────────────────────────────


class TestVerTuple:
    def test_simple(self, ns):
        assert ns["_ver_tuple"]("1.2.3") == (1, 2, 3)

    def test_single(self, ns):
        assert ns["_ver_tuple"]("5") == (5,)

    def test_strips_nonnumeric_suffix(self, ns):
        assert ns["_ver_tuple"]("1.2.3a1") == (1, 2, 3)

    def test_empty(self, ns):
        assert ns["_ver_tuple"]("") == ()


# ── load_state ──────────────────────────────────────────────────────────────


class TestLoadState:
    def test_valid(self, ns, tmp_path):
        f = tmp_path / "state.json"
        f.write_text('{"last_run": "2025-01-01", "blocked": {}}')
        ns["STATE_PATH"] = f
        assert ns["load_state"]()["last_run"] == "2025-01-01"

    def test_missing_file(self, ns, tmp_path):
        ns["STATE_PATH"] = tmp_path / "nope" / "state.json"
        r = ns["load_state"]()
        assert r == {"last_run": None, "blocked": {}}

    def test_invalid_json(self, ns, tmp_path):
        f = tmp_path / "state.json"
        f.write_text("bad")
        ns["STATE_PATH"] = f
        assert ns["load_state"]() == {"last_run": None, "blocked": {}}

    def test_adds_missing_blocked_key(self, ns, tmp_path):
        f = tmp_path / "state.json"
        f.write_text('{"last_run": "x"}')
        ns["STATE_PATH"] = f
        assert ns["load_state"]()["blocked"] == {}


# ── save_state ──────────────────────────────────────────────────────────────


class TestSaveState:
    def test_writes_json(self, ns, tmp_path):
        f = tmp_path / "state.json"
        ns["STATE_PATH"] = f
        ns["save_state"]({"last_run": "2025-06-01", "blocked": {}})
        assert json.loads(f.read_text())["last_run"] == "2025-06-01"

    def test_creates_parent_dirs(self, ns, tmp_path):
        f = tmp_path / "a" / "b" / "state.json"
        ns["STATE_PATH"] = f
        ns["save_state"]({"last_run": None, "blocked": {}})
        assert f.exists()

    def test_dry_run_skips_write(self, dry_ns, tmp_path):
        f = tmp_path / "state.json"
        dry_ns["STATE_PATH"] = f
        dry_ns["save_state"]({"last_run": "x", "blocked": {}})
        assert not f.exists()


# ── should_run ──────────────────────────────────────────────────────────────


class TestShouldRun:
    def test_no_last_run(self, ns):
        assert ns["should_run"]({}) is True

    def test_recent_run_blocked(self, ns):
        HKT = ns["HKT"]
        recent = datetime.now(HKT).isoformat()
        assert ns["should_run"]({"last_run": recent}) is False

    def test_old_run_allowed(self, ns):
        HKT = ns["HKT"]
        old = (datetime.now(HKT) - timedelta(hours=25)).isoformat()
        assert ns["should_run"]({"last_run": old}) is True

    def test_force_overrides(self, force_ns):
        HKT = force_ns["HKT"]
        recent = datetime.now(HKT).isoformat()
        assert force_ns["should_run"]({"last_run": recent}) is True

    def test_invalid_timestamp(self, ns):
        assert ns["should_run"]({"last_run": "garbage"}) is True


# ── emit_signal ─────────────────────────────────────────────────────────────


class TestEmitSignal:
    def test_writes_blocked(self, ns, tmp_path):
        f = tmp_path / "sig.json"
        ns["SIGNAL_PATH"] = f
        ns["emit_signal"]({"x": {"version": "2.0", "since": "2025"}})
        d = json.loads(f.read_text())
        assert "x" in d["blocked"] and "updated" in d

    def test_clears_signal_when_empty(self, ns, tmp_path):
        f = tmp_path / "sig.json"
        f.write_text("{}")
        ns["SIGNAL_PATH"] = f
        ns["emit_signal"]({})
        assert not f.exists()

    def test_no_file_no_error(self, ns, tmp_path):
        ns["SIGNAL_PATH"] = tmp_path / "nope.json"
        ns["emit_signal"]({})  # should not raise

    def test_dry_run_skips(self, dry_ns, tmp_path):
        f = tmp_path / "sig.json"
        dry_ns["SIGNAL_PATH"] = f
        dry_ns["emit_signal"]({"x": {"v": "1"}})
        assert not f.exists()


# ── run (subprocess wrapper) ───────────────────────────────────────────────


class TestRun:
    def test_success_returns_stdout(self, ns):
        m = MagicMock(returncode=0, stdout="  ok  \n", stderr="")
        with patch.object(ns["subprocess"], "run", return_value=m):
            ok, out = ns["run"](["echo"])
            assert ok is True and out == "ok"

    def test_failure_returns_stderr(self, ns):
        m = MagicMock(returncode=1, stdout="", stderr=" err ")
        with patch.object(ns["subprocess"], "run", return_value=m):
            ok, out = ns["run"](["x"])
            assert ok is False and out == "err"

    def test_timeout(self, ns):
        exc = ns["subprocess"].TimeoutExpired("c", 15)
        with patch.object(ns["subprocess"], "run", side_effect=exc):
            ok, out = ns["run"](["slow"])
            assert ok is False and "timed out" in out

    def test_not_found(self, ns):
        with patch.object(ns["subprocess"], "run", side_effect=FileNotFoundError):
            ok, out = ns["run"](["missing"])
            assert ok is False and "not found" in out

    def test_generic_exception(self, ns):
        with patch.object(ns["subprocess"], "run", side_effect=PermissionError("nope")):
            ok, out = ns["run"](["x"])
            assert ok is False and "nope" in out


# ── smoke_test ──────────────────────────────────────────────────────────────


class TestSmokeTest:
    def test_pass(self, ns):
        m = MagicMock(returncode=0, stdout="", stderr="")
        with patch.object(ns["subprocess"], "run", return_value=m):
            assert ns["smoke_test"]() == (True, "")

    def test_fail(self, ns):
        m = MagicMock(returncode=1, stdout="", stderr="ImportError: x")
        with patch.object(ns["subprocess"], "run", return_value=m):
            ok, d = ns["smoke_test"]()
            assert ok is False and "ImportError" in d


# ── diagnose ────────────────────────────────────────────────────────────────


class TestDiagnose:
    def test_clean(self, ns):
        ns["run"] = MagicMock(return_value=(True, ""))
        assert ns["diagnose"]() == {}

    def test_parses_conflict_line(self, ns):
        out = "foo 1.0 has requirement bar>=2.0, but you have bar 1.5"
        ns["run"] = MagicMock(return_value=(False, out))
        r = ns["diagnose"]()
        assert "bar" in r
        assert r["bar"]["required_by"] == "foo"
        assert r["bar"]["installed"] == "1.5"

    def test_unparseable_line(self, ns):
        ns["run"] = MagicMock(return_value=(False, "gibberish"))
        assert ns["diagnose"]() == {}


# ── attempt_fix ─────────────────────────────────────────────────────────────


class TestAttemptFix:
    def test_no_conflicts(self, ns):
        ok, msg = ns["attempt_fix"]({})
        assert ok is False and "no conflicts" in msg

    def test_fix_succeeds(self, ns):
        ns["run"] = MagicMock(return_value=(True, ""))
        ns["smoke_test"] = MagicMock(return_value=(True, ""))
        conflicts = {"x": {"required_by": "a", "constraint": "x>=1", "installed": "0.5"}}
        ok, msg = ns["attempt_fix"](conflicts)
        assert ok is True and msg == "fixed"

    def test_install_fails(self, ns):
        ns["run"] = MagicMock(return_value=(False, "pip error"))
        conflicts = {"x": {"required_by": "a", "constraint": "x>=1", "installed": "0.5"}}
        ok, msg = ns["attempt_fix"](conflicts)
        assert ok is False and "fix failed" in msg

    def test_smoke_fails_after_install(self, ns):
        ns["run"] = MagicMock(return_value=(True, ""))
        ns["smoke_test"] = MagicMock(return_value=(False, "boom"))
        conflicts = {"x": {"required_by": "a", "constraint": "x>=1", "installed": "0.5"}}
        ok, msg = ns["attempt_fix"](conflicts)
        assert ok is False and "boom" in msg


# ── check_claude_code ───────────────────────────────────────────────────────


class TestCheckClaudeCode:
    def _setup_claude_link(self, tmp_path, version):
        bindir = tmp_path / ".local" / "bin"
        bindir.mkdir(parents=True)
        (bindir / "claude").symlink_to(f"/fake/{version}")

    def test_breaking_update_alerts(self, ns, tmp_path):
        self._setup_claude_link(tmp_path, "1.0.0")
        gh_out = json.dumps({"tagName": "v2.0.0", "body": "BREAKING: removed API"})
        ns["run"] = MagicMock(return_value=(True, gh_out))
        with patch.object(Path, "home", return_value=tmp_path):
            alerts = ns["check_claude_code"]({})
        assert len(alerts) == 1
        assert "CC BREAKING" in alerts[0] and "1.0.0" in alerts[0] and "2.0.0" in alerts[0]

    def test_no_breaking_keywords(self, ns, tmp_path):
        self._setup_claude_link(tmp_path, "1.0.0")
        gh_out = json.dumps({"tagName": "v2.0.0", "body": "minor bugfix"})
        ns["run"] = MagicMock(return_value=(True, gh_out))
        with patch.object(Path, "home", return_value=tmp_path):
            assert ns["check_claude_code"]({}) == []

    def test_same_version_no_alert(self, ns, tmp_path):
        self._setup_claude_link(tmp_path, "2.0.0")
        gh_out = json.dumps({"tagName": "v2.0.0", "body": "BREAKING change"})
        ns["run"] = MagicMock(return_value=(True, gh_out))
        with patch.object(Path, "home", return_value=tmp_path):
            assert ns["check_claude_code"]({}) == []

    def test_no_claude_link(self, ns, tmp_path):
        ns["run"] = MagicMock(return_value=(True, "{}"))
        with patch.object(Path, "home", return_value=tmp_path):
            assert ns["check_claude_code"]({}) == []

    def test_gh_fails(self, ns, tmp_path):
        self._setup_claude_link(tmp_path, "1.0.0")
        ns["run"] = MagicMock(return_value=(False, "network error"))
        with patch.object(Path, "home", return_value=tmp_path):
            assert ns["check_claude_code"]({}) == []


# ── _uv_outdated / _uv_snapshot ─────────────────────────────────────────────


class TestUvOutdated:
    def test_returns_packages(self, ns):
        pkgs = [{"name": "foo", "version": "1.0", "latest_version": "2.0"}]
        ns["run"] = MagicMock(return_value=(True, json.dumps(pkgs)))
        assert "foo" in ns["_uv_outdated"]()

    def test_empty(self, ns):
        ns["run"] = MagicMock(return_value=(True, "[]"))
        assert ns["_uv_outdated"]() == {}

    def test_bad_json(self, ns):
        ns["run"] = MagicMock(return_value=(True, "not json"))
        assert ns["_uv_outdated"]() == {}

    def test_failed_run(self, ns):
        ns["run"] = MagicMock(return_value=(False, ""))
        assert ns["_uv_outdated"]() == {}


class TestUvSnapshot:
    def test_returns_version_map(self, ns):
        pkgs = [{"name": "foo", "version": "1.0"}, {"name": "bar", "version": "3.0"}]
        ns["run"] = MagicMock(return_value=(True, json.dumps(pkgs)))
        assert ns["_uv_snapshot"]() == {"foo": "1.0", "bar": "3.0"}

    def test_failed_run(self, ns):
        ns["run"] = MagicMock(return_value=(False, ""))
        assert ns["_uv_snapshot"]() == {}


# ── _bisect_upgrades ────────────────────────────────────────────────────────


class TestBisectUpgrades:
    def test_all_pass(self, ns):
        ns["_uv_install"] = MagicMock(return_value=(True, ""))
        ns["smoke_test"] = MagicMock(return_value=(True, ""))
        blocked: dict = {}
        alerts: list[str] = []
        ns["_bisect_upgrades"]({"foo": ("1.0", "2.0")}, blocked, alerts)
        assert any("pip upgraded" in a for a in alerts)
        assert len(blocked) == 0

    def test_marks_blocked_on_fail(self, ns):
        ns["_uv_install"] = MagicMock(return_value=(True, ""))
        ns["smoke_test"] = MagicMock(return_value=(False, "ImportError"))
        ns["diagnose"] = MagicMock(return_value={})
        blocked: dict = {}
        alerts: list[str] = []
        ns["_bisect_upgrades"]({"foo": ("1.0", "2.0")}, blocked, alerts)
        assert "foo" in blocked
        assert any("pip blocked" in a for a in alerts)

    def test_blocked_with_conflict_detail(self, ns):
        ns["_uv_install"] = MagicMock(return_value=(True, ""))
        ns["smoke_test"] = MagicMock(return_value=(False, "boom"))
        ns["diagnose"] = MagicMock(return_value={
            "bar": {"required_by": "baz", "constraint": "bar>=2", "installed": "1.0"},
        })
        blocked: dict = {}
        alerts: list[str] = []
        ns["_bisect_upgrades"]({"foo": ("1.0", "2.0")}, blocked, alerts)
        assert "foo" in blocked
        assert blocked["foo"]["conflicts"] == {"bar": "bar>=2"}


# ── auto_update_npm ────────────────────────────────────────────────────────


class TestAutoUpdateNpm:
    def test_no_outdated(self, ns):
        ns["run"] = MagicMock(return_value=(False, ""))
        assert ns["auto_update_npm"]({}) == []

    def test_upgrades_package(self, ns):
        npm_out = json.dumps({"eslint": {"current": "8.0", "latest": "9.0"}})
        ns["run"] = MagicMock(side_effect=[
            (True, npm_out),    # npm outdated
            (True, "installed"),  # npm install
        ])
        alerts = ns["auto_update_npm"]({})
        assert len(alerts) == 1 and "npm upgraded" in alerts[0]

    def test_upgrade_fails_reverts(self, ns):
        npm_out = json.dumps({"eslint": {"current": "8.0", "latest": "9.0"}})
        ns["run"] = MagicMock(side_effect=[
            (True, npm_out),    # npm outdated
            (False, "err"),     # install fails
            (True, "reverted"),  # revert
        ])
        alerts = ns["auto_update_npm"]({})
        assert len(alerts) == 1 and "npm failed" in alerts[0]

    def test_dry_run_shows_would_upgrade(self, dry_ns):
        npm_out = json.dumps({"eslint": {"current": "8.0", "latest": "9.0"}})
        dry_ns["run"] = MagicMock(return_value=(True, npm_out))
        alerts = dry_ns["auto_update_npm"]({})
        assert any("would upgrade" in a for a in alerts)

    def test_bad_json_returns_empty(self, ns):
        ns["run"] = MagicMock(return_value=(True, "bad"))
        assert ns["auto_update_npm"]({}) == []


# ── auto_update_python ──────────────────────────────────────────────────────


class TestAutoUpdatePython:
    def test_nothing_outdated(self, ns):
        ns["_uv_outdated"] = MagicMock(return_value={})
        ns["emit_signal"] = MagicMock()
        assert ns["auto_update_python"]({"blocked": {}}) == []

    def test_dry_run_reports(self, dry_ns):
        dry_ns["_uv_outdated"] = MagicMock(return_value={
            "bar": {"name": "bar", "version": "1.0", "latest_version": "2.0"},
        })
        dry_ns["emit_signal"] = MagicMock()
        alerts = dry_ns["auto_update_python"]({"blocked": {}})
        assert any("would upgrade" in a for a in alerts)
        assert any("git-pinned" in a for a in alerts)

    def test_upgrade_smoke_pass(self, ns):
        ns["_uv_outdated"] = MagicMock(return_value={
            "bar": {"name": "bar", "version": "1.0", "latest_version": "2.0"},
        })
        ns["_uv_snapshot"] = MagicMock(side_effect=[
            {"bar": "1.0"}, {"bar": "2.0"},
        ])
        ns["_uv_install"] = MagicMock(return_value=(True, ""))
        ns["smoke_test"] = MagicMock(return_value=(True, ""))
        ns["emit_signal"] = MagicMock()
        ns["run"] = MagicMock(return_value=(False, ""))  # git-pinned skip
        state = {"blocked": {}}
        alerts = ns["auto_update_python"](state)
        assert any("pip upgraded: bar" in a for a in alerts)

    def test_upgrade_smoke_fail_then_bisect(self, ns):
        ns["_uv_outdated"] = MagicMock(return_value={
            "bar": {"name": "bar", "version": "1.0", "latest_version": "2.0"},
        })
        ns["_uv_snapshot"] = MagicMock(side_effect=[
            {"bar": "1.0"}, {"bar": "2.0"},
        ])
        ns["_uv_install"] = MagicMock(return_value=(True, ""))
        ns["smoke_test"] = MagicMock(side_effect=[
            (False, "ImportError"),  # initial smoke after bulk upgrade
            (False, "ImportError"),  # bisect smoke
        ])
        ns["diagnose"] = MagicMock(return_value={})
        ns["emit_signal"] = MagicMock()
        ns["run"] = MagicMock(return_value=(False, ""))  # git-pinned skip
        state = {"blocked": {}}
        alerts = ns["auto_update_python"](state)
        assert any("pip blocked" in a for a in alerts)
        assert "bar" in state["blocked"]

    def test_blocked_same_version_skipped(self, ns):
        ns["_uv_outdated"] = MagicMock(return_value={
            "bar": {"name": "bar", "version": "1.0", "latest_version": "2.0"},
        })
        ns["emit_signal"] = MagicMock()
        ns["run"] = MagicMock(return_value=(False, ""))
        state = {"blocked": {"bar": {"version": "2.0", "since": "2025"}}}
        alerts = ns["auto_update_python"](state)
        assert not any("bar" in a for a in alerts)

    def test_blocked_newer_version_unblocks(self, ns):
        ns["_uv_outdated"] = MagicMock(return_value={
            "bar": {"name": "bar", "version": "1.0", "latest_version": "3.0"},
        })
        ns["_uv_snapshot"] = MagicMock(side_effect=[
            {"bar": "1.0"}, {"bar": "3.0"},
        ])
        ns["_uv_install"] = MagicMock(return_value=(True, ""))
        ns["smoke_test"] = MagicMock(return_value=(True, ""))
        ns["emit_signal"] = MagicMock()
        ns["run"] = MagicMock(return_value=(False, ""))
        state = {"blocked": {"bar": {"version": "2.0", "since": "2025"}}}
        alerts = ns["auto_update_python"](state)
        assert any("pip upgraded" in a for a in alerts)
        assert "bar" not in state["blocked"]

    def test_git_pinned_unpins_when_available(self, ns):
        ns["_uv_outdated"] = MagicMock(return_value={})
        ns["emit_signal"] = MagicMock()
        # run is called for pip index versions
        ns["run"] = MagicMock(return_value=(True, "fastmcp (3.2.0)\nother"))
        ns["_uv_install"] = MagicMock(return_value=(True, ""))
        alerts = ns["auto_update_python"]({"blocked": {}})
        assert any("unpinned" in a and "fastmcp" in a for a in alerts)

    def test_bulk_upgrade_fails(self, ns):
        ns["_uv_outdated"] = MagicMock(return_value={
            "bar": {"name": "bar", "version": "1.0", "latest_version": "2.0"},
        })
        ns["_uv_install"] = MagicMock(return_value=(False, "network error"))
        ns["emit_signal"] = MagicMock()
        ns["run"] = MagicMock(return_value=(False, ""))
        state = {"blocked": {}}
        alerts = ns["auto_update_python"](state)
        assert any("pip upgrade failed" in a for a in alerts)


# ── main ────────────────────────────────────────────────────────────────────


class TestMain:
    def test_skips_when_too_recent(self, ns, capsys):
        ns["load_state"] = MagicMock(return_value={"last_run": "x", "blocked": {}})
        ns["should_run"] = MagicMock(return_value=False)
        ns["main"]()
        assert capsys.readouterr().out == ""

    def test_runs_and_prints_alerts(self, ns, capsys):
        ns["load_state"] = MagicMock(return_value={"last_run": None, "blocked": {}})
        ns["should_run"] = MagicMock(return_value=True)
        ns["check_claude_code"] = MagicMock(return_value=[])
        ns["auto_update_python"] = MagicMock(return_value=["pip upgraded: foo 1→2"])
        ns["auto_update_npm"] = MagicMock(return_value=["npm upgraded: bar 3→4"])
        ns["save_state"] = MagicMock()
        ns["main"]()
        out = capsys.readouterr().out
        assert "pip upgraded" in out
        assert "npm upgraded" in out

    def test_saves_state_after_run(self, ns):
        ns["load_state"] = MagicMock(return_value={"last_run": None, "blocked": {}})
        ns["should_run"] = MagicMock(return_value=True)
        ns["check_claude_code"] = MagicMock(return_value=[])
        ns["auto_update_python"] = MagicMock(return_value=[])
        ns["auto_update_npm"] = MagicMock(return_value=[])
        ns["save_state"] = MagicMock()
        ns["main"]()
        ns["save_state"].assert_called_once()
        saved_state = ns["save_state"].call_args[0][0]
        assert saved_state["last_run"] is not None

    def test_no_alerts_no_output(self, ns, capsys):
        ns["load_state"] = MagicMock(return_value={"last_run": None, "blocked": {}})
        ns["should_run"] = MagicMock(return_value=True)
        ns["check_claude_code"] = MagicMock(return_value=[])
        ns["auto_update_python"] = MagicMock(return_value=[])
        ns["auto_update_npm"] = MagicMock(return_value=[])
        ns["save_state"] = MagicMock()
        ns["main"]()
        assert capsys.readouterr().out == ""
