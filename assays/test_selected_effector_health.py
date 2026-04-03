from __future__ import annotations

import ast
import os
import stat
import subprocess
import tempfile
from pathlib import Path

import pytest


EFFECTORS_DIR = Path.home() / "germline" / "effectors"
TARGET_NAMES = [
    "commensal",
    "golem-dash",
    "chat_history.py",
    "goose-worker",
    "evident-brief",
    "regulatory-capture",
    "demethylase",
    "soma-clean",
    "tm",
    "paracrine",
]


def _script_path(name: str) -> Path:
    return EFFECTORS_DIR / name


@pytest.mark.parametrize("name", TARGET_NAMES)
def test_target_has_shebang(name: str) -> None:
    first_line = _script_path(name).read_text(encoding="utf-8").splitlines()[0]
    assert first_line.startswith("#!"), f"{name} is missing a shebang"


@pytest.mark.parametrize("name", [tool for tool in TARGET_NAMES if tool != "tm"])
def test_python_target_ast_parses(name: str) -> None:
    source = _script_path(name).read_text(encoding="utf-8")
    ast.parse(source, filename=name)


def _tmux_mock_dir(base_dir: Path) -> Path:
    bindir = base_dir / "bin"
    bindir.mkdir()
    tmux_path = bindir / "tmux"
    tmux_path.write_text(
        "#!/usr/bin/env bash\n"
        "if [ \"$1\" = \"list-sessions\" ]; then\n"
        "  echo \"main: 1 windows (created Thu Apr  2 12:00:00 2026)\"\n"
        "  exit 0\n"
        "fi\n"
        "exit 0\n",
        encoding="utf-8",
    )
    tmux_path.chmod(tmux_path.stat().st_mode | stat.S_IXUSR)
    return bindir


@pytest.mark.parametrize("name", TARGET_NAMES)
def test_target_help_exits_zero(name: str) -> None:
    env = os.environ.copy()
    with tempfile.TemporaryDirectory(dir=Path.home() / "germline") as temp_dir:
        if name == "tm":
            env["PATH"] = f"{_tmux_mock_dir(Path(temp_dir))}:{env['PATH']}"

        result = subprocess.run(
            [str(_script_path(name)), "--help"],
            capture_output=True,
            text=True,
            timeout=20,
            env=env,
            cwd=Path.home() / "germline",
        )

    assert result.returncode == 0, (
        f"{name} --help failed with exit={result.returncode}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
    assert result.stdout.strip() or result.stderr.strip(), f"{name} --help produced no output"
