"""Tests for vivesca check command."""

from pathlib import Path

from metabolon.gastrulation.add import add_tool_to_project
from metabolon.gastrulation.init import scaffold_project


def _make_project_with_tool(tmp_path: Path) -> Path:
    """Helper: scaffold project + add a valid tool."""
    target = tmp_path / "myserver"
    scaffold_project("myserver", target=target, description="Test server")
    add_tool_to_project(target, domain="weather", verb="fetch", description="Fetch weather")
    return target


def test_check_valid_project_passes(tmp_path):
    from metabolon.gastrulation.check import check_project

    project = _make_project_with_tool(tmp_path)
    issues = check_project(project)
    assert len(issues) == 0


def test_check_detects_missing_return_type(tmp_path):
    from metabolon.gastrulation.check import check_project

    project = _make_project_with_tool(tmp_path)
    # Break the tool: remove return type annotation
    tool_file = project / "src" / "myserver" / "tools" / "weather.py"
    content = tool_file.read_text()
    content = content.replace("-> WeatherFetchResult:", ":")
    tool_file.write_text(content)

    issues = check_project(project)
    assert any("return type" in i.lower() for i in issues)


def test_check_detects_missing_annotations(tmp_path):
    from metabolon.gastrulation.check import check_project

    project = _make_project_with_tool(tmp_path)
    # Break the tool: remove ToolAnnotations
    tool_file = project / "src" / "myserver" / "tools" / "weather.py"
    content = tool_file.read_text()
    content = content.replace("    annotations=ToolAnnotations(readOnlyHint=True),\n", "")
    tool_file.write_text(content)

    issues = check_project(project)
    assert any("annotation" in i.lower() for i in issues)


def test_check_detects_missing_description(tmp_path):
    from metabolon.gastrulation.check import check_project

    project = _make_project_with_tool(tmp_path)
    # Break the tool: remove description
    tool_file = project / "src" / "myserver" / "tools" / "weather.py"
    content = tool_file.read_text()
    content = content.replace('    description="Fetch weather",\n', "")
    tool_file.write_text(content)

    issues = check_project(project)
    assert any("description" in i.lower() for i in issues)


def test_check_validates_prompts(tmp_path):
    from metabolon.gastrulation.add import add_prompt_to_project
    from metabolon.gastrulation.check import check_project

    project = _make_project_with_tool(tmp_path)
    add_prompt_to_project(project, name="research", description="Research brief")
    issues = check_project(project)
    assert len(issues) == 0


def test_check_validates_resources(tmp_path):
    from metabolon.gastrulation.add import add_resource_to_project
    from metabolon.gastrulation.check import check_project

    project = _make_project_with_tool(tmp_path)
    add_resource_to_project(project, name="status", description="Status", uri_path="status")
    issues = check_project(project)
    assert len(issues) == 0
