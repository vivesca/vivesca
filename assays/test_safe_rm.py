#!/usr/bin/env python3
"""Tests for effectors/safe_rm.py — safe rm wrapper with protected paths.

safe_rm.py is a script (effectors/safe_rm.py), not an importable module.
It is loaded via exec() into isolated namespaces.
"""

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SAFE_RM_PATH = Path(__file__).resolve().parents[1] / "effectors" / "safe_rm.py"


# ── Fixture ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def safe():
    """Load safe_rm via exec into an isolated namespace."""
    ns: dict = {"__name__": "test_safe_rm", "__file__": str(SAFE_RM_PATH)}
    source = SAFE_RM_PATH.read_text(encoding="utf-8")
    exec(source, ns)
    mod = type("safe_rm", (), {})()
    for k, v in ns.items():
        if not k.startswith("__"):
            setattr(mod, k, v)
    mod._ns = ns
    return mod


# ── File structure tests ───────────────────────────────────────────────────


class TestSafeRmBasics:
    def test_file_exists(self):
        """Test that safe_rm.py effector file exists."""
        assert SAFE_RM_PATH.exists()
        assert SAFE_RM_PATH.is_file()

    def test_is_python_script(self):
        """Test that safe_rm.py has Python shebang."""
        first_line = SAFE_RM_PATH.read_text().split("\n")[0]
        assert first_line.startswith("#!/")
        assert "python" in first_line.lower()

    def test_has_docstring(self):
        """Test that safe_rm.py has docstring."""
        content = SAFE_RM_PATH.read_text()
        assert '"""' in content

    def test_docstring_mentions_protected(self):
        """Test docstring mentions protected paths."""
        content = SAFE_RM_PATH.read_text()
        assert "protected" in content.lower()


# ── PROTECTED_PATHS ────────────────────────────────────────────────────────


class TestProtectedPaths:
    def test_home_is_protected(self, safe):
        """Test ~ (home) is in protected paths."""
        expanded = [os.path.expanduser(p) for p in safe.PROTECTED_PATHS]
        assert os.path.expanduser("~") in expanded

    def test_ssh_is_protected(self, safe):
        """Test ~/.ssh is in protected paths."""
        assert "~/.ssh" in safe.PROTECTED_PATHS or os.path.expanduser("~/.ssh") in safe.PROTECTED_PATHS

    def test_gnupg_is_protected(self, safe):
        """Test ~/.gnupg is in protected paths."""
        assert "~/.gnupg" in safe.PROTECTED_PATHS or os.path.expanduser("~/.gnupg") in safe.PROTECTED_PATHS

    def test_root_is_protected(self, safe):
        """Test / is in protected paths."""
        assert "/" in safe.PROTECTED_PATHS

    def test_users_is_protected(self, safe):
        """Test /Users is in protected paths."""
        assert "/Users" in safe.PROTECTED_PATHS

    def test_has_multiple_protected_paths(self, safe):
        """Test there are multiple protected paths."""
        assert len(safe.PROTECTED_PATHS) >= 5


# ── is_protected() ─────────────────────────────────────────────────────────


class TestIsProtected:
    def test_exact_home_is_protected(self, safe):
        """Home directory exactly should be protected."""
        assert safe.is_protected("~") is True

    def test_exact_root_is_protected(self, safe):
        """Root directory should be protected."""
        assert safe.is_protected("/") is True

    def test_exact_ssh_is_protected(self, safe):
        """~/.ssh should be protected."""
        assert safe.is_protected("~/.ssh") is True

    def test_exact_gnupg_is_protected(self, safe):
        """~/.gnupg should be protected."""
        assert safe.is_protected("~/.gnupg") is True

    def test_parent_of_protected_is_protected(self, safe):
        """A parent of a protected path should also be protected.
        E.g. deleting / would delete ~/.ssh — so / is blocked."""
        assert safe.is_protected("/") is True

    def test_tmp_is_not_protected(self, safe):
        """A normal tmp path should not be protected."""
        assert safe.is_protected("/tmp/some_random_dir") is False

    def test_nested_unprotected_path(self, safe):
        """A deeply nested non-protected path should not be protected."""
        assert safe.is_protected("/tmp/a/b/c/d") is False

    def test_home_expansion(self, safe):
        """Paths with ~ should be expanded before checking."""
        assert safe.is_protected("~") is True

    def test_relative_path_resolved(self, safe):
        """Relative paths should be resolved to absolute before checking."""
        assert safe.is_protected("some_random_file.txt") is False

    def test_users_terry_is_protected(self, safe):
        """/Users/terry should be protected."""
        assert safe.is_protected("/Users/terry") is True

    def test_var_tmp_not_protected(self, safe):
        """/var/tmp should not be protected."""
        assert safe.is_protected("/var/tmp") is False


# ── main() ─────────────────────────────────────────────────────────────────


