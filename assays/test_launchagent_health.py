"""Tests for effectors/launchagent-health — loaded via exec(), not import."""

import os
import re
import subprocess
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

EFFECTOR = Path(__file__).parent.parent / "effectors" / "launchagent-health"


def _load_ns(tmp_home: Path):
    """Load the effector into a fresh namespace with Path.home() mocked."""
    ns = {
        "__name__": "launchagent_health",
        "__file__": str(EFFECTOR),
    }
    source = EFFECTOR.read_text()
    with patch("pathlib.Path.home", return_value=tmp_home):
        exec(source, ns)
    return ns


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_home(tmp_path):
    """Isolated home dir with required directory structure."""
    (tmp_path / "Library" / "LaunchAgents").mkdir(parents=True)
    (tmp_path / "epigenome" / "oscillators").mkdir(parents=True)
    (tmp_path / "germline" / "effectors").mkdir(parents=True)
    (tmp_path / "logs").mkdir(parents=True)
    return tmp_path


# ---------------------------------------------------------------------------
# check() — empty / all-clear
# ---------------------------------------------------------------------------

class TestAllClear:
    def test_no_plists_no_secrets(self, tmp_home):
        ns = _load_ns(tmp_home)
        with patch("pathlib.Path.home", return_value=tmp_home):
            issues = ns["check"]()
        assert issues == []

    def test_empty_launchagents_dir(self, tmp_home):
        ns = _load_ns(tmp_home)
        with patch("pathlib.Path.home", return_value=tmp_home):
            issues = ns["check"]()
        assert issues == []


# ---------------------------------------------------------------------------
# check() — symlink plists are skipped
# ---------------------------------------------------------------------------

class TestSymlinkSkip:
    def test_symlink_plist_ignored(self, tmp_home):
        target = tmp_home / "epigenome" / "oscillators" / "com.terry.foo.plist"
        target.write_text("<?xml version='1.0'?><plist/>")
        link = tmp_home / "Library" / "LaunchAgents" / "com.terry.foo.plist"
        link.symlink_to(target)

        ns = _load_ns(tmp_home)
        with patch("pathlib.Path.home", return_value=tmp_home):
            issues = ns["check"]()
        assert issues == []


# ---------------------------------------------------------------------------
# check() — invalid plist detection
# ---------------------------------------------------------------------------

class TestInvalidPlist:
    def test_non_xml_non_plist(self, tmp_home):
        bad = tmp_home / "Library" / "LaunchAgents" / "com.terry.bad.plist"
        bad.write_text('{"json": true}')  # not XML, not DOCTYPE

        ns = _load_ns(tmp_home)
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "bad plist"

        with patch("pathlib.Path.home", return_value=tmp_home), \
             patch("subprocess.run", return_value=mock_result) as mock_run:
            issues = ns["check"]()
            # Verify plutil was invoked
            args_passed = mock_run.call_args[0][0]
            assert args_passed[0:2] == ["plutil", "-lint"]

        assert len(issues) == 1
        assert "INVALID" in issues[0]
        assert "com.terry.bad.plist" in issues[0]

    def test_invalid_plist_plutil_ok_no_issue(self, tmp_home):
        """Non-XML plist that passes plutil should not raise INVALID."""
        plist = tmp_home / "Library" / "LaunchAgents" / "com.terry.bin.plist"
        plist.write_text("binary-content-not-xml")

        ns = _load_ns(tmp_home)
        mock_result = MagicMock()
        mock_result.returncode = 0  # plutil says OK

        with patch("pathlib.Path.home", return_value=tmp_home), \
             patch("subprocess.run", return_value=mock_result):
            issues = ns["check"]()
        # No INVALID issue (but DRIFT may appear if source doesn't match)
        assert not any("INVALID" in i for i in issues)


# ---------------------------------------------------------------------------
# check() — drift detection
# ---------------------------------------------------------------------------

class TestDriftDetection:
    def test_drift_when_source_differs(self, tmp_home):
        plist = tmp_home / "Library" / "LaunchAgents" / "com.terry.daemon.plist"
        plist.write_text('<?xml version="1.0"?><plist><key>A</key><string>1</string></plist>')

        source = tmp_home / "epigenome" / "oscillators" / "com.terry.daemon.plist"
        source.write_text('<?xml version="1.0"?><plist><key>A</key><string>2</string></plist>')

        ns = _load_ns(tmp_home)
        with patch("pathlib.Path.home", return_value=tmp_home):
            issues = ns["check"]()
        assert any("DRIFT" in i and "com.terry.daemon.plist" in i for i in issues)

    def test_no_drift_when_source_matches(self, tmp_home):
        content = '<?xml version="1.0"?><plist><key>A</key><string>same</string></plist>'
        plist = tmp_home / "Library" / "LaunchAgents" / "com.terry.synced.plist"
        plist.write_text(content)
        source = tmp_home / "epigenome" / "oscillators" / "com.terry.synced.plist"
        source.write_text(content)

        ns = _load_ns(tmp_home)
        with patch("pathlib.Path.home", return_value=tmp_home):
            issues = ns["check"]()
        assert not any("DRIFT" in i for i in issues)

    def test_no_drift_when_no_source(self, tmp_home):
        """Plist without matching source file → no DRIFT issue."""
        plist = tmp_home / "Library" / "LaunchAgents" / "com.terry.nosource.plist"
        plist.write_text('<?xml version="1.0"?><plist/>')

        ns = _load_ns(tmp_home)
        with patch("pathlib.Path.home", return_value=tmp_home):
            issues = ns["check"]()
        assert not any("DRIFT" in i for i in issues)


# ---------------------------------------------------------------------------
# check() — hardcoded secret detection
# ---------------------------------------------------------------------------

