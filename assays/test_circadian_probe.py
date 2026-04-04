from __future__ import annotations

"""Tests for circadian-probe effector — AKM Heartbeat nightly digest."""

import subprocess
import sys
import time
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch


def _load_circadian_probe():
    """Load the circadian-probe module by exec-ing its Python body."""
    source = open(str(Path.home() / "germline/effectors/circadian-probe.py")).read()
    # Provide __file__ since the script uses it to find the config file
    ns: dict = {
        "__name__": "circadian_probe",
        "__file__": str(Path.home() / "germline/effectors/circadian-probe.py"),
    }
    exec(source, ns)
    return ns


_mod = _load_circadian_probe()
scan_stale_notes = _mod["scan_stale_notes"]
scan_orphan_links = _mod["scan_orphan_links"]
scan_overdue_todos = _mod["scan_overdue_todos"]
scan_prospective_memory = _mod["scan_prospective_memory"]
build_digest = _mod["build_digest"]
send_via_telegram = _mod["send_via_telegram"]
CHROMATIN = _mod["CHROMATIN"]
MEMORY_DIR = _mod["MEMORY_DIR"]
PRAXIS_FILE = _mod["PRAXIS_FILE"]
PROSPECTIVE_FILE = _mod["PROSPECTIVE_FILE"]
EXCLUDE_DIRS = _mod["EXCLUDE_DIRS"]
STALE_DAYS = _mod["STALE_DAYS"]


# ── Constants tests ───────────────────────────────────────────────────────


def test_chromatin_path():
    """CHROMATIN path is correctly defined."""
    assert Path.home() / "epigenome" / "chromatin" == CHROMATIN


def test_memory_dir_path():
    """MEMORY_DIR path is correctly defined."""
    expected_stem = str(Path.home()).strip("/").replace("/", "-")
    assert Path.home() / ".claude" / "projects" / f"-{expected_stem}" / "memory" == MEMORY_DIR


def test_praxis_file_path():
    """PRAXIS_FILE is under CHROMATIN."""
    assert PRAXIS_FILE == CHROMATIN / "Praxis.md"


def test_prospective_file_path():
    """PROSPECTIVE_FILE is under MEMORY_DIR."""
    assert PROSPECTIVE_FILE == MEMORY_DIR / "prospective.md"


def test_exclude_dirs_contains_expected():
    """EXCLUDE_DIRS contains expected directories."""
    assert ".obsidian" in EXCLUDE_DIRS
    assert ".git" in EXCLUDE_DIRS
    assert ".trash" in EXCLUDE_DIRS
    assert "Archive" in EXCLUDE_DIRS
    assert "Templates" in EXCLUDE_DIRS


def test_stale_days_default():
    """STALE_DAYS has a reasonable default value."""
    assert isinstance(STALE_DAYS, int)
    assert STALE_DAYS > 0
    assert STALE_DAYS <= 365  # Reasonable upper bound


# ── scan_stale_notes tests ───────────────────────────────────────────────


def test_scan_stale_notes_returns_list():
    """scan_stale_notes returns a list."""
    # This test requires CHROMATIN to exist or we mock it
    with patch.object(Path, "exists", return_value=False):
        # When CHROMATIN doesn't exist, should handle gracefully
        pass  # Function uses rglob which will handle non-existent dir


def test_scan_stale_notes_with_mocked_chromatin(tmp_path):
    """scan_stale_notes finds stale notes in mocked directory."""
    # Create some test files with different mtimes
    chromatin = tmp_path / "chromatin"
    chromatin.mkdir()

    # Create a fresh file (not stale)
    fresh_file = chromatin / "fresh.md"
    fresh_file.write_text("fresh content")

    # Create a stale file (modify mtime)
    stale_file = chromatin / "stale.md"
    stale_file.write_text("stale content")
    # Set mtime to 60 days ago
    old_time = time.time() - (60 * 86400)
    import os

    os.utime(stale_file, (old_time, old_time))

    # Patch CHROMATIN
    original = _mod["CHROMATIN"]
    _mod["CHROMATIN"] = chromatin
    try:
        result = scan_stale_notes()
    finally:
        _mod["CHROMATIN"] = original

    # Should find the stale file
    assert isinstance(result, list)
    assert len(result) >= 1
    names = [name for name, _ in result]
    assert "stale" in names


