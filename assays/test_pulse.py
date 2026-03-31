"""Tests for pulse — the organism's heartbeat."""
from __future__ import annotations

import datetime
import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_paths(tmp_path, monkeypatch):
    """Set up mock paths for pulse files."""
    import metabolon.pulse as pulse

    monkeypatch.setattr(pulse, "CARDIAC_LOG", tmp_path / "pulse-manifest.md")
    monkeypatch.setattr(pulse, "CARDIAC_LOCK", tmp_path / "pulse.lock")
    monkeypatch.setattr(pulse, "TOPIC_LOCK", tmp_path / "pulse-topics-done.txt")
    monkeypatch.setattr(pulse, "LOG_DIR", tmp_path / "logs")
    monkeypatch.setattr(pulse, "REPORT_DIR", tmp_path / "reports")
    monkeypatch.setattr(pulse, "VITAL_SIGNS_FILE", tmp_path / "pulse-status.json")
    monkeypatch.setattr(pulse, "FOCUS_DIRECTIVE_FILE", tmp_path / "pulse-focus-directive.txt")
    monkeypatch.setattr(pulse, "PRAXIS_FILE", tmp_path / "Praxis.md")

    return {
        "cardiac_log": tmp_path / "pulse-manifest.md",
        "cardiac_lock": tmp_path / "pulse.lock",
        "topic_lock": tmp_path / "pulse-topics-done.txt",
        "log_dir": tmp_path / "logs",
        "report_dir": tmp_path / "reports",
        "vital_signs": tmp_path / "pulse-status.json",
        "focus_directive": tmp_path / "pulse-focus-directive.txt",
        "praxis": tmp_path / "Praxis.md",
    }


@pytest.fixture
def mock_vasomotor():
    """Mock vasomotor module functions."""
    with patch("metabolon.pulse.measure_vasomotor_tone") as mock_measure, \
         patch("metabolon.pulse.vasomotor_genome") as mock_genome, \
         patch("metabolon.pulse.vasomotor_status") as mock_status, \
         patch("metabolon.pulse.vasomotor_snapshot") as mock_snapshot, \
         patch("metabolon.pulse.record_event") as mock_record, \
         patch("metabolon.pulse.log") as mock_log, \
         patch("metabolon.pulse.is_apneic") as mock_apneic, \
         patch("metabolon.pulse.assess_vital_capacity") as mock_capacity, \
         patch("metabolon.pulse._fetch_telemetry") as mock_telemetry, \
         patch("metabolon.pulse._hours_to_reset") as mock_hours, \
         patch("metabolon.pulse.oxygen_debt") as mock_debt, \
         patch("metabolon.pulse.measured_cost_per_systole") as mock_cost, \
         patch("metabolon.pulse.breathe") as mock_breathe, \
         patch("metabolon.pulse.resume_breathing") as mock_resume, \
         patch("metabolon.pulse.set_recovery_interval") as mock_set_interval, \
         patch("metabolon.pulse.adapt") as mock_adapt, \
         patch("metabolon.pulse.emit_distress_signal") as mock_distress:

        mock_genome.return_value = {
            "infra_pct": 30,
            "basal_rate": 0.15,
            "min_basal_rate": 0.15,
            "max_systole_seconds": 1800,
            "stall_seconds": 300,
            "churn_seconds": 600,
            "systoles_per_run": 5,
            "saturation_patience": 2,
        }
        mock_apneic.return_value = (False, "")
        mock_capacity.return_value = (True, "plenty")
        mock_telemetry.return_value = {"seven_day": {"utilization": 50}}
        mock_hours.return_value = 12
        mock_debt.return_value = 0.0
        mock_cost.return_value = 5.0
        mock_status.return_value = "green"
        mock_snapshot.return_value = {"weekly": 50, "sonnet": 40}
        mock_measure.return_value = {"seven_day": {"utilization": 50}, "seven_day_sonnet": {"utilization": 40}}

        yield {
            "measure": mock_measure,
            "genome": mock_genome,
            "status": mock_status,
            "snapshot": mock_snapshot,
            "record": mock_record,
            "log": mock_log,
            "apneic": mock_apneic,
            "capacity": mock_capacity,
            "telemetry": mock_telemetry,
            "hours": mock_hours,
            "debt": mock_debt,
            "cost": mock_cost,
            "breathe": mock_breathe,
            "resume": mock_resume,
            "set_interval": mock_set_interval,
            "adapt": mock_adapt,
            "distress": mock_distress,
        }


# ---------------------------------------------------------------------------
# Cardiac Lock Tests
# ---------------------------------------------------------------------------


