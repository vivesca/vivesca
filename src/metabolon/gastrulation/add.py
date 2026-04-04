
"""vivesca add — add components to an existing project."""

from pathlib import Path

import click
from jinja2 import Environment, PackageLoader

_env = Environment(
    loader=PackageLoader("metabolon", "templates"),
    keep_trailing_newline=True,
)


def _detect_module(project_dir: Path) -> str:
    """Detect the Python module name from project structure."""

    src = project_dir / "src"
    if not src.exists():
        raise click.ClickException(f"No src/ directory found in {project_dir}")
    modules = [d.name for d in src.iterdir() if d.is_dir() and not d.name.startswith(".")]
    if len(modules) != 1:
        raise click.ClickException(f"Expected one module in src/, found: {modules}")
    return modules[0]


def _to_class_name(s: str) -> str:
    """Convert snake_case to PascalCase."""
    return "".join(word.capitalize() for word in s.split("_"))


def graft_tool(
    project_dir: Path,
    domain: str,
    verb: str,
    description: str,
    read_only: bool = True,
) -> Path:
    """Add a tool file and test to an existing vivesca project."""
    module = _detect_module(project_dir)
    class_name = _to_class_name(f"{domain}_{verb}")

    ctx = {
        "domain": domain,
        "verb": verb,
        "description": description,
        "class_name": class_name,
        "read_only": read_only,
        "module": module,
        "component_dir": "enzymes",
        "file_stem": domain,
        "func_name": f"{domain}_{verb}",
        "name": f"{domain}_{verb}",
        "component_type": "tool",
    }

    tool_file = project_dir / "src" / module / "enzymes" / f"{domain}.py"
    tool_file.write_text(_env.get_template("tool.py.j2").render(**ctx))

    test_file = project_dir / "assays" / f"test_{domain}.py"
    test_file.write_text(_env.get_template("test_component.py.j2").render(**ctx))

    return tool_file


def graft_prompt(
    project_dir: Path,
    name: str,
    description: str,
) -> Path:
    """Add a prompt file to an existing vivesca project."""
    module = _detect_module(project_dir)
    func_name = name.replace("-", "_")

    ctx = {
        "name": name,
        "func_name": func_name,
        "description": description,
        "module": module,
        "component_dir": "codons",
        "file_stem": name.replace("-", "_"),
        "component_type": "prompt",
    }

    prompt_file = project_dir / "src" / module / "codons" / f"{func_name}.py"
    prompt_file.write_text(_env.get_template("prompt.py.j2").render(**ctx))

    test_file = project_dir / "assays" / f"test_{func_name}.py"
    test_file.write_text(_env.get_template("test_component.py.j2").render(**ctx))

    return prompt_file


def graft_resource(
    project_dir: Path,
    name: str,
    description: str,
    uri_path: str = "",
) -> Path:
    """Add a resource file to an existing vivesca project."""
    module = _detect_module(project_dir)
    func_name = name.replace("-", "_")
    # Detect project name from pyproject.toml or use module name
    project_name = module.replace("_", "-")
    uri = f"{project_name}://{uri_path or name}"

    ctx = {
        "name": name,
        "func_name": func_name,
        "description": description,
        "uri": uri,
        "module": module,
        "component_dir": "resources",
        "file_stem": name.replace("-", "_"),
        "component_type": "resource",
    }

    resource_file = project_dir / "src" / module / "resources" / f"{func_name}.py"
    resource_file.write_text(_env.get_template("resource.py.j2").render(**ctx))

    test_file = project_dir / "assays" / f"test_{func_name}.py"
    test_file.write_text(_env.get_template("test_component.py.j2").render(**ctx))

    return resource_file
