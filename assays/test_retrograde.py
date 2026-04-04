from __future__ import annotations

"""Tests for retrograde — symbiont influence tracker."""

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import metabolon.organelles.retrograde as retro

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _recent_ts(days_ago: float = 0) -> str:
    return (datetime.now(UTC) - timedelta(days=days_ago)).isoformat()


def _make_jsonl(path, entries):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(e) for e in entries) + "\n")


# ---------------------------------------------------------------------------
# log_signal
# ---------------------------------------------------------------------------


class TestLogSignal:
    def test_appends_to_file(self, tmp_path):
        log_file = tmp_path / "signals.jsonl"
        with patch.object(retro, "SIGNALS_LOG", log_file):
            retro.log_signal("anterograde", "channel_call", "test detail")
        assert log_file.exists()
        entry = json.loads(log_file.read_text().strip())
        assert entry["direction"] == "anterograde"
        assert entry["type"] == "channel_call"
        assert entry["detail"] == "test detail"

    def test_creates_parent_dirs(self, tmp_path):
        log_file = tmp_path / "sub" / "dir" / "signals.jsonl"
        with patch.object(retro, "SIGNALS_LOG", log_file):
            retro.log_signal("retrograde", "git_commit")
        assert log_file.exists()

    def test_appends_multiple_entries(self, tmp_path):
        log_file = tmp_path / "signals.jsonl"
        with patch.object(retro, "SIGNALS_LOG", log_file):
            retro.log_signal("anterograde", "pulse")
            retro.log_signal("retrograde", "commit")
        lines = log_file.read_text().strip().splitlines()
        assert len(lines) == 2
        assert json.loads(lines[0])["direction"] == "anterograde"
        assert json.loads(lines[1])["direction"] == "retrograde"

    def test_detail_defaults_empty(self, tmp_path):
        log_file = tmp_path / "signals.jsonl"
        with patch.object(retro, "SIGNALS_LOG", log_file):
            retro.log_signal("anterograde", "test_type")
        entry = json.loads(log_file.read_text().strip())
        assert entry["detail"] == ""

    def test_timestamp_is_valid_iso(self, tmp_path):
        log_file = tmp_path / "signals.jsonl"
        with patch.object(retro, "SIGNALS_LOG", log_file):
            retro.log_signal("retrograde", "mem_write")
        entry = json.loads(log_file.read_text().strip())
        datetime.fromisoformat(entry["ts"])


# ---------------------------------------------------------------------------
# _cutoff_iso
# ---------------------------------------------------------------------------


class TestCutoffIso:
    def test_returns_iso_string(self):
        result = retro._cutoff_iso(7)
        assert "T" in result
        datetime.fromisoformat(result)

    def test_shorter_period_is_more_recent(self):
        r7 = retro._cutoff_iso(7)
        r1 = retro._cutoff_iso(1)
        assert r1 > r7

    def test_zero_days(self):
        result = retro._cutoff_iso(0)
        assert "T" in result
        datetime.fromisoformat(result)


# ---------------------------------------------------------------------------
# _count_logged
# ---------------------------------------------------------------------------


class TestCountLogged:
    def test_empty_log(self, tmp_path):
        with patch.object(retro, "SIGNALS_LOG", tmp_path / "nope.jsonl"):
            assert retro._count_logged(7, "anterograde") == 0

    def test_counts_matching_direction(self, tmp_path):
        log = tmp_path / "signals.jsonl"
        now = _recent_ts(0)
        entries = [
            {"ts": now, "direction": "anterograde", "type": "test"},
            {"ts": now, "direction": "retrograde", "type": "test"},
            {"ts": now, "direction": "anterograde", "type": "test"},
        ]
        _make_jsonl(log, entries)
        with patch.object(retro, "SIGNALS_LOG", log):
            assert retro._count_logged(7, "anterograde") == 2

    def test_excludes_old_entries(self, tmp_path):
        log = tmp_path / "signals.jsonl"
        old = _recent_ts(30)
        now = _recent_ts(0)
        entries = [
            {"ts": old, "direction": "anterograde", "type": "old"},
            {"ts": now, "direction": "anterograde", "type": "recent"},
        ]
        _make_jsonl(log, entries)
        with patch.object(retro, "SIGNALS_LOG", log):
            assert retro._count_logged(7, "anterograde") == 1

    def test_malformed_line_skipped(self, tmp_path):
        log = tmp_path / "signals.jsonl"
        now = _recent_ts(0)
        log.write_text(
            json.dumps({"ts": now, "direction": "anterograde", "type": "ok"}) + "\nBROKEN LINE\n"
        )
        with patch.object(retro, "SIGNALS_LOG", log):
            assert retro._count_logged(7, "anterograde") == 1

    def test_missing_ts_skipped(self, tmp_path):
        log = tmp_path / "signals.jsonl"
        log.write_text(json.dumps({"direction": "anterograde"}) + "\n")
        with patch.object(retro, "SIGNALS_LOG", log):
            assert retro._count_logged(7, "anterograde") == 0


