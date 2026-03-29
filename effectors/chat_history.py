#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""
Scan and search Claude Code chat history with proper HKT (UTC+8) day boundaries.

Usage:
    python chat_history.py                          # Today's prompts
    python chat_history.py yesterday                # Yesterday's prompts
    python chat_history.py 2026-01-23               # Specific date
    python chat_history.py --full                   # Show all prompts (not just last 50)
    python chat_history.py --json                   # Output as JSON

Search (prompts only — fast):
    python chat_history.py --search="self-intro"                # Last 7 days
    python chat_history.py --search="DBS" --days=30             # Last 30 days
    python chat_history.py --search="DBS" 2026-02-15            # Specific date

Search (full transcripts — slower, searches both user + assistant):
    python chat_history.py --search="self-intro" --deep         # Last 7 days
    python chat_history.py --search="DBS" --deep --days=30      # Last 30 days
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Dict, Any

HKT = timezone(timedelta(hours=8))
HISTORY_FILES = {
    "Claude": Path.home() / ".claude" / "history.jsonl",
    "Codex": Path.home() / ".codex" / "history.jsonl",
}
PROJECTS_DIR = Path.home() / ".claude" / "projects"
OPENCODE_STORAGE = Path.home() / ".local" / "share" / "opencode" / "storage"


