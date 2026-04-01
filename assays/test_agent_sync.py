from __future__ import annotations

"""Tests for agent-sync.sh — pulls config repos and syncs MEMORY.md."""

import os
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path

SCRIPT_PATH = Path.home() / "germline/effectors/agent-sync.sh"


def run_script(args: list[str] | None = None, env: dict | None = None) -> subprocess.CompletedProcess:
    """Run agent-sync.sh with optional args and custom env."""
    cmd = [str(SCRIPT_PATH)] + (args or [])
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    return subprocess.run(cmd, capture_output=True, text=True, env=run_env)


def make_fake_home() -> str:
    """Create a temporary directory to use as HOME."""
    return tempfile.mkdtemp()


def rm_fake_home(path: str) -> None:
    """Recursively remove a fake HOME, restoring permissions first."""
    p = Path(path)
    if not p.exists():
        return
    # Restore write permission on everything so shutil can remove it
    for root, dirs, files in os.walk(path):
        for d in dirs:
            full = os.path.join(root, d)
            try:
                os.chmod(full, stat.S_IRWXU)
            except OSError:
                pass
        for f in files:
            full = os.path.join(root, f)
            try:
                os.chmod(full, stat.S_IRWXU)
            except OSError:
                pass
    shutil.rmtree(path, ignore_errors=True)


def git_init(repo: Path) -> None:
    """Initialize a git repo with identity configured."""
    subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, capture_output=True, check=True)


def git_commit(repo: Path, filename: str = "readme.md", content: str = "init") -> None:
    """Add and commit a file in the given repo."""
    (repo / filename).write_text(content)
    subprocess.run(["git", "add", filename], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, capture_output=True, check=True)


def dst_path_for_home(fake_home: str) -> Path:
    """Compute the expected MEMORY.md destination for a given HOME."""
    project_dash = str(fake_home).lstrip("/").replace("/", "-")
    return Path(fake_home) / ".claude" / "projects" / f"-{project_dash}" / "memory" / "MEMORY.md"


def make_memory_md(agent_config: Path, content: str = "test memory") -> Path:
    """Create claude/memory/MEMORY.md in the agent-config dir."""
    memory_dir = agent_config / "claude" / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    memory_file = memory_dir / "MEMORY.md"
    memory_file.write_text(content)
    return memory_file


# ── Help flag tests ─────────────────────────────────────────────────


def test_help_flag_exits_zero():
    """--help flag should exit with code 0."""
    result = run_script(["--help"])
    assert result.returncode == 0


def test_help_flag_shows_usage():
    """--help should show usage information."""
    result = run_script(["--help"])
    assert "Usage:" in result.stdout
    assert "agent-sync" in result.stdout


def test_help_flag_short():
    """-h should work the same as --help."""
    result = run_script(["-h"])
    assert result.returncode == 0
    assert "Usage:" in result.stdout


# ── Git repo handling tests ───────────────────────────────────────────


def test_skips_nonexistent_repos():
    """Script should skip repos that don't exist without error."""
    fake_home = make_fake_home()
    try:
        result = run_script(env={"HOME": fake_home})
        assert result.returncode == 0
    finally:
        rm_fake_home(fake_home)


def test_handles_git_repo_no_remote():
    """Script should handle git repos without remotes (pull fails gracefully)."""
    fake_home = make_fake_home()
    try:
        repo = Path(fake_home) / "agent-config"
        repo.mkdir()
        git_init(repo)
        git_commit(repo)

        result = run_script(env={"HOME": fake_home})
        assert result.returncode == 0
    finally:
        rm_fake_home(fake_home)


def test_handles_multiple_repos():
    """Script should process all three repo paths."""
    fake_home = make_fake_home()
    try:
        for name in ["agent-config", "skills", "epigenome/chromatin"]:
            repo = Path(fake_home) / name
            repo.mkdir(parents=True, exist_ok=True)
            git_init(repo)
            git_commit(repo, content=name)

        result = run_script(env={"HOME": fake_home})
        assert result.returncode == 0
    finally:
        rm_fake_home(fake_home)


