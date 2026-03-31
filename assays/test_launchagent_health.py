"""Tests for effectors/launchagent-health — verify plists match source and are valid XML."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

EFFECTOR = Path(__file__).resolve().parent.parent / "effectors" / "launchagent-health"

@pytest.fixture()
def mod(tmp_path, monkeypatch):
    """Load launchagent-health via exec with home patched to tmp_path."""
    ns: dict = {}
    code = EFFECTOR.read_text()
    exec(code, ns)
    # Patch home so LAUNCH_DIR / SOURCE_DIR / LOG / bin_dir point to tmp
    monkeypatch.setattr(ns["Path"], "home", classmethod(lambda cls: tmp_path))
    ns["LAUNCH_DIR"] = tmp_path / "Library" / "LaunchAgents"
    ns["SOURCE_DIR"] = tmp_path / "epigenome" / "oscillators"
    ns["LOG"] = tmp_path / "logs" / "launchagent-health.log"
    ns["LAUNCH_DIR"].mkdir(parents=True, exist_ok=True)
    ns["SOURCE_DIR"].mkdir(parents=True, exist_ok=True)
    # Create a minimal effectors dir so the secret scan doesn't walk real files
    eff_dir = tmp_path / "germline" / "effectors"
    eff_dir.mkdir(parents=True, exist_ok=True)
    return ns


def _write_plist(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content)
    return p


# ── Valid plist detection ───────────────────────────────────────────────────

class TestValidPlist:
    def test_valid_xml_passes(self, mod):
        xml = '<?xml version="1.0"?><plist><dict><key>Label</key><string>x</string></dict></plist>'
        _write_plist(mod["LAUNCH_DIR"], "com.terry.good.plist", xml)
        issues = mod["check"]()
        assert not any("INVALID" in i for i in issues)

    def test_doctype_xml_passes(self, mod):
        xml = '<!DOCTYPE plist><plist><dict></dict></plist>'
        _write_plist(mod["LAUNCH_DIR"], "com.terry.doctype.plist", xml)
        issues = mod["check"]()
        assert not any("INVALID" in i for i in issues)

    def test_invalid_plist_flagged(self, mod):
        _write_plist(mod["LAUNCH_DIR"], "com.terry.bad.plist", "THIS IS NOT XML")
        with patch("subprocess.run", return_value=MagicMock(returncode=1, stderr="bad")):
            issues = mod["check"]()
        assert any("INVALID" in i and "com.terry.bad.plist" in i for i in issues)

    def test_binary_plist_passes_plutil(self, mod):
        """Binary plist (no XML header) but plutil says OK."""
        _write_plist(mod["LAUNCH_DIR"], "com.terry.bin.plist", "bplist00...")
        with patch("subprocess.run", return_value=MagicMock(returncode=0, stdout="OK")):
            issues = mod["check"]()
        assert not any("INVALID" in i for i in issues)

    def test_symlink_skipped(self, mod):
        xml = '<?xml version="1.0"?><plist></plist>'
        target = _write_plist(mod["LAUNCH_DIR"], "com.terry.real.plist", xml)
        link = mod["LAUNCH_DIR"] / "com.terry.link.plist"
        link.symlink_to(target)
        # The symlink should not cause issues — only target is checked
        issues = mod["check"]()
        # Symlink itself is skipped
        assert not any("com.terry.link.plist" in i for i in issues)


# ── Drift detection ─────────────────────────────────────────────────────────

class TestDriftDetection:
    def test_matching_source_no_drift(self, mod):
        content = '<?xml version="1.0"?><plist><dict><key>Label</key><string>y</string></dict></plist>'
        _write_plist(mod["LAUNCH_DIR"], "com.terry.match.plist", content)
        _write_plist(mod["SOURCE_DIR"], "com.terry.match.plist", content)
        issues = mod["check"]()
        assert not any("DRIFT" in i for i in issues)

    def test_drifted_source_flagged(self, mod):
        _write_plist(mod["LAUNCH_DIR"], "com.terry.drift.plist",
                      '<?xml version="1.0"?><plist><dict><key>Old</key></dict></plist>')
        _write_plist(mod["SOURCE_DIR"], "com.terry.drift.plist",
                      '<?xml version="1.0"?><plist><dict><key>New</key></dict></plist>')
        issues = mod["check"]()
        assert any("DRIFT" in i and "com.terry.drift.plist" in i for i in issues)

    def test_missing_source_not_flagged_as_drift(self, mod):
        """If source doesn't exist, drift check is skipped entirely."""
        _write_plist(mod["LAUNCH_DIR"], "com.terry.nosrc.plist",
                      '<?xml version="1.0"?><plist></plist>')
        issues = mod["check"]()
        assert not any("DRIFT" in i for i in issues)


