from __future__ import annotations

"""sporulation — cross-session checkpoint save/load.

A bacterium sporulates when conditions turn hostile: it compresses its essential
DNA into a compact, resistant spore. Same here — compress live context into a
checkpoint, germinate in a fresh session.
"""


import contextlib
import random
from datetime import UTC, datetime
from pathlib import Path

from fastmcp.tools.function_tool import tool
from mcp.types import ToolAnnotations

from metabolon.morphology import Secretion, resolve_memory_dir

_CHECKPOINT_DIR = resolve_memory_dir()

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


def _save(
    context: str,
    where_we_left_off: str,
    action_needed: str,
    summary: str = "",
    codename: str = "",
) -> SporulationSaveResult:
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


def _load(codename: str, consume: bool = True) -> SporulationLoadResult:
    path = _checkpoint_path(codename)
    if not path.exists():
        return SporulationLoadResult(codename=codename, content="", found=False)

    content = path.read_text()
    if consume:
        with contextlib.suppress(OSError):
            path.unlink()
    return SporulationLoadResult(codename=codename, content=content, found=True)


def _list() -> SporulationListResult:
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


@tool(
    name="sporulation",
    description="Session checkpoints. Actions: save|load|list",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def sporulation(
    action: str,
    context: str = "",
    where_we_left_off: str = "",
    action_needed: str = "",
    summary: str = "",
    codename: str = "",
    consume: bool = True,
) -> SporulationSaveResult | SporulationLoadResult | SporulationListResult | str:
    """Manage cross-session checkpoint spores.

    Actions:
      save — compress live session context into a named checkpoint.
        context: What we were doing (2-3 sentences).
        where_we_left_off: Bullet list of last actions and pending items.
        action_needed: Numbered steps to resume (include tool names, file paths).
        summary: One-line summary for the description field.
        codename: Custom codename (auto-generated if empty).

      load — germinate a checkpoint by codename.
        codename: The adjective-noun codename (e.g. "happy-cat").
        consume: If True (default), delete the checkpoint after reading.

      list — list all active checkpoint spores.
    """
    if action == "save":
        return _save(
            context=context,
            where_we_left_off=where_we_left_off,
            action_needed=action_needed,
            summary=summary,
            codename=codename,
        )
    elif action == "load":
        return _load(codename=codename, consume=consume)
    elif action == "list":
        return _list()
    else:
        return f"Unknown action '{action}'. Use save, load, or list."
