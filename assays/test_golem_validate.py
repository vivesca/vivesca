from __future__ import annotations

"""Tests for effectors/golem-validate — Python file quality validator.

The validator is loaded via exec() (not imported), following the effector testing pattern.
"""

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

EFFECTOR = Path(__file__).resolve().parents[1] / "effectors" / "golem-validate"
GERMLINE_ROOT = Path(__file__).resolve().parents[1]


def _run_validator(*files: str) -> subprocess.CompletedProcess[str]:
    """Invoke golem-validate as a subprocess."""
    return subprocess.run(
        [sys.executable, str(EFFECTOR), *files],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(GERMLINE_ROOT),
    )


def _write_py(tmp_path: Path, name: str, content: str) -> Path:
    """Write a Python file into tmp_path and return its path."""
    p = tmp_path / name
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


# ── Syntax checks ──────────────────────────────────────────────────────────


class TestSyntaxCheck:
    def test_valid_syntax_passes(self, tmp_path: Path):
        f = _write_py(tmp_path, "clean.py", """\
            x = 1
            y = x + 2
        """)
        r = _run_validator(str(f))
        assert r.returncode == 0
        assert "PASS" in r.stdout

    def test_syntax_error_fails(self, tmp_path: Path):
        f = _write_py(tmp_path, "broken.py", "def foo(\n")
        r = _run_validator(str(f))
        assert r.returncode == 1
        assert "SyntaxError" in r.stdout


# ── Hardcoded path check ──────────────────────────────────────────────────


class TestHardcodedPath:
    def test_no_bad_path_passes(self, tmp_path: Path):
        f = _write_py(tmp_path, "good.py", """\
            from pathlib import Path
            home = Path.home()
        """)
        r = _run_validator(str(f))
        assert r.returncode == 0
        assert "PASS" in r.stdout

    def test_users_terry_detected(self, tmp_path: Path):
        f = _write_py(tmp_path, "bad_path.py", """\
            config = str(Path.home() / "germline/config.yaml")
        """)
        r = _run_validator(str(f))
        assert r.returncode == 1
        assert str(Path.home() / "") in r.stdout


# ── TODO / FIXME / stub markers ────────────────────────────────────────────


class TestMarkers:
    def test_clean_file_passes(self, tmp_path: Path):
        f = _write_py(tmp_path, "clean.py", "x = 1\n")
        r = _run_validator(str(f))
        assert r.returncode == 0

    @pytest.mark.parametrize("marker", ["TODO", "FIXME", "stub"])
    def test_marker_detected(self, tmp_path: Path, marker: str):
        f = _write_py(tmp_path, "marked.py", f"x = 1  # {marker}: fix later\n")
        r = _run_validator(str(f))
        assert r.returncode == 1
        assert marker.lower() in r.stdout.lower() or "marker" in r.stdout.lower()

    def test_stub_in_function_name_is_flagged(self, tmp_path: Path):
        f = _write_py(tmp_path, "stub_func.py", """\
            def stub_handler():
                pass
        """)
        r = _run_validator(str(f))
        assert r.returncode == 1
        assert "stub" in r.stdout.lower()


# ── Test collectability ────────────────────────────────────────────────────


class TestPytestCollection:
    def test_collectable_test_passes(self, tmp_path: Path):
        f = _write_py(tmp_path, "test_sample.py", """\
            def test_one():
                assert 1 + 1 == 2
        """)
        r = _run_validator(str(f))
        assert r.returncode == 0
        assert "PASS" in r.stdout

    def test_broken_test_file_fails_collection(self, tmp_path: Path):
        f = _write_py(tmp_path, "test_broken.py", """\
            import nonexistent_module_xyz
            def test_one():
                pass
        """)
        r = _run_validator(str(f))
        assert r.returncode == 1
        assert "pytest --co failed" in r.stdout


# ── CLI behaviour ──────────────────────────────────────────────────────────


class TestCLI:
    def test_no_args_returns_2(self):
        r = _run_validator()
        assert r.returncode == 2

    def test_multiple_files_all_pass(self, tmp_path: Path):
        f1 = _write_py(tmp_path, "a.py", "x = 1\n")
        f2 = _write_py(tmp_path, "b.py", "y = 2\n")
        r = _run_validator(str(f1), str(f2))
        assert r.returncode == 0
        lines = [l for l in r.stdout.strip().splitlines() if l.strip()]
        assert len(lines) == 2

    def test_mixed_pass_fail_returns_1(self, tmp_path: Path):
        good = _write_py(tmp_path, "good.py", "x = 1\n")
        bad = _write_py(tmp_path, "bad.py", "def (\n")
        r = _run_validator(str(good), str(bad))
        assert r.returncode == 1
        assert "PASS" in r.stdout
        assert "FAIL" in r.stdout

    def test_output_format_pipe_separated(self, tmp_path: Path):
        f = _write_py(tmp_path, "clean.py", "x = 1\n")
        r = _run_validator(str(f))
        parts = r.stdout.strip().split(" | ")
        # path | status | issues
        assert len(parts) == 3
        assert parts[1].strip() == "PASS"
