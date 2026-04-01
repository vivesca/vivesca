from __future__ import annotations

"""Tests for metabolon.organelles.inflammasome."""

import json
import os
import subprocess
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import metabolon.organelles.inflammasome as mod


# ---------------------------------------------------------------------------
# probe_chromatin
# ---------------------------------------------------------------------------

class TestProbeChromatin:
    @patch.dict("sys.modules", {})
    def test_storage_none_returns_false(self):
        with patch("metabolon.organelles.inflammasome.chromatin", create=True) as m_chrom:
            # Simulate: from ...chromatin import _get_storage, recall
            # We patch the import inside the function
            pass
        # The function uses lazy imports, so we mock at the import level
        fake_chromatin = MagicMock()
        fake_chromatin._get_storage.return_value = None
        with patch.dict("sys.modules", {"metabolon.organelles.chromatin": fake_chromatin}):
            passed, msg = mod.probe_chromatin()
        assert passed is False
        assert "None" in msg

    def test_storage_returns_non_list(self):
        fake_chromatin = MagicMock()
        fake_chromatin._get_storage.return_value = MagicMock()
        fake_chromatin.recall.return_value = "not_a_list"
        with patch.dict("sys.modules", {"metabolon.organelles.chromatin": fake_chromatin}):
            passed, msg = mod.probe_chromatin()
        assert passed is False
        assert "str" in msg

    def test_storage_returns_list_success(self):
        fake_chromatin = MagicMock()
        fake_chromatin._get_storage.return_value = MagicMock()
        fake_chromatin.recall.return_value = [{"id": 1}]
        with patch.dict("sys.modules", {"metabolon.organelles.chromatin": fake_chromatin}):
            passed, msg = mod.probe_chromatin()
        assert passed is True
        assert "1 result" in msg

    def test_storage_returns_empty_list_success(self):
        fake_chromatin = MagicMock()
        fake_chromatin._get_storage.return_value = MagicMock()
        fake_chromatin.recall.return_value = []
        with patch.dict("sys.modules", {"metabolon.organelles.chromatin": fake_chromatin}):
            passed, msg = mod.probe_chromatin()
        assert passed is True
        assert "0 result" in msg

    def test_import_error_returns_false(self):
        with patch.dict("sys.modules", {"metabolon.organelles.chromatin": None}):
            passed, msg = mod.probe_chromatin()
        assert passed is False
        assert "exception" in msg


# ---------------------------------------------------------------------------
# probe_endocytosis
# ---------------------------------------------------------------------------

class TestProbeEndocytosis:
    @patch("metabolon.organelles.inflammasome.Path")
    def test_sources_not_found(self, mock_path_cls):
        mock_path = MagicMock()
        mock_path.__truediv__ = MagicMock(return_value=mock_path)
        mock_path_cls.home.return_value = mock_path
        sources = MagicMock()
        mock_path.__truediv__.return_value = sources
        # Chain: Path.home() / ".config" / "endocytosis" / "sources.yaml"
        step1 = MagicMock()
        step2 = MagicMock()
        sources_yaml = MagicMock()
        sources_yaml.exists.return_value = False
        mock_path.__truediv__.side_effect = [step1, step2, sources_yaml]
        # This is complex with chaining; use a simpler approach
        pass

    def test_sources_not_found_simple(self):
        target = Path("/nonexistent_test_inflammasome_12345")
        with patch.object(mod.Path, "home", return_value=target):
            passed, msg = mod.probe_endocytosis()
        assert passed is False
        assert "not found" in msg

    @patch("yaml.safe_load")
    def test_sources_empty_yaml(self, mock_safe_load):
        mock_safe_load.return_value = {}
        tmp = Path("/tmp/test_inflammasome_sources")
        sources_path = tmp / ".config" / "endocytosis" / "sources.yaml"
        sources_path.parent.mkdir(parents=True, exist_ok=True)
        sources_path.write_text("{}")
        try:
            with patch.object(mod.Path, "home", return_value=tmp):
                passed, msg = mod.probe_endocytosis()
            assert passed is False
            assert "0 sources" in msg
        finally:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)

    @patch("yaml.safe_load")
    def test_sources_with_entries(self, mock_safe_load):
        mock_safe_load.return_value = {"feeds": [{"url": "http://example.com"}]}
        tmp = Path("/tmp/test_inflammasome_sources2")
        sources_path = tmp / ".config" / "endocytosis" / "sources.yaml"
        sources_path.parent.mkdir(parents=True, exist_ok=True)
        sources_path.write_text("feeds:\n  - url: http://example.com")
        try:
            with patch.object(mod.Path, "home", return_value=tmp):
                passed, msg = mod.probe_endocytosis()
            assert passed is True
            assert "1 source" in msg
        finally:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)

    def test_dangling_symlink(self):
        tmp = Path("/tmp/test_inflammasome_dangling")
        sources_path = tmp / ".config" / "endocytosis" / "sources.yaml"
        sources_path.parent.mkdir(parents=True, exist_ok=True)
        dangling = tmp / ".config" / "endocytosis" / "nonexistent_target"
        sources_path.symlink_to(dangling)
        try:
            with patch.object(mod.Path, "home", return_value=tmp):
                passed, msg = mod.probe_endocytosis()
            assert passed is False
            assert "dangling" in msg.lower() or "not found" in msg.lower()
        finally:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------------------
