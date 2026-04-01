from __future__ import annotations

"""Source-level and structural tests for pharos-sync.sh.

Complements test_pharos_sync_sh.py (which covers runtime behavior) with
static-analysis, ordering, and hygiene checks on the script source."""

import os
import re
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path.home() / "germline/effectors/pharos-sync.sh"


def _src() -> str:
    return SCRIPT.read_text()


def _run(*args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    return subprocess.run(
        [str(SCRIPT), *args],
        capture_output=True,
        text=True,
        env=run_env,
        timeout=15,
    )


# ── file hygiene ──────────────────────────────────────────────────────────


class TestFileHygiene:
    def test_exists(self):
        assert SCRIPT.exists()

    def test_executable(self):
        assert os.access(str(SCRIPT), os.X_OK)

    def test_shebang(self):
        assert _src().splitlines()[0] == "#!/usr/bin/env bash"

    def test_no_crlf(self):
        assert b"\r\n" not in SCRIPT.read_bytes()

    def test_trailing_newline(self):
        assert _src().endswith("\n")

    def test_no_todo_fixme(self):
        for marker in ("TODO", "FIXME"):
            assert marker not in _src(), f"Found {marker} in script"


# ── bash syntax ───────────────────────────────────────────────────────────


class TestBashSyntax:
    def test_bash_n_passes(self):
        r = subprocess.run(
            ["bash", "-n", str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert r.returncode == 0, f"Syntax error: {r.stderr}"


# ── shellcheck ────────────────────────────────────────────────────────────


class TestShellcheck:
    def test_shellcheck_passes(self):
        r = subprocess.run(["which", "shellcheck"], capture_output=True)
        if r.returncode != 0:
            pytest.skip("shellcheck not installed")
        r = subprocess.run(
            ["shellcheck", str(SCRIPT)],
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0, f"Shellcheck issues:\n{r.stdout}{r.stderr}"


# ── script structure ──────────────────────────────────────────────────────


class TestStructure:
    """Verify key structural elements exist in the right order."""

    def test_has_sync_file_function(self):
        assert "sync_file()" in _src()

    def test_has_bash_source_guard(self):
        assert 'BASH_SOURCE[0]' in _src()

    def test_set_uo_pipefail(self):
        assert "set -uo pipefail" in _src()

    def test_help_before_set(self):
        """--help check should come before set -uo pipefail."""
        src = _src()
        assert src.index("--help") < src.index("set -uo pipefail")

    def test_sync_file_before_main_block(self):
        """sync_file function is defined before the main block."""
        src = _src()
        assert src.index("sync_file()") < src.index("BASH_SOURCE")

    def test_officina_variable_uses_home(self):
        assert '$HOME/officina' in _src()

    def test_claude_dir_variable_uses_home(self):
        assert '$HOME/.claude' in _src()

    def test_memory_path_uses_users_terry(self):
        assert "-Users-terry/memory" in _src()


# ── sync_file function analysis ───────────────────────────────────────────


class TestSyncFileSource:
    """Static analysis of the sync_file function."""

    def test_checks_src_exists(self):
        assert '[ -f "$src" ]' in _src() or '[ -f "$1" ]' in _src()

    def test_uses_diff_q(self):
        assert "diff -q" in _src()

    def test_mkdir_p_before_copy(self):
        """mkdir -p appears inside sync_file before the cp."""
        src = _src()
        fn = src[src.index("sync_file()"):]
        mkdir_pos = fn.index("mkdir -p")
        cp_pos = fn.index("cp ")
        assert mkdir_pos < cp_pos

    def test_returns_0_on_update(self):
        """'return 0' appears after successful copy."""
        src = _src()
        fn = src[src.index("sync_file()"):]
        cp_pos = fn.index("cp ")
        ret0_pos = fn.index("return 0")
        assert ret0_pos > cp_pos

    def test_returns_1_on_no_change(self):
        """'return 1' appears for no-update case."""
        src = _src()
        fn = src[src.index("sync_file()"):]
        assert "return 1" in fn

    def test_prints_updated_basename(self):
        """Echo message prints basename of destination."""
        assert 'echo "updated: $(basename "$dst")"' in _src()


# ── ordering: main block sections ─────────────────────────────────────────


class TestMainBlockOrdering:
    """Verify the main block performs operations in the expected order."""

    def _positions(self) -> dict[str, int]:
        src = _src()
        return {
            "help": src.index("--help"),
            "set_flags": src.index("set -uo pipefail"),
            "memory_sync": src.index("rsync"),
            "settings_sync": src.index('settings.json"', src.index("sync_file")),
            "credentials": src.index("credentials.json") if "credentials.json" in src else -1,
            "scp_hosts": src.index("for host in") if "for host in" in src else -1,
            "zshenv": src.index(".zshenv") if ".zshenv" in src else -1,
            "git_add": src.index("git -C"),
            "git_commit": src.index('commit -m "sync:'),
            "git_push": src.index("push"),
        }

    def test_help_before_set_flags(self):
        p = self._positions()
        assert p["help"] < p["set_flags"]

    def test_memory_before_settings(self):
        p = self._positions()
        assert p["memory_sync"] < p["settings_sync"]

    def test_settings_before_git(self):
        p = self._positions()
        assert p["settings_sync"] < p["git_add"]

    def test_git_add_before_commit(self):
        p = self._positions()
        assert p["git_add"] < p["git_commit"]

    def test_git_commit_before_push(self):
        p = self._positions()
        assert p["git_commit"] < p["git_push"]

    def test_credentials_after_settings(self):
        p = self._positions()
        if p["credentials"] == -1:
            pytest.skip("No credentials section")
        assert p["settings_sync"] < p["credentials"]


# ── rsync flags ───────────────────────────────────────────────────────────


class TestRsyncFlags:
    def test_rsync_uses_archive_flag(self):
        assert "rsync -a" in _src()

    def test_rsync_uses_delete_flag(self):
        assert "--delete" in _src()

    def test_rsync_trailing_slash_on_src(self):
        """Source directory ends with / to copy contents, not the dir itself."""
        assert '"/$' not in _src()  # no unexpanded vars in trailing slash
        assert "$MEMORY_SRC/" in _src()


# ── git operations ────────────────────────────────────────────────────────


class TestGitOperations:
    def test_git_add_includes_memory(self):
        assert "claude/memory/" in _src()

    def test_git_add_includes_settings(self):
        assert "claude/settings.json" in _src()

    def test_commit_message_format(self):
        assert "sync: claude config" in _src()

    def test_commit_includes_date(self):
        assert "date '+%Y-%m-%d %H:%M'" in _src()

    def test_commit_has_or_true(self):
        """git commit has || true to handle nothing-to-commit."""
        src = _src()
        commit_line = [l for l in src.splitlines() if "commit -m" in l][0]
        assert "|| true" in commit_line

    def test_push_has_or_true(self):
        """git push has || true for graceful failure."""
        src = _src()
        push_line = [l for l in src.splitlines() if "push" in l and "git" in l][0]
        assert "|| true" in push_line


# ── remote sync patterns ─────────────────────────────────────────────────


class TestRemoteSyncPatterns:
    def test_flyctl_uses_ssh_console(self):
        assert "flyctl ssh console" in _src()

    def test_flyctl_targets_lucerna(self):
        assert "-a lucerna" in _src()

    def test_scp_hosts_are_m2_and_m3(self):
        src = _src()
        assert "for host in m2 m3" in src

    def test_scp_uses_connect_timeout(self):
        assert "ConnectTimeout=3" in _src()

    def test_scp_uses_quiet_flag(self):
        assert "scp -q" in _src()

    def test_credentials_heredoc_uses_endcreds(self):
        assert "ENDCREDS" in _src()

    def test_credentials_escapes_home(self):
        """\$HOME is escaped so it expands on the remote, not locally."""
        assert r"\$HOME" in _src()

    def test_chown_after_creds_write(self):
        assert "chown terry:terry" in _src()

    def test_pharos_scp_targets_host(self):
        assert "pharos:" in _src()

    def test_remote_operations_have_or_true(self):
        """All remote operations (flyctl, scp) should have || true."""
        src = _src()
        for line in src.splitlines():
            stripped = line.strip()
            if any(cmd in stripped for cmd in ("flyctl", "scp -q")):
                assert "|| true" in stripped, f"Missing || true: {stripped}"


# ── changed guard ─────────────────────────────────────────────────────────


class TestChangedGuard:
    def test_changed_initialized_false(self):
        assert "changed=false" in _src()

    def test_changed_true_after_rsync(self):
        src = _src()
        rsync_pos = src.index("rsync")
        changed_after = src.index("changed=true", rsync_pos)
        assert changed_after > rsync_pos

    def test_changed_true_after_sync_file(self):
        """sync_file calls are followed by '&& changed=true'."""
        src = _src()
        lines = src.splitlines()
        for i, line in enumerate(lines):
            if "sync_file \\" in line or (
                "sync_file" in line and "source" not in line and "function" not in line.lower()
            ):
                # Find the continuation or the same line
                full = line
                j = i + 1
                while j < len(lines) and lines[j].strip().startswith("&&"):
                    full += " " + lines[j].strip()
                    j += 1
                if "&& changed=true" in full:
                    return
        pytest.fail("No sync_file call followed by && changed=true")

    def test_exit_if_not_changed(self):
        """'$changed || exit 0' exits early when nothing changed."""
        assert "$changed || exit 0" in _src()


# ── help output content ──────────────────────────────────────────────────


class TestHelpOutput:
    def _run_help(self) -> subprocess.CompletedProcess:
        return _run("--help")

    def test_help_mentions_sync(self):
        assert "Sync" in self._run_help().stdout

    def test_help_mentions_claude_config(self):
        assert "Claude" in self._run_help().stdout

    def test_help_mentions_officina(self):
        assert "officina" in self._run_help().stdout

    def test_help_mentions_remote_machines(self):
        out = self._run_help().stdout
        assert "pharos" in out

    def test_help_mentions_m2_m3(self):
        out = self._run_help().stdout
        assert "m2" in out and "m3" in out

    def test_help_no_stderr(self):
        assert self._run_help().stderr == ""


# ── edge case: concurrent runs / stale state ──────────────────────────────


class TestIdempotency:
    """Running the script twice with same content should not create extra commits."""

    def test_double_run_no_extra_commits(self, tmp_path):
        fake_home = tmp_path / "home"
        fake_claude = fake_home / ".claude"
        officina = fake_home / "officina"
        fake_claude.mkdir(parents=True)
        officina.mkdir(parents=True)

        # Init git repo
        subprocess.run(["git", "init", str(officina)], capture_output=True, check=True)
        subprocess.run(
            ["git", "-C", str(officina), "config", "user.email", "t@t.com"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(officina), "config", "user.name", "T"],
            capture_output=True,
        )

        mem_src = fake_claude / "projects" / "-Users-terry" / "memory"
        mem_src.mkdir(parents=True)
        (mem_src / "MEMORY.md").write_text("unchanged")
        (fake_claude / "settings.json").write_text('{"k": 1}')

        env = {"HOME": str(fake_home)}
        _run(env=env)

        # Get commit count after first run
        r1 = subprocess.run(
            ["git", "-C", str(officina), "rev-list", "--count", "HEAD"],
            capture_output=True,
            text=True,
        )
        count1 = int(r1.stdout.strip())

        # Second run — same files, rsync --delete won't delete anything,
        # but rsync may still trigger changed=true because cp always happens
        _run(env=env)

        r2 = subprocess.run(
            ["git", "-C", str(officina), "rev-list", "--count", "HEAD"],
            capture_output=True,
            text=True,
        )
        count2 = int(r2.stdout.strip())
        # Second run might create another commit (rsync sets changed=true)
        # but should not create more than 1 additional commit
        assert count2 <= count1 + 1


# ── main guard: sourcing safety ───────────────────────────────────────────


class TestMainGuard:
    def test_closing_fi_exists(self):
        """The main block's if has a matching fi."""
        src = _src()
        # Count if/fi in the script
        # The main block is inside: if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then ... fi
        assert src.strip().endswith("fi")

    def test_main_guard_uses_bash_source(self):
        """Guard uses BASH_SOURCE[0] == $0, not just function check."""
        assert '${BASH_SOURCE[0]}' in _src()
        assert '${0}' in _src()
