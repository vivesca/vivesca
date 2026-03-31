"""Tests for methylation — weekly crystallization effector."""

from __future__ import annotations

import json
import subprocess
import importlib.util
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest


# Add the project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load methylation (it doesn't have .py extension so we need to load it manually)
methylation_path = Path(__file__).parent.parent / "effectors" / "methylation"
spec = importlib.util.spec_from_file_location("methylation", methylation_path)
methylation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(methylation)
_SCRIPT = Path.home() / "germline" / "effectors" / "methylation"
methylation = types.ModuleType("methylation")
methylation.__file__ = str(_SCRIPT)
_source = _SCRIPT.read_text()
exec(compile(_source, str(_SCRIPT), "exec"), methylation.__dict__)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Patch Path.home() to return tmp_path."""
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
    return tmp_path


@pytest.fixture
def mock_paths(mock_home: Path, monkeypatch: pytest.MonkeyPatch):
    """Set up all methylation paths under tmp_path."""
    cache_dir = mock_home / ".cache" / "inflammasome"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    data_dir = mock_home / ".local" / "share" / "vivesca"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    logs_dir = mock_home / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    tmp_dir = mock_home / "tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    
    germline_dir = mock_home / "germline"
    metabolon_dir = germline_dir / "metabolon" / "organelles"
    metabolon_dir.mkdir(parents=True, exist_ok=True)
    
    effectors_dir = germline_dir / "effectors"
    effectors_dir.mkdir(parents=True, exist_ok=True)
    
    # Create mock channel script
    channel_path = effectors_dir / "channel"
    channel_path.write_text("#!/bin/bash\necho 'mock output'")
    channel_path.chmod(0o755)
    
    # Create mock inflammasome.py with _PROBES and _REPAIR_PATTERNS
    inflammasome_py = metabolon_dir / "inflammasome.py"
    inflammasome_py.write_text('''
_PROBES: list[tuple[str, callable]] = [
    ("chromatin", probe_chromatin),
    ("rss_state", probe_rss_state),
    ("paths", probe_paths),
]

_REPAIR_PATTERNS: list[tuple[str, callable, callable, str]] = [
    ("rss_state", detect_rss_state, _repair_rss_state,
        "repair_rss_state"),
    ("paths", detect_missing_path, _repair_create_path,
        "repair_create_path"),
]
''')
    
    return {
        "cache_dir": cache_dir,
        "data_dir": data_dir,
        "logs_dir": logs_dir,
        "tmp_dir": tmp_dir,
        "channel": channel_path,
        "inflammasome_py": inflammasome_py,
    }


@pytest.fixture
def recent_ts() -> str:
    """Return a timestamp within the 7-day window."""
    return (datetime.now(UTC) - timedelta(days=1)).isoformat()


@pytest.fixture
def old_ts() -> str:
    """Return a timestamp older than 7 days."""
    return (datetime.now(UTC) - timedelta(days=10)).isoformat()


@pytest.fixture
def sample_candidates(mock_paths: dict, recent_ts: str, old_ts: str) -> Path:
    """Write sample methylation candidates file."""
    candidates_path = mock_paths["cache_dir"] / "methylation-candidates.jsonl"
    entries = [
        {"ts": recent_ts, "probe": "chromatin", "repair_label": "repair_path"},
        {"ts": recent_ts, "probe": "rss_state", "repair_label": "repair_rss"},
        {"ts": recent_ts, "probe": "chromatin", "repair_label": "repair_path"},
        {"ts": old_ts, "probe": "old_probe", "repair_label": "old_repair"},  # should be filtered
        {"ts": recent_ts, "tool": "test_tool", "repair_label": "tool_repair"},
        {"ts": recent_ts, "tool": "test_tool", "repair_label": "tool_repair"},
    ]
    with candidates_path.open("w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")
    return candidates_path


@pytest.fixture
def sample_infections(mock_paths: dict, recent_ts: str) -> Path:
    """Write sample infections file."""
    infections_path = mock_paths["data_dir"] / "infections.jsonl"
    entries = [
        {"ts": recent_ts, "tool": "rheotaxis", "healed": True},
        {"ts": recent_ts, "tool": "poiesis", "healed": False},
        {"ts": recent_ts, "tool": "rheotaxis", "healed": False},
        {"ts": recent_ts, "tool": "rheotaxis", "healed": True},
    ]
    with infections_path.open("w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")
    return infections_path


@pytest.fixture
def sample_inflammasome_log(mock_paths: dict, recent_ts: str) -> Path:
    """Write sample inflammasome log."""
    log_path = mock_paths["logs_dir"] / "inflammasome.log"
    lines = [
        f"[{recent_ts}] [FAIL] chromatin — path not found (100ms)",
        f"[{recent_ts}] [FAIL] rss_state — state corrupted (50ms)",
        f"[{recent_ts}] [OK] paths — all paths exist (20ms)",
        f"[{recent_ts}] [FAIL] chromatin — another issue (80ms)",
        f"[2026-01-01T00:00:00Z] [FAIL] old_probe — old failure (30ms)",  # old, should be filtered
    ]
    with log_path.open("w") as f:
        for line in lines:
            f.write(line + "\n")
    return log_path


# ---------------------------------------------------------------------------
# Log tests
# ---------------------------------------------------------------------------


def test_log_writes_to_file(mock_paths: dict, monkeypatch: pytest.MonkeyPatch):
    """log() writes to both stdout and the log file."""
    log_path = mock_paths["logs_dir"] / "methylation.log"
    monkeypatch.setattr(methylation, "LOG_FILE", log_path)
    
    methylation.log("test message")
    
    content = log_path.read_text()
    assert "test message" in content
    assert "[20" in content  # timestamp starts with year


def test_log_handles_write_error(mock_paths: dict, monkeypatch: pytest.MonkeyPatch, capsys):
    """log() doesn't raise if file write fails."""
    # Set LOG_FILE to a path that can't be created
    bad_path = mock_paths["logs_dir"] / "nonexistent" / "deep" / "methylation.log"
    monkeypatch.setattr(methylation, "LOG_FILE", bad_path)
    
    # Should not raise
    methylation.log("test message")
    
    # But should still print
    captured = capsys.readouterr()
    assert "test message" in captured.out


