from __future__ import annotations

"""conjugation_engine — replicate Claude Code configuration to Gemini CLI format.

Conjugation = lateral gene transfer. CC config is the donor; Gemini CLI is the
recipient. The transform is deterministic: event-name remapping + merge-write.

Only `~/.claude/settings.json` → `~/.gemini/settings.json` is supported.
Non-hook/non-MCP fields in the destination are preserved (merge, not overwrite).

Event mapping (CC → Gemini CLI):
    UserPromptSubmit → BeforeModel
    PreToolUse       → BeforeTool
    PostToolUse      → AfterTool
    Stop             → AfterModel

Hook definition structure is identical in both systems:
    {"matcher": "...", "hooks": [{"type": "command", "command": "..."}]}

MCP server structure is identical in both systems.
"""


import json
from pathlib import Path
from typing import Any

# ── paths ────────────────────────────────────────────────────────────────────

CC_SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
GEMINI_SETTINGS_PATH = Path.home() / ".gemini" / "settings.json"

# ── event name mapping ───────────────────────────────────────────────────────

CC_TO_GEMINI_EVENT: dict[str, str] = {
    "UserPromptSubmit": "BeforeModel",
    "PreToolUse": "BeforeTool",
    "PostToolUse": "AfterTool",
    "Stop": "AfterModel",
}

# CC events that have no Gemini CLI equivalent — silently dropped
_CC_UNMAPPED_EVENTS: frozenset[str] = frozenset(
    {
        "Notification",
        "PreCompact",
        "InstructionsLoaded",
    }
)


# ── data structures ──────────────────────────────────────────────────────────


class ConjugationResult:
    """Summary of a conjugation operation."""

    def __init__(
        self,
        hooks_replicated: int,
        mcp_servers_replicated: int,
        hooks_dropped: list[str],
        dry_run: bool,
    ) -> None:
        self.hooks_replicated = hooks_replicated
        self.mcp_servers_replicated = mcp_servers_replicated
        self.hooks_dropped = hooks_dropped
        self.dry_run = dry_run

    @property
    def summary(self) -> str:
        mode = " (dry-run)" if self.dry_run else ""
        parts = [
            f"Replicated {self.hooks_replicated} hook event(s), "
            f"{self.mcp_servers_replicated} MCP server(s){mode}."
        ]
        if self.hooks_dropped:
            dropped = ", ".join(self.hooks_dropped)
            parts.append(f"Dropped unmapped CC events: {dropped}")
        return "  ".join(parts)


# ── readers ──────────────────────────────────────────────────────────────────


def read_cc_settings(path: Path = CC_SETTINGS_PATH) -> dict[str, Any]:
    """Read and parse Claude Code settings.json."""
    if not path.exists():
        return {}
    try:
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return {}


def read_gemini_settings(path: Path = GEMINI_SETTINGS_PATH) -> dict[str, Any]:
    """Read and parse Gemini CLI settings.json. Returns empty dict if absent."""
    if not path.exists():
        return {}
    try:
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return {}


# ── hook transform ───────────────────────────────────────────────────────────


def transform_hooks(
    cc_hooks: dict[str, list[dict[str, Any]]],
) -> tuple[dict[str, list[dict[str, Any]]], list[str], int]:
    """Map CC hook events to Gemini CLI hook events.

    Returns:
        gemini_hooks: dict keyed by Gemini event name
        dropped_events: CC event names with no Gemini equivalent
        total_hooks_mapped: count of individual hook command entries replicated
    """
    gemini_hooks: dict[str, list[dict[str, Any]]] = {}
    dropped_events: list[str] = []
    total_hooks_mapped = 0

    for cc_event, definitions in cc_hooks.items():
        gemini_event = CC_TO_GEMINI_EVENT.get(cc_event)
        if gemini_event is None:
            if cc_event not in _CC_UNMAPPED_EVENTS:
                dropped_events.append(cc_event)
            continue

        # Filter to command-type hooks only — prompt-type have no Gemini equivalent
        command_definitions: list[dict[str, Any]] = []
        for definition in definitions:
            command_hooks = [
                hook_entry
                for hook_entry in definition.get("hooks", [])
                if hook_entry.get("type") == "command"
            ]
            if not command_hooks:
                continue
            mapped_definition: dict[str, Any] = {"hooks": command_hooks}
            matcher = definition.get("matcher")
            if matcher is not None:
                mapped_definition["matcher"] = matcher
            command_definitions.append(mapped_definition)
            total_hooks_mapped += len(command_hooks)

        if command_definitions:
            gemini_hooks[gemini_event] = command_definitions

    return gemini_hooks, dropped_events, total_hooks_mapped


