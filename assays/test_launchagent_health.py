#!/usr/bin/env python3
"""Tests for launchagent-health effector."""

import re
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Load effector via exec (no .py extension)
_effector_path = Path(__file__).parent.parent / "effectors" / "launchagent-health"
_ns = {"__name__": "launchagent_health_test"}
exec(open(_effector_path).read(), _ns)

check = _ns["check"]
LAUNCH_DIR = _ns["LAUNCH_DIR"]
SOURCE_DIR = _ns["SOURCE_DIR"]
LOG = _ns["LOG"]


# ── Plist validation ──────────────────────────────────────────────────

def test_symlinks_skipped(tmp_path):
    """Symlinked plists should not be checked."""
    launch_dir = tmp_path / "Library" / "LaunchAgents"
    launch_dir.mkdir(parents=True)
    target = launch_dir / "com.terry.real.plist"
    target.write_text('<?xml version="1.0"?>\n<plist><dict/></plist>')
    link = launch_dir / "com.terry.link.plist"
    link.symlink_to(target)

    with (
        patch("launchagent_health_test.LAUNCH_DIR", launch_dir),
        patch("launchagent_health_test.SOURCE_DIR", tmp_path / "nope"),
        patch("launchagent_health_test.Path.home", return_value=tmp_path),
    ):
        # Rebind in namespace since LAUNCH_DIR is already resolved
        _ns2 = {"__name__": "lh2"}
        # Build a small check that uses the patched LAUNCH_DIR
        pass

    # Simpler approach: exec with patched paths
    ns = {"__name__": "lh_test_symlinks"}
    ns["LAUNCH_DIR"] = launch_dir
    ns["SOURCE_DIR"] = tmp_path / "nope"
    ns["LOG"] = tmp_path / "logs" / "test.log"
    code = open(_effector_path).read()
    # Replace the module-level constants
    exec(code, ns)
    issues = ns["check"]()
    assert len(issues) == 0


def test_non_xml_plist_flagged_invalid(tmp_path):
    """A non-XML, non-DOCTYPE plist that plutil rejects should be flagged."""
    launch_dir = tmp_path / "Library" / "LaunchAgents"
    launch_dir.mkdir(parents=True)
    bad_plist = launch_dir / "com.terry.bad.plist"
    bad_plist.write_text('{"json": "not a plist"}')

    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = "bad.plist: does not exist or not a plist file"

    ns = {"__name__": "lh_test_bad", "subprocess": MagicMock()}
    ns["subprocess"].run.return_value = mock_result
    ns["LAUNCH_DIR"] = launch_dir
    ns["SOURCE_DIR"] = tmp_path / "nope"
    ns["LOG"] = tmp_path / "logs" / "test.log"
    ns["Path"] = Path
    ns["sys"] = sys
    ns["re"] = re

    exec(open(_effector_path).read(), ns)
    issues = ns["check"]()
    assert any("INVALID" in i and "com.terry.bad.plist" in i for i in issues)


def test_non_xml_plist_valid_binary_passes(tmp_path):
    """A non-XML plist that plutil accepts should not be flagged as invalid."""
    launch_dir = tmp_path / "Library" / "LaunchAgents"
    launch_dir.mkdir(parents=True)
    bin_plist = launch_dir / "com.terry.binary.plist"
    bin_plist.write_text("bplist00?some-binary-content")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "binary.plist: OK"

    ns = {"__name__": "lh_test_binary", "subprocess": MagicMock()}
    ns["subprocess"].run.return_value = mock_result
    ns["LAUNCH_DIR"] = launch_dir
    ns["SOURCE_DIR"] = tmp_path / "nope"
    ns["LOG"] = tmp_path / "logs" / "test.log"
    ns["Path"] = Path
    ns["sys"] = sys
    ns["re"] = re

    exec(open(_effector_path).read(), ns)
    issues = ns["check"]()
    assert not any("INVALID" in i for i in issues)


