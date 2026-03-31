"""demo — MCP server.

Built with vivesca conventions:
- Structured output (Pydantic return types → outputSchema)
- Tool annotations (readOnlyHint, destructiveHint)
- Service-layer separation (tools are thin wrappers)
"""

from pathlib import Path

from fastmcp import FastMCP
from fastmcp.server.providers import FileSystemProvider

_project_root = Path(__file__).resolve().parent.parent.parent


def create_server() -> FastMCP:
    """Build and return the demo FastMCP server."""
    mcp = FastMCP(
        "demo",
        instructions="Demo MCP server",
        providers=[
            FileSystemProvider(_project_root / "src" / "demo" / "tools"),
            FileSystemProvider(_project_root / "src" / "demo" / "resources"),
            FileSystemProvider(_project_root / "src" / "demo" / "prompts"),
        ],
    )
    return mcp


mcp = create_server()


def main():
    """Entry point for demo CLI (stdio transport)."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()