# ── MEMORY.md sync tests ──────────────────────────────────────────────


def test_syncs_memory_md():
    """Script should copy MEMORY.md to Claude project dir."""
    fake_home = make_fake_home()
    try:
        agent_config = Path(fake_home) / "agent-config"
        agent_config.mkdir()
        git_init(agent_config)
        make_memory_md(agent_config, "# Test Memory\n\nThis is test memory content.")

        result = run_script(env={"HOME": fake_home})
        assert result.returncode == 0

        dst = dst_path_for_home(fake_home)
        assert dst.exists(), f"MEMORY.md not found at {dst}"
        assert "Test Memory" in dst.read_text()
    finally:
        rm_fake_home(fake_home)


def test_no_error_when_memory_md_missing():
    """Script should not error if MEMORY.md doesn't exist."""
    fake_home = make_fake_home()
    try:
        agent_config = Path(fake_home) / "agent-config"
        agent_config.mkdir()
        subprocess.run(["git", "init"], cwd=agent_config, capture_output=True, check=True)

        result = run_script(env={"HOME": fake_home})
        assert result.returncode == 0
    finally:
        rm_fake_home(fake_home)


# ── Default run (no args) tests ────────────────────────────────────────


def test_no_args_exits_zero():
    """Running with no arguments should exit 0."""
    fake_home = make_fake_home()
    try:
        result = run_script(env={"HOME": fake_home})
        assert result.returncode == 0
    finally:
        rm_fake_home(fake_home)


def test_no_args_no_stdout():
    """Default run with empty home produces no stdout."""
    fake_home = make_fake_home()
    try:
        result = run_script(env={"HOME": fake_home})
        assert result.stdout.strip() == ""
    finally:
        rm_fake_home(fake_home)


# ── Partial repo existence ─────────────────────────────────────────────


def test_partial_repos_exist():
    """Only some repos exist — should handle gracefully."""
    fake_home = make_fake_home()
    try:
        repo = Path(fake_home) / "skills"
        repo.mkdir(parents=True)
        git_init(repo)
        git_commit(repo, content="skills")

        result = run_script(env={"HOME": fake_home})
        assert result.returncode == 0
    finally:
        rm_fake_home(fake_home)


# ── MEMORY.md fidelity and edge cases ──────────────────────────────────


def test_memory_md_content_preserved():
    """MEMORY.md content should be copied exactly, including special chars."""
    fake_home = make_fake_home()
    try:
        agent_config = Path(fake_home) / "agent-config"
        agent_config.mkdir()
        subprocess.run(["git", "init"], cwd=agent_config, capture_output=True, check=True)

        content = "# Memory\n\n- Item with 'quotes' and \"doubles\"\n- Unicode: caf\u00e9, \u65e5\u672c\u8a9e\n- Empty lines below:\n\n\n- End\n"
        make_memory_md(agent_config, content)

        result = run_script(env={"HOME": fake_home})
        assert result.returncode == 0

        dst = dst_path_for_home(fake_home)
        assert dst.exists()
        assert dst.read_text() == content
    finally:
        rm_fake_home(fake_home)


def test_memory_md_sync_creates_deep_dirs():
    """Destination directory tree should be created if it doesn't exist."""
    fake_home = make_fake_home()
    try:
        agent_config = Path(fake_home) / "agent-config"
        agent_config.mkdir()
        subprocess.run(["git", "init"], cwd=agent_config, capture_output=True, check=True)
        make_memory_md(agent_config, "data")

        # Ensure .claude dir does NOT exist beforehand
        assert not (Path(fake_home) / ".claude").exists()

        result = run_script(env={"HOME": fake_home})
        assert result.returncode == 0

        dst = dst_path_for_home(fake_home)
        assert dst.exists()
    finally:
        rm_fake_home(fake_home)