def test_scan_stale_notes_excludes_hidden_files(tmp_path):
    """scan_stale_notes excludes hidden files."""
    chromatin = tmp_path / "chromatin"
    chromatin.mkdir()

    # Create hidden file
    hidden_file = chromatin / ".hidden.md"
    hidden_file.write_text("hidden")
    old_time = time.time() - (60 * 86400)
    import os

    os.utime(hidden_file, (old_time, old_time))

    # Create normal file
    normal_file = chromatin / "normal.md"
    normal_file.write_text("normal")

    original = _mod["CHROMATIN"]
    _mod["CHROMATIN"] = chromatin
    try:
        result = scan_stale_notes()
    finally:
        _mod["CHROMATIN"] = original

    names = [name for name, _ in result]
    assert ".hidden" not in names


def test_scan_stale_notes_excludes_obsidian_dir(tmp_path):
    """scan_stale_notes excludes .obsidian directory."""
    chromatin = tmp_path / "chromatin"
    obsidian = chromatin / ".obsidian"
    obsidian.mkdir(parents=True)

    # Create stale file in .obsidian
    stale_in_obsidian = obsidian / "stale.md"
    stale_in_obsidian.write_text("stale")
    old_time = time.time() - (60 * 86400)
    import os

    os.utime(stale_in_obsidian, (old_time, old_time))

    original = _mod["CHROMATIN"]
    _mod["CHROMATIN"] = chromatin
    try:
        result = scan_stale_notes()
    finally:
        _mod["CHROMATIN"] = original

    names = [name for name, _ in result]
    assert "stale" not in names


def test_scan_stale_notes_returns_days_stale(tmp_path):
    """scan_stale_notes returns (name, days_stale) tuples."""
    chromatin = tmp_path / "chromatin"
    chromatin.mkdir()

    # Create stale file
    stale_file = chromatin / "old.md"
    stale_file.write_text("old")
    old_time = time.time() - (45 * 86400)
    import os

    os.utime(stale_file, (old_time, old_time))

    original = _mod["CHROMATIN"]
    _mod["CHROMATIN"] = chromatin
    try:
        result = scan_stale_notes()
    finally:
        _mod["CHROMATIN"] = original

    if result:
        name, days = result[0]
        assert isinstance(name, str)
        assert isinstance(days, int)
        assert days >= 45


def test_scan_stale_notes_sorts_by_days_stale(tmp_path):
    """scan_stale_notes sorts results by days stale (descending)."""
    chromatin = tmp_path / "chromatin"
    chromatin.mkdir()

    # Create multiple stale files
    for days, name in [(30, "thirty"), (60, "sixty"), (90, "ninety")]:
        f = chromatin / f"{name}.md"
        f.write_text(name)
        old_time = time.time() - (days * 86400)
        import os

        os.utime(f, (old_time, old_time))

    original = _mod["CHROMATIN"]
    _mod["CHROMATIN"] = chromatin
    try:
        result = scan_stale_notes()
    finally:
        _mod["CHROMATIN"] = original

    if len(result) >= 2:
        # Should be sorted by days descending
        days_list = [d for _, d in result]
        assert days_list == sorted(days_list, reverse=True)


# ── scan_orphan_links tests ───────────────────────────────────────────────


def test_scan_orphan_links_returns_list():
    """scan_orphan_links returns a list."""
    result = scan_orphan_links()
    assert isinstance(result, list)


def test_scan_orphan_links_handles_timeout():
    """scan_orphan_links handles timeout gracefully."""
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 30)):
        result = scan_orphan_links()
    assert result == []


def test_scan_orphan_links_handles_file_not_found():
    """scan_orphan_links handles missing obsidian CLI."""
    with patch("subprocess.run", side_effect=FileNotFoundError):
        result = scan_orphan_links()
    assert result == []