class TestAcquireCardiacLock:
    def test_creates_lock_when_none_exists(self, mock_paths):
        """Should create lock file when none exists."""
        import metabolon.pulse as pulse

        with patch.object(os, 'getpid', return_value=12345):
            pulse.acquire_cardiac_lock()

        assert mock_paths["cardiac_lock"].exists()
        assert mock_paths["cardiac_lock"].read_text() == "12345"

    def test_exits_if_same_pid_running(self, mock_paths):
        """Should exit if lock exists and PID is still running."""
        import metabolon.pulse as pulse

        mock_paths["cardiac_lock"].write_text("12345")

        with patch.object(os, 'getpid', return_value=99999), \
             patch.object(os, 'kill') as mock_kill:
            # os.kill succeeds means process is running
            mock_kill.return_value = None
            with pytest.raises(SystemExit):
                pulse.acquire_cardiac_lock()

    def test_removes_stale_lock_if_pid_not_running(self, mock_paths):
        """Should remove stale lock if PID no longer running."""
        import metabolon.pulse as pulse

        mock_paths["cardiac_lock"].write_text("12345")

        with patch.object(os, 'getpid', return_value=99999), \
             patch.object(os, 'kill') as mock_kill:
            # ProcessLookupError means PID not running
            mock_kill.side_effect = ProcessLookupError()
            pulse.acquire_cardiac_lock()

        assert mock_paths["cardiac_lock"].read_text() == "99999"

    def test_exits_on_permission_error_checking_pid(self, mock_paths):
        """Should exit if permission denied when checking PID."""
        import metabolon.pulse as pulse

        mock_paths["cardiac_lock"].write_text("12345")

        with patch.object(os, 'getpid', return_value=99999), \
             patch.object(os, 'kill') as mock_kill:
            mock_kill.side_effect = PermissionError()
            with pytest.raises(SystemExit):
                pulse.acquire_cardiac_lock()

    def test_handles_corrupt_lock_file(self, mock_paths):
        """Should handle corrupt lock file gracefully."""
        import metabolon.pulse as pulse

        mock_paths["cardiac_lock"].write_text("not-a-number")

        with patch.object(os, 'getpid', return_value=99999):
            pulse.acquire_cardiac_lock()

        assert mock_paths["cardiac_lock"].read_text() == "99999"


class TestReleaseCardiacLock:
    def test_releases_lock_owned_by_current_process(self, mock_paths):
        """Should release lock if owned by current process."""
        import metabolon.pulse as pulse

        mock_paths["cardiac_lock"].write_text("12345")

        with patch.object(os, 'getpid', return_value=12345):
            pulse.release_cardiac_lock()

        assert not mock_paths["cardiac_lock"].exists()

    def test_does_not_release_lock_owned_by_other_process(self, mock_paths):
        """Should not release lock if owned by another process."""
        import metabolon.pulse as pulse

        mock_paths["cardiac_lock"].write_text("12345")

        with patch.object(os, 'getpid', return_value=99999):
            pulse.release_cardiac_lock()

        assert mock_paths["cardiac_lock"].exists()
        assert mock_paths["cardiac_lock"].read_text() == "12345"

    def test_handles_missing_lock_file(self, mock_paths):
        """Should handle missing lock file gracefully."""
        import metabolon.pulse as pulse

        # Should not raise
        pulse.release_cardiac_lock()


# ---------------------------------------------------------------------------
# Cardiac Log Tests
# ---------------------------------------------------------------------------


class TestSeedCardiacLog:
    def test_creates_log_if_not_exists(self, mock_paths):
        """Should create cardiac log file if it doesn't exist."""
        import metabolon.pulse as pulse

        pulse.seed_cardiac_log()

        assert mock_paths["cardiac_log"].exists()
        content = mock_paths["cardiac_log"].read_text()
        assert "# Pulse Manifest" in content
        assert "## Completed" in content
        assert "## In Progress" in content

    def test_preserves_existing_log(self, mock_paths):
        """Should not overwrite existing cardiac log."""
        import metabolon.pulse as pulse

        mock_paths["cardiac_log"].write_text("# Existing content")
        pulse.seed_cardiac_log()

        assert mock_paths["cardiac_log"].read_text() == "# Existing content"

    def test_resets_topic_lock(self, mock_paths):
        """Should reset topic lock file on new run."""
        import metabolon.pulse as pulse

        mock_paths["topic_lock"].write_text("old-topics")
        pulse.seed_cardiac_log()

        assert not mock_paths["topic_lock"].exists()


class TestReadTopicsDone:
    def test_returns_empty_if_file_not_exists(self, mock_paths):
        """Should return empty string if topic lock doesn't exist."""
        import metabolon.pulse as pulse

        result = pulse.read_topics_done()
        assert result == ""

    def test_returns_file_contents(self, mock_paths):
        """Should return contents of topic lock file."""
        import metabolon.pulse as pulse

        mock_paths["topic_lock"].write_text("topic1\ntopic2\n")
        result = pulse.read_topics_done()
        assert result == "topic1\ntopic2"


class TestAppendTopicsDone:
    def test_appends_to_existing_file(self, mock_paths):
        """Should append topics to existing file."""
        import metabolon.pulse as pulse

        mock_paths["topic_lock"].write_text("existing\n")
        pulse.append_topics_done("new-topic")

        assert "existing" in mock_paths["topic_lock"].read_text()
        assert "new-topic" in mock_paths["topic_lock"].read_text()

    def test_creates_file_if_not_exists(self, mock_paths):
        """Should create file if it doesn't exist."""
        import metabolon.pulse as pulse

        pulse.append_topics_done("new-topic")
        assert "new-topic" in mock_paths["topic_lock"].read_text()


