from __future__ import annotations

"""Tests for metabolon.pinocytosis.polarization — all external I/O mocked."""

import json
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from metabolon.pinocytosis.polarization import (
    GUARD_FILE,
    MANIFEST_FILE,
    NORTH_STAR_FILE,
    NOW_FILE,
    PRAXIS_FILE,
    REPORTS_DIR,
    _consumption_count,
    _fmt_resets,
    _guard_status,
    _manifest_summary,
    _north_stars,
    _now_md,
    _praxis_agent_claude,
    _praxis_phantom_count,
    _respirometry,
    budget,
    guard,
    intake,
    manifest_init,
    manifest_show,
)

# ── Helpers ────────────────────────────────────────────────────────


def _fake_file(content: str) -> MagicMock:
    """Return a mock that behaves like a Path file with given content."""
    p = MagicMock(spec=Path)
    p.exists.return_value = True
    p.read_text.return_value = content
    p.write_text = MagicMock()
    p.touch = MagicMock()
    p.unlink = MagicMock()
    return p


def _missing_file() -> MagicMock:
    """Return a mock Path that does not exist."""
    p = MagicMock(spec=Path)
    p.exists.return_value = False
    return p


# ── _consumption_count ────────────────────────────────────────────


class TestConsumptionCount:
    @patch.object(REPORTS_DIR.__class__, "exists", lambda self: False)
    def test_dir_missing_returns_zero(self):
        with patch.object(type(REPORTS_DIR), "exists", return_value=False):
            assert _consumption_count() == 0

    def test_counts_recent_files(self):
        f1 = MagicMock()
        f1.stat.return_value.st_mtime = time.time() - 100  # recent
        f2 = MagicMock()
        f2.stat.return_value.st_mtime = time.time() - 999_999  # old

        with (
            patch.object(type(REPORTS_DIR), "exists", return_value=True),
            patch.object(type(REPORTS_DIR), "iterdir", return_value=[f1, f2]),
        ):
            assert _consumption_count() == 1

    def test_empty_dir_returns_zero(self):
        with (
            patch.object(type(REPORTS_DIR), "exists", return_value=True),
            patch.object(type(REPORTS_DIR), "iterdir", return_value=[]),
        ):
            assert _consumption_count() == 0

    def test_all_recent(self):
        files = [
            MagicMock(stat=MagicMock(return_value=MagicMock(st_mtime=time.time() - i * 100)))
            for i in range(5)
        ]
        with (
            patch.object(type(REPORTS_DIR), "exists", return_value=True),
            patch.object(type(REPORTS_DIR), "iterdir", return_value=files),
        ):
            assert _consumption_count() == 5


# ── _respirometry ─────────────────────────────────────────────────


class TestRespirometry:
    def test_success_returns_parsed_dict(self):
        payload = {"weekly_pct": 42, "sonnet_pct": 10, "resets_at": "soon"}
        mock_result = MagicMock(
            returncode=0,
            stdout=json.dumps(payload),
        )
        with patch("metabolon.pinocytosis.polarization.subprocess.run", return_value=mock_result):
            assert _respirometry() == payload

    def test_nonzero_returncode_returns_error(self):
        mock_result = MagicMock(returncode=1, stdout="")
        with patch("metabolon.pinocytosis.polarization.subprocess.run", return_value=mock_result):
            result = _respirometry()
            assert result == {"error": "respirometry unavailable"}

    def test_timeout_returns_error(self):
        with patch(
            "metabolon.pinocytosis.polarization.subprocess.run",
            side_effect=subprocess.TimeoutExpired("cmd", 10),
        ):
            assert _respirometry() == {"error": "respirometry unavailable"}

    def test_not_found_returns_error(self):
        with patch(
            "metabolon.pinocytosis.polarization.subprocess.run", side_effect=FileNotFoundError
        ):
            assert _respirometry() == {"error": "respirometry unavailable"}

    def test_bad_json_returns_error(self):
        mock_result = MagicMock(returncode=0, stdout="not json")
        with patch("metabolon.pinocytosis.polarization.subprocess.run", return_value=mock_result):
            assert _respirometry() == {"error": "respirometry unavailable"}

    def test_empty_stdout_returns_error(self):
        mock_result = MagicMock(returncode=0, stdout="  \n  ")
        with patch("metabolon.pinocytosis.polarization.subprocess.run", return_value=mock_result):
            assert _respirometry() == {"error": "respirometry unavailable"}