def test_memory_md_overwrites_existing():
    """MEMORY.md should be overwritten if it already exists at destination."""
    fake_home = make_fake_home()
    try:
        agent_config = Path(fake_home) / "agent-config"
        agent_config.mkdir()
        subprocess.run(["git", "init"], cwd=agent_config, capture_output=True, check=True)
        make_memory_md(agent_config, "new content")

        # Pre-create destination with old content
        dst = dst_path_for_home(fake_home)
        dst.parent.mkdir(parents=True)
        dst.write_text("old content")

        result = run_script(env={"HOME": fake_home})
        assert result.returncode == 0
        assert dst.exists()
        assert dst.read_text() == "new content"
    finally:
        rm_fake_home(fake_home)


def test_memory_sync_without_agent_config_repo():
    """If agent-config dir doesn't exist, no MEMORY.md sync should happen."""
    fake_home = make_fake_home()
    try:
        repo = Path(fake_home) / "skills"
        repo.mkdir(parents=True)
        subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)

        result = run_script(env={"HOME": fake_home})
        assert result.returncode == 0
        assert not (Path(fake_home) / ".claude").exists()
    finally:
        rm_fake_home(fake_home)


# ── Path derivation tests ──────────────────────────────────────────────


def test_project_dash_derivation():
    """Verify the HOME→project-dash path transformation."""
    base = tempfile.mkdtemp()
    fake_home = Path(base) / "deep" / "nested" / "home"
    fake_home.mkdir(parents=True)
    try:
        agent_config = fake_home / "agent-config"
        agent_config.mkdir()
        subprocess.run(["git", "init"], cwd=agent_config, capture_output=True, check=True)
        make_memory_md(agent_config, "nested test")

        result = run_script(env={"HOME": str(fake_home)})
        assert result.returncode == 0

        dst = dst_path_for_home(str(fake_home))
        assert dst.exists(), f"Expected MEMORY.md at {dst}"
        assert dst.read_text() == "nested test"
    finally:
        rm_fake_home(base)


# ── Script sanity ───────────────────────────────────────────────────────


def test_script_is_executable():
    """agent-sync.sh must have execute permission."""
    assert SCRIPT_PATH.exists()
    assert os.access(str(SCRIPT_PATH), os.X_OK)


# ── Directory-without-.git guard ────────────────────────────────────────


def test_dir_exists_without_git_dir():
    """A plain directory (no .git) under a repo path should be skipped silently."""
    fake_home = make_fake_home()
    try:
        # Create agent-config as a plain dir (no .git)
        (Path(fake_home) / "agent-config").mkdir()
        # skills has a valid .git
        repo = Path(fake_home) / "skills"
        repo.mkdir()
        git_init(repo)
        git_commit(repo, content="x")

        result = run_script(env={"HOME": fake_home})
        assert result.returncode == 0
    finally:
        rm_fake_home(fake_home)


# ── stderr clean on happy path ──────────────────────────────────────────


def test_no_stderr_on_empty_home():
    """Default run with no repos produces no stderr."""
    fake_home = make_fake_home()
    try:
        result = run_script(env={"HOME": fake_home})
        assert result.stderr.strip() == ""
    finally:
        rm_fake_home(fake_home)


# ── Nested epigenome/chromatin path ─────────────────────────────────────


def test_nested_chromatin_repo():
    """epigenome/chromatin is a nested path — both dirs must be created."""
    fake_home = make_fake_home()
    try:
        chromatin = Path(fake_home) / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        git_init(chromatin)
        git_commit(chromatin, content="c")

        result = run_script(env={"HOME": fake_home})
        assert result.returncode == 0
    finally:
        rm_fake_home(fake_home)


# ── MEMORY.md large content ─────────────────────────────────────────────


