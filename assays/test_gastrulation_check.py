from __future__ import annotations

"""Tests for metabolon/gastrulation/check.py."""


from pathlib import Path

import pytest

from metabolon.gastrulation.check import (
    _check_prompt_file,
    _check_resource_file,
    _check_tool_file,
    _detect_module,
    _has_kwarg,
    _is_decorator,
    probe_gastrulation,
)


class TestDetectModule:
    """Tests for _detect_module helper."""

    def test_detects_single_module(self, tmp_path: Path) -> None:
        """Should detect the single module in src/."""
        src = tmp_path / "src"
        (src / "my_module").mkdir(parents=True)

        result = _detect_module(tmp_path)
        assert result == "my_module"

    def test_returns_empty_on_multiple_modules(self, tmp_path: Path) -> None:
        """Should return empty string if multiple modules found."""
        src = tmp_path / "src"
        (src / "module_a").mkdir(parents=True)
        (src / "module_b").mkdir(parents=True)

        result = _detect_module(tmp_path)
        assert result == ""

    def test_ignores_dot_directories(self, tmp_path: Path) -> None:
        """Should ignore directories starting with dot."""
        src = tmp_path / "src"
        (src / "my_module").mkdir(parents=True)
        (src / ".hidden").mkdir(parents=True)

        result = _detect_module(tmp_path)
        assert result == "my_module"


class TestIsDecorator:
    """Tests for _is_decorator helper."""

    def test_simple_name_decorator(self) -> None:
        """Should match simple name decorator."""
        import ast

        tree = ast.parse("@tool\ndef foo(): pass")
        func = tree.body[0]
        decorator = func.decorator_list[0]

        assert _is_decorator(decorator, "tool") is True

    def test_call_decorator_with_name(self) -> None:
        """Should match @tool() call decorator."""
        import ast

        tree = ast.parse("@tool()\ndef foo(): pass")
        func = tree.body[0]
        decorator = func.decorator_list[0]

        assert _is_decorator(decorator, "tool") is True

    def test_call_decorator_with_attribute(self) -> None:
        """Should match @mcp.tool() attribute decorator."""
        import ast

        tree = ast.parse("@mcp.tool()\ndef foo(): pass")
        func = tree.body[0]
        decorator = func.decorator_list[0]

        assert _is_decorator(decorator, "tool") is True

    def test_wrong_name(self) -> None:
        """Should not match different decorator name."""
        import ast

        tree = ast.parse("@prompt()\ndef foo(): pass")
        func = tree.body[0]
        decorator = func.decorator_list[0]

        assert _is_decorator(decorator, "tool") is False


class TestHasKwarg:
    """Tests for _has_kwarg helper."""

    def test_has_kwarg(self) -> None:
        """Should find keyword argument in decorator."""
        import ast

        tree = ast.parse("@tool(description='test')\ndef foo(): pass")
        func = tree.body[0]

        assert _has_kwarg(func, "tool", "description") is True

    def test_missing_kwarg(self) -> None:
        """Should return False if kwarg missing."""
        import ast

        tree = ast.parse("@tool()\ndef foo(): pass")
        func = tree.body[0]

        assert _has_kwarg(func, "tool", "description") is False

    def test_wrong_decorator(self) -> None:
        """Should return False if decorator name doesn't match."""
        import ast

        tree = ast.parse("@prompt(description='test')\ndef foo(): pass")
        func = tree.body[0]

        assert _has_kwarg(func, "tool", "description") is False


