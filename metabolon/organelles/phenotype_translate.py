from __future__ import annotations

"""phenotype_translate — generate Gemini CLI hook config from Claude Code hook config.

Reads ~/.claude/settings.json (or a given path), extracts the hooks section,
translates event names and command wrappers, and outputs a valid Gemini CLI
hooks section. Optionally merges into ~/.gemini/settings.json.

Event name mapping (CC → Gemini CLI):
    UserPromptSubmit → BeforeAgent
    PreToolUse       → BeforeTool
    PostToolUse      → AfterTool
    Stop             → AfterAgent
    Notification     → Notification   (same)
    PreCompact       → PreCompress

For each hook command that points to a synaptic/*.py script the command is
wrapped with gemini_adapter.py so the existing hook script receives CC-format
stdin and its CC-format stdout is translated back to Gemini CLI format at
runtime — without modifying the hook scripts themselves.

This is deliberately separate from conjugation_engine (which does a simpler
pass-through). phenotype_translate adds the runtime adapter layer.
"""


import json
import warnings
from pathlib import Path
from typing import Any

# ── paths ────────────────────────────────────────────────────────────────────

CC_SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
GEMINI_SETTINGS_PATH = Path.home() / ".gemini" / "settings.json"

# gemini_adapter.py lives next to the synaptic hook scripts
_SYNAPTIC_DIR = Path(__file__).resolve().parent.parent.parent / "synaptic"
GEMINI_ADAPTER_PATH = _SYNAPTIC_DIR / "gemini_adapter.py"

# ── event name mapping ───────────────────────────────────────────────────────

CC_TO_GEMINI_EVENT: dict[str, str] = {
    "UserPromptSubmit": "BeforeAgent",
    "PreToolUse": "BeforeTool",
    "PostToolUse": "AfterTool",
    "Stop": "AfterAgent",
    "Notification": "Notification",
    "PreCompact": "PreCompress",
}

# CC events silently dropped (no Gemini equivalent, not worth warning about)
_CC_SILENTLY_DROPPED: frozenset[str] = frozenset({"InstructionsLoaded"})


# ── command wrapping ─────────────────────────────────────────────────────────


def _is_synaptic_script(command: str) -> bool:
    """Return True if the command invokes a synaptic/*.py hook script.

    Matches patterns like:
        python3 ~/.claude/hooks/synapse.py
        python3 ~/germline/synaptic/axon.py
        /usr/bin/python3 ~/.claude/hooks/dendrite.py
    """
    parts = command.strip().split()
    if not parts:
        return False
    # Find the script argument (first .py arg)
    for part in parts:
        if part.endswith(".py"):
            p = Path(part.replace("~", str(Path.home())))
            name = p.name
            parent = p.parent.name
            # Match if it's in hooks/ or synaptic/ directory
            if parent in ("hooks", "synaptic"):
                return True
    return False


def _wrap_command(command: str, adapter_path: Path) -> str:
    """Wrap a hook command to run through gemini_adapter.py.

    Before wrapping:
        python3 ~/.claude/hooks/synapse.py

    After wrapping:
        python3 /path/to/gemini_adapter.py ~/.claude/hooks/synapse.py
    """
    parts = command.strip().split(None, 1)  # split into interpreter + rest
    if not parts:
        return command

    # Find python3 / python interpreter prefix
    interpreter = ""
    script_and_args = command.strip()

    # Detect interpreter (python3, python, /usr/bin/python3, etc.)
    first = parts[0]
    if "python" in first.lower() or first in ("/usr/bin/env",):
        interpreter = first
        rest = parts[1] if len(parts) > 1 else ""
        script_and_args = rest
    else:
        # Non-python command — wrap anyway; adapter accepts any script via python3
        interpreter = "python3"
        script_and_args = command.strip()

    adapter_str = str(adapter_path)
    return f"{interpreter} {adapter_str} {script_and_args}".strip()


# ── hook transform ───────────────────────────────────────────────────────────


class TranslationResult:
    """Summary of a phenotype translation operation."""

    def __init__(
        self,
        hooks_translated: int,
        hooks_wrapped: int,
        prompt_hooks_skipped: int,
        events_dropped: list[str],
        dry_run: bool,
    ) -> None:
        self.hooks_translated = hooks_translated
        self.hooks_wrapped = hooks_wrapped
        self.prompt_hooks_skipped = prompt_hooks_skipped
        self.events_dropped = events_dropped
        self.dry_run = dry_run

    @property
    def summary(self) -> str:
        mode = " (dry-run)" if self.dry_run else ""
        parts = [
            f"Translated {self.hooks_translated} hook(s){mode}.",
            f"Wrapped {self.hooks_wrapped} synaptic script(s) with gemini_adapter.",
        ]
        if self.prompt_hooks_skipped:
            parts.append(f"Skipped {self.prompt_hooks_skipped} prompt-type hook(s) (unsupported).")
        if self.events_dropped:
            parts.append(f"Dropped unknown CC events: {', '.join(self.events_dropped)}.")
        return "  ".join(parts)


