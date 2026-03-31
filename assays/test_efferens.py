#!/usr/bin/env python3
"""Tests for effectors/efferens — shared notice board CLI.

Unit tests mock acta; integration tests exercise the real CLI via subprocess.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

EFFERENS = Path(__file__).resolve().parents[1] / "effectors" / "efferens"


# ── Load module via exec (with acta mocked) ──────────────────────────────────


@pytest.fixture()
def efferens():
    """Load efferens module with acta mocked."""
    mock_acta = MagicMock()
    ns: dict = {
        "__name__": "efferens",
        "__file__": str(EFFERENS),
    }
    source = EFFERENS.read_text()
    # Pre-populate sys.modules so the `import acta` inside exec succeeds
    with patch.dict(sys.modules, {"acta": mock_acta}):
        exec(source, ns)
    mod = type("efferens", (), {})()
    for k, v in ns.items():
        if not k.startswith("__"):
            setattr(mod, k, v)
    mod._acta = mock_acta
    return mod


# ── cmd_list ─────────────────────────────────────────────────────────────────


class TestCmdList:
    def test_empty_board(self, efferens, capsys):
        efferens._acta.read.return_value = []
        args = argparse.Namespace(to=None)
        efferens.cmd_list(args)
        assert "Board empty" in capsys.readouterr().out

    def test_empty_board_filtered(self, efferens, capsys):
        efferens._acta.read.return_value = []
        args = argparse.Namespace(to="terry")
        efferens.cmd_list(args)
        assert "No messages for 'terry'" in capsys.readouterr().out

    def test_lists_messages(self, efferens, capsys):
        efferens._acta.read.return_value = [
            {
                "id": "2026-01-01-test.md",
                "from": "copia",
                "to": "terry",
                "severity": "action",
                "body": "Do something important",
            },
        ]
        efferens.cmd_list(argparse.Namespace(to=None))
        out = capsys.readouterr().out
        assert "1 message(s)" in out
        assert "2026-01-01-test.md" in out
        assert "copia → terry" in out
        assert "Do something important" in out

    def test_action_marker(self, efferens, capsys):
        efferens._acta.read.return_value = [
            {"id": "a.md", "from": "x", "to": "y", "severity": "action", "body": "b"},
        ]
        efferens.cmd_list(argparse.Namespace(to=None))
        assert "[!]" in capsys.readouterr().out

    def test_warning_marker(self, efferens, capsys):
        efferens._acta.read.return_value = [
            {"id": "w.md", "from": "x", "to": "y", "severity": "warning", "body": "b"},
        ]
        efferens.cmd_list(argparse.Namespace(to=None))
        assert "[~]" in capsys.readouterr().out

    def test_info_marker(self, efferens, capsys):
        efferens._acta.read.return_value = [
            {"id": "i.md", "from": "x", "to": "y", "severity": "info", "body": "b"},
        ]
        efferens.cmd_list(argparse.Namespace(to=None))
        out = capsys.readouterr().out
        assert "[ ]" in out

    def test_filtered_by_to(self, efferens, capsys):
        efferens._acta.read.return_value = [
            {"id": "m.md", "from": "x", "to": "test-filter", "severity": "info", "body": "hi"},
        ]
        efferens.cmd_list(argparse.Namespace(to="test-filter"))
        out = capsys.readouterr().out
        assert "(to: test-filter)" in out

    def test_body_truncated_at_100(self, efferens, capsys):
        efferens._acta.read.return_value = [
            {"id": "long.md", "from": "x", "to": "y", "severity": "info", "body": "A" * 200},
        ]
        efferens.cmd_list(argparse.Namespace(to=None))
        out = capsys.readouterr().out
        # Preview should be truncated; full 200 chars should not appear
        assert "A" * 100 in out
        assert "A" * 101 not in out

    def test_newlines_in_body_collapsed(self, efferens, capsys):
        efferens._acta.read.return_value = [
            {"id": "nl.md", "from": "x", "to": "y", "severity": "info", "body": "line1\nline2"},
        ]
        efferens.cmd_list(argparse.Namespace(to=None))
        out = capsys.readouterr().out
        assert "line1 line2" in out


# ── cmd_post ─────────────────────────────────────────────────────────────────


class TestCmdPost:
    def test_post_prints_filename(self, efferens, capsys):
        efferens._acta.post.return_value = Path("2026-01-01-test.md")
        args = argparse.Namespace(
            message="hello", sender="cli", to="all", severity="info", subject="test"
        )
        efferens.cmd_post(args)
        assert "Posted: 2026-01-01-test.md" in capsys.readouterr().out

    def test_post_passes_all_args(self, efferens):
        efferens._acta.post.return_value = Path("x.md")
        args = argparse.Namespace(
            message="msg", sender="bot", to="terry", severity="warning", subject="sub"
        )
        efferens.cmd_post(args)
        efferens._acta.post.assert_called_once_with(
            message="msg", sender="bot", to="terry", severity="warning", subject="sub"
        )


# ── cmd_clear ────────────────────────────────────────────────────────────────


class TestCmdClear:
    def test_clear_all(self, efferens, capsys):
        efferens._acta.clear_all.return_value = 5
        efferens.cmd_clear(argparse.Namespace(all=True, id=None))
        assert "Cleared 5 message(s)" in capsys.readouterr().out

    def test_clear_one(self, efferens, capsys):
        efferens._acta.clear.return_value = True
        efferens.cmd_clear(argparse.Namespace(all=False, id="2026-01-01-test.md"))
        assert "Cleared: 2026-01-01-test.md" in capsys.readouterr().out

    def test_clear_one_not_found(self, efferens):
        efferens._acta.clear.return_value = False
        with pytest.raises(SystemExit) as exc:
            efferens.cmd_clear(argparse.Namespace(all=False, id="nope.md"))
        assert exc.value.code == 1

    def test_clear_no_args(self, efferens):
        with pytest.raises(SystemExit) as exc:
            efferens.cmd_clear(argparse.Namespace(all=False, id=None))
        assert exc.value.code == 1


# ── cmd_archive ──────────────────────────────────────────────────────────────


class TestCmdArchive:
    def test_archive_all(self, efferens, capsys):
        efferens._acta.archive_all.return_value = 3
        efferens.cmd_archive(argparse.Namespace(all=True, id=None))
        assert "Archived 3 message(s)" in capsys.readouterr().out

    def test_archive_one(self, efferens, capsys):
        efferens._acta.archive.return_value = True
        efferens.cmd_archive(argparse.Namespace(all=False, id="2026-01-01-test.md"))
        assert "Archived: 2026-01-01-test.md" in capsys.readouterr().out

    def test_archive_one_not_found(self, efferens):
        efferens._acta.archive.return_value = False
        with pytest.raises(SystemExit) as exc:
            efferens.cmd_archive(argparse.Namespace(all=False, id="nope.md"))
        assert exc.value.code == 1

    def test_archive_no_args(self, efferens):
        with pytest.raises(SystemExit) as exc:
            efferens.cmd_archive(argparse.Namespace(all=False, id=None))
        assert exc.value.code == 1


# ── cmd_count ────────────────────────────────────────────────────────────────


class TestCmdCount:
    def test_count(self, efferens, capsys):
        efferens._acta.count.return_value = 42
        efferens.cmd_count(argparse.Namespace())
        assert "42" in capsys.readouterr().out


# ── main (argparse routing) ──────────────────────────────────────────────────


class TestMain:
    def test_default_runs_list(self, efferens, capsys):
        """No subcommand → list."""
        efferens._acta.read.return_value = []
        with patch("sys.argv", ["efferens"]):
            efferens.main()
        assert "Board empty" in capsys.readouterr().out

    def test_list_subcommand(self, efferens, capsys):
        efferens._acta.read.return_value = []
        with patch("sys.argv", ["efferens", "list"]):
            efferens.main()
        assert "Board empty" in capsys.readouterr().out

    def test_count_subcommand(self, efferens, capsys):
        efferens._acta.count.return_value = 7
        with patch("sys.argv", ["efferens", "count"]):
            efferens.main()
        assert "7" in capsys.readouterr().out

    def test_post_subcommand(self, efferens, capsys):
        efferens._acta.post.return_value = Path("2026-03-31-test.md")
        with patch("sys.argv", ["efferens", "post", "hello", "--from", "test"]):
            efferens.main()
        assert "Posted:" in capsys.readouterr().out


# ── Integration (subprocess, real acta) ──────────────────────────────────────


class TestIntegration:
    """These tests hit the real acta board. They create & clean up."""

    def test_help(self):
        r = subprocess.run(
            [sys.executable, str(EFFERENS), "--help"],
            capture_output=True, text=True,
        )
        assert r.returncode == 0
        assert "shared notice board" in r.stdout

    def test_count_returns_int(self):
        r = subprocess.run(
            [sys.executable, str(EFFERENS), "count"],
            capture_output=True, text=True,
        )
        assert r.returncode == 0
        int(r.stdout.strip())  # must be parseable as int

    def test_list_runs(self):
        r = subprocess.run(
            [sys.executable, str(EFFERENS), "list"],
            capture_output=True, text=True,
        )
        assert r.returncode == 0

    def test_post_and_archive_roundtrip(self):
        # Post
        r = subprocess.run(
            [sys.executable, str(EFFERENS), "post",
             "efferens assay test", "--from", "pytest",
             "--to", "pytest", "--subject", "efferens-roundtrip"],
            capture_output=True, text=True,
        )
        assert r.returncode == 0
        assert "Posted:" in r.stdout
        posted_name = r.stdout.split("Posted:")[1].strip()

        # Verify it appears in list --to pytest
        r = subprocess.run(
            [sys.executable, str(EFFERENS), "list", "--to", "pytest"],
            capture_output=True, text=True,
        )
        assert posted_name in r.stdout

        # Archive it
        r = subprocess.run(
            [sys.executable, str(EFFERENS), "archive", posted_name],
            capture_output=True, text=True,
        )
        assert r.returncode == 0
        assert f"Archived: {posted_name}" in r.stdout

    def test_clear_nonexistent_exits_1(self):
        r = subprocess.run(
            [sys.executable, str(EFFERENS), "clear", "nonexistent-99999.md"],
            capture_output=True, text=True,
        )
        assert r.returncode == 1
        assert "Not found" in r.stderr
