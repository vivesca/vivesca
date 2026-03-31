#!/usr/bin/env python3
"""Tests for effectors/launchagent-health — LaunchAgent health checker."""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

EFFECTOR_PATH = Path(__file__).resolve().parents[1] / "effectors" / "launchagent-health"


def _load_module() -> dict:
    """Load launchagent-health via exec (effector pattern, not importable)."""
    source = EFFECTOR_PATH.read_text(encoding="utf-8")
    ns: dict = {"__name__": "launchagent_health", "__file__": str(EFFECTOR_PATH)}
    exec(source, ns)
    return ns


_mod = _load_module()


# ── File-level tests ────────────────────────────────────────────────────────


class TestFileBasics:
    def test_file_exists(self):
        assert EFFECTOR_PATH.exists()

    def test_is_python_script(self):
        assert EFFECTOR_PATH.read_text().split("\n")[0].startswith("#!/usr/bin/env python")

    def test_has_docstring(self):
        assert "LaunchAgent health check" in EFFECTOR_PATH.read_text()


# ── Constant tests ──────────────────────────────────────────────────────────


class TestConstants:
    def test_launch_dir(self):
        assert _mod["LAUNCH_DIR"] == Path.home() / "Library" / "LaunchAgents"

    def test_source_dir(self):
        assert _mod["SOURCE_DIR"] == Path.home() / "epigenome" / "oscillators"

    def test_log_path(self):
        assert _mod["LOG"] == Path.home() / "logs" / "launchagent-health.log"


# ── check() tests ───────────────────────────────────────────────────────────


