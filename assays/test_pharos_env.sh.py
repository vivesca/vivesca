from __future__ import annotations

"""Tests for effectors/pharos-env.sh — subprocess-based tests."""

import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "pharos-env.sh"


# ── helpers ─────────────────────────────────────────────────────────────


def _run(
    *args: str, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess:
    if env is None:
        env = os.environ.copy()
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )


def _make_patched_script(tmp_path: Path) -> Path:
    """Return a copy of the script with HOME rewritten so zshenv lookup uses tmp_path."""
    src = SCRIPT.read_text()
    patched = src.replace(
        'export HOME="${HOME:-$(eval echo ~)}"',
        f'export HOME="{tmp_path}"',
    )
    out = tmp_path / "pharos-env-test.sh"
    out.write_text(patched)
    out.chmod(0o755)
    return out


def _run_patched(tmp_path: Path, *args: str) -> subprocess.CompletedProcess:
    script = _make_patched_script(tmp_path)
    return subprocess.run(
        ["bash", str(script), *args],
        capture_output=True,
        text=True,
        env=os.environ.copy(),
        timeout=10,
    )


# ── help / usage ───────────────────────────────────────────────────────


class TestHelp:
    def test_long_help_exits_zero(self):
        assert _run("--help").returncode == 0

    def test_short_help_exits_zero(self):
        assert _run("-h").returncode == 0

    def test_help_shows_usage(self):
        assert "Usage:" in _run("--help").stdout

    def test_help_mentions_systemd(self):
        assert "systemd" in _run("--help").stdout

    def test_help_no_stderr(self):
        assert _run("--help").stderr == ""


# ── file basics ────────────────────────────────────────────────────────


class TestFileBasics:
    def test_file_exists(self):
        assert SCRIPT.is_file()

    def test_shebang_is_bash(self):
        assert SCRIPT.read_text().splitlines()[0] == "#!/bin/bash"

    def test_strict_mode(self):
        assert "set -euo pipefail" in SCRIPT.read_text()

    def test_is_executable(self):
        assert os.access(SCRIPT, os.X_OK)


# ── HOME handling ──────────────────────────────────────────────────────


class TestHome:
    def test_default_home(self):
        """With inherited HOME the script keeps it."""
        r = _run("printenv", "HOME")
        assert r.returncode == 0
        assert r.stdout.strip() == os.environ["HOME"]

    def test_home_fallback_when_unset(self):
        """When HOME is unset the script computes it via eval echo ~."""
        env = os.environ.copy()
        env.pop("HOME", None)
        r = _run("printenv", "HOME", env=env)
        assert r.returncode == 0
        # Should resolve to the real home directory
        assert r.stdout.strip() == str(Path.home())

    def test_home_fallback_when_empty(self):
        """Empty-string HOME: ~ expands to $HOME (still empty), so result is empty."""
        env = os.environ.copy()
        env["HOME"] = ""
        r = _run("printenv", "HOME", env=env)
        assert r.returncode == 0
        # ${HOME:-$(eval echo ~)} triggers the fallback (empty triggers :-),
        # but ~ itself resolves to $HOME which is still empty — circular.
        assert r.stdout.strip() == ""


# ── PATH construction ──────────────────────────────────────────────────


class TestPath:
    _EXPECTED_ENTRIES = [
        ".local/bin",
        ".cargo/bin",
        ".bun/bin",
        "go/bin",
        ".nix-profile/bin",
        "/nix/var/nix/profiles/default/bin",
        "/usr/local/bin",
        "/usr/bin",
        "/bin",
    ]

    def test_path_contains_all_entries(self):
        path = _run("printenv", "PATH").stdout.strip()
        for entry in self._EXPECTED_ENTRIES:
            assert entry in path, f"{entry} missing from PATH"

    def test_path_starts_with_local_bin(self):
        path = _run("printenv", "PATH").stdout.strip()
        assert path.startswith(str(Path.home() / ".local/bin"))

    def test_path_exactly_nine_entries(self):
        path = _run("printenv", "PATH").stdout.strip()
        assert len(path.split(":")) == 9

    def test_path_no_duplicates(self):
        entries = _run("printenv", "PATH").stdout.strip().split(":")
        assert len(entries) == len(set(entries))

    def test_user_dirs_before_system_dirs(self):
        path = _run("printenv", "PATH").stdout.strip()
        local = path.index(str(Path.home() / ".local/bin"))
        usr = path.index("/usr/bin")
        assert local < usr


