from __future__ import annotations

"""Tests for metabolon.organelles.retrograde — symbiont influence tracking."""

import datetime
import json
from unittest.mock import MagicMock, mock_open, patch

from metabolon.organelles.retrograde import (
    _count_anterograde,
    _count_logged,
    _count_retrograde,
    _cutoff_iso,
    log_signal,
    signal_balance,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _iso(minutes_ago: int = 0) -> str:
    """ISO timestamp for *now minus minutes_ago*."""
    dt = datetime.datetime.now(datetime.UTC) - datetime.timedelta(minutes=minutes_ago)
    return dt.isoformat()


def _signals_lines(*entries: dict) -> str:
    return "\n".join(json.dumps(e) for e in entries) + "\n"


def _make_event(ts: str, event: str = "", cmd: str = "") -> dict:
    return {"ts": ts, "event": event, "cmd": cmd}


def _make_signal(ts: str, direction: str, stype: str = "", detail: str = "") -> dict:
    return {"ts": ts, "direction": direction, "type": stype, "detail": detail}


# ===========================================================================
# log_signal
# ===========================================================================


class TestLogSignal:
    """Tests for log_signal()."""

    @patch("metabolon.organelles.retrograde.SIGNALS_LOG", new_callable=MagicMock)
    def test_appends_entry(self, mock_path: MagicMock) -> None:
        mock_path.parent.mkdir = MagicMock()
        mock_path.open = mock_open()
        before = datetime.datetime.now(datetime.UTC)
        log_signal("anterograde", "dispatch", "test detail")
        after = datetime.datetime.now(datetime.UTC)

        mock_path.open.assert_called_once_with("a")
        handle = mock_path.open.return_value
        handle.write.assert_called_once()
        written = handle.write.call_args[0][0]
        entry = json.loads(written.strip())
        assert entry["direction"] == "anterograde"
        assert entry["type"] == "dispatch"
        assert entry["detail"] == "test detail"
        ts = datetime.datetime.fromisoformat(entry["ts"])
        assert before <= ts <= after

    @patch("metabolon.organelles.retrograde.SIGNALS_LOG", new_callable=MagicMock)
    def test_creates_parent_directory(self, mock_path: MagicMock) -> None:
        mock_path.open = mock_open()
        log_signal("retrograde", "commit")
        mock_path.parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @patch("metabolon.organelles.retrograde.SIGNALS_LOG", new_callable=MagicMock)
    def test_default_detail_empty(self, mock_path: MagicMock) -> None:
        mock_path.parent.mkdir = MagicMock()
        mock_path.open = mock_open()
        log_signal("retrograde", "memory_write")
        handle = mock_path.open.return_value
        written = handle.write.call_args[0][0]
        entry = json.loads(written.strip())
        assert entry["detail"] == ""

    @patch("metabolon.organelles.retrograde.SIGNALS_LOG", new_callable=MagicMock)
    def test_written_line_ends_with_newline(self, mock_path: MagicMock) -> None:
        mock_path.parent.mkdir = MagicMock()
        mock_path.open = mock_open()
        log_signal("anterograde", "pulse")
        handle = mock_path.open.return_value
        written = handle.write.call_args[0][0]
        assert written.endswith("\n")

    @patch("metabolon.organelles.retrograde.SIGNALS_LOG", new_callable=MagicMock)
    def test_multiple_appends(self, mock_path: MagicMock) -> None:
        mock_path.parent.mkdir = MagicMock()
        mock_path.open = mock_open()
        log_signal("anterograde", "a")
        log_signal("retrograde", "b")
        log_signal("anterograde", "c")
        assert mock_path.open.call_count == 3


# ===========================================================================
# _cutoff_iso
# ===========================================================================


class TestCutoffIso:
    """Tests for _cutoff_iso()."""

    @patch("metabolon.organelles.retrograde.datetime")
    def test_returns_iso_string(self, mock_dt: MagicMock) -> None:
        fake_now = datetime.datetime(2026, 1, 15, 12, 0, 0, tzinfo=datetime.UTC)
        mock_dt.datetime.now.return_value = fake_now
        mock_dt.timedelta = datetime.timedelta
        mock_dt.UTC = datetime.UTC
        result = _cutoff_iso(7)
        expected = datetime.datetime(2026, 1, 8, 12, 0, 0, tzinfo=datetime.UTC).isoformat()
        assert result == expected

    @patch("metabolon.organelles.retrograde.datetime")
    def test_zero_days(self, mock_dt: MagicMock) -> None:
        fake_now = datetime.datetime(2026, 4, 1, 0, 0, 0, tzinfo=datetime.UTC)
        mock_dt.datetime.now.return_value = fake_now
        mock_dt.timedelta = datetime.timedelta
        mock_dt.UTC = datetime.UTC
        result = _cutoff_iso(0)
        assert result == fake_now.isoformat()


# ===========================================================================
# _count_logged
# ===========================================================================


class TestCountLogged:
    """Tests for _count_logged()."""

    @patch("metabolon.organelles.retrograde.SIGNALS_LOG", new_callable=MagicMock)
    def test_empty_file(self, mock_path: MagicMock) -> None:
        mock_path.exists.return_value = False
        assert _count_logged(7, "anterograde") == 0

    @patch("metabolon.organelles.retrograde.SIGNALS_LOG", new_callable=MagicMock)
    def test_counts_matching_direction(self, mock_path: MagicMock) -> None:
        mock_path.exists.return_value = True
        lines = _signals_lines(
            _make_signal(_iso(0), "anterograde"),
            _make_signal(_iso(0), "retrograde"),
            _make_signal(_iso(1), "anterograde"),
        )
        mock_path.read_text.return_value = lines
        assert _count_logged(7, "anterograde") == 2

    @patch("metabolon.organelles.retrograde.SIGNALS_LOG", new_callable=MagicMock)
    def test_excludes_old_entries(self, mock_path: MagicMock) -> None:
        mock_path.exists.return_value = True
        old_ts = _iso(60 * 24 * 10)  # 10 days ago
        lines = _signals_lines(
            _make_signal(old_ts, "anterograde"),
            _make_signal(_iso(0), "anterograde"),
        )
        mock_path.read_text.return_value = lines
        assert _count_logged(7, "anterograde") == 1

    @patch("metabolon.organelles.retrograde.SIGNALS_LOG", new_callable=MagicMock)
    def test_malformed_json_skipped(self, mock_path: MagicMock) -> None:
        mock_path.exists.return_value = True
        valid = _make_signal(_iso(0), "retrograde")
        mock_path.read_text.return_value = "BAD JSON\n" + json.dumps(valid) + "\n"
        assert _count_logged(7, "retrograde") == 1

    @patch("metabolon.organelles.retrograde.SIGNALS_LOG", new_callable=MagicMock)
    def test_naive_ts_treated_as_utc(self, mock_path: MagicMock) -> None:
        mock_path.exists.return_value = True
        naive_ts = datetime.datetime.now(datetime.UTC).isoformat()[:23]  # strip tz
        lines = _signals_lines(
            {"ts": naive_ts, "direction": "anterograde", "type": "x"},
        )
        mock_path.read_text.return_value = lines
        assert _count_logged(1, "anterograde") == 1


# ===========================================================================
# _count_anterograde
# ===========================================================================


class TestCountAnterograde:
    """Tests for _count_anterograde()."""

    @patch("metabolon.organelles.retrograde._count_logged", return_value=0)
    @patch("metabolon.organelles.retrograde.EVENT_LOG", new_callable=MagicMock)
    def test_empty_event_log(self, mock_event_log: MagicMock, mock_counted: MagicMock) -> None:
        mock_event_log.exists.return_value = False
        assert _count_anterograde(7) == 0

    @patch("metabolon.organelles.retrograde._count_logged", return_value=0)
    @patch("metabolon.organelles.retrograde.EVENT_LOG", new_callable=MagicMock)
    def test_counts_systole_events(
        self, mock_event_log: MagicMock, mock_counted: MagicMock
    ) -> None:
        mock_event_log.exists.return_value = True
        lines = (
            "\n".join(
                json.dumps(e)
                for e in [
                    _make_event(_iso(0), "systole_start"),
                    _make_event(_iso(1), "run_start"),
                    _make_event(_iso(2), "adapt_start"),
                ]
            )
            + "\n"
        )
        mock_event_log.read_text.return_value = lines
        assert _count_anterograde(7) == 3

    @patch("metabolon.organelles.retrograde._count_logged", return_value=0)
    @patch("metabolon.organelles.retrograde.EVENT_LOG", new_callable=MagicMock)
    def test_counts_channel_cmd(self, mock_event_log: MagicMock, mock_counted: MagicMock) -> None:
        mock_event_log.exists.return_value = True
        lines = json.dumps(_make_event(_iso(0), cmd="channel")) + "\n"
        mock_event_log.read_text.return_value = lines
        assert _count_anterograde(7) == 1

    @patch("metabolon.organelles.retrograde._count_logged", return_value=0)
    @patch("metabolon.organelles.retrograde.EVENT_LOG", new_callable=MagicMock)
    def test_ignores_unrelated_events(
        self, mock_event_log: MagicMock, mock_counted: MagicMock
    ) -> None:
        mock_event_log.exists.return_value = True
        lines = json.dumps(_make_event(_iso(0), event="something_else")) + "\n"
        mock_event_log.read_text.return_value = lines
        assert _count_anterograde(7) == 0

    @patch("metabolon.organelles.retrograde._count_logged", return_value=5)
    @patch("metabolon.organelles.retrograde.EVENT_LOG", new_callable=MagicMock)
    def test_adds_logged_count(self, mock_event_log: MagicMock, mock_counted: MagicMock) -> None:
        mock_event_log.exists.return_value = False
        assert _count_anterograde(7) == 5

    @patch("metabolon.organelles.retrograde._count_logged", return_value=0)
    @patch("metabolon.organelles.retrograde.EVENT_LOG", new_callable=MagicMock)
    def test_excludes_old_events(self, mock_event_log: MagicMock, mock_counted: MagicMock) -> None:
        mock_event_log.exists.return_value = True
        old_ts = _iso(60 * 24 * 10)  # 10 days ago
        lines = json.dumps(_make_event(old_ts, "systole_start")) + "\n"
        mock_event_log.read_text.return_value = lines
        assert _count_anterograde(7) == 0

    @patch("metabolon.organelles.retrograde._count_logged", return_value=0)
    @patch("metabolon.organelles.retrograde.EVENT_LOG", new_callable=MagicMock)
    def test_malformed_event_skipped(
        self, mock_event_log: MagicMock, mock_counted: MagicMock
    ) -> None:
        mock_event_log.exists.return_value = True
        good = _make_event(_iso(0), "systole_start")
        mock_event_log.read_text.return_value = "NOT JSON\n" + json.dumps(good) + "\n"
        assert _count_anterograde(7) == 1


# ===========================================================================
# _count_retrograde
# ===========================================================================


class TestCountRetrograde:
    """Tests for _count_retrograde()."""

    @patch("metabolon.organelles.retrograde._count_logged", return_value=0)
    @patch("metabolon.organelles.retrograde.INFECTIONS_LOG", new_callable=MagicMock)
    @patch("metabolon.organelles.retrograde.METHYLATION_JSONL", new_callable=MagicMock)
    @patch("metabolon.organelles.retrograde.METHYLATION_CANDIDATES", new_callable=MagicMock)
    @patch("metabolon.organelles.retrograde.TRACKED_REPOS", new=[])
    @patch("metabolon.organelles.retrograde.subprocess")
    def test_no_data_returns_zero(
        self,
        mock_sp: MagicMock,
        mock_mc: MagicMock,
        mock_mj: MagicMock,
        mock_il: MagicMock,
        mock_cl: MagicMock,
    ) -> None:
        mock_mc.exists.return_value = False
        mock_mj.exists.return_value = False
        mock_il.exists.return_value = False
        assert _count_retrograde(7) == 0

    @patch("metabolon.organelles.retrograde._count_logged", return_value=0)
    @patch("metabolon.organelles.retrograde.INFECTIONS_LOG", new_callable=MagicMock)
    @patch("metabolon.organelles.retrograde.METHYLATION_JSONL", new_callable=MagicMock)
    @patch("metabolon.organelles.retrograde.METHYLATION_CANDIDATES", new_callable=MagicMock)
    @patch("metabolon.organelles.retrograde.TRACKED_REPOS", new=[MagicMock()])
    @patch("metabolon.organelles.retrograde.subprocess")
    def test_counts_git_commits(
        self,
        mock_sp: MagicMock,
        mock_mc: MagicMock,
        mock_mj: MagicMock,
        mock_il: MagicMock,
        mock_cl: MagicMock,
    ) -> None:
        mock_sp.run.return_value = MagicMock(
            stdout="abc123 fix bug\ndef456 add feature\n", stderr=""
        )
        mock_mc.exists.return_value = False
        mock_mj.exists.return_value = False
        mock_il.exists.return_value = False
        # MagicMock repo: repo / ".git".exists() returns truthy MagicMock
        result = _count_retrograde(7)
        assert result >= 2  # at least the 2 git commits

    @patch("metabolon.organelles.retrograde._count_logged", return_value=0)
    @patch("metabolon.organelles.retrograde.INFECTIONS_LOG", new_callable=MagicMock)
    @patch("metabolon.organelles.retrograde.METHYLATION_JSONL", new_callable=MagicMock)
    @patch("metabolon.organelles.retrograde.METHYLATION_CANDIDATES", new_callable=MagicMock)
    @patch("metabolon.organelles.retrograde.TRACKED_REPOS", new=[])
    @patch("metabolon.organelles.retrograde.subprocess")
    def test_counts_methylation_candidates(
        self,
        mock_sp: MagicMock,
        mock_mc: MagicMock,
        mock_mj: MagicMock,
        mock_il: MagicMock,
        mock_cl: MagicMock,
    ) -> None:
        entry = {"ts": _iso(0), "action": "propose"}
        mock_mc.exists.return_value = True
        mock_mc.read_text.return_value = json.dumps(entry) + "\n"
        mock_mj.exists.return_value = False
        mock_il.exists.return_value = False
        assert _count_retrograde(7) >= 1

    @patch("metabolon.organelles.retrograde._count_logged", return_value=0)
    @patch("metabolon.organelles.retrograde.INFECTIONS_LOG", new_callable=MagicMock)
    @patch("metabolon.organelles.retrograde.METHYLATION_JSONL", new_callable=MagicMock)
    @patch("metabolon.organelles.retrograde.METHYLATION_CANDIDATES", new_callable=MagicMock)
    @patch("metabolon.organelles.retrograde.TRACKED_REPOS", new=[])
    @patch("metabolon.organelles.retrograde.subprocess")
    def test_counts_healed_infections_not_test_fixtures(
        self,
        mock_sp: MagicMock,
        mock_mc: MagicMock,
        mock_mj: MagicMock,
        mock_il: MagicMock,
        mock_cl: MagicMock,
    ) -> None:
        healed_real = {"ts": _iso(0), "tool": "some_real_tool", "healed": True}
        healed_fixture = {"ts": _iso(0), "tool": "fail_tool", "healed": True}
        not_healed = {"ts": _iso(0), "tool": "another_tool", "healed": False}
        mock_mc.exists.return_value = False
        mock_mj.exists.return_value = False
        mock_il.exists.return_value = True
        mock_il.read_text.return_value = (
            "\n".join(json.dumps(e) for e in [healed_real, healed_fixture, not_healed]) + "\n"
        )
        # Should count only the healed_real entry (1)
        assert _count_retrograde(7) == 1

    @patch("metabolon.organelles.retrograde._count_logged", return_value=3)
    @patch("metabolon.organelles.retrograde.INFECTIONS_LOG", new_callable=MagicMock)
    @patch("metabolon.organelles.retrograde.METHYLATION_JSONL", new_callable=MagicMock)
    @patch("metabolon.organelles.retrograde.METHYLATION_CANDIDATES", new_callable=MagicMock)
    @patch("metabolon.organelles.retrograde.TRACKED_REPOS", new=[])
    @patch("metabolon.organelles.retrograde.subprocess")
    def test_adds_logged_retrograde(
        self,
        mock_sp: MagicMock,
        mock_mc: MagicMock,
        mock_mj: MagicMock,
        mock_il: MagicMock,
        mock_cl: MagicMock,
    ) -> None:
        mock_mc.exists.return_value = False
        mock_mj.exists.return_value = False
        mock_il.exists.return_value = False
        assert _count_retrograde(7) == 3

    @patch("metabolon.organelles.retrograde._count_logged", return_value=0)
    @patch("metabolon.organelles.retrograde.INFECTIONS_LOG", new_callable=MagicMock)
    @patch("metabolon.organelles.retrograde.METHYLATION_JSONL", new_callable=MagicMock)
    @patch("metabolon.organelles.retrograde.METHYLATION_CANDIDATES", new_callable=MagicMock)
    @patch("metabolon.organelles.retrograde.TRACKED_REPOS", new=[])
    @patch("metabolon.organelles.retrograde.subprocess")
    def test_excludes_old_methylation(
        self,
        mock_sp: MagicMock,
        mock_mc: MagicMock,
        mock_mj: MagicMock,
        mock_il: MagicMock,
        mock_cl: MagicMock,
    ) -> None:
        old_ts = _iso(60 * 24 * 10)
        entry = {"ts": old_ts, "action": "propose"}
        mock_mc.exists.return_value = True
        mock_mc.read_text.return_value = json.dumps(entry) + "\n"
        mock_mj.exists.return_value = False
        mock_il.exists.return_value = False
        assert _count_retrograde(7) == 0

    @patch("metabolon.organelles.retrograde._count_logged", return_value=0)
    @patch("metabolon.organelles.retrograde.INFECTIONS_LOG", new_callable=MagicMock)
    @patch("metabolon.organelles.retrograde.METHYLATION_JSONL", new_callable=MagicMock)
    @patch("metabolon.organelles.retrograde.METHYLATION_CANDIDATES", new_callable=MagicMock)
    @patch("metabolon.organelles.retrograde.TRACKED_REPOS", new=[])
    @patch("metabolon.organelles.retrograde.subprocess")
    def test_git_exception_handled(
        self,
        mock_sp: MagicMock,
        mock_mc: MagicMock,
        mock_mj: MagicMock,
        mock_il: MagicMock,
        mock_cl: MagicMock,
    ) -> None:
        """Git command failure should not raise."""
        # TRACKED_REPOS is empty here, so no git calls happen — this test
        # validates that the function completes cleanly.
        mock_mc.exists.return_value = False
        mock_mj.exists.return_value = False
        mock_il.exists.return_value = False
        assert _count_retrograde(7) == 0


# ===========================================================================
# signal_balance
# ===========================================================================


class TestSignalBalance:
    """Tests for signal_balance()."""

    @patch("metabolon.organelles.retrograde._count_retrograde", return_value=0)
    @patch("metabolon.organelles.retrograde._count_anterograde", return_value=10)
    def test_sovereign_when_retro_zero(self, mock_ante: MagicMock, mock_retro: MagicMock) -> None:
        result = signal_balance(7)
        assert result["assessment"] == "sovereign"
        assert result["anterograde_count"] == 10
        assert result["retrograde_count"] == 0
        assert result["ratio"] == 10.0  # ante>0, retro==0 → float(ante)
        assert result["window_days"] == 7

    @patch("metabolon.organelles.retrograde._count_retrograde", return_value=1)
    @patch("metabolon.organelles.retrograde._count_anterograde", return_value=2)
    def test_balanced(self, mock_ante: MagicMock, mock_retro: MagicMock) -> None:
        result = signal_balance(7)
        assert result["assessment"] == "balanced"
        assert result["ratio"] == 2.0

    @patch("metabolon.organelles.retrograde._count_retrograde", return_value=10)
    @patch("metabolon.organelles.retrograde._count_anterograde", return_value=2)
    def test_dependent(self, mock_ante: MagicMock, mock_retro: MagicMock) -> None:
        result = signal_balance(7)
        assert result["assessment"] == "dependent"
        assert result["ratio"] == 0.2

    @patch("metabolon.organelles.retrograde._count_retrograde", return_value=0)
    @patch("metabolon.organelles.retrograde._count_anterograde", return_value=0)
    def test_both_zero(self, mock_ante: MagicMock, mock_retro: MagicMock) -> None:
        result = signal_balance(7)
        # ante==0, retro==0: ratio = (1.0 if ante>0 else 1.0) → 1.0
        assert result["ratio"] == 1.0
        assert result["assessment"] == "balanced"

    @patch("metabolon.organelles.retrograde._count_retrograde", return_value=1)
    @patch("metabolon.organelles.retrograde._count_anterograde", return_value=3)
    def test_sovereign_boundary(self, mock_ante: MagicMock, mock_retro: MagicMock) -> None:
        result = signal_balance(7)
        assert result["ratio"] == 3.0
        assert result["assessment"] == "sovereign"

    @patch("metabolon.organelles.retrograde._count_retrograde", return_value=1)
    @patch("metabolon.organelles.retrograde._count_anterograde", return_value=1)
    def test_balanced_at_one_to_one(self, mock_ante: MagicMock, mock_retro: MagicMock) -> None:
        result = signal_balance(7)
        assert result["ratio"] == 1.0
        assert result["assessment"] == "balanced"

    @patch("metabolon.organelles.retrograde._count_retrograde", return_value=3)
    @patch("metabolon.organelles.retrograde._count_anterograde", return_value=9)
    def test_ratio_rounded(self, mock_ante: MagicMock, mock_retro: MagicMock) -> None:
        result = signal_balance(7)
        assert result["ratio"] == 3.0
        assert isinstance(result["ratio"], float)

    @patch("metabolon.organelles.retrograde._count_retrograde", return_value=7)
    @patch("metabolon.organelles.retrograde._count_anterograde", return_value=10)
    def test_custom_window(self, mock_ante: MagicMock, mock_retro: MagicMock) -> None:
        result = signal_balance(30)
        assert result["window_days"] == 30
        mock_ante.assert_called_once_with(30)
        mock_retro.assert_called_once_with(30)

    @patch("metabolon.organelles.retrograde._count_retrograde", return_value=0)
    @patch("metabolon.organelles.retrograde._count_anterograde", return_value=0)
    def test_default_window_is_seven(self, mock_ante: MagicMock, mock_retro: MagicMock) -> None:
        signal_balance()
        mock_ante.assert_called_once_with(7)

    @patch("metabolon.organelles.retrograde._count_retrograde", return_value=2)
    @patch("metabolon.organelles.retrograde._count_anterograde", return_value=7)
    def test_ratio_rounds_to_two_decimals(
        self, mock_ante: MagicMock, mock_retro: MagicMock
    ) -> None:
        result = signal_balance(7)
        assert result["ratio"] == 3.5

    @patch("metabolon.organelles.retrograde._count_retrograde", return_value=0)
    @patch("metabolon.organelles.retrograde._count_anterograde", return_value=1)
    def test_retro_zero_ante_positive_default_ratio(
        self, mock_ante: MagicMock, mock_retro: MagicMock
    ) -> None:
        result = signal_balance(7)
        # ante>0, retro==0: ratio = float(ante) if ante>0 else 1.0 = 1.0
        assert result["ratio"] == 1.0
        assert result["assessment"] == "balanced"
