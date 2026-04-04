"""synthase — spawn headless CC with full organism access.

Tools:
  synthase — run a prompt through Claude Code with MCP, skills, memory
"""

from pathlib import Path

from fastmcp.tools.function_tool import tool
from mcp.types import ToolAnnotations

from metabolon.organelles.effector import run_cli

CHANNEL = str(Path.home() / "germline" / "effectors" / "channel")

_TIMEOUT = 300


@tool(
    name="synthase",
    description="Headless CC with full organism access (MCP, skills, memory).",
    annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=False),
)
def synthase(prompt: str, model: str = "sonnet") -> str:
    """Spawn a headless Claude Code session with full organism context.

    Args:
        prompt: The task or question for CC.
        model: Model to use — haiku, sonnet, or opus.
    """
    if model not in ("haiku", "sonnet", "opus"):
        raise ValueError(f"Unknown model: {model}. Choose haiku, sonnet, or opus.")
    return run_cli(CHANNEL, [model, "--organism", "-p", prompt], timeout=_TIMEOUT)