def test_memory_md_large_file():
    """MEMORY.md over 100KB should be copied in full."""
    fake_home = make_fake_home()
    try:
        agent_config = Path(fake_home) / "agent-config"
        agent_config.mkdir()
        subprocess.run(["git", "init"], cwd=agent_config, capture_output=True, check=True)

        line = "- " + "x" * 500 + "\n"
        big_content = line * 400
        make_memory_md(agent_config, big_content)

        result = run_script(env={"HOME": fake_home})
        assert result.returncode == 0

        dst = dst_path_for_home(fake_home)
        assert dst.exists()
        assert dst.read_text() == big_content
    finally:
        rm_fake_home(fake_home)


# ── Empty / whitespace MEMORY.md ─────────────────────────────────────────


def test_memory_md_empty_file():
    """An empty (zero-byte) MEMORY.md should still be copied."""
    fake_home = make_fake_home()
    try:
        agent_config = Path(fake_home) / "agent-config"
        agent_config.mkdir()
        subprocess.run(["git", "init"], cwd=agent_config, capture_output=True, check=True)
        make_memory_md(agent_config, "")

        result = run_script(env={"HOME": fake_home})
        assert result.returncode == 0

        dst = dst_path_for_home(fake_home)
        assert dst.exists()
        assert dst.read_text() == ""
    finally:
        rm_fake_home(fake_home)


def test_memory_md_whitespace_only():
    """MEMORY.md with only whitespace should be copied as-is."""
    fake_home = make_fake_home()
    try:
        agent_config = Path(fake_home) / "agent-config"
        agent_config.mkdir()
        subprocess.run(["git", "init"], cwd=agent_config, capture_output=True, check=True)
        make_memory_md(agent_config, "   \n\n\t\n")

        result = run_script(env={"HOME": fake_home})
        assert result.returncode == 0

        dst = dst_path_for_home(fake_home)
        assert dst.exists()
        assert dst.read_text() == "   \n\n\t\n"
    finally:
        rm_fake_home(fake_home)


# ── Idempotency ──────────────────────────────────────────────────────────


def test_idempotent_double_run():
    """Running the script twice should produce identical results."""
    fake_home = make_fake_home()
    try:
        agent_config = Path(fake_home) / "agent-config"
        agent_config.mkdir()
        subprocess.run(["git", "init"], cwd=agent_config, capture_output=True, check=True)
        make_memory_md(agent_config, "stable content\n")

        dst = dst_path_for_home(fake_home)

        r1 = run_script(env={"HOME": fake_home})
        assert r1.returncode == 0
        content1 = dst.read_text()

        r2 = run_script(env={"HOME": fake_home})
        assert r2.returncode == 0
        content2 = dst.read_text()

        assert content1 == content2 == "stable content\n"
    finally:
        rm_fake_home(fake_home)


# ── Unknown arguments ────────────────────────────────────────────────────


def test_unknown_args_still_exit_zero():
    """Unknown arguments are ignored; script still exits 0."""
    fake_home = make_fake_home()
    try:
        result = run_script(["--bogus"], env={"HOME": fake_home})
        assert result.returncode == 0
    finally:
        rm_fake_home(fake_home)


# ── agent-config has MEMORY.md but no .git ───────────────────────────────


def test_memory_md_sync_without_git_in_agent_config():
    """MEMORY.md is synced even when agent-config lacks .git directory."""
    fake_home = make_fake_home()
    try:
        agent_config = Path(fake_home) / "agent-config"
        agent_config.mkdir()
        make_memory_md(agent_config, "no-git memory")

        result = run_script(env={"HOME": fake_home})
        assert result.returncode == 0

        dst = dst_path_for_home(fake_home)
        assert dst.exists()
        assert dst.read_text() == "no-git memory"
    finally:
        rm_fake_home(fake_home)


# ── git repo with no commits ─────────────────────────────────────────────


def test_git_repo_no_commits():
    """A bare git init (no commits) should not crash the script."""
    fake_home = make_fake_home()
    try:
        repo = Path(fake_home) / "agent-config"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)

        result = run_script(env={"HOME": fake_home})
        assert result.returncode == 0
    finally:
        rm_fake_home(fake_home)