# probe_rheotaxis
# ---------------------------------------------------------------------------

class TestProbeRheotaxis:
    @patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test-key-12345"})
    def test_key_set(self):
        passed, msg = mod.probe_rheotaxis()
        assert passed is True
        assert "14 chars" in msg

    @patch.dict(os.environ, {}, clear=True)
    def test_key_not_set(self):
        # Remove if inherited
        os.environ.pop("PERPLEXITY_API_KEY", None)
        passed, msg = mod.probe_rheotaxis()
        assert passed is False
        assert "not set" in msg

    @patch.dict(os.environ, {"PERPLEXITY_API_KEY": ""})
    def test_key_empty(self):
        passed, msg = mod.probe_rheotaxis()
        assert passed is False
        assert "not set" in msg


# ---------------------------------------------------------------------------
# probe_rheotaxis_self_test
# ---------------------------------------------------------------------------

class TestProbeRheotaxisSelfTest:
    @patch("shutil.which", return_value=None)
    def test_binary_not_found(self, mock_which):
        passed, msg = mod.probe_rheotaxis_self_test()
        assert passed is False
        assert "not found" in msg

    @patch("metabolon.organelles.inflammasome.subprocess")
    @patch("shutil.which", return_value="/usr/local/bin/rheotaxis")
    def test_nonzero_exit(self, mock_which, mock_subprocess):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "some error"
        mock_subprocess.run.return_value = mock_result
        mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired
        passed, msg = mod.probe_rheotaxis_self_test()
        assert passed is False
        assert "exited 1" in msg

    @patch("metabolon.organelles.inflammasome.subprocess")
    @patch("shutil.which", return_value="/usr/local/bin/rheotaxis")
    def test_empty_stdout(self, mock_which, mock_subprocess):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "  "
        mock_result.stderr = ""
        mock_subprocess.run.return_value = mock_result
        mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired
        passed, msg = mod.probe_rheotaxis_self_test()
        assert passed is False
        assert "empty output" in msg

    @patch("metabolon.organelles.inflammasome.subprocess")
    @patch("shutil.which", return_value="/usr/local/bin/rheotaxis")
    def test_success(self, mock_which, mock_subprocess):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"status": "ok"}'
        mock_result.stderr = ""
        mock_subprocess.run.return_value = mock_result
        mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired
        passed, msg = mod.probe_rheotaxis_self_test()
        assert passed is True
        assert "ok" in msg

    @patch("metabolon.organelles.inflammasome.subprocess")
    @patch("shutil.which", return_value="/usr/local/bin/rheotaxis")
    def test_timeout(self, mock_which, mock_subprocess):
        mock_subprocess.run.side_effect = subprocess.TimeoutExpired(cmd="rheotaxis", timeout=15)
        mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired
        passed, msg = mod.probe_rheotaxis_self_test()
        assert passed is False
        assert "timed out" in msg


# ---------------------------------------------------------------------------
# probe_vasomotor_conf
# ---------------------------------------------------------------------------

class TestProbeVasomotorConf:
    def test_conf_file_not_found(self):
        fake_vasomotor = MagicMock()
        fake_vasomotor.CONF_PATH = Path("/nonexistent_conf_12345.json")
        with patch.dict("sys.modules", {"metabolon.vasomotor": fake_vasomotor}):
            passed, msg = mod.probe_vasomotor_conf()
        assert passed is False
        assert "not found" in msg

    def test_conf_empty_dict(self, tmp_path):
        conf_path = tmp_path / "respiration.conf"
        conf_path.write_text("{}")
        fake_vasomotor = MagicMock()
        fake_vasomotor.CONF_PATH = conf_path
        with patch.dict("sys.modules", {"metabolon.vasomotor": fake_vasomotor}):
            passed, msg = mod.probe_vasomotor_conf()
        assert passed is False
        assert "empty" in msg

    def test_conf_missing_keys(self, tmp_path):
        conf_path = tmp_path / "respiration.conf"
        conf_path.write_text(json.dumps({"aerobic_ceiling": 10}))
        fake_vasomotor = MagicMock()
        fake_vasomotor.CONF_PATH = conf_path
        with patch.dict("sys.modules", {"metabolon.vasomotor": fake_vasomotor}):
            passed, msg = mod.probe_vasomotor_conf()
        assert passed is False
        assert "missing expected keys" in msg

    def test_conf_valid(self, tmp_path):
        conf_path = tmp_path / "respiration.conf"
        conf_path.write_text(json.dumps({"aerobic_ceiling": 10, "systole_model": "linear"}))
        fake_vasomotor = MagicMock()
        fake_vasomotor.CONF_PATH = conf_path
        with patch.dict("sys.modules", {"metabolon.vasomotor": fake_vasomotor}):
            passed, msg = mod.probe_vasomotor_conf()
        assert passed is True
        assert "aerobic_ceiling=10" in msg
        assert "linear" in msg


