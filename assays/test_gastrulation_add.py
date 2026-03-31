from __future__ import annotations
"""Tests for metabolon/gastrulation/add.py."""


from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.gastrulation.add import (
    _detect_module,
    _to_class_name,
    graft_prompt,
    graft_resource,
    graft_tool,
)


class TestDetectModule:
    """Tests for _detect_module helper."""

    def test_detects_single_module(self, tmp_path: Path) -> None:
        """Should detect the single module in src/."""
        src = tmp_path / "src"
        (src / "my_module").mkdir(parents=True)

        result = _detect_module(tmp_path)
        assert result == "my_module"

    def test_raises_on_no_src(self, tmp_path: Path) -> None:
        """Should raise if no src/ directory exists."""
        import click

        with pytest.raises(click.ClickException, match="No src/ directory"):
            _detect_module(tmp_path)

    def test_raises_on_multiple_modules(self, tmp_path: Path) -> None:
        """Should raise if multiple modules found."""
        import click

        src = tmp_path / "src"
        (src / "module_a").mkdir(parents=True)
        (src / "module_b").mkdir(parents=True)

        with pytest.raises(click.ClickException, match="Expected one module"):
            _detect_module(tmp_path)

    def test_ignores_dot_directories(self, tmp_path: Path) -> None:
        """Should ignore directories starting with dot."""
        src = tmp_path / "src"
        (src / "my_module").mkdir(parents=True)
        (src / ".hidden").mkdir(parents=True)

        result = _detect_module(tmp_path)
        assert result == "my_module"


class TestToClassName:
    """Tests for _to_class_name helper."""

    def test_simple_snake_case(self) -> None:
        """Should convert snake_case to PascalCase."""
        assert _to_class_name("hello_world") == "HelloWorld"

    def test_single_word(self) -> None:
        """Should capitalize single word."""
        assert _to_class_name("hello") == "Hello"

    def test_multiple_underscores(self) -> None:
        """Should handle multiple underscores."""
        assert _to_class_name("foo_bar_baz") == "FooBarBaz"

    def test_domain_verb_pattern(self) -> None:
        """Should handle domain_verb pattern."""
        assert _to_class_name("weather_get") == "WeatherGet"


class TestGraftTool:
    """Tests for graft_tool function."""

    def _setup_project(self, tmp_path: Path) -> Path:
        """Create a minimal project structure."""
        src = tmp_path / "src" / "test_module"
        (src / "enzymes").mkdir(parents=True)
        (tmp_path / "assays").mkdir()
        return tmp_path

    def test_graft_tool_creates_files(self, tmp_path: Path) -> None:
        """Should create tool and test files."""
        project = self._setup_project(tmp_path)

        with patch("metabolon.gastrulation.add._env") as mock_env:
            mock_env.get_template.return_value.render.return_value = "# generated"

            result = graft_tool(
                project_dir=project,
                domain="weather",
                verb="get",
                description="Get weather data",
            )

        assert result == project / "src" / "test_module" / "enzymes" / "weather.py"
        assert result.exists()

        test_file = project / "assays" / "test_weather.py"
        assert test_file.exists()

    def test_graft_tool_uses_templates(self, tmp_path: Path) -> None:
        """Should call correct templates with context."""
        project = self._setup_project(tmp_path)

        with patch("metabolon.gastrulation.add._env") as mock_env:
            mock_template = MagicMock()
            mock_template.render.return_value = "# generated"
            mock_env.get_template.return_value = mock_template

            graft_tool(
                project_dir=project,
                domain="stock",
                verb="price",
                description="Get stock price",
                read_only=False,
            )

        # Check template calls
        calls = mock_env.get_template.call_args_list
        template_names = [c[0][0] for c in calls]
        assert "tool.py.j2" in template_names
        assert "test_component.py.j2" in template_names

        # Check render context
        render_calls = mock_template.render.call_args_list
        assert len(render_calls) == 2  # tool + test
        ctx = render_calls[0][1] if render_calls[0][1] else render_calls[0][0][0]
        assert ctx["domain"] == "stock"
        assert ctx["verb"] == "price"
        assert ctx["read_only"] is False

    def test_graft_tool_class_name(self, tmp_path: Path) -> None:
        """Should generate correct class name from domain_verb."""
        project = self._setup_project(tmp_path)

        with patch("metabolon.gastrulation.add._env") as mock_env:
            mock_template = MagicMock()
            mock_template.render.return_value = "# generated"
            mock_env.get_template.return_value = mock_template

            graft_tool(
                project_dir=project,
                domain="user",
                verb="create",
                description="Create a user",
            )

        ctx = mock_template.render.call_args[1] or mock_template.render.call_args[0][0]
        assert ctx["class_name"] == "UserCreate"


