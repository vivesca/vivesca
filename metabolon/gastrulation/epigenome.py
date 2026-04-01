from __future__ import annotations

"""vivesca epigenome — scaffold a new epigenome (instance repo).

The genome encodes structure; the epigenome expresses it.
This command lays down the chromatin scaffold for a new instance:
credentials, config, constitution, and automation hooks.
"""


import subprocess
from pathlib import Path

import click

# Template root within the metabolon package.
_TEMPLATE_ROOT = Path(__file__).resolve().parent.parent / "templates" / "epigenome"


def scaffold_epigenome(target: Path) -> Path:
    """Lay down the epigenome scaffold at *target*.

    Creates the full directory structure, copies template files,
    and initialises a git repo with an initial commit.

    Args:
        target: Directory to create (must not exist or be empty).

    Returns:
        Path to the created epigenome directory.

    Raises:
        click.ClickException: If the target already exists and is non-empty.
    """
    # Guard: refuse to overwrite non-empty directories — protect existing chromatin.
    if target.exists() and any(target.iterdir()):
        raise click.ClickException(f"Directory {target} already exists and is not empty")

    # Lay down the organelle compartments.
    for subdir in ["credentials", "config", "launchd"]:
        (target / subdir).mkdir(parents=True, exist_ok=True)

    # Transcribe template files into the new epigenome.
    _transcribe_templates(target)

    # Initialise as a git repo — seal the founding phenotype.
    _initialise_genome_repo(target)

    return target


def _transcribe_templates(target: Path) -> None:
    """Copy template files from the package into the new epigenome.

    Each file is a default phenotype expression — the instance overrides as needed.
    """
    template_files = [
        # Credentials compartment: keys and tokens (gitignored, never committed)
        ("credentials/.env.template", "credentials/.env.template"),
        # Config compartment: server and instance identity
        ("config/server.yaml", "config/server.yaml"),
        ("config/config.yaml", "config/config.yaml"),
        # Launchd: automation scaffold with usage guide
        ("launchd/README.md", "launchd/README.md"),
        # Nucleus: constitution and repo metadata
        ("genome.md", "genome.md"),
        (".gitignore", ".gitignore"),
        ("README.md", "README.md"),
    ]

    for src_rel, dst_rel in template_files:
        src = _TEMPLATE_ROOT / src_rel
        dst = target / dst_rel

        # Ensure parent directory exists (handles nested paths).
        dst.parent.mkdir(parents=True, exist_ok=True)

        if src.exists():
            dst.write_bytes(src.read_bytes())
        else:
            # Missing template: emit empty file rather than failing silently.
            dst.touch()


def _initialise_genome_repo(target: Path) -> None:
    """Initialise a git repo and seal the founding epigenome commit.

    Silently skips if git is unavailable — the scaffold is still usable.
    """
    try:
        subprocess.run(
            ["git", "init"],
            cwd=target,
            check=True,
            capture_output=True,
        timeout=300,
        )
        subprocess.run(
            ["git", "add", "."],
            cwd=target,
            check=True,
            capture_output=True,
        timeout=300,
        )
        subprocess.run(
            ["git", "commit", "-m", "chore: initialise epigenome scaffold"],
            cwd=target,
            check=True,
            capture_output=True,
        timeout=300,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        # git unavailable or failed — epigenome files are still written.
        pass