def extract_text_from_content(content) -> str:
    """Extract readable text from a message content field."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                btype = block.get("type", "")
                if btype == "text":
                    parts.append(block.get("text", ""))
                elif btype == "tool_result":
                    # Skip tool results — too noisy
                    pass
                elif btype == "tool_use":
                    # Include tool name for context but not full input
                    name = block.get("name", "")
                    if name:
                        parts.append(f"[tool: {name}]")
                # Skip thinking blocks — private
        return " ".join(parts)
    return ""


def search_transcripts(pattern: str, start_ms: int, end_ms: int, limit: int = 50) -> list:
    """Search full session transcripts for a pattern."""
    matches = []
    regex = re.compile(pattern, re.IGNORECASE)

    # Convert ms boundaries to seconds for mtime comparison (with 1-day buffer)
    start_epoch = start_ms / 1000 - 86400
    end_epoch = end_ms / 1000 + 86400

    if not PROJECTS_DIR.exists():
        return matches

    # Find all session JSONL files within the time range (using mtime)
    session_files = []
    for project_dir in PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue
        for jsonl_file in project_dir.glob("*.jsonl"):
            try:
                mtime = jsonl_file.stat().st_mtime
                if mtime >= start_epoch and mtime <= end_epoch:
                    session_files.append(jsonl_file)
            except OSError:
                continue

    for jsonl_file in sorted(session_files, key=lambda f: f.stat().st_mtime, reverse=True):
        try:
            with open(jsonl_file, "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        entry_type = entry.get("type", "")
                        if entry_type not in ("user", "assistant"):
                            continue

                        # Parse timestamp
                        ts_str = entry.get("timestamp", "")
                        if not ts_str:
                            continue
                        try:
                            ts_dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                            ts_ms = int(ts_dt.timestamp() * 1000)
                        except (ValueError, TypeError):
                            continue

                        if not (start_ms <= ts_ms < end_ms):
                            continue

                        # Extract text
                        message = entry.get("message", {})
                        content = message.get("content", "")
                        text = extract_text_from_content(content)
                        if not text or not text.strip():
                            continue

                        # Search
                        if regex.search(text):
                            ts_hkt = datetime.fromtimestamp(ts_ms / 1000, tz=HKT)
                            session_id = entry.get("sessionId", jsonl_file.stem)
                            role = "you" if entry_type == "user" else "claude"

                            # Find match context (snippet around the match)
                            match_obj = regex.search(text)
                            start_idx = max(0, match_obj.start() - 40)
                            end_idx = min(len(text), match_obj.end() + 60)
                            snippet = text[start_idx:end_idx].replace("\n", " ")
                            if start_idx > 0:
                                snippet = "..." + snippet
                            if end_idx < len(text):
                                snippet = snippet + "..."

                            matches.append({
                                "date": ts_hkt.strftime("%Y-%m-%d"),
                                "time": ts_hkt.strftime("%H:%M"),
                                "timestamp": ts_ms,
                                "session": session_id[:8],
                                "session_full": session_id,
                                "role": role,
                                "snippet": snippet,
                                "tool": "Claude",
                            })
                    except (json.JSONDecodeError, Exception):
                        continue
        except (OSError, Exception):
            continue

    # Sort by timestamp descending (most recent first)
    matches.sort(key=lambda x: x["timestamp"], reverse=True)
    return matches[:limit]


def search_prompts(pattern: str, start_ms: int, end_ms: int, tool: Optional[str] = None, limit: int = 50) -> list:
    """Search prompt history for a pattern (fast, prompts only)."""
    matches = []
    regex = re.compile(pattern, re.IGNORECASE)

    if tool and tool in HISTORY_FILES:
        files_to_scan = {tool: HISTORY_FILES[tool]}
    elif tool:
        files_to_scan = {}
    else:
        files_to_scan = HISTORY_FILES

    for label, path in files_to_scan.items():
        if not path.exists():
            continue
        with open(path, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    ts = entry.get("timestamp", 0)
                    if not isinstance(ts, int) or not (start_ms <= ts < end_ms):
                        continue

                    prompt = entry.get("display", entry.get("prompt", ""))
                    if not prompt or not regex.search(prompt):
                        continue

                    ts_hkt = datetime.fromtimestamp(ts / 1000, tz=HKT)
                    sess = entry.get("sessionId", "unknown")

                    # Snippet around match
                    match_obj = regex.search(prompt)
                    start_idx = max(0, match_obj.start() - 40)
                    end_idx = min(len(prompt), match_obj.end() + 60)
                    snippet = prompt[start_idx:end_idx].replace("\n", " ")
                    if start_idx > 0:
                        snippet = "..." + snippet
                    if end_idx < len(prompt):
                        snippet = snippet + "..."

                    matches.append({
                        "date": ts_hkt.strftime("%Y-%m-%d"),
                        "time": ts_hkt.strftime("%H:%M"),
                        "timestamp": ts,
                        "session": sess[:8],
                        "session_full": sess,
                        "role": "you",
                        "snippet": snippet,
                        "tool": label,
                    })
                except (json.JSONDecodeError, Exception):
                    continue

    # Also search OpenCode if applicable
    if tool is None or (tool and tool.lower() == "opencode"):
        oc_prompts = scan_opencode(start_ms, end_ms)
        for p in oc_prompts:
            if regex.search(p["prompt"]):
                match_obj = regex.search(p["prompt"])
                start_idx = max(0, match_obj.start() - 40)
                end_idx = min(len(p["prompt"]), match_obj.end() + 60)
                snippet = p["prompt"][start_idx:end_idx].replace("\n", " ")
                if start_idx > 0:
                    snippet = "..." + snippet
                if end_idx < len(p["prompt"]):
                    snippet = snippet + "..."
                matches.append({
                    "date": p["time"][:10] if len(p["time"]) > 10 else datetime.now(HKT).strftime("%Y-%m-%d"),
                    "time": p["time"],
                    "timestamp": p["timestamp"],
                    "session": p["session"],
                    "session_full": p["session_full"],
                    "role": "you",
                    "snippet": snippet,
                    "tool": "OpenCode",
                })

    matches.sort(key=lambda x: x["timestamp"], reverse=True)
    return matches[:limit]


def scan_opencode(start_ms: int, end_ms: int) -> list:
    """Scan OpenCode storage for sessions and prompts."""
    prompts = []
    if not OPENCODE_STORAGE.exists():
        return prompts

    session_files = list(OPENCODE_STORAGE.glob("session/*/*.json"))
    for sf in session_files:
        try:
            with open(sf, "r") as f:
                sess_data = json.load(f)
                created_ms = sess_data.get("time", {}).get("created", 0)
                if not (start_ms <= created_ms < end_ms):
                    updated_ms = sess_data.get("time", {}).get("updated", 0)
                    if not (start_ms <= updated_ms < end_ms):
                        continue

                sess_id = sess_data.get("id")

                msg_dir = OPENCODE_STORAGE / "message" / sess_id
                if not msg_dir.exists():
                    continue

                msg_files = list(msg_dir.glob("msg_*.json"))
                for mf in msg_files:
                    with open(mf, "r") as f:
                        msg_data = json.load(f)
                        if msg_data.get("role") != "user":
                            continue

                        ts_ms = msg_data.get("time", {}).get("created", 0)
                        if not (start_ms <= ts_ms < end_ms):
                            continue

                        msg_id = msg_data.get("id")

                        part_dir = OPENCODE_STORAGE / "part" / msg_id
                        prompt_text = ""
                        if part_dir.exists():
                            part_files = sorted(part_dir.glob("prt_*.json"))
                            for pf in part_files:
                                with open(pf, "r") as f:
                                    part_data = json.load(f)
                                    prompt_text += part_data.get("text", "")

                        if prompt_text:
                            ts_hkt = datetime.fromtimestamp(ts_ms / 1000, tz=HKT)
                            prompts.append({
                                "time": ts_hkt.strftime("%H:%M"),
                                "timestamp": ts_ms,
                                "session": sess_id[:8],
                                "session_full": sess_id,
                                "prompt": prompt_text,
                                "tool": "OpenCode",
                            })
        except Exception:
            continue
    return prompts


def scan_history(target_date_str: str, limit: int = 50, tool: Optional[str] = None) -> Dict[str, Any]:
    """Scan history files for a specific date in HKT."""
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d").replace(tzinfo=HKT)

    day_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    start_ms = int(day_start.timestamp() * 1000)
    end_ms = int(day_end.timestamp() * 1000)

    prompts = []

    if tool and tool in HISTORY_FILES:
        files_to_scan = {tool: HISTORY_FILES[tool]}
    elif tool:
        files_to_scan = {}
    else:
        files_to_scan = HISTORY_FILES

    for label, path in files_to_scan.items():
        if not path.exists():
            continue

        with open(path, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    ts = entry.get("timestamp", 0)
                    if not isinstance(ts, int) or not (start_ms <= ts < end_ms):
                        continue

                    ts_hkt = datetime.fromtimestamp(ts / 1000, tz=HKT)
                    sess = entry.get("sessionId", "unknown")
                    prompt = entry.get("display", entry.get("prompt", ""))

                    prompts.append({
                        "time": ts_hkt.strftime("%H:%M"),
                        "timestamp": ts,
                        "session": sess[:8],
                        "session_full": sess,
                        "prompt": prompt,
                        "tool": label,
                    })
                except (json.JSONDecodeError, Exception):
                    continue

    if tool is None or (tool and tool.lower() == "opencode"):
        prompts.extend(scan_opencode(start_ms, end_ms))

    prompts.sort(key=lambda x: x["timestamp"])

    sessions = {}
    for p in prompts:
        sid = p["session_full"]
        if sid not in sessions:
            sessions[sid] = {
                "count": 0,
                "first": datetime.fromtimestamp(p["timestamp"] / 1000, tz=HKT),
                "last": datetime.fromtimestamp(p["timestamp"] / 1000, tz=HKT),
                "tool": p["tool"],
            }
        sessions[sid]["count"] += 1
        sessions[sid]["last"] = datetime.fromtimestamp(p["timestamp"] / 1000, tz=HKT)

    return {
        "date": target_date_str,
        "total": len(prompts),
        "sessions": [
            {
                "id": sid[:8],
                "full_id": sid,
                "count": s["count"],
                "tool": s["tool"],
                "first": s["first"].strftime("%H:%M"),
                "last": s["last"].strftime("%H:%M"),
                "range": f"{s['first'].strftime('%H:%M')}-{s['last'].strftime('%H:%M')}",
            }
            for sid, s in sorted(sessions.items(), key=lambda x: x[1]["first"])
        ],
        "prompts": prompts[-limit:] if limit else prompts,
        "all_prompts": prompts,
    }


def print_results(result: dict, full: bool = False):
    """Print results in human-readable format."""
    if "error" in result:
        print(result["error"])
        return

    print(f"Date: {result['date']} (HKT)")
    print(f"Total: {result['total']} prompts across {len(result['sessions'])} sessions")
    print()

    if result["sessions"]:
        first = result["sessions"][0]["first"]
        last = result["sessions"][-1]["last"]
        print(f"Time range: {first} - {last}")
        print()

    print("Sessions:")
    for s in result["sessions"]:
        print(f"  [{s['id']}] {s['count']:3d} prompts ({s['range']}) - {s['tool']}")

    print()
    prompts = result["all_prompts"] if full else result["prompts"]
    label = "All prompts:" if full else f"Recent prompts (last {len(prompts)}):"
    print(label)
    for p in prompts:
        prompt_preview = p["prompt"][:80].replace("\n", " ")
        if len(p["prompt"]) > 80:
            prompt_preview += "..."
        print(f"  {p['time']} [{p['session']}] ({p['tool']}) {prompt_preview}")


def print_search_results(matches: list, pattern: str, days: int, deep: bool):
    """Print search results in human-readable format."""
    mode = "full transcripts" if deep else "prompts only"
    print(f'Search: "{pattern}" (last {days} days, {mode})')
    if not matches:
        print("No matches found.")
        return

    # Group by date
    by_date: dict[str, list] = {}
    for m in matches:
        by_date.setdefault(m["date"], []).append(m)

    print(f"Found {len(matches)} matches across {len(by_date)} days\n")

    for date in sorted(by_date.keys(), reverse=True):
        print(f"  {date}:")
        for m in sorted(by_date[date], key=lambda x: x["timestamp"]):
            role_tag = f"({m['role']})" if deep else ""
            snippet = m["snippet"][:100]
            print(f"    {m['time']} [{m['session']}] {role_tag:9s} {snippet}")
        print()


def main():
    args = sys.argv[1:]

    # Parse flags
    full = "--full" in args
    as_json = "--json" in args
    deep = "--deep" in args

    # Parse --search=PATTERN
    search_pattern = None
    for arg in args:
        if arg.startswith("--search="):
            search_pattern = arg.split("=", 1)[1]
            break

    # Parse --days=N
    days = None
    for arg in args:
        if arg.startswith("--days="):
            try:
                days = int(arg.split("=", 1)[1])
            except ValueError:
                pass
            break

    # Parse --tool=NAME
    tool = None
    for arg in args:
        if arg.startswith("--tool="):
            tool = arg.split("=", 1)[1]
            break

    # Strip flags from positional args
    positional = [a for a in args if not a.startswith("--")]

    # --- Search mode ---
    if search_pattern:
        # Determine date range
        if positional and positional[0] not in ("today", "yesterday"):
            # Specific date given — search just that day
            target = positional[0]
            try:
                target_date = datetime.strptime(target, "%Y-%m-%d").replace(tzinfo=HKT)
            except ValueError:
                print(f"Invalid date format: {target}. Use YYYY-MM-DD.")
                sys.exit(1)
            day_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            effective_days = 1
        else:
            # Date range
            effective_days = days if days else 7
            now = datetime.now(HKT)
            day_end = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            day_start = day_end - timedelta(days=effective_days)

        start_ms = int(day_start.timestamp() * 1000)
        end_ms = int(day_end.timestamp() * 1000)

        t0 = time.monotonic()

        if deep:
            matches = search_transcripts(search_pattern, start_ms, end_ms)
        else:
            matches = search_prompts(search_pattern, start_ms, end_ms, tool=tool)

        elapsed = time.monotonic() - t0

        if as_json:
            print(json.dumps(matches, indent=2, default=str))
        else:
            print_search_results(matches, search_pattern, effective_days, deep)
            print(f"({elapsed:.1f}s)")
        return

    # --- Normal date-scan mode ---
    if not positional or positional[0] == "today":
        target = datetime.now(HKT).strftime("%Y-%m-%d")
    elif positional[0] == "yesterday":
        target = (datetime.now(HKT) - timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        target = positional[0]

    try:
        datetime.strptime(target, "%Y-%m-%d")
    except ValueError:
        print(f"Invalid date format: {target}. Use YYYY-MM-DD.")
        sys.exit(1)

    limit = 0 if full else 50
    result = scan_history(target, limit=limit, tool=tool)

    if as_json:
        if not full:
            result.pop("all_prompts", None)
        print(json.dumps(result, indent=2, default=str))
    else:
        print_results(result, full=full)


if __name__ == "__main__":
    main()
