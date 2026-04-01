from __future__ import annotations

"""Tests for effectors/qmd-reindex.sh — bash script tested via subprocess."""

import os
import stat
import subprocess
import tempfile
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "qmd-reindex.sh"


# ── helpers ─────────────────────────────────────────────────────────────


@pytest.fixture()
def tmp_path(tmp_path):
    # Use real tmp_path — no asyncio weirdness needed for this script
    return tmp_path


def _run(
    extra_env: dict | None = None,
    args: list[str] | None = None,
    timeout: int = 10,
) -> subprocess.CompletedProcess:
    """Run qmd-reindex.sh with optional extra env vars and args."""
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    cmd = ["bash", str(SCRIPT)]
    if args:
        cmd.extend(args)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)


def _make_fake_qmd(bin_dir: Path, update_exit: int = 0, embed_exit: int = 0,
                   update_output: str = "", embed_output: str = "") -> Path:
    """Create a fake 'qmd' executable in bin_dir that records calls."""
    qmd = bin_dir / "qmd"
    qmd.write_text(
        "#!/bin/bash\n"
        "case \"$1\" in\n"
        f"  update) echo -n '{update_output}'; exit {update_exit} ;;\n"
        f"  embed) echo -n '{embed_output}'; exit {embed_exit} ;;\n"
        "  *) echo 'unknown subcommand' >&2; exit 1 ;;\n"
        "esac\n"
    )
    qmd.chmod(0o755)
    return qmd


def _make_fake_pgrep(bin_dir: Path, found: bool = False) -> Path:
    """Create a fake 'pgrep' that simulates finding (or not) a running process."""
    pgrep = bin_dir / "pgrep"
    exit_code = 0 if found else 1
    pgrep.write_text(f"#!/bin/bash\nexit {exit_code}\n")
    pgrep.chmod(0o755)
    return pgrep


# ── file basics ─────────────────────────────────────────────────────────


class TestFileBasics:
    def test_file_exists(self):
        assert SCRIPT.exists()

    def test_is_bash_script(self):
        first = SCRIPT.read_text().split("\n")[0]
        assert first.startswith("#!/bin/bash")

    def test_has_set_euo(self):
        src = SCRIPT.read_text()
        assert "set -euo pipefail" in src

    def test_script_is_executable(self):
        assert os.access(SCRIPT, os.X_OK)


# ── help flag ───────────────────────────────────────────────────────────


class TestHelp:
    def test_help_exits_zero(self):
        r = _run(args=["--help"])
        assert r.returncode == 0

    def test_short_flag_exits_zero(self):
        r = _run(args=["-h"])
        assert r.returncode == 0

    def test_help_shows_usage(self):
        r = _run(args=["--help"])
        assert "Usage:" in r.stdout

    def test_help_mentions_qmd(self):
        r = _run(args=["--help"])
        assert "qmd" in r.stdout

    def test_help_mentions_reindex(self):
        r = _run(args=["--help"])
        assert "re-index" in r.stdout.lower() or "reindex" in r.stdout.lower()

    def test_help_no_stderr(self):
        r = _run(args=["--help"])
        assert r.stderr == ""

    def test_help_exits_early(self):
        """--help prints help and exits without running qmd commands."""
        r = _run(args=["--help"])
        # If it ran qmd update/qmd embed, those would fail (no qmd in PATH)
        # and set -e would cause a non-zero exit
        assert r.returncode == 0


# ── PATH setup ──────────────────────────────────────────────────────────


class TestPathSetup:
    def test_adds_bun_bin_to_path(self):
        """Script prepends $HOME/.bun/bin to PATH."""
        src = SCRIPT.read_text()
        assert '.bun/bin' in src

    def test_uses_home_var(self):
        """Script references $HOME for the bun bin path."""
        src = SCRIPT.read_text()
        assert "$HOME" in src


# ── pgrep skip logic ───────────────────────────────────────────────────


class TestSkipIfRunning:
    def test_skips_when_qmd_embed_running(self, tmp_path):
        """If pgrep finds 'qmd embed', script exits 0 without running qmd."""
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        _make_fake_pgrep(bin_dir, found=True)
        # Provide a qmd that would fail if called (to prove it wasn't called)
        qmd = bin_dir / "qmd"
        qmd.write_text("#!/bin/bash\nexit 99\n")
        qmd.chmod(0o755)

        r = _run(
            extra_env={"PATH": f"{bin_dir}:{os.environ.get('PATH', '')}"},
        )
        assert r.returncode == 0
        assert r.stdout == ""

    def test_runs_when_qmd_embed_not_running(self, tmp_path):
        """If pgrep doesn't find 'qmd embed', script proceeds to run qmd."""
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        _make_fake_pgrep(bin_dir, found=False)
        _make_fake_qmd(bin_dir)

        r = _run(
            extra_env={"PATH": f"{bin_dir}:{os.environ.get('PATH', '')}"},
        )
        assert r.returncode == 0

    def test_pgrep_checks_embed_pattern(self):
        """Script uses 'pgrep -f \"qmd embed\"' specifically."""
        src = SCRIPT.read_text()
        assert 'pgrep -f "qmd embed"' in src or "pgrep -f 'qmd embed'" in src