class TestCompactCardiacLog:
    def test_does_nothing_if_log_not_exists(self, mock_paths):
        """Should do nothing if cardiac log doesn't exist."""
        import metabolon.pulse as pulse

        # Should not raise
        pulse.compact_cardiac_log()

    def test_does_nothing_if_log_under_100_lines(self, mock_paths):
        """Should not compact if log has <= 100 lines."""
        import metabolon.pulse as pulse

        lines = ["Line " + str(i) for i in range(50)]
        mock_paths["cardiac_log"].write_text("\n".join(lines))

        pulse.compact_cardiac_log()

        result = mock_paths["cardiac_log"].read_text()
        assert len(result.splitlines()) == 50

    def test_compacts_log_over_100_lines(self, mock_paths, mock_vasomotor):
        """Should compact log if it has > 100 lines."""
        import metabolon.pulse as pulse

        # Create header (3 lines) + many content lines
        header = ["# Pulse Manifest -- 2026-03-31", "", "## Completed"]
        content = ["  - Item " + str(i) for i in range(150)]
        all_lines = header + content
        mock_paths["cardiac_log"].write_text("\n".join(all_lines))

        pulse.compact_cardiac_log()

        result = mock_paths["cardiac_log"].read_text()
        result_lines = result.splitlines()
        assert len(result_lines) <= 100
        assert "compacted" in result.lower()


# ---------------------------------------------------------------------------
# Disk Pressure Tests
# ---------------------------------------------------------------------------


class TestSenseDiskPressure:
    def test_returns_true_if_sufficient_disk(self, mock_paths, mock_vasomotor):
        """Should return True if disk has enough free space."""
        import metabolon.pulse as pulse

        with patch("metabolon.pulse.shutil.disk_usage") as mock_disk:
            # 20GB free
            mock_disk.return_value = MagicMock(free=20 * 1024**3)
            result = pulse.sense_disk_pressure()

        assert result is True

    def test_returns_true_on_disk_exception(self, mock_paths, mock_vasomotor):
        """Should return True if disk check fails (don't block)."""
        import metabolon.pulse as pulse

        with patch("metabolon.pulse.shutil.disk_usage") as mock_disk:
            mock_disk.side_effect = Exception("disk error")
            result = pulse.sense_disk_pressure()

        assert result is True

    def test_runs_lysosome_when_pressure_moderate(self, mock_paths, mock_vasomotor):
        """Should run lysosome when disk pressure is moderate."""
        import metabolon.pulse as pulse

        mock_lysosome_result = MagicMock(
            freed_gb=3.0,
            before_gb=10.0,
            after_gb=13.0,
        )
        # Mock the import inside the function
        with patch("metabolon.pulse.shutil.disk_usage") as mock_disk, \
             patch.dict("sys.modules", {"metabolon.enzymes.interoception": MagicMock(lysosome_digest=lambda: mock_lysosome_result)}):
            # 10GB free (below DISK_CLEAN_GB=15)
            mock_disk.return_value = MagicMock(free=10 * 1024**3)
            result = pulse.sense_disk_pressure()

        assert result is True

    def test_returns_false_if_disk_critical(self, mock_paths, mock_vasomotor):
        """Should return False if disk is critically low."""
        import metabolon.pulse as pulse

        mock_lysosome_result = MagicMock(
            freed_gb=0.5,
            before_gb=3.0,
            after_gb=3.5,
        )
        with patch("metabolon.pulse.shutil.disk_usage") as mock_disk, \
             patch.dict("sys.modules", {"metabolon.enzymes.interoception": MagicMock(lysosome_digest=lambda: mock_lysosome_result)}):
            # 3GB free (below DISK_FLOOR_GB=5)
            mock_disk.return_value = MagicMock(free=3 * 1024**3)
            result = pulse.sense_disk_pressure()

        assert result is False


# ---------------------------------------------------------------------------
# Systole Prompt Tests
# ---------------------------------------------------------------------------


class TestBuildSystolePrompt:
    def test_basic_prompt(self, mock_paths, mock_vasomotor):
        """Should build basic systole prompt."""
        import metabolon.pulse as pulse

        # Mock the template to use consistent variable names
        mock_template = "One heartbeat. Allocate ~{infra_pct}% of agents."
        with patch.object(pulse, "SYSTOLE_PROMPT_TEMPLATE", mock_template):
            genome = {"infra_pct": 30}
            prompt = pulse._build_systole_prompt(genome)

        assert "One heartbeat" in prompt
        assert "30%" in prompt

    def test_includes_focus_star(self, mock_paths, mock_vasomotor):
        """Should include focus star in prompt if provided."""
        import metabolon.pulse as pulse

        mock_template = "One heartbeat. Allocate ~{infra_pct}% of agents.{focus_line}"
        with patch.object(pulse, "SYSTOLE_PROMPT_TEMPLATE", mock_template):
            genome = {"infra_pct": 30, "focus_star": "North Star Alpha"}
            prompt = pulse._build_systole_prompt(genome)

        assert "North Star Alpha" in prompt

    def test_focus_parameter_overrides_genome(self, mock_paths, mock_vasomotor):
        """Should use focus parameter over genome focus_star."""
        import metabolon.pulse as pulse

        mock_template = "One heartbeat. Allocate ~{infra_pct}% of agents.{focus_line}"
        with patch.object(pulse, "SYSTOLE_PROMPT_TEMPLATE", mock_template):
            genome = {"infra_pct": 30}  # No focus_star in genome
            prompt = pulse._build_systole_prompt(genome, focus="Override Star")

        # The focus parameter becomes focus_star, so it appears in the focus_line
        assert "Override Star" in prompt
        assert "**FOCUS:**" in prompt


