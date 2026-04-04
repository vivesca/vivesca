"""Tests for effectors/queue-balance — task distribution by provider."""

import subprocess
import sys
import textwrap
from pathlib import Path

EFFECTOR = Path(__file__).parent.parent / "effectors" / "queue-balance"


def _run_queue_balance(queue_content: str, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    """Run queue-balance with a temp queue file, return CompletedProcess."""
    queue_file = tmp_path / "translation-queue.md"
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
        - [ ] `ribosome --provider zhipu --max-turns 30 "Task A"`
        - [ ] `ribosome --provider zhipu --max-turns 30 "Task B"`
        - [ ] `ribosome --provider infini --max-turns 30 "Task C"`
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
        - [ ] `ribosome --provider zhipu --max-turns 30 "Task A"`
        - [ ] `ribosome --provider zhipu --max-turns 30 "Task B"`
        - [ ] `ribosome --provider zhipu --max-turns 30 "Task C"`
        - [ ] `ribosome --provider infini --max-turns 30 "Task D"`
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
        - [ ] `ribosome --provider zhipu --max-turns 30 "Task A"`
        - [ ] `ribosome --provider infini --max-turns 30 "Task B"`
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
        - [ ] `ribosome --provider zhipu --max-turns 30 "Task A"`
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
    assert "No tasks found" in result.stdout


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
        - [ ] `ribosome --provider zhipu --max-turns 30 "Task A"`
        ## Done
        - [x] `ribosome --provider zhipu --max-turns 30 "Old task"`
        - [x] `ribosome --provider infini --max-turns 30 "Old task 2"`
    """)
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        result = _run_queue_balance(queue, Path(td))
    assert result.returncode == 0, f"stderr: {result.stderr}"
    # Only zhipu=1 from Pending, not 2 zhipu + 1 infini from Done
    # Check the table row shows zhipu with count 1
    table_lines = [ln for ln in result.stdout.splitlines() if ln.strip().startswith("zhipu")]
    assert len(table_lines) >= 1, f"no zhipu table row found in:\n{result.stdout}"
    # The first table row should show exactly 1 task
    first_row = table_lines[0]
    assert "1" in first_row.split()[1], f"expected 1 task for zhipu, got: {first_row}"
    # Should NOT see infini (it's only in Done)
    assert "infini" not in result.stdout.lower()


def test_shows_concurrency_column():
    """Report includes concurrency info per provider."""
    queue = textwrap.dedent("""\
        # Queue
        - [ ] `ribosome --provider zhipu --max-turns 30 "Task A"`
        - [ ] `ribosome --provider volcano --max-turns 30 "Task B"`
    """)
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        result = _run_queue_balance(queue, Path(td))
    assert result.returncode == 0, f"stderr: {result.stderr}"
    # Table should have Conc column header
    assert "Conc" in result.stdout
    # zhipu concurrency is 4
    assert "4" in result.stdout


def test_throughput_drain_time():
    """Report shows drain time estimates (rounds)."""
    queue = textwrap.dedent("""\
        # Queue
        - [ ] `ribosome --provider zhipu --max-turns 30 "Task A"`
        - [ ] `ribosome --provider zhipu --max-turns 30 "Task B"`
        - [ ] `ribosome --provider zhipu --max-turns 30 "Task C"`
        - [ ] `ribosome --provider zhipu --max-turns 30 "Task D"`
        - [ ] `ribosome --provider zhipu --max-turns 30 "Task E"`
        - [ ] `ribosome --provider volcano --max-turns 30 "Task F"`
    """)
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        result = _run_queue_balance(queue, Path(td))
    assert result.returncode == 0, f"stderr: {result.stderr}"
    # Should show throughput section
    assert "rounds" in result.stdout.lower()
    # zhipu has 5 tasks / 4 conc = 2 rounds
    assert "2 rounds" in result.stdout


def test_throughput_imbalance_suggestion():
    """When drain times differ >2x, suggests redistribution."""
    queue = textwrap.dedent("""\
        # Queue
        - [ ] `ribosome --provider zhipu --max-turns 30 "T1"`
        - [ ] `ribosome --provider zhipu --max-turns 30 "T2"`
        - [ ] `ribosome --provider zhipu --max-turns 30 "T3"`
        - [ ] `ribosome --provider zhipu --max-turns 30 "T4"`
        - [ ] `ribosome --provider zhipu --max-turns 30 "T5"`
        - [ ] `ribosome --provider zhipu --max-turns 30 "T6"`
        - [ ] `ribosome --provider zhipu --max-turns 30 "T7"`
        - [ ] `ribosome --provider zhipu --max-turns 30 "T8"`
        - [ ] `ribosome --provider volcano --max-turns 30 "T9"`
    """)
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        result = _run_queue_balance(queue, Path(td))
    assert result.returncode == 0, f"stderr: {result.stderr}"
    # zhipu: 8/4 = 2 rounds, volcano: 1/8 = 1 round
    # Should detect throughput imbalance
    assert "imbalance" in result.stdout.lower() or "move" in result.stdout.lower()


def test_json_output():
    """--json flag produces valid JSON with expected keys."""
    queue = textwrap.dedent("""\
        # Queue
        - [ ] `ribosome --provider zhipu --max-turns 30 "Task A"`
        - [ ] `ribosome --provider volcano --max-turns 30 "Task B"`
    """)
    import json
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        queue_file = Path(td) / "translation-queue.md"
        queue_file.write_text(queue)
        result = subprocess.run(
            [sys.executable, str(EFFECTOR), str(queue_file), "--json"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    data = json.loads(result.stdout)
    assert "provider_counts" in data
    assert "throughput" in data
    assert "concurrency" in data
    assert data["provider_counts"]["zhipu"] == 1
    assert data["provider_counts"]["volcano"] == 1
    assert data["concurrency"]["zhipu"] == 4
    assert data["concurrency"]["volcano"] == 8


def test_unassigned_assigns_to_spare_capacity():
    """Unassigned tasks should be suggested for provider with most spare."""
    queue = textwrap.dedent("""\
        # Queue
        #### Build — orphan task 1
        #### Build — orphan task 2
        - [ ] `ribosome --provider volcano --max-turns 30 "Task A"`
    """)
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        result = _run_queue_balance(queue, Path(td))
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "unassigned" in result.stdout.lower()
    # Should suggest assigning to a provider with spare capacity
    assert "assign" in result.stdout.lower() or "dispatch" in result.stdout.lower()
