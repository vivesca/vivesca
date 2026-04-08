#!/usr/bin/env python3
"""Reserve PyPI names for vivesca organism. Run via cron until all grabbed."""

import subprocess
import sys
import tempfile
from pathlib import Path

NAMES = [
    # Rate-limited from 2026-04-07
    "topoisomerase",
    "telomerase",
    "polymerase",
    "peroxisome",
    "lysosome",
    "endosome",
    "nucleolus",
    # CLI tools
    "allelopathy",
    # Extra bio names worth holding
    "connexin",
    "cadherin",
    "selectin",
    "ontogenesis",
    "organogenesis",
    "telophase",
    "anaphase",
    "anticodon",
    "heterochromatin",
    "euchromatin",
]


def reserve(name: str, token: str) -> bool:
    with tempfile.TemporaryDirectory() as tmpdir:
        pkg = Path(tmpdir) / name
        pkg.mkdir()
        (pkg / "__init__.py").write_text(
            f'"""{name} — reserved for vivesca organism."""\n__version__ = "0.0.1"\n'
        )
        (Path(tmpdir) / "pyproject.toml").write_text(
            f'[build-system]\nbuild-backend = "hatchling.build"\nrequires = ["hatchling"]\n\n'
            f'[project]\nname = "{name}"\nversion = "0.0.1"\n'
            f'description = "Reserved — vivesca organism component"\nlicense = "MIT"\n'
            f'requires-python = ">=3.11"\n\n[tool.hatch.build.targets.wheel]\npackages = ["{name}"]\n'
        )
        build = subprocess.run(["uv", "build"], cwd=tmpdir, capture_output=True)
        if build.returncode != 0:
            return False
        pub = subprocess.run(
            ["uv", "publish", "--token", token, *Path(tmpdir, "dist").glob("*")],
            capture_output=True,
            text=True,
        )
        return pub.returncode == 0


def main():
    token_proc = subprocess.run(
        [
            "op",
            "item",
            "get",
            "pypi-token",
            "--vault",
            "Agents",
            "--fields",
            "credential",
            "--reveal",
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if token_proc.returncode != 0:
        print("Cannot get PyPI token", file=sys.stderr)
        sys.exit(1)
    token = token_proc.stdout.strip()

    remaining = []
    for name in NAMES:
        if reserve(name, token):
            print(f"✓ {name}")
        else:
            remaining.append(name)
            print(f"✗ {name}")

    if not remaining:
        print("\nAll reserved. Remove cron job.")
    else:
        print(f"\n{len(remaining)} remaining: {', '.join(remaining)}")


if __name__ == "__main__":
    main()
