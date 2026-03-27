"""porta — Chrome-to-agent-browser cookie bridge.

Tools:
  porta_inject — Inject Chrome cookies into agent-browser for a domain.
"""

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.morphology import EffectorResult


@tool(
    name="porta_inject",
    description="Inject Chrome cookies into agent-browser for a domain.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def porta_inject(domain: str) -> EffectorResult:
    """Porta gate — bridge Chrome session cookies into agent-browser.

    Reads Chrome cookies from macOS Keychain via pycookiecheat, navigates
    agent-browser to the domain, then sets each cookie via document.cookie.

    Requires a GUI session (Keychain access). Will not work from Blink/SSH.
    Does not handle localStorage or JWT-only auth.

    Args:
        domain: Domain to inject cookies for, e.g. "bigmodel.cn".
    """
    from metabolon.organelles.porta import inject

    result = inject(domain)
    return EffectorResult(
        success=result["success"],
        message=result["message"],
        data={"count": result["count"], "domain": domain},
    )