class TestIsovolumicContraction:
    def test_includes_directive_if_exists(self, mock_paths, mock_vasomotor):
        """Should include focus directive in prompt."""
        import metabolon.pulse as pulse

        mock_paths["focus_directive"].write_text("FOCUS: Test Star\nURGENT (2): item1; item2")
        genome = {"infra_pct": 30}
        context = {"coverage": {"Star A": 5, "Star B": 10}}

        mock_template = "One heartbeat. Allocate ~{infra_pct}% of agents.{focus_line}"
        with patch.object(pulse, "SYSTOLE_PROMPT_TEMPLATE", mock_template):
            prompt = pulse.isovolumic_contraction(genome, None, context)

        assert "PRE-COMPUTED DIRECTIVES" in prompt
        assert "Test Star" in prompt

    def test_includes_coverage_map(self, mock_paths, mock_vasomotor):
        """Should include coverage map in prompt."""
        import metabolon.pulse as pulse

        genome = {"infra_pct": 30}
        context = {"coverage": {"Star A": 5, "Star B": 10}}

        mock_template = "One heartbeat. Allocate ~{infra_pct}% of agents.{focus_line}"
        with patch.object(pulse, "SYSTOLE_PROMPT_TEMPLATE", mock_template):
            prompt = pulse.isovolumic_contraction(genome, None, context)

        assert "NORTH STAR COVERAGE" in prompt
        assert "Star A" in prompt

    def test_includes_completed_topics(self, mock_paths, mock_vasomotor):
        """Should include completed topics in prompt."""
        import metabolon.pulse as pulse

        mock_paths["topic_lock"].write_text("topic1\ntopic2")
        genome = {"infra_pct": 30}
        context = {}

        mock_template = "One heartbeat. Allocate ~{infra_pct}% of agents.{focus_line}"
        with patch.object(pulse, "SYSTOLE_PROMPT_TEMPLATE", mock_template):
            prompt = pulse.isovolumic_contraction(genome, None, context)

        assert "COMPLETED TOPICS" in prompt
        assert "DO NOT REDO" in prompt


# ---------------------------------------------------------------------------
# Atrial Systole Tests
# ---------------------------------------------------------------------------


class TestAtrialSystole:
    def test_returns_context_dict(self, mock_paths, mock_vasomotor):
        """Should return context dictionary."""
        import metabolon.pulse as pulse

        with patch("metabolon.perfusion.perfusion_report") as mock_perf:
            mock_perf.return_value = {
                "focus_star": "Star Alpha",
                "coverage": {"Star Alpha": 3, "Star Beta": 8},
                "ischaemic": [],
            }
            context = pulse.atrial_systole()

        assert "focus_star" in context
        assert context["focus_star"] == "Star Alpha"

    def test_writes_focus_directive(self, mock_paths, mock_vasomotor):
        """Should write focus directive file."""
        import metabolon.pulse as pulse

        with patch("metabolon.perfusion.perfusion_report") as mock_perf:
            mock_perf.return_value = {
                "focus_star": "Star Alpha",
                "coverage": {},
                "ischaemic": [],
            }
            pulse.atrial_systole()

        directive = mock_paths["focus_directive"].read_text()
        assert "Star Alpha" in directive

    def test_scans_praxis_for_urgent_items(self, mock_paths, mock_vasomotor):
        """Should scan Praxis for urgent items with near dates."""
        import metabolon.pulse as pulse
        from datetime import date, timedelta

        tomorrow = date.today() + timedelta(days=1)
        praxis_content = f"""
- TODO: Task 1 due {tomorrow.isoformat()} #agent:terry
- TODO: Task 2 due 2026-06-01 #agent:terry
"""
        mock_paths["praxis"].write_text(praxis_content)

        with patch("metabolon.perfusion.perfusion_report") as mock_perf:
            mock_perf.return_value = {
                "focus_star": None,
                "coverage": {},
                "ischaemic": [],
            }
            context = pulse.atrial_systole()

        assert len(context.get("urgent", [])) > 0


# ---------------------------------------------------------------------------
# Diastole Tests
# ---------------------------------------------------------------------------


class TestDiastole:
    def test_compacts_cardiac_log(self, mock_paths, mock_vasomotor):
        """Should compact cardiac log during diastole."""
        import metabolon.pulse as pulse

        # Create a large log
        lines = ["# Pulse Manifest", "", "## Completed"] + [f"  - Item {i}" for i in range(150)]
        mock_paths["cardiac_log"].write_text("\n".join(lines))

        with patch("metabolon.respiration.auto_convert") as mock_convert, \
             patch("metabolon.respiration.phantom_sweep") as mock_phantom:
            mock_convert.return_value = {"converted": 0}
            mock_phantom.return_value = {"phantom_count": 0}
            pulse.diastole(1)

        # Log should be compacted
        assert len(mock_paths["cardiac_log"].read_text().splitlines()) <= 100

    def test_extracts_topics_from_manifest(self, mock_paths, mock_vasomotor):
        """Should extract completed topics from manifest."""
        import metabolon.pulse as pulse

        manifest = """# Pulse Manifest

## Completed
- [x] **GARP M3 Cards** - completed
- [x] **HSBC Stakeholder Map** - done
"""
        mock_paths["cardiac_log"].write_text(manifest)

        with patch("metabolon.respiration.auto_convert") as mock_convert, \
             patch("metabolon.respiration.phantom_sweep") as mock_phantom:
            mock_convert.return_value = {"converted": 0}
            mock_phantom.return_value = {"phantom_count": 0}
            pulse.diastole(1)

        topics = mock_paths["topic_lock"].read_text()
        assert "garp-m3-cards" in topics.lower()

    def test_auto_converts_confirmation_items(self, mock_paths, mock_vasomotor):
        """Should auto-convert confirmation items during diastole."""
        import metabolon.pulse as pulse

        mock_paths["cardiac_log"].write_text("# Pulse Manifest\n")

        with patch("metabolon.respiration.auto_convert") as mock_convert, \
             patch("metabolon.respiration.phantom_sweep") as mock_phantom:
            mock_convert.return_value = {"converted": 5}
            mock_phantom.return_value = {"phantom_count": 0}
            pulse.diastole(1)

        mock_convert.assert_called_once()
        mock_vasomotor["record"].assert_called()