def test_xml_plist_passes_validation(tmp_path):
    """XML plists should pass the validation check."""
    launch_dir = tmp_path / "Library" / "LaunchAgents"
    launch_dir.mkdir(parents=True)
    xml_plist = launch_dir / "com.terry.good.plist"
    xml_plist.write_text('<?xml version="1.0"?>\n<plist version="1.0"><dict/></plist>')

    ns = {"__name__": "lh_test_xml", "subprocess": MagicMock()}
    ns["LAUNCH_DIR"] = launch_dir
    ns["SOURCE_DIR"] = tmp_path / "nope"
    ns["LOG"] = tmp_path / "logs" / "test.log"
    ns["Path"] = Path
    ns["sys"] = sys
    ns["re"] = re

    exec(open(_effector_path).read(), ns)
    issues = ns["check"]()
    assert not any("INVALID" in i for i in issues)


def test_doctype_plist_passes_validation(tmp_path):
    """DOCTYPE plists should pass the validation check."""
    launch_dir = tmp_path / "Library" / "LaunchAgents"
    launch_dir.mkdir(parents=True)
    dt_plist = launch_dir / "com.terry.doctype.plist"
    dt_plist.write_text('<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN">\n<plist><dict/></plist>')

    ns = {"__name__": "lh_test_doctype", "subprocess": MagicMock()}
    ns["LAUNCH_DIR"] = launch_dir
    ns["SOURCE_DIR"] = tmp_path / "nope"
    ns["LOG"] = tmp_path / "logs" / "test.log"
    ns["Path"] = Path
    ns["sys"] = sys
    ns["re"] = re

    exec(open(_effector_path).read(), ns)
    issues = ns["check"]()
    assert not any("INVALID" in i for i in issues)


# ── Drift detection ───────────────────────────────────────────────────

def test_drift_detected_when_source_differs(tmp_path):
    """Drift should be reported when deployed plist differs from source."""
    launch_dir = tmp_path / "Library" / "LaunchAgents"
    launch_dir.mkdir(parents=True)
    source_dir = tmp_path / "epigenome" / "oscillators"
    source_dir.mkdir(parents=True)

    deployed = launch_dir / "com.terry.drift.plist"
    deployed.write_text('<?xml version="1.0"?>\n<plist><dict><key>A</key><string>1</string></dict></plist>')

    source = source_dir / "com.terry.drift.plist"
    source.write_text('<?xml version="1.0"?>\n<plist><dict><key>A</key><string>2</string></dict></plist>')

    ns = {"__name__": "lh_test_drift", "subprocess": MagicMock()}
    ns["LAUNCH_DIR"] = launch_dir
    ns["SOURCE_DIR"] = source_dir
    ns["LOG"] = tmp_path / "logs" / "test.log"
    ns["Path"] = Path
    ns["sys"] = sys
    ns["re"] = re

    exec(open(_effector_path).read(), ns)
    issues = ns["check"]()
    assert any("DRIFT" in i and "com.terry.drift.plist" in i for i in issues)


def test_no_drift_when_source_matches(tmp_path):
    """No drift when deployed plist matches source exactly."""
    launch_dir = tmp_path / "Library" / "LaunchAgents"
    launch_dir.mkdir(parents=True)
    source_dir = tmp_path / "epigenome" / "oscillators"
    source_dir.mkdir(parents=True)

    content = '<?xml version="1.0"?>\n<plist><dict><key>A</key><string>1</string></dict></plist>'
    deployed = launch_dir / "com.terry.match.plist"
    deployed.write_text(content)
    source = source_dir / "com.terry.match.plist"
    source.write_text(content)

    ns = {"__name__": "lh_test_match", "subprocess": MagicMock()}
    ns["LAUNCH_DIR"] = launch_dir
    ns["SOURCE_DIR"] = source_dir
    ns["LOG"] = tmp_path / "logs" / "test.log"
    ns["Path"] = Path
    ns["sys"] = sys
    ns["re"] = re

    exec(open(_effector_path).read(), ns)
    issues = ns["check"]()
    assert not any("DRIFT" in i for i in issues)