class TestCheckToolFile:
    """Tests for _check_tool_file."""

    def test_valid_tool_no_issues(self, tmp_path: Path) -> None:
        """Should return no issues for valid tool."""
        code = '''
from mcp import ToolAnnotations

@tool(
    description="Get weather",
    annotations=ToolAnnotations(readOnlyHint=True)
)
def weather_get(city: str) -> dict:
    """Get weather for city."""
    return {}
'''
        tool_file = tmp_path / "weather.py"
        tool_file.write_text(code)

        issues = _check_tool_file(tool_file)
        assert issues == []

    def test_missing_return_type(self, tmp_path: Path) -> None:
        """Should detect missing return type annotation."""
        code = '''
@tool(description="Get weather", annotations=ToolAnnotations())
def weather_get(city: str):
    return {}
'''
        tool_file = tmp_path / "weather.py"
        tool_file.write_text(code)

        issues = _check_tool_file(tool_file)
        assert any("missing return type annotation" in i for i in issues)

    def test_missing_annotations_kwarg(self, tmp_path: Path) -> None:
        """Should detect missing annotations kwarg."""
        code = '''
@tool(description="Get weather")
def weather_get(city: str) -> dict:
    return {}
'''
        tool_file = tmp_path / "weather.py"
        tool_file.write_text(code)

        issues = _check_tool_file(tool_file)
        assert any("missing annotations=ToolAnnotations" in i for i in issues)

    def test_missing_description_kwarg(self, tmp_path: Path) -> None:
        """Should detect missing description kwarg."""
        code = '''
@tool(annotations=ToolAnnotations())
def weather_get(city: str) -> dict:
    return {}
'''
        tool_file = tmp_path / "weather.py"
        tool_file.write_text(code)

        issues = _check_tool_file(tool_file)
        assert any("missing description" in i for i in issues)

    def test_syntax_error(self, tmp_path: Path) -> None:
        """Should handle syntax error gracefully."""
        tool_file = tmp_path / "broken.py"
        tool_file.write_text("def broken(:\n")

        issues = _check_tool_file(tool_file)
        assert len(issues) == 1
        assert "syntax error" in issues[0]

    def test_non_tool_function_ignored(self, tmp_path: Path) -> None:
        """Should ignore functions without @tool decorator."""
        code = '''
def helper_function(x: int) -> int:
    return x * 2
'''
        tool_file = tmp_path / "helpers.py"
        tool_file.write_text(code)

        issues = _check_tool_file(tool_file)
        assert issues == []


class TestCheckPromptFile:
    """Tests for _check_prompt_file."""

    def test_valid_prompt_no_issues(self, tmp_path: Path) -> None:
        """Should return no issues for valid prompt."""
        code = '''
@prompt(description="Review code")
def code_review(code: str) -> str:
    return f"Reviewing: {code}"
'''
        prompt_file = tmp_path / "review.py"
        prompt_file.write_text(code)

        issues = _check_prompt_file(prompt_file)
        assert issues == []

    def test_missing_description(self, tmp_path: Path) -> None:
        """Should detect missing description in @prompt()."""
        code = '''
@prompt()
def code_review(code: str) -> str:
    return f"Reviewing: {code}"
'''
        prompt_file = tmp_path / "review.py"
        prompt_file.write_text(code)

        issues = _check_prompt_file(prompt_file)
        assert any("missing description" in i for i in issues)

    def test_syntax_error(self, tmp_path: Path) -> None:
        """Should handle syntax error gracefully."""
        prompt_file = tmp_path / "broken.py"
        prompt_file.write_text("@prompt(\ndef broken():")

        issues = _check_prompt_file(prompt_file)
        assert len(issues) == 1
        assert "syntax error" in issues[0]

    def test_non_prompt_function_ignored(self, tmp_path: Path) -> None:
        """Should ignore functions without @prompt decorator."""
        code = '''
def format_prompt(text: str) -> str:
    return text.strip()
'''
        prompt_file = tmp_path / "format.py"
        prompt_file.write_text(code)

        issues = _check_prompt_file(prompt_file)
        assert issues == []


