"""Coaching file injection — prepends structured feedback to worker prompts."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def inject_coaching(prompt: str, coaching_file: Path | None) -> str:
    """Prepend coaching notes to a prompt. Returns prompt unchanged if no file."""
    if coaching_file is None or not coaching_file.exists():
        return prompt
    coaching_content = coaching_file.read_text(encoding="utf-8").strip()
    if not coaching_content:
        return prompt
    return f"<coaching-notes>\n{coaching_content}\n</coaching-notes>\n\n{prompt}"