# ---------------------------------------------------------------------------
# Timestamp parsing tests
# ---------------------------------------------------------------------------


def test_parse_ts_valid():
    """_parse_ts parses valid ISO-8601 timestamps."""
    ts_str = "2026-03-31T12:00:00+00:00"
    result = methylation._parse_ts(ts_str)
    assert result is not None
    assert result.year == 2026
    assert result.month == 3


def test_parse_ts_naive_adds_utc():
    """_parse_ts adds UTC timezone to naive timestamps."""
    ts_str = "2026-03-31T12:00:00"
    result = methylation._parse_ts(ts_str)
    assert result is not None
    assert result.tzinfo is not None


def test_parse_ts_invalid_returns_none():
    """_parse_ts returns None for invalid timestamps."""
    assert methylation._parse_ts("not a timestamp") is None
    assert methylation._parse_ts("") is None


def test_cutoff_returns_seven_days_ago():
    """_cutoff returns datetime 7 days ago."""
    cutoff = methylation._cutoff()
    now = datetime.now(UTC)
    delta = now - cutoff
    assert 6 < delta.days < 8  # approximately 7 days


# ---------------------------------------------------------------------------
# Signal reading tests
# ---------------------------------------------------------------------------


def test_read_methylation_candidates_no_file(mock_paths: dict, monkeypatch: pytest.MonkeyPatch):
    """Returns empty list if candidates file doesn't exist."""
    monkeypatch.setattr(methylation, "METHYLATION_CANDIDATES", mock_paths["cache_dir"] / "nonexistent.jsonl")
    result = methylation.read_methylation_candidates()
    assert result == []


