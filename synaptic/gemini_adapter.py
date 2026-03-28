#!/usr/bin/env python3
"""gemini_adapter.py — runtime bridge between Gemini CLI hook format and CC hook format.

Usage:
    python3 gemini_adapter.py <hook_script.py> [extra args...]

Gemini CLI calls this script as the hook command, passing its JSON on stdin.
The adapter:
  1. Reads Gemini CLI stdin JSON
  2. Translates field names to CC format
  3. Calls the original hook script via subprocess, piping the CC JSON on its stdin
  4. Reads the hook script's stdout
  5. Translates the CC output back to Gemini CLI format on stdout

Stdin field mapping (Gemini CLI → CC):
  BeforeAgent event:
    message.content     → prompt + message.content
    session_id          → session_id (preserved)

  BeforeTool / AfterTool event:
    tool.name           → tool
    tool.input          → tool_input
    tool_response       → tool_response (AfterTool only, preserved)

Stdout field mapping (CC → Gemini CLI):
  {"decision": "block", "reason": "..."}
      → {"decision": "deny", "reason": "..."}
  {"output": "..."}
      → {"hookSpecificOutput": {"additionalContext": "..."}}
  plain text (non-JSON stdout)
      → {"hookSpecificOutput": {"additionalContext": "<text>"}}
  {"type": "prompt", ...}
      → skipped with a warning to stderr (Gemini CLI has no prompt-type hooks)

Events that have no CC equivalent (Notification, PreCompress) are passed through
with a no-op (exit 0, no output) so the hook does not error.
"""

from __future__ import annotations

import json
import subprocess
import sys
import warnings
from pathlib import Path

# ── Gemini CLI → CC event name map ───────────────────────────────────────────

GEMINI_TO_CC_EVENT: dict[str, str] = {
    "BeforeAgent": "UserPromptSubmit",
    "BeforeTool": "PreToolUse",
    "AfterTool": "PostToolUse",
    "AfterAgent": "Stop",
    "Notification": "Notification",
    "PreCompress": "PreCompact",
}

# Events with no meaningful CC hook equivalent — pass through as no-op
_NOOP_EVENTS: frozenset[str] = frozenset({"Notification", "PreCompress"})


# ── stdin translation: Gemini CLI → CC ───────────────────────────────────────


def translate_gemini_to_cc(gemini_data: dict) -> dict:
    """Translate Gemini CLI hook stdin JSON to CC hook stdin JSON.

    Returns a new dict suitable for piping to an existing CC hook script.
    Preserves all unmapped keys so hooks can access them if needed.
    """
    cc = dict(gemini_data)

    event = gemini_data.get("event", "")

    if event == "BeforeAgent":
        # Gemini: {"event": "BeforeAgent", "session_id": "...", "message": {"content": "..."}}
        # CC:     {"session_id": "...", "prompt": "...", "message": {...}}
        msg = gemini_data.get("message", {})
        content = msg.get("content", "") if isinstance(msg, dict) else ""
        cc["prompt"] = content
        # Keep "message" as-is for hooks that read data["message"]["content"]

    elif event in ("BeforeTool", "AfterTool"):
        # Gemini: {"event": "BeforeTool", "tool": {"name": "Bash", "input": {...}}}
        # CC:     {"tool": "Bash", "tool_input": {...}}
        tool_obj = gemini_data.get("tool", {})
        if isinstance(tool_obj, dict):
            cc["tool"] = tool_obj.get("name", "")
            cc["tool_input"] = tool_obj.get("input", {})
        else:
            cc["tool"] = str(tool_obj)
            cc["tool_input"] = {}
        # tool_response is already at the top level in both formats

    elif event == "AfterAgent":
        # Gemini: {"event": "AfterAgent", "session_id": "..."}
        # CC Stop: {"session_id": "..."} — nothing extra needed
        pass

    # Remove the "event" key — CC hooks don't use it
    cc.pop("event", None)

    return cc


# ── stdout translation: CC → Gemini CLI ──────────────────────────────────────


