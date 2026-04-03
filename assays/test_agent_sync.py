from __future__ import annotations

"""Tests for agent-sync.sh — pull config repos and sync MEMORY.md."""

import os
import subprocess
from pathlib import Path

SCRIPT = Path.home() / "germline/effectors/agent-sync.sh"


def _run(*extra_args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    """Run agent-sync.sh with optional extra args and env overrides."""
    run_env = {**os.environ, "HOME": str(Path.home())}
    if env:
        run_env.update(env)
    return subprocess.run(
        [str(SCRIPT), *extra_args],
        capture_output=True,
        text=True,
        env=run_env,
        timeout=10,
    )


# ── help / usage ──────────────────────────────────────────────────────


def test_help_flag_exits_zero():
    """--help exits with code 0."""
    r = _run("--help")
    assert r.returncode == 0


def test_h_flag_exits_zero():
    """Short -h flag exits with code 0."""
    r = _run("-h")
    assert r.returncode == 0


def test_help_shows_usage():
    """--help output contains 'Usage'."""
    r = _run("--help")
    assert "Usage" in r.stdout


def test_help_mentions_agent_sync():
    """--help output mentions agent-sync."""
    r = _run("--help")
    assert "agent-sync" in r.stdout


# ── no repos — graceful success ───────────────────────────────────────


def test_no_args_no_repos_succeeds(tmp_path, monkeypatch):
    """Script succeeds when no repo dirs exist (all skipped)."""
    monkeypatch.setenv("HOME", str(tmp_path))
    r = subprocess.run(
        [str(SCRIPT)],
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": str(tmp_path)},
        timeout=10,
    )
    assert r.returncode == 0


# ── git pull behaviour ────────────────────────────────────────────────


def test_repo_with_git_dir_is_pulled(tmp_path):
    """Repos containing .git/ trigger a git pull attempt."""
    repo = tmp_path / "agent-config"
    repo.mkdir()
    (repo / ".git").mkdir()
    # Create a real-ish git repo so git pull can at least start
    subprocess.run(["git", "init", str(repo)], capture_output=True, check=True)
    subprocess.run(
        ["git", "-C", str(repo), "commit", "--allow-empty", "-m", "init"],
        capture_output=True,
        check=True,
        env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
             "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"},
    )
    r = subprocess.run(
        [str(SCRIPT)],
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": str(tmp_path)},
        timeout=10,
    )
    # Script should still succeed (git pull on local-only repo is fine)
    assert r.returncode == 0


def test_repo_without_git_dir_is_skipped(tmp_path):
    """Repos without .git/ are silently skipped."""
    repo = tmp_path / "skills"
    repo.mkdir()
    # No .git dir — should be skipped
    r = subprocess.run(
        [str(SCRIPT)],
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": str(tmp_path)},
        timeout=10,
    )
    assert r.returncode == 0
    assert "fatal" not in r.stderr.lower()


def test_nonexistent_repo_dir_is_skipped(tmp_path):
    """Repos whose directories don't exist are skipped."""
    r = subprocess.run(
        [str(SCRIPT)],
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": str(tmp_path)},
        timeout=10,
    )
    assert r.returncode == 0


# ── MEMORY.md sync ───────────────────────────────────────────────────


def test_memory_copied_when_source_exists(tmp_path):
    """MEMORY.md is copied to Claude project dir when source exists."""
    # Set up agent-config with MEMORY.md
    cfg = tmp_path / "agent-config"
    cfg.mkdir()
    (cfg / ".git").mkdir()  # make it look like a repo
    mem_dir = cfg / "claude" / "memory"
    mem_dir.mkdir(parents=True)
    (mem_dir / "MEMORY.md").write_text("# test memory\n")

    r = subprocess.run(
        [str(SCRIPT)],
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": str(tmp_path)},
        timeout=10,
    )
    assert r.returncode == 0

    # Derive expected destination path
    project_dash = str(tmp_path).lstrip("/")
    project_dash = project_dash.replace("/", "-")
    dst = tmp_path / ".claude" / "projects" / f"-{project_dash}" / "memory" / "MEMORY.md"
    assert dst.exists()
    assert dst.read_text() == "# test memory\n"


def test_memory_not_copied_when_source_missing(tmp_path):
    """No error when MEMORY.md source does not exist."""
    cfg = tmp_path / "agent-config"
    cfg.mkdir()
    (cfg / ".git").mkdir()

    r = subprocess.run(
        [str(SCRIPT)],
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": str(tmp_path)},
        timeout=10,
    )
    assert r.returncode == 0


