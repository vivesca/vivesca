from __future__ import annotations

"""Tests for vivesca check command."""


from typing import TYPE_CHECKING

from metabolon.gastrulation.add import graft_tool
from metabolon.gastrulation.init import scaffold_project

if TYPE_CHECKING:
    from pathlib import Path


def _make_project_with_tool(tmp_path: Path) -> Path:
    """Helper: scaffold project + add a valid tool."""

    target = tmp_path / "myserver"
    scaffold_project("myserver", target=target, description="Test server")
    graft_tool(target, domain="weather", verb="fetch", description="Fetch weather")
    return target


def test_check_valid_project_passes(tmp_path):
    from metabolon.gastrulation.check import probe_gastrulation

    project = _make_project_with_tool(tmp_path)
    issues = probe_gastrulation(project)
    assert len(issues) == 0


def test_check_detects_missing_return_type(tmp_path):
    from metabolon.gastrulation.check import probe_gastrulation

    project = _make_project_with_tool(tmp_path)
    # Break the tool: remove return type annotation
    tool_file = project / "src" / "myserver" / "enzymes" / "weather.py"
    content = tool_file.read_text()
    content = content.replace("-> WeatherFetchResult:", ":")
    tool_file.write_text(content)

    issues = probe_gastrulation(project)
    assert any("return type" in i.lower() for i in issues)


def test_check_detects_missing_annotations(tmp_path):
    from metabolon.gastrulation.check import probe_gastrulation

    project = _make_project_with_tool(tmp_path)
    # Break the tool: remove ToolAnnotations
    tool_file = project / "src" / "myserver" / "enzymes" / "weather.py"
    content = tool_file.read_text()
    content = content.replace("    annotations=ToolAnnotations(readOnlyHint=True),\n", "")
    tool_file.write_text(content)

    issues = probe_gastrulation(project)
    assert any("annotation" in i.lower() for i in issues)


def test_check_detects_missing_description(tmp_path):
    from metabolon.gastrulation.check import probe_gastrulation

    project = _make_project_with_tool(tmp_path)
    # Break the tool: remove description
    tool_file = project / "src" / "myserver" / "enzymes" / "weather.py"
    content = tool_file.read_text()
    content = content.replace('    description="Fetch weather",\n', "")
    tool_file.write_text(content)

    issues = probe_gastrulation(project)
    assert any("description" in i.lower() for i in issues)


def test_check_validates_prompts(tmp_path):
    from metabolon.gastrulation.add import graft_prompt
    from metabolon.gastrulation.check import probe_gastrulation

    project = _make_project_with_tool(tmp_path)
    graft_prompt(project, name="research", description="Research brief")
    issues = probe_gastrulation(project)
    assert len(issues) == 0


def test_check_validates_resources(tmp_path):
    from metabolon.gastrulation.add import graft_resource
    from metabolon.gastrulation.check import probe_gastrulation

    project = _make_project_with_tool(tmp_path)
    graft_resource(project, name="status", description="Status", uri_path="status")
    issues = probe_gastrulation(project)
    assert len(issues) == 0