# ---------------------------------------------------------------------------
# probe_respirometry
# ---------------------------------------------------------------------------

class TestProbeRespirometry:
    @patch("shutil.which", return_value=None)
    def test_binary_not_found(self, mock_which):
        passed, msg = mod.probe_respirometry()
        assert passed is False
        assert "not found" in msg

    @patch("metabolon.organelles.inflammasome.subprocess")
    @patch("shutil.which", return_value="/usr/local/bin/respirometry")
    def test_nonzero_exit(self, mock_which, mock_subprocess):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "error msg"
        mock_subprocess.run.return_value = mock_result
        mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired
        passed, msg = mod.probe_respirometry()
        assert passed is False
        assert "exited 1" in msg

    @patch("metabolon.organelles.inflammasome.subprocess")
    @patch("shutil.which", return_value="/usr/local/bin/respirometry")
    def test_invalid_json(self, mock_which, mock_subprocess):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "not json"
        mock_result.stderr = ""
        mock_subprocess.run.return_value = mock_result
        mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired
        passed, msg = mod.probe_respirometry()
        assert passed is False
        assert "invalid JSON" in msg

    @patch("metabolon.organelles.inflammasome.subprocess")
    @patch("shutil.which", return_value="/usr/local/bin/respirometry")
    def test_missing_seven_day_utilization(self, mock_which, mock_subprocess):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({"other": "data"})
        mock_result.stderr = ""
        mock_subprocess.run.return_value = mock_result
        mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired
        passed, msg = mod.probe_respirometry()
        assert passed is False
        assert "missing seven_day.utilization" in msg

    @patch("metabolon.organelles.inflammasome.subprocess")
    @patch("shutil.which", return_value="/usr/local/bin/respirometry")
    def test_success_with_stale_warning(self, mock_which, mock_subprocess):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(
            {"seven_day": {"utilization": 0.5}, "stale": True}
        )
        mock_result.stderr = ""
        mock_subprocess.run.return_value = mock_result
        mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired
        passed, msg = mod.probe_respirometry()
        assert passed is True
        assert "0.5" in msg
        assert "stale" in msg

    @patch("metabolon.organelles.inflammasome.subprocess")
    @patch("shutil.which", return_value="/usr/local/bin/respirometry")
    def test_success_fresh(self, mock_which, mock_subprocess):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(
            {"seven_day": {"utilization": 0.75}, "stale": False}
        )
        mock_result.stderr = ""
        mock_subprocess.run.return_value = mock_result
        mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired
        passed, msg = mod.probe_respirometry()
        assert passed is True
        assert "0.75" in msg
        assert "stale" not in msg

    @patch("metabolon.organelles.inflammasome.subprocess")
    @patch("shutil.which", return_value="/usr/local/bin/respirometry")
    def test_timeout(self, mock_which, mock_subprocess):
        mock_subprocess.run.side_effect = subprocess.TimeoutExpired(cmd="resp", timeout=10)
        mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired
        passed, msg = mod.probe_respirometry()
        assert passed is False
        assert "timed out" in msg


# ---------------------------------------------------------------------------
# probe_perfusion
# ---------------------------------------------------------------------------

class TestProbePerfusion:
    def test_empty_routable_stars(self):
        fake_perf = MagicMock()
        fake_perf._ROUTABLE_STARS = []
        with patch.dict("sys.modules", {"metabolon.perfusion": fake_perf}):
            passed, msg = mod.probe_perfusion()
        assert passed is False
        assert "empty" in msg

    def test_nonempty_routable_stars(self):
        fake_perf = MagicMock()
        fake_perf._ROUTABLE_STARS = ["star1", "star2"]
        with patch.dict("sys.modules", {"metabolon.perfusion": fake_perf}):
            passed, msg = mod.probe_perfusion()
        assert passed is True
        assert "2 star" in msg

    def test_import_error(self):
        with patch.dict("sys.modules", {"metabolon.perfusion": None}):
            passed, msg = mod.probe_perfusion()
        assert passed is False
        assert "exception" in msg


