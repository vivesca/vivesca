#!/usr/bin/env python3
"""Tests for effectors/methylation.

All external file I/O and subprocess calls are mocked.
"""

import json
import pytest
import subprocess
from unittest.mock import MagicMock, patch, mock_open
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Add the project root to path so we can import the module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the module directly since it's a script
from effectors import methylation


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def mock_now():
    """Fixture for mocking the current time."""
    fixed_now = datetime(2026, 3, 31, 12, 0, 0, tzinfo=UTC)
    with patch('effectors.methylation.datetime') as mock_dt:
        mock_dt.now.return_value = fixed_now
        mock_dt.UTC = UTC
        mock_dt.fromisoformat = datetime.fromisoformat
        yield fixed_now


@pytest.fixture
def sample_candidates():
    """Sample methylation candidates events."""
    base_ts = (datetime.now(UTC) - timedelta(days=3)).isoformat()
    return [
        {"ts": base_ts, "probe": "chromatin", "repair_label": "fix_permissions", "success": True},
        {"ts": base_ts, "probe": "chromatin", "repair_label": "fix_permissions", "success": True},
        {"ts": base_ts, "probe": "import_check", "repair_label": "fix_missing_dependency", "success": True},
    ]


@pytest.fixture
def sample_infections():
    """Sample infection events."""
    base_ts = (datetime.now(UTC) - timedelta(days=2)).isoformat()
    return [
        {"ts": base_ts, "tool": "chromatin", "healed": False},
        {"ts": base_ts, "tool": "chromatin", "healed": False},
        {"ts": base_ts, "tool": "angiogenesis", "healed": True},
    ]