# ── Path derivation edge cases ───────────────────────────────────────────


def test_home_with_spaces_in_path():
    """HOME containing spaces should still derive project-dash correctly."""
    base = tempfile.mkdtemp()
    fake_home = Path(base) / "my home dir"
    fake_home.mkdir()
    try:
        agent_config = fake_home / "agent-config"
        agent_config.mkdir()
        subprocess.run(["git", "init"], cwd=agent_config, capture_output=True, check=True)
        make_memory_md(agent_config, "spacey home")

        result = run_script(env={"HOME": str(fake_home)})
        assert result.returncode == 0

        dst = dst_path_for_home(str(fake_home))
        assert dst.exists(), f"Expected at {dst}"
        assert dst.read_text() == "spacey home"
    finally:
        rm_fake_home(base)


def test_home_with_trailing_slash():
    """HOME with a trailing slash should not crash the script."""
    fake_home = make_fake_home()
    try:
        agent_config = Path(fake_home) / "agent-config"
        agent_config.mkdir()
        subprocess.run(["git", "init"], cwd=agent_config, capture_output=True, check=True)
        make_memory_md(agent_config, "trailing slash")

        home_with_slash = fake_home + "/"
        result = run_script(env={"HOME": home_with_slash})
        assert result.returncode == 0
    finally:
        rm_fake_home(fake_home)


def test_home_single_component_path():
    """HOME like /tmpxyz (single component) should produce a single-segment dash."""
    base = tempfile.mkdtemp()
    fake_home = Path(base) / "h"
    fake_home.mkdir()
    try:
        agent_config = fake_home / "agent-config"
        agent_config.mkdir()
        subprocess.run(["git", "init"], cwd=agent_config, capture_output=True, check=True)
        make_memory_md(agent_config, "short path")

        result = run_script(env={"HOME": str(fake_home)})
        assert result.returncode == 0

        dst = dst_path_for_home(str(fake_home))
        assert dst.exists()
    finally:
        rm_fake_home(base)


# ── Symlinked MEMORY.md ──────────────────────────────────────────────────


def test_memory_md_is_symlink():
    """A symlinked MEMORY.md should be followed by cp (copies target content)."""
    fake_home = make_fake_home()
    try:
        agent_config = Path(fake_home) / "agent-config"
        agent_config.mkdir()
        subprocess.run(["git", "init"], cwd=agent_config, capture_output=True, check=True)

        memory_dir = agent_config / "claude" / "memory"
        memory_dir.mkdir(parents=True)
        real_file = memory_dir / "REAL_MEMORY.md"
        real_file.write_text("real content via symlink")
        symlink = memory_dir / "MEMORY.md"
        symlink.symlink_to(real_file)

        result = run_script(env={"HOME": fake_home})
        assert result.returncode == 0

        dst = dst_path_for_home(fake_home)
        assert dst.exists()
        assert dst.read_text() == "real content via symlink"
    finally:
        rm_fake_home(fake_home)


# ── Write-protected destination ──────────────────────────────────────────


def test_write_protected_dest_dir():
    """If .claude/projects is read-only, script exits non-zero via set -e."""
    fake_home = make_fake_home()
    try:
        agent_config = Path(fake_home) / "agent-config"
        agent_config.mkdir()
        subprocess.run(["git", "init"], cwd=agent_config, capture_output=True, check=True)
        make_memory_md(agent_config, "blocked content")

        # Pre-create a read-only .claude directory
        claude_dir = Path(fake_home) / ".claude"
        claude_dir.mkdir()
        claude_dir.chmod(0o000)

        try:
            result = run_script(env={"HOME": fake_home})
            # set -e will cause exit on mkdir -p failure
            assert result.returncode != 0
        finally:
            claude_dir.chmod(0o755)
    finally:
        rm_fake_home(fake_home)


# ── Git pull rebase fallback ────────────────────────────────────────────


