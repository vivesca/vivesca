"""vivesca init — scaffold a new MCP server project."""
from __future__ import annotations

from typing import TYPE_CHECKING

import click
from jinja2 import Environment, PackageLoader

if TYPE_CHECKING:
    from pathlib import Path

_env = Environment(
    loader=PackageLoader("metabolon", "templates"),
    keep_trailing_newline=True,
)


def _to_module(name: str) -> str:
    """Convert project name to valid Python module name."""

    return name.replace("-", "_")


def scaffold_project(name: str, target: Path, description: str) -> Path:
    """Scaffold a complete MCP server project.

    Args:
        name: Project name (may contain hyphens).
        target: Directory to create.
        description: One-line description.

    Returns:
        Path to the created project directory.
    """
    if target.exists() and any(target.iterdir()):
        raise click.ClickException(f"Directory {target} already exists and is not empty")

    module = _to_module(name)
    ctx = {"name": name, "module": module, "description": description}

    # Create directory structure
    src = target / "src" / module
    for d in [
        src / "enzymes",
        src / "codons",
        src / "resources",
        src / "morphology",
        target / "assays",
    ]:
        d.mkdir(parents=True, exist_ok=True)

    # Create __init__.py files for packages
    for d in [src, src / "enzymes", src / "codons", src / "resources", src / "morphology"]:
        (d / "__init__.py").touch()

    # Render templates
    templates = {
        "project/pyproject.toml.j2": target / "pyproject.toml",
        "project/server.py.j2": src / "server.py",
        "project/__init__.py.j2": src / "__init__.py",
        "project/__main__.py.j2": src / "__main__.py",
        "project/test_handshake.py.j2": target / "assays" / "test_handshake.py",
    }

    for template_name, output_path in templates.items():
        template = _env.get_template(template_name)
        output_path.write_text(template.render(**ctx))

    return target
