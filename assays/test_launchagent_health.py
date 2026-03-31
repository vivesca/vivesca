#!/usr/bin/env python3
"""Tests for effectors/launchagent-health — LaunchAgent health checker."""
from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

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
    def test_no_plists_no_issues(self, monkeypatch, tmp_path):
        """No plists and clean effectors → no issues."""
        fake_launch = tmp_path / "LaunchAgents"
        fake_launch.mkdir()
        fake_source = tmp_path / "oscillators"
        fake_source.mkdir()
        fake_bin = tmp_path / "effectors"
        fake_bin.mkdir()

        monkeypatch.setitem(_mod, "LAUNCH_DIR", fake_launch)
        monkeypatch.setitem(_mod, "SOURCE_DIR", fake_source)
        monkeypatch.setitem(_mod, "LOG", tmp_path / "health.log")

        # Patch Path.home() used inside check() for bin_dir
        _orig_path = _mod["Path"]
        class FakePath(_orig_path):
            @classmethod
            def home(cls):
                return tmp_path
        monkeypatch.setitem(_mod, "Path", FakePath)

        issues = check()
        assert issues == []

    def test_symlink_plists_skipped(self, monkeypatch, tmp_path):
        """Symlinked plists are not checked (they auto-update)."""
        fake_launch = tmp_path / "LaunchAgents"
        fake_launch.mkdir()
        fake_source = tmp_path / "oscillators"
        fake_source.mkdir()
        fake_bin = tmp_path / "effectors"
        fake_bin.mkdir()

        # Create real plist and symlink to it
        real_dir = tmp_path / "real"
        real_dir.mkdir()
        real_plist = real_dir / "com.terry.test.plist"
        real_plist.write_text("garbage")
        link = fake_launch / "com.terry.test.plist"
        link.symlink_to(real_plist)

        monkeypatch.setitem(_mod, "LAUNCH_DIR", fake_launch)
        monkeypatch.setitem(_mod, "SOURCE_DIR", fake_source)
        monkeypatch.setitem(_mod, "LOG", tmp_path / "health.log")

        _orig_path = _mod["Path"]
        class FakePath(_orig_path):
            @classmethod
            def home(cls):
                return tmp_path
        monkeypatch.setitem(_mod, "Path", FakePath)

        issues = check()
        plist_issues = [i for i in issues if "com.terry.test.plist" in i]
        assert plist_issues == []

    def test_invalid_plist_detected(self, monkeypatch, tmp_path):
        """Non-XML, non-binary plist that fails plutil is flagged INVALID."""
        fake_launch = tmp_path / "LaunchAgents"
        fake_launch.mkdir()
        fake_bin = tmp_path / "effectors"
        fake_bin.mkdir()

        bad_plist = fake_launch / "com.terry.bad.plist"
        bad_plist.write_text('{"not": "xml"}')

        monkeypatch.setitem(_mod, "LAUNCH_DIR", fake_launch)
        monkeypatch.setitem(_mod, "SOURCE_DIR", tmp_path / "oscillators")
        monkeypatch.setitem(_mod, "LOG", tmp_path / "health.log")

        _orig_path = _mod["Path"]
        class FakePath(_orig_path):
            @classmethod
            def home(cls):
                return tmp_path
        monkeypatch.setitem(_mod, "Path", FakePath)

        mock_result = MagicMock(returncode=1, stderr="bad plist")
        with patch("subprocess.run", return_value=mock_result):
            issues = check()

        assert any("INVALID" in i and "com.terry.bad.plist" in i for i in issues)

    def test_drift_detected_when_source_differs(self, monkeypatch, tmp_path):
        """Drift flagged when plist differs from source."""
        fake_launch = tmp_path / "LaunchAgents"
        fake_launch.mkdir()
        fake_source = tmp_path / "oscillators"
        fake_source.mkdir()
        fake_bin = tmp_path / "effectors"
        fake_bin.mkdir()

        plist_content = '<?xml version="1.0"?>\n<plist><dict><key>A</key><string>1</string></dict></plist>'
        (fake_launch / "com.terry.drift.plist").write_text(plist_content)
        source_content = '<?xml version="1.0"?>\n<plist><dict><key>A</key><string>2</string></dict></plist>'
        (fake_source / "com.terry.drift.plist").write_text(source_content)

        monkeypatch.setitem(_mod, "LAUNCH_DIR", fake_launch)
        monkeypatch.setitem(_mod, "SOURCE_DIR", fake_source)
        monkeypatch.setitem(_mod, "LOG", tmp_path / "health.log")

        _orig_path = _mod["Path"]
        class FakePath(_orig_path):
            @classmethod
            def home(cls):
                return tmp_path
        monkeypatch.setitem(_mod, "Path", FakePath)

        issues = check()
        assert any("DRIFT" in i and "com.terry.drift.plist" in i for i in issues)

    def test_matching_plist_no_issue(self, monkeypatch, tmp_path):
        """Matching plist and source → no issue."""
        fake_launch = tmp_path / "LaunchAgents"
        fake_launch.mkdir()
        fake_source = tmp_path / "oscillators"
        fake_source.mkdir()
        fake_bin = tmp_path / "effectors"
        fake_bin.mkdir()

        content = '<?xml version="1.0"?>\n<plist><dict><key>A</key><string>1</string></dict></plist>'
        (fake_launch / "com.terry.match.plist").write_text(content)
        (fake_source / "com.terry.match.plist").write_text(content)

        monkeypatch.setitem(_mod, "LAUNCH_DIR", fake_launch)
        monkeypatch.setitem(_mod, "SOURCE_DIR", fake_source)
        monkeypatch.setitem(_mod, "LOG", tmp_path / "health.log")

        _orig_path = _mod["Path"]
        class FakePath(_orig_path):
            @classmethod
            def home(cls):
                return tmp_path
        monkeypatch.setitem(_mod, "Path", FakePath)

        issues = check()
        plist_issues = [i for i in issues if "com.terry.match.plist" in i]
        assert plist_issues == []

    def test_hardcoded_secret_detected(self, monkeypatch, tmp_path):
        """Scripts containing hardcoded secrets are flagged."""
        fake_launch = tmp_path / "LaunchAgents"
        fake_launch.mkdir()
        fake_bin = tmp_path / "effectors"
        fake_bin.mkdir()

        bad_script = fake_bin / "leaky-script"
        bad_script.write_text(textwrap.dedent("""\
            #!/bin/bash
            API_KEY=sk-abcdefghij1234567890abcdefghijklmn
            echo "using key"
        """))

        monkeypatch.setitem(_mod, "LAUNCH_DIR", fake_launch)
        monkeypatch.setitem(_mod, "SOURCE_DIR", tmp_path / "oscillators")
        monkeypatch.setitem(_mod, "LOG", tmp_path / "health.log")

        _orig_path = _mod["Path"]
        class FakePath(_orig_path):
            @classmethod
            def home(cls):
                return tmp_path
        monkeypatch.setitem(_mod, "Path", FakePath)

        issues = check()
        assert any("HARDCODED KEY" in i for i in issues)

    def test_secret_in_security_find_not_flagged(self, monkeypatch, tmp_path):
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

        monkeypatch.setitem(_mod, "LAUNCH_DIR", fake_launch)
        monkeypatch.setitem(_mod, "SOURCE_DIR", tmp_path / "oscillators")
        monkeypatch.setitem(_mod, "LOG", tmp_path / "health.log")

        _orig_path = _mod["Path"]
        class FakePath(_orig_path):
            @classmethod
            def home(cls):
                return tmp_path
        monkeypatch.setitem(_mod, "Path", FakePath)

        issues = check()
        assert not any("safe-script" in i for i in issues)

    def test_binary_files_skipped(self, monkeypatch, tmp_path):
        """Binary files are skipped during secret scan."""
        fake_launch = tmp_path / "LaunchAgents"
        fake_launch.mkdir()
        fake_bin = tmp_path / "effectors"
        fake_bin.mkdir()

        binary_file = fake_bin / "some-binary"
        binary_file.write_bytes(b"\x00\x00\x00\x00rest of data")

        monkeypatch.setitem(_mod, "LAUNCH_DIR", fake_launch)
        monkeypatch.setitem(_mod, "SOURCE_DIR", tmp_path / "oscillators")
        monkeypatch.setitem(_mod, "LOG", tmp_path / "health.log")

        _orig_path = _mod["Path"]
        class FakePath(_orig_path):
            @classmethod
            def home(cls):
                return tmp_path
        monkeypatch.setitem(_mod, "Path", FakePath)

        issues = check()
        assert not any("some-binary" in i for i in issues)

    def test_doctype_plist_accepted(self, monkeypatch, tmp_path):
        """Plist starting with <!DOCTYPE is accepted as valid XML."""
        fake_launch = tmp_path / "LaunchAgents"
        fake_launch.mkdir()
        fake_source = tmp_path / "oscillators"
        fake_source.mkdir()
        fake_bin = tmp_path / "effectors"
        fake_bin.mkdir()

        content = '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n<plist><dict/></plist>'
        (fake_launch / "com.terry.doctype.plist").write_text(content)
        # No matching source → no drift check

        monkeypatch.setitem(_mod, "LAUNCH_DIR", fake_launch)
        monkeypatch.setitem(_mod, "SOURCE_DIR", fake_source)
        monkeypatch.setitem(_mod, "LOG", tmp_path / "health.log")

        _orig_path = _mod["Path"]
        class FakePath(_orig_path):
            @classmethod
            def home(cls):
                return tmp_path
        monkeypatch.setitem(_mod, "Path", FakePath)

        issues = check()
        plist_issues = [i for i in issues if "com.terry.doctype.plist" in i]
        assert plist_issues == []

    def test_com_vivesca_plists_scanned(self, monkeypatch, tmp_path):
        """com.vivesca.* plists are also scanned."""
        fake_launch = tmp_path / "LaunchAgents"
        fake_launch.mkdir()
        fake_bin = tmp_path / "effectors"
        fake_bin.mkdir()

        bad_plist = fake_launch / "com.vivesca.bad.plist"
        bad_plist.write_text('{"not": "xml"}')

        monkeypatch.setitem(_mod, "LAUNCH_DIR", fake_launch)
        monkeypatch.setitem(_mod, "SOURCE_DIR", tmp_path / "oscillators")
        monkeypatch.setitem(_mod, "LOG", tmp_path / "health.log")

        _orig_path = _mod["Path"]
        class FakePath(_orig_path):
            @classmethod
            def home(cls):
                return tmp_path
        monkeypatch.setitem(_mod, "Path", FakePath)

        mock_result = MagicMock(returncode=1, stderr="bad")
        with patch("subprocess.run", return_value=mock_result):
            issues = check()

        assert any("INVALID" in i and "com.vivesca.bad.plist" in i for i in issues)
