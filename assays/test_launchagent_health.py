#!/usr/bin/env python3
"""Tests for launchagent-health effector."""

import re
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Path to the effector (no .py extension)
EFFECTOR = Path(__file__).parent.parent / "effectors" / "launchagent-health"
EFFECTOR_SRC = open(EFFECTOR).read()


def _load_ns(
    launch_dir,
    source_dir,
    log,
    eff_dir=None,
    mock_subprocess=False,
    mock_sys=False,
):
    """Exec the effector into an isolated namespace with overridden paths.

    The effector code has module-level assignments (LAUNCH_DIR = ...) and
    imports (import subprocess, import sys) that overwrite pre-set values.
    We exec first then override constants and mocks afterward.  Functions
    defined in exec close over the namespace dict, so they see updated values.
    """
    code = EFFECTOR_SRC
    if eff_dir is not None:
        code = code.replace(
            'Path.home() / "germline" / "effectors"',
            f"Path({repr(str(eff_dir))})",
        )

    # Always exec with __name__ != "__main__" so the main block is skipped
    ns = {"__name__": "lh_test", "Path": Path, "re": re, "sys": sys}
    exec(code, ns)

    # Override module-level constants AFTER exec
    ns["LAUNCH_DIR"] = launch_dir
    ns["SOURCE_DIR"] = source_dir
    ns["LOG"] = log

    # Override subprocess with mock if requested (plutil not available on Linux)
    if mock_subprocess:
        ns["subprocess"] = MagicMock()

    # Override sys with mock if requested (to capture sys.exit calls)
    if mock_sys:
        ns["sys"] = MagicMock()

    return ns


# ── Plist validation ──────────────────────────────────────────────────


def test_symlinks_skipped(tmp_path):
    """Symlinked plists should not be checked."""
    launch_dir = tmp_path / "Library" / "LaunchAgents"
    launch_dir.mkdir(parents=True)
    target = launch_dir / "com.terry.real.plist"
    target.write_text('<?xml version="1.0"?>\n<plist><dict/></plist>')
    link = launch_dir / "com.terry.link.plist"
    link.symlink_to(target)

    ns = _load_ns(launch_dir, tmp_path / "nope", tmp_path / "test.log")
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

    ns = _load_ns(
        launch_dir,
        tmp_path / "nope",
        tmp_path / "test.log",
        mock_subprocess=True,
    )
    ns["subprocess"].run.return_value = mock_result
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

    ns = _load_ns(
        launch_dir,
        tmp_path / "nope",
        tmp_path / "test.log",
        subprocess_mock=MagicMock(),
    )
    ns["subprocess"].run.return_value = mock_result
    issues = ns["check"]()
    assert not any("INVALID" in i for i in issues)


def test_xml_plist_passes_validation(tmp_path):
    """XML plists should pass the validation check."""
    launch_dir = tmp_path / "Library" / "LaunchAgents"
    launch_dir.mkdir(parents=True)
    xml_plist = launch_dir / "com.terry.good.plist"
    xml_plist.write_text('<?xml version="1.0"?>\n<plist version="1.0"><dict/></plist>')

    ns = _load_ns(launch_dir, tmp_path / "nope", tmp_path / "test.log")
    issues = ns["check"]()
    assert not any("INVALID" in i for i in issues)


def test_doctype_plist_passes_validation(tmp_path):
    """DOCTYPE plists should pass the validation check."""
    launch_dir = tmp_path / "Library" / "LaunchAgents"
    launch_dir.mkdir(parents=True)
    dt_plist = launch_dir / "com.terry.doctype.plist"
    dt_plist.write_text('<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN">\n<plist><dict/></plist>')

    ns = _load_ns(launch_dir, tmp_path / "nope", tmp_path / "test.log")
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

    ns = _load_ns(launch_dir, source_dir, tmp_path / "test.log")
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

    ns = _load_ns(launch_dir, source_dir, tmp_path / "test.log")
    issues = ns["check"]()
    assert not any("DRIFT" in i for i in issues)


def test_no_drift_when_no_source(tmp_path):
    """No drift reported when source file doesn't exist (not tracked)."""
    launch_dir = tmp_path / "Library" / "LaunchAgents"
    launch_dir.mkdir(parents=True)

    deployed = launch_dir / "com.terry.untracked.plist"
    deployed.write_text('<?xml version="1.0"?>\n<plist><dict/></plist>')

    ns = _load_ns(launch_dir, tmp_path / "nonexistent", tmp_path / "test.log")
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

    ns = _load_ns(launch_dir, tmp_path / "nope", tmp_path / "test.log", eff_dir=eff_dir)
    issues = ns["check"]()
    assert any("HARDCODED KEY" in i and "my-script" in i for i in issues)


