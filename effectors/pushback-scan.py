#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Pushback scan — Eugene Yan's pattern (eugeneyan.com May 2026).

Walks Claude Code session JSONL files, extracts pure user prompts (skipping
tool_result entries and hook-injected content), counts recurring correction
phrases, and prints a ranked list with sample turns.

Output feeds methylation: phrases with high hit counts mark CLAUDE.md gaps
where the model failed often enough that Terry corrected it explicitly.

Usage:
  pushback-scan.py                  # 30-day window, all projects
  pushback-scan.py --days 90
  pushback-scan.py --stats-only
  pushback-scan.py --add "argh,seriously?"   # ad-hoc extra phrases
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path

DEFAULT_PHRASES: tuple[str, ...] = (
    "still wrong",
    "did you check",
    "did you read",
    "did you actually",
    "are you sure",
    "you didn't",
    "i told you",
    "i already",
    "that's not",
    "thats not",
    "actually,",
    "again,",
    "you said",
    "no, ",
    "nope",
    "wrong.",
    "can you also",
    "stop ",
    "don't ",
    "?? ",
    "why did you",
    "why are you",
    "i asked you",
)

HOOK_MARKERS = (
    "<system-reminder>",
    "UserPromptSubmit hook",
    "<command-name>",
    "<persisted-output>",
    "[Request interrupted",
    "<bash-stdout>",
    "<local-command-stdout>",
)

# Real Terry-typed pushback is terse. Long "user" entries are sub-agent
# dispatch payloads, skill bodies injected by Skill tool, or council prompts.
MAX_USER_TURN_CHARS = 600

DISPATCH_PREFIXES = (
    "You are ",
    "Base directory for this skill",
    "Base directory:",
    "<task>",
    "<coaching-notes>",
)

DISPATCH_MARKERS = (
    "GROUNDING RULE:",
    "Your task is to",
    "auto memory",
    "council deliberation",
    "subagent_type",
)


def looks_like_dispatch(text: str) -> bool:
    if len(text) > MAX_USER_TURN_CHARS:
        return True
    stripped = text.lstrip()
    if any(stripped.startswith(p) for p in DISPATCH_PREFIXES):
        return True
    return any(m in text for m in DISPATCH_MARKERS)


def extract_user_text(entry: dict) -> str | None:
    if entry.get("type") != "user":
        return None
    msg = entry.get("message") or {}
    content = msg.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        # Drop tool_result entries — those are model-input, not user pushback.
        if any(item.get("type") == "tool_result" for item in content):
            return None
        parts = [item.get("text", "") for item in content if isinstance(item, dict)]
        joined = "\n".join(p for p in parts if p)
        return joined or None
    return None


def is_hook_injected(text: str) -> bool:
    return any(m in text for m in HOOK_MARKERS)


def scan(projects_root: Path, cutoff: datetime, phrases: tuple[str, ...]):
    counts: dict[str, int] = defaultdict(int)
    samples: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    total_turns = 0
    sessions_seen: set[str] = set()

    for jsonl in projects_root.rglob("*.jsonl"):
        try:
            mtime = datetime.fromtimestamp(jsonl.stat().st_mtime, tz=UTC)
        except OSError:
            continue
        if mtime < cutoff:
            continue

        session_id = jsonl.stem[:8]
        date_str = mtime.astimezone().strftime("%Y-%m-%d")

        try:
            with jsonl.open("r", errors="replace") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    text = extract_user_text(entry)
                    if not text or is_hook_injected(text) or looks_like_dispatch(text):
                        continue
                    total_turns += 1
                    sessions_seen.add(session_id)
                    lowered = text.lower()
                    for phrase in phrases:
                        if phrase in lowered:
                            counts[phrase] += 1
                            if len(samples[phrase]) < 3:
                                snippet = text.strip().replace("\n", " ")[:240]
                                samples[phrase].append((date_str, session_id, snippet))
        except OSError:
            continue

    return counts, samples, total_turns, len(sessions_seen)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Pushback phrase scan over Claude Code transcripts."
    )
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--stats-only", action="store_true")
    parser.add_argument("--add", default="", help="comma-separated extra phrases")
    parser.add_argument(
        "--projects",
        type=Path,
        default=Path.home() / ".claude" / "projects",
        help="Claude projects root",
    )
    args = parser.parse_args()

    extra = tuple(p.strip().lower() for p in args.add.split(",") if p.strip())
    phrases = DEFAULT_PHRASES + extra

    if not args.projects.exists():
        print(f"No projects dir at {args.projects}", file=sys.stderr)
        return 1

    cutoff = datetime.now(UTC) - timedelta(days=args.days)
    counts, samples, total_turns, sessions = scan(args.projects, cutoff, phrases)

    print(f"Pushback scan — last {args.days} days  ({args.projects})")
    print(f"Sessions touched:   {sessions}")
    print(f"User turns scanned: {total_turns}")
    print()

    ranked = sorted(((p, c) for p, c in counts.items() if c > 0), key=lambda x: -x[1])
    if not ranked:
        print("No matches.")
        return 0

    width = max(len(p) for p, _ in ranked)
    print(f"  {'phrase'.ljust(width)}  {'hits':>5}  rate")
    print(f"  {'-' * width}  {'-' * 5}  ----")
    denom = max(total_turns, 1)
    for phrase, count in ranked:
        pct = (count / denom) * 100.0
        print(f"  {phrase.ljust(width)}  {count:>5}  {pct:5.2f}%")

    if args.stats_only:
        return 0

    print()
    print("Sample turns (top 5 phrases, up to 3 each):")
    for phrase, _ in ranked[:5]:
        for date_str, session_id, snippet in samples[phrase]:
            print()
            print(f"=== {date_str} [{session_id}]  «{phrase}» ===")
            print(snippet)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