@pytest.fixture
def sample_failures():
    """Sample inflammasome log failures."""
    base_ts = (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return [
        f"[{base_ts}] [FAIL] chromatin — permission check failed (123ms)",
        f"[{base_ts}] [FAIL] chromatin — path not found (45ms)",
        f"[{base_ts}] [FAIL] import_check — missing module (23ms)",
    ]


# -----------------------------------------------------------------------------
# Timestamp parsing tests
# -----------------------------------------------------------------------------

class TestParseTs:
    """Tests for _parse_ts function."""

    def test_valid_iso_with_tz(self):
        """Test parsing valid ISO format with timezone."""
        ts_str = "2026-03-26T09:10:30+00:00"
        result = methylation._parse_ts(ts_str)
        assert result is not None
        assert result.year == 2026
        assert result.tzinfo is not None

    def test_valid_iso_without_tz(self):
        """Test parsing valid ISO format without timezone gets UTC added."""
        ts_str = "2026-03-26T09:10:30"
        result = methylation._parse_ts(ts_str)
        assert result is not None
        assert result.tzinfo == UTC

    def test_invalid_format(self):
        """Test invalid format returns None."""
        assert methylation._parse_ts("not-a-date") is None
        assert methylation._parse_ts("") is None
        assert methylation._parse_ts(None) is None


# -----------------------------------------------------------------------------
# File reading tests
# -----------------------------------------------------------------------------

class TestReadMethylationCandidates:
    """Tests for read_methylation_candidates."""

    def test_file_does_not_exist_returns_empty_list(self):
        """If file doesn't exist, return empty list."""
        with patch.object(methylation.METHYLATION_CANDIDATES, 'exists', return_value=False):
            result = methylation.read_methylation_candidates()
            assert result == []

    def test_file_exists_parses_valid_jsonl(self, sample_candidates):
        """Test parsing valid JSONL file with recent events."""
        content = "\n".join(json.dumps(c) for c in sample_candidates)
        with patch.object(methylation.METHYLATION_CANDIDATES, 'exists', return_value=True):
            with patch.object(methylation.METHYLATION_CANDIDATES, 'read_text', return_value=content):
                result = methylation.read_methylation_candidates()
                assert len(result) == 3
                assert all("probe" in ev for ev in result)

    def test_skips_old_events(self, sample_candidates):
        """Test events older than WINDOW_DAYS are skipped."""
        old_candidate = {
            "ts": (datetime.now(UTC) - timedelta(days=14)).isoformat(),
            "probe": "old",
            "success": True
        }
        sample_candidates.append(old_candidate)
        content = "\n".join(json.dumps(c) for c in sample_candidates)
        with patch.object(methylation.METHYLATION_CANDIDATES, 'exists', return_value=True):
            with patch.object(methylation.METHYLATION_CANDIDATES, 'read_text', return_value=content):
                result = methylation.read_methylation_candidates()
                assert len(result) == 3  # old one filtered out
                assert all(ev["probe"] != "old" for ev in result)

    def test_handles_corrupted_lines_gracefully(self):
        """Test corrupted JSON lines are skipped."""
        content = """{"ts": "2026-03-26T09:10:30Z", "probe": "test"}
this is not valid json
{"ts": "2026-03-27T10:00:00Z", "probe": "test2"}
"""
        with patch.object(methylation.METHYLATION_CANDIDATES, 'exists', return_value=True):
            with patch.object(methylation.METHYLATION_CANDIDATES, 'read_text', return_value=content):
                result = methylation.read_methylation_candidates()
                assert len(result) == 2  # only valid lines


class TestReadInflammasomeLog:
    """Tests for read_inflammasome_log."""

    def test_file_does_not_exist_returns_empty_list(self):
        """If file doesn't exist, return empty list."""
        with patch.object(methylation.INFLAMMASOME_LOG, 'exists', return_value=False):
            result = methylation.read_inflammasome_log()
            assert result == []

    def test_parses_failures_correctly(self, sample_failures, mock_now):
        """Test parsing FAIL lines correctly extracts ts, probe, message."""
        content = "\n".join(sample_failures)
        with patch.object(methylation.INFLAMMASOME_LOG, 'exists', return_value=True):
            with patch.object(methylation.INFLAMMASOME_LOG, 'read_text', return_value=content):
                result = methylation.read_inflammasome_log()
                assert len(result) == 3
                # Check chromatin appears twice
                probes = [f["probe"] for f in result]
                assert probes.count("chromatin") == 2
                assert "import_check" in probes
                # Check message extraction
                chromatin_messages = [f["message"] for f in result if f["probe"] == "chromatin"]
                assert "permission check failed" in chromatin_messages


# -----------------------------------------------------------------------------
# Pattern extraction tests
# -----------------------------------------------------------------------------

class TestExtractProbeNames:
    """Tests for extract_probe_names."""

    def test_returns_empty_if_inflammasome_missing(self):
        """Test returns empty list when inflammasome.py not found."""
        with patch.object(methylation.INFLAMMASOME_PY, 'exists', return_value=False):
            result = methylation.extract_probe_names()
            assert result == []

    def test_extracts_probes_from_correct_format(self):
        """Test extracts probe names from _PROBES list."""
        mock_src = '''
some other code
_PROBES: list[str] = [
    ("chromatin", probe_chromatin),
    ("import_check", probe_import),
    ("path_validation", probe_path),
]
more code
'''
        with patch.object(methylation.INFLAMMASOME_PY, 'read_text', return_value=mock_src):
            result = methylation.extract_probe_names()
            assert result == ["chromatin", "import_check", "path_validation"]


class TestExtractRepairPatternLabels:
    """Tests for extract_repair_pattern_labels."""

    def test_extracts_labels_correctly(self):
        """Test extracts repair pattern labels."""
        mock_src = '''
_REPAIR_PATTERNS = [
    (rss_state, lambda x: True, repair_rss, "fix_permissions"),
    (missing_import, check_import, fix_import, "fix_missing_dependency"),
]
'''
        with patch.object(methylation.INFLAMMASOME_PY, 'read_text', return_value=mock_src):
            result = methylation.extract_repair_pattern_labels()
            assert "fix_permissions" in result
            assert "fix_missing_dependency" in result


# -----------------------------------------------------------------------------
# Pattern finding tests
# -----------------------------------------------------------------------------

class TestFindCrystallizablePatterns:
    """Tests for find_crystallizable_patterns."""

    def test_returns_empty_when_no_patterns_above_threshold(self, sample_candidates, sample_infections):
        """Test returns empty dicts when no patterns >= MIN_PATTERN_COUNT."""
        # Only one chromatin failure below threshold of 2
        failures = [{"probe": "chromatin"}]
        result = methylation.find_crystallizable_patterns(
            sample_candidates[:1],  # 1 chromatin
            sample_infections[:1],   # 1 chromatin
            failures
        )
        assert all(not v for v in result.values())

    def test_finds_patterns_above_threshold(self, sample_candidates, sample_infections):
        """Test correctly identifies patterns that cross threshold."""
        # Two chromatin failures → should be included
        failures = [{"probe": "chromatin"}, {"probe": "chromatin"}, {"probe": "import_check"}]
        result = methylation.find_crystallizable_patterns(
            sample_candidates,  # chromatin has 2
            sample_infections,  # chromatin has 2
            failures  # chromatin has 2
        )
        assert "chromatin" in result["repair_candidates"]
        assert result["repair_candidates"]["chromatin"] == 2
        assert "chromatin" in result["probe_failures"]
        assert result["probe_failures"]["chromatin"] == 2
        assert "chromatin" in result["infection_tools"]
        assert result["infection_tools"]["chromatin"] == 2


# -----------------------------------------------------------------------------
# Summary tests
# -----------------------------------------------------------------------------

class TestSummarizeRepairs:
    """Tests for summarize_repairs."""

    def test_returns_nothing_message_when_empty(self):
        """Test when no candidates, returns appropriate message."""
        result = methylation.summarize_repairs([])
        assert "No successful repairs" in result

    def test_builds_correct_summary_with_counts(self, sample_candidates):
        """Test summary includes counts."""
        result = methylation.summarize_repairs(sample_candidates)
        assert "chromatin: 2x" in result


class TestSummarizeInfections:
    """Tests for summarize_infections."""

    def test_includes_healed_counts(self, sample_infections):
        """Test correctly counts healed vs unhealed."""
        failures = []
        result = methylation.summarize_infections(sample_infections, failures)
        assert "chromatin: 2x (0 healed)" in result
        assert "angiogenesis: 1x (1 healed)" in result


# -----------------------------------------------------------------------------
# Dispatch tests
# -----------------------------------------------------------------------------

class TestDispatchSonnet:
    """Tests for dispatch_sonnet, mocks subprocess."""

    def test_returns_none_when_channel_missing(self):
        """Test returns None when channel executable not found."""
        with patch.object(methylation.CHANNEL, 'exists', return_value=False):
            result = methylation.dispatch_sonnet("test prompt")
            assert result is None

    def test_successful_subprocess_call_returns_output(self):
        """Test successful subprocess execution returns stdout."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "TYPE: probe\nNAME: test\nCODE: def test():\n    return Path.home().exists()\nRATIONALE: test"
        mock_result.stderr = ""

        with patch.object(methylation.CHANNEL, 'exists', return_value=True):
            with patch('effectors.methylation.subprocess.run', return_value=mock_result):
                with patch('effectors.methylation._record_mitophagy'):
                    result = methylation.dispatch_sonnet("test prompt")
                    assert result is not None
                    assert "TYPE: probe" in result

    def test_returns_none_on_subprocess_error(self):
        """Test returns None when subprocess fails."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error"

        with patch.object(methylation.CHANNEL, 'exists', return_value=True):
            with patch('effectors.methylation.subprocess.run', return_value=mock_result):
                with patch('effectors.methylation._record_mitophagy'):
                    result = methylation.dispatch_sonnet("test prompt")
                    assert result is None

    def test_handles_timeout_gracefully(self):
        """Test timeout returns None and records failure."""
        with patch.object(methylation.CHANNEL, 'exists', return_value=True):
            with patch('effectors.methylation.subprocess.run', side_effect=subprocess.TimeoutExpired(cmd=[], timeout=120)):
                with patch('effectors.methylation._record_mitophagy') as mock_record:
                    result = methylation.dispatch_sonnet("test prompt")
                    assert result is None
                    mock_record.assert_called_once()
                    # Check it recorded failure
                    assert mock_record.call_args[1]['success'] is False


# -----------------------------------------------------------------------------
# Auto-apply safety gate tests
# -----------------------------------------------------------------------------

class TestIsSafeToAutoapply:
    """Tests for is_safe_to_autoapply."""

    def test_returns_false_if_not_probe(self):
        """Test non-probe types not safe."""
        response = """TYPE: architectural
NAME: test
CODE: some description
RATIONALE: improve system
"""
        assert not methylation.is_safe_to_autoapply(response)

    def test_returns_true_for_safe_probe_with_exists_check(self):
        """Test safe probe with .exists() check passes."""
        response = """TYPE: probe
NAME: check_home_exists
CODE: def probe_check_home():
    return Path.home().exists()
RATIONALE: check home directory
"""
        assert methylation.is_safe_to_autoapply(response) is True

    def test_returns_true_for_safe_probe_with_import_check(self):
        """Test safe probe with import check passes."""
        response = """TYPE: probe
NAME: check_module
CODE: def probe_module():
    try:
        import mymodule
        return True
    except ImportError:
        return False
RATIONALE: check module
"""
        assert methylation.is_safe_to_autoapply(response) is True

    def test_returns_false_if_contains_subprocess(self):
        """Test probe with subprocess fails."""
        response = """TYPE: probe
NAME: bad_probe
CODE: def bad_probe():
    subprocess.run(["rm", "-rf", "/"])
RATIONALE: bad
"""
        assert methylation.is_safe_to_autoapply(response) is False

    def test_returns_false_if_writes_to_files(self):
        """Test probe that writes to files not safe."""
        response = """TYPE: probe
NAME: bad_probe
CODE: def bad_probe():
    with open("file.txt", "w") as f:
        f.write("data")
RATIONALE: bad
"""
        assert methylation.is_safe_to_autoapply(response) is False


# -----------------------------------------------------------------------------
# Hybridization pass tests
# -----------------------------------------------------------------------------

class TestHybridizationPass:
    """Tests for hybridization_pass."""

    def test_returns_none_when_no_cross_subsystem_gap(self):
        """Test returns None when no gap identified."""
        patterns = {
            "repair_candidates": {},
            "probe_failures": {},
            "infection_tools": {}
        }
        result = methylation.hybridization_pass(patterns, [], [], [])
        assert result is None

    def test_identifies_cross_subsystem_gap(self):
        """Test identifies cross-subsystem failure gap."""
        patterns = {
            "repair_candidates": {},
            "probe_failures": {"novel_tool": 2},
            "infection_tools": {"novel_tool": 2}
        }
        infections = [
            {"tool": "novel_tool", "healed": False},
            {"tool": "novel_tool", "healed": False},
        ]
        failures = [{"probe": "novel_tool"}, {"probe": "novel_tool"}]
        result = methylation.hybridization_pass(patterns, [], infections, failures)
        assert result is not None
        assert "'novel_tool'" in result
        assert "probe failure" in result


# -----------------------------------------------------------------------------
# Write proposal tests
# -----------------------------------------------------------------------------

class TestWriteProposal:
    """Tests for write_proposal."""

    def test_creates_correct_content(self, tmp_path):
        """Test proposal file is written with correct structure."""
        with patch('effectors.methylation.TMP_DIR', tmp_path):
            patterns = {
                "repair_candidates": {"chromatin": 2},
                "probe_failures": {"chromatin": 2},
                "infection_tools": {}
            }
            response = "TYPE: probe\nNAME: test\nCODE: test code\nRATIONALE: test rationale"
            result = methylation.write_proposal(response, patterns, "2026-03-31")
            assert isinstance(result, Path)
            assert result.exists()
            content = result.read_text()
            assert "Methylation Proposal" in content
            assert "repair `chromatin` seen 2x" in content
            assert response in content


# -----------------------------------------------------------------------------
# Main integration test
# -----------------------------------------------------------------------------

class TestMain:
    """Integration tests for main, all external dependencies mocked."""

    def test_main_no_patterns_exits_cleanly(self, mock_now):
        """Test when no patterns above threshold, main exits cleanly."""
        with patch('effectors.methylation.read_methylation_candidates', return_value=[]):
            with patch('effectors.methylation.read_infections', return_value=[]):
                with patch('effectors.methylation.read_inflammasome_log', return_value=[]):
                    # Should not raise exceptions
                    methylation.main()

    def test_main_with_patterns_dispatches_and_writes_proposal(self, mock_now):
        """Test main flow with patterns works end-to-end."""
        patterns = {
            "repair_candidates": {"chromatin": 2},
            "probe_failures": {"chromatin": 2},
            "infection_tools": {}
        }
        with patch('effectors.methylation.read_methylation_candidates', return_value=[{}, {}]):
            with patch('effectors.methylation.read_infections', return_value=[{}, {}]):
                with patch('effectors.methylation.read_inflammasome_log', return_value=[{}, {}]):
                    with patch('effectors.methylation.find_crystallizable_patterns', return_value=patterns):
                        with patch('effectors.methylation.extract_probe_names', return_value=["chromatin"]):
                            with patch('effectors.methylation.extract_repair_pattern_labels', return_value=["fix"]):
                                with patch('effectors.methylation.dispatch_sonnet', return_value="test response"):
                                    with patch('effectors.methylation.write_proposal') as mock_write:
                                        with patch('effectors.methylation.hybridization_pass', return_value=None):
                                            methylation.main()
                                            mock_write.assert_called_once()
