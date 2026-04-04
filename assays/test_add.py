"""Tests for metabolon.gastrulation.add."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import click
import pytest

from metabolon.gastrulation.add import (
    _detect_module,
    _to_class_name,
    graft_prompt,
    graft_resource,
    graft_tool,
)

# ---------------------------------------------------------------------------
# _to_class_name
# ---------------------------------------------------------------------------


class TestToClassName:
    def test_single_word(self):
        assert _to_class_name("foo") == "Foo"

    def test_multi_word(self):
        assert _to_class_name("fetch_url") == "FetchUrl"

    def test_already_capitalised(self):
        # capitalize() lowercases the rest, so "Foo" -> "Foo" is fine
        assert _to_class_name("foo_bar_baz") == "FooBarBaz"

    def test_empty_string(self):
        assert _to_class_name("") == ""


# ---------------------------------------------------------------------------
# _detect_module
# ---------------------------------------------------------------------------


class TestDetectModule:
    def test_finds_single_module(self, tmp_path: Path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "my_pkg").mkdir()
        assert _detect_module(tmp_path) == "my_pkg"

    def test_raises_when_no_src(self, tmp_path: Path):
        with pytest.raises(click.ClickException, match="No src/"):
            _detect_module(tmp_path)

    def test_raises_when_multiple_modules(self, tmp_path: Path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "alpha").mkdir()
        (src / "beta").mkdir()
        with pytest.raises(click.ClickException, match="Expected one module"):
            _detect_module(tmp_path)

    def test_ignores_hidden_dirs(self, tmp_path: Path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "real_pkg").mkdir()
        (src / ".hidden").mkdir()
        assert _detect_module(tmp_path) == "real_pkg"


# ---------------------------------------------------------------------------
# graft_tool
# ---------------------------------------------------------------------------


class TestGraftTool:
    @patch("metabolon.gastrulation.add._env")
    def test_creates_tool_and_test_files(self, mock_env: MagicMock, tmp_path: Path):
        # Set up a valid project structure
        src = tmp_path / "src"
        src.mkdir()
        (src / "mypkg").mkdir()
        (src / "mypkg" / "enzymes").mkdir()
        assays = tmp_path / "assays"
        assays.mkdir()

        mock_template = MagicMock()
        mock_template.render.return_value = "# generated tool"
        mock_env.get_template.return_value = mock_template

        result = graft_tool(tmp_path, "weather", "fetch", "Get weather", read_only=True)

        # Tool file path
        expected_tool = tmp_path / "src" / "mypkg" / "enzymes" / "weather.py"
        assert result == expected_tool
        assert expected_tool.exists()
        mock_env.get_template.assert_any_call("tool.py.j2")
        assert mock_template.render.call_count == 2  # tool template + test template
        ctx = mock_template.render.call_args.kwargs
        assert ctx["class_name"] == "WeatherFetch"

    @patch("metabolon.gastrulation.add._env")
    def test_class_name_construction(self, mock_env: MagicMock, tmp_path: Path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "pkg").mkdir()
        (src / "pkg" / "enzymes").mkdir()
        assays = tmp_path / "assays"
        assays.mkdir()

        mock_template = MagicMock()
        mock_template.render.return_value = ""
        mock_env.get_template.return_value = mock_template

        graft_tool(tmp_path, "data_store", "sync", "Sync data")

        call_kwargs = mock_template.render.call_args.kwargs
        assert call_kwargs["class_name"] == "DataStoreSync"
        assert call_kwargs["func_name"] == "data_store_sync"


# ---------------------------------------------------------------------------
# graft_prompt
# ---------------------------------------------------------------------------


class TestGraftPrompt:
    @patch("metabolon.gastrulation.add._env")
    def test_creates_prompt_and_test(self, mock_env: MagicMock, tmp_path: Path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "mypkg").mkdir()
        (src / "mypkg" / "codons").mkdir()
        assays = tmp_path / "assays"
        assays.mkdir()

        mock_template = MagicMock()
        mock_template.render.return_value = "# generated prompt"
        mock_env.get_template.return_value = mock_template

        result = graft_prompt(tmp_path, "my-prompt", "A test prompt")

        expected = tmp_path / "src" / "mypkg" / "codons" / "my_prompt.py"
        assert result == expected
        assert expected.exists()
        mock_env.get_template.assert_any_call("prompt.py.j2")

    @patch("metabolon.gastrulation.add._env")
    def test_hyphen_to_underscore(self, mock_env: MagicMock, tmp_path: Path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "pkg").mkdir()
        (src / "pkg" / "codons").mkdir()
        assays = tmp_path / "assays"
        assays.mkdir()

        mock_template = MagicMock()
        mock_template.render.return_value = ""
        mock_env.get_template.return_value = mock_template

        graft_prompt(tmp_path, "summarise-text", "Summarise")

        call_kwargs = mock_template.render.call_args.kwargs
        assert call_kwargs["func_name"] == "summarise_text"
        assert call_kwargs["component_dir"] == "codons"


# ---------------------------------------------------------------------------
# graft_resource
# ---------------------------------------------------------------------------


class TestGraftResource:
    @patch("metabolon.gastrulation.add._env")
    def test_creates_resource_file(self, mock_env: MagicMock, tmp_path: Path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "my_app").mkdir()
        (src / "my_app" / "resources").mkdir()
        assays = tmp_path / "assays"
        assays.mkdir()

        mock_template = MagicMock()
        mock_template.render.return_value = "# generated resource"
        mock_env.get_template.return_value = mock_template

        result = graft_resource(tmp_path, "user", "User resource", uri_path="users")

        expected = tmp_path / "src" / "my_app" / "resources" / "user.py"
        assert result == expected
        assert expected.exists()
        mock_env.get_template.assert_any_call("resource.py.j2")

    @patch("metabolon.gastrulation.add._env")
    def test_uri_construction_with_path(self, mock_env: MagicMock, tmp_path: Path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "cool_proj").mkdir()
        (src / "cool_proj" / "resources").mkdir()
        assays = tmp_path / "assays"
        assays.mkdir()

        mock_template = MagicMock()
        mock_template.render.return_value = ""
        mock_env.get_template.return_value = mock_template

        graft_resource(tmp_path, "items", "Items resource", uri_path="v1/items")

        call_kwargs = mock_template.render.call_args.kwargs
        assert call_kwargs["uri"] == "cool-proj://v1/items"

    @patch("metabolon.gastrulation.add._env")
    def test_uri_construction_default(self, mock_env: MagicMock, tmp_path: Path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "my_proj").mkdir()
        (src / "my_proj" / "resources").mkdir()
        assays = tmp_path / "assays"
        assays.mkdir()

        mock_template = MagicMock()
        mock_template.render.return_value = ""
        mock_env.get_template.return_value = mock_template

        graft_resource(tmp_path, "config", "Config resource")

        call_kwargs = mock_template.render.call_args.kwargs
        # Default uri_path="" means uri = "my-proj://config"
        assert call_kwargs["uri"] == "my-proj://config"
