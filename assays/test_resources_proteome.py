from __future__ import annotations

"""Tests for metabolon.resources.proteome — mock-based."""


from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _mock_file(name: str, *, is_file: bool = True) -> MagicMock:
    """Create a sortable MagicMock(Path) with a given name."""
    m = MagicMock(spec=Path)
    m.name = name
    m.is_file.return_value = is_file
    m.__lt__ = lambda self, other: self.name < other.name
    return m


# ---------------------------------------------------------------------------
# _scan_effector_dir
# ---------------------------------------------------------------------------


class TestScanEffectorDir:
    """Test _scan_effector_dir with mocked filesystem."""

    @patch("metabolon.resources.proteome.os.access", return_value=True)
    def test_returns_executable_files(self, mock_access: MagicMock) -> None:
        from metabolon.resources.proteome import _scan_effector_dir

        f1 = _mock_file("lysin")
        f2 = _mock_file("sortase")

        bin_dir = MagicMock(spec=Path)
        bin_dir.exists.return_value = True
        bin_dir.iterdir.return_value = [f1, f2]

        result = _scan_effector_dir(bin_dir)
        assert len(result) == 2
        assert result[0]["name"] == "lysin"
        assert result[0]["type"] == "cli"
        assert result[1]["name"] == "sortase"
        assert all("vivesca/effectors/" in e["source"] for e in result)

    def test_nonexistent_dir_returns_empty(self) -> None:
        from metabolon.resources.proteome import _scan_effector_dir

        d = MagicMock(spec=Path)
        d.exists.return_value = False
        assert _scan_effector_dir(d) == []

    @patch("metabolon.resources.proteome.os.access", return_value=False)
    def test_skips_non_executable(self, mock_access: MagicMock) -> None:
        from metabolon.resources.proteome import _scan_effector_dir

        f = _mock_file("dormant")

        bin_dir = MagicMock(spec=Path)
        bin_dir.exists.return_value = True
        bin_dir.iterdir.return_value = [f]

        assert _scan_effector_dir(bin_dir) == []

    @patch("metabolon.resources.proteome.os.access", return_value=True)
    def test_skips_dotfiles_and_dirs(self, mock_access: MagicMock) -> None:
        from metabolon.resources.proteome import _scan_effector_dir

        hidden = _mock_file(".hidden")
        underscore = _mock_file("_private")
        subdir = _mock_file("subdir", is_file=False)

        bin_dir = MagicMock(spec=Path)
        bin_dir.exists.return_value = True
        bin_dir.iterdir.return_value = [hidden, underscore, subdir]

        assert _scan_effector_dir(bin_dir) == []

    @patch("metabolon.resources.proteome.os.access", return_value=True)
    def test_sorted_output(self, mock_access: MagicMock) -> None:
        from metabolon.resources.proteome import _scan_effector_dir

        files = [_mock_file(n) for n in ["zebra", "alpha", "mango"]]

        bin_dir = MagicMock(spec=Path)
        bin_dir.exists.return_value = True
        bin_dir.iterdir.return_value = files

        result = _scan_effector_dir(bin_dir)
        assert [e["name"] for e in result] == ["alpha", "mango", "zebra"]


# ---------------------------------------------------------------------------
# _scan_organelle_tools
# ---------------------------------------------------------------------------


