from __future__ import annotations

"""Base Pydantic models for vivesca structured output.

Every tool secretes a product into the organism's environment.
These base classes define the membrane through which all
tool outputs pass — typed, structured, forward-compatible.
"""


from pathlib import Path

from pydantic import BaseModel, ConfigDict


def resolve_memory_dir() -> Path:
    """Resolve the CC project memory dir for the current platform.

    CC project dirs encode the working directory with ``-`` replacing ``/``.
    On macOS (home = /Users/terry) the dir is ``-Users-terry``;
    on Linux/soma (home = /home/terry) it's ``-home-terry``.
    """
    base = Path.home() / ".claude" / "projects"
    for candidate in ("-home-terry", "-Users-terry", "-home-terry-germline"):
        d = base / candidate / "memory"
        if d.exists():
            return d
    # Fallback: first project dir that has a memory/ subdir
    if base.exists():
        for p in sorted(base.iterdir()):
            mem = p / "memory"
            if mem.is_dir():
                return mem
    # Last resort: derive from home path
    home = str(Path.home()).replace("/", "-").lstrip("-")
    return base / f"-{home}" / "memory"


class Secretion(BaseModel):
    """Base class for all tool secretions.

    Every tool is a cell that secretes structured product.
    Inherit from this to get:
    - Automatic outputSchema generation via FastMCP
    - Forward-compatible extra fields
    - Consistent JSON serialization
    """

    model_config = ConfigDict(extra="allow")


class Pathology(BaseModel):
    """Structured error — a disease state in tool execution.

    Returned when a tool encounters a failure that must be
    communicated as structured diagnostic information.
    """

    error: str
    code: str = "unknown"
    details: dict = {}


class Vesicle(Secretion):
    """Membrane-bound transport container for list payloads.

    Wraps a collection of items for transport through the
    organism's signalling pathways. Auto-counts contents.
    """

    items: list[dict]
    count: int = 0

    def model_post_init(self, __context) -> None:
        if self.count == 0 and self.items:
            self.count = len(self.items)


class Vital(Secretion):
    """Vital sign measurement — health/status check output."""

    status: str  # "ok", "warning", "error"
    message: str
    details: dict = {}


class EffectorResult(Secretion):
    """Result of an effector action — a mutation in the environment."""

    success: bool
    message: str
    data: dict = {}