# ---------------------------------------------------------------------------
# _count_anterograde
# ---------------------------------------------------------------------------


class TestCountAnterograde:
    def test_empty_event_log(self, tmp_path):
        evt = tmp_path / "events.jsonl"
        with (
            patch.object(retro, "EVENT_LOG", evt),
            patch.object(retro, "SIGNALS_LOG", tmp_path / "sig.jsonl"),
        ):
            assert retro._count_anterograde(7) == 0

    def test_counts_systole_events(self, tmp_path):
        now = _recent_ts(0)
        entries = [
            {"ts": now, "event": "systole_start"},
            {"ts": now, "event": "run_start"},
            {"ts": now, "event": "adapt_start"},
            {"ts": now, "event": "other_event"},
            {"ts": now, "cmd": "channel"},
        ]
        evt = tmp_path / "events.jsonl"
        _make_jsonl(evt, entries)
        with (
            patch.object(retro, "EVENT_LOG", evt),
            patch.object(retro, "SIGNALS_LOG", tmp_path / "sig.jsonl"),
        ):
            # systole_start + run_start + adapt_start + channel = 4
            assert retro._count_anterograde(7) == 4

    def test_excludes_old_events(self, tmp_path):
        old = _recent_ts(30)
        now = _recent_ts(0)
        entries = [
            {"ts": old, "event": "systole_start"},
            {"ts": now, "event": "systole_start"},
        ]
        evt = tmp_path / "events.jsonl"
        _make_jsonl(evt, entries)
        with (
            patch.object(retro, "EVENT_LOG", evt),
            patch.object(retro, "SIGNALS_LOG", tmp_path / "sig.jsonl"),
        ):
            assert retro._count_anterograde(7) == 1

    def test_malformed_event_line_skipped(self, tmp_path):
        now = _recent_ts(0)
        evt = tmp_path / "events.jsonl"
        evt.write_text(json.dumps({"ts": now, "event": "systole_start"}) + "\nNOTJSON\n")
        with (
            patch.object(retro, "EVENT_LOG", evt),
            patch.object(retro, "SIGNALS_LOG", tmp_path / "sig.jsonl"),
        ):
            assert retro._count_anterograde(7) == 1

    def test_includes_logged_signals(self, tmp_path):
        now = _recent_ts(0)
        sig = tmp_path / "signals.jsonl"
        _make_jsonl(sig, [{"ts": now, "direction": "anterograde", "type": "manual"}])
        with (
            patch.object(retro, "EVENT_LOG", tmp_path / "nope.jsonl"),
            patch.object(retro, "SIGNALS_LOG", sig),
        ):
            assert retro._count_anterograde(7) == 1

    def test_naive_ts_gets_utc(self, tmp_path):
        """Timestamps without timezone info are treated as UTC."""
        now_naive = datetime.now(UTC).replace(tzinfo=None).isoformat()
        evt = tmp_path / "events.jsonl"
        _make_jsonl(evt, [{"ts": now_naive, "event": "systole_start"}])
        with (
            patch.object(retro, "EVENT_LOG", evt),
            patch.object(retro, "SIGNALS_LOG", tmp_path / "sig.jsonl"),
        ):
            assert retro._count_anterograde(7) == 1


# ---------------------------------------------------------------------------
# _count_retrograde
# ---------------------------------------------------------------------------