class TestGraftPrompt:
    """Tests for graft_prompt function."""

    def _setup_project(self, tmp_path: Path) -> Path:
        """Create a minimal project structure."""
        src = tmp_path / "src" / "test_module"
        (src / "codons").mkdir(parents=True)
        (tmp_path / "assays").mkdir()
        return tmp_path

    def test_graft_prompt_creates_files(self, tmp_path: Path) -> None:
        """Should create prompt and test files."""
        project = self._setup_project(tmp_path)

        with patch("metabolon.gastrulation.add._env") as mock_env:
            mock_env.get_template.return_value.render.return_value = "# generated"

            result = graft_prompt(
                project_dir=project,
                name="code-review",
                description="Review code for issues",
            )

        assert result == project / "src" / "test_module" / "codons" / "code_review.py"
        assert result.exists()

        test_file = project / "assays" / "test_code_review.py"
        assert test_file.exists()

    def test_graft_prompt_converts_name(self, tmp_path: Path) -> None:
        """Should convert hyphenated name to snake_case function name."""
        project = self._setup_project(tmp_path)

        with patch("metabolon.gastrulation.add._env") as mock_env:
            mock_template = MagicMock()
            mock_template.render.return_value = "# generated"
            mock_env.get_template.return_value = mock_template

            graft_prompt(
                project_dir=project,
                name="explain-code",
                description="Explain what code does",
            )

        ctx = mock_template.render.call_args[1] or mock_template.render.call_args[0][0]
        assert ctx["func_name"] == "explain_code"

    def test_graft_prompt_context_values(self, tmp_path: Path) -> None:
        """Should pass correct context to template."""
        project = self._setup_project(tmp_path)

        with patch("metabolon.gastrulation.add._env") as mock_env:
            mock_template = MagicMock()
            mock_template.render.return_value = "# generated"
            mock_env.get_template.return_value = mock_template

            graft_prompt(
                project_dir=project,
                name="summarize",
                description="Summarize text",
            )

        ctx = mock_template.render.call_args[1] or mock_template.render.call_args[0][0]
        assert ctx["name"] == "summarize"
        assert ctx["component_type"] == "prompt"
        assert ctx["component_dir"] == "codons"


class TestGraftResource:
    """Tests for graft_resource function."""

    def _setup_project(self, tmp_path: Path) -> Path:
        """Create a minimal project structure."""
        src = tmp_path / "src" / "test_module"
        (src / "resources").mkdir(parents=True)
        (tmp_path / "assays").mkdir()
        return tmp_path

    def test_graft_resource_creates_files(self, tmp_path: Path) -> None:
        """Should create resource and test files."""
        project = self._setup_project(tmp_path)

        with patch("metabolon.gastrulation.add._env") as mock_env:
            mock_env.get_template.return_value.render.return_value = "# generated"

            result = graft_resource(
                project_dir=project,
                name="docs",
                description="Documentation files",
            )

        assert result == project / "src" / "test_module" / "resources" / "docs.py"
        assert result.exists()

        test_file = project / "assays" / "test_docs.py"
        assert test_file.exists()

    def test_graft_resource_uri_generation(self, tmp_path: Path) -> None:
        """Should generate URI from project name and resource name."""
        project = self._setup_project(tmp_path)

        with patch("metabolon.gastrulation.add._env") as mock_env:
            mock_template = MagicMock()
            mock_template.render.return_value = "# generated"
            mock_env.get_template.return_value = mock_template

            graft_resource(
                project_dir=project,
                name="config",
                description="Config files",
                uri_path="settings.yaml",
            )

        ctx = mock_template.render.call_args[1] or mock_template.render.call_args[0][0]
        # Module is test_module, so URI should be test-module://settings.yaml
        assert ctx["uri"] == "test-module://settings.yaml"

    def test_graft_resource_uri_defaults_to_name(self, tmp_path: Path) -> None:
        """Should use resource name in URI if no uri_path provided."""
        project = self._setup_project(tmp_path)

        with patch("metabolon.gastrulation.add._env") as mock_env:
            mock_template = MagicMock()
            mock_template.render.return_value = "# generated"
            mock_env.get_template.return_value = mock_template

            graft_resource(
                project_dir=project,
                name="logs",
                description="Log files",
            )

        ctx = mock_template.render.call_args[1] or mock_template.render.call_args[0][0]
        assert ctx["uri"] == "test-module://logs"

    def test_graft_resource_context_values(self, tmp_path: Path) -> None:
        """Should pass correct context to template."""
        project = self._setup_project(tmp_path)

        with patch("metabolon.gastrulation.add._env") as mock_env:
            mock_template = MagicMock()
            mock_template.render.return_value = "# generated"
            mock_env.get_template.return_value = mock_template

            graft_resource(
                project_dir=project,
                name="data-files",
                description="Data files",
            )

        ctx = mock_template.render.call_args[1] or mock_template.render.call_args[0][0]
        assert ctx["func_name"] == "data_files"
        assert ctx["component_type"] == "resource"
        assert ctx["component_dir"] == "resources"