# ── _guard_status ─────────────────────────────────────────────────


class TestGuardStatus:
    def test_file_exists_true(self):
        with patch.object(type(GUARD_FILE), "exists", return_value=True):
            assert _guard_status() is True

    def test_file_missing_false(self):
        with patch.object(type(GUARD_FILE), "exists", return_value=False):
            assert _guard_status() is False


# ── _manifest_summary ─────────────────────────────────────────────


class TestManifestSummary:
    def test_missing_returns_not_exists(self):
        with patch.object(type(MANIFEST_FILE), "exists", return_value=False):
            result = _manifest_summary()
            assert result == {"exists": False, "summary": None}

    def test_present_returns_first_8_lines(self):
        content = "\n".join(f"line {i}" for i in range(20))
        with (
            patch.object(type(MANIFEST_FILE), "exists", return_value=True),
            patch.object(type(MANIFEST_FILE), "read_text", return_value=content),
        ):
            result = _manifest_summary()
        assert result["exists"] is True
        assert result["summary"].count("\n") == 7  # 8 lines => 7 newlines

    def test_short_file(self):
        content = "only two\nlines here"
        with (
            patch.object(type(MANIFEST_FILE), "exists", return_value=True),
            patch.object(type(MANIFEST_FILE), "read_text", return_value=content),
        ):
            result = _manifest_summary()
        assert result["exists"] is True
        assert result["summary"] == content


# ── _north_stars ──────────────────────────────────────────────────


class TestNorthStars:
    def test_missing_file(self):
        with patch.object(type(NORTH_STAR_FILE), "exists", return_value=False):
            assert _north_stars() == []

    def test_parses_numbered_headings(self):
        content = "## 1. Ship X\n## 2. Fix Y\n### not a star\n## unnumbered\n## 3. Write Z\n"
        with (
            patch.object(type(NORTH_STAR_FILE), "exists", return_value=True),
            patch.object(type(NORTH_STAR_FILE), "read_text", return_value=content),
        ):
            result = _north_stars()
        assert result == ["1. Ship X", "2. Fix Y", "3. Write Z"]

    def test_no_matching_headings(self):
        content = "# top\n### sub\nnothing here\n"
        with (
            patch.object(type(NORTH_STAR_FILE), "exists", return_value=True),
            patch.object(type(NORTH_STAR_FILE), "read_text", return_value=content),
        ):
            assert _north_stars() == []


# ── _praxis_agent_claude ──────────────────────────────────────────


class TestPraxisAgentClaude:
    def test_missing_file(self):
        with patch.object(type(PRAXIS_FILE), "exists", return_value=False):
            assert _praxis_agent_claude() == []

    def test_extracts_matching_lines(self):
        content = "- item1 agent:claude x\n- item2\n- item3 agent:claude y\n"
        with (
            patch.object(type(PRAXIS_FILE), "exists", return_value=True),
            patch.object(type(PRAXIS_FILE), "read_text", return_value=content),
        ):
            result = _praxis_agent_claude()
        assert len(result) == 2
        assert "agent:claude" in result[0]
        assert "agent:claude" in result[1]

    def test_no_matching_lines(self):
        content = "- item1\n- item2 agent:terry\n"
        with (
            patch.object(type(PRAXIS_FILE), "exists", return_value=True),
            patch.object(type(PRAXIS_FILE), "read_text", return_value=content),
        ):
            assert _praxis_agent_claude() == []


# ── _praxis_phantom_count ────────────────────────────────────────