class TestCountRetrograde:
    def _patch_env(self, tmp_path, repos=None):
        """Return a context manager patching all paths + TRACKED_REPOS."""
        sig = tmp_path / "signals.jsonl"
        meth_cand = tmp_path / "meth_cand.jsonl"
        meth_jsonl = tmp_path / "meth.jsonl"
        infect = tmp_path / "infections.jsonl"
        patches = [
            patch.object(retro, "SIGNALS_LOG", sig),
            patch.object(retro, "METHYLATION_CANDIDATES", meth_cand),
            patch.object(retro, "METHYLATION_JSONL", meth_jsonl),
            patch.object(retro, "INFECTIONS_LOG", infect),
            patch.object(retro, "TRACKED_REPOS", repos or []),
        ]
        return patches

    def _enter_patches(self, patches):
        """Enter all patches and return them for cleanup."""
        entered = []
        for p in patches:
            entered.append(p.start())
        return entered

    def test_no_repos_no_logs(self, tmp_path):
        patches = self._patch_env(tmp_path)
        try:
            for p in patches:
                p.start()
            assert retro._count_retrograde(7) == 0
        finally:
            for p in patches:
                p.stop()

    def test_git_commits_counted(self, tmp_path):
        repo_dir = tmp_path / "myrepo"
        repo_dir.mkdir()
        (repo_dir / ".git").mkdir()

        mock_result = MagicMock()
        mock_result.stdout = "abc123 fix something\ndef456 add feature\n"
        mock_result.stderr = ""

        patches = self._patch_env(tmp_path, repos=[repo_dir])
        try:
            for p in patches:
                p.start()
            with patch("metabolon.organelles.retrograde.subprocess.run", return_value=mock_result):
                count = retro._count_retrograde(7)
            assert count == 2
        finally:
            for p in patches:
                p.stop()

    def test_git_empty_output(self, tmp_path):
        repo_dir = tmp_path / "myrepo"
        repo_dir.mkdir()
        (repo_dir / ".git").mkdir()

        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""

        patches = self._patch_env(tmp_path, repos=[repo_dir])
        try:
            for p in patches:
                p.start()
            with patch("metabolon.organelles.retrograde.subprocess.run", return_value=mock_result):
                assert retro._count_retrograde(7) == 0
        finally:
            for p in patches:
                p.stop()

    def test_git_failure_ignored(self, tmp_path):
        repo_dir = tmp_path / "myrepo"
        repo_dir.mkdir()
        (repo_dir / ".git").mkdir()

        patches = self._patch_env(tmp_path, repos=[repo_dir])
        try:
            for p in patches:
                p.start()
            with patch(
                "metabolon.organelles.retrograde.subprocess.run",
                side_effect=OSError("no git"),
            ):
                assert retro._count_retrograde(7) == 0
        finally:
            for p in patches:
                p.stop()

    def test_repo_without_git_skipped(self, tmp_path):
        repo_dir = tmp_path / "nogit"
        repo_dir.mkdir()
        # No .git directory

        patches = self._patch_env(tmp_path, repos=[repo_dir])
        try:
            for p in patches:
                p.start()
            # Should not call subprocess at all — just return 0
            with patch(
                "metabolon.organelles.retrograde.subprocess.run", side_effect=AssertionError
            ):
                assert retro._count_retrograde(7) == 0
        finally:
            for p in patches:
                p.stop()

    def test_methylation_candidates_counted(self, tmp_path):
        now = _recent_ts(0)
        patches = self._patch_env(tmp_path)
        try:
            for p in patches:
                p.start()
            meth_cand = tmp_path / "meth_cand.jsonl"
            _make_jsonl(meth_cand, [{"ts": now, "proposal": "test"}])
            assert retro._count_retrograde(7) >= 1
        finally:
            for p in patches:
                p.stop()

    def test_old_methylation_excluded(self, tmp_path):
        old = _recent_ts(30)
        patches = self._patch_env(tmp_path)
        try:
            for p in patches:
                p.start()
            meth_cand = tmp_path / "meth_cand.jsonl"
            _make_jsonl(meth_cand, [{"ts": old, "proposal": "old"}])
            assert retro._count_retrograde(7) == 0
        finally:
            for p in patches:
                p.stop()

    def test_methylation_jsonl_counted(self, tmp_path):
        now = _recent_ts(0)
        patches = self._patch_env(tmp_path)
        try:
            for p in patches:
                p.start()
            meth_jsonl = tmp_path / "meth.jsonl"
            _make_jsonl(meth_jsonl, [{"ts": now, "key": "val"}])
            assert retro._count_retrograde(7) >= 1
        finally:
            for p in patches:
                p.stop()

    def test_infections_healed_counted(self, tmp_path):
        now = _recent_ts(0)
        patches = self._patch_env(tmp_path)
        try:
            for p in patches:
                p.start()
            infect = tmp_path / "infections.jsonl"
            _make_jsonl(
                infect,
                [{"ts": now, "tool": "real_tool", "healed": True}],
            )
            assert retro._count_retrograde(7) >= 1
        finally:
            for p in patches:
                p.stop()

    def test_infections_test_fixtures_excluded(self, tmp_path):
        now = _recent_ts(0)
        patches = self._patch_env(tmp_path)
        try:
            for p in patches:
                p.start()
            infect = tmp_path / "infections.jsonl"
            _make_jsonl(
                infect,
                [
                    {"ts": now, "tool": "fail_tool", "healed": True},
                    {"ts": now, "tool": "failing_tool", "healed": True},
                    {"ts": now, "tool": "unknown_tool", "healed": True},
                    {"ts": now, "tool": "tool", "healed": True},
                    {"ts": now, "tool": "real_tool", "healed": True},
                ],
            )
            # Only real_tool should count
            assert retro._count_retrograde(7) == 1
        finally:
            for p in patches:
                p.stop()

    def test_unhealed_infection_not_counted(self, tmp_path):
        now = _recent_ts(0)
        patches = self._patch_env(tmp_path)
        try:
            for p in patches:
                p.start()
            infect = tmp_path / "infections.jsonl"
            _make_jsonl(
                infect,
                [{"ts": now, "tool": "real_tool", "healed": False}],
            )
            assert retro._count_retrograde(7) == 0
        finally:
            for p in patches:
                p.stop()

    def test_logged_retrograde_signals_counted(self, tmp_path):
        now = _recent_ts(0)
        patches = self._patch_env(tmp_path)
        try:
            for p in patches:
                p.start()
            sig = tmp_path / "signals.jsonl"
            _make_jsonl(sig, [{"ts": now, "direction": "retrograde", "type": "manual"}])
            assert retro._count_retrograde(7) >= 1
        finally:
            for p in patches:
                p.stop()

    def test_malformed_infection_line_skipped(self, tmp_path):
        patches = self._patch_env(tmp_path)
        try:
            for p in patches:
                p.start()
            infect = tmp_path / "infections.jsonl"
            infect.write_text("NOTJSON\n")
            assert retro._count_retrograde(7) == 0
        finally:
            for p in patches:
                p.stop()