# ── successful run ──────────────────────────────────────────────────────


class TestSuccessfulRun:
    def _setup_and_run(self, tmp_path: Path, **kwargs) -> subprocess.CompletedProcess:
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        _make_fake_pgrep(bin_dir, found=False)
        _make_fake_qmd(bin_dir, **kwargs)
        return _run(
            extra_env={"PATH": f"{bin_dir}:{os.environ.get('PATH', '')}"},
        )

    def test_exits_zero(self, tmp_path):
        r = self._setup_and_run(tmp_path)
        assert r.returncode == 0

    def test_runs_qmd_update_then_embed(self, tmp_path):
        """Both qmd update and qmd embed are invoked."""
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        _make_fake_pgrep(bin_dir, found=False)
        # Create a qmd that logs subcommands to a file
        log = tmp_path / "calls.log"
        qmd = bin_dir / "qmd"
        qmd.write_text(f"#!/bin/bash\necho \"$1\" >> {log}\nexit 0\n")
        qmd.chmod(0o755)

        _run(extra_env={"PATH": f"{bin_dir}:{os.environ.get('PATH', '')}"})
        calls = log.read_text().strip().split("\n")
        assert calls == ["update", "embed"]

    def test_update_stderr_suppressed(self, tmp_path):
        """qmd update stderr is redirected to /dev/null."""
        src = SCRIPT.read_text()
        assert "qmd update 2>/dev/null" in src

    def test_embed_stderr_suppressed(self, tmp_path):
        """qmd embed stderr is redirected to /dev/null."""
        src = SCRIPT.read_text()
        assert "qmd embed 2>/dev/null" in src


# ── qmd command failure ────────────────────────────────────────────────


class TestQmdFailure:
    def test_update_failure_causes_nonzero_exit(self, tmp_path):
        """If qmd update fails (set -e), script exits non-zero."""
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        _make_fake_pgrep(bin_dir, found=False)
        _make_fake_qmd(bin_dir, update_exit=1)
        r = _run(
            extra_env={"PATH": f"{bin_dir}:{os.environ.get('PATH', '')}"},
        )
        assert r.returncode != 0

    def test_embed_failure_causes_nonzero_exit(self, tmp_path):
        """If qmd embed fails (set -e), script exits non-zero."""
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        _make_fake_pgrep(bin_dir, found=False)
        _make_fake_qmd(bin_dir, embed_exit=1)
        r = _run(
            extra_env={"PATH": f"{bin_dir}:{os.environ.get('PATH', '')}"},
        )
        assert r.returncode != 0


# ── qmd not in PATH ────────────────────────────────────────────────────


class TestQmdNotInPath:
    def test_fails_when_qmd_missing(self, tmp_path):
        """Without qmd on PATH, script fails (set -e)."""
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        _make_fake_pgrep(bin_dir, found=False)
        # No qmd created — but keep system PATH so bash itself is found
        r = _run(
            extra_env={"PATH": f"{bin_dir}:{os.environ.get('PATH', '')}"},
        )
        assert r.returncode != 0


# ── script structure ───────────────────────────────────────────────────


class TestScriptStructure:
    def test_help_before_pgrep(self):
        """Help check comes before pgrep (so --help works even if pgrep behaves oddly)."""
        src = SCRIPT.read_text()
        help_pos = src.find("--help")
        pgrep_pos = src.find("pgrep")
        assert help_pos < pgrep_pos, "--help check should precede pgrep check"

    def test_pgrep_before_qmd_commands(self):
        """pgrep check comes before qmd update/embed execution lines."""
        src = SCRIPT.read_text()
        # Use \nqmd to find execution lines, not mentions in help text
        pgrep_pos = src.find("pgrep -f")
        update_pos = src.find("\nqmd update")
        assert pgrep_pos < update_pos

    def test_update_before_embed(self):
        """qmd update runs before qmd embed."""
        src = SCRIPT.read_text()
        update_pos = src.find("qmd update")
        embed_pos = src.find("qmd embed")
        assert update_pos < embed_pos