class TestMain:
    def test_no_args_exits(self, safe, monkeypatch):
        """Should exit 1 when no path provided."""
        monkeypatch.setattr(sys, "argv", ["safe_rm.py"])
        with pytest.raises(SystemExit) as exc_info:
            safe.main()
        assert exc_info.value.code == 1

    def test_no_args_shows_usage(self, safe, monkeypatch, capsys):
        """Should print usage when no path provided."""
        monkeypatch.setattr(sys, "argv", ["safe_rm.py"])
        with pytest.raises(SystemExit):
            safe.main()
        out = capsys.readouterr().out
        assert "Usage" in out

    def test_protected_path_blocked(self, safe, monkeypatch, capsys):
        """Should block deletion of protected path and exit 1."""
        monkeypatch.setattr(sys, "argv", ["safe_rm.py", "~/.ssh"])
        with pytest.raises(SystemExit) as exc_info:
            safe.main()
        assert exc_info.value.code == 1
        out = capsys.readouterr().out
        assert "BLOCKED" in out

    def test_root_blocked(self, safe, monkeypatch, capsys):
        """Should block deletion of / and exit 1."""
        monkeypatch.setattr(sys, "argv", ["safe_rm.py", "/"])
        with pytest.raises(SystemExit) as exc_info:
            safe.main()
        assert exc_info.value.code == 1
        out = capsys.readouterr().out
        assert "BLOCKED" in out

    def test_safe_path_printed(self, safe, monkeypatch, capsys):
        """Should print absolute path of safe path and exit 0."""
        monkeypatch.setattr(sys, "argv", ["safe_rm.py", "/tmp/some_dir"])
        with pytest.raises(SystemExit) as exc_info:
            safe.main()
        assert exc_info.value.code == 0
        out = capsys.readouterr().out
        assert "/tmp/some_dir" in out

    def test_multiple_safe_paths(self, safe, monkeypatch, capsys):
        """Should print all safe paths."""
        monkeypatch.setattr(sys, "argv", ["safe_rm.py", "/tmp/a", "/tmp/b"])
        with pytest.raises(SystemExit) as exc_info:
            safe.main()
        assert exc_info.value.code == 0
        out = capsys.readouterr().out
        assert "/tmp/a" in out
        assert "/tmp/b" in out

    def test_mixed_paths_blocked_on_first_protected(self, safe, monkeypatch, capsys):
        """Should block when first protected path encountered."""
        monkeypatch.setattr(sys, "argv", ["safe_rm.py", "/tmp/ok", "~/.ssh", "/tmp/also_ok"])
        with pytest.raises(SystemExit) as exc_info:
            safe.main()
        assert exc_info.value.code == 1

    def test_home_blocked(self, safe, monkeypatch, capsys):
        """Should block deletion of home directory."""
        monkeypatch.setattr(sys, "argv", ["safe_rm.py", "~"])
        with pytest.raises(SystemExit) as exc_info:
            safe.main()
        assert exc_info.value.code == 1

    def test_block_message_mentions_manual(self, safe, monkeypatch, capsys):
        """Block message should mention doing it manually."""
        monkeypatch.setattr(sys, "argv", ["safe_rm.py", "/"])
        with pytest.raises(SystemExit):
            safe.main()
        out = capsys.readouterr().out
        assert "manually" in out.lower()

    def test_block_message_shows_emoji(self, safe, monkeypatch, capsys):
        """Block message should show ❌ emoji."""
        monkeypatch.setattr(sys, "argv", ["safe_rm.py", "/"])
        with pytest.raises(SystemExit):
            safe.main()
        out = capsys.readouterr().out
        assert "❌" in out


# ── CLI subprocess ──────────────────────────────────────────────────────────


class TestCLISubprocess:
    def test_no_args_exits_nonzero(self):
        """Running safe_rm.py with no args should exit nonzero."""
        r = subprocess.run(
            [sys.executable, str(SAFE_RM_PATH)],
            capture_output=True, text=True, timeout=30,
        )
        assert r.returncode != 0
        assert "Usage" in r.stdout

    def test_protected_path_blocked(self):
        """Running safe_rm.py with / should exit nonzero."""
        r = subprocess.run(
            [sys.executable, str(SAFE_RM_PATH), "/"],
            capture_output=True, text=True, timeout=30,
        )
        assert r.returncode != 0
        assert "BLOCKED" in r.stdout

    def test_safe_path_succeeds(self):
        """Running safe_rm.py with /tmp/safe_rm_test_xyz should succeed."""
        r = subprocess.run(
            [sys.executable, str(SAFE_RM_PATH), "/tmp/safe_rm_test_xyz_12345"],
            capture_output=True, text=True, timeout=30,
        )
        assert r.returncode == 0
        assert "/tmp/safe_rm_test_xyz_12345" in r.stdout

    def test_ssh_blocked(self):
        """Running safe_rm.py with ~/.ssh should exit nonzero."""
        r = subprocess.run(
            [sys.executable, str(SAFE_RM_PATH), "~/.ssh"],
            capture_output=True, text=True, timeout=30,
        )
        assert r.returncode != 0
        assert "BLOCKED" in r.stdout
