"""Test MCP initialize handshake for myapp."""

import asyncio
import sys
from pathlib import Path


async def test_handshake():
    """Connect to myapp via stdio and verify the MCP handshake."""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "myapp"],
        cwd=str(Path(__file__).resolve().parent.parent),
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            result = await session.initialize()
            assert result.serverInfo.name == "myapp"
            assert result.capabilities.tools is not None
            print(f"Handshake OK: {result.serverInfo.name}")


if __name__ == "__main__":
    asyncio.run(test_handshake())