# ---------------------------------------------------------------------------
# probe_infection
# ---------------------------------------------------------------------------

class TestProbeInfection:
    def test_success_no_chronics(self):
        fake_infection = MagicMock()
        fake_infection.infection_summary.return_value = None
        fake_infection.recall_infections.return_value = []
        fake_infection.chronic_infections.return_value = []
        with patch.dict("sys.modules", {"metabolon.metabolism.infection": fake_infection}):
            passed, msg = mod.probe_infection()
        assert passed is True
        assert "0 event" in msg

    def test_success_with_events_and_chronics(self):
        fake_infection = MagicMock()
        fake_infection.infection_summary.return_value = None
        fake_infection.recall_infections.return_value = [MagicMock(), MagicMock()]
        fake_infection.chronic_infections.return_value = [
            {"fingerprint": "abc", "count": 3, "healed_count": 1},
        ]
        with patch.dict("sys.modules", {"metabolon.metabolism.infection": fake_infection}):
            passed, msg = mod.probe_infection()
        assert passed is True
        assert "2 event" in msg
        assert "1 chronic" in msg

    def test_chronic_with_zero_unhealed(self):
        fake_infection = MagicMock()
        fake_infection.infection_summary.return_value = None
        fake_infection.recall_infections.return_value = []
        fake_infection.chronic_infections.return_value = [
            {"fingerprint": "xyz", "count": 2, "healed_count": 2},
        ]
        with patch.dict("sys.modules", {"metabolon.metabolism.infection": fake_infection}):
            passed, msg = mod.probe_infection()
        assert passed is False
        assert "logic error" in msg

    def test_import_error(self):
        with patch.dict("sys.modules", {"metabolon.metabolism.infection": None}):
            passed, msg = mod.probe_infection()
        assert passed is False
        assert "exception" in msg


# ---------------------------------------------------------------------------
# probe_rss_state
# ---------------------------------------------------------------------------

class TestProbeRssState:
    def test_state_not_found(self):
        with patch.object(mod.Path, "home", return_value=Path("/nonexistent_rss_12345")):
            passed, msg = mod.probe_rss_state()
        assert passed is False
        assert "not found" in msg

    def test_state_stale(self, tmp_path):
        state_path = tmp_path / ".cache" / "endocytosis" / "state.json"
        state_path.parent.mkdir(parents=True)
        state_path.write_text("{}")
        # Set mtime to 50 hours ago
        old_time = time.time() - (50 * 3600)
        os.utime(state_path, (old_time, old_time))
        with patch.object(mod.Path, "home", return_value=tmp_path):
            passed, msg = mod.probe_rss_state()
        assert passed is False
        assert "stale" in msg

    def test_state_fresh(self, tmp_path):
        state_path = tmp_path / ".cache" / "endocytosis" / "state.json"
        state_path.parent.mkdir(parents=True)
        state_path.write_text("{}")
        with patch.object(mod.Path, "home", return_value=tmp_path):
            passed, msg = mod.probe_rss_state()
        assert passed is True
        assert "age" in msg


# ---------------------------------------------------------------------------
# probe_importin
# ---------------------------------------------------------------------------

class TestProbeImportin:
    def test_importin_not_found(self):
        fake_cytosol = MagicMock()
        fake_cytosol.VIVESCA_ROOT = Path("/nonexistent_vivesca_root_12345")
        with patch.dict("sys.modules", {"metabolon.cytosol": fake_cytosol}):
            passed, msg = mod.probe_importin()
        assert passed is False
        assert "not found" in msg

    def test_importin_exists_but_not_readable(self, tmp_path):
        effector = tmp_path / "effectors" / "importin"
        effector.parent.mkdir(parents=True)
        effector.write_text("#!/bin/bash\necho ok")
        fake_cytosol = MagicMock()
        fake_cytosol.VIVESCA_ROOT = tmp_path
        with patch.dict("sys.modules", {"metabolon.cytosol": fake_cytosol}):
            with patch("os.access", return_value=False):
                passed, msg = mod.probe_importin()
        assert passed is False
        assert "not readable" in msg

    def test_importin_found_and_readable(self, tmp_path):
        effector = tmp_path / "effectors" / "importin"
        effector.parent.mkdir(parents=True)
        effector.write_text("#!/bin/bash\necho ok")
        fake_cytosol = MagicMock()
        fake_cytosol.VIVESCA_ROOT = tmp_path
        with patch.dict("sys.modules", {"metabolon.cytosol": fake_cytosol}):
            passed, msg = mod.probe_importin()
        assert passed is True
        assert "found" in msg