class TestPraxisPhantomCount:
    def test_missing_file(self):
        with patch.object(type(PRAXIS_FILE), "exists", return_value=False):
            assert _praxis_phantom_count() == 0

    def test_import_error_returns_zero(self):
        # The function does `from metabolon.checkpoint import sweep_praxis_for_phantoms`
        # inside a try/except. Remove the module from sys.modules so the import fails.
        with (
            patch.object(type(PRAXIS_FILE), "exists", return_value=True),
            patch.object(type(PRAXIS_FILE), "read_text", return_value="data"),
            patch.dict("sys.modules", {}, clear=False),
        ):
            # Ensure metabolon.checkpoint is not importable
            import sys

            sys.modules.pop("metabolon.checkpoint", None)
            assert _praxis_phantom_count() == 0

    def test_returns_count(self):
        with (
            patch.object(type(PRAXIS_FILE), "exists", return_value=True),
            patch.object(type(PRAXIS_FILE), "read_text", return_value="data"),
            patch("metabolon.pinocytosis.polarization.sweep_praxis_for_phantoms", create=True),
            patch.dict(
                "sys.modules",
                {
                    "metabolon.checkpoint": MagicMock(
                        sweep_praxis_for_phantoms=MagicMock(return_value=["a", "b", "c"])
                    )
                },
            ),
        ):
            # Need to patch at the import site
            pass
        # Simpler: patch the module-level import
        with (
            patch.object(type(PRAXIS_FILE), "exists", return_value=True),
            patch.object(type(PRAXIS_FILE), "read_text", return_value="data"),
        ):
            # The function does `from metabolon.checkpoint import ...` so
            # if that module doesn't exist it returns 0 — test the happy path
            # by injecting the module into sys.modules
            import sys

            fake_mod = MagicMock()
            fake_mod.sweep_praxis_for_phantoms.return_value = ["p1", "p2"]
            with patch.dict(sys.modules, {"metabolon.checkpoint": fake_mod}):
                assert _praxis_phantom_count() == 2


# ── _now_md ───────────────────────────────────────────────────────


class TestNowMd:
    def test_missing_returns_none(self):
        with patch.object(type(NOW_FILE), "exists", return_value=False):
            assert _now_md() is None

    def test_present_returns_content(self):
        with (
            patch.object(type(NOW_FILE), "exists", return_value=True),
            patch.object(type(NOW_FILE), "read_text", return_value="  hello world  \n"),
        ):
            assert _now_md() == "hello world"


# ── _fmt_resets ───────────────────────────────────────────────────


class TestFmtResets:
    def test_none_returns_question_mark(self):
        assert _fmt_resets(None) == "?"

    def test_empty_string_returns_question_mark(self):
        assert _fmt_resets("") == "?"

    def test_valid_iso(self):
        dt = datetime(2026, 4, 1, 12, 0, tzinfo=UTC)
        result = _fmt_resets(dt.isoformat())
        assert "2026-04-01" in result
        assert "HKT" in result

    def test_bad_string_returns_question_mark(self):
        assert _fmt_resets("not-a-date") == "?"


# ── guard() ───────────────────────────────────────────────────────


class TestGuard:
    def test_guard_on_creates_file(self):
        mock_gf = MagicMock(spec=Path)
        mock_gf.parent.mkdir = MagicMock()
        mock_gf.touch = MagicMock()
        with patch("metabolon.pinocytosis.polarization.GUARD_FILE", mock_gf):
            result = guard("on")
        assert "activated" in result
        mock_gf.touch.assert_called_once()

    def test_guard_off_existing(self):
        mock_gf = MagicMock(spec=Path)
        mock_gf.exists.return_value = True
        with patch("metabolon.pinocytosis.polarization.GUARD_FILE", mock_gf):
            result = guard("off")
        assert "deactivated" in result
        mock_gf.unlink.assert_called_once()

    def test_guard_off_not_active(self):
        mock_gf = MagicMock(spec=Path)
        mock_gf.exists.return_value = False
        with patch("metabolon.pinocytosis.polarization.GUARD_FILE", mock_gf):
            result = guard("off")
        assert "not active" in result

    def test_guard_status_active(self):
        mock_gf = MagicMock(spec=Path)
        mock_gf.exists.return_value = True
        with patch("metabolon.pinocytosis.polarization.GUARD_FILE", mock_gf):
            result = guard("status")
        assert "ACTIVE" in result

    def test_guard_status_inactive(self):
        mock_gf = MagicMock(spec=Path)
        mock_gf.exists.return_value = False
        with patch("metabolon.pinocytosis.polarization.GUARD_FILE", mock_gf):
            result = guard("status")
        assert "inactive" in result


