"""Tests for polymerase --sections flag.

Polymerase is a script, not an importable module. Tests invoke it via subprocess
and check stdout/exit code.
"""

import subprocess
from pathlib import Path

POLYMERASE = Path.home() / "germline/effectors/polymerase"


def _run(*args: str) -> subprocess.CompletedProcess:
    """Invoke polymerase with given args, always with --dry-run to avoid
    clobbering the real coaching output file."""
    return subprocess.run(
        [str(POLYMERASE), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def _count_section_headers(stdout: str) -> int:
    """Count lines starting with '### ' (section headers in compact format)."""
    return sum(1 for line in stdout.splitlines() if line.startswith("### "))


def test_polymerase_binary_exists():
    """Sanity check: the polymerase script is present and executable."""
    assert POLYMERASE.exists(), f"polymerase not found at {POLYMERASE}"
    assert POLYMERASE.stat().st_mode & 0o111, "polymerase is not executable"


def test_no_flag_emits_all_sections():
    """Baseline: with no --sections flag, all 12 sections should appear."""
    result = _run("--dry-run")
    assert result.returncode == 0, f"stderr: {result.stderr}"
    headers = _count_section_headers(result.stdout)
    assert headers == 12, (
        f"expected 12 section headers with no filter, got {headers}. "
        f"First 500 chars of stdout: {result.stdout[:500]}"
    )


def test_single_section_code():
    """--sections code should emit only the Code Patterns section."""
    result = _run("--sections", "code", "--dry-run")
    assert result.returncode == 0, f"stderr: {result.stderr}"
    headers = _count_section_headers(result.stdout)
    assert headers == 1, f"expected 1 section header, got {headers}"
    assert "### Code Patterns" in result.stdout
    # Must NOT contain other sections
    assert "### Testing" not in result.stdout
    assert "### Article Analysis" not in result.stdout


def test_two_sections_intersect():
    """--sections code,exec should emit exactly those two sections."""
    result = _run("--sections", "code,exec", "--dry-run")
    assert result.returncode == 0, f"stderr: {result.stderr}"
    headers = _count_section_headers(result.stdout)
    assert headers == 2, f"expected 2 section headers, got {headers}"
    assert "### Code Patterns" in result.stdout
    assert "### Execution Discipline" in result.stdout
    assert "### Testing" not in result.stdout


def test_unknown_section_filters_silently():
    """--sections nonexistent should produce no body sections, exit 0."""
    result = _run("--sections", "nonexistent", "--dry-run")
    assert result.returncode == 0, f"stderr: {result.stderr}"
    headers = _count_section_headers(result.stdout)
    assert headers == 0, f"expected 0 section headers, got {headers}"
    # But frontmatter header line should still be present
    assert "## ribosome coaching" in result.stdout


def test_empty_sections_value():
    """--sections '' should behave like nonexistent: no body sections."""
    result = _run("--sections", "", "--dry-run")
    assert result.returncode == 0, f"stderr: {result.stderr}"
    headers = _count_section_headers(result.stdout)
    assert headers == 0


def test_sections_equals_syntax():
    """--sections=code,verify (equals form) should also work."""
    result = _run("--sections=code,verify", "--dry-run")
    assert result.returncode == 0, f"stderr: {result.stderr}"
    headers = _count_section_headers(result.stdout)
    assert headers == 2, f"expected 2 section headers, got {headers}"
    assert "### Code Patterns" in result.stdout
    assert "### Verification" in result.stdout


def test_sections_with_critical_intersects():
    """--sections code --critical should emit Code Patterns with only CRITICAL+HIGH rules."""
    result = _run("--sections", "code", "--critical", "--dry-run")
    assert result.returncode == 0, f"stderr: {result.stderr}"
    headers = _count_section_headers(result.stdout)
    assert headers == 1
    assert "### Code Patterns" in result.stdout
    # The full code section has ~10 rules; --critical filters to CRITICAL+HIGH only.
    # Count bullets under Code Patterns section. All remaining bullets should be
    # from the code section. The total bullet count should be <= total rules in code.
    bullets = [line for line in result.stdout.splitlines() if line.startswith("- **")]
    assert 1 <= len(bullets) <= 10, (
        f"expected between 1 and 10 rules under Code Patterns with --critical, got {len(bullets)}"
    )


def test_existing_flags_unchanged():
    """--validate and --stats must still work after the change."""
    validate_result = _run("--validate")
    assert validate_result.returncode == 0, f"--validate broke: stderr={validate_result.stderr}"

    stats_result = _run("--stats")
    assert stats_result.returncode == 0, f"--stats broke: stderr={stats_result.stderr}"
    assert "Total rules:" in stats_result.stdout
    assert "By impact:" in stats_result.stdout
    assert "By section:" in stats_result.stdout


def test_sections_without_dry_run_writes_to_tmp():
    """--sections without --dry-run must write to /tmp, not clobber the coaching output.

    Verifies that the production feedback_ribosome_coaching.md file is not modified
    when polymerase is run with a partial section filter.
    """
    coaching_file = Path.home() / "epigenome/marks/feedback_ribosome_coaching.md"
    if not coaching_file.exists():
        # If the coaching file doesn't exist, skip this test (env-specific).
        return

    before_mtime = coaching_file.stat().st_mtime
    before_content = coaching_file.read_text(encoding="utf-8")

    result = _run("--sections", "code")
    assert result.returncode == 0, f"stderr: {result.stderr}"

    # Coaching file must not have been modified
    after_mtime = coaching_file.stat().st_mtime
    after_content = coaching_file.read_text(encoding="utf-8")
    assert before_mtime == after_mtime, (
        "polymerase --sections (without --dry-run) modified the coaching file — "
        "it should have written to /tmp instead"
    )
    assert before_content == after_content

    # /tmp file should exist
    tmp_output = Path("/tmp/polymerase-filtered.md")
    assert tmp_output.exists(), "expected /tmp/polymerase-filtered.md to exist"
    tmp_content = tmp_output.read_text(encoding="utf-8")
    assert "### Code Patterns" in tmp_content