class TestScanOrganelleTools:
    """Test _scan_organelle_tools with mocked _extract_tool_details."""

    @patch("metabolon.resources.proteome._extract_tool_details")
    def test_extracts_tools_from_modules(self, mock_extract: MagicMock) -> None:
        from metabolon.resources.proteome import _scan_organelle_tools

        mock_extract.return_value = [
            {"name": "vivesca__search", "doc": "Search things", "params": ["q"]},
            {"name": "vivesca__fetch", "doc": "Fetch data", "params": ["url"]},
        ]

        mod = MagicMock(spec=Path)
        mod.name = "search.py"
        mod.stem = "search"

        tools_dir = MagicMock(spec=Path)
        tools_dir.exists.return_value = True
        tools_dir.glob.return_value = [mod]

        result = _scan_organelle_tools(tools_dir)
        assert len(result) == 2
        assert result[0]["name"] == "vivesca__search"
        assert result[0]["type"] == "mcp"
        assert result[0]["source"] == "vivesca/search"
        assert result[0]["description"] == "Search things"
        assert result[1]["description"] == "Fetch data"

    def test_nonexistent_dir_returns_empty(self) -> None:
        from metabolon.resources.proteome import _scan_organelle_tools

        d = MagicMock(spec=Path)
        d.exists.return_value = False
        assert _scan_organelle_tools(d) == []

    @patch("metabolon.resources.proteome._extract_tool_details")
    def test_skips_init_module(self, mock_extract: MagicMock) -> None:
        from metabolon.resources.proteome import _scan_organelle_tools

        init_mod = MagicMock(spec=Path)
        init_mod.name = "__init__.py"

        tools_dir = MagicMock(spec=Path)
        tools_dir.exists.return_value = True
        tools_dir.glob.return_value = [init_mod]

        result = _scan_organelle_tools(tools_dir)
        assert result == []
        mock_extract.assert_not_called()

    @patch("metabolon.resources.proteome._extract_tool_details")
    def test_empty_doc_becomes_empty_string(self, mock_extract: MagicMock) -> None:
        from metabolon.resources.proteome import _scan_organelle_tools

        mock_extract.return_value = [
            {"name": "vivesca__nodoc", "doc": None, "params": []},
        ]

        mod = MagicMock(spec=Path)
        mod.name = "bare.py"
        mod.stem = "bare"

        tools_dir = MagicMock(spec=Path)
        tools_dir.exists.return_value = True
        tools_dir.glob.return_value = [mod]

        result = _scan_organelle_tools(tools_dir)
        assert len(result) == 1
        assert result[0]["description"] == ""

    @patch("metabolon.resources.proteome._extract_tool_details")
    def test_no_tools_in_module(self, mock_extract: MagicMock) -> None:
        from metabolon.resources.proteome import _scan_organelle_tools

        mock_extract.return_value = []

        mod = MagicMock(spec=Path)
        mod.name = "empty.py"
        mod.stem = "empty"

        tools_dir = MagicMock(spec=Path)
        tools_dir.exists.return_value = True
        tools_dir.glob.return_value = [mod]

        assert _scan_organelle_tools(tools_dir) == []


# ---------------------------------------------------------------------------
# _read_signal_routing
# ---------------------------------------------------------------------------


class TestReadSignalRouting:
    """Test _read_signal_routing with mocked file I/O."""

    def test_reads_existing_file(self) -> None:
        from metabolon.resources.proteome import _read_signal_routing

        p = MagicMock(spec=Path)
        p.exists.return_value = True
        p.read_text.return_value = "# Routing Table
| Trigger | Tool |
"

        result = _read_signal_routing(p)
        assert "Routing Table" in result
        assert "Trigger" in result

    def test_missing_file_returns_empty(self) -> None:
        from metabolon.resources.proteome import _read_signal_routing

        p = MagicMock(spec=Path)
        p.exists.return_value = False
        assert _read_signal_routing(p) == ""

    def test_oserror_returns_empty(self) -> None:
        from metabolon.resources.proteome import _read_signal_routing

        p = MagicMock(spec=Path)
        p.exists.return_value = True
        p.read_text.side_effect = OSError("permission denied")
        assert _read_signal_routing(p) == ""

    def test_strips_whitespace(self) -> None:
        from metabolon.resources.proteome import _read_signal_routing

        p = MagicMock(spec=Path)
        p.exists.return_value = True
        p.read_text.return_value = "  content line  

"
        assert _read_signal_routing(p) == "content line"


# ---------------------------------------------------------------------------
# express_effector_index (public API)
# ---------------------------------------------------------------------------