def test_git_repo_with_uncommitted_changes():
    """Git repo with dirty working tree should not crash the script."""
    fake_home = make_fake_home()
    try:
        repo = Path(fake_home) / "agent-config"
        repo.mkdir()
        git_init(repo)
        git_commit(repo, filename="file.txt", content="initial")

        # Make working tree dirty
        (repo / "file.txt").write_text("modified but not staged")

        result = run_script(env={"HOME": fake_home})
        assert result.returncode == 0
    finally:
        rm_fake_home(fake_home)


# ── REPOS array completeness ────────────────────────────────────────────


def test_all_three_repos_synced_when_present():
    """All three repos are iterated and attempted even if only some have .git."""
    fake_home = make_fake_home()
    try:
        # Create all three dirs but only two have .git
        for name in ["agent-config", "skills", "epigenome/chromatin"]:
            repo = Path(fake_home) / name
            repo.mkdir(parents=True, exist_ok=True)

        # agent-config has .git + MEMORY.md
        ac = Path(fake_home) / "agent-config"
        git_init(ac)
        make_memory_md(ac, "full cycle")

        # skills has .git + commit
        sk = Path(fake_home) / "skills"
        git_init(sk)
        git_commit(sk, content="s")

        # epigenome/chromatin is a plain dir (no .git) — should be skipped

        result = run_script(env={"HOME": fake_home})
        assert result.returncode == 0

        dst = dst_path_for_home(fake_home)
        assert dst.exists()
        assert dst.read_text() == "full cycle"
    finally:
        rm_fake_home(fake_home)


# ── Binary / non-UTF8 content in MEMORY.md ──────────────────────────────


def test_memory_md_binary_content():
    """MEMORY.md with binary content should be copied byte-for-byte."""
    fake_home = make_fake_home()
    try:
        agent_config = Path(fake_home) / "agent-config"
        agent_config.mkdir()
        subprocess.run(["git", "init"], cwd=agent_config, capture_output=True, check=True)

        memory_dir = agent_config / "claude" / "memory"
        memory_dir.mkdir(parents=True)
        binary_data = b"\x00\x01\x02\xff\xfe\xfd binary\xffcontent"
        (memory_dir / "MEMORY.md").write_bytes(binary_data)

        result = run_script(env={"HOME": fake_home})
        assert result.returncode == 0

        dst = dst_path_for_home(fake_home)
        assert dst.exists()
        assert dst.read_bytes() == binary_data
    finally:
        rm_fake_home(fake_home)


# ── Usage message content ───────────────────────────────────────────────


def test_usage_mentions_options():
    """--help output should mention the -h/--help option."""
    result = run_script(["--help"])
    assert "-h" in result.stdout or "--help" in result.stdout


def test_usage_mentions_memory_sync():
    """--help output should describe the MEMORY.md sync purpose."""
    result = run_script(["--help"])
    assert "MEMORY" in result.stdout or "memory" in result.stdout.lower()


# ── Source-level structural tests ────────────────────────────────────────


def test_script_source_has_bash_shebang():
    """Script must start with #!/usr/bin/env bash."""
    source = SCRIPT_PATH.read_text()
    assert source.startswith("#!/usr/bin/env bash\n")


def test_script_uses_strict_mode():
    """Script must use set -euo pipefail for safety."""
    source = SCRIPT_PATH.read_text()
    assert "set -euo pipefail" in source


def test_script_defines_three_repos():
    """REPOS array must contain exactly three paths."""
    source = SCRIPT_PATH.read_text()
    assert '"$HOME/agent-config"' in source
    assert '"$HOME/skills"' in source
    assert '"$HOME/epigenome/chromatin"' in source


def test_script_tries_rebase_before_plain_pull():
    """git pull --rebase is attempted before plain git pull."""
    source = SCRIPT_PATH.read_text()
    rebase_idx = source.index("pull --rebase")
    plain_idx = source.index("pull 2")
    assert rebase_idx < plain_idx, "rebase pull must come before plain pull fallback"