def translate_hooks(
    cc_hooks: dict[str, list[dict[str, Any]]],
    adapter_path: Path = GEMINI_ADAPTER_PATH,
    wrap: bool = True,
) -> tuple[dict[str, list[dict[str, Any]]], TranslationResult]:
    """Translate CC hooks section to Gemini CLI hooks section.

    Args:
        cc_hooks: The ``hooks`` dict from ~/.claude/settings.json.
        adapter_path: Path to gemini_adapter.py for command wrapping.
        wrap: If True, wrap synaptic/*.py commands with gemini_adapter.

    Returns:
        (gemini_hooks, result) — the translated hooks dict and a summary.
    """
    gemini_hooks: dict[str, list[dict[str, Any]]] = {}
    hooks_translated = 0
    hooks_wrapped = 0
    prompt_hooks_skipped = 0
    events_dropped: list[str] = []

    for cc_event, definitions in cc_hooks.items():
        gemini_event = CC_TO_GEMINI_EVENT.get(cc_event)

        if gemini_event is None:
            if cc_event not in _CC_SILENTLY_DROPPED:
                events_dropped.append(cc_event)
            continue

        translated_definitions: list[dict[str, Any]] = []

        for definition in definitions:
            translated_hooks_list: list[dict[str, Any]] = []

            for hook_entry in definition.get("hooks", []):
                hook_type = hook_entry.get("type", "")

                if hook_type == "prompt":
                    # Gemini CLI has no prompt-type hooks
                    warnings.warn(
                        f"[phenotype_translate] Skipping prompt-type hook in {cc_event} "
                        f"— Gemini CLI does not support prompt-type hooks.",
                        UserWarning,
                        stacklevel=2,
                    )
                    prompt_hooks_skipped += 1
                    continue

                if hook_type != "command":
                    # Unknown hook type — skip
                    continue

                command = hook_entry.get("command", "")
                new_entry: dict[str, Any] = dict(hook_entry)

                if wrap and _is_synaptic_script(command):
                    new_entry["command"] = _wrap_command(command, adapter_path)
                    hooks_wrapped += 1

                translated_hooks_list.append(new_entry)
                hooks_translated += 1

            if not translated_hooks_list:
                continue

            mapped_def: dict[str, Any] = {"hooks": translated_hooks_list}
            # Preserve matcher if present
            matcher = definition.get("matcher")
            if matcher is not None:
                mapped_def["matcher"] = matcher

            translated_definitions.append(mapped_def)

        if translated_definitions:
            gemini_hooks[gemini_event] = translated_definitions

    result = TranslationResult(
        hooks_translated=hooks_translated,
        hooks_wrapped=hooks_wrapped,
        prompt_hooks_skipped=prompt_hooks_skipped,
        events_dropped=events_dropped,
        dry_run=False,  # updated by caller
    )
    return gemini_hooks, result


# ── settings I/O ─────────────────────────────────────────────────────────────


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
    """Read existing Gemini CLI settings.json. Returns empty dict if absent."""
    if not path.exists():
        return {}
    try:
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return {}


