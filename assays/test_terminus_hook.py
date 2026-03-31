from __future__ import annotations

"""Tests for terminus hook."""

import json
import re
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "synaptic"))
import terminus


# ── mod_dirty_repos ─────────────────────────────────────────


def test_mod_dirty_repos_all_clean(capsys: pytest.CaptureFixture[str]) -> None:
    """Clean repos produce no output."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        terminus.mod_dirty_repos()
    captured = capsys.readouterr()
    assert "Uncommitted" not in captured.out


def test_mod_dirty_repos_with_dirty(capsys: pytest.CaptureFixture[str]) -> None:
    """Dirty repos produce a warning message."""

    def mock_run(cmd, *args, **kwargs):
        m = MagicMock(returncode=0, stderr="")
        cmd_str = cmd if isinstance(cmd, str) else " ".join(cmd)
        if "status" in cmd_str and "--porcelain" in cmd_str:
            m.stdout = " M file.py\n"
        else:
            m.stdout = ""
        return m

    with patch("subprocess.run", side_effect=mock_run):
        terminus.mod_dirty_repos()
    captured = capsys.readouterr()
    assert "Uncommitted" in captured.out


# ── mod_contracts ────────────────────────────────────────────


def test_mod_contracts_no_dir(tmp_path: Path) -> None:
    """No contracts directory = no action."""
    with patch.object(terminus, "CONTRACTS_DIR", tmp_path / "nonexistent"):
        terminus.mod_contracts()
    # Should not raise or exit


def test_mod_contracts_all_checked(tmp_path: Path) -> None:
    """Contract with all items checked = no blocker."""
    contracts_dir = tmp_path / "contracts"
    contracts_dir.mkdir()
    (contracts_dir / "test.md").write_text("# Contract\n- [x] Done\n- [x] Also done\n")
    with patch.object(terminus, "CONTRACTS_DIR", contracts_dir):
        terminus.mod_contracts()
    # Should not raise or exit


def test_mod_contracts_unchecked_exits(tmp_path: Path) -> None:
    """Contract with unchecked items = sys.exit(2)."""
    contracts_dir = tmp_path / "contracts"
    contracts_dir.mkdir()
    (contracts_dir / "blocker.md").write_text("# Contract\n- [ ] Todo item\n")
    with patch.object(terminus, "CONTRACTS_DIR", contracts_dir):
        with pytest.raises(SystemExit) as exc_info:
            terminus.mod_contracts()
        assert exc_info.value.code == 2


# ── mod_anabolism ────────────────────────────────────────────


def test_mod_anabolism_no_lock(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """No anabolism lock file = no output."""
    with patch.object(terminus, "ANAB_LOCK", tmp_path / "nope"):
        terminus.mod_anabolism()
    captured = capsys.readouterr()
    assert captured.out == ""


def test_mod_anabolism_green_budget(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Green budget = block message."""
    lock = tmp_path / ".anabolism-guard-active"
    lock.touch()
    with patch.object(terminus, "ANAB_LOCK", lock):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="green", returncode=0)
            terminus.mod_anabolism()
    captured = capsys.readouterr()
    result = json.loads(captured.out.strip())
    assert result["decision"] == "block"


# ── mod_consolidation ────────────────────────────────────────


def test_mod_consolidation_recent_skip(tmp_path: Path) -> None:
    """Recent consolidation = no action."""
    import time
    state_file = tmp_path / "consolidation-last.json"
    state_file.write_text(json.dumps({"ts": time.time() - 100}))
    with patch.object(terminus, "CONSOL_STATE", state_file):
        terminus.mod_consolidation()
    # Should not launch subprocess


def test_mod_consolidation_triggers(tmp_path: Path) -> None:
    """Stale consolidation = launches dissolve."""
    import time
    state_file = tmp_path / "consolidation-last.json"
    state_file.write_text(json.dumps({"ts": time.time() - 86400}))
    with patch.object(terminus, "CONSOL_STATE", state_file):
        with patch("subprocess.Popen") as mock_popen:
            terminus.mod_consolidation()
            mock_popen.assert_called_once()