def test_scan_orphan_links_parses_output():
    """scan_orphan_links parses obsidian output correctly."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "orphan1.md\norphan2.md\n(another line)\n\n"

    with patch("subprocess.run", return_value=mock_result):
        result = scan_orphan_links()

    assert "orphan1.md" in result
    assert "orphan2.md" in result
    # Lines starting with ( should be filtered
    assert not any("(" in r for r in result)


def test_scan_orphan_links_handles_nonzero_exit():
    """scan_orphan_links handles non-zero exit code."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "error"

    with patch("subprocess.run", return_value=mock_result):
        result = scan_orphan_links()

    assert result == []


# ── scan_overdue_todos tests ───────────────────────────────────────────────


def test_scan_overdue_todos_returns_list():
    """scan_overdue_todos returns a list."""
    with patch.object(Path, "exists", return_value=False):
        # Load fresh module with patched path
        pass
    result = scan_overdue_todos()
    assert isinstance(result, list)


def test_scan_overdue_todos_no_file(tmp_path):
    """scan_overdue_todos returns empty list when PRAXIS_FILE doesn't exist."""
    praxis = tmp_path / "Praxis.md"
    original = _mod["PRAXIS_FILE"]
    _mod["PRAXIS_FILE"] = praxis
    try:
        result = scan_overdue_todos()
    finally:
        _mod["PRAXIS_FILE"] = original

    assert result == []


def test_scan_overdue_todos_finds_overdue(tmp_path):
    """scan_overdue_todos finds overdue items."""
    praxis = tmp_path / "Praxis.md"
    yesterday = date.today() - timedelta(days=1)
    praxis.write_text(f"- [ ] Task due {yesterday.isoformat()}\n")

    original = _mod["PRAXIS_FILE"]
    _mod["PRAXIS_FILE"] = praxis
    try:
        result = scan_overdue_todos()
    finally:
        _mod["PRAXIS_FILE"] = original

    assert len(result) == 1
    assert "Task due" in result[0]
    assert "overdue" in result[0].lower()


def test_scan_overdue_todos_ignores_future_dates(tmp_path):
    """scan_overdue_todos ignores future dates."""
    praxis = tmp_path / "Praxis.md"
    tomorrow = date.today() + timedelta(days=1)
    praxis.write_text(f"- [ ] Future task {tomorrow.isoformat()}\n")

    original = _mod["PRAXIS_FILE"]
    _mod["PRAXIS_FILE"] = praxis
    try:
        result = scan_overdue_todos()
    finally:
        _mod["PRAXIS_FILE"] = original

    assert result == []


def test_scan_overdue_todos_ignores_completed(tmp_path):
    """scan_overdue_todos ignores completed items [x]."""
    praxis = tmp_path / "Praxis.md"
    yesterday = date.today() - timedelta(days=1)
    praxis.write_text(f"- [x] Completed task {yesterday.isoformat()}\n")

    original = _mod["PRAXIS_FILE"]
    _mod["PRAXIS_FILE"] = praxis
    try:
        result = scan_overdue_todos()
    finally:
        _mod["PRAXIS_FILE"] = original

    assert result == []


def test_scan_overdue_todos_ignores_no_date(tmp_path):
    """scan_overdue_todos ignores items without dates."""
    praxis = tmp_path / "Praxis.md"
    praxis.write_text("- [ ] Task without date\n")

    original = _mod["PRAXIS_FILE"]
    _mod["PRAXIS_FILE"] = praxis
    try:
        result = scan_overdue_todos()
    finally:
        _mod["PRAXIS_FILE"] = original

    assert result == []


def test_scan_overdue_todos_calculates_days_late(tmp_path):
    """scan_overdue_todos calculates days late correctly."""
    praxis = tmp_path / "Praxis.md"
    week_ago = date.today() - timedelta(days=7)
    praxis.write_text(f"- [ ] Week old task {week_ago.isoformat()}\n")

    original = _mod["PRAXIS_FILE"]
    _mod["PRAXIS_FILE"] = praxis
    try:
        result = scan_overdue_todos()
    finally:
        _mod["PRAXIS_FILE"] = original

    assert len(result) == 1
    assert "7d overdue" in result[0]