def merge_hooks_into_gemini(
    current: dict[str, Any],
    gemini_hooks: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    """Merge translated hooks into existing Gemini settings dict.

    Replaces only the 'hooks' key; all other fields are preserved.
    """
    merged = dict(current)
    if gemini_hooks:
        merged["hooks"] = gemini_hooks
    return merged


def diff_settings(current: dict[str, Any], proposed: dict[str, Any]) -> str:
    """Return a human-readable unified diff of two settings dicts."""
    import difflib

    current_text = json.dumps(current, indent=2, sort_keys=True)
    proposed_text = json.dumps(proposed, indent=2, sort_keys=True)

    if current_text == proposed_text:
        return "(no changes)"

    lines = list(
        difflib.unified_diff(
            current_text.splitlines(keepends=True),
            proposed_text.splitlines(keepends=True),
            fromfile="current ~/.gemini/settings.json",
            tofile="proposed ~/.gemini/settings.json",
        )
    )
    return "".join(lines)


# ── phenotype sync ───────────────────────────────────────────────────────────


class SyncResult:
    """Summary of a phenotype sync operation."""

    def __init__(
        self,
        symlinks_ok: list[str],
        symlinks_fixed: list[str],
        symlinks_failed: list[str],
        hooks_result: TranslationResult | None,
        gemini_md_ok: bool,
        integrin_issues: list[dict],
        unknown_platforms: list[str],
        dry_run: bool,
        skills_synced: int = 0,
    ) -> None:
        self.symlinks_ok = symlinks_ok
        self.symlinks_fixed = symlinks_fixed
        self.symlinks_failed = symlinks_failed
        self.hooks_result = hooks_result
        self.gemini_md_ok = gemini_md_ok
        self.integrin_issues = integrin_issues
        self.unknown_platforms = unknown_platforms
        self.dry_run = dry_run
        self.skills_synced = skills_synced

    @property
    def ok(self) -> bool:
        return (
            not self.symlinks_failed
            and not self.integrin_issues
            and self.gemini_md_ok
        )

    @property
    def summary(self) -> str:
        mode = " (dry-run)" if self.dry_run else ""
        lines: list[str] = []

        # Symlinks
        total = len(self.symlinks_ok) + len(self.symlinks_fixed) + len(self.symlinks_failed)
        if self.symlinks_fixed:
            lines.append(
                f"Symlinks{mode}: {len(self.symlinks_ok)} ok, "
                f"{len(self.symlinks_fixed)} fixed: {', '.join(self.symlinks_fixed)}"
            )
        elif self.symlinks_failed:
            lines.append(
                f"Symlinks{mode}: {len(self.symlinks_ok)}/{total} ok — "
                f"FAILED: {', '.join(self.symlinks_failed)}"
            )
        else:
            lines.append(f"Symlinks{mode}: {total} ok.")

        # Hook translation
        if self.hooks_result is not None:
            lines.append(f"Hooks{mode}: {self.hooks_result.summary}")
        else:
            lines.append(f"Hooks{mode}: skipped (no CC settings found).")

        # Skills
        lines.append(f"Skills{mode}: {self.skills_synced} synced to ~/.agents/skills/ + ~/.claude/skills/.")

        # GEMINI.md
        status = "ok" if self.gemini_md_ok else "MISSING or wrong target"
        lines.append(f"GEMINI.md{mode}: {status}.")

        # Integrin verification
        if self.integrin_issues:
            issues_desc = "; ".join(
                f"{i['path']} ({i['problem']})" for i in self.integrin_issues
            )
            lines.append(f"Integrin{mode}: issues — {issues_desc}")
        else:
            lines.append(f"Integrin{mode}: all checks pass.")

        # Unknown platforms
        if self.unknown_platforms:
            lines.append(
                f"Unknown platforms detected: {', '.join(self.unknown_platforms)} "
                f"(add to PLATFORM_SYMLINKS in locus.py)."
            )

        return "\n".join(lines)


def _ensure_symlink(symlink_path: Path, target: Path, dry_run: bool) -> str:
    """Ensure symlink_path → target exists and is correct.

    Returns 'ok', 'fixed', or 'failed'.
    """
    try:
        if symlink_path.is_symlink():
            if symlink_path.resolve() == target.resolve():
                return "ok"
            # Wrong target — remove and recreate
            if not dry_run:
                symlink_path.unlink()
                symlink_path.symlink_to(target)
            return "fixed"
        elif symlink_path.exists():
            # Regular file in the way — cannot safely replace
            return "failed"
        else:
            # Missing — create
            if not dry_run:
                symlink_path.parent.mkdir(parents=True, exist_ok=True)
                symlink_path.symlink_to(target)
            return "fixed"
    except OSError:
        return "failed"


def sync_phenotype(
    *,
    dry_run: bool = False,
    cc_settings_path: Path = CC_SETTINGS_PATH,
    gemini_settings_path: Path = GEMINI_SETTINGS_PATH,
    adapter_path: Path = GEMINI_ADAPTER_PATH,
    wrap: bool = True,
) -> SyncResult:
    """Ensure all LLM CLI platforms express the organism's identity.

    Steps (in order):
    1. Symlinks  — verify/create PLATFORM_SYMLINKS → phenotype_md.
    2. Hooks     — translate CC hooks → Gemini CLI hooks (unless dry_run).
    3. GEMINI.md — verify ~/.gemini/GEMINI.md → phenotype_md.
    4. Integrin  — call _check_phenotype_symlinks() for final verification.

    Args:
        dry_run: Report what would change without writing anything.
        cc_settings_path: Source CC settings.json.
        gemini_settings_path: Destination Gemini CLI settings.json.
        adapter_path: Path to gemini_adapter.py.
        wrap: Wrap synaptic/*.py commands with gemini_adapter.

    Returns:
        SyncResult with full status.
    """
    from metabolon.locus import PLATFORM_SYMLINKS, phenotype_md
    from metabolon.enzymes.integrin import _check_phenotype_symlinks

    # ── step 1: symlinks ─────────────────────────────────────────────
    symlinks_ok: list[str] = []
    symlinks_fixed: list[str] = []
    symlinks_failed: list[str] = []

    for symlink_path in PLATFORM_SYMLINKS:
        outcome = _ensure_symlink(symlink_path, phenotype_md, dry_run=dry_run)
        label = str(symlink_path)
        if outcome == "ok":
            symlinks_ok.append(label)
        elif outcome == "fixed":
            symlinks_fixed.append(label)
        else:
            symlinks_failed.append(label)

    # ── step 2: hook translation ─────────────────────────────────────
    hooks_result: TranslationResult | None = None
    if cc_settings_path.exists():
        cc_settings = read_cc_settings(cc_settings_path)
        cc_hooks = cc_settings.get("hooks", {})
        current_gemini = read_gemini_settings(gemini_settings_path)
        gemini_hooks, hooks_result = translate_hooks(
            cc_hooks, adapter_path=adapter_path, wrap=wrap
        )
        hooks_result.dry_run = dry_run
        if not dry_run:
            proposed = merge_hooks_into_gemini(current_gemini, gemini_hooks)
            gemini_settings_path.parent.mkdir(parents=True, exist_ok=True)
            with gemini_settings_path.open("w", encoding="utf-8") as fh:
                import json as _json
                _json.dump(proposed, fh, indent=2)
                fh.write("\n")

    # ── step 2.5: skill symlinking ────────────────────────────────────
    # Sync receptors → ~/.agents/skills/ (Gemini + Codex) and ~/.claude/skills/ (CC).
    # Gemini/Codex auto-discover ~/.agents/skills/; CC only reads ~/.claude/skills/.
    from metabolon.locus import receptors

    skill_targets = [
        Path.home() / ".agents" / "skills",
        Path.home() / ".claude" / "skills",
    ]
    skills_synced = 0
    if receptors.is_dir():
        for skills_dir in skill_targets:
            if not dry_run:
                skills_dir.mkdir(parents=True, exist_ok=True)
            for skill_dir in sorted(receptors.iterdir()):
                skill_file = skill_dir / "SKILL.md"
                if not skill_file.is_file():
                    continue
                target_link = skills_dir / skill_dir.name
                if target_link.is_symlink() and target_link.resolve() == skill_dir.resolve():
                    skills_synced += 1
                    continue
                if not dry_run:
                    target_link.unlink(missing_ok=True)
                    target_link.symlink_to(skill_dir)
                skills_synced += 1

    # ── step 3: GEMINI.md check ────────────────────────────────────────
    gemini_md_path = Path.home() / ".gemini" / "GEMINI.md"
    gemini_md_ok = (
        gemini_md_path.is_symlink()
        and gemini_md_path.resolve() == phenotype_md.resolve()
    )

    # ── step 4: integrin verification ────────────────────────────────
    integrin_issues, unknown_platforms = _check_phenotype_symlinks()

    return SyncResult(
        symlinks_ok=symlinks_ok,
        symlinks_fixed=symlinks_fixed,
        symlinks_failed=symlinks_failed,
        hooks_result=hooks_result,
        gemini_md_ok=gemini_md_ok,
        integrin_issues=integrin_issues,
        unknown_platforms=unknown_platforms,
        dry_run=dry_run,
        skills_synced=skills_synced,
    )


# ── main entry point ─────────────────────────────────────────────────────────


def translate_to_gemini(
    *,
    cc_settings_path: Path = CC_SETTINGS_PATH,
    gemini_settings_path: Path = GEMINI_SETTINGS_PATH,
    adapter_path: Path = GEMINI_ADAPTER_PATH,
    wrap: bool = True,
    dry_run: bool = False,
) -> tuple[TranslationResult, str]:
    """Translate CC hooks to Gemini CLI format and optionally merge to disk.

    Args:
        cc_settings_path: Source CC settings file.
        gemini_settings_path: Destination Gemini CLI settings file.
        adapter_path: Path to gemini_adapter.py for command wrapping.
        wrap: Wrap synaptic/*.py commands with gemini_adapter (default True).
        dry_run: Compute diff without writing to disk.

    Returns:
        (result, diff_text) where diff_text is the unified diff string.
    """
    cc_settings = read_cc_settings(cc_settings_path)
    current_gemini = read_gemini_settings(gemini_settings_path)

    cc_hooks = cc_settings.get("hooks", {})
    gemini_hooks, result = translate_hooks(cc_hooks, adapter_path=adapter_path, wrap=wrap)
    result.dry_run = dry_run

    proposed = merge_hooks_into_gemini(current_gemini, gemini_hooks)
    diff_text = diff_settings(current_gemini, proposed)

    if not dry_run:
        gemini_settings_path.parent.mkdir(parents=True, exist_ok=True)
        with gemini_settings_path.open("w", encoding="utf-8") as fh:
            json.dump(proposed, fh, indent=2)
            fh.write("\n")

    return result, diff_text