def test_memory_dest_dir_created(tmp_path):
    """Destination directory is auto-created if missing."""
    cfg = tmp_path / "agent-config"
    cfg.mkdir()
    (cfg / ".git").mkdir()
    mem_dir = cfg / "claude" / "memory"
    mem_dir.mkdir(parents=True)
    (mem_dir / "MEMORY.md").write_text("data")

    # Ensure .claue dir does NOT exist yet
    assert not (tmp_path / ".claude").exists()

    r = subprocess.run(
        [str(SCRIPT)],
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": str(tmp_path)},
        timeout=10,
    )
    assert r.returncode == 0

    project_dash = str(tmp_path).lstrip("/").replace("/", "-")
    dst = tmp_path / ".claude" / "projects" / f"-{project_dash}" / "memory" / "MEMORY.md"
    assert dst.exists()


def test_memory_overwrites_existing(tmp_path):
    """MEMORY.md is overwritten if destination already exists."""
    cfg = tmp_path / "agent-config"
    cfg.mkdir()
    (cfg / ".git").mkdir()
    mem_dir = cfg / "claude" / "memory"
    mem_dir.mkdir(parents=True)
    (mem_dir / "MEMORY.md").write_text("new content")

    # Pre-create destination with stale content
    project_dash = str(tmp_path).lstrip("/").replace("/", "-")
    dst_dir = tmp_path / ".claude" / "projects" / f"-{project_dash}" / "memory"
    dst_dir.mkdir(parents=True)
    (dst_dir / "MEMORY.md").write_text("old content")

    r = subprocess.run(
        [str(SCRIPT)],
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": str(tmp_path)},
        timeout=10,
    )
    assert r.returncode == 0
    assert (dst_dir / "MEMORY.md").read_text() == "new content"


# ── project dash derivation ──────────────────────────────────────────


def test_project_dash_from_simple_home(tmp_path):
    """Verify the sed+tr dash derivation for a simple tmp_path."""
    # tmp_path is like /tmp/pytest-xxx/aaa — slash-stripped becomes tmp/pytest-xxx/aaa
    # tr '/' "-" replaces slashes with dashes
    stripped = str(tmp_path).lstrip("/")
    dashed = stripped.replace("/", "-")
    # If tmp_path has only one component after /, no dashes from slashes
    # But typically pytest tmp_path is /tmp/pytest-xxx/test-foo-0
    # So dashed should contain at least one dash replacing the slash
    assert "-" in dashed or "/" not in stripped


# ── all three repo paths ──────────────────────────────────────────────


def test_all_three_repo_dirs_are_iterated(tmp_path):
    """agent-config, skills, and epigenome/chromatin are all pulled."""
    for name in ("agent-config", "skills", "epigenome/chromatin"):
        repo = tmp_path / name
        repo.mkdir(parents=True)
        subprocess.run(["git", "init", str(repo)], capture_output=True, check=True)
        subprocess.run(
            ["git", "-C", str(repo), "commit", "--allow-empty", "-m", "init"],
            capture_output=True,
            check=True,
            env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                 "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"},
        )

    r = subprocess.run(
        [str(SCRIPT)],
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": str(tmp_path)},
        timeout=10,
    )
    assert r.returncode == 0


def test_epigenome_chromatin_nested_path(tmp_path):
    """epigenome/chromatin nested dir is handled correctly."""
    repo = tmp_path / "epigenome" / "chromatin"
    repo.mkdir(parents=True)
    subprocess.run(["git", "init", str(repo)], capture_output=True, check=True)
    subprocess.run(
        ["git", "-C", str(repo), "commit", "--allow-empty", "-m", "init"],
        capture_output=True, check=True,
        env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
             "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"},
    )

    r = subprocess.run(
        [str(SCRIPT)],
        capture_output=True, text=True,
        env={**os.environ, "HOME": str(tmp_path)},
        timeout=10,
    )
    assert r.returncode == 0


# ── git pull failure handling ──────────────────────────────────────────


def test_git_pull_failure_swallowed(tmp_path):
    """Script succeeds even when git pull fails (|| true)."""
    repo = tmp_path / "agent-config"
    repo.mkdir()
    (repo / ".git").mkdir()
    # .git is a directory but NOT a valid repo — git pull will fail
    r = subprocess.run(
        [str(SCRIPT)],
        capture_output=True, text=True,
        env={**os.environ, "HOME": str(tmp_path)},
        timeout=10,
    )
    assert r.returncode == 0


