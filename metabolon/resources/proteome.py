"""Effectors — how the organism acts on the world.

Resources:
  vivesca://effectors — CLI tools, MCP tools, and trigger routing
"""

from __future__ import annotations

import os
from pathlib import Path

from metabolon.cytosol import VIVESCA_ROOT
from metabolon.resources.anatomy import _extract_tool_details

_BIN_DIR = VIVESCA_ROOT / "effectors"
_VIVESCA_TOOLS = Path(__file__).resolve().parent.parent / "tools"
_ROUTING_TABLE = VIVESCA_ROOT / "proteome.md"


def _scan_effector_dir(bin_dir: Path) -> list[dict]:
    """Scan vivesca/effectors/ for executable files with optional --help descriptions."""
    entries: list[dict] = []
    if not bin_dir.exists():
        return entries

    for f in sorted(bin_dir.iterdir()):
        if f.name.startswith(".") or f.name.startswith("_"):
            continue
        if not f.is_file():
            continue
        # Check executable bit
        if not os.access(f, os.X_OK):
            continue
        entries.append({"name": f.name, "type": "cli", "source": "vivesca/effectors/"})
    return entries


def _scan_organelle_tools(tools_dir: Path) -> list[dict]:
    """Scan vivesca tool modules for @tool-decorated functions."""
    entries: list[dict] = []
    if not tools_dir.exists():
        return entries

    for mod in sorted(tools_dir.glob("*.py")):
        if mod.name == "__init__.py":
            continue
        details = _extract_tool_details(mod)
        for td in details:
            doc = td["doc"] if td["doc"] else ""
            entries.append(
                {
                    "name": td["name"],
                    "type": "mcp",
                    "source": f"vivesca/{mod.stem}",
                    "description": doc,
                }
            )
    return entries


def _read_signal_routing(path: Path) -> str:
    """Read the curated trigger→tool routing table."""
    if not path.exists():
        return ""
    try:
        return path.read_text().strip()
    except OSError:
        return ""


def express_effector_index(
    bin_dir: Path | None = None,
    tools_dir: Path | None = None,
    routing_path: Path | None = None,
) -> str:
    """Build a unified tool index from CLI binaries, MCP tools, and routing table."""
    bd = bin_dir or _BIN_DIR
    td = tools_dir or _VIVESCA_TOOLS
    rp = routing_path or _ROUTING_TABLE

    cli_tools = _scan_effector_dir(bd)
    mcp_tools = _scan_organelle_tools(td)

    lines: list[str] = []

    lines.append("# Tool Index\n")

    # Routing table (curated trigger→tool mapping)
    routing = _read_signal_routing(rp)
    if routing:
        lines.append(routing)
        lines.append("")

    # MCP tools (computed)
    lines.append(f"## MCP Tools ({len(mcp_tools)})\n")
    lines.append("| Tool | Domain | Description |")
    lines.append("|------|--------|-------------|")
    for t in mcp_tools:
        desc = t.get("description", "")[:80]
        lines.append(f"| `{t['name']}` | {t['source']} | {desc} |")

    # CLI tools (computed)
    lines.append(f"\n## CLI Tools ({len(cli_tools)})\n")
    lines.append("| Tool | Source |")
    lines.append("|------|--------|")
    for t in cli_tools:
        lines.append(f"| `{t['name']}` | {t['source']} |")

    total = len(cli_tools) + len(mcp_tools)
    lines.insert(1, f"_Total: {total} tools ({len(mcp_tools)} MCP, {len(cli_tools)} CLI)_\n")

    return "\n".join(lines)
