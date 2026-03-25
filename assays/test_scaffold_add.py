"""Tests for vivesca add commands."""

from pathlib import Path

from metabolon.gastrulation.init import scaffold_project


def _make_project(tmp_path: Path) -> Path:
    """Helper: scaffold a project for testing add commands."""
    target = tmp_path / "myserver"
    scaffold_project("myserver", target=target, description="Test server")
    return target


def test_add_tool_creates_file(tmp_path):
    from metabolon.gastrulation.add import graft_tool

    project = _make_project(tmp_path)
    graft_tool(project, domain="weather", verb="fetch", description="Fetch weather data")

    tool_file = project / "src" / "myserver" / "tools" / "weather.py"
    assert tool_file.exists()

    content = tool_file.read_text()
    assert "weather_fetch" in content
    assert "Secretion" in content
    assert "ToolAnnotations" in content
    assert "class" in content  # Has a Pydantic output model


def test_add_tool_creates_test(tmp_path):
    from metabolon.gastrulation.add import graft_tool

    project = _make_project(tmp_path)
    graft_tool(project, domain="weather", verb="fetch", description="Fetch weather data")

    test_file = project / "assays" / "test_weather.py"
    assert test_file.exists()

    content = test_file.read_text()
    assert "weather_fetch" in content


def test_add_tool_read_only_flag(tmp_path):
    from metabolon.gastrulation.add import graft_tool

    project = _make_project(tmp_path)
    graft_tool(
        project, domain="weather", verb="fetch", description="Test", read_only=True
    )

    content = (project / "src" / "myserver" / "tools" / "weather.py").read_text()
    assert "readOnlyHint=True" in content


def test_add_tool_destructive_flag(tmp_path):
    from metabolon.gastrulation.add import graft_tool

    project = _make_project(tmp_path)
    graft_tool(
        project,
        domain="cache",
        verb="purge",
        description="Purge cache",
        read_only=False,
    )

    content = (project / "src" / "myserver" / "tools" / "cache.py").read_text()
    assert "readOnlyHint=False" in content


def test_add_prompt_creates_file(tmp_path):
    from metabolon.gastrulation.add import graft_prompt

    project = _make_project(tmp_path)
    graft_prompt(project, name="research", description="Research brief")

    prompt_file = project / "src" / "myserver" / "codons" / "research.py"
    assert prompt_file.exists()

    content = prompt_file.read_text()
    assert "research" in content
    assert "@prompt" in content


def test_add_resource_creates_file(tmp_path):
    from metabolon.gastrulation.add import graft_resource

    project = _make_project(tmp_path)
    graft_resource(project, name="status", description="Server status", uri_path="status")

    resource_file = project / "src" / "myserver" / "resources" / "status.py"
    assert resource_file.exists()

    content = resource_file.read_text()
    assert "myserver://status" in content
    assert "@resource" in content


def test_add_tool_detects_module_name(tmp_path):
    """Hyphenated project names should use underscore module name."""
    target = tmp_path / "my-server"
    scaffold_project("my-server", target=target, description="Test")

    from metabolon.gastrulation.add import graft_tool

    graft_tool(target, domain="weather", verb="fetch", description="Test")

    tool_file = target / "src" / "my_server" / "tools" / "weather.py"
    assert tool_file.exists()
