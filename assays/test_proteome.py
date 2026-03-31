"""Tests for metabolon.resources.proteome."""

from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_cli_dir(tmp_path: Path) -> Path:
    """Create a temporary directory with some fake CLI executables."""
    bin_dir = tmp_path / "effectors"
    bin_dir.mkdir()
    # Executable files
    for name in ("lysin", "sortase"):
        f = bin_dir / name
        f.write_text("#!/bin/sh\n")
        f.chmod(0o755)
    # Non-executable — should be skipped
    (bin_dir / "dormant").write_text("not executable")
    # Directory — should be skipped
    (bin_dir / "subdir").mkdir()
    # Dotfile / underscore — should be skipped
    for name in (".hidden", "_private"):
        f = bin_dir / name
        f.write_text("#!/bin/sh\n")
        f.chmod(0o755)
    return bin_dir


@pytest.fixture()
def sample_tools_dir(tmp_path: Path) -> Path:
    """Create a temporary tools dir with a fake @tool-bearing module."""
    tools = tmp_path / "tools"
    tools.mkdir()
    mod = tools / "example.py"
    mod.write_text(textwrap.dedent("""\
        from some_sdk import tool

        @tool
        def vivesca__foo(query: str) -> str:
            '''Search for things.'''
            return query

        @tool(name="vivesca__bar")
        async def bar_func(x: int) -> int:
            '''Do the thing.'''
            return x

        def helper():
            pass
    """))
    return tools


@pytest.fixture()
def sample_routing(tmp_path: Path) -> Path:
    """Create a minimal routing table file."""
    rp = tmp_path / "proteome.md"
    rp.write_text("# Signal Routing\n| Trigger | Tool |\n|---------|------|\n| email  | endosomal |")
    return rp


# ---------------------------------------------------------------------------
# _scan_effector_dir
# ---------------------------------------------------------------------------

class TestScanEffectorDir:
    def test_finds_executables(self, sample_cli_dir: Path) -> None:
        from metabolon.resources.proteome import _scan_effector_dir

        result = _scan_effector_dir(sample_cli_dir)
        names = {e["name"] for e in result}
        assert names == {"lysin", "sortase"}
        assert all(e["type"] == "cli" for e in result)
        assert all("vivesca/effectors/" in e["source"] for e in result)

    def test_nonexistent_dir(self, tmp_path: Path) -> None:
        from metabolon.resources.proteome import _scan_effector_dir

        result = _scan_effector_dir(tmp_path / "nope")
        assert result == []

    def test_empty_dir(self, tmp_path: Path) -> None:
        from metabolon.resources.proteome import _scan_effector_dir

        d = tmp_path / "empty"
        d.mkdir()
        assert _scan_effector_dir(d) == []


# ---------------------------------------------------------------------------
# _scan_organelle_tools
# ---------------------------------------------------------------------------

class TestScanOrganelleTools:
    def test_extracts_tools(self, sample_tools_dir: Path) -> None:
        from metabolon.resources.proteome import _scan_organelle_tools

        result = _scan_organelle_tools(sample_tools_dir)
        assert len(result) == 2
        names = {e["name"] for e in result}
        assert "vivesca__foo" in names
        assert "vivesca__bar" in names
        assert all(e["type"] == "mcp" for e in result)
        assert all(e["source"].startswith("vivesca/") for e in result)

    def test_nonexistent_dir(self, tmp_path: Path) -> None:
        from metabolon.resources.proteome import _scan_organelle_tools

        assert _scan_organelle_tools(tmp_path / "absent") == []

    def test_dir_without_tools(self, tmp_path: Path) -> None:
        from metabolon.resources.proteome import _scan_organelle_tools

        d = tmp_path / "empty_tools"
        d.mkdir()
        (d / "nomod.txt").write_text("hello")
        assert _scan_organelle_tools(d) == []


# ---------------------------------------------------------------------------
# _read_signal_routing
# ---------------------------------------------------------------------------

