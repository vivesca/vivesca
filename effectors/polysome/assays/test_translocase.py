"""Tests for translocase _detect_repo helper."""
from __future__ import annotations

import sys
import importlib.util
from pathlib import Path
from unittest import mock

# Load translocase module (no side-effects at module level)
spec = importlib.util.spec_from_file_location(
    "translocase_module",
    "/home/vivesca/germline/effectors/polysome/translocase.py",
)
translocase = importlib.util.module_from_spec(spec)
sys.modules["polysome.translocase"] = translocase
sys.modules["effectors.polysome.translocase"] = translocase
spec.loader.exec_module(translocase)

_detect_repo = translocase._detect_repo


# -------------------------------------------------------------------
# Standalone expanduser mock — detects tilde from str(), expands with
# the controlled HOME.  Bound-method calls from patched Path objects
# pass the Path instance as the first positional argument.
# -------------------------------------------------------------------
_HOME = "/home/terry"


def _expanduser_mock(self_path: Path) -> Path:
    """Expand ~ in a Path by inspecting its string representation."""
    s = str(self_path)
    if s.startswith("~/"):
        return Path(_HOME) / s[2:]
    return self_path


class TestDetectRepo:
    """Unit tests for _detect_repo(task, default) -> str."""

    HOME = "/home/terry"

    def _call(self, task: str) -> str:
        default = f"{self.HOME}/germline"
        return _detect_repo(task, default)

    def test_code_path_mtor(self):
        """task='Build X in ~/code/mtor' with .git present → ~/code/mtor."""
        mtor_git = Path(f"{self.HOME}/code/mtor/.git")

        def is_dir_side_effect(self_path: Path) -> bool:
            return self_path == mtor_git

        # Pass the unbound function — bound-method invocation passes Path as first arg
        with mock.patch.object(Path, "expanduser", _expanduser_mock):
            with mock.patch.object(Path, "is_dir", is_dir_side_effect):
                result = self._call("Build X in ~/code/mtor")

        assert result == f"{self.HOME}/code/mtor"

    def test_nested_path_cli_py(self):
        """task='Fix ~/code/mtor/mtor/cli.py' walks up → ~/code/mtor."""
        mtor_root = Path(f"{self.HOME}/code/mtor")
        mtor_git = mtor_root / ".git"
        cli_parents = [
            Path(f"{self.HOME}/code/mtor/mtor"),
            mtor_root,
            Path(f"{self.HOME}/code"),
            Path(self.HOME),
        ]

        def is_dir_side_effect(self_path: Path) -> bool:
            return self_path == mtor_git

        with mock.patch.object(Path, "expanduser", _expanduser_mock):
            with mock.patch.object(Path, "is_dir", is_dir_side_effect):
                with mock.patch.object(Path, "parents", cli_parents):
                    result = self._call("Fix ~/code/mtor/mtor/cli.py")

        assert result == str(mtor_root)

    def test_no_match_stays_germline(self):
        """task with no ~/code/ path → default ~/germline returned."""
        with mock.patch.object(Path, "expanduser", _expanduser_mock):
            with mock.patch.object(Path, "is_dir", return_value=False):
                result = self._call("Do something in the current repo")

        assert result == f"{self.HOME}/germline"

    def test_no_git_stays_germline(self):
        """task has ~/code/foo but no .git in path tree → default returned."""
        foo_parents = [Path(f"{self.HOME}/code"), Path(self.HOME)]

        with mock.patch.object(Path, "expanduser", _expanduser_mock):
            with mock.patch.object(Path, "is_dir", return_value=False):
                with mock.patch.object(Path, "parents", foo_parents):
                    result = self._call("Edit ~/code/foo/src/main.py")

        assert result == f"{self.HOME}/germline"