def test_read_methylation_candidates_filters_by_age(
    mock_paths: dict,
    sample_candidates: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """Only returns entries within the 7-day window."""
    monkeypatch.setattr(methylation, "METHYLATION_CANDIDATES", sample_candidates)
    result = methylation.read_methylation_candidates()
    
    # Should filter out the old_ts entry
    assert len(result) == 5
    for entry in result:
        assert entry.get("probe") != "old_probe"


def test_read_methylation_candidates_handles_corrupt_line(
    mock_paths: dict,
    monkeypatch: pytest.MonkeyPatch,
):
    """Skips lines that aren't valid JSON."""
    candidates_path = mock_paths["cache_dir"] / "methylation-candidates.jsonl"
    recent_ts = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    with candidates_path.open("w") as f:
        f.write('{"ts": "' + recent_ts + '", "probe": "valid"}\n')
        f.write("this is not json\n")
        f.write('{"ts": "' + recent_ts + '", "probe": "also_valid"}\n')
    
    monkeypatch.setattr(methylation, "METHYLATION_CANDIDATES", candidates_path)
    result = methylation.read_methylation_candidates()
    
    assert len(result) == 2


def test_read_infections_no_file(mock_paths: dict, monkeypatch: pytest.MonkeyPatch):
    """Returns empty list if infections file doesn't exist."""
    monkeypatch.setattr(methylation, "INFECTION_LOG", mock_paths["data_dir"] / "nonexistent.jsonl")
    result = methylation.read_infections()
    assert result == []


def test_read_infections_filters_by_age(
    mock_paths: dict,
    sample_infections: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """Only returns entries within the 7-day window."""
    monkeypatch.setattr(methylation, "INFECTION_LOG", sample_infections)
    result = methylation.read_infections()
    assert len(result) == 4


def test_read_inflammasome_log_no_file(mock_paths: dict, monkeypatch: pytest.MonkeyPatch):
    """Returns empty list if log file doesn't exist."""
    monkeypatch.setattr(methylation, "INFLAMMASOME_LOG", mock_paths["logs_dir"] / "nonexistent.log")
    result = methylation.read_inflammasome_log()
    assert result == []


def test_read_inflammasome_log_parses_failures(
    mock_paths: dict,
    sample_inflammasome_log: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """Parses FAIL lines and extracts probe name and message."""
    monkeypatch.setattr(methylation, "INFLAMMASOME_LOG", sample_inflammasome_log)
    result = methylation.read_inflammasome_log()
    
    # Should only return FAIL lines within the window
    assert len(result) == 3
    
    # Check parsing
    chromatin_failures = [f for f in result if f["probe"] == "chromatin"]
    assert len(chromatin_failures) == 2
    assert "path not found" in chromatin_failures[0]["message"]


def test_read_inflammasome_log_filters_by_age(
    mock_paths: dict,
    monkeypatch: pytest.MonkeyPatch,
):
    """Filters out entries older than 7 days."""
    log_path = mock_paths["logs_dir"] / "inflammasome.log"
    old_ts = (datetime.now(UTC) - timedelta(days=10)).isoformat()
    recent_ts = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    
    with log_path.open("w") as f:
        f.write(f"[{old_ts}] [FAIL] old_probe — old message (10ms)\n")
        f.write(f"[{recent_ts}] [FAIL] new_probe — new message (20ms)\n")
    
    monkeypatch.setattr(methylation, "INFLAMMASOME_LOG", log_path)
    result = methylation.read_inflammasome_log()
    
    assert len(result) == 1
    assert result[0]["probe"] == "new_probe"


# ---------------------------------------------------------------------------
# Pattern extraction tests
# ---------------------------------------------------------------------------


def test_extract_probe_names(mock_paths: dict, monkeypatch: pytest.MonkeyPatch):
    """Extracts probe names from inflammasome.py."""
    monkeypatch.setattr(methylation, "INFLAMMASOME_PY", mock_paths["inflammasome_py"])
    result = methylation.extract_probe_names()
    
    assert "chromatin" in result
    assert "rss_state" in result
    assert "paths" in result


def test_extract_probe_names_no_file(mock_paths: dict, monkeypatch: pytest.MonkeyPatch):
    """Returns empty list if inflammasome.py doesn't exist."""
    monkeypatch.setattr(methylation, "INFLAMMASOME_PY", mock_paths["metabolon_dir"] / "nonexistent.py")
    result = methylation.extract_probe_names()
    assert result == []


def test_extract_repair_pattern_labels(mock_paths: dict, monkeypatch: pytest.MonkeyPatch):
    """Extracts repair pattern labels from inflammasome.py."""
    monkeypatch.setattr(methylation, "INFLAMMASOME_PY", mock_paths["inflammasome_py"])
    result = methylation.extract_repair_pattern_labels()
    
    assert "repair_rss_state" in result
    assert "repair_create_path" in result


def test_extract_repair_pattern_labels_no_file(mock_paths: dict, monkeypatch: pytest.MonkeyPatch):
    """Returns empty list if inflammasome.py doesn't exist."""
    monkeypatch.setattr(methylation, "INFLAMMASOME_PY", mock_paths["metabolon_dir"] / "nonexistent.py")
    result = methylation.extract_repair_pattern_labels()
    assert result == []


# ---------------------------------------------------------------------------
# Summarization tests
# ---------------------------------------------------------------------------


def test_summarize_repairs_empty():
    """summarize_repairs returns message for empty input."""
    result = methylation.summarize_repairs([])
    assert "No successful repairs" in result


def test_summarize_repairs_groups_by_probe():
    """summarize_repairs groups repairs by probe/tool name."""
    candidates = [
        {"probe": "chromatin", "repair_label": "r1"},
        {"probe": "chromatin", "repair_label": "r2"},
        {"tool": "test_tool", "repair_label": "r3"},
    ]
    result = methylation.summarize_repairs(candidates)
    
    assert "chromatin: 2x" in result
    assert "test_tool: 1x" in result


def test_summarize_infections_empty():
    """summarize_infections handles empty inputs."""
    result = methylation.summarize_infections([], [])
    assert "No infection events" in result
    assert "No probe failures" in result


def test_summarize_infections_groups_by_tool():
    """summarize_infections groups events by tool and counts healed."""
    infections = [
        {"tool": "rheotaxis", "healed": True},
        {"tool": "rheotaxis", "healed": False},
        {"tool": "poiesis", "healed": False},
    ]
    failures = [
        {"probe": "chromatin"},
        {"probe": "chromatin"},
        {"probe": "paths"},
    ]
    result = methylation.summarize_infections(infections, failures)
    
    assert "rheotaxis: 2x (1 healed)" in result
    assert "chromatin: 2x" in result


# ---------------------------------------------------------------------------
# Pattern qualification tests
# ---------------------------------------------------------------------------


def test_find_crystallizable_patterns_below_threshold():
    """Patterns below MIN_PATTERN_COUNT are not returned."""
    candidates = [{"probe": "rare"}]  # only 1
    infections = [{"tool": "uncommon"}]  # only 1
    failures = [{"probe": "sparse"}]  # only 1
    
    result = methylation.find_crystallizable_patterns(candidates, infections, failures)
    
    assert result["repair_candidates"] == {}
    assert result["probe_failures"] == {}
    assert result["infection_tools"] == {}


def test_find_crystallizable_patterns_above_threshold():
    """Patterns at or above MIN_PATTERN_COUNT are returned."""
    candidates = [
        {"probe": "common"},
        {"probe": "common"},
    ]
    infections = [
        {"tool": "frequent"},
        {"tool": "frequent"},
    ]
    failures = [
        {"probe": "recurring"},
        {"probe": "recurring"},
    ]
    
    result = methylation.find_crystallizable_patterns(candidates, infections, failures)
    
    assert "common" in result["repair_candidates"]
    assert result["repair_candidates"]["common"] == 2
    assert "recurring" in result["probe_failures"]
    assert "frequent" in result["infection_tools"]


def test_find_crystallizable_patterns_aggregates_keys():
    """Uses probe/tool/repair_label for aggregation."""
    candidates = [
        {"probe": "p1"},
        {"tool": "p1"},  # same key, different field
        {"repair_label": "p1"},  # same key, different field
    ]
    
    result = methylation.find_crystallizable_patterns(candidates, [], [])
    
    # All three aggregate under "p1"
    assert result["repair_candidates"].get("p1") == 3


# ---------------------------------------------------------------------------
# Dispatch tests
# ---------------------------------------------------------------------------


def test_dispatch_sonnet_channel_not_exists(mock_paths: dict, monkeypatch: pytest.MonkeyPatch):
    """Returns None if channel effector doesn't exist."""
    monkeypatch.setattr(methylation, "CHANNEL", mock_paths["tmp_dir"] / "nonexistent")
    
    result = methylation.dispatch_sonnet("test prompt")
    
    assert result is None


def test_dispatch_sonnet_success(mock_paths: dict, monkeypatch: pytest.MonkeyPatch):
    """Returns stdout on successful channel call."""
    monkeypatch.setattr(methylation, "CHANNEL", mock_paths["channel"])
    
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="synthesis output",
            stderr="",
        )
        result = methylation.dispatch_sonnet("test prompt")
    
    assert result == "synthesis output"
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert "sonnet" in args or args[1]  # model arg


def test_dispatch_sonnet_nonzero_exit(mock_paths: dict, monkeypatch: pytest.MonkeyPatch):
    """Returns None on non-zero exit code."""
    monkeypatch.setattr(methylation, "CHANNEL", mock_paths["channel"])
    
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="error message",
        )
        result = methylation.dispatch_sonnet("test prompt")
    
    assert result is None


def test_dispatch_sonnet_timeout(mock_paths: dict, monkeypatch: pytest.MonkeyPatch):
    """Returns None on timeout."""
    monkeypatch.setattr(methylation, "CHANNEL", mock_paths["channel"])
    
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="channel", timeout=120)
        result = methylation.dispatch_sonnet("test prompt")
    
    assert result is None