# ── manifest_init() ───────────────────────────────────────────────


class TestManifestInit:
    def test_creates_manifest(self):
        mock_mf = MagicMock(spec=Path)
        mock_mf.parent.mkdir = MagicMock()
        mock_mf.write_text = MagicMock()
        with patch("metabolon.pinocytosis.polarization.MANIFEST_FILE", mock_mf):
            result = manifest_init()
        assert "Manifest created" in result
        mock_mf.write_text.assert_called_once()
        written = mock_mf.write_text.call_args[0][0]
        assert "Polarization Session" in written
        assert "Wave 1" in written


# ── manifest_show() ───────────────────────────────────────────────


class TestManifestShow:
    def test_missing_manifest(self):
        with patch.object(type(MANIFEST_FILE), "exists", return_value=False):
            result = manifest_show()
        assert "not found" in result

    def test_present_manifest(self):
        content = "# Session"
        with (
            patch.object(type(MANIFEST_FILE), "exists", return_value=True),
            patch.object(type(MANIFEST_FILE), "read_text", return_value=content),
        ):
            assert manifest_show() == content


# ── budget() ──────────────────────────────────────────────────────


class TestBudget:
    def _make_usage(
        self,
        opus_pct=50.0,
        sonnet_pct=30.0,
        opus_resets=None,
        sonnet_resets=None,
        stale=False,
        source="test",
    ):
        return {
            "seven_day": {
                "utilization": opus_pct,
                "resets_at": opus_resets or "2026-04-07T00:00:00+08:00",
            },
            "seven_day_sonnet": {
                "utilization": sonnet_pct,
                "resets_at": sonnet_resets or "2026-04-07T00:00:00+08:00",
            },
            "stale": stale,
            "source": source,
        }

    def test_happy_path_text(self):
        usage = self._make_usage()
        with patch(
            "metabolon.pinocytosis.polarization.get_usage", return_value=usage, create=True
        ):
            # Patch the import inside budget()
            fake_resp = MagicMock(return_value=usage)
            with patch.dict(
                "sys.modules", {"metabolon.respirometry": MagicMock(get_usage=fake_resp)}
            ):
                result = budget()
        assert "opus:" in result
        assert "50%" in result
        assert "sonnet:" in result
        assert "30%" in result

    def test_error_falls_back(self):
        with (
            patch.dict("sys.modules", {}),
            patch(
                "metabolon.pinocytosis.polarization._respirometry",
                return_value={"error": "unavailable"},
            ),
        ):
            result = budget()
        assert "unavailable" in result

    def test_json_output(self):
        usage = self._make_usage()
        fake_resp = MagicMock(return_value=usage)
        with patch.dict("sys.modules", {"metabolon.respirometry": MagicMock(get_usage=fake_resp)}):
            result = budget(as_json=True)
        data = json.loads(result)
        assert data["opus_pct"] == 50.0
        assert data["sonnet_pct"] == 30.0

    def test_json_error_output(self):
        with (
            patch.dict("sys.modules", {}),
            patch(
                "metabolon.pinocytosis.polarization._respirometry", return_value={"error": "fail"}
            ),
        ):
            result = budget(as_json=True)
        data = json.loads(result)
        assert data["error"] == "fail"

    def test_stale_marker(self):
        usage = self._make_usage(stale=True)
        fake_resp = MagicMock(return_value=usage)
        with patch.dict("sys.modules", {"metabolon.respirometry": MagicMock(get_usage=fake_resp)}):
            result = budget()
        assert "[stale]" in result

    def test_negative_utilization_shows_no_data(self):
        usage = self._make_usage(opus_pct=-1, sonnet_pct=-1)
        fake_resp = MagicMock(return_value=usage)
        with patch.dict("sys.modules", {"metabolon.respirometry": MagicMock(get_usage=fake_resp)}):
            result = budget()
        assert "no budget data available" in result


# ── intake() ──────────────────────────────────────────────────────