class TestCheckResourceFile:
    """Tests for _check_resource_file."""

    def test_valid_resource_no_issues(self, tmp_path: Path) -> None:
        """Should return no issues for valid resource."""
        code = '''
@resource("config://settings.yaml")
def get_settings() -> str:
    return "settings"
'''
        resource_file = tmp_path / "config.py"
        resource_file.write_text(code)

        issues = _check_resource_file(resource_file)
        assert issues == []

    def test_missing_uri(self, tmp_path: Path) -> None:
        """Should detect missing URI in @resource()."""
        code = '''
@resource()
def get_settings() -> str:
    return "settings"
'''
        resource_file = tmp_path / "config.py"
        resource_file.write_text(code)

        issues = _check_resource_file(resource_file)
        assert any("missing URI" in i for i in issues)

    def test_syntax_error(self, tmp_path: Path) -> None:
        """Should handle syntax error gracefully."""
        resource_file = tmp_path / "broken.py"
        resource_file.write_text("@resource(\ndef broken():")

        issues = _check_resource_file(resource_file)
        assert len(issues) == 1
        assert "syntax error" in issues[0]

    def test_non_resource_function_ignored(self, tmp_path: Path) -> None:
        """Should ignore functions without @resource decorator."""
        code = '''
def load_file(path: str) -> bytes:
    return b"data"
'''
        resource_file = tmp_path / "loader.py"
        resource_file.write_text(code)

        issues = _check_resource_file(resource_file)
        assert issues == []


class TestProbeGastrulation:
    """Tests for probe_gastrulation main function."""

    def _setup_project(self, tmp_path: Path) -> Path:
        """Create a minimal project structure."""
        src = tmp_path / "src" / "test_module"
        (src / "enzymes").mkdir(parents=True)
        (src / "codons").mkdir(parents=True)
        (src / "resources").mkdir(parents=True)
        return tmp_path

    def test_empty_project_no_issues(self, tmp_path: Path) -> None:
        """Should return empty list for empty directories."""
        project = self._setup_project(tmp_path)

        issues = probe_gastrulation(project)
        assert issues == []

    def test_collects_issues_from_tools(self, tmp_path: Path) -> None:
        """Should collect issues from tool files."""
        project = self._setup_project(tmp_path)
        src = project / "src" / "test_module"

        # Create a tool with issues
        tool_file = src / "enzymes" / "weather.py"
        tool_file.write_text('''
@tool()
def weather_get(city: str):
    return {}
''')

        issues = probe_gastrulation(project)
        assert len(issues) > 0

    def test_collects_issues_from_prompts(self, tmp_path: Path) -> None:
        """Should collect issues from prompt files."""
        project = self._setup_project(tmp_path)
        src = project / "src" / "test_module"

        prompt_file = src / "codons" / "review.py"
        prompt_file.write_text('''
@prompt()
def review(code: str) -> str:
    return code
''')

        issues = probe_gastrulation(project)
        assert len(issues) > 0

    def test_collects_issues_from_resources(self, tmp_path: Path) -> None:
        """Should collect issues from resource files."""
        project = self._setup_project(tmp_path)
        src = project / "src" / "test_module"

        resource_file = src / "resources" / "config.py"
        resource_file.write_text('''
@resource()
def config() -> str:
    return ""
''')

        issues = probe_gastrulation(project)
        assert len(issues) > 0

    def test_skips_init_files(self, tmp_path: Path) -> None:
        """Should skip __init__.py files."""
        project = self._setup_project(tmp_path)
        src = project / "src" / "test_module"

        # Create __init__.py with "bad" code that would fail if checked
        init_file = src / "enzymes" / "__init__.py"
        init_file.write_text("bad syntax [")

        issues = probe_gastrulation(project)
        # Should not include syntax error from __init__.py
        assert not any("__init__.py" in i for i in issues)

    def test_handles_missing_directories(self, tmp_path: Path) -> None:
        """Should handle missing component directories gracefully."""
        src = tmp_path / "src" / "test_module"
        src.mkdir(parents=True)
        # No enzymes/codons/resources directories

        issues = probe_gastrulation(tmp_path)
        assert issues == []