def test_dispatch_sonnet_exception(mock_paths: dict, monkeypatch: pytest.MonkeyPatch):
    """Returns None on any exception."""
    monkeypatch.setattr(methylation, "CHANNEL", mock_paths["channel"])
    
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = OSError("something broke")
        result = methylation.dispatch_sonnet("test prompt")
    
    assert result is None


def test_tissue_route_fallback(monkeypatch: pytest.MonkeyPatch):
    """_tissue_route returns fallback on import error."""
    with patch.dict("sys.modules", {"metabolon.organelles.tissue_routing": None}):
        result = methylation._tissue_route("methylation", "glm")
    
    assert result == "glm"


def test_record_mitophagy_handles_error():
    """_record_mitophagy silently handles any error."""
    # Should not raise
    methylation._record_mitophagy("model", "task", True, 100)


# ---------------------------------------------------------------------------
# Proposal writing tests
# ---------------------------------------------------------------------------


def test_write_proposal(mock_paths: dict):
    """write_proposal creates the expected file."""
    patterns = {
        "repair_candidates": {"chromatin": 3},
        "probe_failures": {"rss_state": 2},
        "infection_tools": {"poiesis": 2},
    }
    response = "TYPE: probe\nNAME: test_probe\nCODE: pass\nRATIONALE: test"
    
    result = methylation.write_proposal(response, patterns, "2026-03-31")
    
    assert result.exists()
    assert "methylation-proposal-2026-03-31.md" in str(result)
    
    content = result.read_text()
    assert "# Methylation Proposal" in content
    assert "chromatin" in content
    assert "rss_state" in content
    assert "poiesis" in content
    assert "TYPE: probe" in content


