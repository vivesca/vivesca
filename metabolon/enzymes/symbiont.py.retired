from __future__ import annotations

"""symbiont — free agentic LLM via CC harness.

Runs GLM-5.1 (ZhiPu Coding Plan, free) as a full CC session
with access to all MCP tools. Endosymbiont pattern: separate
genome, host's machinery.
"""

import os
import shutil
import subprocess

from fastmcp.tools.function_tool import tool
from mcp.types import ToolAnnotations


@tool(
    name="symbiont",
    description="Free agentic LLM (GLM-5.1). Full MCP tool access. Use for heavy tasks to save Opus context.",
    annotations=ToolAnnotations(readOnlyHint=False),
)
def symbiont(prompt: str) -> str:
    """Run a prompt through GLM-5.1 via CC harness with full tool access.

    Args:
        prompt: The task or question for GLM-5.1.
    """
    env = {
        **dict(os.environ),
        "ANTHROPIC_BASE_URL": "https://open.bigmodel.cn/api/anthropic",
        "ANTHROPIC_API_KEY": os.environ.get("ZHIPU_API_KEY", ""),
        "CLAUDECODE": "",
    }
    result = subprocess.run(
        [shutil.which("claude") or "claude",
         "--print", "-p", prompt,
         "--disallowedTools", "mcp__vivesca__symbiont",
         "--model", "glm-5.1"],
        capture_output=True, text=True, timeout=300, env=env,
    )
    if result.returncode != 0:
        return f"symbiont error: {result.stderr[:300]}"
    return result.stdout.strip()
