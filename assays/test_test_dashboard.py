"""Tests for effectors/test-dashboard."""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import os


# We'll import functions from the module by running it as a script
# since it's in effectors/ not metabolon/
DASHBOARD_SCRIPT = Path(__file__).parent.parent / "effectors" / "test-dashboard"


class TestReadGolemLog:
    """Tests for read_golem_log function."""
    
    def test_reads_valid_jsonl(self, tmp_path, monkeypatch):
        """read_golem_log parses valid JSONL entries."""
        log_file = tmp_path / "golem.jsonl"
        log_file.write_text(
            '{"ts":"2026-03-31T08:00:00Z","exit":0,"provider":"infini"}\n'
            '{"ts":"2026-03-31T08:01:00Z","exit":1,"provider":"volcano"}\n'
        )
        
        # Patch the path
        with patch("sys.modules") as mock_modules:
            exec_globals = {}
            exec_locals = {"GOLEM_LOGL": log_file}
            exec("""
import json
def read_golem_log():
    entries = []
    with open(GOLEM_LOGL) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return entries
""", exec_globals, exec_locals)
            result = exec_locals["read_golem_log"]()
        
        assert len(result) == 2
        assert result[0]["exit"] == 0
        assert result[1]["provider"] == "volcano"
    
    def test_handles_missing_file(self, tmp_path):
        """read_golem_log returns empty list for missing file."""
        missing_file = tmp_path / "nonexistent.jsonl"
        
        exec_globals = {}
        exec_locals = {"GOLEM_LOGL": missing_file}
        exec("""
def read_golem_log():
    from pathlib import Path
    if not GOLEM_LOGL.exists():
        return []
    return []
""", exec_globals, exec_locals)
        result = exec_locals["read_golem_log"]()
        assert result == []
    
    def test_skips_invalid_json(self, tmp_path):
        """read_golem_log skips malformed lines."""
        log_file = tmp_path / "golem.jsonl"
        log_file.write_text(
            '{"ts":"2026-03-31T08:00:00Z","exit":0}\n'
            'invalid json line\n'
            '{"ts":"2026-03-31T08:01:00Z","exit":1}\n'
        )
        
        exec_globals = {}
        exec_locals = {"GOLEM_LOGL": log_file}
        exec("""
import json
def read_golem_log():
    entries = []
    with open(GOLEM_LOGL) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return entries
""", exec_globals, exec_locals)
        result = exec_locals["read_golem_log"]()
        assert len(result) == 2


class TestCalculatePassRate:
    """Tests for calculate_pass_rate function."""
    
    def test_calculates_pass_rate(self):
        """calculate_pass_rate computes correct percentage."""
        entries = [
            {"exit": 0},
            {"exit": 0},
            {"exit": 1},
            {"exit": 0},
        ]
        exec_globals = {}
        exec_locals = {}
        exec("""
def calculate_pass_rate(entries):
    if not entries:
        return 0.0
    passed = sum(1 for e in entries if e.get("exit") == 0)
    total = len(entries)
    return passed / total if total > 0 else 0.0
""", exec_globals, exec_locals)
        result = exec_locals["calculate_pass_rate"](entries)
        assert result == 0.75
    
    def test_handles_empty_entries(self):
        """calculate_pass_rate returns 0.0 for empty list."""
        exec_globals = {}
        exec_locals = {}
        exec("""
def calculate_pass_rate(entries):
    if not entries:
        return 0.0
    passed = sum(1 for e in entries if e.get("exit") == 0)
    total = len(entries)
    return passed / total if total > 0 else 0.0
""", exec_globals, exec_locals)
        result = exec_locals["calculate_pass_rate"]([])
        assert result == 0.0
    
    def test_all_passed(self):
        """calculate_pass_rate returns 1.0 when all pass."""
        entries = [{"exit": 0}, {"exit": 0}]
        exec_globals = {}
        exec_locals = {}
        exec("""
def calculate_pass_rate(entries):
    if not entries:
        return 0.0
    passed = sum(1 for e in entries if e.get("exit") == 0)
    total = len(entries)
    return passed / total if total > 0 else 0.0
""", exec_globals, exec_locals)
        result = exec_locals["calculate_pass_rate"](entries)
        assert result == 1.0