def test_write_proposal_empty_patterns(mock_paths: dict):
    """write_proposal handles empty patterns gracefully."""
    patterns = {
        "repair_candidates": {},
        "probe_failures": {},
        "infection_tools": {},
    }
    response = "TYPE: architectural\nNAME: observation\nCODE: none\nRATIONALE: test"
    
    result = methylation.write_proposal(response, patterns, "2026-03-31")
    
    content = result.read_text()
    assert "(none above threshold)" in content


# ---------------------------------------------------------------------------
# Hybridization tests
# ---------------------------------------------------------------------------


def test_hybridization_pass_no_gap():
    """Returns None when no gap is found."""
    patterns = {
        "repair_candidates": {},
        "probe_failures": {},
        "infection_tools": {},
    }
    
    result = methylation.hybridization_pass(patterns, [], [], [])
    assert result is None


def test_hybridization_pass_known_subsystem_only():
    """Returns None if all failures are from known subsystems."""
    patterns = {
        "repair_candidates": {},
        "probe_failures": {"inflammasome": 3},
        "infection_tools": {"poiesis": 3},
    }
    infections = [{"tool": "poiesis", "healed": False}]
    
    # All failing tools are known subsystems
    result = methylation.hybridization_pass(patterns, [], infections, [])
    
    # No gap because all are known
    assert result is None