class TestIntake:
    def _patch_all(self):
        """Return a dict of patches for all helper functions."""
        return {
            "_consumption_count": patch(
                "metabolon.pinocytosis.polarization._consumption_count", return_value=5
            ),
            "_respirometry": patch(
                "metabolon.pinocytosis.polarization._respirometry",
                return_value={
                    "weekly_pct": 40,
                    "sonnet_pct": 20,
                    "resets_at": "soon",
                    "stale": False,
                },
            ),
            "_guard_status": patch(
                "metabolon.pinocytosis.polarization._guard_status", return_value=True
            ),
            "_manifest_summary": patch(
                "metabolon.pinocytosis.polarization._manifest_summary",
                return_value={"exists": False, "summary": None},
            ),
            "_north_stars": patch(
                "metabolon.pinocytosis.polarization._north_stars", return_value=["1. Ship it"]
            ),
            "_praxis_agent_claude": patch(
                "metabolon.pinocytosis.polarization._praxis_agent_claude",
                return_value=["- item agent:claude"],
            ),
            "_praxis_phantom_count": patch(
                "metabolon.pinocytosis.polarization._praxis_phantom_count", return_value=0
            ),
            "_now_md": patch(
                "metabolon.pinocytosis.polarization._now_md", return_value="do stuff"
            ),
        }

    def test_human_readable_output(self):
        patches = self._patch_all()
        with (
            patches["_consumption_count"],
            patches["_respirometry"],
            patches["_guard_status"],
            patches["_manifest_summary"],
            patches["_north_stars"],
            patches["_praxis_agent_claude"],
            patches["_praxis_phantom_count"],
            patches["_now_md"],
        ):
            result = intake()
        assert "POLARIZATION PREFLIGHT" in result
        assert "CONSUMPTION" in result
        assert "GUARD" in result
        assert "ACTIVE" in result
        assert "NORTH STARS" in result
        assert "1. Ship it" in result
        assert "NOW.md" in result

    def test_json_output(self):
        patches = self._patch_all()
        with (
            patches["_consumption_count"],
            patches["_respirometry"],
            patches["_guard_status"],
            patches["_manifest_summary"],
            patches["_north_stars"],
            patches["_praxis_agent_claude"],
            patches["_praxis_phantom_count"],
            patches["_now_md"],
        ):
            result = intake(as_json=True)
        data = json.loads(result)
        assert data["consumption_count"] == 5
        assert data["guard_active"] is True
        assert data["north_stars"] == ["1. Ship it"]
        assert data["praxis_agent_claude_count"] == 1
        assert data["now_md"] == "do stuff"

    def test_low_consumption_signal(self):
        patches = self._patch_all()
        patches["_consumption_count"] = patch(
            "metabolon.pinocytosis.polarization._consumption_count", return_value=1
        )
        with (
            patches["_consumption_count"],
            patches["_respirometry"],
            patches["_guard_status"],
            patches["_manifest_summary"],
            patches["_north_stars"],
            patches["_praxis_agent_claude"],
            patches["_praxis_phantom_count"],
            patches["_now_md"],
        ):
            result = intake()
        assert "Produce more" in result

    def test_medium_consumption_signal(self):
        patches = self._patch_all()
        patches["_consumption_count"] = patch(
            "metabolon.pinocytosis.polarization._consumption_count", return_value=5
        )
        with (
            patches["_consumption_count"],
            patches["_respirometry"],
            patches["_guard_status"],
            patches["_manifest_summary"],
            patches["_north_stars"],
            patches["_praxis_agent_claude"],
            patches["_praxis_phantom_count"],
            patches["_now_md"],
        ):
            result = intake()
        assert "Self-sufficient" in result

    def test_high_consumption_signal(self):
        patches = self._patch_all()
        patches["_consumption_count"] = patch(
            "metabolon.pinocytosis.polarization._consumption_count", return_value=12
        )
        with (
            patches["_consumption_count"],
            patches["_respirometry"],
            patches["_guard_status"],
            patches["_manifest_summary"],
            patches["_north_stars"],
            patches["_praxis_agent_claude"],
            patches["_praxis_phantom_count"],
            patches["_now_md"],
        ):
            result = intake()
        assert "Overproduction" in result

    def test_budget_error_in_output(self):
        patches = self._patch_all()
        patches["_respirometry"] = patch(
            "metabolon.pinocytosis.polarization._respirometry",
            return_value={"error": "respirometry unavailable"},
        )
        with (
            patches["_consumption_count"],
            patches["_respirometry"],
            patches["_guard_status"],
            patches["_manifest_summary"],
            patches["_north_stars"],
            patches["_praxis_agent_claude"],
            patches["_praxis_phantom_count"],
            patches["_now_md"],
        ):
            result = intake()
        assert "respirometry unavailable" in result

    def test_phantom_count_shown(self):
        patches = self._patch_all()
        patches["_praxis_phantom_count"] = patch(
            "metabolon.pinocytosis.polarization._praxis_phantom_count", return_value=3
        )
        with (
            patches["_consumption_count"],
            patches["_respirometry"],
            patches["_guard_status"],
            patches["_manifest_summary"],
            patches["_north_stars"],
            patches["_praxis_agent_claude"],
            patches["_praxis_phantom_count"],
            patches["_now_md"],
        ):
            result = intake()
        assert "3 suspect phantom" in result

    def test_manifest_with_content(self):
        patches = self._patch_all()
        patches["_manifest_summary"] = patch(
            "metabolon.pinocytosis.polarization._manifest_summary",
            return_value={"exists": True, "summary": "line1\nline2"},
        )
        with (
            patches["_consumption_count"],
            patches["_respirometry"],
            patches["_guard_status"],
            patches["_manifest_summary"],
            patches["_north_stars"],
            patches["_praxis_agent_claude"],
            patches["_praxis_phantom_count"],
            patches["_now_md"],
        ):
            result = intake()
        assert "line1" in result

    def test_now_md_missing(self):
        patches = self._patch_all()
        patches["_now_md"] = patch("metabolon.pinocytosis.polarization._now_md", return_value=None)
        with (
            patches["_consumption_count"],
            patches["_respirometry"],
            patches["_guard_status"],
            patches["_manifest_summary"],
            patches["_north_stars"],
            patches["_praxis_agent_claude"],
            patches["_praxis_phantom_count"],
            patches["_now_md"],
        ):
            result = intake()
        assert "not found" in result