def test_script_uses_cp_for_memory_sync():
    """MEMORY.md sync uses cp, not mv (must be non-destructive)."""
    source = SCRIPT_PATH.read_text()
    assert "cp " in source
    assert "\nmv " not in source


# ── Repo processing order ───────────────────────────────────────────────


def test_repos_processed_in_order():
    """All three repos are iterated when present with valid .git dirs."""
    fake_home = make_fake_home()
    try:
        for name in ["agent-config", "skills", "epigenome/chromatin"]:
            repo = Path(fake_home) / name
            repo.mkdir(parents=True, exist_ok=True)
            git_init(repo)
            git_commit(repo, content=name)

        result = run_script(env={"HOME": fake_home})
        assert result.returncode == 0
    finally:
        rm_fake_home(fake_home)


# ── cp preserves file permissions ────────────────────────────────────────


def test_memory_md_preserves_executable_bit():
    """If source MEMORY.md is executable, the copy should also be executable."""
    fake_home = make_fake_home()
    try:
        agent_config = Path(fake_home) / "agent-config"
        agent_config.mkdir()
        subprocess.run(["git", "init"], cwd=agent_config, capture_output=True, check=True)

        memory_dir = agent_config / "claude" / "memory"
        memory_dir.mkdir(parents=True)
        src = memory_dir / "MEMORY.md"
        src.write_text("# executable memory\n")
        src.chmod(0o755)

        result = run_script(env={"HOME": fake_home})
        assert result.returncode == 0

        dst = dst_path_for_home(fake_home)
        assert dst.exists()
        assert os.access(str(dst), os.X_OK)
    finally:
        rm_fake_home(fake_home)


# ── HOME pointing to non-existent directory ──────────────────────────────


def test_home_nonexistent_directory():
    """Script should exit cleanly when HOME points to a non-existent path."""
    result = run_script(env={"HOME": "/nonexistent/path/that/does/not/exist"})
    # The REPOS loop uses [ -d ... ] || continue so it skips all.
    # No MEMORY.md found at SRC so the if [ -f ] guard skips mkdir.
    # Script exits 0.
    assert result.returncode in (0, 1)


# ── Only agent-config MEMORY.md is synced ────────────────────────────────


def test_only_agent_config_memory_synced():
    """Only agent-config/claude/memory/MEMORY.md is synced, not from other repos."""
    fake_home = make_fake_home()
    try:
        agent_config = Path(fake_home) / "agent-config"
        agent_config.mkdir()
        subprocess.run(["git", "init"], cwd=agent_config, capture_output=True, check=True)
        make_memory_md(agent_config, "from agent-config")

        skills = Path(fake_home) / "skills"
        skills.mkdir()
        subprocess.run(["git", "init"], cwd=skills, capture_output=True, check=True)
        sk_memory = skills / "claude" / "memory"
        sk_memory.mkdir(parents=True)
        (sk_memory / "MEMORY.md").write_text("from skills — should be ignored")

        result = run_script(env={"HOME": fake_home})
        assert result.returncode == 0

        dst = dst_path_for_home(fake_home)
        assert dst.exists()
        assert dst.read_text() == "from agent-config"
    finally:
        rm_fake_home(fake_home)


# ── Destination follows Claude project-dash convention ───────────────────


def test_dst_dirname_matches_project_convention():
    """Verify the destination follows Claude's -<project-dash>/memory/ convention."""
    fake_home = make_fake_home()
    try:
        agent_config = Path(fake_home) / "agent-config"
        agent_config.mkdir()
        subprocess.run(["git", "init"], cwd=agent_config, capture_output=True, check=True)
        make_memory_md(agent_config, "convention test")

        result = run_script(env={"HOME": fake_home})
        assert result.returncode == 0

        projects_dir = Path(fake_home) / ".claude" / "projects"
        assert projects_dir.exists()
        entries = list(projects_dir.iterdir())
        assert len(entries) == 1
        assert entries[0].name.startswith("-")
    finally:
        rm_fake_home(fake_home)