# ---------------------------------------------------------------------------
# Recent Secretions Tests
# ---------------------------------------------------------------------------


class TestCountRecentSecretions:
    def test_counts_new_files(self, mock_paths, tmp_path):
        """Should count files created after the given timestamp."""
        import metabolon.pulse as pulse
        import time

        # Create some files
        dir1 = tmp_path / "secretions"
        dir1.mkdir()
        (dir1 / "file1.txt").write_text("content")
        (dir1 / "file2.txt").write_text("content")

        count = pulse._count_recent_secretions([dir1], time.time() - 10)
        assert count == 2

    def test_ignores_old_files(self, mock_paths, tmp_path):
        """Should ignore files created before the timestamp."""
        import metabolon.pulse as pulse
        import time

        dir1 = tmp_path / "secretions"
        dir1.mkdir()
        (dir1 / "old_file.txt").write_text("content")

        # Use future timestamp
        count = pulse._count_recent_secretions([dir1], time.time() + 100)
        assert count == 0

    def test_handles_missing_directory(self, mock_paths, tmp_path):
        """Should handle missing directories gracefully."""
        import metabolon.pulse as pulse

        missing = tmp_path / "does_not_exist"
        count = pulse._count_recent_secretions([missing], 0)
        assert count == 0


# ---------------------------------------------------------------------------
# Fire Systole Tests
# ---------------------------------------------------------------------------


class TestFireSystole:
    def test_returns_success_on_zero_exit(self, mock_paths, mock_vasomotor):
        """Should return (True, tail) on successful exit."""
        import metabolon.pulse as pulse
        import time

        mock_paths["log_dir"].mkdir(parents=True)
        log_file = mock_paths["log_dir"] / "pulse-systoles.log"
        log_file.write_text("test output")

        # Use a side effect to make poll return 0 after first call
        poll_count = [0]
        def poll_side_effect():
            poll_count[0] += 1
            if poll_count[0] > 1:
                return 0  # Process completed
            return None  # Still running

        with patch("metabolon.pulse.subprocess.Popen") as mock_popen, \
             patch("metabolon.pulse.time.sleep"):
            mock_proc = MagicMock()
            mock_proc.poll.side_effect = poll_side_effect
            mock_proc.pid = 12345
            mock_popen.return_value = mock_proc

            success, tail = pulse.fire_systole(1, "sonnet", prompt="test prompt")

        assert success is True

    def test_returns_failure_on_nonzero_exit(self, mock_paths, mock_vasomotor):
        """Should return (False, tail) on non-zero exit."""
        import metabolon.pulse as pulse

        mock_paths["log_dir"].mkdir(parents=True)
        log_file = mock_paths["log_dir"] / "pulse-systoles.log"
        log_file.write_text("error output")

        poll_count = [0]
        def poll_side_effect():
            poll_count[0] += 1
            if poll_count[0] > 1:
                return 1  # Process failed
            return None

        with patch("metabolon.pulse.subprocess.Popen") as mock_popen, \
             patch("metabolon.pulse.time.sleep"):
            mock_proc = MagicMock()
            mock_proc.poll.side_effect = poll_side_effect
            mock_proc.pid = 12345
            mock_popen.return_value = mock_proc

            success, tail = pulse.fire_systole(1, "sonnet", prompt="test prompt")

        assert success is False

    def test_uses_provided_prompt(self, mock_paths, mock_vasomotor):
        """Should use provided prompt instead of building one."""
        import metabolon.pulse as pulse

        mock_paths["log_dir"].mkdir(parents=True)
        log_file = mock_paths["log_dir"] / "pulse-systoles.log"
        log_file.write_text("output")

        poll_count = [0]
        def poll_side_effect():
            poll_count[0] += 1
            if poll_count[0] > 1:
                return 0
            return None

        with patch("metabolon.pulse.subprocess.Popen") as mock_popen, \
             patch("metabolon.pulse.subprocess.run") as mock_run, \
             patch("metabolon.pulse.time.sleep"):
            mock_proc = MagicMock()
            mock_proc.poll.side_effect = poll_side_effect
            mock_proc.pid = 12345
            mock_popen.return_value = mock_proc
            mock_run.return_value = MagicMock(stdout="00:01:00")

            pulse.fire_systole(1, "sonnet", prompt="Custom prompt")

            # Check that the prompt was passed to Popen (first call)
            call_args = mock_popen.call_args_list[0][0][0]
            # The command should include "Custom prompt" as the last argument
            assert call_args[-1] == "Custom prompt"


