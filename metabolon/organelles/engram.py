"""engram — chat session archive search (formerly anam)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

from metabolon import locus

# HKT = UTC+8
_HKT = timezone(timedelta(hours=8))


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def _history_files() -> list[tuple[str, Path]]:
    return [
        ("Claude", locus.claude_dir / "history.jsonl"),
        ("Codex", Path.home() / ".codex" / "history.jsonl"),
    ]


def _projects_dir() -> Path:
    return locus.claude_dir / "projects"


def _opencode_storage() -> Path:
    return Path.home() / ".local" / "share" / "opencode" / "storage"


# ---------------------------------------------------------------------------
# Time helpers
# ---------------------------------------------------------------------------

def _now_hkt() -> datetime:
    return datetime.now(tz=_HKT)


def _resolve_date(s: str) -> str:
    now = _now_hkt()
    if s == "today":
        return now.strftime("%Y-%m-%d")
    if s == "yesterday":
        return (now - timedelta(days=1)).strftime("%Y-%m-%d")
    # Validate YYYY-MM-DD
    try:
        datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid date format: {s}. Use YYYY-MM-DD.")
    return s


def _date_to_range_ms(date_str: str) -> tuple[int, int]:
    d = datetime.strptime(date_str, "%Y-%m-%d")
    start = datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=_HKT)
    end = start + timedelta(days=1)
    return int(start.timestamp() * 1000), int(end.timestamp() * 1000)


def _ms_to_hkt(ms: int) -> datetime:
    return datetime.fromtimestamp(ms / 1000, tz=_HKT)


def _parse_rfc3339(s: str) -> datetime | None:
    """Parse RFC-3339 / ISO-8601 timestamp to aware datetime."""
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Content extraction (Claude transcript blocks)
# ---------------------------------------------------------------------------

def _extract_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if not isinstance(block, dict):
                continue
            t = block.get("type")
            if t == "text":
                text = block.get("text", "")
                if text:
                    parts.append(text)
            elif t == "tool_use":
                name = block.get("name", "")
                if name:
                    parts.append(f"[tool: {name}]")
        return " ".join(parts)
    return ""


# ---------------------------------------------------------------------------
# Snippet
# ---------------------------------------------------------------------------

def _make_snippet(text: str, match_start: int, match_end: int) -> str:
    start = max(0, match_start - 40)
    end = min(len(text), match_end + 60)
    snippet = text[start:end].replace("\n", " ")
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    return snippet


# ---------------------------------------------------------------------------
# Role matching
# ---------------------------------------------------------------------------

def _matches_role(role: str, filt: str) -> bool:
    f = filt.lower()
    if f in ("you", "user", "me"):
        return role == "you"
    if f in ("claude", "assistant", "ai"):
        return role in ("claude", "opencode")
    if f == "opencode":
        return role == "opencode"
    return role.lower() == f


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class Prompt:
    time_str: str
    timestamp_ms: int
    session: str
    session_full: str
    prompt: str
    tool: str


@dataclass(slots=True)
class SearchMatch:
    date: str
    time_str: str
    timestamp_ms: int
    session: str
    role: str
    snippet: str
    tool: str


# ---------------------------------------------------------------------------
# OpenCode message iterator (shared traversal)
# ---------------------------------------------------------------------------

def _iter_opencode_messages(
    start_ms: int,
    end_ms: int,
    session_filter: str | None,
):
    """Yield (sess_id, msg, ts_ms) for all OpenCode messages in the time range."""
    storage = _opencode_storage()
    session_dir = storage / "session"
    if not session_dir.exists():
        return

    for sess_path in session_dir.iterdir():
        if not sess_path.is_dir():
            continue
        for jf in sess_path.glob("*.json"):
            try:
                sess = json.loads(jf.read_text())
            except Exception:
                continue

            t = sess.get("time") or {}
            created = t.get("created") or 0
            updated = t.get("updated") or 0
            if not ((start_ms <= created < end_ms) or (start_ms <= updated < end_ms)):
                continue

            sess_id = sess.get("id")
            if not sess_id:
                continue

            if session_filter:
                if not (sess_id.startswith(session_filter) or sess_id[:8].startswith(session_filter)):
                    continue

            msg_dir = storage / "message" / sess_id
            if not msg_dir.exists():
                continue

            msg_files = sorted(
                (f for f in msg_dir.iterdir() if f.name.startswith("msg_") and f.name.endswith(".json")),
                key=lambda f: f.name,
            )

            for mf in msg_files:
                try:
                    msg = json.loads(mf.read_text())
                except Exception:
                    continue

                mt = msg.get("time") or {}
                ts_ms = mt.get("created") or 0
                if ts_ms < start_ms or ts_ms >= end_ms:
                    continue

                yield sess_id, msg, ts_ms


def _read_opencode_text(storage: Path, msg_id: str) -> str:
    """Concatenate all part texts for an OpenCode message."""
    part_dir = storage / "part" / msg_id
    if not part_dir.exists():
        return ""
    parts: list[str] = []
    for pf in sorted(part_dir.iterdir(), key=lambda f: f.name):
        try:
            part = json.loads(pf.read_text())
            t = part.get("text", "")
            if t:
                parts.append(t)
        except Exception:
            continue
    return "".join(parts)


# ---------------------------------------------------------------------------
# OpenCode scan (date mode, user prompts only)
# ---------------------------------------------------------------------------

def _scan_opencode(start_ms: int, end_ms: int) -> list[Prompt]:
    storage = _opencode_storage()
    prompts: list[Prompt] = []

    for sess_id, msg, ts_ms in _iter_opencode_messages(start_ms, end_ms, session_filter=None):
        if msg.get("role") != "user":
            continue

        msg_id = msg.get("id")
        if not msg_id:
            continue

        prompt_text = _read_opencode_text(storage, msg_id)
        if prompt_text:
            dt = _ms_to_hkt(ts_ms)
            prompts.append(Prompt(
                time_str=dt.strftime("%H:%M"),
                timestamp_ms=ts_ms,
                session=sess_id[:8],
                session_full=sess_id,
                prompt=prompt_text,
                tool="OpenCode",
            ))

    return prompts


# ---------------------------------------------------------------------------
# Scan history (date mode)
# ---------------------------------------------------------------------------

def _scan_history(date_str: str, tool_filter: str | None = None) -> list[Prompt]:
    start_ms, end_ms = _date_to_range_ms(date_str)
    prompts: list[Prompt] = []

    for label, path in _history_files():
        if tool_filter and not label.lower() == tool_filter.lower():
            continue
        if not path.exists():
            continue
        try:
            with path.open() as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except Exception:
                        continue
                    ts = entry.get("timestamp")
                    if not isinstance(ts, (int, float)):
                        continue
                    ts = int(ts)
                    if ts < start_ms or ts >= end_ms:
                        continue
                    prompt_text = entry.get("display") or entry.get("prompt") or ""
                    session = entry.get("sessionId") or "unknown"
                    dt = _ms_to_hkt(ts)
                    prompts.append(Prompt(
                        time_str=dt.strftime("%H:%M"),
                        timestamp_ms=ts,
                        session=session[:8],
                        session_full=session,
                        prompt=prompt_text,
                        tool=label,
                    ))
        except Exception:
            continue

    if not tool_filter or tool_filter.lower() == "opencode":
        prompts.extend(_scan_opencode(start_ms, end_ms))

    prompts.sort(key=lambda p: p.timestamp_ms)
    return prompts


# ---------------------------------------------------------------------------
# Search prompts (fast, prompts only)
# ---------------------------------------------------------------------------

def _search_prompts(
    regex: re.Pattern[str],
    start_ms: int,
    end_ms: int,
    tool_filter: str | None,
    role_filter: str | None,
    session_filter: str | None,
) -> list[SearchMatch]:
    # Prompts are always role "you" — if filtering for other roles, skip
    if role_filter and not _matches_role("you", role_filter):
        return []

    storage = _opencode_storage()
    matches: list[SearchMatch] = []

    for label, path in _history_files():
        if tool_filter and label.lower() != tool_filter.lower():
            continue
        if not path.exists():
            continue
        try:
            with path.open() as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except Exception:
                        continue
                    ts = entry.get("timestamp")
                    if not isinstance(ts, (int, float)):
                        continue
                    ts = int(ts)
                    if ts < start_ms or ts >= end_ms:
                        continue
                    session = entry.get("sessionId") or "unknown"
                    if session_filter:
                        if not (session.startswith(session_filter) or session[:8].startswith(session_filter)):
                            continue
                    prompt_text = entry.get("display") or entry.get("prompt") or ""
                    m = regex.search(prompt_text)
                    if m:
                        dt = _ms_to_hkt(ts)
                        matches.append(SearchMatch(
                            date=dt.strftime("%Y-%m-%d"),
                            time_str=dt.strftime("%H:%M"),
                            timestamp_ms=ts,
                            session=session[:8],
                            role="you",
                            snippet=_make_snippet(prompt_text, m.start(), m.end()),
                            tool=label,
                        ))
        except Exception:
            continue

    # OpenCode prompts
    if not tool_filter or tool_filter.lower() == "opencode":
        for sess_id, msg, ts_ms in _iter_opencode_messages(start_ms, end_ms, session_filter):
            if msg.get("role") != "user":
                continue
            msg_id = msg.get("id")
            if not msg_id:
                continue
            prompt_text = _read_opencode_text(storage, msg_id)
            if not prompt_text:
                continue
            mo = regex.search(prompt_text)
            if mo:
                dt = _ms_to_hkt(ts_ms)
                matches.append(SearchMatch(
                    date=dt.strftime("%Y-%m-%d"),
                    time_str=dt.strftime("%H:%M"),
                    timestamp_ms=ts_ms,
                    session=sess_id[:8],
                    role="you",
                    snippet=_make_snippet(prompt_text, mo.start(), mo.end()),
                    tool="OpenCode",
                ))

    matches.sort(key=lambda x: x.timestamp_ms, reverse=True)
    return matches


# ---------------------------------------------------------------------------
# Search transcripts (deep)
# ---------------------------------------------------------------------------

def _search_transcripts(
    regex: re.Pattern[str],
    start_ms: int,
    end_ms: int,
    tool_filter: str | None,
    role_filter: str | None,
    session_filter: str | None,
) -> list[SearchMatch]:
    storage = _opencode_storage()
    matches: list[SearchMatch] = []

    # Claude transcripts
    if not tool_filter or tool_filter.lower() == "claude":
        proj_dir = _projects_dir()
        if proj_dir.exists():
            start_epoch = (start_ms // 1000) - 86400
            end_epoch = (end_ms // 1000) + 86400

            session_files: list[Path] = []
            for proj in proj_dir.iterdir():
                if not proj.is_dir():
                    continue
                for f in proj.iterdir():
                    if f.suffix == ".jsonl":
                        try:
                            mtime = f.stat().st_mtime
                            if start_epoch <= mtime <= end_epoch:
                                session_files.append(f)
                        except OSError:
                            continue

            for path in session_files:
                try:
                    with path.open() as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                entry = json.loads(line)
                            except Exception:
                                continue

                            entry_type = entry.get("type")
                            if entry_type not in ("user", "assistant"):
                                continue

                            role = "you" if entry_type == "user" else "claude"

                            if role_filter and not _matches_role(role, role_filter):
                                continue

                            ts_str = entry.get("timestamp")
                            if not ts_str:
                                continue
                            ts_dt = _parse_rfc3339(ts_str)
                            if ts_dt is None:
                                continue
                            ts_ms = int(ts_dt.timestamp() * 1000)
                            if ts_ms < start_ms or ts_ms >= end_ms:
                                continue

                            # Session filter
                            sid = entry.get("sessionId") or path.stem
                            if session_filter and not sid.startswith(session_filter):
                                continue

                            msg = entry.get("message") or {}
                            content = msg.get("content")
                            if content is None:
                                continue

                            text = _extract_text(content)
                            if not text:
                                continue

                            m = regex.search(text)
                            if m:
                                hkt_dt = ts_dt.astimezone(_HKT)
                                session = entry.get("sessionId") or path.stem
                                matches.append(SearchMatch(
                                    date=hkt_dt.strftime("%Y-%m-%d"),
                                    time_str=hkt_dt.strftime("%H:%M"),
                                    timestamp_ms=ts_ms,
                                    session=session[:8],
                                    role=role,
                                    snippet=_make_snippet(text, m.start(), m.end()),
                                    tool="Claude",
                                ))
                except Exception:
                    continue

    # OpenCode transcripts
    if not tool_filter or tool_filter.lower() == "opencode":
        for sess_id, msg, ts_ms in _iter_opencode_messages(start_ms, end_ms, session_filter):
            role_str = msg.get("role") or ""
            if role_str not in ("user", "assistant"):
                continue

            role = "you" if role_str == "user" else "opencode"

            if role_filter and not _matches_role(role, role_filter):
                continue

            msg_id = msg.get("id")
            if not msg_id:
                continue

            text = _read_opencode_text(storage, msg_id)
            if not text:
                continue

            m = regex.search(text)
            if m:
                dt = _ms_to_hkt(ts_ms)
                matches.append(SearchMatch(
                    date=dt.strftime("%Y-%m-%d"),
                    time_str=dt.strftime("%H:%M"),
                    timestamp_ms=ts_ms,
                    session=sess_id[:8],
                    role=role,
                    snippet=_make_snippet(text, m.start(), m.end()),
                    tool="OpenCode",
                ))

    matches.sort(key=lambda x: x.timestamp_ms, reverse=True)
    return matches


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

def _print_scan(prompts: list[Prompt], date_str: str, full: bool) -> None:
    # Build session index
    sessions: dict[str, dict] = {}
    for p in prompts:
        if p.session_full not in sessions:
            dt = _ms_to_hkt(p.timestamp_ms)
            sessions[p.session_full] = {
                "count": 0,
                "first": dt,
                "last": dt,
                "tool": p.tool,
                "id_short": p.session,
            }
        s = sessions[p.session_full]
        s["count"] += 1
        dt = _ms_to_hkt(p.timestamp_ms)
        if dt < s["first"]:
            s["first"] = dt
        if dt > s["last"]:
            s["last"] = dt

    sorted_sessions = sorted(sessions.values(), key=lambda s: s["first"])

    print(f"Date: {date_str} (HKT)")
    print(f"Total: {len(prompts)} prompts across {len(sessions)} sessions")
    print()

    if sorted_sessions:
        first_s = sorted_sessions[0]
        last_s = sorted_sessions[-1]
        print(f"Time range: {first_s['first'].strftime('%H:%M')} - {last_s['last'].strftime('%H:%M')}")
        print()

    print("Sessions:")
    for s in sorted_sessions:
        print(f"  [{s['id_short']}] {s['count']:3} prompts ({s['first'].strftime('%H:%M')}-{s['last'].strftime('%H:%M')}) - {s['tool']}")
    print()

    if full:
        display = prompts
        label = "All prompts:"
    else:
        display = prompts[-50:] if len(prompts) > 50 else prompts
        label = f"Recent prompts (last {len(display)}):"

    print(label)
    for p in display:
        preview = p.prompt.replace("\n", " ")[:80]
        ellipsis = "..." if len(p.prompt) > 80 else ""
        print(f"  {p.time_str} [{p.session}] ({p.tool}) {preview}{ellipsis}")


def _print_search(
    matches: list[SearchMatch],
    pattern: str,
    days: int,
    deep: bool,
    role_filter: str | None,
    session_filter: str | None,
) -> None:
    mode = "full transcripts" if deep else "prompts only"
    filters_parts: list[str] = []
    if role_filter:
        filters_parts.append(f"role={role_filter}")
    if session_filter:
        filters_parts.append(f"session={session_filter}")
    filters = (", " + ", ".join(filters_parts)) if filters_parts else ""
    print(f'Search: "{pattern}" (last {days} days, {mode}{filters})')

    if not matches:
        print("No matches found.")
        return

    by_date: dict[str, list[SearchMatch]] = {}
    for m in matches:
        by_date.setdefault(m.date, []).append(m)

    print(f"Found {len(matches)} matches across {len(by_date)} days\n")

    for date in sorted(by_date.keys(), reverse=True):
        print(f"  {date}:")
        day_matches = sorted(by_date[date], key=lambda x: x.timestamp_ms)
        for m in day_matches:
            role_tag = f"({m.role})" if deep else ""
            snippet = m.snippet[:100]
            print(f"    {m.time_str} [{m.session}] {role_tag:9} {snippet}")
        print()


def _print_json_scan(prompts: list[Prompt], date_str: str) -> None:
    sessions: dict[str, int] = {}
    for p in prompts:
        sessions[p.session_full] = sessions.get(p.session_full, 0) + 1

    output = {
        "date": date_str,
        "total": len(prompts),
        "sessions": len(sessions),
        "prompts": [
            {
                "time": p.time_str,
                "timestamp": p.timestamp_ms,
                "session": p.session,
                "prompt": p.prompt,
                "tool": p.tool,
            }
            for p in prompts
        ],
    }
    print(json.dumps(output, indent=2))


def _print_json_search(matches: list[SearchMatch]) -> None:
    print(json.dumps([asdict(m) for m in matches], indent=2))


# ---------------------------------------------------------------------------
# Public API (for organelle callers)
# ---------------------------------------------------------------------------

def scan(date: str = "today", tool: str | None = None) -> list[Prompt]:
    """Return prompts for a given date. date = 'today', 'yesterday', or YYYY-MM-DD."""
    date_str = _resolve_date(date)
    return _scan_history(date_str, tool)


def search(
    pattern: str,
    days: int = 7,
    deep: bool = True,
    tool: str | None = None,
    role: str | None = None,
    session: str | None = None,
) -> list[SearchMatch]:
    """Search chat history. deep=True searches full transcripts; False = prompts only."""
    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error as exc:
        raise ValueError(f"Invalid regex pattern: {pattern}") from exc

    now = _now_hkt()
    tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    end_ms = int(tomorrow.timestamp() * 1000)
    start_ms = end_ms - days * 86400 * 1000

    if deep:
        return _search_transcripts(regex, start_ms, end_ms, tool, role, session)
    else:
        return _search_prompts(regex, start_ms, end_ms, tool, role, session)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _cli() -> None:
    import time as _time

    parser = argparse.ArgumentParser(
        prog="engram",
        description="Search AI coding chat history",
    )
    parser.add_argument(
        "date",
        nargs="?",
        default="today",
        help="Date to scan (YYYY-MM-DD, 'today', 'yesterday')",
    )
    parser.add_argument("--full", action="store_true", help="Show all prompts (not just last 50)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--tool", help="Filter by tool (Claude, Codex, OpenCode)")

    subparsers = parser.add_subparsers(dest="subcommand")
    search_parser = subparsers.add_parser("search", help="Search prompts or transcripts")
    search_parser.add_argument("pattern", help="Search pattern (regex)")
    search_parser.add_argument("--days", type=int, default=7, help="Number of days to search (default: 7)")
    search_parser.add_argument(
        "--prompts-only",
        action="store_true",
        help="Search user prompts only (default: search full transcripts)",
    )
    search_parser.add_argument("--tool", help="Filter by tool (Claude, Codex, OpenCode)")
    search_parser.add_argument("--role", help="Filter by role (you, claude, opencode, assistant)")
    search_parser.add_argument("--session", help="Filter by session ID (prefix match)")
    search_parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    try:
        if args.subcommand == "search":
            deep = not args.prompts_only
            now = _now_hkt()
            tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            end_ms = int(tomorrow.timestamp() * 1000)
            start_ms = end_ms - args.days * 86400 * 1000

            try:
                regex = re.compile(args.pattern, re.IGNORECASE)
            except re.error as exc:
                raise ValueError(f"Invalid regex pattern: {args.pattern}") from exc

            t0 = _time.monotonic()

            if deep:
                results = _search_transcripts(
                    regex, start_ms, end_ms,
                    args.tool, args.role, args.session,
                )
            else:
                results = _search_prompts(
                    regex, start_ms, end_ms,
                    args.tool, args.role, args.session,
                )

            elapsed = _time.monotonic() - t0

            if args.json:
                _print_json_search(results)
            else:
                _print_search(results, args.pattern, args.days, deep, args.role, args.session)
                print(f"({elapsed:.1f}s)")

        else:
            date_str = _resolve_date(args.date)
            prompts = _scan_history(date_str, args.tool)

            if args.json:
                _print_json_scan(prompts, date_str)
            else:
                _print_scan(prompts, date_str, args.full)

    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    _cli()