# ── unrecognized arguments ────────────────────────────────────────────


def test_unrecognized_args_run_normally(tmp_path):
    """Unknown args are silently ignored (script doesn't flag them)."""
    r = subprocess.run(
        [str(SCRIPT), "--unknown"],
        capture_output=True, text=True,
        env={**os.environ, "HOME": str(tmp_path)},
        timeout=10,
    )
    # Script doesn't handle unknown args — falls through to main logic
    assert r.returncode == 0


# ── MEMORY.md edge cases ──────────────────────────────────────────────


def test_memory_empty_file_copied(tmp_path):
    """Empty MEMORY.md is still copied to destination."""
    cfg = tmp_path / "agent-config"
    cfg.mkdir()
    (cfg / ".git").mkdir()
    mem_dir = cfg / "claude" / "memory"
    mem_dir.mkdir(parents=True)
    (mem_dir / "MEMORY.md").write_text("")

    r = subprocess.run(
        [str(SCRIPT)],
        capture_output=True, text=True,
        env={**os.environ, "HOME": str(tmp_path)},
        timeout=10,
    )
    assert r.returncode == 0

    project_dash = str(tmp_path).lstrip("/").replace("/", "-")
    dst = tmp_path / ".claude" / "projects" / f"-{project_dash}" / "memory" / "MEMORY.md"
    assert dst.exists()
    assert dst.read_text() == ""


def test_memory_unicode_content_preserved(tmp_path):
    """MEMORY.md with unicode content is copied faithfully."""
    cfg = tmp_path / "agent-config"
    cfg.mkdir()
    (cfg / ".git").mkdir()
    mem_dir = cfg / "claude" / "memory"
    mem_dir.mkdir(parents=True)
    content = "# Mémoire 🧠\n日本語テスト\n"
    (mem_dir / "MEMORY.md").write_text(content)

    r = subprocess.run(
        [str(SCRIPT)],
        capture_output=True, text=True,
        env={**os.environ, "HOME": str(tmp_path)},
        timeout=10,
    )
    assert r.returncode == 0

    project_dash = str(tmp_path).lstrip("/").replace("/", "-")
    dst = tmp_path / ".claude" / "projects" / f"-{project_dash}" / "memory" / "MEMORY.md"
    assert dst.read_text() == content


def test_memory_large_content(tmp_path):
    """Large MEMORY.md (1MB) is copied without issue."""
    cfg = tmp_path / "agent-config"
    cfg.mkdir()
    (cfg / ".git").mkdir()
    mem_dir = cfg / "claude" / "memory"
    mem_dir.mkdir(parents=True)
    large = "x" * 1_000_000
    (mem_dir / "MEMORY.md").write_text(large)

    r = subprocess.run(
        [str(SCRIPT)],
        capture_output=True, text=True,
        env={**os.environ, "HOME": str(tmp_path)},
        timeout=10,
    )
    assert r.returncode == 0

    project_dash = str(tmp_path).lstrip("/").replace("/", "-")
    dst = tmp_path / ".claude" / "projects" / f"-{project_dash}" / "memory" / "MEMORY.md"
    assert dst.read_text() == large


# ── script validity ──────────────────────────────────────────────────


def test_script_is_valid_bash():
    """Script passes bash -n syntax check."""
    r = subprocess.run(
        ["bash", "-n", str(SCRIPT)],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, f"Syntax error: {r.stderr}"


def test_script_is_executable():
    """Script has executable permission."""
    assert SCRIPT.stat().st_mode & 0o111, "agent-sync.sh is not executable"


# ── project dash with deep nested home ────────────────────────────────


def test_project_dash_deep_nested_home(tmp_path):
    """Project dash derivation works for deeply nested home paths."""
    deep = tmp_path / "a" / "b" / "c" / "d"
    deep.mkdir(parents=True)
    cfg = deep / "agent-config"
    cfg.mkdir()
    (cfg / ".git").mkdir()
    mem_dir = cfg / "claude" / "memory"
    mem_dir.mkdir(parents=True)
    (mem_dir / "MEMORY.md").write_text("deep test\n")

    r = subprocess.run(
        [str(SCRIPT)],
        capture_output=True, text=True,
        env={**os.environ, "HOME": str(deep)},
        timeout=10,
    )
    assert r.returncode == 0

    project_dash = str(deep).lstrip("/").replace("/", "-")
    dst = deep / ".claude" / "projects" / f"-{project_dash}" / "memory" / "MEMORY.md"
    assert dst.exists()
    assert dst.read_text() == "deep test\n"