class TestExpressEffectorIndex:
    """Test express_effector_index with all internal helpers mocked."""

    @patch("metabolon.resources.proteome._read_signal_routing", return_value="")
    @patch("metabolon.resources.proteome._scan_organelle_tools")
    @patch("metabolon.resources.proteome._scan_effector_dir")
    def test_full_index(
        self,
        mock_scan_cli: MagicMock,
        mock_scan_mcp: MagicMock,
        mock_routing: MagicMock,
    ) -> None:
        from metabolon.resources.proteome import express_effector_index

        mock_scan_cli.return_value = [
            {"name": "lysin", "type": "cli", "source": "vivesca/effectors/"},
        ]
        mock_scan_mcp.return_value = [
            {"name": "vivesca__search", "type": "mcp", "source": "vivesca/search", "description": "Search"},
        ]

        output = express_effector_index(
            bin_dir=Path("/fake/bin"),
            tools_dir=Path("/fake/tools"),
            routing_path=Path("/fake/routing.md"),
        )

        assert "# Tool Index" in output
        assert "Total: 2 tools (1 MCP, 1 CLI)" in output
        assert "## MCP Tools (1)" in output
        assert "vivesca__search" in output
        assert "## CLI Tools (1)" in output
        assert "lysin" in output

    @patch("metabolon.resources.proteome._read_signal_routing", return_value="# Routing
stuff")
    @patch("metabolon.resources.proteome._scan_organelle_tools", return_value=[])
    @patch("metabolon.resources.proteome._scan_effector_dir", return_value=[])
    def test_routing_included(
        self,
        mock_cli: MagicMock,
        mock_mcp: MagicMock,
        mock_routing: MagicMock,
    ) -> None:
        from metabolon.resources.proteome import express_effector_index

        output = express_effector_index(
            bin_dir=Path("/x"),
            tools_dir=Path("/y"),
            routing_path=Path("/z"),
        )
        assert "# Routing" in output
        assert "stuff" in output

    @patch("metabolon.resources.proteome._read_signal_routing", return_value="")
    @patch("metabolon.resources.proteome._scan_organelle_tools", return_value=[])
    @patch("metabolon.resources.proteome._scan_effector_dir", return_value=[])
    def test_empty_everything(
        self,
        mock_cli: MagicMock,
        mock_mcp: MagicMock,
        mock_routing: MagicMock,
    ) -> None:
        from metabolon.resources.proteome import express_effector_index

        output = express_effector_index(
            bin_dir=Path("/x"),
            tools_dir=Path("/y"),
            routing_path=Path("/z"),
        )
        assert "Total: 0 tools (0 MCP, 0 CLI)" in output
        assert "## MCP Tools (0)" in output
        assert "## CLI Tools (0)" in output

    @patch("metabolon.resources.proteome._read_signal_routing", return_value="")
    @patch("metabolon.resources.proteome._scan_organelle_tools", return_value=[])
    @patch("metabolon.resources.proteome._scan_effector_dir")
    def test_description_truncation(
        self,
        mock_cli: MagicMock,
        mock_mcp: MagicMock,
        mock_routing: MagicMock,
    ) -> None:
        from metabolon.resources.proteome import express_effector_index

        mock_cli.return_value = []
        long_desc = "A" * 120
        mock_mcp.return_value = [
            {"name": "vivesca__long", "type": "mcp", "source": "vivesca/x", "description": long_desc},
        ]

        output = express_effector_index(
            bin_dir=Path("/x"),
            tools_dir=Path("/y"),
            routing_path=Path("/z"),
        )

        for line in output.splitlines():
            if "vivesca__long" in line:
                cells = [c.strip() for c in line.split("|") if c.strip()]
                desc = cells[-1]
                assert len(desc) <= 80
                break

    @patch("metabolon.resources.proteome._read_signal_routing", return_value="")
    @patch("metabolon.resources.proteome._scan_organelle_tools")
    @patch("metabolon.resources.proteome._scan_effector_dir")
    def test_uses_default_paths_when_none_provided(
        self,
        mock_cli: MagicMock,
        mock_mcp: MagicMock,
        mock_routing: MagicMock,
    ) -> None:
        from metabolon.resources.proteome import _BIN_DIR, _ROUTING_TABLE, _VIVESCA_TOOLS, express_effector_index

        mock_cli.return_value = []
        mock_mcp.return_value = []

        output = express_effector_index()

        mock_cli.assert_called_once_with(_BIN_DIR)
        mock_mcp.assert_called_once_with(_VIVESCA_TOOLS)
        mock_routing.assert_called_once_with(_ROUTING_TABLE)
        assert isinstance(output, str)

    @patch("metabolon.resources.proteome._read_signal_routing", return_value="")
    @patch("metabolon.resources.proteome._scan_organelle_tools", return_value=[])
    @patch("metabolon.resources.proteome._scan_effector_dir")
    def test_multiple_cli_tools_in_table(
        self,
        mock_cli: MagicMock,
        mock_mcp: MagicMock,
        mock_routing: MagicMock,
    ) -> None:
        from metabolon.resources.proteome import express_effector_index

        mock_cli.return_value = [
            {"name": "zebra", "type": "cli", "source": "vivesca/effectors/"},
            {"name": "alpha", "type": "cli", "source": "vivesca/effectors/"},
        ]

        output = express_effector_index(
            bin_dir=Path("/x"),
            tools_dir=Path("/y"),
            routing_path=Path("/z"),
        )

        assert "zebra" in output
        assert "alpha" in output
        assert "Total: 2 tools (0 MCP, 2 CLI)" in output

    @patch("metabolon.resources.proteome._read_signal_routing", return_value="")
    @patch("metabolon.resources.proteome._scan_organelle_tools")
    @patch("metabolon.resources.proteome._scan_effector_dir", return_value=[])
    def test_mcp_tool_without_description(
        self,
        mock_cli: MagicMock,
        mock_mcp: MagicMock,
        mock_routing: MagicMock,
    ) -> None:
        from metabolon.resources.proteome import express_effector_index

        mock_mcp.return_value = [
            {"name": "vivesca__bare", "type": "mcp", "source": "vivesca/x", "description": ""},
        ]

        output = express_effector_index(
            bin_dir=Path("/x"),
            tools_dir=Path("/y"),
            routing_path=Path("/z"),
        )

        assert "vivesca__bare" in output
        lines = [l for l in output.splitlines() if "vivesca__bare" in l]
        assert len(lines) == 1
