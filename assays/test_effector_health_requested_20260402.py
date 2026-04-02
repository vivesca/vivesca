from __future__ import annotations

import ast
import subprocess
from pathlib import Path

import pytest


EFFECTORS_DIR = Path.home() / "germline" / "effectors"
TARGET_NAMES = [
    "rename-plists",
    "chromatin-decay-report.py",
    "test-dashboard",
    "grep",
    "rheotaxis-local",
    "methylation",
    "browser",
    "hkicpa",
    "skill-lint",
    "tmux-osc52.sh",
]


def _script_path(name: str) -> Path:
    return EFFECTORS_DIR / name


def _resolved_source_path(name: str) -> Path:
    return _script_path(name).resolve()


def _first_line(name: str) -> str:
    return _resolved_source_path(name).read_text(encoding="utf-8").splitlines()[0]


def _is_python_target(name: str) -> bool:
    shebang = _first_line(name)
    return "python" in shebang or "uv run --script" in shebang


@pytest.mark.parametrize("name", TARGET_NAMES)
def test_target_has_shebang(name: str) -> None:
    assert _first_line(name).startswith("#!"), f"{name} is missing a shebang"


@pytest.mark.parametrize(
    "name",
    [name for name in TARGET_NAMES if _is_python_target(name)],
)
def test_python_target_ast_parses(name: str) -> None:
    source = _resolved_source_path(name).read_text(encoding="utf-8")
    ast.parse(source, filename=name)


@pytest.mark.parametrize("name", TARGET_NAMES)
def test_target_help_exits_zero(name: str) -> None:
    result = subprocess.run(
        [str(_script_path(name)), "--help"],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=Path.home() / "germline",
    )

    assert result.returncode == 0, (
        f"{name} --help failed with exit={result.returncode}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
    assert result.stdout.strip() or result.stderr.strip(), f"{name} --help produced no output"
