from __future__ import annotations

"""Test MCP initialize handshake via the mcp client SDK.

Uses FastMCP's client to connect to the vivesca server over stdio
and verify the handshake, tool listing, and resource listing.
"""


import asyncio
import sys
from pathlib import Path

import pytest


@pytest.mark.slow
@pytest.mark.asyncio
async def test_handshake():
    """Connect to vivesca via stdio and verify the MCP handshake."""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "vivesca"],
        cwd=str(Path(__file__).resolve().parent.parent),
    )

    async with (
        stdio_client(server_params) as (read_stream, write_stream),
        ClientSession(read_stream, write_stream) as session,
    ):
        # --- 1. Initialize ---
        result = await session.initialize()
        print(f"Protocol version: {result.protocolVersion}")
        print(f"Server: {result.serverInfo.name} v{result.serverInfo.version}")

        assert result.serverInfo.name == "vivesca", (
            f"Server name mismatch: {result.serverInfo.name}"
        )
        assert result.capabilities.tools is not None, "Expected tools capability"

        # --- 2. List tools ---
        tools_result = await session.expressed_tools()
        tools = tools_result.tools
        tool_names = sorted(t.name for t in tools)

        print(f"\nTools ({len(tools)}):")
        for t in sorted(tools, key=lambda x: x.name):
            desc = t.description or ""
            print(f"  {t.name}: {desc[:70]}")

        expected_tools = [
            "anabolism_flywheel",
            "proteasome_confirm",
            "proteasome_spending",
            "checkpoint_delete",
            "checkpoint_list",
            "checkpoint_move",
            "checkpoint_set",
            "rheotaxis",
            "circadian_sleep",
            "endocytosis_check_auth",
            "endocytosis_extract",
            "endocytosis_screenshot",
            "exocytosis_image",
            "exocytosis_text",
            "histone_mark",
            "histone_search",
            "histone_stats",
            "histone_status",
            "homeostasis_system",
            "ligand_bind",
            "ligand_draft",
            "lysosome_digest",
            "membrane_potential",
            "metabolism_knowledge_signal",
            "nociception_log",
            "proprioception_drill",
            "proprioception_sense",
            "proprioception_skills",
            "receptor_list",
            "receptor_sync",
        ]
        assert tool_names == expected_tools, (
            f"Tool mismatch.\n  Expected: {expected_tools}\n  Got:      {tool_names}"
        )

        # --- 3. Verify tool schemas have required fields ---
        for t in tools:
            assert t.name, "Tool missing name"
            assert t.description, f"Tool {t.name} missing description"
            schema = t.inputSchema
            assert schema, f"Tool {t.name} missing inputSchema"

        # --- 4. Verify structured output schemas ---
        tools_with_output = [t for t in tools if t.outputSchema]
        print(f"\nTools with outputSchema: {len(tools_with_output)}/{len(tools)}")
        for t in sorted(tools_with_output, key=lambda x: x.name):
            schema = t.outputSchema or {}
            print(f"  {t.name}: {list(schema.get('properties', {}).keys())}")

        assert len(tools_with_output) == len(tools), (
            f"All tools should have outputSchema, missing: {[t.name for t in tools if not t.outputSchema]}"
        )

        # --- 5. List resources ---
        resources_result = await session.list_resources()
        resources = resources_result.resources

        print(f"\nResources ({len(resources)}):")
        for r in resources:
            print(f"  {r.uri}: {r.name}")

        resource_uris = [str(r.uri) for r in resources]
        expected_resources = [
            "vivesca://budget",
            "vivesca://calendar/today",
            "vivesca://constitution",
            "vivesca://rheotaxis/search-log",
            "vivesca://oghma/stats",
        ]
        for expected_uri in expected_resources:
            assert expected_uri in resource_uris, (
                f"Missing resource {expected_uri}. Got: {resource_uris}"
            )

        # --- 6. List prompts ---
        prompts_result = await session.list_prompts()
        prompts = prompts_result.prompts

        print(f"\nPrompts ({len(prompts)}):")
        for p in sorted(prompts, key=lambda x: x.name):
            desc = p.description or ""
            print(f"  {p.name}: {desc[:70]}")

        prompt_names = sorted(p.name for p in prompts)
        expected_prompts = [
            "draft_message",
            "morning_brief",
            "research",
        ]
        assert prompt_names == expected_prompts, (
            f"Prompt mismatch.\n  Expected: {expected_prompts}\n  Got:      {prompt_names}"
        )

        print("\n--- All handshake tests passed. ---")


if __name__ == "__main__":
    asyncio.run(test_handshake())