def test_no_drift_when_no_source(tmp_path):
    """No drift reported when source file doesn't exist (not tracked)."""
    launch_dir = tmp_path / "Library" / "LaunchAgents"
    launch_dir.mkdir(parents=True)

    deployed = launch_dir / "com.terry.untracked.plist"
    deployed.write_text('<?xml version="1.0"?>\n<plist><dict/></plist>')

    ns = {"__name__": "lh_test_nosrc", "subprocess": MagicMock()}
    ns["LAUNCH_DIR"] = launch_dir
    ns["SOURCE_DIR"] = tmp_path / "nonexistent"
    ns["LOG"] = tmp_path / "logs" / "test.log"
    ns["Path"] = Path
    ns["sys"] = sys
    ns["re"] = re

    exec(open(_effector_path).read(), ns)
    issues = ns["check"]()
    assert not any("DRIFT" in i for i in issues)


# ── Secret scanning ───────────────────────────────────────────────────

def test_hardcoded_sk_key_detected(tmp_path):
    """OpenAI-style sk- keys in effectors should be flagged."""
    eff_dir = tmp_path / "germline" / "effectors"
    eff_dir.mkdir(parents=True)
    bad_script = eff_dir / "my-script"
    bad_script.write_text('API_KEY = "sk-abcdefghijklmnopqrstuvwxyz123456"\n')

    launch_dir = tmp_path / "Library" / "LaunchAgents"
    launch_dir.mkdir(parents=True)

    ns = {"__name__": "lh_test_sk", "subprocess": MagicMock()}
    ns["LAUNCH_DIR"] = launch_dir
    ns["SOURCE_DIR"] = tmp_path / "nope"
    ns["LOG"] = tmp_path / "logs" / "test.log"
    ns["Path"] = Path
    ns["sys"] = sys
    ns["re"] = re

    exec(open(_effector_path).read(), ns)
    # Patch the effector dir inside the namespace to point at tmp
    issues = ns["check"]()
    # The script hardcodes Path.home() / "germline" / "effectors" so it
    # scans the real effectors dir. We need to override that path.
    # Instead, re-exec with a patched home:
    pass

    # Better approach: exec with a modified source that uses our tmp eff_dir
    code = open(_effector_path).read()
    # Replace the hardcoded path
    code = code.replace(
        'Path.home() / "germline" / "effectors"',
        f'Path({repr(str(eff_dir))})',
    )
    ns2 = {"__name__": "lh_test_sk2", "subprocess": MagicMock()}
    ns2["LAUNCH_DIR"] = launch_dir
    ns2["SOURCE_DIR"] = tmp_path / "nope"
    ns2["LOG"] = tmp_path / "logs" / "test.log"
    ns2["Path"] = Path
    ns2["sys"] = sys
    ns2["re"] = re
    exec(code, ns2)
    issues = ns2["check"]()
    assert any("HARDCODED KEY" in i and "my-script" in i for i in issues)


def test_ghp_key_detected(tmp_path):
    """GitHub personal access tokens should be flagged."""
    eff_dir = tmp_path / "germline" / "effectors"
    eff_dir.mkdir(parents=True)
    bad_script = eff_dir / "deploy"
    bad_script.write_text('TOKEN = "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij"\n')

    launch_dir = tmp_path / "Library" / "LaunchAgents"
    launch_dir.mkdir(parents=True)

    code = open(_effector_path).read().replace(
        'Path.home() / "germline" / "effectors"',
        f'Path({repr(str(eff_dir))})',
    )
    ns = {"__name__": "lh_test_ghp", "subprocess": MagicMock()}
    ns["LAUNCH_DIR"] = launch_dir
    ns["SOURCE_DIR"] = tmp_path / "nope"
    ns["LOG"] = tmp_path / "logs" / "test.log"
    ns["Path"] = Path
    ns["sys"] = sys
    ns["re"] = re
    exec(code, ns)
    issues = ns["check"]()
    assert any("HARDCODED KEY" in i and "deploy" in i for i in issues)