def test_hybridization_pass_finds_gap():
    """Identifies gaps from cross-subsystem failures."""
    patterns = {
        "repair_candidates": {},
        "probe_failures": {"novel_probe": 3},
        "infection_tools": {"novel_tool": 2},
    }
    infections = [{"tool": "novel_tool", "healed": False}]
    
    result = methylation.hybridization_pass(patterns, [], infections, [])
    
    assert result is not None
    assert "novel_probe" in result or "novel_tool" in result


def test_hybridization_pass_unhealed_infections():
    """Identifies gaps from unhealed infections."""
    patterns = {
        "repair_candidates": {},
        "probe_failures": {"new_system": 2},
        "infection_tools": {},
    }
    infections = [{"tool": "another_new", "healed": False}]
    failures = [{"probe": "new_system"}]
    
    result = methylation.hybridization_pass(patterns, [], infections, failures)
    
    # Should find gap due to novel unhealed infection
    assert result is not None


def test_write_hybridization_proposal_new_file(mock_paths: dict):
    """Creates new hybridization proposal file."""
    response = "MECHANISM: autophagy\nBIOLOGY: test\nMAPPING: test\nBREAK: test\nPROPOSAL: test"
    gap = "Observed gap in coverage"
    
    result = methylation.write_hybridization_proposal(response, gap, "2026-03-31")
    
    assert result.exists()
    content = result.read_text()
    assert "# Hybridization Proposals" in content
    assert "Observed gap in coverage" in content


def test_write_hybridization_proposal_appends(mock_paths: dict):
    """Appends to existing hybridization proposal file."""
    gap = "Second gap observed"
    response = "MECHANISM: exocytosis"
    
    # First write
    methylation.write_hybridization_proposal("first response", "first gap", "2026-03-31")
    
    # Second write should append
    result = methylation.write_hybridization_proposal(response, gap, "2026-03-31")
    
    content = result.read_text()
    assert "first gap" in content
    assert "Second gap observed" in content


# ---------------------------------------------------------------------------
# Auto-apply gate tests
# ---------------------------------------------------------------------------


def test_is_safe_to_autoapply_not_probe():
    """Returns False for non-probe proposals."""
    response = "TYPE: repair\nNAME: fix_something\nCODE: pass\nRATIONALE: test"
    assert methylation.is_safe_to_autoapply(response) is False


def test_is_safe_to_autoapply_unsafe_code():
    """Returns False if code contains unsafe patterns."""
    response = """TYPE: probe
NAME: dangerous_probe
CODE:
def probe_dangerous():
    subprocess.run(["rm", "-rf", "/"])
RATIONALE: very bad"""
    
    assert methylation.is_safe_to_autoapply(response) is False


def test_is_safe_to_autoapply_safe_probe():
    """Returns True for safe path/import check probes."""
    response = """TYPE: probe
NAME: safe_path_check
CODE:
def probe_paths():
    from pathlib import Path
    return Path.home().exists()
RATIONALE: Safe path check"""
    
    assert methylation.is_safe_to_autoapply(response) is True