# ---------------------------------------------------------------------------
# Vital Signs Tests
# ---------------------------------------------------------------------------


class TestRecordVitalSigns:
    def test_creates_report_file(self, mock_paths, mock_vasomotor):
        """Should create pulse report file."""
        import metabolon.pulse as pulse

        pulse.record_vital_signs(3, "completed")

        # Check that a report was created
        reports = list(mock_paths["report_dir"].glob("*.md"))
        assert len(reports) == 1

        content = reports[0].read_text()
        assert "3 systoles" in content.lower() or "Systoles completed: 3" in content
        assert "completed" in content.lower()

    def test_includes_manifest_content(self, mock_paths, mock_vasomotor):
        """Should include manifest content in report."""
        import metabolon.pulse as pulse

        mock_paths["cardiac_log"].write_text("# Test Manifest\n\nContent here")
        pulse.record_vital_signs(1, "test")

        reports = list(mock_paths["report_dir"].glob("*.md"))
        content = reports[0].read_text()
        assert "Test Manifest" in content


class TestCrossModelReview:
    def test_dispatches_review_process(self, mock_paths, mock_vasomotor):
        """Should dispatch cross-model review in background."""
        import metabolon.pulse as pulse

        with patch("metabolon.pulse.subprocess.Popen") as mock_popen:
            pulse.cross_model_review(mock_paths["cardiac_log"])

        mock_popen.assert_called_once()

    def test_handles_missing_pulse_review(self, mock_paths, mock_vasomotor):
        """Should handle missing pulse-review command gracefully."""
        import metabolon.pulse as pulse

        with patch("metabolon.pulse.subprocess.Popen") as mock_popen:
            mock_popen.side_effect = FileNotFoundError()
            # Should not raise
            pulse.cross_model_review(mock_paths["cardiac_log"])


class TestPostEfferensSummary:
    def test_posts_to_acta(self, mock_paths, mock_vasomotor):
        """Should post summary to ACTA."""
        import metabolon.pulse as pulse

        with patch("acta.post") as mock_post:
            pulse.post_efferens_summary(3, "completed")

        mock_post.assert_called_once()

    def test_handles_acta_error(self, mock_paths, mock_vasomotor):
        """Should handle ACTA errors gracefully."""
        import metabolon.pulse as pulse

        with patch("acta.post") as mock_post:
            mock_post.side_effect = Exception("ACTA error")
            # Should not raise
            pulse.post_efferens_summary(3, "completed")


# ---------------------------------------------------------------------------
# Autophagy Tests
# ---------------------------------------------------------------------------


class TestAutophagy:
    def test_records_vital_signs(self, mock_paths, mock_vasomotor):
        """Should record vital signs during autophagy."""
        import metabolon.pulse as pulse

        with patch("metabolon.pulse.post_efferens_summary"), \
             patch("metabolon.pulse._auto_commit_germline"), \
             patch("metabolon.pulse.cross_model_review"):
            pulse.autophagy(3, "completed")

        reports = list(mock_paths["report_dir"].glob("*.md"))
        assert len(reports) == 1

    def test_archives_manifest(self, mock_paths, mock_vasomotor):
        """Should archive manifest during autophagy."""
        import metabolon.pulse as pulse

        mock_paths["cardiac_log"].write_text("# Manifest content")

        with patch("metabolon.pulse.post_efferens_summary"), \
             patch("metabolon.pulse._auto_commit_germline"), \
             patch("metabolon.pulse.cross_model_review"):
            pulse.autophagy(1, "test")

        # Original manifest should be renamed (archived)
        assert not mock_paths["cardiac_log"].exists()
        # Archive should exist
        archives = list(mock_paths["cardiac_log"].parent.glob("pulse-*.md"))
        assert len(archives) == 1


