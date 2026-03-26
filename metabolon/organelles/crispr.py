"""crispr.py — adaptive immunity: spacer-guided failure recognition. No LLM step."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

_SPACER_DIR = Path.home() / ".cache" / "crispr"
_SPACER_FILE = _SPACER_DIR / "spacers.jsonl"
_SELF_PREFIXES = ("inflammasome:", "autoimmunity:")

# (match_re, placeholder_token, regex_fragment)
_SUBS: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r"/[^\s'\"]+"),                   "{path}", r"/[^\s'\"]+"),
    (re.compile(r'"[^"]*"'),                       '"{str}"', r'"[^"]*"'),
    (re.compile(r"'[^']*'"),                       "'{str}'", r"'[^']*'"),
    (re.compile(r"\b([A-Z_][A-Z0-9_]{2,}|_[a-zA-Z_]+)\b"), "{name}", r"[A-Z_][A-Z0-9_]*"),
    (re.compile(r"\b\d+\b"),                       "{n}",    r"\d+"),
]


def _regexify(msg: str) -> tuple[str, str]:
    """Return (pattern, regex) for msg — replace variable tokens with placeholders."""
    pattern = msg
    for sub_re, token, _ in _SUBS:
        pattern = sub_re.sub(token, pattern)
    regex = re.escape(pattern)
    regex = regex.replace(re.escape("{path}"), r"/[^\s'\"]+")
    regex = regex.replace(re.escape("{str}"), r"[^'\"]*")
    regex = regex.replace(re.escape("{name}"), r"[A-Z_][A-Z0-9_]*")
    regex = regex.replace(re.escape("{n}"), r"\d+")
    return pattern, regex


def is_self_test(tool_name: str) -> bool:
    """PAM check — True if tool is a self-test source (never acquire from these)."""
    return any(tool_name.startswith(p) for p in _SELF_PREFIXES)


def acquire_spacer(error_message: str, tool_name: str) -> dict:
    """Capture a novel failure as a spacer. Returns spacer dict (empty if blocked by PAM)."""
    if is_self_test(tool_name):
        return {}
    pattern, regex = _regexify(error_message)
    spacer = {
        "ts": datetime.now(UTC).isoformat(),
        "tool": tool_name,
        "raw_error": error_message,
        "pattern": pattern,
        "regex": regex,
    }
    try:
        _SPACER_DIR.mkdir(parents=True, exist_ok=True)
        with _SPACER_FILE.open("a") as f:
            f.write(json.dumps(spacer) + "\n")
    except Exception:
        pass
    return spacer


def compile_guides() -> list[dict]:
    """Compile spacers into guide RNAs (list of dicts with compiled regex). Skips bad entries."""
    if not _SPACER_FILE.exists():
        return []
    guides: list[dict] = []
    try:
        lines = _SPACER_FILE.read_text().splitlines()
    except Exception:
        return []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            s = json.loads(line)
            compiled = re.compile(s["regex"], re.IGNORECASE)
            guides.append({
                "tool": s.get("tool", ""),
                "pattern": s.get("pattern", ""),
                "regex_compiled": compiled,
                "acquired_ts": s.get("ts", ""),
                "raw_error": s.get("raw_error", ""),
            })
        except Exception:
            continue
    return guides


def scan(error_message: str, tool_name: str = "") -> dict | None:
    """Check error_message against all guides. Returns matching spacer or None (novel)."""
    if tool_name and is_self_test(tool_name):
        return None
    for guide in compile_guides():
        try:
            if guide["regex_compiled"].search(error_message):
                return {k: guide[k] for k in ("tool", "pattern", "acquired_ts", "raw_error")}
        except Exception:
            continue
    return None


def spacer_count() -> int:
    """Number of spacers in the array."""
    if not _SPACER_FILE.exists():
        return 0
    try:
        return sum(1 for ln in _SPACER_FILE.read_text().splitlines() if ln.strip())
    except Exception:
        return 0


def prune_spacers(max_age_days: int = 90) -> int:
    """Remove spacers older than max_age_days. Returns count pruned."""
    if not _SPACER_FILE.exists():
        return 0
    cutoff = datetime.now(UTC) - timedelta(days=max_age_days)
    kept, pruned = [], 0
    try:
        lines = _SPACER_FILE.read_text().splitlines()
    except Exception:
        return 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            s = json.loads(line)
            ts = datetime.fromisoformat(s.get("ts", ""))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=UTC)
            if ts >= cutoff:
                kept.append(line)
            else:
                pruned += 1
        except Exception:
            kept.append(line)
    if pruned:
        try:
            _SPACER_FILE.write_text("\n".join(kept) + ("\n" if kept else ""))
        except Exception:
            pruned = 0
    return pruned