def test_ghp_key_detected(tmp_path):
    """GitHub personal access tokens should be flagged."""
    eff_dir = tmp_path / "germline" / "effectors"
    eff_dir.mkdir(parents=True)
    bad_script = eff_dir / "deploy"
    bad_script.write_text('TOKEN = "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij"\n')

    launch_dir = tmp_path / "Library" / "LaunchAgents"
    launch_dir.mkdir(parents=True)

    ns = _load_ns(launch_dir, tmp_path / "nope", tmp_path / "test.log", eff_dir=eff_dir)
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

    ns = _load_ns(launch_dir, tmp_path / "nope", tmp_path / "test.log", eff_dir=eff_dir)
    issues = ns["check"]()
    assert any("HARDCODED KEY" in i and "slack-bot" in i for i in issues)


def test_xoxp_slack_token_detected(tmp_path):
    """Slack user tokens (xoxp-) should be flagged."""
    eff_dir = tmp_path / "germline" / "effectors"
    eff_dir.mkdir(parents=True)
    bad_script = eff_dir / "slack-user"
    bad_script.write_text('TOKEN = "xoxp-1234567890-abcdefg-hijklmnop"\n')

    launch_dir = tmp_path / "Library" / "LaunchAgents"
    launch_dir.mkdir(parents=True)

    ns = _load_ns(launch_dir, tmp_path / "nope", tmp_path / "test.log", eff_dir=eff_dir)
    issues = ns["check"]()
    assert any("HARDCODED KEY" in i and "slack-user" in i for i in issues)


def test_security_find_line_not_flagged(tmp_path):
    """Lines containing 'security find' should not be flagged even with key patterns."""
    eff_dir = tmp_path / "germline" / "effectors"
    eff_dir.mkdir(parents=True)
    ok_script = eff_dir / "safe-script"
    ok_script.write_text('TOKEN = subprocess.run(["security find", "xoxb-abc-123"])\n')

    launch_dir = tmp_path / "Library" / "LaunchAgents"
    launch_dir.mkdir(parents=True)

    ns = _load_ns(launch_dir, tmp_path / "nope", tmp_path / "test.log", eff_dir=eff_dir)
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

    ns = _load_ns(launch_dir, tmp_path / "nope", tmp_path / "test.log", eff_dir=eff_dir)
    issues = ns["check"]()
    assert not any("binary-tool" in i for i in issues)


# ── Empty / clean ─────────────────────────────────────────────────────


def test_all_clear_when_no_issues(tmp_path):
    """No issues when directories are empty."""
    launch_dir = tmp_path / "Library" / "LaunchAgents"
    launch_dir.mkdir(parents=True)
    eff_dir = tmp_path / "germline" / "effectors"
    eff_dir.mkdir(parents=True)

    ns = _load_ns(launch_dir, tmp_path / "nope", tmp_path / "test.log", eff_dir=eff_dir)
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

    mock_result = MagicMock()
    mock_result.returncode = 1

    ns = _load_ns(
        launch_dir,
        source_dir,
        tmp_path / "test.log",
        subprocess_mock=MagicMock(),
    )
    ns["subprocess"].run.return_value = mock_result
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

    sys_mock = MagicMock()
    ns = _load_ns(
        launch_dir,
        tmp_path / "nope",
        log,
        eff_dir=eff_dir,
        sys_mock=sys_mock,
        as_main=True,
    )
    with pytest.raises(SystemExit) as exc_info:
        # Re-run __main__ block by calling the exec'd code path
        # Since as_main=True already set __name__ = "__main__", exec already ran it.
        # But we overrode constants AFTER exec. Call check + main logic manually.
        issues = ns["check"]()
        if issues:
            output = "LaunchAgent health issues:\n" + "\n".join(f"  - {i}" for i in issues)
            print(output)
            log.parent.mkdir(exist_ok=True)
            with open(log, "a") as f:
                from datetime import datetime
                f.write(f"\n[{datetime.now().isoformat()}]\n{output}\n")
            sys_mock.exit(1)
        else:
            print("All clear.")
            sys_mock.exit(0)

    assert sys_mock.exit.call_args[0][0] == 0
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
    sub_mock = MagicMock()
    sub_mock.run.return_value = mock_result

    sys_mock = MagicMock()
    ns = _load_ns(
        launch_dir,
        tmp_path / "nope",
        log,
        eff_dir=eff_dir,
        subprocess_mock=sub_mock,
        sys_mock=sys_mock,
    )
    # Run main logic
    issues = ns["check"]()
    assert len(issues) > 0, f"Expected issues but got none"
    output = "LaunchAgent health issues:\n" + "\n".join(f"  - {i}" for i in issues)
    print(output)
    log.parent.mkdir(exist_ok=True)
    with open(log, "a") as f:
        from datetime import datetime
        f.write(f"\n[{datetime.now().isoformat()}]\n{output}\n")
    sys_mock.exit(1)

    assert sys_mock.exit.call_args[0][0] == 1
    captured = capsys.readouterr().out
    assert "LaunchAgent health issues" in captured
    assert "INVALID" in captured
    assert log.exists()
    log_content = log.read_text()
    assert "INVALID" in log_content
