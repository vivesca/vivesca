"""Reflexes — automatic responses to lifecycle stimuli.

Resources:
  vivesca://reflexes — inventory of all CC lifecycle hooks
"""

from __future__ import annotations

import json
from pathlib import Path

_SETTINGS = Path.home() / ".claude" / "settings.json"


def _extract_reflex_name(command: str) -> str:
    """Extract a readable hook name from a command string."""
    # e.g. "python3 ~/.claude/hooks/vault-pull.py" -> "vault-pull"
    # e.g. "node ~/.claude/hooks/bash-guard.js" -> "bash-guard"
    parts = command.rsplit("/", 1)
    if len(parts) == 2:
        filename = parts[1]
        # Strip extension
        for ext in (".py", ".js", ".sh"):
            if filename.endswith(ext):
                filename = filename[: -len(ext)]
                break
        return filename
    return command[:40]


def generate_reflex_inventory(settings_path: Path | None = None) -> str:
    """Parse settings.json and build a hooks inventory."""
    path = settings_path or _SETTINGS
    if not path.exists():
        return "No settings.json found."

    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return "Could not parse settings.json."

    hooks = data.get("hooks", {})
    if not hooks:
        return "No hooks configured."

    lines: list[str] = []
    total = 0

    lines.append("# Claude Code Hooks\n")

    for event, groups in hooks.items():
        event_hooks: list[dict] = []
        for group in groups:
            matcher = group.get("matcher", "")
            for h in group.get("hooks", []):
                hook_type = h.get("type", "unknown")
                if hook_type == "command":
                    name = _extract_reflex_name(h.get("command", ""))
                    event_hooks.append(
                        {
                            "name": name,
                            "matcher": matcher,
                            "type": "command",
                        }
                    )
                elif hook_type == "prompt":
                    prompt_text = h.get("prompt", "")[:60]
                    event_hooks.append(
                        {
                            "name": f"[prompt] {prompt_text}...",
                            "matcher": matcher,
                            "type": "prompt",
                        }
                    )

        if event_hooks:
            lines.append(f"## {event} ({len(event_hooks)})\n")
            lines.append("| Hook | Matcher |")
            lines.append("|------|---------|")
            for eh in event_hooks:
                matcher_display = f"`{eh['matcher']}`" if eh["matcher"] else "_(all)_"
                lines.append(f"| `{eh['name']}` | {matcher_display} |")
            lines.append("")
            total += len(event_hooks)

    lines.insert(2, f"_Total: {total} hooks across {len(hooks)} events_\n")

    return "\n".join(lines)