# ---------------------------------------------------------------------------
# probe_mcp_server
# ---------------------------------------------------------------------------

class TestProbeMcpServer:
    @patch("metabolon.organelles.inflammasome.subprocess")
    def test_not_loaded(self, mock_subprocess):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = ""
        mock_subprocess.run.return_value = mock_result
        mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired
        passed, msg = mod.probe_mcp_server()
        assert passed is False
        assert "not loaded" in msg

    @patch("metabolon.organelles.inflammasome.subprocess")
    def test_loaded(self, mock_subprocess):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_subprocess.run.return_value = mock_result
        mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired
        passed, msg = mod.probe_mcp_server()
        assert passed is True
        assert "loaded" in msg

    @patch("metabolon.organelles.inflammasome.subprocess")
    def test_timeout(self, mock_subprocess):
        mock_subprocess.run.side_effect = subprocess.TimeoutExpired(cmd="launchctl", timeout=5)
        mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired
        passed, msg = mod.probe_mcp_server()
        assert passed is False
        assert "timed out" in msg


# ---------------------------------------------------------------------------
# _run_probe_with_timeout
# ---------------------------------------------------------------------------

class TestRunProbeWithTimeout:
    def test_fast_probe_returns_result(self):
        def good_probe():
            return True, "all good"
        passed, msg = mod._run_probe_with_timeout(good_probe)
        assert passed is True
        assert "all good" in msg

    def test_probe_that_raises(self):
        def bad_probe():
            raise RuntimeError("boom")
        passed, msg = mod._run_probe_with_timeout(bad_probe)
        assert passed is False
        assert "boom" in msg

    def test_probe_returns_nothing(self):
        """When a probe returns None (no return statement), _run_probe_with_timeout
        stores None in result_holder and returns it — callers get None, not a tuple.
        This is a known edge case; probes are contractually required to return tuples."""
        def empty_probe():
            pass
        result = mod._run_probe_with_timeout(empty_probe)
        assert result is None  # probe returned None, not a (bool, str) tuple


# ---------------------------------------------------------------------------
# run_all_probes
# ---------------------------------------------------------------------------

class TestRunAllProbes:
    @patch.object(mod, "_PROBES", [("test_probe", lambda: (True, "ok"))])
    def test_returns_expected_structure(self):
        results = mod.run_all_probes()
        assert len(results) == 1
        r = results[0]
        assert r["name"] == "test_probe"
        assert r["passed"] is True
        assert r["message"] == "ok"
        assert "duration_ms" in r

    @patch.object(mod, "_PROBES", [
        ("p1", lambda: (True, "ok")),
        ("p2", lambda: (False, "bad")),
    ])
    def test_mixed_results(self):
        results = mod.run_all_probes()
        assert len(results) == 2
        assert results[0]["passed"] is True
        assert results[1]["passed"] is False

    @patch.object(mod, "_PROBES", [("crash", lambda: (_ for _ in ()).throw(ValueError("ouch")))])
    def test_probe_exception_caught(self):
        # The probe raises; _run_probe_with_timeout catches it
        def crash_probe():
            raise ValueError("ouch")
        with patch.object(mod, "_PROBES", [("crash", crash_probe)]):
            results = mod.run_all_probes()
        assert len(results) == 1
        assert results[0]["passed"] is False


# ---------------------------------------------------------------------------
# probe_report
# ---------------------------------------------------------------------------

class TestProbeReport:
    @patch.object(mod, "run_all_probes")
    def test_report_format_pass(self, mock_run):
        mock_run.return_value = [
            {"name": "chromatin", "passed": True, "message": "ok", "duration_ms": 12},
        ]
        report = mod.probe_report()
        assert "[PASS] chromatin" in report
        assert "Summary: 1/1 passed" in report

    @patch.object(mod, "run_all_probes")
    def test_report_format_fail(self, mock_run):
        mock_run.return_value = [
            {"name": "rss_state", "passed": False, "message": "stale", "duration_ms": 1},
        ]
        report = mod.probe_report()
        assert "[FAIL] rss_state" in report
        assert "Summary: 0/1 passed" in report

    @patch.object(mod, "run_all_probes")
    def test_report_mixed(self, mock_run):
        mock_run.return_value = [
            {"name": "a", "passed": True, "message": "ok", "duration_ms": 5},
            {"name": "b", "passed": False, "message": "err", "duration_ms": 3},
            {"name": "c", "passed": True, "message": "ok", "duration_ms": 1},
        ]
        report = mod.probe_report()
        assert "Summary: 2/3 passed" in report


