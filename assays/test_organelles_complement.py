from __future__ import annotations

"""Tests for complement — convergent detection and resolution."""

import json
import importlib
from datetime import datetime, UTC
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Import after patching will be done in fixtures
# We'll import the module inside fixtures after patching Path.home


@pytest.fixture(autouse=True)
def mock_home(tmp_path, monkeypatch):
    """Ensure Path.home() points to a temporary directory."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr("pathlib.Path.home", lambda: home)
    return home


@pytest.fixture
def complement_module(mock_home, monkeypatch):
    """Return the complement module with all filesystem dependencies mocked."""
    # Now that Path.home is patched, we can import the module
    # However, the module may have already been imported earlier (top of file).
    # We'll force reload to recompute module-level constants.
    import metabolon.organelles.complement as comp_module
    importlib.reload(comp_module)
    # Now the constants _PRIMING_PATH and _COMPLEMENT_STATE are based on mocked home.
    # Ensure parent directories exist
    (mock_home / ".cache" / "inflammasome").mkdir(parents=True, exist_ok=True)
    (mock_home / ".local" / "share" / "vivesca").mkdir(parents=True, exist_ok=True)
    return comp_module


@pytest.fixture
def mock_infections(monkeypatch):
    """Mock recall_infections in complement module."""
    events = []
    def mock_recall():
        return events
    monkeypatch.setattr("metabolon.organelles.complement.recall_infections", mock_recall)
    return events


@pytest.fixture
def mock_vasomotor(monkeypatch):
    """Mock log and record_event in complement module."""
    logged = []
    recorded = []
    def mock_log(msg: str):
        logged.append(msg)
    def mock_record(event: str, **kwargs):
        recorded.append((event, kwargs))
    monkeypatch.setattr("metabolon.organelles.complement.log", mock_log)
    monkeypatch.setattr("metabolon.organelles.complement.record_event", mock_record)
    return {"logged": logged, "recorded": recorded}


@pytest.fixture
def mock_datetime_now(monkeypatch):
    """Mock datetime.datetime.now to return a fixed time."""
    fixed_now = datetime(2025, 1, 1, 12, 0, 0)
    class MockDatetime:
        @classmethod
        def now(cls, tz=None):
            return fixed_now
    monkeypatch.setattr("metabolon.organelles.complement.datetime.datetime", MockDatetime)
    return fixed_now


def test_assemble_mac_empty(complement_module, mock_infections, mock_vasomotor):
    """No probe failures, no infections → empty hits."""
    # No priming file
    hits = complement_module.assemble_mac()
    assert hits == []


def test_assemble_mac_probe_only(complement_module, mock_infections, mock_home):
    """Only probe failures (no infections) → hits with infection_count=0."""
    priming_path = mock_home / ".cache" / "inflammasome" / "priming.json"
    priming_path.write_text(json.dumps({"toolA": 3, "toolB": 1}))
    hits = complement_module.assemble_mac()
    assert len(hits) == 2
    # Both hits should have probe_consecutive_fails > 0, infection_count 0
    for hit in hits:
        assert hit["probe_consecutive_fails"] > 0
        assert hit["infection_count"] == 0
        assert not hit["convergent"]
        assert hit["resolution"] == "escalate"
        assert hit["reason"] == "unhealed infection"
    keys = {hit["key"] for hit in hits}
    assert keys == {"toolA", "toolB"}


def test_assemble_mac_infection_only(complement_module, mock_infections, mock_datetime_now):
    """Only infections (no probe failures) → hits with probe_consecutive_fails=0."""
    mock_infections.extend([
        {"ts": "2025-01-01T12:00:00Z", "tool": "toolC", "error": "err", "fingerprint": "fp1", "healed": False},
        {"ts": "2025-01-01T13:00:00Z", "tool": "toolC", "error": "err2", "fingerprint": "fp2", "healed": False},
        {"ts": "2025-01-01T14:00:00Z", "tool": "toolD", "error": "err3", "fingerprint": "fp3", "healed": False},
    ])
    hits = complement_module.assemble_mac()
    assert len(hits) == 2
    for hit in hits:
        assert hit["probe_consecutive_fails"] == 0
        assert hit["infection_count"] > 0
        assert not hit["convergent"]
        assert hit["resolution"] == "escalate"
        assert hit["reason"] == "unhealed infection"
    tool_c = next(h for h in hits if h["key"] == "toolC")
    assert tool_c["infection_count"] == 2
    tool_d = next(h for h in hits if h["key"] == "toolD")
    assert tool_d["infection_count"] == 1


def test_assemble_mac_convergent(complement_module, mock_infections, mock_home):
    """Both probe failures and infections for same key → convergent."""
    priming_path = mock_home / ".cache" / "inflammasome" / "priming.json"
    priming_path.write_text(json.dumps({"toolE": 5}))
    mock_infections.extend([
        {"ts": "2025-01-01T12:00:00Z", "tool": "toolE", "error": "err", "fingerprint": "fp", "healed": False},
    ])
    hits = complement_module.assemble_mac()
    assert len(hits) == 1
    hit = hits[0]
    assert hit["probe_consecutive_fails"] == 5
    assert hit["infection_count"] == 1
    assert hit["convergent"]
    assert hit["resolution"] == "escalate"
    assert hit["reason"] == "convergent detection"


def test_assemble_mac_suppression(complement_module, mock_infections, mock_home):
    """Keys in SUPPRESSIONS get resolution 'suppress' and reason from dict."""
    priming_path = mock_home / ".cache" / "inflammasome" / "priming.json"
    priming_path.write_text(json.dumps({"rheotaxis": 2}))
    mock_infections.extend([
        {"ts": "2025-01-01T12:00:00Z", "tool": "rheotaxis", "error": "err", "fingerprint": "fp", "healed": False},
    ])
    hits = complement_module.assemble_mac()
    assert len(hits) == 1
    hit = hits[0]
    assert hit["key"] == "rheotaxis"
    assert hit["resolution"] == "suppress"
    assert hit["reason"] == complement_module.SUPPRESSIONS["rheotaxis"]


def test_assemble_mac_prefixed_key(complement_module, mock_infections, mock_home):
    """Probe failures with 'self_test_failure:' prefix are matched."""
    priming_path = mock_home / ".cache" / "inflammasome" / "priming.json"
    priming_path.write_text(json.dumps({"self_test_failure:toolF": 4}))
    mock_infections.extend([
        {"ts": "2025-01-01T12:00:00Z", "tool": "toolF", "error": "err", "fingerprint": "fp", "healed": False},
    ])
    hits = complement_module.assemble_mac()
    # Expect two hits: one for prefixed key (probe only), one for normalized key (convergent)
    assert len(hits) == 2
    # Find prefixed hit
    prefixed = next(h for h in hits if h["key"] == "self_test_failure:toolF")
    assert prefixed["probe_consecutive_fails"] == 4
    assert prefixed["infection_count"] == 0
    assert not prefixed["convergent"]
    assert prefixed["resolution"] == "escalate"
    # Find normalized hit
    normalized = next(h for h in hits if h["key"] == "toolF")
    assert normalized["probe_consecutive_fails"] == 4
    assert normalized["infection_count"] == 1
    assert normalized["convergent"]
    assert normalized["resolution"] == "escalate"


def test_resolve_empty(complement_module, mock_infections, mock_vasomotor):
    """No hits → status quiescent."""
    result = complement_module.resolve()
    assert result["status"] == "quiescent"
    assert result["hits"] == 0
    # record_event not called
    assert len(mock_vasomotor["recorded"]) == 0


def test_resolve_with_hits(complement_module, mock_infections, mock_vasomotor, mock_home):
    """Hits are categorized into suppressed, resolved, escalated."""
    priming_path = mock_home / ".cache" / "inflammasome" / "priming.json"
    priming_path.write_text(json.dumps({"toolA": 1, "rheotaxis": 2, "toolB": 3}))
    mock_infections.extend([
        {"ts": "2025-01-01T12:00:00Z", "tool": "toolA", "error": "err", "fingerprint": "fp", "healed": False},
        {"ts": "2025-01-01T12:00:00Z", "tool": "toolB", "error": "err", "fingerprint": "fp", "healed": False},
    ])
    result = complement_module.resolve()
    assert result["status"] == "active"
    assert result["hits"] == 3
    # suppressed: rheotaxis (in SUPPRESSIONS)
    assert result["suppressed"] == 1
    # resolved: none (since we have no resolution "remediate")
    assert result["resolved"] == 0
    # escalated: toolA, toolB
    assert result["escalated"] == 2
    # convergent: toolA (probe+infection) and toolB (probe+infection)
    assert result["convergent"] == 2
    # record_event should have been called with complement_activation
    assert len(mock_vasomotor["recorded"]) == 1
    event_name, kwargs = mock_vasomotor["recorded"][0]
    assert event_name == "complement_activation"
    assert kwargs["hits"] == 3
    assert kwargs["suppressed"] == 1
    assert kwargs["escalated"] == 2
    # log should have been called
    assert len(mock_vasomotor["logged"]) == 1


def test_amplify(complement_module, monkeypatch):
    """Amplify calls record_event with complement_amplification."""
    mock_record = Mock()
    monkeypatch.setattr(complement_module, "record_event", mock_record)
    result = complement_module.amplify("some_key")
    assert result is True
    mock_record.assert_called_once_with("complement_amplification", key="some_key")


def test_coverage_summary_empty(tmp_path):
    """No metabolon directory -> empty summary."""
    import metabolon.organelles.complement as comp_module
    # Temporarily monkeypatch Path.home? Not needed because coverage_summary uses project_root.
    result = comp_module.coverage_summary(project_root=tmp_path)
    assert result["total_modules"] == 0
    assert result["covered_modules"] == 0
    assert result["coverage_ratio"] == 0.0
    assert result["modules"] == []


def test_coverage_summary_with_modules(tmp_path):
    """Mock a metabolon directory with some Python files and test files."""
    import metabolon.organelles.complement as comp_module
    project_root = tmp_path / "proj"
    metabolon_dir = project_root / "metabolon"
    assays_dir = project_root / "assays"
    metabolon_dir.mkdir(parents=True)
    assays_dir.mkdir(parents=True)
    # Create a subdirectory with a .py file
    subdir = metabolon_dir / "organelles"
    subdir.mkdir()
    module_file = subdir / "complement.py"
    module_file.write_text("# dummy")
    # Create a test file (primary pattern)
    test_file = assays_dir / "test_complement.py"
    test_file.write_text("# dummy")
    # Another module without test
    module_file2 = subdir / "other.py"
    module_file2.write_text("# dummy")
    # Run coverage_summary
    result = comp_module.coverage_summary(project_root=project_root)
    assert result["total_modules"] == 2
    assert result["covered_modules"] == 1
    assert result["coverage_ratio"] == 0.5
    modules = result["modules"]
    assert len(modules) == 2
    comp_module_info = next(m for m in modules if m["name"] == "complement")
    assert comp_module_info["has_test"] is True
    assert comp_module_info["test_file"] == "test_complement.py"
    other_module = next(m for m in modules if m["name"] == "other")
    assert other_module["has_test"] is False
    assert other_module["test_file"] is None


def test_coverage_summary_secondary_pattern(tmp_path):
    """Test secondary pattern test_{subdir}_{module}.py."""
    import metabolon.organelles.complement as comp_module
    project_root = tmp_path / "proj"
    metabolon_dir = project_root / "metabolon"
    assays_dir = project_root / "assays"
    metabolon_dir.mkdir(parents=True)
    assays_dir.mkdir(parents=True)
    subdir = metabolon_dir / "organelles"
    subdir.mkdir()
    module_file = subdir / "complement.py"
    module_file.write_text("# dummy")
    # Secondary test file
    test_file = assays_dir / "test_organelles_complement.py"
    test_file.write_text("# dummy")
    result = comp_module.coverage_summary(project_root=project_root)
    assert result["total_modules"] == 1
    assert result["covered_modules"] == 1
    module = result["modules"][0]
    assert module["has_test"] is True
    assert module["test_file"] == "test_organelles_complement.py"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