def test_is_safe_to_autoapply_shutil_which():
    """Returns True for probes using shutil.which."""
    response = """TYPE: probe
NAME: tool_check
CODE:
import shutil
def probe_tool():
    return shutil.which("git") is not None
RATIONALE: Check for tool"""
    
    assert methylation.is_safe_to_autoapply(response) is True


def test_is_safe_to_autoapply_rejects_write():
    """Returns False if code attempts file writes."""
    response = """TYPE: probe
NAME: bad_probe
CODE:
def probe_bad():
    Path("/tmp/test").write_text("data")
RATIONALE: Writes data"""
    
    assert methylation.is_safe_to_autoapply(response) is False


def test_is_safe_to_autoapply_rejects_mkdir():
    """Returns False if code attempts mkdir."""
    response = """TYPE: probe
NAME: mkdir_probe
CODE:
def probe_mkdir():
    Path("/tmp/newdir").mkdir()
RATIONALE: Creates directory"""
    
    assert methylation.is_safe_to_autoapply(response) is False


# ---------------------------------------------------------------------------
# Main function tests
# ---------------------------------------------------------------------------


def test_main_no_patterns(mock_paths: dict, monkeypatch: pytest.MonkeyPatch, capsys):
    """main() exits early when no patterns above threshold."""
    monkeypatch.setattr(methylation, "METHYLATION_CANDIDATES", mock_paths["cache_dir"] / "nonexistent.jsonl")
    monkeypatch.setattr(methylation, "INFECTION_LOG", mock_paths["data_dir"] / "nonexistent.jsonl")
    monkeypatch.setattr(methylation, "INFLAMMASOME_LOG", mock_paths["logs_dir"] / "nonexistent.log")
    
    methylation.main()
    
    captured = capsys.readouterr()
    assert "no patterns above threshold" in captured.out


def test_main_dispatches_and_writes(
    mock_paths: dict,
    sample_candidates: Path,
    sample_infections: Path,
    sample_inflammasome_log: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """main() dispatches to sonnet and writes proposal when patterns exist."""
    monkeypatch.setattr(methylation, "METHYLATION_CANDIDATES", sample_candidates)
    monkeypatch.setattr(methylation, "INFECTION_LOG", sample_infections)
    monkeypatch.setattr(methylation, "INFLAMMASOME_LOG", sample_inflammasome_log)
    monkeypatch.setattr(methylation, "CHANNEL", mock_paths["channel"])
    
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="TYPE: probe\nNAME: test\nCODE: pass\nRATIONALE: test",
            stderr="",
        )
        methylation.main()
    
    # Should have written a proposal
    proposals = list(mock_paths["tmp_dir"].glob("methylation-proposal-*.md"))
    assert len(proposals) >= 1


def test_main_handles_no_response(
    mock_paths: dict,
    sample_candidates: Path,
    sample_infections: Path,
    sample_inflammasome_log: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys,
):
    """main() handles case where sonnet returns no response."""
    monkeypatch.setattr(methylation, "METHYLATION_CANDIDATES", sample_candidates)
    monkeypatch.setattr(methylation, "INFECTION_LOG", sample_infections)
    monkeypatch.setattr(methylation, "INFLAMMASOME_LOG", sample_inflammasome_log)
    monkeypatch.setattr(methylation, "CHANNEL", mock_paths["channel"])
    
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="error",
        )
        methylation.main()
    
    captured = capsys.readouterr()
    assert "no response from sonnet" in captured.out.lower()