# ---------------------------------------------------------------------------
# signal_balance
# ---------------------------------------------------------------------------


class TestSignalBalance:
    def test_sovereign_when_high_anterograde(self):
        with (
            patch.object(retro, "_count_anterograde", return_value=30),
            patch.object(retro, "_count_retrograde", return_value=5),
        ):
            result = retro.signal_balance(7)
            assert result["assessment"] == "sovereign"
            assert result["ratio"] == 6.0
            assert result["anterograde_count"] == 30
            assert result["retrograde_count"] == 5
            assert result["window_days"] == 7

    def test_balanced_when_moderate(self):
        with (
            patch.object(retro, "_count_anterograde", return_value=10),
            patch.object(retro, "_count_retrograde", return_value=5),
        ):
            result = retro.signal_balance(7)
            assert result["assessment"] == "balanced"
            assert result["ratio"] == 2.0

    def test_balanced_at_boundary_1_to_1(self):
        with (
            patch.object(retro, "_count_anterograde", return_value=5),
            patch.object(retro, "_count_retrograde", return_value=5),
        ):
            result = retro.signal_balance(7)
            assert result["assessment"] == "balanced"
            assert result["ratio"] == 1.0

    def test_sovereign_at_boundary_3_to_1(self):
        with (
            patch.object(retro, "_count_anterograde", return_value=15),
            patch.object(retro, "_count_retrograde", return_value=5),
        ):
            result = retro.signal_balance(7)
            assert result["assessment"] == "sovereign"
            assert result["ratio"] == 3.0

    def test_dependent_when_retrograde_dominates(self):
        with (
            patch.object(retro, "_count_anterograde", return_value=2),
            patch.object(retro, "_count_retrograde", return_value=10),
        ):
            result = retro.signal_balance(7)
            assert result["assessment"] == "dependent"
            assert result["ratio"] == 0.2

    def test_zero_retrograde_ratio_equals_anterograde(self):
        """When retrograde=0, ratio = float(anterograde) if ante > 0."""
        with (
            patch.object(retro, "_count_anterograde", return_value=5),
            patch.object(retro, "_count_retrograde", return_value=0),
        ):
            result = retro.signal_balance(7)
            assert result["ratio"] == 5.0
            assert result["assessment"] == "sovereign"

    def test_zero_both_defaults_ratio_to_1(self):
        with (
            patch.object(retro, "_count_anterograde", return_value=0),
            patch.object(retro, "_count_retrograde", return_value=0),
        ):
            result = retro.signal_balance(7)
            assert result["ratio"] == 1.0
            assert result["assessment"] == "balanced"

    def test_default_window_is_7(self):
        with (
            patch.object(retro, "_count_anterograde", return_value=0),
            patch.object(retro, "_count_retrograde", return_value=0),
        ):
            result = retro.signal_balance()
            assert result["window_days"] == 7

    def test_custom_window(self):
        with (
            patch.object(retro, "_count_anterograde", return_value=0) as m_ante,
            patch.object(retro, "_count_retrograde", return_value=0) as m_retro,
        ):
            retro.signal_balance(30)
            m_ante.assert_called_once_with(30)
            m_retro.assert_called_once_with(30)

    def test_ratio_is_rounded(self):
        with (
            patch.object(retro, "_count_anterograde", return_value=10),
            patch.object(retro, "_count_retrograde", return_value=3),
        ):
            result = retro.signal_balance(7)
            assert result["ratio"] == 3.33