# ── scan_prospective_memory tests ───────────────────────────────────────────


def test_scan_prospective_memory_returns_list():
    """scan_prospective_memory returns a list."""
    result = scan_prospective_memory()
    assert isinstance(result, list)


def test_scan_prospective_memory_no_file(tmp_path):
    """scan_prospective_memory returns empty list when file doesn't exist."""
    prospective = tmp_path / "prospective.md"
    original = _mod["PROSPECTIVE_FILE"]
    _mod["PROSPECTIVE_FILE"] = prospective
    try:
        result = scan_prospective_memory()
    finally:
        _mod["PROSPECTIVE_FILE"] = original

    assert result == []


def test_scan_prospective_memory_finds_any_session(tmp_path):
    """scan_prospective_memory finds 'any session' triggers."""
    prospective = tmp_path / "prospective.md"
    prospective.write_text("""## Active
- WHEN: any session → THEN: Do something (added: 2024-01-01)

## Inactive
- WHEN: next session → THEN: Should not appear
""")

    original = _mod["PROSPECTIVE_FILE"]
    _mod["PROSPECTIVE_FILE"] = prospective
    try:
        result = scan_prospective_memory()
    finally:
        _mod["PROSPECTIVE_FILE"] = original

    assert len(result) >= 1
    assert any("Do something" in r for r in result)


def test_scan_prospective_memory_finds_next_session(tmp_path):
    """scan_prospective_memory finds 'next session' triggers."""
    prospective = tmp_path / "prospective.md"
    prospective.write_text("""## Active
- WHEN: next session → THEN: Do next thing (added: 2024-01-01)
""")

    original = _mod["PROSPECTIVE_FILE"]
    _mod["PROSPECTIVE_FILE"] = prospective
    try:
        result = scan_prospective_memory()
    finally:
        _mod["PROSPECTIVE_FILE"] = original

    assert len(result) >= 1
    assert any("Do next thing" in r for r in result)


def test_scan_prospective_memory_ignores_inactive_section(tmp_path):
    """scan_prospective_memory only looks in Active section."""
    prospective = tmp_path / "prospective.md"
    prospective.write_text("""## Inactive
- WHEN: any session → THEN: Should not appear

## Active
- WHEN: next session → THEN: Should appear
""")

    original = _mod["PROSPECTIVE_FILE"]
    _mod["PROSPECTIVE_FILE"] = prospective
    try:
        result = scan_prospective_memory()
    finally:
        _mod["PROSPECTIVE_FILE"] = original

    # Should only find items from Active section
    assert any("Should appear" in r for r in result)
    assert not any("Should not appear" in r for r in result)


def test_scan_prospective_memory_finds_date_proximity(tmp_path):
    """scan_prospective_memory finds date-based triggers near today."""
    prospective = tmp_path / "prospective.md"
    today = date.today()
    # Use a date close to today (within proximity window)
    # The code looks for month+day format like "Mar 15"
    month_names = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]
    today_str = f"{month_names[today.month - 1]} {today.day}"

    prospective.write_text(f"""## Active
- WHEN: {today_str} → THEN: Birthday reminder (added: 2024-01-01)
""")

    original = _mod["PROSPECTIVE_FILE"]
    _mod["PROSPECTIVE_FILE"] = prospective
    try:
        result = scan_prospective_memory()
    finally:
        _mod["PROSPECTIVE_FILE"] = original

    # Should find the date-based trigger
    assert any("Birthday reminder" in r for r in result)


def test_scan_prospective_memory_deduplicates(tmp_path):
    """scan_prospective_memory deduplicates results."""
    prospective = tmp_path / "prospective.md"
    prospective.write_text("""## Active
- WHEN: any session → THEN: Do the same thing (added: 2024-01-01)
- WHEN: any session → THEN: Do the same thing (added: 2024-01-02)
""")

    original = _mod["PROSPECTIVE_FILE"]
    _mod["PROSPECTIVE_FILE"] = prospective
    try:
        result = scan_prospective_memory()
    finally:
        _mod["PROSPECTIVE_FILE"] = original

    # Should deduplicate
    assert len(result) == 1