# ── exec forwarding ────────────────────────────────────────────────────


class TestExec:
    def test_echo_command(self):
        r = _run("echo", "hello")
        assert r.returncode == 0
        assert r.stdout.strip() == "hello"

    def test_multiple_args(self):
        r = _run("printf", "%s|%s|%s", "a", "b", "c")
        assert r.returncode == 0
        assert r.stdout == "a|b|c"

    def test_args_with_spaces(self):
        r = _run("echo", "hello world", "foo bar")
        assert r.returncode == 0
        assert r.stdout.strip() == "hello world foo bar"

    def test_args_with_special_chars(self):
        r = _run("printf", "%s", "a*b?c")
        assert r.returncode == 0
        assert r.stdout == "a*b?c"

    def test_nonzero_exit_propagated(self):
        assert _run("false").returncode != 0

    def test_specific_exit_code_propagated(self):
        assert _run("bash", "-c", "exit 42").returncode == 42

    def test_command_not_found_fails(self):
        assert _run("this-does-not-exist-xyz").returncode != 0

    def test_stderr_passes_through(self):
        r = _run("bash", "-c", "echo err >&2")
        assert "err" in r.stderr

    def test_no_args(self):
        """exec "$@" with no args is effectively a no-op; exits 0."""
        assert _run().returncode == 0


# ── zshenv.local sourcing ──────────────────────────────────────────────


class TestZshenv:
    def test_source_block_present(self):
        src = SCRIPT.read_text()
        assert 'if [ -f "$HOME/.zshenv.local" ]; then' in src
        assert "set -a" in src
        assert 'source "$HOME/.zshenv.local"' in src
        assert "set +a" in src

    def test_sources_exports(self, tmp_path):
        (tmp_path / ".zshenv.local").write_text('PHAROS_TEST_SECRET="open sesame"\n')
        r = _run_patched(tmp_path, "printenv", "PHAROS_TEST_SECRET")
        assert r.returncode == 0
        assert r.stdout.strip() == "open sesame"

    def test_missing_zshenv_ok(self, tmp_path):
        assert not (tmp_path / ".zshenv.local").exists()
        assert _run_patched(tmp_path, "true").returncode == 0

    def test_auto_export_without_export_keyword(self, tmp_path):
        (tmp_path / ".zshenv.local").write_text('PHAROS_IMPLICIT="auto"\n')
        r = _run_patched(tmp_path, "printenv", "PHAROS_IMPLICIT")
        assert r.stdout.strip() == "auto"

    def test_syntax_error_causes_failure(self, tmp_path):
        (tmp_path / ".zshenv.local").write_text("this-is-not-valid-bash!!!\n")
        assert _run_patched(tmp_path, "true").returncode != 0

    def test_empty_zshenv_ok(self, tmp_path):
        (tmp_path / ".zshenv.local").write_text("")
        assert _run_patched(tmp_path, "true").returncode == 0

    def test_comment_lines_ignored(self, tmp_path):
        (tmp_path / ".zshenv.local").write_text(
            "# comment\n\nPHAROS_CMT=yes\n# another\n"
        )
        r = _run_patched(tmp_path, "printenv", "PHAROS_CMT")
        assert r.stdout.strip() == "yes"

    def test_multiple_vars(self, tmp_path):
        (tmp_path / ".zshenv.local").write_text(
            'A="1"\nB="2"\nC="3"\n'
        )
        assert _run_patched(tmp_path, "printenv", "A").stdout.strip() == "1"
        assert _run_patched(tmp_path, "printenv", "B").stdout.strip() == "2"
        assert _run_patched(tmp_path, "printenv", "C").stdout.strip() == "3"

    def test_override_caller_env(self, tmp_path):
        (tmp_path / ".zshenv.local").write_text('PHAROS_OVR="new"\n')
        script = _make_patched_script(tmp_path)
        env = os.environ.copy()
        env["PHAROS_OVR"] = "old"
        r = subprocess.run(
            ["bash", str(script), "printenv", "PHAROS_OVR"],
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
        )
        assert r.stdout.strip() == "new"


# ── idempotency ────────────────────────────────────────────────────────


class TestIdempotency:
    def test_same_path_on_two_runs(self):
        r1 = _run("printenv", "PATH")
        r2 = _run("printenv", "PATH")
        assert r1.stdout == r2.stdout

    def test_same_home_on_two_runs(self):
        r1 = _run("printenv", "HOME")
        r2 = _run("printenv", "HOME")
        assert r1.stdout == r2.stdout
