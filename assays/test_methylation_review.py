from __future__ import annotations

"""Tests for effectors/methylation-review — weekly methylation review synthesis.

methylation-review is a script (effectors/methylation-review), not an importable module.
It is loaded via exec() so that module-level constants can be patched per test.
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

METHYLATION_REVIEW_PATH = Path(__file__).resolve().parents[1] / "effectors" / "methylation-review"


# ── Fixture ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def mr(tmp_path):
    """Load methylation-review via exec, redirect all path constants to tmp_path."""
    ns: dict = {"__name__": "test_methylation_review"}
    source = METHYLATION_REVIEW_PATH.read_text(encoding="utf-8")
    exec(source, ns)

    # Redirect paths to tmp_path so no real filesystem access happens
    germline_dir = tmp_path / "germline"
    germline_dir.mkdir()
    tmp_dir = tmp_path / "tmp"
    tmp_dir.mkdir()

    ns["GERMLINE"] = germline_dir
    ns["METHYLATION_JSONL"] = germline_dir / "methylation.jsonl"
    ns["METHYLATION_EFFECTOR"] = germline_dir / "effectors" / "methylation"
    ns["TMP_DIR"] = tmp_dir
    ns["CHANNEL"] = germline_dir / "effectors" / "channel"

    return ns


# ── run_cmd ──────────────────────────────────────────────────────────────────


class TestRunCmd:
    def test_success_returns_code_outputs(self, mr):
        mock_result = MagicMock(returncode=0, stdout="output text", stderr="")
        with patch.object(mr["subprocess"], "run", return_value=mock_result):
            code, out, err = mr["run_cmd"](["echo", "hello"])
        assert code == 0
        assert out == "output text"
        assert err == ""

    def test_nonzero_returns_code_stderr(self, mr):
        mock_result = MagicMock(returncode=1, stdout="", stderr="bad")
        with patch.object(mr["subprocess"], "run", return_value=mock_result):
            code, out, err = mr["run_cmd"](["false"])
        assert code == 1
        assert err == "bad"

    def test_exception_returns_minus_one_error(self, mr):
        with patch.object(mr["subprocess"], "run", side_effect=FileNotFoundError("no cmd")):
            code, out, err = mr["run_cmd"](["nonexistent_command_xyz_123"])
        assert code == -1
        assert out == ""
        assert "no cmd" in err


# ── gather_jsonl_observations ────────────────────────────────────────────────


class TestGatherJsonlObservations:
    def test_no_file_returns_message(self, mr):
        result = mr["gather_jsonl_observations"](days=7)
        assert "(no methylation.jsonl found)" in result

    def test_empty_file_returns_no_recent(self, mr):
        mr["METHYLATION_JSONL"].write_text("", encoding="utf-8")
        result = mr["gather_jsonl_observations"](days=7)
        assert "(no recent observations)" in result

    def test_includes_recent_excludes_old(self, mr):
        now = datetime.now(timezone.utc)
        recent_ts = (now - timedelta(days=3)).isoformat().replace("+00:00", "Z")
        old_ts = (now - timedelta(days=10)).isoformat().replace("+00:00", "Z")

        lines = [
            json.dumps({"ts": recent_ts, "event": "crystallize", "target": "skill-a"}),
            json.dumps({"ts": old_ts, "event": "trim", "target": "skill-b"}),
        ]
        mr["METHYLATION_JSONL"].write_text("\n".join(lines), encoding="utf-8")
        result = mr["gather_jsonl_observations"](days=7)
        assert "skill-a" in result
        assert "skill-b" not in result

    def test_handles_z_suffix_timestamps(self, mr):
        now = datetime.now(timezone.utc)
        ts = (now - timedelta(days=1)).isoformat().replace("+00:00", "Z")
        mr["METHYLATION_JSONL"].write_text(
            json.dumps({"ts": ts, "event": "test-z"}) + "\n", encoding="utf-8",
        )
        result = mr["gather_jsonl_observations"](days=7)
        assert "test-z" in result

    def test_handles_naive_timestamps(self, mr):
        now = datetime.now(timezone.utc)
        ts = (now - timedelta(days=3)).isoformat()  # no Z, no timezone
        mr["METHYLATION_JSONL"].write_text(
            json.dumps({"ts": ts, "event": "naive-ts"}) + "\n", encoding="utf-8",
        )
        result = mr["gather_jsonl_observations"](days=7)
        assert "naive-ts" in result

    def test_skips_bad_json_lines(self, mr):
        lines = [
            "not valid json {{",
            json.dumps({"ts": datetime.now().isoformat(), "event": "good"}),
        ]
        mr["METHYLATION_JSONL"].write_text("\n".join(lines), encoding="utf-8")
        result = mr["gather_jsonl_observations"](days=7)
        assert "good" in result
        assert len(result.splitlines()) == 1

    def test_error_reading_returns_error(self, mr):
        mr["METHYLATION_JSONL"].mkdir()  # directory, not file
        result = mr["gather_jsonl_observations"](days=7)
        assert "(error reading jsonl:" in result

    def test_days_parameter_filters(self, mr):
        now = datetime.now(timezone.utc)
        five_ago = (now - timedelta(days=5)).isoformat().replace("+00:00", "Z")
        two_ago = (now - timedelta(days=2)).isoformat().replace("+00:00", "Z")

        lines = [
            json.dumps({"ts": five_ago, "event": "five-day"}),
            json.dumps({"ts": two_ago, "event": "two-day"}),
        ]
        mr["METHYLATION_JSONL"].write_text("\n".join(lines), encoding="utf-8")
        result = mr["gather_jsonl_observations"](days=3)
        assert "two-day" in result
        assert "five-day" not in result


# ── gather_effector_proposals ────────────────────────────────────────────────


class TestGatherEffectorProposals:
    def test_no_files_returns_empty(self, mr):
        mr["METHYLATION_EFFECTOR"].parent.mkdir(parents=True, exist_ok=True)
        mr["METHYLATION_EFFECTOR"].write_text("#!", encoding="utf-8")

        def mock_run(cmd, **kwargs):
            return MagicMock(returncode=0, stdout="", stderr="")

        with patch.object(mr["subprocess"], "run", mock_run):
            result = mr["gather_effector_proposals"]()
        assert result == ""

    def test_combines_proposal_and_hybridization_files(self, mr):
        tmp_dir = mr["TMP_DIR"]
        today = datetime.now().strftime("%Y-%m-%d")

        prop_path = tmp_dir / f"methylation-proposal-{today}.md"
        prop_path.write_text("# Methylation Proposals\n\n- Fix labeling", encoding="utf-8")

        hyb_path = tmp_dir / f"hybridization-proposals-{today}.md"
        hyb_path.write_text("# Hybridization\n\n- Add new receptor", encoding="utf-8")

        mr["METHYLATION_EFFECTOR"].parent.mkdir(parents=True, exist_ok=True)
        mr["METHYLATION_EFFECTOR"].write_text("#!", encoding="utf-8")

        def mock_run(cmd, **kwargs):
            return MagicMock(returncode=0, stdout="", stderr="")

        with patch.object(mr["subprocess"], "run", mock_run):
            result = mr["gather_effector_proposals"]()

        assert "Methylation Proposals" in result
        assert "Hybridization" in result
        assert "Fix labeling" in result
        assert "Add new receptor" in result

    def test_effector_failure_logs_warning_continues(self, mr, capsys):
        mr["METHYLATION_EFFECTOR"].parent.mkdir(parents=True, exist_ok=True)
        mr["METHYLATION_EFFECTOR"].write_text("#!", encoding="utf-8")

        def mock_run(cmd, **kwargs):
            return MagicMock(returncode=1, stdout="", stderr="some error")

        with patch.object(mr["subprocess"], "run", mock_run):
            mr["gather_effector_proposals"]()
        out = capsys.readouterr().out
        assert "WARN: methylation effector failed" in out

    def test_only_proposal_file_exists(self, mr):
        tmp_dir = mr["TMP_DIR"]
        today = datetime.now().strftime("%Y-%m-%d")
        prop_path = tmp_dir / f"methylation-proposal-{today}.md"
        prop_path.write_text("- Item A\n- Item B", encoding="utf-8")

        mr["METHYLATION_EFFECTOR"].parent.mkdir(parents=True, exist_ok=True)
        mr["METHYLATION_EFFECTOR"].write_text("#!", encoding="utf-8")

        def mock_run(cmd, **kwargs):
            return MagicMock(returncode=0, stdout="", stderr="")

        with patch.object(mr["subprocess"], "run", mock_run):
            result = mr["gather_effector_proposals"]()
        assert "Item A" in result
        assert "Item B" in result


# ── synthesize_review ───────────────────────────────────────────────────────


class TestSynthesizeReview:
    def test_channel_success_returns_synthesized_output(self, mr):
        mock_output = "# Weekly Review\n\n## Mechanical\n- Safe stuff"

        def mock_run_cmd(cmd, timeout=180):
            return (0, mock_output, "")

        with patch.dict(mr, {"run_cmd": mock_run_cmd}):
            result = mr["synthesize_review"]("proposals", "observations")
        assert "Weekly Review" in result
        assert "Mechanical" in result
        assert "Safe stuff" in result

    def test_channel_failure_returns_error_plus_raw(self, mr):
        def mock_run_cmd(cmd, timeout=180):
            return (1, "", "channel error")

        with patch.dict(mr, {"run_cmd": mock_run_cmd}):
            result = mr["synthesize_review"]("raw proposals here", "obs here")
        assert "Error: Synthesis failed" in result
        assert "raw proposals here" in result
        assert "obs here" in result

    def test_passes_correct_prompt_to_channel(self, mr):
        captured = {}

        def mock_run_cmd(cmd, timeout=180):
            captured["cmd"] = cmd
            return (0, "synthesized", "")

        with patch.dict(mr, {"run_cmd": mock_run_cmd}):
            mr["synthesize_review"]("my props", "my obs")

        cmd = captured["cmd"]
        # Should call channel with "opus" and "-p" flag
        assert str(mr["CHANNEL"]) in cmd
        assert "opus" in cmd
        assert "-p" in cmd


# ── main ─────────────────────────────────────────────────────────────────────


class TestMain:
    def test_writes_review_to_tmp(self, mr, capsys):
        def mock_gather_effector():
            return "proposal content"

        def mock_gather_obs():
            return "observation content"

        def mock_synthesize(p, o):
            return "# Final Review\n\n- Done"

        with patch.dict(mr, {
            "gather_effector_proposals": mock_gather_effector,
            "gather_jsonl_observations": mock_gather_obs,
            "synthesize_review": mock_synthesize,
        }):
            mr["main"]()

        out = capsys.readouterr().out
        assert "Review written to" in out

        # Check file was created
        date_str = datetime.now().strftime("%Y-%m-%d")
        review_path = mr["TMP_DIR"] / f"methylation-review-{date_str}.md"
        assert review_path.exists()
        assert "Final Review" in review_path.read_text()

    def test_prints_summary(self, mr, capsys):
        def mock_gather_effector():
            return ""

        def mock_gather_obs():
            return ""

        def mock_synthesize(p, o):
            return "line1\nline2\nline3"

        with patch.dict(mr, {
            "gather_effector_proposals": mock_gather_effector,
            "gather_jsonl_observations": mock_gather_obs,
            "synthesize_review": mock_synthesize,
        }):
            mr["main"]()

        out = capsys.readouterr().out
        assert "Saved to" in out
        assert "--- Summary ---" in out
        assert "line1" in out

    def test_review_path_contains_date(self, mr, capsys):
        with patch.dict(mr, {
            "gather_effector_proposals": lambda: "",
            "gather_jsonl_observations": lambda: "",
            "synthesize_review": lambda p, o: "review body",
        }):
            mr["main"]()

        date_str = datetime.now().strftime("%Y-%m-%d")
        review_path = mr["TMP_DIR"] / f"methylation-review-{date_str}.md"
        assert review_path.exists()