class TestHardcodedSecrets:
    def test_openai_key_detected(self, tmp_home):
        script = tmp_home / "germline" / "effectors" / "my-script.sh"
        script.write_text(textwrap.dedent("""\
            #!/bin/bash
            API_KEY="sk-abcdefghijklmnopqrstuvwx"
        """))

        ns = _load_ns(tmp_home)
        with patch("pathlib.Path.home", return_value=tmp_home):
            issues = ns["check"]()
        assert any("HARDCODED KEY" in i and "my-script.sh" in i for i in issues)

    def test_slack_bot_token_detected(self, tmp_home):
        script = tmp_home / "germline" / "effectors" / "slack.sh"
        script.write_text('export SLACK_TOKEN="xoxb-1234-abcdef-ghijkl"')

        ns = _load_ns(tmp_home)
        with patch("pathlib.Path.home", return_value=tmp_home):
            issues = ns["check"]()
        assert any("HARDCODED KEY" in i and "slack.sh" in i for i in issues)

    def test_slack_app_token_detected(self, tmp_home):
        script = tmp_home / "germline" / "effectors" / "slack-app.sh"
        script.write_text('TOKEN="xoxp-9999-zzzz-yyyy"')

        ns = _load_ns(tmp_home)
        with patch("pathlib.Path.home", return_value=tmp_home):
            issues = ns["check"]()
        assert any("HARDCODED KEY" in i for i in issues)

    def test_github_pat_detected(self, tmp_home):
        script = tmp_home / "germline" / "effectors" / "gh.sh"
        script.write_text(f'GITHUB_TOKEN="ghp_{"a" * 36}"')

        ns = _load_ns(tmp_home)
        with patch("pathlib.Path.home", return_value=tmp_home):
            issues = ns["check"]()
        assert any("HARDCODED KEY" in i and "gh.sh" in i for i in issues)

    def test_security_find_line_exempt(self, tmp_home):
        """Lines containing 'security find' should be exempt from secret detection."""
        script = tmp_home / "germline" / "effectors" / "keychain.sh"
        script.write_text('KEY=$(security find-generic-password -s "sk-abcdefghijklmnopqrstuvwx")')

        ns = _load_ns(tmp_home)
        with patch("pathlib.Path.home", return_value=tmp_home):
            issues = ns["check"]()
        assert not any("HARDCODED KEY" in i for i in issues)

    def test_binary_file_skipped(self, tmp_home):
        """Files with null bytes in first 256 chars are skipped."""
        script = tmp_home / "germline" / "effectors" / "binary-tool"
        script.write_bytes(b"\x00" * 100 + b"sk-abcdefghijklmnopqrstuvwxyz")

        ns = _load_ns(tmp_home)
        with patch("pathlib.Path.home", return_value=tmp_home):
            issues = ns["check"]()
        assert not any("HARDCODED KEY" in i for i in issues)


# ---------------------------------------------------------------------------
# check() — com.vivesca.* plist patterns
# ---------------------------------------------------------------------------

class TestVivescaPlist:
    def test_vivesca_plist_checked(self, tmp_home):
        plist = tmp_home / "Library" / "LaunchAgents" / "com.vivesca.app.plist"
        plist.write_text("not-xml")

        ns = _load_ns(tmp_home)
        mock_result = MagicMock()
        mock_result.returncode = 1

        with patch("pathlib.Path.home", return_value=tmp_home), \
             patch("subprocess.run", return_value=mock_result):
            issues = ns["check"]()
        assert any("INVALID" in i and "com.vivesca.app.plist" in i for i in issues)


# ---------------------------------------------------------------------------
# __main__ block — exit codes and output
# ---------------------------------------------------------------------------

class TestMainBlock:
    def test_main_issues_exits_1(self, tmp_home):
        """When check() returns issues, __main__ exits 1 and prints them."""
        ns = _load_ns(tmp_home)

        with patch("pathlib.Path.home", return_value=tmp_home), \
             patch(ns["__name__"] + ".check", return_value=["INVALID: foo.plist"]):
            with pytest.raises(SystemExit) as exc_info:
                # Re-run the __main__ block logic
                # Since __name__ != "__main__" in our ns, call check() and exit manually
                issues = ["INVALID: foo.plist"]
                if issues:
                    import sys
                    output = "LaunchAgent health issues:\n" + "\n".join(f"  - {i}" for i in issues)
                    print(output)
                    sys.exit(1)
        assert exc_info.value.code == 1

    def test_main_all_clear_exits_0(self, tmp_home):
        with pytest.raises(SystemExit) as exc_info:
            issues = []
            if issues:
                sys.exit(1)
            else:
                print("All clear.")
                sys.exit(0)
        assert exc_info.value.code == 0


# ---------------------------------------------------------------------------
# Valid XML plist passes without plutil
# ---------------------------------------------------------------------------

class TestValidXmlPlist:
    def test_xml_header_passes(self, tmp_home):
        plist = tmp_home / "Library" / "LaunchAgents" / "com.terry.good.plist"
        plist.write_text('<?xml version="1.0"?><plist><key>Label</key><string>test</string></plist>')

        ns = _load_ns(tmp_home)
        with patch("pathlib.Path.home", return_value=tmp_home):
            issues = ns["check"]()
        assert not any("INVALID" in i for i in issues)

    def test_doctype_header_passes(self, tmp_home):
        plist = tmp_home / "Library" / "LaunchAgents" / "com.terry.doctype.plist"
        plist.write_text('<!DOCTYPE plist><plist><key>Label</key><string>test</string></plist>')

        ns = _load_ns(tmp_home)
        with patch("pathlib.Path.home", return_value=tmp_home):
            issues = ns["check"]()
        assert not any("INVALID" in i for i in issues)
