"""Tests for effectors/test-dashboard."""

from __future__ import annotations

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess
import re

DASHBOARD_SCRIPT = Path(__file__).parent.parent / "effectors" / "test-dashboard"


class TestDashboardOutput:
    """Integration tests for dashboard output."""
    
    def test_script_runs_successfully(self):
        """test-dashboard script executes without error."""
        result = subprocess.run(
            [str(DASHBOARD_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=120
        )
        assert result.returncode == 0
        assert "Total tests:" in result.stdout
        assert "Pass rate:" in result.stdout
        assert "Golem runs by provider:" in result.stdout
        assert "Recent trend" in result.stdout
        assert "Untested modules:" in result.stdout
    
    def test_outputs_total_tests(self):
        """Output includes total test count."""
        result = subprocess.run(
            [str(DASHBOARD_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=120
        )
        m = re.search(r"Total tests: (\d+)", result.stdout)
        assert m is not None
        total = int(m.group(1))
        assert total > 0
    
    def test_outputs_pass_rate_format(self):
        """Pass rate is formatted as percentage."""
        result = subprocess.run(
            [str(DASHBOARD_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=120
        )
        m = re.search(r"Pass rate: (\d+\.\d+)%", result.stdout)
        assert m is not None
        rate = float(m.group(1))
        assert 0 <= rate <= 100
    
    def test_outputs_provider_counts(self):
        """Output includes provider counts."""
        result = subprocess.run(
            [str(DASHBOARD_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=120
        )
        # Should have providers like infini, volcano, etc.
        assert "infini:" in result.stdout or "volcano:" in result.stdout or "unknown:" in result.stdout
    
    def test_outputs_recent_trend_entries(self):
        """Recent trend shows last 5 entries."""
        result = subprocess.run(
            [str(DASHBOARD_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=120
        )
        # Check for status indicators
        assert "✓" in result.stdout or "✗" in result.stdout
    
    def test_outputs_untested_count(self):
        """Output includes untested module count."""
        result = subprocess.run(
            [str(DASHBOARD_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=120
        )
        m = re.search(r"Untested modules: (\d+)", result.stdout)
        assert m is not None
        count = int(m.group(1))
        assert count >= 0


class TestGolemLogParsing:
    """Unit tests for golem.jsonl parsing logic."""
    
    def test_parse_valid_entry(self, tmp_path):
        """Parse valid JSONL entry correctly."""
        log_file = tmp_path / "golem.jsonl"
        entry = {
            "ts": "2026-03-31T08:00:00Z",
            "duration": 120,
            "exit": 0,
            "turns": 30,
            "provider": "infini",
            "prompt": "Test prompt",
            "tail": "Test output"
        }
        log_file.write_text(json.dumps(entry) + "\n")
        
        # Read and parse
        with open(log_file) as f:
            parsed = json.loads(f.readline().strip())
        
        assert parsed["provider"] == "infini"
        assert parsed["exit"] == 0
        assert parsed["duration"] == 120
    
    def test_parse_multiple_entries(self, tmp_path):
        """Parse multiple JSONL entries."""
        log_file = tmp_path / "golem.jsonl"
        entries = [
            {"ts": "t1", "exit": 0, "provider": "infini"},
            {"ts": "t2", "exit": 1, "provider": "volcano"},
            {"ts": "t3", "exit": 0, "provider": "infini"},
        ]
        log_file.write_text("\n".join(json.dumps(e) for e in entries) + "\n")
        
        # Read all
        parsed = []
        with open(log_file) as f:
            for line in f:
                if line.strip():
                    parsed.append(json.loads(line))
        
        assert len(parsed) == 3
    
    def test_handle_missing_provider(self, tmp_path):
        """Handle entry without provider field."""
        log_file = tmp_path / "golem.jsonl"
        entry = {"ts": "t1", "exit": 0}  # No provider
        log_file.write_text(json.dumps(entry) + "\n")
        
        with open(log_file) as f:
            parsed = json.loads(f.readline().strip())
        
        # Default to 'unknown'
        provider = parsed.get("provider", "unknown")
        assert provider == "unknown"


class TestPassRateCalculation:
    """Unit tests for pass rate calculation."""
    
    def test_all_passed(self):
        """100% pass rate when all succeed."""
        entries = [
            {"exit": 0}, {"exit": 0}, {"exit": 0}
        ]
        passed = sum(1 for e in entries if e.get("exit") == 0)
        rate = passed / len(entries) if entries else 0.0
        assert rate == 1.0
    
    def test_half_passed(self):
        """50% pass rate when half succeed."""
        entries = [
            {"exit": 0}, {"exit": 1}
        ]
        passed = sum(1 for e in entries if e.get("exit") == 0)
        rate = passed / len(entries) if entries else 0.0
        assert rate == 0.5
    
    def test_empty_entries(self):
        """0% pass rate for empty list."""
        entries = []
        passed = sum(1 for e in entries if e.get("exit") == 0)
        rate = passed / len(entries) if entries else 0.0
        assert rate == 0.0
    
    def test_nonzero_exit_codes(self):
        """Non-zero exit codes count as failures."""
        entries = [
            {"exit": 0}, {"exit": 1}, {"exit": 2}, {"exit": None}
        ]
        passed = sum(1 for e in entries if e.get("exit") == 0)
        rate = passed / len(entries) if entries else 0.0
        assert rate == 0.25


class TestProviderCounts:
    """Unit tests for provider counting."""
    
    def test_count_by_provider(self):
        """Count entries by provider correctly."""
        from collections import Counter
        entries = [
            {"provider": "infini", "exit": 0},
            {"provider": "volcano", "exit": 0},
            {"provider": "infini", "exit": 1},
            {"provider": "infini", "exit": 0},
        ]
        counts = Counter(e.get("provider", "unknown") for e in entries)
        assert counts["infini"] == 3
        assert counts["volcano"] == 1
    
    def test_missing_provider_uses_unknown(self):
        """Entries without provider use 'unknown'."""
        from collections import Counter
        entries = [
            {"exit": 0},  # No provider
            {"provider": "infini", "exit": 0},
        ]
        counts = Counter(e.get("provider", "unknown") for e in entries)
        assert counts["unknown"] == 1
        assert counts["infini"] == 1


class TestRecentTrend:
    """Unit tests for recent trend extraction."""
    
    def test_get_last_n(self):
        """Get last n entries correctly."""
        entries = [
            {"ts": "t1", "provider": "a"},
            {"ts": "t2", "provider": "b"},
            {"ts": "t3", "provider": "c"},
            {"ts": "t4", "provider": "d"},
        ]
        n = 2
        recent = entries[-n:] if len(entries) >= n else entries
        assert len(recent) == 2
        assert recent[0]["ts"] == "t3"
        assert recent[1]["ts"] == "t4"
    
    def test_truncate_prompt(self):
        """Truncate prompts > 50 chars."""
        long_prompt = "x" * 100
        truncated = long_prompt[:50] + "..." if len(long_prompt) > 50 else long_prompt
        assert len(truncated) == 53
        assert truncated.endswith("...")
    
    def test_short_prompt_unchanged(self):
        """Short prompts remain unchanged."""
        short_prompt = "test"
        truncated = short_prompt[:50] + "..." if len(short_prompt) > 50 else short_prompt
        assert truncated == "test"


class TestModuleDiscovery:
    """Unit tests for module discovery."""
    
    def test_find_py_files(self, tmp_path):
        """Find Python files in directory."""
        metabolon = tmp_path / "metabolon"
        metabolon.mkdir()
        (metabolon / "foo.py").write_text("")
        (metabolon / "bar.py").write_text("")
        (metabolon / "__init__.py").write_text("")
        
        modules = set()
        for f in metabolon.glob("*.py"):
            if f.name != "__init__.py":
                modules.add(f.stem)
        
        assert "foo" in modules
        assert "bar" in modules
        assert "__init__" not in modules
    
    def test_find_subdir_modules(self, tmp_path):
        """Find modules in subdirectories."""
        metabolon = tmp_path / "metabolon"
        metabolon.mkdir()
        enzymes = metabolon / "enzymes"
        enzymes.mkdir()
        (enzymes / "circadian.py").write_text("")
        (enzymes / "__init__.py").write_text("")
        
        modules = set()
        for subdir in metabolon.iterdir():
            if subdir.is_dir() and not subdir.name.startswith("__"):
                for f in subdir.glob("*.py"):
                    if f.name != "__init__.py":
                        modules.add(f"{subdir.name}/{f.stem}")
        
        assert "enzymes/circadian" in modules
    
    def test_extract_tested_modules(self, tmp_path):
        """Extract module names from test file names."""
        assays = tmp_path / "assays"
        assays.mkdir()
        (assays / "test_foo.py").write_text("")
        (assays / "test_bar_baz.py").write_text("")
        (assays / "conftest.py").write_text("")
        
        tested = set()
        for f in assays.glob("test_*.py"):
            name = f.stem[5:]  # Remove "test_" prefix
            if name:
                tested.add(name)
        
        assert "foo" in tested
        assert "bar_baz" in tested
        assert "conftest" not in tested


class TestPytestCollection:
    """Unit tests for pytest collection parsing."""
    
    def test_parse_test_lines(self):
        """Parse pytest --co -q output lines."""
        output = """assays/test_foo.py::TestFoo::test_one
assays/test_foo.py::TestFoo::test_two
assays/test_bar.py::test_standalone
"""
        from collections import defaultdict
        tests_per_file = defaultdict(int)
        total = 0
        
        for line in output.splitlines():
            m = re.match(r"^(assays/test_.*\.py)::", line)
            if m:
                test_file = m.group(1)
                tests_per_file[test_file] += 1
                total += 1
        
        assert total == 3
        assert tests_per_file["assays/test_foo.py"] == 2
        assert tests_per_file["assays/test_bar.py"] == 1
    
    def test_ignore_non_test_lines(self):
        """Ignore lines that don't match test pattern."""
        output = """some other output
assays/test_foo.py::test_one
=== 1 test collected ===
"""
        total = 0
        for line in output.splitlines():
            m = re.match(r"^(assays/test_.*\.py)::", line)
            if m:
                total += 1
        
        assert total == 1