# ---------------------------------------------------------------------------
# is_primed
# ---------------------------------------------------------------------------

class TestIsPrimed:
    def test_first_failure_primes(self):
        priming = {}
        result = mod.is_primed("test", False, priming)
        assert result is False
        assert priming["test"] == 1

    def test_second_failure_activates(self):
        priming = {"test": 1}
        result = mod.is_primed("test", False, priming)
        assert result is True
        assert priming["test"] == 2

    def test_pass_resets_counter(self):
        priming = {"test": 5}
        result = mod.is_primed("test", True, priming)
        assert result is False
        assert "test" not in priming

    def test_pass_no_counter(self):
        priming = {}
        result = mod.is_primed("test", True, priming)
        assert result is False
        assert "test" not in priming


# ---------------------------------------------------------------------------
# check_pyroptosis
# ---------------------------------------------------------------------------

class TestCheckPyroptosis:
    def test_below_threshold(self):
        assert mod.check_pyroptosis("test", {"test": 2}) is False

    def test_at_threshold(self):
        assert mod.check_pyroptosis("test", {"test": 3}) is True

    def test_above_threshold(self):
        assert mod.check_pyroptosis("test", {"test": 10}) is True

    def test_no_entry(self):
        assert mod.check_pyroptosis("test", {}) is False


# ---------------------------------------------------------------------------
# _load_priming / _save_priming
# ---------------------------------------------------------------------------

class TestPrimingIO:
    def test_load_nonexistent(self, tmp_path):
        with patch.object(mod, "_PRIMING_PATH", tmp_path / "nope.json"):
            result = mod._load_priming()
        assert result == {}

    def test_load_valid(self, tmp_path):
        p = tmp_path / "priming.json"
        p.write_text(json.dumps({"a": 2}))
        with patch.object(mod, "_PRIMING_PATH", p):
            result = mod._load_priming()
        assert result == {"a": 2}

    def test_load_corrupt(self, tmp_path):
        p = tmp_path / "priming.json"
        p.write_text("not json!!!")
        with patch.object(mod, "_PRIMING_PATH", p):
            result = mod._load_priming()
        assert result == {}

    def test_save_creates_dirs(self, tmp_path):
        target = tmp_path / "deep" / "dir" / "priming.json"
        with patch.object(mod, "_PRIMING_PATH", target):
            mod._save_priming({"x": 1})
        assert target.exists()
        assert json.loads(target.read_text()) == {"x": 1}

    def test_save_fails_silently(self, tmp_path):
        # Use a path that can't be created (permission-denied-like)
        with patch.object(mod, "_PRIMING_PATH", Path("/proc/fake/no_write.json")):
            mod._save_priming({"x": 1})  # should not raise


# ---------------------------------------------------------------------------
# _repair_rss_stale
# ---------------------------------------------------------------------------

class TestRepairRssStale:
    @patch("shutil.which", return_value=None)
    def test_vivesca_not_found(self, mock_which):
        ok, msg = mod._repair_rss_stale()
        assert ok is False
        assert "not found" in msg

    @patch("metabolon.organelles.inflammasome.subprocess")
    @patch("shutil.which", return_value="/usr/local/bin/vivesca")
    def test_dispatch_success(self, mock_which, mock_subprocess):
        ok, msg = mod._repair_rss_stale()
        assert ok is True
        assert "dispatched" in msg
        mock_subprocess.Popen.assert_called_once()

    @patch("shutil.which", side_effect=RuntimeError("oops"))
    def test_exception(self, mock_which):
        ok, msg = mod._repair_rss_stale()
        assert ok is False
        assert "oops" in msg


# ---------------------------------------------------------------------------
# _repair_mcp_not_loaded
# ---------------------------------------------------------------------------

class TestRepairMcpNotLoaded:
    @patch("metabolon.organelles.inflammasome.subprocess")
    def test_success(self, mock_subprocess):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_subprocess.run.return_value = mock_result
        mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired
        ok, msg = mod._repair_mcp_not_loaded()
        assert ok is True
        assert "ok" in msg

    @patch("metabolon.organelles.inflammasome.subprocess")
    def test_load_fails(self, mock_subprocess):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "error"
        mock_subprocess.run.return_value = mock_result
        mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired
        ok, msg = mod._repair_mcp_not_loaded()
        assert ok is False
        assert "exited 1" in msg

    @patch("metabolon.organelles.inflammasome.subprocess")
    def test_timeout(self, mock_subprocess):
        mock_subprocess.run.side_effect = subprocess.TimeoutExpired(cmd="launchctl", timeout=10)
        mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired
        ok, msg = mod._repair_mcp_not_loaded()
        assert ok is False
        assert "timed out" in msg


