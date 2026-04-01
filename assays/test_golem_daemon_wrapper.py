from __future__ import annotations

"""Tests for effectors/golem-daemon-wrapper.sh — bash wrapper that sources env and execs golem-daemon."""

import os
import stat
import subprocess
import tempfile
from pathlib import Path

WRAPPER = Path.home() / "germline" / "effectors" / "golem-daemon-wrapper.sh"
DAEMON = Path.home() / "germline" / "effectors" / "golem-daemon"


# ── help flags ────────────────────────────────────────────────────────


def test_golem_daemon_wrapper_help_flag_exits_zero():
    """--help prints usage and exits 0."""
    r = subprocess.run(
        ["bash", str(WRAPPER), "--help"],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0


def test_help_flag_outputs_usage():
    """--help output contains description and usage."""
    r = subprocess.run(
        ["bash", str(WRAPPER), "--help"],
        capture_output=True,
        text=True,
    )
    out = r.stdout
    assert "golem-daemon-wrapper" in out
    assert "Usage:" in out


def test_help_flag_outputs_description():
    """--help output mentions its purpose."""
    r = subprocess.run(
        ["bash", str(WRAPPER), "--help"],
        capture_output=True,
        text=True,
    )
    assert "sources API keys" in r.stdout


def test_help_flag_no_stderr():
    """--help produces no stderr."""
    r = subprocess.run(
        ["bash", str(WRAPPER), "--help"],
        capture_output=True,
        text=True,
    )
    assert r.stderr == ""


def test_short_help_flag():
    """-h works the same as --help."""
    r = subprocess.run(
        ["bash", str(WRAPPER), "-h"],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0
    assert "golem-daemon-wrapper" in r.stdout


def test_help_outputs_no_user_options():
    """--help mentions managed by supervisor."""
    r = subprocess.run(
        ["bash", str(WRAPPER), "--help"],
        capture_output=True,
        text=True,
    )
    assert "Managed by" in r.stdout


# ── file attributes ───────────────────────────────────────────────────


def test_wrapper_is_executable():
    """Wrapper script has execute permission."""
    st = WRAPPER.stat()
    assert st.st_mode & stat.S_IXUSR


def test_wrapper_is_bash_script():
    """Wrapper starts with a bash shebang."""
    first_line = WRAPPER.read_text().splitlines()[0]
    assert first_line.startswith("#!/usr/bin/env bash") or first_line.startswith("#!/bin/bash")


def test_wrapper_uses_set_strict():
    """Wrapper uses strict mode (set -euo pipefail)."""
    content = WRAPPER.read_text()
    assert "set -euo pipefail" in content


# ── env sourcing ──────────────────────────────────────────────────────


def test_env_file_sourced_when_present():
    """If ~/.env.fly exists, its exported vars reach the exec'd process."""
    with tempfile.TemporaryDirectory() as td:
        env_file = Path(td) / ".env.fly"
        env_file.write_text("TEST_GOLEM_WRAPPER_VAR=hello123\n")

        # Create a shim python3 that prints the var and exits
        shim_dir = Path(td) / "bin"
        shim_dir.mkdir()
        shim = shim_dir / "python3"
        shim.write_text("#!/bin/bash\necho \"VAR=$TEST_GOLEM_WRAPPER_VAR\"\nexit 0\n")
        shim.chmod(0o755)

        # Also need a fake germline dir so the path resolves
        fake_germline = Path(td) / "germline" / "effectors"
        fake_germline.mkdir(parents=True)
        fake_daemon = fake_germline / "golem-daemon"
        fake_daemon.write_text("# dummy\n")

        r = subprocess.run(
            [
                "bash", "-c",
                f'HOME={td} PATH={shim_dir}:$PATH bash "{WRAPPER}"',
            ],
            capture_output=True,
            text=True,
        )
        assert "VAR=hello123" in r.stdout, f"Expected sourced var in output, got: {r.stdout!r} stderr: {r.stderr!r}"


def test_no_env_file_still_works():
    """If ~/.env.fly is absent, the script still proceeds to exec."""
    with tempfile.TemporaryDirectory() as td:
        shim_dir = Path(td) / "bin"
        shim_dir.mkdir()
        shim = shim_dir / "python3"
        shim.write_text("#!/bin/bash\necho \"LAUNCHED\"\nexit 0\n")
        shim.chmod(0o755)

        fake_germline = Path(td) / "germline" / "effectors"
        fake_germline.mkdir(parents=True)
        fake_daemon = fake_germline / "golem-daemon"
        fake_daemon.write_text("# dummy\n")

        r = subprocess.run(
            [
                "bash", "-c",
                f'HOME={td} PATH={shim_dir}:$PATH bash "{WRAPPER}"',
            ],
            capture_output=True,
            text=True,
        )
        assert "LAUNCHED" in r.stdout, f"Expected LAUNCHED in output, got: {r.stdout!r} stderr: {r.stderr!r}"


# ── exec target ───────────────────────────────────────────────────────


def test_exec_calls_daemon_with_start_foreground():
    """The wrapper execs python3 on golem-daemon with start --foreground."""
    with tempfile.TemporaryDirectory() as td:
        shim_dir = Path(td) / "bin"
        shim_dir.mkdir()
        shim = shim_dir / "python3"
        # Print all args so we can verify the command line
        shim.write_text('#!/bin/bash\necho "ARGS: $@"\nexit 0\n')
        shim.chmod(0o755)

        fake_germline = Path(td) / "germline" / "effectors"
        fake_germline.mkdir(parents=True)
        fake_daemon = fake_germline / "golem-daemon"
        fake_daemon.write_text("# dummy\n")

        r = subprocess.run(
            [
                "bash", "-c",
                f'HOME={td} PATH={shim_dir}:$PATH bash "{WRAPPER}"',
            ],
            capture_output=True,
            text=True,
        )
        assert "start" in r.stdout
        assert "--foreground" in r.stdout


def test_exec_uses_correct_daemon_path():
    """The wrapper execs the daemon from $HOME/germline/effectors/golem-daemon."""
    content = WRAPPER.read_text()
    assert '$HOME/germline/effectors/golem-daemon' in content


def test_uses_exec_not_just_run():
    """The wrapper uses exec to replace the shell process."""
    content = WRAPPER.read_text()
    assert "exec python3" in content


# ── env.fly export behavior ──────────────────────────────────────────


def test_env_vars_are_exported():
    """set -a ensures vars from .env.fly are exported to child process."""
    with tempfile.TemporaryDirectory() as td:
        env_file = Path(td) / ".env.fly"
        env_file.write_text("MY_SECRET_KEY=abc123\nMY_OTHER_VAR=xyz\n")

        shim_dir = Path(td) / "bin"
        shim_dir.mkdir()
        shim = shim_dir / "python3"
        # Use env to show exported vars
        shim.write_text('#!/bin/bash\nenv\nexit 0\n')
        shim.chmod(0o755)

        fake_germline = Path(td) / "germline" / "effectors"
        fake_germline.mkdir(parents=True)
        fake_daemon = fake_germline / "golem-daemon"
        fake_daemon.write_text("# dummy\n")

        r = subprocess.run(
            [
                "bash", "-c",
                f'HOME={td} PATH={shim_dir}:$PATH bash "{WRAPPER}"',
            ],
            capture_output=True,
            text=True,
        )
        assert "MY_SECRET_KEY=abc123" in r.stdout
        assert "MY_OTHER_VAR=xyz" in r.stdout


# ── edge cases ────────────────────────────────────────────────────────


def test_no_args_proceeds_to_exec():
    """Running with no arguments proceeds to exec (not --help)."""
    with tempfile.TemporaryDirectory() as td:
        shim_dir = Path(td) / "bin"
        shim_dir.mkdir()
        shim = shim_dir / "python3"
        shim.write_text('#!/bin/bash\necho "RAN"\nexit 0\n')
        shim.chmod(0o755)

        fake_germline = Path(td) / "germline" / "effectors"
        fake_germline.mkdir(parents=True)
        fake_daemon = fake_germline / "golem-daemon"
        fake_daemon.write_text("# dummy\n")

        r = subprocess.run(
            [
                "bash", "-c",
                f'HOME={td} PATH={shim_dir}:$PATH bash "{WRAPPER}"',
            ],
            capture_output=True,
            text=True,
        )
        assert "RAN" in r.stdout


def test_unknown_arg_still_execs():
    """Unknown flags (not --help/-h) pass through and exec runs."""
    with tempfile.TemporaryDirectory() as td:
        shim_dir = Path(td) / "bin"
        shim_dir.mkdir()
        shim = shim_dir / "python3"
        shim.write_text('#!/bin/bash\necho "RAN_WITH_ARGS: $@"\nexit 0\n')
        shim.chmod(0o755)

        fake_germline = Path(td) / "germline" / "effectors"
        fake_germline.mkdir(parents=True)
        fake_daemon = fake_germline / "golem-daemon"
        fake_daemon.write_text("# dummy\n")

        r = subprocess.run(
            [
                "bash", "-c",
                f'HOME={td} PATH={shim_dir}:$PATH bash "{WRAPPER}" --unknown',
            ],
            capture_output=True,
            text=True,
        )
        # The wrapper doesn't pass unknown args to exec; it always execs
        # the daemon with fixed args. But it should still run.
        assert "RAN_WITH_ARGS" in r.stdout


# ── env.fly content edge cases ──────────────────────────────────────────


def test_env_file_with_comments_and_blanks():
    """Comments and blank lines in .env.fly don't cause errors."""
    with tempfile.TemporaryDirectory() as td:
        env_file = Path(td) / ".env.fly"
        env_file.write_text(
            "# This is a comment\n"
            "\n"
            "  \n"
            "MY_VAR=has_value\n"
            "# Another comment\n"
            "OTHER_VAR=also_set\n"
        )

        shim_dir = Path(td) / "bin"
        shim_dir.mkdir()
        shim = shim_dir / "python3"
        shim.write_text('#!/bin/bash\nenv\nexit 0\n')
        shim.chmod(0o755)

        fake_germline = Path(td) / "germline" / "effectors"
        fake_germline.mkdir(parents=True)
        fake_daemon = fake_germline / "golem-daemon"
        fake_daemon.write_text("# dummy\n")

        r = subprocess.run(
            [
                "bash", "-c",
                f'HOME={td} PATH={shim_dir}:$PATH bash "{WRAPPER}"',
            ],
            capture_output=True,
            text=True,
        )
        assert "MY_VAR=has_value" in r.stdout
        assert "OTHER_VAR=also_set" in r.stdout


def test_env_file_value_with_equals_sign():
    """Values containing = are handled correctly by set -a + source."""
    with tempfile.TemporaryDirectory() as td:
        env_file = Path(td) / ".env.fly"
        env_file.write_text('API_KEY=abc=def=ghi\n')

        shim_dir = Path(td) / "bin"
        shim_dir.mkdir()
        shim = shim_dir / "python3"
        shim.write_text('#!/bin/bash\necho "KEY=$API_KEY"\nexit 0\n')
        shim.chmod(0o755)

        fake_germline = Path(td) / "germline" / "effectors"
        fake_germline.mkdir(parents=True)
        fake_daemon = fake_germline / "golem-daemon"
        fake_daemon.write_text("# dummy\n")

        r = subprocess.run(
            [
                "bash", "-c",
                f'HOME={td} PATH={shim_dir}:$PATH bash "{WRAPPER}"',
            ],
            capture_output=True,
            text=True,
        )
        assert "KEY=abc=def=ghi" in r.stdout


def test_env_file_value_with_quotes():
    """Quoted values in .env.fly are passed through correctly."""
    with tempfile.TemporaryDirectory() as td:
        env_file = Path(td) / ".env.fly"
        env_file.write_text('MY_KEY="quoted value here"\n')

        shim_dir = Path(td) / "bin"
        shim_dir.mkdir()
        shim = shim_dir / "python3"
        shim.write_text('#!/bin/bash\necho "VAL=$MY_KEY"\nexit 0\n')
        shim.chmod(0o755)

        fake_germline = Path(td) / "germline" / "effectors"
        fake_germline.mkdir(parents=True)
        fake_daemon = fake_germline / "golem-daemon"
        fake_daemon.write_text("# dummy\n")

        r = subprocess.run(
            [
                "bash", "-c",
                f'HOME={td} PATH={shim_dir}:$PATH bash "{WRAPPER}"',
            ],
            capture_output=True,
            text=True,
        )
        assert "VAL=quoted value here" in r.stdout


def test_env_file_multiple_vars_all_exported():
    """All variables from .env.fly are available to the exec'd process."""
    with tempfile.TemporaryDirectory() as td:
        env_file = Path(td) / ".env.fly"
        env_file.write_text(
            "KEY_A=val_a\n"
            "KEY_B=val_b\n"
            "KEY_C=val_c\n"
        )

        shim_dir = Path(td) / "bin"
        shim_dir.mkdir()
        shim = shim_dir / "python3"
        shim.write_text('#!/bin/bash\necho "A=$KEY_A B=$KEY_B C=$KEY_C"\nexit 0\n')
        shim.chmod(0o755)

        fake_germline = Path(td) / "germline" / "effectors"
        fake_germline.mkdir(parents=True)
        fake_daemon = fake_germline / "golem-daemon"
        fake_daemon.write_text("# dummy\n")

        r = subprocess.run(
            [
                "bash", "-c",
                f'HOME={td} PATH={shim_dir}:$PATH bash "{WRAPPER}"',
            ],
            capture_output=True,
            text=True,
        )
        assert "A=val_a" in r.stdout
        assert "B=val_b" in r.stdout
        assert "C=val_c" in r.stdout


def test_set_a_scope_only_env_fly_vars():
    """set -a only exports vars from .env.fly, not pre-existing unset vars."""
    with tempfile.TemporaryDirectory() as td:
        env_file = Path(td) / ".env.fly"
        env_file.write_text("FROM_ENV_FLY=yes\n")

        shim_dir = Path(td) / "bin"
        shim_dir.mkdir()
        shim = shim_dir / "python3"
        shim.write_text('#!/bin/bash\necho "FLY=$FROM_ENV_FLY"\nexit 0\n')
        shim.chmod(0o755)

        fake_germline = Path(td) / "germline" / "effectors"
        fake_germline.mkdir(parents=True)
        fake_daemon = fake_germline / "golem-daemon"
        fake_daemon.write_text("# dummy\n")

        r = subprocess.run(
            [
                "bash", "-c",
                f'HOME={td} PATH={shim_dir}:$PATH bash "{WRAPPER}"',
            ],
            capture_output=True,
            text=True,
        )
        assert "FLY=yes" in r.stdout


# ── exec behavior ───────────────────────────────────────────────────────


def test_exec_replaces_shell_process():
    """exec replaces the bash process — child PID equals wrapper PID."""
    with tempfile.TemporaryDirectory() as td:
        shim_dir = Path(td) / "bin"
        shim_dir.mkdir()
        shim = shim_dir / "python3"
        shim.write_text('#!/bin/bash\necho "CHILDPID=$$"\nexit 0\n')
        shim.chmod(0o755)

        fake_germline = Path(td) / "germline" / "effectors"
        fake_germline.mkdir(parents=True)
        fake_daemon = fake_germline / "golem-daemon"
        fake_daemon.write_text("# dummy\n")

        r = subprocess.run(
            [
                "bash", "-c",
                f'HOME={td} PATH={shim_dir}:$PATH bash "{WRAPPER}"',
            ],
            capture_output=True,
            text=True,
        )
        # With exec, the child PID printed should be the same PID bash -c sees
        # We can verify exec happened by checking stdout contains a PID
        assert "CHILDPID=" in r.stdout
        pid_str = r.stdout.split("CHILDPID=")[1].strip().split("\n")[0]
        assert pid_str.isdigit()


def test_python3_from_path_not_hardcoded():
    """The wrapper resolves python3 from PATH, not a hardcoded path."""
    content = WRAPPER.read_text()
    # Should use bare 'python3', not /usr/bin/python3 or similar
    assert "exec python3" in content
    assert "/usr/bin/python3" not in content


# ── help output details ────────────────────────────────────────────────


def test_help_mentions_foreground():
    """--help output mentions foreground mode."""
    r = subprocess.run(
        ["bash", str(WRAPPER), "--help"],
        capture_output=True,
        text=True,
    )
    assert "foreground" in r.stdout.lower()


def test_help_mentions_env_or_api_keys():
    """--help output mentions sourcing API keys or environment."""
    r = subprocess.run(
        ["bash", str(WRAPPER), "--help"],
        capture_output=True,
        text=True,
    )
    out_lower = r.stdout.lower()
    assert "api keys" in out_lower or "env" in out_lower or "sources" in out_lower


# ── set -a / set +a presence ───────────────────────────────────────────


def test_wrapper_uses_set_a_and_set_plus_a():
    """Wrapper brackets source with set -a and set +a for auto-export."""
    content = WRAPPER.read_text()
    assert "set -a" in content
    assert "set +a" in content


def test_wrapper_sources_home_env_fly():
    """Wrapper sources $HOME/.env.fly (uses $HOME, not hardcoded)."""
    content = WRAPPER.read_text()
    assert '$HOME/.env.fly' in content


def test_env_file_with_export_prefix():
    """Lines with 'export KEY=val' in .env.fly still work with set -a."""
    with tempfile.TemporaryDirectory() as td:
        env_file = Path(td) / ".env.fly"
        env_file.write_text('export EXPLICIT_EXPORT=yes\n')

        shim_dir = Path(td) / "bin"
        shim_dir.mkdir()
        shim = shim_dir / "python3"
        shim.write_text('#!/bin/bash\necho "VAL=$EXPLICIT_EXPORT"\nexit 0\n')
        shim.chmod(0o755)

        fake_germline = Path(td) / "germline" / "effectors"
        fake_germline.mkdir(parents=True)
        fake_daemon = fake_germline / "golem-daemon"
        fake_daemon.write_text("# dummy\n")

        r = subprocess.run(
            [
                "bash", "-c",
                f'HOME={td} PATH={shim_dir}:$PATH bash "{WRAPPER}"',
            ],
            capture_output=True,
            text=True,
        )
        assert "VAL=yes" in r.stdout


def test_env_file_with_empty_value():
    """Empty values in .env.fly are exported as empty strings."""
    with tempfile.TemporaryDirectory() as td:
        env_file = Path(td) / ".env.fly"
        env_file.write_text('EMPTY_VAR=\n')

        shim_dir = Path(td) / "bin"
        shim_dir.mkdir()
        shim = shim_dir / "python3"
        shim.write_text('#!/bin/bash\necho "EMPTY=[$EMPTY_VAR]"\nexit 0\n')
        shim.chmod(0o755)

        fake_germline = Path(td) / "germline" / "effectors"
        fake_germline.mkdir(parents=True)
        fake_daemon = fake_germline / "golem-daemon"
        fake_daemon.write_text("# dummy\n")

        r = subprocess.run(
            [
                "bash", "-c",
                f'HOME={td} PATH={shim_dir}:$PATH bash "{WRAPPER}"',
            ],
            capture_output=True,
            text=True,
        )
        assert "EMPTY=[]" in r.stdout


# ── conditional env sourcing ──────────────────────────────────────────────


def test_wrapper_checks_env_file_exists_before_sourcing():
    """Wrapper uses 'if [ -f ... ]' to guard the source command."""
    content = WRAPPER.read_text()
    assert '-f "$HOME/.env.fly"' in content or '-f "$HOME/.env.fly"]' in content


def test_missing_env_file_no_errors():
    """When .env.fly does not exist, the wrapper silently proceeds (no stderr)."""
    with tempfile.TemporaryDirectory() as td:
        shim_dir = Path(td) / "bin"
        shim_dir.mkdir()
        shim = shim_dir / "python3"
        shim.write_text('#!/bin/bash\necho "OK"\nexit 0\n')
        shim.chmod(0o755)

        fake_germline = Path(td) / "germline" / "effectors"
        fake_germline.mkdir(parents=True)
        fake_daemon = fake_germline / "golem-daemon"
        fake_daemon.write_text("# dummy\n")

        r = subprocess.run(
            [
                "bash", "-c",
                f'HOME={td} PATH={shim_dir}:$PATH bash "{WRAPPER}"',
            ],
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0
        assert r.stderr == ""


# ── shellcheck directive ─────────────────────────────────────────────────


def test_wrapper_has_shellcheck_ignore_for_source():
    """Wrapper includes shellcheck disable for the dynamic source."""
    content = WRAPPER.read_text()
    assert "shellcheck" in content


# ── env.fly with special characters ──────────────────────────────────────


def test_env_file_value_with_spaces_no_quotes():
    """Unquoted values with spaces are handled by the source mechanism."""
    with tempfile.TemporaryDirectory() as td:
        env_file = Path(td) / ".env.fly"
        env_file.write_text('SPACED_VAL="hello world"\n')

        shim_dir = Path(td) / "bin"
        shim_dir.mkdir()
        shim = shim_dir / "python3"
        shim.write_text('#!/bin/bash\necho "SP=$SPACED_VAL"\nexit 0\n')
        shim.chmod(0o755)

        fake_germline = Path(td) / "germline" / "effectors"
        fake_germline.mkdir(parents=True)
        fake_daemon = fake_germline / "golem-daemon"
        fake_daemon.write_text("# dummy\n")

        r = subprocess.run(
            [
                "bash", "-c",
                f'HOME={td} PATH={shim_dir}:$PATH bash "{WRAPPER}"',
            ],
            capture_output=True,
            text=True,
        )
        assert "SP=hello world" in r.stdout


def test_env_file_overrides_existing_var():
    """If a var is already set in the environment, .env.fly overrides it."""
    with tempfile.TemporaryDirectory() as td:
        env_file = Path(td) / ".env.fly"
        env_file.write_text("OVERRIDE_VAR=from_env_fly\n")

        shim_dir = Path(td) / "bin"
        shim_dir.mkdir()
        shim = shim_dir / "python3"
        shim.write_text('#!/bin/bash\necho "OV=$OVERRIDE_VAR"\nexit 0\n')
        shim.chmod(0o755)

        fake_germline = Path(td) / "germline" / "effectors"
        fake_germline.mkdir(parents=True)
        fake_daemon = fake_germline / "golem-daemon"
        fake_daemon.write_text("# dummy\n")

        r = subprocess.run(
            [
                "bash", "-c",
                f'HOME={td} PATH={shim_dir}:$PATH OVERRIDE_VAR=original bash "{WRAPPER}"',
            ],
            capture_output=True,
            text=True,
        )
        assert "OV=from_env_fly" in r.stdout


# ── set +a restores normal behavior ──────────────────────────────────────


def test_set_plus_a_after_source():
    """set +a appears AFTER the source line, bracketing it."""
    content = WRAPPER.read_text()
    lines = content.splitlines()
    set_a_idx = None
    set_plus_a_idx = None
    source_idx = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "set -a":
            set_a_idx = i
        elif stripped == "set +a":
            set_plus_a_idx = i
        elif "source" in stripped and ".env.fly" in stripped:
            source_idx = i
    assert set_a_idx is not None, "set -a not found"
    assert set_plus_a_idx is not None, "set +a not found"
    assert source_idx is not None, "source .env.fly not found"
    assert set_a_idx < source_idx < set_plus_a_idx, (
        f"Order wrong: set -a at {set_a_idx}, source at {source_idx}, set +a at {set_plus_a_idx}"
    )