def test_xoxb_slack_token_detected(tmp_path):
    """Slack bot tokens (xoxb-) should be flagged."""
    eff_dir = tmp_path / "germline" / "effectors"
    eff_dir.mkdir(parents=True)
    bad_script = eff_dir / "slack-bot"
    bad_script.write_text('SLACK_TOKEN = "xoxb-1234567890-abcdefg-hijklmnop"\n')

    launch_dir = tmp_path / "Library" / "LaunchAgents"
    launch_dir.mkdir(parents=True)

    code = open(_effector_path).read().replace(
        'Path.home() / "germline" / "effectors"',
        f'Path({repr(str(eff_dir))})',
    )
    ns = {"__name__": "lh_test_xoxb", "subprocess": MagicMock()}
    ns["LAUNCH_DIR"] = launch_dir
    ns["SOURCE_DIR"] = tmp_path / "nope"
    ns["LOG"] = tmp_path / "logs" / "test.log"
    ns["Path"] = Path
    ns["sys"] = sys
    ns["re"] = re
    exec(code, ns)
    issues = ns["check"]()
    assert any("HARDCODED KEY" in i and "slack-bot" in i for i in issues)


def test_security_find_generic_not_flagged(tmp_path):
    """Lines containing 'security find' should not be flagged even with key patterns."""
    eff_dir = tmp_path / "germline" / "effectors"
    eff_dir.mkdir(parents=True)
    ok_script = eff_dir / "safe-script"
    # xoxb- pattern but with "security find" in the line — should be skipped
    ok_script.write_text('TOKEN = subprocess.run(["security find", "xoxb-abc-123"])\n')

    launch_dir = tmp_path / "Library" / "LaunchAgents"
    launch_dir.mkdir(parents=True)

    code = open(_effector_path).read().replace(
        'Path.home() / "germline" / "effectors"',
        f'Path({repr(str(eff_dir))})',
    )
    ns = {"__name__": "lh_test_safe", "subprocess": MagicMock()}
    ns["LAUNCH_DIR"] = launch_dir
    ns["SOURCE_DIR"] = tmp_path / "nope"
    ns["LOG"] = tmp_path / "logs" / "test.log"
    ns["Path"] = Path
    ns["sys"] = sys
    ns["re"] = re
    exec(code, ns)
    issues = ns["check"]()
    assert not any("safe-script" in i for i in issues)


def test_binary_files_skipped(tmp_path):
    """Binary files (containing null bytes) should be skipped during secret scan."""
    eff_dir = tmp_path / "germline" / "effectors"
    eff_dir.mkdir(parents=True)
    bin_file = eff_dir / "binary-tool"
    bin_file.write_bytes(b'\x00\x00\x00sk-abcdefghijklmnopqrstuvwxyz123456\x00')

    launch_dir = tmp_path / "Library" / "LaunchAgents"
    launch_dir.mkdir(parents=True)

    code = open(_effector_path).read().replace(
        'Path.home() / "germline" / "effectors"',
        f'Path({repr(str(eff_dir))})',
    )
    ns = {"__name__": "lh_test_bin", "subprocess": MagicMock()}
    ns["LAUNCH_DIR"] = launch_dir
    ns["SOURCE_DIR"] = tmp_path / "nope"
    ns["LOG"] = tmp_path / "logs" / "test.log"
    ns["Path"] = Path
    ns["sys"] = sys
    ns["re"] = re
    exec(code, ns)
    issues = ns["check"]()
    assert not any("binary-tool" in i for i in issues)


# ── Empty / clean ─────────────────────────────────────────────────────

def test_all_clear_when_no_issues(tmp_path):
    """No issues when directory is empty."""
    launch_dir = tmp_path / "Library" / "LaunchAgents"
    launch_dir.mkdir(parents=True)

    eff_dir = tmp_path / "germline" / "effectors"
    eff_dir.mkdir(parents=True)

    code = open(_effector_path).read().replace(
        'Path.home() / "germline" / "effectors"',
        f'Path({repr(str(eff_dir))})',
    )
    ns = {"__name__": "lh_test_clear", "subprocess": MagicMock()}
    ns["LAUNCH_DIR"] = launch_dir
    ns["SOURCE_DIR"] = tmp_path / "nope"
    ns["LOG"] = tmp_path / "logs" / "test.log"
    ns["Path"] = Path
    ns["sys"] = sys
    ns["re"] = re
    exec(code, ns)
    issues = ns["check"]()
    assert issues == []