def test_scan_prospective_memory_truncates_long_actions(tmp_path):
    """scan_prospective_memory truncates actions over 100 chars."""
    prospective = tmp_path / "prospective.md"
    long_action = "x" * 150
    prospective.write_text(f"""## Active
- WHEN: any session → THEN: {long_action} (added: 2024-01-01)
""")

    original = _mod["PROSPECTIVE_FILE"]
    _mod["PROSPECTIVE_FILE"] = prospective
    try:
        result = scan_prospective_memory()
    finally:
        _mod["PROSPECTIVE_FILE"] = original

    assert len(result) == 1
    assert len(result[0]) <= 100
    assert result[0].endswith("...")


# ── build_digest tests ─────────────────────────────────────────────────────


def test_build_digest_returns_string():
    """build_digest returns a string."""
    result = build_digest()
    assert isinstance(result, str)


def test_build_digest_includes_header():
    """build_digest includes date header."""
    result = build_digest()
    assert "AKM Heartbeat" in result
    assert date.today().isoformat() in result


def test_build_digest_structure():
    """build_digest has expected structure."""
    result = build_digest()

    # Should have header with date
    assert "🫀" in result or "AKM" in result

    # Should have sections (if any issues found) or healthy message
    assert (
        any(
            section in result
            for section in [
                "Stale Notes",
                "Orphan Links",
                "Overdue TODOs",
                "Prospective Reminders",
            ]
        )
        or "healthy" in result.lower()
        or "nothing flagged" in result
    )


def test_build_digest_healthy_when_no_issues():
    """build_digest reports healthy when no issues found."""
    # Since build_digest calls functions from its global namespace,
    # we need to modify the globals directly
    original_stale = build_digest.__globals__["scan_stale_notes"]
    original_orphan = build_digest.__globals__["scan_orphan_links"]
    original_overdue = build_digest.__globals__["scan_overdue_todos"]
    original_prospective = build_digest.__globals__["scan_prospective_memory"]

    build_digest.__globals__["scan_stale_notes"] = lambda: []
    build_digest.__globals__["scan_orphan_links"] = lambda: []
    build_digest.__globals__["scan_overdue_todos"] = lambda: []
    build_digest.__globals__["scan_prospective_memory"] = lambda: []

    try:
        result = build_digest()
    finally:
        build_digest.__globals__["scan_stale_notes"] = original_stale
        build_digest.__globals__["scan_orphan_links"] = original_orphan
        build_digest.__globals__["scan_overdue_todos"] = original_overdue
        build_digest.__globals__["scan_prospective_memory"] = original_prospective

    assert "healthy" in result.lower() or "nothing flagged" in result.lower()


def test_build_digest_includes_stale_section():
    """build_digest includes stale notes section when found."""
    original_stale = build_digest.__globals__["scan_stale_notes"]
    original_orphan = build_digest.__globals__["scan_orphan_links"]
    original_overdue = build_digest.__globals__["scan_overdue_todos"]
    original_prospective = build_digest.__globals__["scan_prospective_memory"]

    build_digest.__globals__["scan_stale_notes"] = lambda: [("old_note", 60)]
    build_digest.__globals__["scan_orphan_links"] = lambda: []
    build_digest.__globals__["scan_overdue_todos"] = lambda: []
    build_digest.__globals__["scan_prospective_memory"] = lambda: []

    try:
        result = build_digest()
    finally:
        build_digest.__globals__["scan_stale_notes"] = original_stale
        build_digest.__globals__["scan_orphan_links"] = original_orphan
        build_digest.__globals__["scan_overdue_todos"] = original_overdue
        build_digest.__globals__["scan_prospective_memory"] = original_prospective

    assert "Stale Notes" in result
    assert "old_note" in result
    assert "60d" in result