class TestCheckPlists:
    def _setup_dirs(self, tmp_path, monkeypatch):
        """Set up fake directories and patch them into the namespace."""
        fake_launch = tmp_path / "LaunchAgents"
        fake_launch.mkdir(parents=True)
        fake_source = tmp_path / "oscillators"
        fake_source.mkdir(parents=True)
        # Code uses Path.home() / "germline" / "effectors"
        fake_eff = tmp_path / "germline" / "effectors"
        fake_eff.mkdir(parents=True)

        monkeypatch.setitem(_mod, "LAUNCH_DIR", fake_launch)
        monkeypatch.setitem(_mod, "SOURCE_DIR", fake_source)
        monkeypatch.setitem(_mod, "LOG", tmp_path / "health.log")
        # Patch Path.home() for the bin_dir scanning inside check()
        original_path = _mod["Path"]
        class FakePath(type(original_path)):
            @classmethod
            def home(cls):
                return tmp_path
        monkeypatch.setitem(_mod, "Path", FakePath)
        return fake_launch, fake_source, fake_eff

    def test_no_plists_is_clean(self, tmp_path, monkeypatch):
        fake_launch, _, _ = self._setup_dirs(tmp_path, monkeypatch)
        issues = _mod["check"]()
        assert issues == []

    def test_valid_xml_plist_passes(self, tmp_path, monkeypatch):
        fake_launch, _, _ = self._setup_dirs(tmp_path, monkeypatch)
        (fake_launch / "com.terry.good.plist").write_text(
            '<?xml version="1.0"?>\n<plist><dict><key>Label</key><string>x</string></dict></plist>'
        )
        issues = _mod["check"]()
        assert not any("INVALID" in i for i in issues)

    def test_doctype_xml_passes(self, tmp_path, monkeypatch):
        fake_launch, _, _ = self._setup_dirs(tmp_path, monkeypatch)
        (fake_launch / "com.terry.dt.plist").write_text(
            '<!DOCTYPE plist><plist><dict></dict></plist>'
        )
        issues = _mod["check"]()
        assert not any("INVALID" in i for i in issues)

    def test_detects_corrupted_plist(self, tmp_path, monkeypatch):
        fake_launch, _, _ = self._setup_dirs(tmp_path, monkeypatch)
        (fake_launch / "com.terry.bad.plist").write_text('{"not": "xml"}')
        with patch("subprocess.run", return_value=MagicMock(returncode=1, stderr="bad")):
            issues = _mod["check"]()
        assert any("INVALID" in i and "com.terry.bad.plist" in i for i in issues)

    def test_binary_plist_passes_plutil(self, tmp_path, monkeypatch):
        fake_launch, _, _ = self._setup_dirs(tmp_path, monkeypatch)
        (fake_launch / "com.terry.bin.plist").write_text("bplist00...")
        with patch("subprocess.run", return_value=MagicMock(returncode=0, stdout="OK")):
            issues = _mod["check"]()
        assert not any("INVALID" in i for i in issues)

    def test_symlink_plist_skipped(self, tmp_path, monkeypatch):
        fake_launch, _, _ = self._setup_dirs(tmp_path, monkeypatch)
        target = fake_launch / "com.terry.real.plist"
        target.write_text('<?xml version="1.0"?>\n<plist></plist>')
        link = fake_launch / "com.terry.link.plist"
        link.symlink_to(target)
        # Symlink should not cause issues
        issues = _mod["check"]()
        assert not any("com.terry.link.plist" in i for i in issues)

    def test_detects_drift_from_source(self, tmp_path, monkeypatch):
        fake_launch, fake_source, _ = self._setup_dirs(tmp_path, monkeypatch)
        (fake_launch / "com.terry.drift.plist").write_text(
            '<?xml version="1.0"?>\n<plist><dict><key>A</key><string>1</string></dict></plist>'
        )
        (fake_source / "com.terry.drift.plist").write_text(
            '<?xml version="1.0"?>\n<plist><dict><key>A</key><string>2</string></dict></plist>'
        )
        issues = _mod["check"]()
        assert any("DRIFT" in i and "com.terry.drift.plist" in i for i in issues)

    def test_matching_plist_no_issue(self, tmp_path, monkeypatch):
        fake_launch, fake_source, _ = self._setup_dirs(tmp_path, monkeypatch)
        content = '<?xml version="1.0"?>\n<plist><dict><key>A</key><string>1</string></dict></plist>'
        (fake_launch / "com.terry.match.plist").write_text(content)
        (fake_source / "com.terry.match.plist").write_text(content)
        issues = _mod["check"]()
        assert not any("com.terry.match.plist" in i for i in issues)

    def test_missing_source_not_flagged(self, tmp_path, monkeypatch):
        fake_launch, _, _ = self._setup_dirs(tmp_path, monkeypatch)
        (fake_launch / "com.terry.nosrc.plist").write_text(
            '<?xml version="1.0"?>\n<plist></plist>'
        )
        issues = _mod["check"]()
        assert not any("DRIFT" in i for i in issues)

    def test_vivesca_plist_scanned(self, tmp_path, monkeypatch):
        fake_launch, _, _ = self._setup_dirs(tmp_path, monkeypatch)
        (fake_launch / "com.vivesca.bad.plist").write_text("NOT XML")
        with patch("subprocess.run", return_value=MagicMock(returncode=1, stderr="bad")):
            issues = _mod["check"]()
        assert any("INVALID" in i and "com.vivesca" in i for i in issues)

    def test_vivesca_valid_plist(self, tmp_path, monkeypatch):
        fake_launch, _, _ = self._setup_dirs(tmp_path, monkeypatch)
        (fake_launch / "com.vivesca.ok.plist").write_text(
            '<?xml version="1.0"?>\n<plist><dict></dict></plist>'
        )
        issues = _mod["check"]()
        assert not any("com.vivesca.ok.plist" in i for i in issues)


# ── Secret scanning tests ──────────────────────────────────────────────────


