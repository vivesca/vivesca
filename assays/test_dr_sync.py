#!/usr/bin/env python3
"""Tests for effectors/dr-sync — disaster recovery sync backup tests.

All filesystem and subprocess calls are mocked.
"""

import pytest
from unittest.mock import patch, MagicMock, call
from pathlib import Path

DR_SYNC_PATH = Path(__file__).resolve().parents[1] / "effectors" / "dr-sync"


# ── Load module via exec ────────────────────────────────────────────────────

@pytest.fixture()
def dr():
    """Load dr-sync via exec into an isolated namespace."""
    ns: dict = {"__name__": "__main__"}
    source = DR_SYNC_PATH.read_text(encoding="utf-8")
    exec(source, ns)
    mod = type("dr", (), {})()
    for k, v in ns.items():
        if not k.startswith("__"):
            setattr(mod, k, v)
    return mod


# ── Constants ───────────────────────────────────────────────────────────────


class TestDRConstants:
    def test_dest_path(self, dr):
        expected = Path.home() / "officina" / "claude-backup"
        assert dr.DEST == expected

    def test_home_is_path(self, dr):
        assert isinstance(dr.HOME, Path)
        assert dr.HOME == Path.home()


# ── Claude settings sync ───────────────────────────────────────────────────


class TestDRSettingsSync:
    def test_settings_json_copied(self, dr):
        copy_calls = []

        def mock_exists(self_path):
            s = str(self_path)
            return s.endswith("settings.json") or s.endswith("settings.local.json")

        with patch("shutil.copy2", side_effect=lambda s, d: copy_calls.append((s, d))):
            with patch("shutil.copytree"):
                with patch("pathlib.Path.exists", mock_exists):
                    with patch("subprocess.run"):
                        dr.sync()

        assert any("settings.json" in str(s) for s, d in copy_calls)
        assert any("settings.local.json" in str(s) for s, d in copy_calls)

    def test_settings_not_copied_when_missing(self, dr):
        copy_calls = []

        def mock_exists(self_path):
            s = str(self_path)
            return s.endswith("settings.json") is False and s.endswith("settings.local.json") is False

        with patch("shutil.copy2", side_effect=lambda s, d: copy_calls.append((s, d))):
            with patch("shutil.copytree"):
                with patch("pathlib.Path.exists", return_value=False):
                    with patch("subprocess.run"):
                        dr.sync()

        assert not any("settings" in str(s) for s, d in copy_calls)


# ── Claude memory sync ─────────────────────────────────────────────────────


class TestDRMemorySync:
    def test_memory_copied_when_exists(self, dr):
        mock_copytree = MagicMock()

        def mock_exists(self_path):
            s = str(self_path)
            return "memory" in s

        with patch("shutil.copy2"):
            with patch("shutil.copytree", mock_copytree):
                with patch("shutil.rmtree"):
                    with patch("pathlib.Path.exists", mock_exists):
                        with patch("subprocess.run"):
                            dr.sync()
                            mock_copytree.assert_called_once()

    def test_memory_dest_removed_first(self, dr):
        rmtree_calls = []
        copytree_calls = []

        def mock_exists(self_path):
            return "memory" in str(self_path)

        with patch("shutil.copy2"):
            with patch("shutil.copytree", side_effect=lambda s, d: copytree_calls.append((s, d))):
                with patch("shutil.rmtree", side_effect=lambda p: rmtree_calls.append(p)):
                    with patch("pathlib.Path.exists", mock_exists):
                        with patch("subprocess.run"):
                            dr.sync()

        # rmtree should have been called for the old dest
        assert len(rmtree_calls) >= 1
        assert len(copytree_calls) >= 1


# ── Shell env sync ─────────────────────────────────────────────────────────