# ---------------------------------------------------------------------------
# _repair_chemotaxis_key
# ---------------------------------------------------------------------------

class TestRepairChemotaxisKey:
    def test_importin_not_found(self):
        fake_cytosol = MagicMock()
        fake_cytosol.VIVESCA_ROOT = Path("/nonexistent_chemotaxis_12345")
        with patch.dict("sys.modules", {"metabolon.cytosol": fake_cytosol}):
            ok, msg = mod._repair_chemotaxis_key()
        assert ok is False
        assert "not found" in msg.lower()

    @patch.dict(os.environ, {}, clear=True)
    def test_keychain_env_does_not_set_key(self, tmp_path):
        """Simulate importin that runs but doesn't set the key."""
        effector = tmp_path / "effectors" / "importin"
        effector.parent.mkdir(parents=True)
        effector.write_text("def load_keychain_env(): pass\n")
        fake_cytosol = MagicMock()
        fake_cytosol.VIVESCA_ROOT = tmp_path
        os.environ.pop("PERPLEXITY_API_KEY", None)
        with patch.dict("sys.modules", {"metabolon.cytosol": fake_cytosol}):
            ok, msg = mod._repair_chemotaxis_key()
        assert ok is False
        assert "still not set" in msg

    @patch.dict(os.environ, {"PERPLEXITY_API_KEY": "new-key-from-keychain"})
    def test_keychain_env_sets_key(self, tmp_path):
        effector = tmp_path / "effectors" / "importin"
        effector.parent.mkdir(parents=True)
        effector.write_text(
            "import os\n"
            "def load_keychain_env():\n"
            "    os.environ['PERPLEXITY_API_KEY'] = 'new-key-from-keychain'\n"
        )
        fake_cytosol = MagicMock()
        fake_cytosol.VIVESCA_ROOT = tmp_path
        with patch.dict("sys.modules", {"metabolon.cytosol": fake_cytosol}):
            ok, msg = mod._repair_chemotaxis_key()
        assert ok is True
        assert "21 chars" in msg


# ---------------------------------------------------------------------------
# adaptive_response
# ---------------------------------------------------------------------------