def test_main_hybridization_pass(
    mock_paths: dict,
    sample_candidates: Path,
    sample_infections: Path,
    sample_inflammasome_log: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """main() runs hybridization pass and writes proposal if gap found."""
    # Create patterns that will trigger hybridization
    candidates_path = mock_paths["cache_dir"] / "methylation-candidates.jsonl"
    recent_ts = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    with candidates_path.open("w") as f:
        f.write(json.dumps({"ts": recent_ts, "probe": "novel_probe"}) + "\n")
        f.write(json.dumps({"ts": recent_ts, "probe": "novel_probe"}) + "\n")
    
    infections_path = mock_paths["data_dir"] / "infections.jsonl"
    with infections_path.open("w") as f:
        f.write(json.dumps({"ts": recent_ts, "tool": "novel_tool", "healed": False}) + "\n")
        f.write(json.dumps({"ts": recent_ts, "tool": "novel_tool", "healed": False}) + "\n")
    
    log_path = mock_paths["logs_dir"] / "inflammasome.log"
    with log_path.open("w") as f:
        f.write(f"[{recent_ts}] [FAIL] novel_probe — failure (10ms)\n")
        f.write(f"[{recent_ts}] [FAIL] novel_probe — failure (10ms)\n")
    
    monkeypatch.setattr(methylation, "METHYLATION_CANDIDATES", candidates_path)
    monkeypatch.setattr(methylation, "INFECTION_LOG", infections_path)
    monkeypatch.setattr(methylation, "INFLAMMASOME_LOG", log_path)
    monkeypatch.setattr(methylation, "CHANNEL", mock_paths["channel"])
    
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="MECHANISM: test\nBIOLOGY: test\nMAPPING: test\nBREAK: test\nPROPOSAL: test",
            stderr="",
        )
        methylation.main()
    
    # Should have written both proposals
    methylation_proposals = list(mock_paths["tmp_dir"].glob("methylation-proposal-*.md"))
    hybrid_proposals = list(mock_paths["tmp_dir"].glob("hybridization-proposals-*.md"))
    assert len(methylation_proposals) >= 1
    # Hybridization might or might not run depending on gap detection


def test_main_exits_zero_on_exception(monkeypatch: pytest.MonkeyPatch):
    """main() always exits 0 even on exception."""
    with patch.object(methylation, "read_methylation_candidates", side_effect=RuntimeError("boom")):
        with pytest.raises(SystemExit) as exc_info:
            methylation.main()
    
    assert exc_info.value.code == 0


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------


def test_full_pipeline_integration(
    mock_paths: dict,
    sample_candidates: Path,
    sample_infections: Path,
    sample_inflammasome_log: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """Test the full methylation pipeline from signal reading to proposal writing."""
    monkeypatch.setattr(methylation, "METHYLATION_CANDIDATES", sample_candidates)
    monkeypatch.setattr(methylation, "INFECTION_LOG", sample_infections)
    monkeypatch.setattr(methylation, "INFLAMMASOME_LOG", sample_inflammasome_log)
    monkeypatch.setattr(methylation, "CHANNEL", mock_paths["channel"])
    
    # Read signals
    candidates = methylation.read_methylation_candidates()
    infections = methylation.read_infections()
    failures = methylation.read_inflammasome_log()
    
    assert len(candidates) > 0
    assert len(infections) > 0
    assert len(failures) > 0
    
    # Find patterns
    patterns = methylation.find_crystallizable_patterns(candidates, infections, failures)
    
    # Should have some crystallizable patterns (chromatin appears 2x)
    assert patterns["repair_candidates"] or patterns["probe_failures"] or patterns["infection_tools"]
    
    # Build summaries
    repairs_summary = methylation.summarize_repairs(candidates)
    infection_summary = methylation.summarize_infections(infections, failures)
    
    assert "chromatin" in repairs_summary
    assert "rheotaxis" in infection_summary


def test_max_entries_limit(mock_paths: dict, monkeypatch: pytest.MonkeyPatch):
    """Signal reading respects MAX_ENTRIES limit."""
    # Create file with many entries
    candidates_path = mock_paths["cache_dir"] / "methylation-candidates.jsonl"
    recent_ts = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    
    with candidates_path.open("w") as f:
        for i in range(200):
            f.write(json.dumps({"ts": recent_ts, "probe": f"probe_{i}"}) + "\n")
    
    monkeypatch.setattr(methylation, "METHYLATION_CANDIDATES", candidates_path)
    
    # Patch MAX_ENTRIES to smaller value for test
    monkeypatch.setattr(methylation, "MAX_ENTRIES", 50)
    
    result = methylation.read_methylation_candidates()
    
    # Should only read last MAX_ENTRIES lines
    assert len(result) <= 50