# ── main() CLI ────────────────────────────────────────────────────


class TestMain:
    def test_default_preflight(self, capsys):
        with (
            patch("sys.argv", ["polarization"]),
            patch("metabolon.pinocytosis.polarization.intake", return_value="preflight output"),
        ):
            from metabolon.pinocytosis.polarization import main

            main()
        assert "preflight output" in capsys.readouterr().out

    def test_guard_on(self, capsys):
        with (
            patch("sys.argv", ["polarization", "guard", "on"]),
            patch("metabolon.pinocytosis.polarization.guard", return_value="ok"),
        ):
            from metabolon.pinocytosis.polarization import main

            main()
        assert "ok" in capsys.readouterr().out

    def test_manifest_init(self, capsys):
        with (
            patch("sys.argv", ["polarization", "manifest", "init"]),
            patch("metabolon.pinocytosis.polarization.manifest_init", return_value="created"),
        ):
            from metabolon.pinocytosis.polarization import main

            main()
        assert "created" in capsys.readouterr().out

    def test_manifest_show(self, capsys):
        with (
            patch("sys.argv", ["polarization", "manifest", "show"]),
            patch("metabolon.pinocytosis.polarization.manifest_show", return_value="shown"),
        ):
            from metabolon.pinocytosis.polarization import main

            main()
        assert "shown" in capsys.readouterr().out

    def test_manifest_update(self, capsys):
        with patch("sys.argv", ["polarization", "manifest", "update"]):
            from metabolon.pinocytosis.polarization import main

            main()
        assert "agents write directly" in capsys.readouterr().out

    def test_budget_cmd(self, capsys):
        with (
            patch("sys.argv", ["polarization", "budget"]),
            patch("metabolon.pinocytosis.polarization.budget", return_value="budget info"),
        ):
            from metabolon.pinocytosis.polarization import main

            main()
        assert "budget info" in capsys.readouterr().out

    def test_preflight_json_flag(self, capsys):
        with (
            patch("sys.argv", ["polarization", "preflight", "--json"]),
            patch("metabolon.pinocytosis.polarization.intake", return_value='{"key": 1}') as mock,
        ):
            from metabolon.pinocytosis.polarization import main

            main()
        mock.assert_called_once_with(as_json=True)
