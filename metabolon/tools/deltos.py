"""deltos — exocytosis of messages into the Telegram channel.

Tools:
  exocytosis_text  — secrete a text/HTML message
  exocytosis_image — secrete an image file with optional caption
"""

import os

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.morphology import EffectorResult


class ExocytosisResult(EffectorResult):
    """Product of secreting a message into the Telegram channel."""

    pass


def _package_for_telegram(text: str) -> str:
    """Secretory vesicle packaging: format content for Telegram destination.

    Telegram conventions: strip markdown headers, keep concise,
    use HTML formatting. Content is packaged for the recipient,
    not sent raw.
    """
    import re

    # Strip markdown headers → bold HTML
    text = re.sub(r"^#{1,3}\s+(.+)$", r"<b>\1</b>", text, flags=re.MULTILINE)
    # Strip markdown bold → HTML bold
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    # Strip markdown links → plain text with URL
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r"\1 (\2)", text)
    return text


@tool(
    name="exocytosis_text",
    description="Send text to Telegram. HTML by default; format='plain' for raw.",
    annotations=ToolAnnotations(destructiveHint=False, idempotentHint=False),
)
def exocytosis_text(text: str, format: str = "html") -> ExocytosisResult:
    """Secrete a text message into the Telegram channel. Packaging applied."""
    if format == "html":
        text = _package_for_telegram(text)
    from metabolon.organelles.secretory_vesicle import send_text

    html_mode = format != "plain"
    result = send_text(text, html=html_mode)
    return ExocytosisResult(success=True, message=result)


@tool(
    name="exocytosis_image",
    description="Send an image to Telegram with optional caption.",
    annotations=ToolAnnotations(destructiveHint=False, idempotentHint=False),
)
def exocytosis_image(path: str, caption: str = "") -> ExocytosisResult:
    """Secrete an image into the Telegram channel."""
    from metabolon.organelles.secretory_vesicle import send_photo

    expanded = os.path.expanduser(path)
    if not os.path.isfile(expanded):
        raise ValueError(f"File not found: {expanded}")

    result = send_photo(expanded, caption=caption)
    return ExocytosisResult(success=True, message=result)