class TestAutoCommitGermline:
    def test_commits_dirty_files(self, mock_paths, mock_vasomotor, tmp_path):
        """Should commit dirty files in germline."""
        import metabolon.pulse as pulse

        with patch("metabolon.pulse.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="M loci/pulse/file.md")

            with patch("metabolon.pulse.Path.home", return_value=tmp_path):
                pulse._auto_commit_germline()

        # Should have called git add and git commit
        assert mock_run.call_count >= 2

    def test_skips_clean_repo(self, mock_paths, mock_vasomotor, tmp_path):
        """Should skip commit if repo is clean."""
        import metabolon.pulse as pulse

        with patch("metabolon.pulse.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="")

            with patch("metabolon.pulse.Path.home", return_value=tmp_path):
                pulse._auto_commit_germline()

        # Should only check status
        assert mock_run.call_count == 1


# ---------------------------------------------------------------------------
# Event Log Rotation Tests
# ---------------------------------------------------------------------------


class TestCycleEventLog:
    def test_rotates_large_log(self, mock_paths, mock_vasomotor, tmp_path):
        """Should rotate log file if over 1MB."""
        import metabolon.pulse as pulse

        event_log = tmp_path / "events.jsonl"
        # Write > 1MB of data
        event_log.write_text("x" * 1_100_000)

        with patch("metabolon.pulse.EVENT_LOG", event_log), \
             patch("metabolon.pulse.log"):
            pulse.cycle_event_log()

        # Original should be renamed
        assert not event_log.exists()
        assert event_log.with_suffix(".jsonl.1").exists()

    def test_skips_small_log(self, mock_paths, mock_vasomotor, tmp_path):
        """Should not rotate log if under 1MB."""
        import metabolon.pulse as pulse

        event_log = tmp_path / "events.jsonl"
        event_log.write_text("small content")

        with patch("metabolon.pulse.EVENT_LOG", event_log):
            pulse.cycle_event_log()

        # Original should still exist
        assert event_log.exists()

    def test_handles_missing_log(self, mock_paths, mock_vasomotor, tmp_path):
        """Should handle missing event log gracefully."""
        import metabolon.pulse as pulse

        event_log = tmp_path / "nonexistent.jsonl"

        with patch("metabolon.pulse.EVENT_LOG", event_log):
            # Should not raise
            pulse.cycle_event_log()


# ---------------------------------------------------------------------------
# Entrainment Tests
# ---------------------------------------------------------------------------


class TestCheckEntrainment:
    def test_returns_false_on_normal_action(self, mock_paths, mock_vasomotor):
        """Should return (False, 'normal') for normal action."""
        import metabolon.pulse as pulse

        with patch("metabolon.organelles.entrainment.zeitgebers") as mock_zeitgebers, \
             patch("metabolon.organelles.entrainment.optimal_schedule") as mock_schedule:
            mock_zeitgebers.return_value = {"hkt_hour": 10}
            mock_schedule.return_value = {
                "recommendations": {"pulse": {"action": "normal", "reason": "nominal"}}
            }

            suppress, reason = pulse._check_entrainment()

        assert suppress is False
        assert reason == "normal"

    def test_returns_true_on_suppress_action(self, mock_paths, mock_vasomotor, tmp_path):
        """Should return (True, reason) for suppress action."""
        import metabolon.pulse as pulse

        skip_file = tmp_path / "skip-until"

        with patch("metabolon.organelles.entrainment.zeitgebers") as mock_zeitgebers, \
             patch("metabolon.organelles.entrainment.optimal_schedule") as mock_schedule, \
             patch("metabolon.vasomotor.SKIP_UNTIL_FILE", skip_file):
            mock_zeitgebers.return_value = {"hkt_hour": 3}
            mock_schedule.return_value = {
                "recommendations": {"pulse": {"action": "suppress", "reason": "night_hours"}}
            }

            suppress, reason = pulse._check_entrainment()

        assert suppress is True
        assert "suppress" in reason
        # Should write skip-until file
        assert skip_file.exists()

    def test_returns_false_on_exception(self, mock_paths, mock_vasomotor):
        """Should return (False, 'entrainment_unavailable') on exception."""
        import metabolon.pulse as pulse

        with patch("metabolon.organelles.entrainment.zeitgebers") as mock_zeitgebers:
            mock_zeitgebers.side_effect = Exception("test error")

            suppress, reason = pulse._check_entrainment()

        assert suppress is False
        assert reason == "entrainment_unavailable"


# ---------------------------------------------------------------------------
# Main Loop Tests
# ---------------------------------------------------------------------------


class TestMain:
    def test_skips_if_apneic(self, mock_paths, mock_vasomotor):
        """Should skip if respiration indicates apnea."""
        import metabolon.pulse as pulse

        mock_vasomotor["apneic"].return_value = (True, "skip-until")

        pulse.main(dry_run=True)

        mock_vasomotor["log"].assert_called()

    def test_skips_if_entrainment_suppresses(self, mock_paths, mock_vasomotor):
        """Should skip if entrainment suppresses."""
        import metabolon.pulse as pulse

        with patch("metabolon.pulse._check_entrainment") as mock_ent:
            mock_ent.return_value = (True, "night_hours")

            pulse.main(dry_run=True)

        mock_vasomotor["log"].assert_called()

    def test_skips_if_no_headroom(self, mock_paths, mock_vasomotor):
        """Should skip if no budget headroom."""
        import metabolon.pulse as pulse

        mock_vasomotor["capacity"].return_value = (False, "budget exhausted")

        with patch("metabolon.pulse._check_entrainment") as mock_ent:
            mock_ent.return_value = (False, "normal")

            pulse.main(dry_run=True)

        mock_vasomotor["log"].assert_called()

    def test_runs_systoles_when_healthy(self, mock_paths, mock_vasomotor):
        """Should run systoles when all checks pass."""
        import metabolon.pulse as pulse

        mock_paths["log_dir"].mkdir(parents=True)

        with patch("metabolon.pulse._check_entrainment") as mock_ent, \
             patch("metabolon.pulse.atrial_systole") as mock_atrial, \
             patch("metabolon.pulse.isovolumic_contraction") as mock_iso, \
             patch("metabolon.pulse.fire_systole") as mock_fire, \
             patch("metabolon.pulse.sense_disk_pressure", return_value=True), \
             patch("metabolon.pulse.autophagy"), \
             patch("metabolon.pulse.diastole"):

            mock_ent.return_value = (False, "normal")
            mock_atrial.return_value = {"coverage": {}}
            mock_iso.return_value = "test prompt"
            mock_fire.return_value = (True, "")
            mock_vasomotor["status"].return_value = "green"

            pulse.main(systoles=1, dry_run=True)

        mock_vasomotor["record"].assert_called()

    def test_stops_on_budget_yellow(self, mock_paths, mock_vasomotor):
        """Should stop if budget status is yellow."""
        import metabolon.pulse as pulse

        mock_vasomotor["status"].return_value = "yellow"

        with patch("metabolon.pulse._check_entrainment") as mock_ent, \
             patch("metabolon.pulse.sense_disk_pressure", return_value=True), \
             patch("metabolon.pulse.autophagy"):

            mock_ent.return_value = (False, "normal")

            pulse.main(systoles=3, dry_run=True)

        # Should have recorded budget_stop
        calls = [str(c) for c in mock_vasomotor["record"].call_args_list]
        assert any("budget_stop" in str(c) for c in calls)

    def test_stops_on_circuit_breaker(self, mock_paths, mock_vasomotor):
        """Should stop after 3 consecutive failures."""
        import metabolon.pulse as pulse

        mock_paths["log_dir"].mkdir(parents=True)

        with patch("metabolon.pulse._check_entrainment") as mock_ent, \
             patch("metabolon.pulse.atrial_systole") as mock_atrial, \
             patch("metabolon.pulse.isovolumic_contraction") as mock_iso, \
             patch("metabolon.pulse.fire_systole") as mock_fire, \
             patch("metabolon.pulse.sense_disk_pressure", return_value=True), \
             patch("metabolon.pulse.autophagy"):

            mock_ent.return_value = (False, "normal")
            mock_atrial.return_value = {"coverage": {}}
            mock_iso.return_value = "test prompt"
            mock_fire.return_value = (False, "")  # Always fail
            mock_vasomotor["status"].return_value = "green"

            pulse.main(systoles=10, dry_run=False)

        # Should have recorded circuit_breaker
        calls = [str(c) for c in mock_vasomotor["record"].call_args_list]
        assert any("circuit_breaker" in str(c) for c in calls)

    def test_detects_saturation(self, mock_paths, mock_vasomotor):
        """Should detect saturation signals in output."""
        import metabolon.pulse as pulse

        mock_paths["log_dir"].mkdir(parents=True)

        with patch("metabolon.pulse._check_entrainment") as mock_ent, \
             patch("metabolon.pulse.atrial_systole") as mock_atrial, \
             patch("metabolon.pulse.isovolumic_contraction") as mock_iso, \
             patch("metabolon.pulse.fire_systole") as mock_fire, \
             patch("metabolon.pulse.sense_disk_pressure", return_value=True), \
             patch("metabolon.pulse.autophagy"), \
             patch("metabolon.pulse.diastole"):

            mock_ent.return_value = (False, "normal")
            mock_atrial.return_value = {"coverage": {}}
            mock_iso.return_value = "test prompt"
            mock_fire.return_value = (True, "No new work to do. All items covered.")
            mock_vasomotor["status"].return_value = "green"

            pulse.main(systoles=3, dry_run=False)

        # Should have recorded saturation
        calls = [str(c) for c in mock_vasomotor["record"].call_args_list]
        assert any("saturation" in str(c).lower() for c in calls)

    def test_respects_stop_after_deadline(self, mock_paths, mock_vasomotor):
        """Should respect stop-after deadline."""
        import metabolon.pulse as pulse

        mock_paths["log_dir"].mkdir(parents=True)

        # Set a deadline in the past
        past_time = (datetime.datetime.now() - datetime.timedelta(hours=1)).strftime("%H:%M")

        with patch("metabolon.pulse._check_entrainment") as mock_ent, \
             patch("metabolon.pulse.sense_disk_pressure", return_value=True), \
             patch("metabolon.pulse.autophagy"):

            mock_ent.return_value = (False, "normal")
            mock_vasomotor["status"].return_value = "green"

            pulse.main(systoles=5, stop_after=past_time, dry_run=True)

        # Should have recorded deadline_reached
        calls = [str(c) for c in mock_vasomotor["record"].call_args_list]
        assert any("deadline" in str(c) for c in calls)


class TestAdaptiveCadence:
    def test_uses_provided_systole_count(self, mock_paths, mock_vasomotor):
        """Should use provided systole count directly."""
        import metabolon.pulse as pulse

        with patch("metabolon.pulse._check_entrainment") as mock_ent, \
             patch("metabolon.pulse.sense_disk_pressure", return_value=True), \
             patch("metabolon.pulse.autophagy"):

            mock_ent.return_value = (False, "normal")
            mock_vasomotor["capacity"].return_value = (True, "plenty")
            mock_vasomotor["status"].return_value = "green"

            pulse.main(systoles=7, dry_run=True)

        # Check that systoles=7 was used
        calls = [str(c) for c in mock_vasomotor["record"].call_args_list]
        assert any("7" in str(c) or "max_systoles" in str(c) for c in calls)

    def test_calculates_budget_driven_systoles(self, mock_paths, mock_vasomotor):
        """Should calculate systoles based on budget."""
        import metabolon.pulse as pulse

        mock_vasomotor["telemetry"].return_value = {
            "seven_day": {"utilization": 30}  # Low usage = more budget
        }
        mock_vasomotor["cost"].return_value = 5.0

        with patch("metabolon.pulse._check_entrainment") as mock_ent, \
             patch("metabolon.pulse.sense_disk_pressure", return_value=True), \
             patch("metabolon.pulse.autophagy"):

            mock_ent.return_value = (False, "normal")
            mock_vasomotor["capacity"].return_value = (True, "plenty")
            mock_vasomotor["status"].return_value = "green"

            pulse.main(dry_run=True)

        mock_vasomotor["telemetry"].assert_called()
