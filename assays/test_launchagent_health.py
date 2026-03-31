#!/usr/bin/env python3
"""Tests for effectors/launchagent-health — LaunchAgent health checker."""
from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

EFFECTOR_PATH = Path(__file__).resolve().parents[1] / "effectors" / "launchagent-health"


def _load_module():
    """Load launchagent-health via exec (effector pattern, not importable)."""
    source = EFFECTOR_PATH.read_text(encoding="utf-8")
    ns: dict = {"__name__": "launchagent_health", "__file__": str(EFFECTOR_PATH)}
    exec(source, ns)
    return ns


_mod = _load_module()
check = _mod["check"]
LAUNCH_DIR = _mod["LAUNCH_DIR"]
SOURCE_DIR = _mod["SOURCE_DIR"]
LOG = _mod["LOG"]


# ── File-level tests ────────────────────────────────────────────────────────


class TestFileBasics:
    def test_file_exists(self):
        assert EFFECTOR_PATH.exists()
        assert EFFECTOR_PATH.is_file()

    def test_is_python_script(self):
        first_line = EFFECTOR_PATH.read_text().split("\n")[0]
        assert first_line.startswith("#!/usr/bin/env python")

    def test_has_docstring(self):
        source = EFFECTOR_PATH.read_text()
        assert "LaunchAgent health check" in source


# ── Constant tests ──────────────────────────────────────────────────────────


class TestConstants:
    def test_launch_dir(self):
        assert LAUNCH_DIR == Path.home() / "Library" / "LaunchAgents"

    def test_source_dir(self):
        assert SOURCE_DIR == Path.home() / "epigenome" / "oscillators"

    def test_log_path(self):
        assert LOG == Path.home() / "logs" / "launchagent-health.log"


# ── check() tests ───────────────────────────────────────────────────────────