class TestAdaptiveResponse:
    @patch.object(mod, "_save_priming")
    @patch.object(mod, "_load_priming", return_value={})
    def test_passed_probe_gets_none_repair(self, mock_load, mock_save):
        results = [{"name": "chromatin", "passed": True, "message": "ok"}]
        out = mod.adaptive_response(results)
        assert out[0]["repair_attempted"] is None

    @patch.object(mod, "_save_priming")
    @patch.object(mod, "_load_priming", return_value={})
    def test_first_failure_priming(self, mock_load, mock_save):
        results = [{"name": "rss_state", "passed": False, "message": "stale data"}]
        out = mod.adaptive_response(results)
        assert out[0]["repair_attempted"] == "priming"

    @patch.object(mod, "_save_priming")
    @patch.object(mod, "_load_priming", return_value={"rss_state": 1})
    def test_second_failure_triggers_repair(self, mock_load, mock_save):
        results = [{"name": "rss_state", "passed": False, "message": "stale data"}]
        mock_repair = MagicMock(return_value=(True, "dispatched"))
        patched_patterns = [
            ("rss_state", lambda msg: "stale" in msg, mock_repair, "rss_fetch_background"),
        ] + mod._REPAIR_PATTERNS[1:]
        with patch.object(mod, "_REPAIR_PATTERNS", patched_patterns):
            out = mod.adaptive_response(results)
        assert out[0]["repair_attempted"] == "rss_fetch_background:ok"

    @patch.object(mod, "_save_priming")
    @patch.object(mod, "_load_priming", return_value={"rss_state": 1})
    def test_repair_failure(self, mock_load, mock_save):
        results = [{"name": "rss_state", "passed": False, "message": "stale data"}]
        mock_repair = MagicMock(return_value=(False, "vivesca not found"))
        patched_patterns = [
            ("rss_state", lambda msg: "stale" in msg, mock_repair, "rss_fetch_background"),
        ] + mod._REPAIR_PATTERNS[1:]
        with patch.object(mod, "_REPAIR_PATTERNS", patched_patterns):
            out = mod.adaptive_response(results)
        assert "rss_fetch_background:fail" in out[0]["repair_attempted"]

    @patch.object(mod, "_save_priming")
    @patch.object(mod, "_load_priming", return_value={"mcp_server": 1})
    def test_mcp_server_repair_triggered(self, mock_load, mock_save):
        results = [{"name": "mcp_server", "passed": False, "message": "is not loaded"}]
        mock_repair = MagicMock(return_value=(True, "loaded ok"))
        patched_patterns = [
            mod._REPAIR_PATTERNS[0],
            ("mcp_server", lambda msg: "not loaded" in msg, mock_repair, "launchctl_load_mcp"),
            mod._REPAIR_PATTERNS[2],
        ]
        with patch.object(mod, "_REPAIR_PATTERNS", patched_patterns):
            out = mod.adaptive_response(results)
        assert out[0]["repair_attempted"] == "launchctl_load_mcp:ok"

    @patch.object(mod, "_save_priming")
    @patch.object(mod, "_load_priming", return_value={"rheotaxis": 1})
    def test_rheotaxis_key_repair_triggered(self, mock_load, mock_save):
        results = [{"name": "rheotaxis", "passed": False, "message": "API key not set or empty"}]
        mock_repair = MagicMock(return_value=(True, "key loaded"))
        patched_patterns = [
            mod._REPAIR_PATTERNS[0],
            mod._REPAIR_PATTERNS[1],
            ("rheotaxis", lambda msg: "not set" in msg, mock_repair, "importin_load_keychain"),
        ]
        with patch.object(mod, "_REPAIR_PATTERNS", patched_patterns):
            out = mod.adaptive_response(results)
        assert out[0]["repair_attempted"] == "importin_load_keychain:ok"

    @patch.object(mod, "_save_priming")
    @patch.object(mod, "_load_priming", return_value={"unknown_probe": 1})
    def test_unknown_failure(self, mock_load, mock_save):
        results = [{"name": "unknown_probe", "passed": False, "message": "something broke"}]
        out = mod.adaptive_response(results)
        assert out[0]["repair_attempted"] == "unknown"

    @patch.object(mod, "_save_priming")
    @patch.object(mod, "_load_priming", return_value={"endocytosis": 1})
    def test_critical_no_repair(self, mock_load, mock_save):
        results = [{"name": "endocytosis", "passed": False, "message": "sources.yaml not found"}]
        out = mod.adaptive_response(results)
        assert out[0]["repair_attempted"] == "critical"

    @patch.object(mod, "_save_priming")
    @patch.object(mod, "_load_priming", return_value={"endocytosis": 1})
    def test_critical_not_triggered_for_non_structural_msg(self, mock_load, mock_save):
        results = [{"name": "endocytosis", "passed": False, "message": "some other error"}]
        out = mod.adaptive_response(results)
        # Should fall through to "unknown" since message doesn't match critical keywords
        assert out[0]["repair_attempted"] == "unknown"

    @patch.object(mod, "_save_priming")
    @patch.object(mod, "_load_priming", return_value={"test_probe": 3})
    def test_pyroptosis_escalation(self, mock_load, mock_save):
        results = [{"name": "test_probe", "passed": False, "message": "keeps failing"}]
        out = mod.adaptive_response(results)
        # is_primed increments 3→4 before check_pyroptosis sees it
        assert "pyroptosis:4" in out[0]["repair_attempted"]

    @patch.object(mod, "_save_priming")
    @patch.object(mod, "_load_priming", return_value={})
    def test_passed_resets_priming(self, mock_load, mock_save):
        results = [{"name": "rss_state", "passed": True, "message": "ok"}]
        mod.adaptive_response(results)
        # Check that is_primed was called with passed=True (resets counter)
        # The priming dict passed to _save_priming should not contain rss_state
        save_calls = mock_save.call_args_list
        priming_arg = save_calls[-1][0][0]
        assert "rss_state" not in priming_arg

    @patch.object(mod, "_save_priming")
    @patch.object(mod, "_load_priming", return_value={"rss_state": 1})
    def test_post_repair_verification_on_success(self, mock_load, mock_save):
        results = [{"name": "rss_state", "passed": False, "message": "stale data"}]
        with patch.object(mod, "_repair_rss_stale", return_value=(True, "dispatched")):
            with patch.object(mod, "_run_probe_with_timeout", return_value=(True, "fresh")):
                out = mod.adaptive_response(results)
        assert out[0].get("verified") is True

    @patch.object(mod, "_save_priming")
    @patch.object(mod, "_load_priming", return_value={"rss_state": 1})
    def test_post_repair_verification_failure(self, mock_load, mock_save):
        results = [{"name": "rss_state", "passed": False, "message": "stale data"}]
        with patch.object(mod, "_repair_rss_stale", return_value=(True, "dispatched")):
            with patch.object(mod, "_run_probe_with_timeout", return_value=(False, "still stale")):
                out = mod.adaptive_response(results)
        assert out[0].get("verified") is False