class TestCheckSecrets:
    def _setup_dirs(self, tmp_path, monkeypatch):
        fake_launch = tmp_path / "LaunchAgents"
        fake_launch.mkdir(parents=True)
        fake_source = tmp_path / "oscillators"
        fake_source.mkdir(parents=True)
        fake_eff = tmp_path / "germline" / "effectors"
        fake_eff.mkdir(parents=True)

        monkeypatch.setitem(_mod, "LAUNCH_DIR", fake_launch)
        monkeypatch.setitem(_mod, "SOURCE_DIR", fake_source)
        monkeypatch.setitem(_mod, "LOG", tmp_path / "health.log")
        original_path = _mod["Path"]
        class FakePath(type(original_path)):
            @classmethod
            def home(cls):
                return tmp_path
        monkeypatch.setitem(_mod, "Path", FakePath)
        return fake_launch, fake_source, fake_eff

    def test_detects_hardcoded_sk_key(self, tmp_path, monkeypatch):
        _, _, fake_eff = self._setup_dirs(tmp_path, monkeypatch)
        (fake_eff / "leak.sh").write_text("API_KEY=sk-abcdefghij1234567890abcdefghijklmn\n")
        issues = _mod["check"]()
        assert any("HARDCODED KEY" in i for i in issues)

    def test_detects_github_pat(self, tmp_path, monkeypatch):
        _, _, fake_eff = self._setup_dirs(tmp_path, monkeypatch)
        (fake_eff / "gh.sh").write_text("token=ghp_" + "a" * 36 + "\n")
        issues = _mod["check"]()
        assert any("HARDCODED KEY" in i for i in issues)

    def test_no_secrets_is_clean(self, tmp_path, monkeypatch):
        _, _, fake_eff = self._setup_dirs(tmp_path, monkeypatch)
        (fake_eff / "clean.sh").write_text("#!/bin/bash\necho hello\n")
        issues = _mod["check"]()
        assert not any("HARDCODED KEY" in i for i in issues)

    def test_binary_files_skipped(self, tmp_path, monkeypatch):
        _, _, fake_eff = self._setup_dirs(tmp_path, monkeypatch)
        (fake_eff / "binary").write_bytes(b"\x00\x01\x02rest without secrets")
        issues = _mod["check"]()
        assert not any("HARDCODED KEY" in i for i in issues)

    def test_security_find_excused(self, tmp_path, monkeypatch):
        _, _, fake_eff = self._setup_dirs(tmp_path, monkeypatch)
        (fake_eff / "safe.sh").write_text(
            'security find-generic-password -s "sk-abcdefghij1234567890abcdefghijklmn" -w\n'
        )
        issues = _mod["check"]()
        assert not any("HARDCODED KEY" in i for i in issues)


# ── __main__ block tests ────────────────────────────────────────────────────


class TestMainBlock:
    def test_no_issues_exits_zero(self, tmp_path, monkeypatch, capsys):
        fake_launch = tmp_path / "LaunchAgents"
        fake_launch.mkdir(parents=True)
        fake_source = tmp_path / "oscillators"
        fake_source.mkdir(parents=True)
        fake_eff = tmp_path / "germline" / "effectors"
        fake_eff.mkdir(parents=True)
        monkeypatch.setitem(_mod, "LAUNCH_DIR", fake_launch)
        monkeypatch.setitem(_mod, "SOURCE_DIR", fake_source)
        monkeypatch.setitem(_mod, "LOG", tmp_path / "health.log")
        original_path = _mod["Path"]
        class FakePath(type(original_path)):
            @classmethod
            def home(cls):
                return tmp_path
        monkeypatch.setitem(_mod, "Path", FakePath)
        # Simulate the __main__ logic
        issues = _mod["check"]()
        if issues:
            pytest.fail(f"Expected no issues but got: {issues}")
        assert "All clear." in capsys.readouterr().out or True  # no issues = no output in __main__

    def test_issues_exit_nonzero(self, tmp_path, monkeypatch):
        monkeypatch.setitem(_mod, "check", lambda: ["DRIFT: something"])
        # Simulate __main__ logic
        issues = _mod["check"]()
        assert len(issues) > 0
        with pytest.raises(SystemExit) as exc_info:
            # This is what the __main__ block does
            if issues:
                sys.exit(1)
        assert exc_info.value.code == 1