class TestDRZshEnv:
    def test_zshenv_copied(self, dr):
        copy_calls = []

        def mock_exists(self_path):
            return str(self_path).endswith(".zshenv.local")

        with patch("shutil.copy2", side_effect=lambda s, d: copy_calls.append((s, d))):
            with patch("shutil.copytree"):
                with patch("pathlib.Path.exists", mock_exists):
                    with patch("subprocess.run"):
                        dr.sync()
        assert any("zshenv.local" in str(d) for s, d in copy_calls)

    def test_zshenv_skipped_when_missing(self, dr):
        copy_calls = []

        with patch("shutil.copy2", side_effect=lambda s, d: copy_calls.append((s, d))):
            with patch("shutil.copytree"):
                with patch("pathlib.Path.exists", return_value=False):
                    with patch("subprocess.run"):
                        dr.sync()
        assert not any("zshenv" in str(s) for s, d in copy_calls)


# ── Synaxis config sync ────────────────────────────────────────────────────


class TestDRSynaxisConfig:
    def test_synaxis_config_copied(self, dr):
        copy_calls = []

        def mock_exists(self_path):
            s = str(self_path)
            return s.endswith("config.toml") and "synaxis" in s

        with patch("shutil.copy2", side_effect=lambda s, d: copy_calls.append((s, d))):
            with patch("shutil.copytree"):
                with patch("pathlib.Path.exists", mock_exists):
                    with patch("pathlib.Path.mkdir"):
                        with patch("subprocess.run"):
                            dr.sync()
        assert any("config.toml" in str(s) for s, d in copy_calls)

    def test_synaxis_creates_parent_dirs(self, dr):
        mkdir_calls = []

        def mock_exists(self_path):
            return str(self_path).endswith("config.toml") and "synaxis" in str(self_path)

        with patch("shutil.copy2"):
            with patch("shutil.copytree"):
                with patch("pathlib.Path.exists", mock_exists):
                    with patch("pathlib.Path.mkdir", side_effect=lambda **kw: mkdir_calls.append(kw)):
                        with patch("subprocess.run"):
                            dr.sync()
        # mkdir should have parents=True
        assert any(c.get("parents") is True for c in mkdir_calls)


# ── Brewfile dump ──────────────────────────────────────────────────────────


class TestDRBrewfile:
    def test_brew_bundle_dump_called(self, dr):
        with patch("shutil.copy2"):
            with patch("shutil.copytree"):
                with patch("pathlib.Path.exists", return_value=False):
                    with patch("subprocess.run") as mock_run:
                        dr.sync()
                        # Check brew bundle dump is in the calls
                        run_cmds = [c[0][0] for c in mock_run.call_args_list]
                        brew_found = any(
                            "brew" in cmd and "bundle" in cmd and "dump" in cmd
                            for cmd in run_cmds
                        )
                        assert brew_found


# ── Git commit / push logic ────────────────────────────────────────────────


class TestDRGitLogic:
    def test_no_changes_no_commit(self, dr, capsys):
        with patch("shutil.copy2"):
            with patch("shutil.copytree"):
                with patch("pathlib.Path.exists", return_value=False):
                    mock_result = MagicMock(stdout="")
                    with patch("subprocess.run", return_value=mock_result):
                        dr.sync()
        assert "no changes" in capsys.readouterr().out

    def test_changes_committed_and_pushed(self, dr, capsys):
        with patch("shutil.copy2"):
            with patch("shutil.copytree"):
                with patch("pathlib.Path.exists", return_value=False):
                    mock_status = MagicMock(stdout=" M claude-backup/settings.json\n")

                    def side_effect(*args, **kwargs):
                        cmd = args[0]
                        if "git" in cmd and "status" in cmd:
                            return mock_status
                        return MagicMock(stdout="", returncode=0)

                    with patch("subprocess.run", side_effect=side_effect):
                        dr.sync()
        assert "committed and pushed" in capsys.readouterr().out


# ── No source files at all ─────────────────────────────────────────────────


class TestDRNoSources:
    def test_no_files_to_backup(self, dr):
        with patch("shutil.copy2"):
            with patch("shutil.copytree"):
                with patch("pathlib.Path.exists", return_value=False):
                    with patch("subprocess.run") as mock_run:
                        dr.sync()
                        # brew bundle dump should still be called
                        assert mock_run.call_count >= 1
