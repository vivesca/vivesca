from __future__ import annotations

"""Tests that every oscillator (LaunchAgent) plist points to existing binaries/scripts.

Catches path drift: when an effector is renamed/moved but its plist isn't updated.
"""


import plistlib
import re
from pathlib import Path

import pytest

OSCILLATOR_DIR = Path.home() / "epigenome" / "oscillators"
USER_HOME = str(Path.home())
# Paths under these prefixes are system-managed — assumed to exist.
SYSTEM_PREFIXES = ("/bin/", "/usr/", "/opt/", "/sbin/", "/Library/")
# Regex to extract absolute paths from shell -c strings.
# Stop at shell operators (&, |, ;, ), space) and quotes.
_PATH_RE = re.compile(rf"{re.escape(USER_HOME)}[^\s;&|\"'`)]+")


def _collect_user_paths(args: list[str]) -> list[str]:
    """Extract user-space paths that are binaries/scripts from ProgramArguments.

    Only checks direct path arguments and the first path in shell -c strings
    (the binary, not operands like log files).
    """
    paths: list[str] = []
    is_shell_c = (
        len(args) >= 3
        and args[0] in ("/bin/sh", "/bin/bash", "/bin/zsh")
        and args[1] == "-c"
    )

    for i, arg in enumerate(args):
        if any(arg.startswith(p) for p in SYSTEM_PREFIXES):
            continue
        if is_shell_c and i >= 2:
            # In shell -c strings, extract paths but only check executables,
            # not log files or other operands.
            for match in _PATH_RE.findall(arg):
                # Skip paths that look like log/data files (not executables).
                if Path(match).suffix in (".log", ".json", ".md", ".txt", ".csv"):
                    continue
                paths.append(match)
        elif arg.startswith(USER_HOME):
            paths.append(arg)
    return paths


def _collect_plists() -> list[tuple[str, Path]]:
    if not OSCILLATOR_DIR.is_dir():
        return []
    return [
        (p.stem, p) for p in sorted(OSCILLATOR_DIR.glob("*.plist"))
    ]


_PLISTS = _collect_plists()


@pytest.mark.parametrize(
    "label,plist_path",
    _PLISTS,
    ids=[label for label, _ in _PLISTS],
)
def test_plist_targets_exist(label: str, plist_path: Path) -> None:
    """Every user-space path in ProgramArguments must exist on disk."""
    with open(plist_path, "rb") as f:
        data = plistlib.load(f)

    args = data.get("ProgramArguments", [])
    assert args, f"{label}: ProgramArguments is empty"

    user_paths = _collect_user_paths(args)
    missing = []
    for raw in user_paths:
        target = Path(raw)
        if not target.exists():
            missing.append(str(target))

    assert not missing, (
        f"{label}: target(s) not found on disk:\n"
        + "\n".join(f"  {m}" for m in missing)
    )


@pytest.mark.parametrize(
    "label,plist_path",
    _PLISTS,
    ids=[label for label, _ in _PLISTS],
)
def test_plist_valid_xml(label: str, plist_path: Path) -> None:
    """Every plist must be parseable."""
    with open(plist_path, "rb") as f:
        data = plistlib.load(f)
    assert "Label" in data, f"{label}: missing Label key"
    assert "ProgramArguments" in data, f"{label}: missing ProgramArguments"
