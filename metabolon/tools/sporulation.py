"""sporulation — cross-session checkpoint save/load.

A bacterium sporulates when conditions turn hostile: it compresses its essential
DNA into a compact, resistant spore. Same here — compress live context into a
checkpoint, germinate in a fresh session.

Tools:
  sporulation_save   — write a session checkpoint with a codename
  sporulation_load   — read an existing checkpoint by codename
  sporulation_list   — list active checkpoints
"""

from __future__ import annotations

import contextlib
import random
from datetime import UTC, datetime
from pathlib import Path

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.morphology import Secretion

_CHECKPOINT_DIR = Path.home() / ".claude" / "projects" / "-Users-terry" / "memory"

_ADJECTIVES = [
    "happy",
    "calm",
    "bold",
    "warm",
    "keen",
    "swift",
    "bright",
    "quiet",
    "wild",
    "crisp",
    "pale",
    "dark",
    "soft",
    "sharp",
    "cool",
    "odd",
    "rare",
    "slim",
    "tall",
    "deep",
    "gold",
    "iron",
    "blue",
    "red",
    "green",
    "silver",
    "amber",
    "coral",
    "jade",
    "onyx",
]
_NOUNS = [
    "cat",
    "fox",
    "owl",
    "elk",
    "bee",
    "ant",
    "bat",
    "cod",
    "eel",
    "yak",
    "oak",
    "elm",
    "fig",
    "ash",
    "bay",
    "gem",
    "orb",
    "arc",
    "key",
    "bell",
    "star",
    "moon",
    "rain",
    "leaf",
    "wave",
    "fern",
    "moss",
    "pine",
    "crow",
    "hawk",
]


def _gen_codename(existing: set[str]) -> str:
    """Generate a unique adjective-noun codename."""
    for _ in range(50):
        name = f"{random.choice(_ADJECTIVES)}-{random.choice(_NOUNS)}"
        if name not in existing:
            return name
    return f"{random.choice(_ADJECTIVES)}-{random.choice(_NOUNS)}"


def _checkpoint_path(codename: str) -> Path:
    return _CHECKPOINT_DIR / f"checkpoint_{codename}.md"


def _existing_codenames() -> set[str]:
    if not _CHECKPOINT_DIR.exists():
        return set()
    names = set()
    for p in _CHECKPOINT_DIR.glob("checkpoint_*.md"):
        names.add(p.stem[len("checkpoint_") :])
    return names


def _purge_stale() -> list[str]:
    """Delete checkpoints older than 7 days. Returns list of purged codenames."""
    purged = []
    if not _CHECKPOINT_DIR.exists():
        return purged
    cutoff = datetime.now(UTC).timestamp() - (7 * 86400)
    for p in _CHECKPOINT_DIR.glob("checkpoint_*.md"):
        try:
            if p.stat().st_mtime < cutoff:
                p.unlink()
                purged.append(p.stem[len("checkpoint_") :])
        except OSError:
            pass
    return purged


class SporulationSaveResult(Secretion):
    """Result of saving a session checkpoint."""

    codename: str
    path: str
    purged: list[str]


class SporulationLoadResult(Secretion):
    """Result of loading a session checkpoint."""

    codename: str
    content: str
    found: bool


class SporulationListResult(Secretion):
    """Active session checkpoints."""

    checkpoints: list[dict]


@tool(
    name="sporulation_save",
    description="Save a session checkpoint. Returns codename for resume in a new session.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def sporulation_save(
    context: str,
    where_we_left_off: str,
    action_needed: str,
    summary: str = "",
    codename: str = "",
) -> SporulationSaveResult:
    """Compress live session context into a named checkpoint spore.

    Args:
        context: What we were doing (2-3 sentences).
        where_we_left_off: Bullet list of last actions and pending items.
        action_needed: Numbered steps to resume (include tool names, file paths).
        summary: One-line summary for the description field.
        codename: Custom codename (auto-generated if empty).
    """
    _CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    purged = _purge_stale()

    existing = _existing_codenames()
    if not codename:
        codename = _gen_codename(existing)
    elif codename in existing:
        return SporulationSaveResult(
            codename=codename,
            path="",
            purged=purged,
        )

    now = datetime.now(UTC).strftime("%Y-%m-%d ~%H:%M HKT")
    desc = summary or context[:80].strip()
    path = _checkpoint_path(codename)

    content = f"""---
name: {codename} checkpoint
description: Resume point for {desc} ({now})
type: project
---

## Context
{context}

## Where we left off
{where_we_left_off}

## Action needed
{action_needed}

## Passcode: {codename}
"""
    path.write_text(content)
    return SporulationSaveResult(codename=codename, path=str(path), purged=purged)


@tool(
    name="sporulation_load",
    description="Load a session checkpoint by codename. Consumes the spore on success.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def sporulation_load(codename: str, consume: bool = True) -> SporulationLoadResult:
    """Germinate a checkpoint — read it and optionally delete after loading.

    Args:
        codename: The adjective-noun codename (e.g. "happy-cat").
        consume: If True (default), delete the checkpoint after reading.
    """
    path = _checkpoint_path(codename)
    if not path.exists():
        return SporulationLoadResult(codename=codename, content="", found=False)

    content = path.read_text()
    if consume:
        with contextlib.suppress(OSError):
            path.unlink()
    return SporulationLoadResult(codename=codename, content=content, found=True)


@tool(
    name="sporulation_list",
    description="List active session checkpoints with codenames and descriptions.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def sporulation_list() -> SporulationListResult:
    """List all active checkpoint spores."""
    if not _CHECKPOINT_DIR.exists():
        return SporulationListResult(checkpoints=[])

    checkpoints = []
    for p in sorted(_CHECKPOINT_DIR.glob("checkpoint_*.md")):
        codename = p.stem[len("checkpoint_") :]
        desc = ""
        try:
            for line in p.read_text().splitlines():
                if line.startswith("description:"):
                    desc = line.split(":", 1)[1].strip()
                    break
        except OSError:
            pass
        mtime = p.stat().st_mtime
        age_days = (datetime.now(UTC).timestamp() - mtime) / 86400
        checkpoints.append(
            {
                "codename": codename,
                "description": desc,
                "age_days": round(age_days, 1),
            }
        )

    return SporulationListResult(checkpoints=checkpoints)