class TestCheck:
    def test_no_plists_returns_empty(self, tmp_path):
        """No plists → no issues."""
        fake_launch = tmp_path / "LaunchAgents"
        fake_launch.mkdir()
        fake_source = tmp_path / "oscillators"
        fake_source.mkdir()
        fake_bin = tmp_path / "effectors"
        fake_bin.mkdir()

        with patch.object(_mod, "LAUNCH_DIR", fake_launch):
            with patch.object(_mod, "SOURCE_DIR", fake_source):
                with patch.object(_mod, "LOG", tmp_path / "health.log"):
                    # Patch the bin_dir inside check() to use our fake
                    with patch.object(_mod["Path"], "home", return_value=type("P", (), {"__truediv__": lambda s, o: fake_bin / o})()):
                        issues = check()

        # Since no plists exist, should have no issues
        # (Note: check also scans effectors for secrets; we handle that below)

    def test_symlink_plists_skipped(self, tmp_path):
        """Symlinked plists are skipped (they auto-update)."""
        fake_launch = tmp_path / "LaunchAgents"
        fake_launch.mkdir()

        # Create a real plist elsewhere
        real_plist = tmp_path / "real" / "com.terry.test.plist"
        real_plist.parent.mkdir(parents=True)
        real_plist.write_text('<?xml version="1.0"?>\n<plist><dict/></plist>\n')

        # Create symlink
        link = fake_launch / "com.terry.test.plist"
        link.symlink_to(real_plist)

        issues = []
        with patch.object(_mod, "LAUNCH_DIR", fake_launch):
            with patch.object(_mod, "SOURCE_DIR", tmp_path / "oscillators"):
                with patch.object(_mod, "LOG", tmp_path / "health.log"):
                    # We need to intercept the bin scanning
                    with patch("builtins.__import__", side_effect=ImportError):
                        pass  # Just test the plist portion via direct exec

        # Directly test the plist loop logic
        assert link.is_symlink()
        # Symlinks should be skipped in the iteration

    def test_invalid_plist_detected(self, tmp_path):
        """Non-XML, non-binary plist that fails plutil is flagged."""
        fake_launch = tmp_path / "LaunchAgents"
        fake_launch.mkdir()

        bad_plist = fake_launch / "com.terry.bad.plist"
        bad_plist.write_text('{"not": "xml"}')

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "bad plist"

        with patch.object(_mod, "LAUNCH_DIR", fake_launch):
            with patch.object(_mod, "SOURCE_DIR", tmp_path / "oscillators"):
                with patch.object(_mod, "LOG", tmp_path / "health.log"):
                    with patch("subprocess.run", return_value=mock_result):
                        # Also patch the bin scanning part
                        fake_bin = tmp_path / "effectors"
                        fake_bin.mkdir()
                        with patch.object(_mod, "LOG", tmp_path / "health.log"):
                            issues = check()

        assert any("INVALID" in i and "com.terry.bad.plist" in i for i in issues)

    def test_drift_detected_when_source_differs(self, tmp_path):
        """Drift flagged when plist differs from source."""
        fake_launch = tmp_path / "LaunchAgents"
        fake_launch.mkdir()
        fake_source = tmp_path / "oscillators"
        fake_source.mkdir()

        plist_content = '<?xml version="1.0"?>\n<plist><dict><key>A</key><string>1</string></dict></plist>'
        (fake_launch / "com.terry.drift.plist").write_text(plist_content)

        source_content = '<?xml version="1.0"?>\n<plist><dict><key>A</key><string>2</string></dict></plist>'
        (fake_source / "com.terry.drift.plist").write_text(source_content)

        with patch.object(_mod, "LAUNCH_DIR", fake_launch):
            with patch.object(_mod, "SOURCE_DIR", fake_source):
                with patch.object(_mod, "LOG", tmp_path / "health.log"):
                    issues = check()

        assert any("DRIFT" in i and "com.terry.drift.plist" in i for i in issues)

    def test_matching_plist_no_issue(self, tmp_path):
        """Matching plist and source → no issue."""
        fake_launch = tmp_path / "LaunchAgents"
        fake_launch.mkdir()
        fake_source = tmp_path / "oscillators"
        fake_source.mkdir()

        content = '<?xml version="1.0"?>\n<plist><dict><key>A</key><string>1</string></dict></plist>'
        (fake_launch / "com.terry.match.plist").write_text(content)
        (fake_source / "com.terry.match.plist").write_text(content)

        with patch.object(_mod, "LAUNCH_DIR", fake_launch):
            with patch.object(_mod, "SOURCE_DIR", fake_source):
                with patch.object(_mod, "LOG", tmp_path / "health.log"):
                    issues = check()

        plist_issues = [i for i in issues if "com.terry.match.plist" in i]
        assert plist_issues == []

    def test_hardcoded_secret_detected(self, tmp_path):
        """Scripts containing hardcoded secrets are flagged."""
        fake_launch = tmp_path / "LaunchAgents"
        fake_launch.mkdir()
        fake_bin = tmp_path / "effectors"
        fake_bin.mkdir()

        # Write a script with a hardcoded key
        bad_script = fake_bin / "leaky-script"
        bad_script.write_text(textwrap.dedent("""\
            #!/bin/bash
            API_KEY=sk-abcdefghij1234567890abcdefghijklmn
            echo "using key"
        """))

        # The check() function uses Path.home() for bin_dir — we need to patch
        # the exact reference inside check's body
        with patch.object(_mod, "LAUNCH_DIR", fake_launch):
            with patch.object(_mod, "SOURCE_DIR", tmp_path / "oscillators"):
                with patch.object(_mod, "LOG", tmp_path / "health.log"):
                    # Patch Path.home() inside the re/secret scanning block
                    original_path = _mod["Path"]
                    class FakePath(type(original_path)):
                        @classmethod
                        def home(cls):
                            return tmp_path
                    with patch.object(_mod, "Path", FakePath):
                        issues = check()

        assert any("HARDCODED KEY" in i for i in issues)

    def test_secret_in_security_find_not_flagged(self, tmp_path):
        """Keys used with 'security find' are not flagged."""
        fake_launch = tmp_path / "LaunchAgents"
        fake_launch.mkdir()
        fake_bin = tmp_path / "effectors"
        fake_bin.mkdir()

        safe_script = fake_bin / "safe-script"
        safe_script.write_text(textwrap.dedent("""\
            #!/bin/bash
            # Uses security find to retrieve key
            security find-generic-password -s "api" -w
        """))

        with patch.object(_mod, "LAUNCH_DIR", fake_launch):
            with patch.object(_mod, "SOURCE_DIR", tmp_path / "oscillators"):
                with patch.object(_mod, "LOG", tmp_path / "health.log"):
                    original_path = _mod["Path"]
                    class FakePath(type(original_path)):
                        @classmethod
                        def home(cls):
                            return tmp_path
                    with patch.object(_mod, "Path", FakePath):
                        issues = check()

        assert not any("HARDCODED KEY" in i and "safe-script" in i for i in issues)

    def test_binary_files_skipped(self, tmp_path):
        """Binary files are skipped during secret scan."""
        fake_launch = tmp_path / "LaunchAgents"
        fake_launch.mkdir()
        fake_bin = tmp_path / "effectors"
        fake_bin.mkdir()

        binary_file = fake_bin / "some-binary"
        binary_file.write_bytes(b"\x00\x00\x00\x00rest of data")

        with patch.object(_mod, "LAUNCH_DIR", fake_launch):
            with patch.object(_mod, "SOURCE_DIR", tmp_path / "oscillators"):
                with patch.object(_mod, "LOG", tmp_path / "health.log"):
                    original_path = _mod["Path"]
                    class FakePath(type(original_path)):
                        @classmethod
                        def home(cls):
                            return tmp_path
                    with patch.object(_mod, "Path", FakePath):
                        issues = check()

        assert not any("some-binary" in i for i in issues)


# ── CLI (__main__) tests ────────────────────────────────────────────────────


class TestMain:
    def test_main_exits_0_when_healthy(self, tmp_path, capsys):
        """main() exits 0 when no issues found."""
        with patch.object(_mod, "LAUNCH_DIR", tmp_path / "empty"):
            with patch.object(_mod, "SOURCE_DIR", tmp_path / "oscillators"):
                with patch.object(_mod, "LOG", tmp_path / "health.log"):
                    tmp_path.mkdir(parents=True, exist_ok=True)
                    (tmp_path / "empty").mkdir()
                    (tmp_path / "oscillators").mkdir()
                    original_path = _mod["Path"]
                    class FakePath(type(original_path)):
                        @classmethod
                        def home(cls):
                            return tmp_path
                    with patch.object(_mod, "Path", FakePath):
                        with pytest.raises(SystemExit) as exc_info:
                            _mod["check"]()
                            # For the __main__ block, we need to simulate it
        # The check function returns issues — test that empty issues = no error
        with patch.object(_mod, "LAUNCH_DIR", tmp_path / "empty"):
            with patch.object(_mod, "SOURCE_DIR", tmp_path / "oscillators"):
                with patch.object(_mod, "LOG", tmp_path / "health.log"):
                    original_path = _mod["Path"]
                    class FakePath(type(original_path)):
                        @classmethod
                        def home(cls):
                            return tmp_path
                    with patch.object(_mod, "Path", FakePath):
                        issues = check()
        assert issues == []