def translate_cc_to_gemini(raw_output: str) -> str | None:
    """Translate CC hook stdout to Gemini CLI hook stdout.

    Returns:
        JSON string to write to stdout, or None if output should be suppressed.

    CC output forms handled:
      1. Empty / whitespace → None (no output)
      2. JSON with {"decision": "block"} → {"decision": "deny", "reason": "..."}
      3. JSON with {"output": "..."} → hookSpecificOutput.additionalContext
      4. JSON with {"type": "prompt"} → None (warn to stderr, Gemini unsupported)
      5. JSON with {"decision": "allow"} or {"decision": "approve"} → None (allow silently)
      6. Plain text (non-JSON) → hookSpecificOutput.additionalContext
      7. Any other JSON → hookSpecificOutput.additionalContext (json-stringified)
    """
    stripped = raw_output.strip()
    if not stripped:
        return None

    # Attempt JSON parse
    parsed = None
    try:
        parsed = json.loads(stripped)
    except (json.JSONDecodeError, ValueError):
        pass

    if parsed is None:
        # Plain text output — wrap as context injection
        return json.dumps({"hookSpecificOutput": {"additionalContext": stripped}})

    if not isinstance(parsed, dict):
        # JSON array or scalar — treat as context
        return json.dumps({"hookSpecificOutput": {"additionalContext": stripped}})

    # prompt-type: not supported by Gemini CLI
    if parsed.get("type") == "prompt":
        print(
            "[gemini_adapter] WARNING: CC hook emitted type=prompt — "
            "Gemini CLI has no prompt-type hooks. Skipping.",
            file=sys.stderr,
        )
        return None

    # Block decision
    decision = parsed.get("decision", "")
    if decision == "block":
        gemini: dict = {"decision": "deny"}
        reason = parsed.get("reason", "")
        if reason:
            gemini["reason"] = reason
        return json.dumps(gemini)

    # Allow/approve decisions — pass through silently
    if decision in ("allow", "approve"):
        return None

    # CC context injection: {"output": "..."}
    if "output" in parsed:
        context = parsed["output"]
        return json.dumps({"hookSpecificOutput": {"additionalContext": str(context)}})

    # hookSpecificOutput already present (hook may output native CC format)
    if "hookSpecificOutput" in parsed:
        # Pass through as-is — already in a Gemini-compatible shape
        return stripped

    # Fallback: stringify the entire JSON as context
    return json.dumps({"hookSpecificOutput": {"additionalContext": stripped}})


# ── main ─────────────────────────────────────────────────────────────────────


def run(hook_script: str, extra_args: list[str], gemini_data: dict) -> int:
    """Run the hook script with translated stdin and translate its stdout.

    Returns the exit code from the hook script (0 = allow/continue).
    """
    event = gemini_data.get("event", "")

    # No-op events — just exit 0 silently
    if event in _NOOP_EVENTS:
        return 0

    cc_data = translate_gemini_to_cc(gemini_data)
    cc_stdin = json.dumps(cc_data).encode()

    cmd = [sys.executable, hook_script] + extra_args
    try:
        result = subprocess.run(
            cmd,
            input=cc_stdin,
            capture_output=True,
            timeout=30,
        )
    except FileNotFoundError:
        print(
            f"[gemini_adapter] ERROR: hook script not found: {hook_script}",
            file=sys.stderr,
        )
        return 1
    except subprocess.TimeoutExpired:
        print(
            f"[gemini_adapter] ERROR: hook script timed out: {hook_script}",
            file=sys.stderr,
        )
        return 1

    # Forward hook's stderr to our stderr (for debugging)
    if result.stderr:
        sys.stderr.buffer.write(result.stderr)

    # Translate stdout
    raw_output = result.stdout.decode(errors="replace")
    gemini_output = translate_cc_to_gemini(raw_output)
    if gemini_output is not None:
        print(gemini_output)

    # Propagate exit code — hook scripts exit non-zero to block
    return result.returncode


def main() -> None:
    if len(sys.argv) < 2:
        print(
            "Usage: python3 gemini_adapter.py <hook_script.py> [extra args...]",
            file=sys.stderr,
        )
        sys.exit(1)

    hook_script = sys.argv[1]
    extra_args = sys.argv[2:]

    # Resolve relative paths against the script's directory
    if not Path(hook_script).is_absolute():
        hook_script = str(Path(__file__).parent / hook_script)

    try:
        raw = sys.stdin.read()
        gemini_data = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"[gemini_adapter] ERROR: invalid JSON on stdin: {exc}", file=sys.stderr)
        sys.exit(1)

    exit_code = run(hook_script, extra_args, gemini_data)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
