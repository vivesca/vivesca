from __future__ import annotations

"""Tests for compaction hook."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "synaptic"))
from typing import TYPE_CHECKING

import compaction

if TYPE_CHECKING:
    import pytest

# ── mod_auto_flush ───────────────────────────────────────────


def test_mod_auto_flush_clean_repos() -> None:
    """Clean repos produce no output."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)
        compaction.mod_auto_flush()
    # subprocess.run called but no messages printed


def test_mod_auto_flush_dirty_repo(capsys: pytest.CaptureFixture[str]) -> None:
    """Dirty repo triggers auto-commit and push."""

    def mock_run(cmd, *args, **kwargs):
        m = MagicMock(returncode=0, stderr="")
        cmd_str = cmd if isinstance(cmd, str) else " ".join(cmd)
        if "status" in cmd_str and "--porcelain" in cmd_str:
            m.stdout = " M file.py\n"
        else:
            m.stdout = ""
        return m

    with patch("subprocess.run", side_effect=mock_run):
        compaction.mod_auto_flush()
    captured = capsys.readouterr()
    assert "auto-committed" in captured.err


# ── mod_log_compaction ──────────────────────────────────────


def test_mod_log_compaction_writes(tmp_path: Path) -> None:
    """Patching HOME so daily note path resolves inside tmp_path."""
    # Build the nested dir structure the function expects: HOME/notes/Daily/
    daily_dir = tmp_path / "notes" / "Daily"
    daily_dir.mkdir(parents=True)
    daily_note = daily_dir / f"{__import__('datetime').datetime.now().strftime('%Y-%m-%d')}.md"
    daily_note.write_text("# Daily\n")
    data = {"custom_instructions": "test compact"}
    with patch.object(compaction, "HOME", tmp_path):
        compaction.mod_log_compaction(data)
    content = daily_note.read_text()
    assert "Compact" in content
    assert "test compact" in content


# ── main ─────────────────────────────────────────────────────


def test_main_handles_empty_stdin(tmp_path: Path) -> None:
    """main() should not crash with empty stdin."""
    with patch("sys.stdin", new_callable=lambda: lambda: iter([])):
        with patch.object(compaction, "HOME", tmp_path):
            # Should not raise
            compaction.main()