class TestReadSignalRouting:
    def test_reads_file(self, sample_routing: Path) -> None:
        from metabolon.resources.proteome import _read_signal_routing

        text = _read_signal_routing(sample_routing)
        assert "Signal Routing" in text
        assert "endosomal" in text

    def test_missing_file(self, tmp_path: Path) -> None:
        from metabolon.resources.proteome import _read_signal_routing

        assert _read_signal_routing(tmp_path / "gone.md") == ""

    def test_unreadable_file(self, tmp_path: Path) -> None:
        from metabolon.resources.proteome import _read_signal_routing

        f = tmp_path / "secret.md"
        f.write_text("top secret")
        f.chmod(0o000)
        try:
            assert _read_signal_routing(f) == ""
        finally:
            f.chmod(0o644)  # restore for cleanup

    def test_empty_file(self, tmp_path: Path) -> None:
        from metabolon.resources.proteome import _read_signal_routing

        f = tmp_path / "blank.md"
        f.write_text("")
        assert _read_signal_routing(f) == ""

    def test_whitespace_only_file(self, tmp_path: Path) -> None:
        from metabolon.resources.proteome import _read_signal_routing

        f = tmp_path / "ws.md"
        f.write_text("   \n  \n")
        assert _read_signal_routing(f) == ""


# ---------------------------------------------------------------------------
# express_effector_index (public API)
# ---------------------------------------------------------------------------

class TestExpressEffectorIndex:
    def test_full_output(self, sample_cli_dir: Path, sample_tools_dir: Path, sample_routing: Path) -> None:
        from metabolon.resources.proteome import express_effector_index

        output = express_effector_index(
            bin_dir=sample_cli_dir,
            tools_dir=sample_tools_dir,
            routing_path=sample_routing,
        )
        # Title
        assert "# Tool Index" in output
        # Total line
        assert "Total: 4 tools (2 MCP, 2 CLI)" in output
        # Routing section present
        assert "Signal Routing" in output
        # MCP table
        assert "## MCP Tools (2)" in output
        assert "vivesca__foo" in output
        assert "vivesca__bar" in output
        # CLI table
        assert "## CLI Tools (2)" in output
        assert "lysin" in output
        assert "sortase" in output

    def test_empty_dirs_no_routing(self, tmp_path: Path) -> None:
        from metabolon.resources.proteome import express_effector_index

        empty_bin = tmp_path / "bin"
        empty_bin.mkdir()
        empty_tools = tmp_path / "tools"
        empty_tools.mkdir()
        no_routing = tmp_path / "proteome.md"

        output = express_effector_index(
            bin_dir=empty_bin,
            tools_dir=empty_tools,
            routing_path=no_routing,
        )
        assert "# Tool Index" in output
        assert "Total: 0 tools (0 MCP, 0 CLI)" in output
        assert "## MCP Tools (0)" in output
        assert "## CLI Tools (0)" in output

    def test_nonexistent_dirs(self, tmp_path: Path) -> None:
        from metabolon.resources.proteome import express_effector_index

        output = express_effector_index(
            bin_dir=tmp_path / "no_bin",
            tools_dir=tmp_path / "no_tools",
            routing_path=tmp_path / "no_routing.md",
        )
        assert "Total: 0 tools (0 MCP, 0 CLI)" in output

    def test_mcp_description_truncated(self, tmp_path: Path) -> None:
        """Descriptions longer than 80 chars should be truncated in the table."""
        from metabolon.resources.proteome import express_effector_index

        tools = tmp_path / "t"
        tools.mkdir()
        mod = tools / "long.py"
        long_doc = "A" * 120
        mod.write_text(
            f'from sdk import tool\n\n@tool\ndef vivesca__long_tool(x: int) -> int:\n    \'\'\'{long_doc}\'\'\'\n    return x\n'
        )
        output = express_effector_index(
            bin_dir=tmp_path / "nb",
            tools_dir=tools,
            routing_path=tmp_path / "nr.md",
        )
        # The description in the table should be at most 80 chars
        # Find the table row
        for line in output.splitlines():
            if "vivesca__long_tool" in line:
                # Extract description cell (last cell in pipe table)
                cells = [c.strip() for c in line.split("|") if c.strip()]
                desc = cells[-1]
                assert len(desc) <= 80
                break

    def test_defaults_use_module_paths(self) -> None:
        """Calling with no args should use the module-level defaults without crashing."""
        from metabolon.resources.proteome import express_effector_index

        # This hits real filesystem paths. It should return a string regardless
        # of whether the dirs exist.
        output = express_effector_index()
        assert isinstance(output, str)
        assert "# Tool Index" in output