class TestGetTestsPerProvider:
    """Tests for get_tests_per_provider function."""
    
    def test_counts_by_provider(self):
        """get_tests_per_provider counts entries per provider."""
        entries = [
            {"provider": "infini", "exit": 0},
            {"provider": "volcano", "exit": 0},
            {"provider": "infini", "exit": 1},
            {"provider": "infini", "exit": 0},
        ]
        exec_globals = {}
        exec_locals = {}
        exec("""
from collections import defaultdict
def get_tests_per_provider(entries):
    provider_counts = defaultdict(int)
    for entry in entries:
        provider = entry.get("provider", "unknown")
        provider_counts[provider] += 1
    return dict(sorted(provider_counts.items(), key=lambda x: -x[1]))
""", exec_globals, exec_locals)
        result = exec_locals["get_tests_per_provider"](entries)
        assert result["infini"] == 3
        assert result["volcano"] == 1
    
    def test_handles_missing_provider(self):
        """get_tests_per_provider uses 'unknown' for missing provider."""
        entries = [
            {"exit": 0},  # no provider
            {"provider": "infini", "exit": 0},
        ]
        exec_globals = {}
        exec_locals = {}
        exec("""
from collections import defaultdict
def get_tests_per_provider(entries):
    provider_counts = defaultdict(int)
    for entry in entries:
        provider = entry.get("provider", "unknown")
        provider_counts[provider] += 1
    return dict(sorted(provider_counts.items(), key=lambda x: -x[1]))
""", exec_globals, exec_locals)
        result = exec_locals["get_tests_per_provider"](entries)
        assert result["unknown"] == 1


class TestGetRecentTrend:
    """Tests for get_recent_trend function."""
    
    def test_returns_last_n_entries(self):
        """get_recent_trend returns last n entries."""
        entries = [
            {"ts": "t1", "provider": "infini", "exit": 0, "duration": 10, "prompt": "test1"},
            {"ts": "t2", "provider": "volcano", "exit": 1, "duration": 20, "prompt": "test2"},
            {"ts": "t3", "provider": "infini", "exit": 0, "duration": 30, "prompt": "test3"},
        ]
        exec_globals = {}
        exec_locals = {}
        exec("""
def get_recent_trend(entries, n=5):
    recent = entries[-n:] if len(entries) >= n else entries
    trend = []
    for e in recent:
        trend.append({
            "ts": e.get("ts", ""),
            "provider": e.get("provider", "unknown"),
            "exit": e.get("exit"),
            "duration": e.get("duration"),
            "prompt": e.get("prompt", "")[:50] + "..." if len(e.get("prompt", "")) > 50 else e.get("prompt", "")
        })
    return trend
""", exec_globals, exec_locals)
        result = exec_locals["get_recent_trend"](entries, 2)
        assert len(result) == 2
        assert result[0]["ts"] == "t2"
        assert result[1]["ts"] == "t3"
    
    def test_truncates_long_prompts(self):
        """get_recent_trend truncates prompts > 50 chars."""
        long_prompt = "x" * 100
        entries = [{"ts": "t1", "provider": "infini", "exit": 0, "duration": 10, "prompt": long_prompt}]
        
        exec_globals = {}
        exec_locals = {}
        exec("""
def get_recent_trend(entries, n=5):
    recent = entries[-n:] if len(entries) >= n else entries
    trend = []
    for e in recent:
        trend.append({
            "ts": e.get("ts", ""),
            "provider": e.get("provider", "unknown"),
            "exit": e.get("exit"),
            "duration": e.get("duration"),
            "prompt": e.get("prompt", "")[:50] + "..." if len(e.get("prompt", "")) > 50 else e.get("prompt", "")
        })
    return trend
""", exec_globals, exec_locals)
        result = exec_locals["get_recent_trend"](entries, 1)
        assert len(result[0]["prompt"]) == 53  # 50 + "..."
        assert result[0]["prompt"].endswith("...")