# ── MCP server transform ─────────────────────────────────────────────────────


def transform_mcp_servers(
    cc_mcp_servers: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Copy CC MCP server definitions to Gemini CLI format.

    Both systems use identical structure:
        {"name": {"command": "...", "args": [...]}}
    A shallow copy is sufficient.
    """
    return {name: dict(config) for name, config in cc_mcp_servers.items()}


# ── skills stub ──────────────────────────────────────────────────────────────


def transform_skills(_cc_settings: dict[str, Any]) -> None:
    """Stub: skill mapping not yet implemented."""
    pass


# ── merge write ──────────────────────────────────────────────────────────────


def merge_into_gemini_settings(
    current: dict[str, Any],
    gemini_hooks: dict[str, list[dict[str, Any]]],
    gemini_mcp_servers: dict[str, dict[str, Any]],
    hooks_only: bool = False,
    mcp_only: bool = False,
) -> dict[str, Any]:
    """Merge translated config into existing Gemini settings.

    Non-hook/non-MCP fields in current settings are preserved.
    The hooks and mcpServers sections are fully replaced by the translated values.
    """
    merged = dict(current)

    if not mcp_only and gemini_hooks:
        merged["hooks"] = gemini_hooks

    if not hooks_only and gemini_mcp_servers:
        # Merge MCP servers — preserve existing, add/update from CC
        existing_mcp = merged.get("mcpServers", {})
        existing_mcp.update(gemini_mcp_servers)
        merged["mcpServers"] = existing_mcp

    return merged


def diff_settings(
    current: dict[str, Any],
    proposed: dict[str, Any],
) -> str:
    """Return a human-readable diff of two settings dicts."""
    current_text = json.dumps(current, indent=2, sort_keys=True)
    proposed_text = json.dumps(proposed, indent=2, sort_keys=True)

    if current_text == proposed_text:
        return "(no changes)"

    import difflib

    lines = list(
        difflib.unified_diff(
            current_text.splitlines(keepends=True),
            proposed_text.splitlines(keepends=True),
            fromfile="current ~/.gemini/settings.json",
            tofile="proposed ~/.gemini/settings.json",
        )
    )
    return "".join(lines)


# ── main entry point ─────────────────────────────────────────────────────────


def replicate_to_gemini(
    *,
    hooks_only: bool = False,
    mcp_only: bool = False,
    dry_run: bool = False,
    cc_settings_path: Path = CC_SETTINGS_PATH,
    gemini_settings_path: Path = GEMINI_SETTINGS_PATH,
) -> tuple[ConjugationResult, str]:
    """Replicate CC configuration to Gemini CLI settings.json.

    Returns:
        (result, diff_text) — result is a ConjugationResult summary;
        diff_text is the unified diff (empty string if no changes and not dry-run).
    """
    cc_settings = read_cc_settings(cc_settings_path)
    current_gemini = read_gemini_settings(gemini_settings_path)

    cc_hooks = cc_settings.get("hooks", {})
    cc_mcp_servers = cc_settings.get("mcpServers", {})

    gemini_hooks, dropped_events, hooks_mapped = transform_hooks(cc_hooks)
    gemini_mcp_servers = transform_mcp_servers(cc_mcp_servers)

    proposed = merge_into_gemini_settings(
        current_gemini,
        gemini_hooks,
        gemini_mcp_servers,
        hooks_only=hooks_only,
        mcp_only=mcp_only,
    )

    diff_text = diff_settings(current_gemini, proposed)

    if not dry_run:
        gemini_settings_path.parent.mkdir(parents=True, exist_ok=True)
        with gemini_settings_path.open("w", encoding="utf-8") as fh:
            json.dump(proposed, fh, indent=2)
            fh.write("\n")

    mcp_count = len(gemini_mcp_servers) if not hooks_only else 0
    result = ConjugationResult(
        hooks_replicated=hooks_mapped if not mcp_only else 0,
        mcp_servers_replicated=mcp_count,
        hooks_dropped=dropped_events,
        dry_run=dry_run,
    )
    return result, diff_text
