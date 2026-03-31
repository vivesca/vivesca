from __future__ import annotations
"""Tests for effectors/queue-balance — task distribution by provider."""

import subprocess
import sys
import textwrap
from pathlib import Path

EFFECTOR = Path(__file__).parent.parent / "effectors" / "queue-balance"


def _run_queue_balance(queue_content: str, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    """Run queue-balance with a temp queue file, return CompletedProcess."""
    queue_file = tmp_path / "golem-queue.md"
    queue_file.write_text(queue_content)
    result = subprocess.run(
        [sys.executable, str(EFFECTOR), str(queue_file)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result


def test_counts_providers():
    """Tasks with --provider X are counted per provider."""
    queue = textwrap.dedent("""\
        # Queue
        ## Pending
        - [ ] `golem --provider zhipu --max-turns 30 "Task A"`
        - [ ] `golem --provider zhipu --max-turns 30 "Task B"`
        - [ ] `golem --provider infini --max-turns 30 "Task C"`
    """)
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        result = _run_queue_balance(queue, Path(td))
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "zhipu" in result.stdout
    assert "infini" in result.stdout
    # zhipu has 2, infini has 1
    assert "2" in result.stdout


def test_detects_imbalance():
    """When one provider has >2x another, rebalancing is suggested."""
    queue = textwrap.dedent("""\
        # Queue
        - [ ] `golem --provider zhipu --max-turns 30 "Task A"`
        - [ ] `golem --provider zhipu --max-turns 30 "Task B"`
        - [ ] `golem --provider zhipu --max-turns 30 "Task C"`
        - [ ] `golem --provider infini --max-turns 30 "Task D"`
    """)
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        result = _run_queue_balance(queue, Path(td))
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "rebalanc" in result.stdout.lower() or "imbalance" in result.stdout.lower()


def test_balanced_no_warning():
    """Balanced distribution produces no rebalancing suggestion."""
    queue = textwrap.dedent("""\
        # Queue
        - [ ] `golem --provider zhipu --max-turns 30 "Task A"`
        - [ ] `golem --provider infini --max-turns 30 "Task B"`
    """)
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        result = _run_queue_balance(queue, Path(td))
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "rebalanc" not in result.stdout.lower()


def test_unassigned_tasks_counted():
    """Task headings without --provider are counted as unassigned."""
    queue = textwrap.dedent("""\
        # Queue
        ### Builds
        #### Build — something
        #### Build — another thing
        - [ ] `golem --provider zhipu --max-turns 30 "Task A"`
    """)
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        result = _run_queue_balance(queue, Path(td))
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "unassigned" in result.stdout.lower()


def test_empty_queue():
    """Empty queue reports zero tasks gracefully."""
    queue = "# Queue\n## Pending\n"
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        result = _run_queue_balance(queue, Path(td))
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "0" in result.stdout


def test_missing_file():
    """Non-existent file exits with error."""
    result = subprocess.run(
        [sys.executable, str(EFFECTOR), "/nonexistent/path/queue.md"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0


def test_no_args():
    """Running without arguments exits with error."""
    result = subprocess.run(
        [sys.executable, str(EFFECTOR)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0


def test_ignores_done_section():
    """Tasks under ## Done are not counted."""
    queue = textwrap.dedent("""\
        # Queue
        ## Pending
        - [ ] `golem --provider zhipu --max-turns 30 "Task A"`
        ## Done
        - [x] `golem --provider zhipu --max-turns 30 "Old task"`
        - [x] `golem --provider infini --max-turns 30 "Old task 2"`
    """)
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        result = _run_queue_balance(queue, Path(td))
    assert result.returncode == 0, f"stderr: {result.stderr}"
    # Only zhipu=1 from Pending, not 2 zhipu + 1 infini
    lines = result.stdout.splitlines()
    # Find the zhipu count line
    zhipu_count = 0
    for line in lines:
        if "zhipu" in line.lower():
            zhipu_count += 1
    # Should see zhipu mentioned exactly once (for the pending task)
    assert zhipu_count == 1
    # Should NOT see infini (it's only in Done)
    assert "infini" not in result.stdout.lower()