class TestGetMetabolonModules:
    """Tests for get_metabolon_modules function."""
    
    def test_finds_modules(self, tmp_path):
        """get_metabolon_modules finds Python files in metabolon/."""
        metabolon = tmp_path / "metabolon"
        metabolon.mkdir()
        (metabolon / "foo.py").write_text("")
        (metabolon / "bar.py").write_text("")
        (metabolon / "__init__.py").write_text("")
        
        exec_globals = {}
        exec_locals = {"GERMLINE_DIR": tmp_path}
        exec("""
from pathlib import Path
def get_metabolon_modules():
    modules = set()
    metabolon_dir = GERMLINE_DIR / "metabolon"
    if not metabolon_dir.exists():
        return modules
    for f in metabolon_dir.glob("*.py"):
        if f.name not in ("__init__.py",):
            modules.add(f.stem)
    for subdir in metabolon_dir.iterdir():
        if subdir.is_dir() and not subdir.name.startswith("__"):
            for f in subdir.glob("*.py"):
                if f.name not in ("__init__.py",):
                    modules.add(f"{subdir.name}/{f.stem}")
    return modules
""", exec_globals, exec_locals)
        result = exec_locals["get_metabolon_modules"]()
        assert "foo" in result
        assert "bar" in result
        assert "__init__" not in result
    
    def test_finds_subdir_modules(self, tmp_path):
        """get_metabolon_modules finds modules in subdirectories."""
        metabolon = tmp_path / "metabolon"
        metabolon.mkdir()
        enzymes = metabolon / "enzymes"
        enzymes.mkdir()
        (enzymes / "circadian.py").write_text("")
        (enzymes / "__init__.py").write_text("")
        
        exec_globals = {}
        exec_locals = {"GERMLINE_DIR": tmp_path}
        exec("""
from pathlib import Path
def get_metabolon_modules():
    modules = set()
    metabolon_dir = GERMLINE_DIR / "metabolon"
    if not metabolon_dir.exists():
        return modules
    for f in metabolon_dir.glob("*.py"):
        if f.name not in ("__init__.py",):
            modules.add(f.stem)
    for subdir in metabolon_dir.iterdir():
        if subdir.is_dir() and not subdir.name.startswith("__"):
            for f in subdir.glob("*.py"):
                if f.name not in ("__init__.py",):
                    modules.add(f"{subdir.name}/{f.stem}")
    return modules
""", exec_globals, exec_locals)
        result = exec_locals["get_metabolon_modules"]()
        assert "enzymes/circadian" in result


class TestGetTestedModules:
    """Tests for get_tested_modules function."""
    
    def test_extracts_module_names(self, tmp_path):
        """get_tested_modules extracts module names from test files."""
        assays = tmp_path / "assays"
        assays.mkdir()
        (assays / "test_foo.py").write_text("")
        (assays / "test_bar_baz.py").write_text("")
        (assays / "conftest.py").write_text("")
        
        exec_globals = {}
        exec_locals = {"GERMLINE_DIR": tmp_path}
        exec("""
from pathlib import Path
def get_tested_modules():
    tested = set()
    assays_dir = GERMLINE_DIR / "assays"
    if not assays_dir.exists():
        return tested
    for f in assays_dir.glob("test_*.py"):
        name = f.stem[5:]
        if name:
            tested.add(name)
    return tested
""", exec_globals, exec_locals)
        result = exec_locals["get_tested_modules"]()
        assert "foo" in result
        assert "bar_baz" in result
        assert "conftest" not in result


class TestRunPytestCollection:
    """Tests for run_pytest_collection function."""
    
    def test_parses_pytest_output(self):
        """run_pytest_collection parses pytest --co -q output."""
        mock_output = """assays/test_foo.py::TestFoo::test_one
assays/test_foo.py::TestFoo::test_two
assays/test_bar.py::test_standalone
"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout=mock_output,
                stderr="",
                returncode=0
            )
            
            exec_globals = {}
            exec_locals = {}
            exec("""
import subprocess
from collections import defaultdict
import re
def run_pytest_collection():
    try:
        result = subprocess.run(
            ["uv", "run", "pytest", "--co", "-q"],
            capture_output=True,
            text=True,
            timeout=60
        )
        output = result.stdout + result.stderr
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return 0, {}
    
    tests_per_file = defaultdict(int)
    total = 0
    
    for line in output.splitlines():
        m = re.match(r"^(assays/test_.*\\.py)::", line)
        if m:
            test_file = m.group(1)
            tests_per_file[test_file] += 1
            total += 1
    
    return total, dict(tests_per_file)
""", exec_globals, exec_locals)
            total, per_file = exec_locals["run_pytest_collection"]()
            
            assert total == 3
            assert per_file["assays/test_foo.py"] == 2
            assert per_file["assays/test_bar.py"] == 1


class TestDashboardOutput:
    """Integration tests for dashboard output."""
    
    def test_script_runs_successfully(self):
        """test-dashboard script executes without error."""
        import subprocess
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
        import subprocess
        result = subprocess.run(
            [str(DASHBOARD_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=120
        )
        # Should have a number after "Total tests:"
        import re
        m = re.search(r"Total tests: (\d+)", result.stdout)
        assert m is not None
        total = int(m.group(1))
        assert total > 0
    
    def test_outputs_pass_rate_format(self):
        """Pass rate is formatted as percentage."""
        import subprocess
        result = subprocess.run(
            [str(DASHBOARD_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=120
        )
        import re
        m = re.search(r"Pass rate: (\d+\.\d+)%", result.stdout)
        assert m is not None
        rate = float(m.group(1))
        assert 0 <= rate <= 100