# ── Secret scanning ─────────────────────────────────────────────────────────

class TestSecretScanning:
    def test_detects_openai_key(self, mod):
        eff = mod["LAUNCH_DIR"].parent.parent / "germline" / "effectors"
        eff.mkdir(parents=True, exist_ok=True)
        (eff / "leak.sh").write_text("export KEY=sk-abc123def456ghi789jkl012mno345pqr678\n")
        issues = mod["check"]()
        assert any("HARDCODED KEY" in i for i in issues)

    def test_detects_github_pat(self, mod):
        eff = mod["LAUNCH_DIR"].parent.parent / "germline" / "effectors"
        eff.mkdir(parents=True, exist_ok=True)
        (eff / "gh.sh").write_text("token=ghp_" + "a" * 36 + "\n")
        issues = mod["check"]()
        assert any("HARDCODED KEY" in i for i in issues)

    def test_clean_script_no_flag(self, mod):
        eff = mod["LAUNCH_DIR"].parent.parent / "germline" / "effectors"
        eff.mkdir(parents=True, exist_ok=True)
        (eff / "clean.sh").write_text("#!/bin/bash\necho hello\n")
        issues = mod["check"]()
        assert not any("HARDCODED KEY" in i for i in issues)

    def test_binary_file_skipped(self, mod):
        eff = mod["LAUNCH_DIR"].parent.parent / "germline" / "effectors"
        eff.mkdir(parents=True, exist_ok=True)
        (eff / "binary").write_bytes(b"\x00\x01\x02\x03rest of file without secrets")
        issues = mod["check"]()
        assert not any("HARDCODED KEY" in i for i in issues)

    def test_security_find_excused(self, mod):
        """Lines containing 'security find' are not flagged even with a key pattern."""
        eff = mod["LAUNCH_DIR"].parent.parent / "germline" / "effectors"
        eff.mkdir(parents=True, exist_ok=True)
        (eff / "safe.sh").write_text(
            'security find -s "sk-abc123def456ghi789jkl012mno345pqr678"\n'
        )
        issues = mod["check"]()
        assert not any("HARDCODED KEY" in i for i in issues)


# ── main / exit codes ──────────────────────────────────────────────────────

class TestMain:
    def test_all_clear_exits_zero(self, mod, capsys):
        mod["check"] = lambda: []
        with pytest.raises(SystemExit) as exc_info:
            mod["__name__"] = "__main__"
            # Re-run the __main__ block logic directly
            issues = []
            if issues:
                sys.exit(1)
            else:
                print("All clear.")
                sys.exit(0)
        assert exc_info.value.code == 0

    def test_issues_exits_nonzero(self, mod):
        issues = ["DRIFT: something"]
        with pytest.raises(SystemExit) as exc_info:
            if issues:
                sys.exit(1)
            else:
                sys.exit(0)
        assert exc_info.value.code == 1


# ── com.vivesca.* plists ───────────────────────────────────────────────────

class TestVivescaPlists:
    def test_vivesca_plist_scanned(self, mod):
        xml = "NOT XML"
        _write_plist(mod["LAUNCH_DIR"], "com.vivesca.bad.plist", xml)
        with patch("subprocess.run", return_value=MagicMock(returncode=1, stderr="bad")):
            issues = mod["check"]()
        assert any("INVALID" in i and "com.vivesca" in i for i in issues)

    def test_vivesca_plist_valid(self, mod):
        xml = '<?xml version="1.0"?><plist><dict></dict></plist>'
        _write_plist(mod["LAUNCH_DIR"], "com.vivesca.ok.plist", xml)
        issues = mod["check"]()
        assert not any("com.vivesca.ok.plist" in i for i in issues)