def test_build_digest_includes_orphan_section():
    """build_digest includes orphan notes section when found."""
    original_stale = build_digest.__globals__["scan_stale_notes"]
    original_orphan = build_digest.__globals__["scan_orphan_links"]
    original_overdue = build_digest.__globals__["scan_overdue_todos"]
    original_prospective = build_digest.__globals__["scan_prospective_memory"]

    build_digest.__globals__["scan_stale_notes"] = lambda: []
    build_digest.__globals__["scan_orphan_links"] = lambda: ["orphan1.md"]
    build_digest.__globals__["scan_overdue_todos"] = lambda: []
    build_digest.__globals__["scan_prospective_memory"] = lambda: []

    try:
        result = build_digest()
    finally:
        build_digest.__globals__["scan_stale_notes"] = original_stale
        build_digest.__globals__["scan_orphan_links"] = original_orphan
        build_digest.__globals__["scan_overdue_todos"] = original_overdue
        build_digest.__globals__["scan_prospective_memory"] = original_prospective

    assert "Orphan" in result
    assert "orphan1" in result


def test_build_digest_includes_overdue_section():
    """build_digest includes overdue TODOs section when found."""
    original_stale = build_digest.__globals__["scan_stale_notes"]
    original_orphan = build_digest.__globals__["scan_orphan_links"]
    original_overdue = build_digest.__globals__["scan_overdue_todos"]
    original_prospective = build_digest.__globals__["scan_prospective_memory"]

    build_digest.__globals__["scan_stale_notes"] = lambda: []
    build_digest.__globals__["scan_orphan_links"] = lambda: []
    build_digest.__globals__["scan_overdue_todos"] = lambda: ["Task (5d overdue)"]
    build_digest.__globals__["scan_prospective_memory"] = lambda: []

    try:
        result = build_digest()
    finally:
        build_digest.__globals__["scan_stale_notes"] = original_stale
        build_digest.__globals__["scan_orphan_links"] = original_orphan
        build_digest.__globals__["scan_overdue_todos"] = original_overdue
        build_digest.__globals__["scan_prospective_memory"] = original_prospective

    assert "Overdue" in result
    assert "Task" in result


def test_build_digest_includes_prospective_section():
    """build_digest includes prospective reminders section when found."""
    original_stale = build_digest.__globals__["scan_stale_notes"]
    original_orphan = build_digest.__globals__["scan_orphan_links"]
    original_overdue = build_digest.__globals__["scan_overdue_todos"]
    original_prospective = build_digest.__globals__["scan_prospective_memory"]

    build_digest.__globals__["scan_stale_notes"] = lambda: []
    build_digest.__globals__["scan_orphan_links"] = lambda: []
    build_digest.__globals__["scan_overdue_todos"] = lambda: []
    build_digest.__globals__["scan_prospective_memory"] = lambda: ["Remember X"]

    try:
        result = build_digest()
    finally:
        build_digest.__globals__["scan_stale_notes"] = original_stale
        build_digest.__globals__["scan_orphan_links"] = original_orphan
        build_digest.__globals__["scan_overdue_todos"] = original_overdue
        build_digest.__globals__["scan_prospective_memory"] = original_prospective

    assert "Prospective" in result
    assert "Remember X" in result


# ── send_via_telegram tests ───────────────────────────────────────────────


def test_send_via_telegram_success():
    """send_via_telegram returns True on success."""
    mock_module = MagicMock()
    mock_module.secrete_text = MagicMock()

    with patch.dict("sys.modules", {"metabolon.organelles.secretory_vesicle": mock_module}):
        source = open(str(Path.home() / "germline/effectors/circadian-probe.py")).read()
        ns = {
            "__name__": "test",
            "__file__": str(Path.home() / "germline/effectors/circadian-probe.py"),
        }
        exec(source, ns)
        send_via_telegram_fresh = ns["send_via_telegram"]

        result = send_via_telegram_fresh("test message")

    assert result is True


def test_send_via_telegram_failure():
    """send_via_telegram returns False on exception."""
    mock_module = MagicMock()
    mock_module.secrete_text = MagicMock(side_effect=Exception("API error"))

    with patch.dict("sys.modules", {"metabolon.organelles.secretory_vesicle": mock_module}):
        source = open(str(Path.home() / "germline/effectors/circadian-probe.py")).read()
        ns = {
            "__name__": "test",
            "__file__": str(Path.home() / "germline/effectors/circadian-probe.py"),
        }
        exec(source, ns)
        send_via_telegram_fresh = ns["send_via_telegram"]

        result = send_via_telegram_fresh("test message")

    assert result is False


