#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Sync MCP servers from canonical config to Claude Code, Codex, and OpenCode.

Canonical source: ~/agent-config/mcp-servers.json
Targets:
  - Claude Code (prints commands to run)
  - ~/.codex/config.toml
  - ~/.opencode/mcp.json

Usage:
  uv run ~/scripts/mcp-sync.py [--apply]

Without --apply: shows what would change (dry run)
With --apply: updates Codex/OpenCode, prints Claude commands
"""

import json
import os
import sys
from pathlib import Path

# Paths
CANONICAL_CONFIG = Path.home() / "agent-config" / "mcp-servers.json"
CODEX_CONFIG = Path.home() / ".codex" / "config.toml"
OPENCODE_MCP = Path.home() / ".opencode" / "mcp.json"

# Command path mappings for Codex (needs full paths)
PATH_MAP = {
    "npx": "/opt/homebrew/bin/npx",
    "uvx": "/Users/terry/.pyenv/shims/uvx",
}


def load_canonical() -> tuple[dict, dict]:
    """Load canonical MCP config. Returns (servers, codex_extras)."""
    with open(CANONICAL_CONFIG) as f:
        data = json.load(f)
    return data.get("mcpServers", {}), data.get("_codexExtras", {})


def generate_claude_commands(servers: dict) -> list[str]:
    """Generate claude mcp add commands."""
    commands = []

    for name, server in servers.items():
        parts = ["claude", "mcp", "add", "-s", "user"]

        # Add env vars
        if "env" in server:
            for k, v in server["env"].items():
                # Use env var reference
                parts.extend(["-e", f"{k}={v}"])

        parts.append(name)
        parts.append("--")
        parts.append(server.get("command", ""))
        parts.extend(server.get("args", []))

        commands.append(" ".join(parts))

    return commands


def generate_codex_mcp_lines(servers: dict, extras: dict) -> list[str]:
    """Generate TOML lines for MCP servers."""
    lines = []

    # Add extras first (context7, serena)
    for name, server in extras.items():
        lines.append(f"[mcp_servers.{name}]")
        if "url" in server:
            lines.append(f'url = "{server["url"]}"')
        else:
            cmd = server.get("command", "")
            lines.append(f'command = "{PATH_MAP.get(cmd, cmd)}"')
            args_str = ", ".join(f'"{a}"' for a in server.get("args", []))
            lines.append(f"args = [{args_str}]")
        lines.append("")

    # Add main servers
    for name, server in servers.items():
        lines.append(f"[mcp_servers.{name}]")
        cmd = server.get("command", "")
        lines.append(f'command = "{PATH_MAP.get(cmd, cmd)}"')
        args_str = ", ".join(f'"{a}"' for a in server.get("args", []))
        lines.append(f"args = [{args_str}]")
        if "env" in server:
            env_parts = ", ".join(f'{k} = "{v}"' for k, v in server["env"].items())
            lines.append(f"env = {{ {env_parts} }}")
        lines.append("")

    return lines


def sync_codex(servers: dict, extras: dict, dry_run: bool = True) -> None:
    """Sync MCP servers to Codex config."""
    with open(CODEX_CONFIG) as f:
        content = f.read()

    lines = content.split("\n")
    new_lines = []
    in_mcp_section = False
    mcp_inserted = False

    for line in lines:
        if line.strip().startswith("[mcp_servers."):
            if not mcp_inserted:
                new_lines.extend(generate_codex_mcp_lines(servers, extras))
                mcp_inserted = True
            in_mcp_section = True
            continue

        if (
            in_mcp_section
            and line.strip().startswith("[")
            and not line.strip().startswith("[mcp_servers")
        ):
            in_mcp_section = False

        if not in_mcp_section:
            new_lines.append(line)

    if not mcp_inserted:
        final_lines = []
        inserted = False
        for line in new_lines:
            if not inserted and (
                line.strip().startswith("[projects") or line.strip().startswith("[features")
            ):
                final_lines.extend(generate_codex_mcp_lines(servers, extras))
                final_lines.append("")
                inserted = True
            final_lines.append(line)
        if not inserted:
            final_lines.extend(generate_codex_mcp_lines(servers, extras))
        new_lines = final_lines

    result = "\n".join(new_lines)

    if dry_run:
        print("=== Codex config (would write) ===")
        print(result)
    else:
        with open(CODEX_CONFIG, "w") as f:
            f.write(result)
        print(f"✓ Updated {CODEX_CONFIG}")


def sync_opencode(servers: dict, dry_run: bool = True) -> None:
    """Sync MCP servers to OpenCode config (strip env var values)."""
    opencode_servers = {}

    for name, server in servers.items():
        s = {"command": server.get("command", "")}
        if "args" in server:
            s["args"] = server["args"]
        # Keep env keys but OpenCode reads from actual env at runtime
        if "env" in server:
            s["env"] = {k: os.environ.get(k, "") for k in server["env"]}
        opencode_servers[name] = s

    result = {"mcpServers": opencode_servers}
    output = json.dumps(result, indent=2)

    if dry_run:
        print("\n=== OpenCode config (would write) ===")
        print(output)
    else:
        with open(OPENCODE_MCP, "w") as f:
            f.write(output + "\n")
        print(f"✓ Updated {OPENCODE_MCP}")


def main():
    apply = "--apply" in sys.argv

    print(f"Canonical source: {CANONICAL_CONFIG}")
    print(f"Mode: {'APPLY' if apply else 'DRY RUN'}\n")

    servers, extras = load_canonical()
    print(f"Found {len(servers)} servers + {len(extras)} Codex extras\n")

    # Claude Code commands
    print("--- Claude Code Commands ---")
    print("Run these to sync Claude Code (or skip if already configured):\n")
    for cmd in generate_claude_commands(servers):
        print(cmd)
    print()

    # Codex
    print("--- Codex Sync ---")
    sync_codex(servers, extras, dry_run=not apply)

    # OpenCode
    print("\n--- OpenCode Sync ---")
    sync_opencode(servers, dry_run=not apply)

    if not apply:
        print("\n---")
        print("Run with --apply to update Codex/OpenCode configs")


if __name__ == "__main__":
    main()