# ── vivesca namespace ─────────────────────────────────────────────────

def test_vivesca_plists_checked(tmp_path):
    """com.vivesca.* plists should also be checked."""
    launch_dir = tmp_path / "Library" / "LaunchAgents"
    launch_dir.mkdir(parents=True)
    source_dir = tmp_path / "epigenome" / "oscillators"
    source_dir.mkdir(parents=True)

    deployed = launch_dir / "com.vivesca.app.plist"
    deployed.write_text('not xml at all')
    source = source_dir / "com.vivesca.app.plist"
    source.write_text('also not xml')

    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = "invalid"

    ns = {"__name__": "lh_test_vivesca", "subprocess": MagicMock()}
    ns["subprocess"].run.return_value = mock_result
    ns["LAUNCH_DIR"] = launch_dir
    ns["SOURCE_DIR"] = source_dir
    ns["LOG"] = tmp_path / "logs" / "test.log"
    ns["Path"] = Path
    ns["sys"] = sys
    ns["re"] = re

    exec(open(_effector_path).read(), ns)
    issues = ns["check"]()
    assert any("INVALID" in i and "com.vivesca.app.plist" in i for i in issues)


# ── __main__ exit codes ───────────────────────────────────────────────

def test_main_exits_0_on_clean(capsys, tmp_path):
    """__main__ should exit 0 and print 'All clear.' when no issues."""
    launch_dir = tmp_path / "Library" / "LaunchAgents"
    launch_dir.mkdir(parents=True)
    eff_dir = tmp_path / "germline" / "effectors"
    eff_dir.mkdir(parents=True)
    log = tmp_path / "logs" / "test.log"

    code = open(_effector_path).read()
    code = code.replace(
        'Path.home() / "germline" / "effectors"',
        f'Path({repr(str(eff_dir))})',
    )
    ns = {"__name__": "__main__", "subprocess": MagicMock()}
    ns["LAUNCH_DIR"] = launch_dir
    ns["SOURCE_DIR"] = tmp_path / "nope"
    ns["LOG"] = log
    ns["Path"] = Path
    ns["sys"] = MagicMock()
    ns["re"] = re

    with pytest.raises(SystemExit) as exc_info:
        exec(code, ns)
    assert exc_info.value.code == 0
    assert "All clear" in capsys.readouterr().out


def test_main_exits_1_on_issues(capsys, tmp_path):
    """__main__ should exit 1 and print issues when found."""
    launch_dir = tmp_path / "Library" / "LaunchAgents"
    launch_dir.mkdir(parents=True)
    bad_plist = launch_dir / "com.terry.bad.plist"
    bad_plist.write_text('not-xml')
    eff_dir = tmp_path / "germline" / "effectors"
    eff_dir.mkdir(parents=True)
    log = tmp_path / "logs" / "test.log"

    mock_result = MagicMock()
    mock_result.returncode = 1

    code = open(_effector_path).read()
    code = code.replace(
        'Path.home() / "germline" / "effectors"',
        f'Path({repr(str(eff_dir))})',
    )
    ns = {"__name__": "__main__", "subprocess": MagicMock()}
    ns["subprocess"].run.return_value = mock_result
    ns["LAUNCH_DIR"] = launch_dir
    ns["SOURCE_DIR"] = tmp_path / "nope"
    ns["LOG"] = log
    ns["Path"] = Path
    ns["sys"] = MagicMock()
    ns["re"] = re

    with pytest.raises(SystemExit) as exc_info:
        exec(code, ns)
    assert exc_info.value.code == 1
    output = capsys.readouterr().out
    assert "LaunchAgent health issues" in output
    assert "INVALID" in output
    # Also verify log was written
    assert log.exists()
    log_content = log.read_text()
    assert "INVALID" in log_content
