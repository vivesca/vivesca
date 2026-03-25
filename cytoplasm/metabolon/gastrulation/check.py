"""vivesca check — validate a project against vivesca conventions.

Uses AST analysis to check:
- Tools: return type annotations, ToolAnnotations, description
- Prompts: description in @prompt() decorator
- Resources: URI in @resource() decorator
"""

import ast
from pathlib import Path


def check_project(project_dir: Path) -> list[str]:
    """Check a vivesca project for convention violations.

    Returns a list of issue descriptions. Empty list = all good.
    """
    issues: list[str] = []
    module = _detect_module(project_dir)

    # Check tools
    tools_dir = project_dir / "src" / module / "tools"
    if tools_dir.exists():
        for py_file in sorted(tools_dir.glob("*.py")):
            if py_file.name == "__init__.py":
                continue
            issues.extend(_check_tool_file(py_file))

    # Check codons (prompts)
    prompts_dir = project_dir / "src" / module / "codons"
    if prompts_dir.exists():
        for py_file in sorted(prompts_dir.glob("*.py")):
            if py_file.name == "__init__.py":
                continue
            issues.extend(_check_prompt_file(py_file))

    # Check resources
    resources_dir = project_dir / "src" / module / "resources"
    if resources_dir.exists():
        for py_file in sorted(resources_dir.glob("*.py")):
            if py_file.name == "__init__.py":
                continue
            issues.extend(_check_resource_file(py_file))

    return issues


def _detect_module(project_dir: Path) -> str:
    """Detect the Python module name from project structure."""
    src = project_dir / "src"
    modules = [d.name for d in src.iterdir() if d.is_dir() and not d.name.startswith(".")]
    if len(modules) != 1:
        return ""
    return modules[0]


def _is_decorator(decorator: ast.expr, name: str) -> bool:
    """Check if a decorator matches a given name."""
    if isinstance(decorator, ast.Call):
        func = decorator.func
        if isinstance(func, ast.Name) and func.id == name:
            return True
        if isinstance(func, ast.Attribute) and func.attr == name:
            return True
    return bool(isinstance(decorator, ast.Name) and decorator.id == name)


def _has_kwarg(node: ast.FunctionDef, decorator_name: str, kwarg_name: str) -> bool:
    """Check if a decorator has a specific keyword argument."""
    for d in node.decorator_list:
        if isinstance(d, ast.Call) and _is_decorator(d, decorator_name):
            return any(kw.arg == kwarg_name for kw in d.keywords)
    return False


def _check_tool_file(path: Path) -> list[str]:
    """Check a single tool file for convention violations."""
    issues: list[str] = []
    rel = path.name

    try:
        tree = ast.parse(path.read_text())
    except SyntaxError as e:
        return [f"{rel}: syntax error — {e}"]

    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue

        is_tool = any(_is_decorator(d, "tool") for d in node.decorator_list)
        if not is_tool:
            continue

        func_name = node.name

        if node.returns is None:
            issues.append(
                f"{rel}: {func_name} — missing return type annotation (required for outputSchema)"
            )

        if not _has_kwarg(node, "tool", "annotations"):
            issues.append(
                f"{rel}: {func_name} — missing annotations=ToolAnnotations(...) (required for client hints)"
            )

        if not _has_kwarg(node, "tool", "description"):
            issues.append(
                f"{rel}: {func_name} — missing description (required for discoverability)"
            )

    return issues


def _check_prompt_file(path: Path) -> list[str]:
    """Check a prompt file for convention violations."""
    issues: list[str] = []
    rel = path.name

    try:
        tree = ast.parse(path.read_text())
    except SyntaxError as e:
        return [f"{rel}: syntax error — {e}"]

    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        is_prompt = any(_is_decorator(d, "prompt") for d in node.decorator_list)
        if not is_prompt:
            continue

        if not _has_kwarg(node, "prompt", "description"):
            issues.append(
                f"{rel}: {node.name} — missing description in @prompt() (required for discoverability)"
            )

    return issues


def _check_resource_file(path: Path) -> list[str]:
    """Check a resource file for convention violations."""
    issues: list[str] = []
    rel = path.name

    try:
        tree = ast.parse(path.read_text())
    except SyntaxError as e:
        return [f"{rel}: syntax error — {e}"]

    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        is_resource = any(_is_decorator(d, "resource") for d in node.decorator_list)
        if not is_resource:
            continue

        has_uri = False
        for d in node.decorator_list:
            if isinstance(d, ast.Call) and _is_decorator(d, "resource"):
                has_uri = len(d.args) > 0
        if not has_uri:
            issues.append(
                f"{rel}: {node.name} — missing URI in @resource() (required for discovery)"
            )

    return issues
