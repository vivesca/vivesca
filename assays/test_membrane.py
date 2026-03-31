from __future__ import annotations
"""Smoke tests for vivesca MCP server assembly.

Guards against silent 0-tool servers (burned us 2026-03-28 when a
directory rename left a stale path in membrane.py).
"""


import asyncio

import pytest


@pytest.fixture(scope="module")
def mcp():
    from metabolon.membrane import mcp
    return mcp


def test_assembly_produces_tools(mcp):
    """The assembled server must expose at least one tool."""
    tools = asyncio.run(mcp.list_tools())
    assert len(tools) > 30, f"Expected 30+ tools, got {len(tools)}"


def test_assembly_produces_prompts(mcp):
    """The assembled server must expose at least one prompt."""
    prompts = asyncio.run(mcp.list_prompts())
    assert len(prompts) > 0, f"Expected prompts, got {len(prompts)}"


def test_provider_dirs_exist():
    """All FileSystemProvider source dirs must exist on disk."""
    from metabolon.cytosol import VIVESCA_ROOT

    src = VIVESCA_ROOT / "metabolon"
    for dirname in ("enzymes", "codons"):
        d = src / dirname
        assert d.is_dir(), f"Provider dir missing: {d}"
        py_files = [f for f in d.glob("*.py") if f.name != "__init__.py"]
        assert py_files, f"No modules in {d}"