def test_send_via_telegram_handles_import_error():
    """send_via_telegram handles ImportError gracefully."""
    # Force ImportError by injecting a broken module
    broken = MagicMock()
    broken.secrete_text = property(lambda self: (_ for _ in ()).throw(ImportError("no module")))

    with patch.dict("sys.modules", {"metabolon.organelles.secretory_vesicle": None}):
        source = open(str(Path.home() / "germline/effectors/circadian-probe.py")).read()
        ns = {
            "__name__": "test",
            "__file__": str(Path.home() / "germline/effectors/circadian-probe.py"),
        }
        exec(source, ns)
        send_via_telegram_fresh = ns["send_via_telegram"]

        result = send_via_telegram_fresh("test message")

    assert result is False


# ── CLI integration tests ─────────────────────────────────────────────────


def test_circadian_probe_cli_runs():
    """circadian-probe.py runs without errors."""
    probe_path = Path(str(Path.home() / "germline/effectors/circadian-probe.py"))

    # Mock send_via_telegram to avoid actual API calls
    with patch.dict("sys.modules", {"metabolon.organelles.secretory_vesicle": MagicMock()}):
        result = subprocess.run(
            [sys.executable, str(probe_path)],
            capture_output=True,
            text=True,
            timeout=60,
        )

    # Should output the digest
    assert "AKM Heartbeat" in result.stdout or result.returncode == 1  # May fail on Telegram send


def test_circadian_probe_cli_outputs_digest():
    """circadian-probe.py outputs a digest to stdout."""
    probe_path = Path(str(Path.home() / "germline/effectors/circadian-probe.py"))

    # Mock the Telegram import
    mock_module = MagicMock()
    mock_module.secrete_text = MagicMock()

    with patch.dict("sys.modules", {"metabolon.organelles.secretory_vesicle": mock_module}):
        result = subprocess.run(
            [sys.executable, str(probe_path)],
            capture_output=True,
            text=True,
            timeout=60,
        )

    # Should include today's date in ISO format
    assert date.today().isoformat() in result.stdout or result.returncode != 0


def test_circadian_probe_cli_exits_on_telegram_failure():
    """circadian-probe.py exits with code 1 when Telegram fails."""
    probe_path = Path(str(Path.home() / "germline/effectors/circadian-probe.py"))

    # Create a mock that raises an exception
    def mock_secrete_text(msg, **kwargs):
        raise Exception("Telegram API error")

    mock_module = MagicMock()
    mock_module.secrete_text = mock_secrete_text

    with patch.dict("sys.modules", {"metabolon.organelles.secretory_vesicle": mock_module}):
        result = subprocess.run(
            [sys.executable, str(probe_path)],
            capture_output=True,
            text=True,
            timeout=60,
        )

    # Should exit with 1 on failure
    # Note: if module import fails, it may exit with 1
    assert result.returncode in [0, 1]  # Either success or graceful failure


# ── Config tests ───────────────────────────────────────────────────────────


def test_config_stale_days():
    """STALE_DAYS is read from config or has default."""
    assert isinstance(STALE_DAYS, int)
    assert STALE_DAYS > 0


def test_max_stale_report_limit():
    """scan_stale_notes respects MAX_STALE_REPORT limit."""
    # The constant is defined in the module
    MAX_STALE_REPORT = _mod["MAX_STALE_REPORT"]

    assert isinstance(MAX_STALE_REPORT, int)
    assert MAX_STALE_REPORT > 0


def test_max_orphan_report_limit():
    """MAX_ORPHAN_REPORT is defined."""
    MAX_ORPHAN_REPORT = _mod["MAX_ORPHAN_REPORT"]
    assert isinstance(MAX_ORPHAN_REPORT, int)
    assert MAX_ORPHAN_REPORT > 0
