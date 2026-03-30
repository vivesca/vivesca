"""emit — all outbound secretion (output) channels.

Actions: spark|tweet|daily_note|praxis|publish|reminder|telemetry|telegram_text|telegram_image|linkedin|knowledge_signal|interphase_close
Absorbs: secretory (emit_*), deltos (exocytosis_*), pseudopod endocytosis_extract helpers, polymerization, interphase_close.
"""

from __future__ import annotations

import contextlib
import os
import re
from datetime import date as _date, datetime, timedelta, timezone
from pathlib import Path

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.cytosol import invoke_organelle, synthesize
from metabolon.locus import chromatin
from metabolon.metabolism.signals import Outcome, SensorySystem, Stimulus
from metabolon.morphology import EffectorResult, Secretion
from metabolon.organelles import golgi as _golgi
from metabolon.organelles import pacemaker as _pacemaker
from metabolon.organelles import praxis as _praxis
from metabolon.organelles import secretory_vesicle as _sv

HKT = timezone(timedelta(hours=8))
NOTES = str(chromatin)


def _today_iso() -> str:
    return datetime.now(HKT).strftime("%Y-%m-%d")


def _append_to_file(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as f:
        f.write(content)


# Paths
TELEMETRY_FILE = os.path.join(NOTES, "Meta", "Content Telemetry.md")
SPARKS_FILE = os.path.join(NOTES, "Consulting", "_sparks.md")
DAILY_DIR = os.path.join(NOTES, "Daily")
INTERPHASE_DAILY_DIR = Path.home() / "epigenome" / "chromatin" / "Daily"

TELEMETRY_HEADER = (
    "# Content Telemetry\n\n"
    "| date | channel | slug | title | source-skill | tags |\n"
    "|------|---------|------|-------|--------------|------|\n"
)

_COMPRESS_PROMPT = """\
Compress this insight into a tweet of at most 280 characters.
Rules:
- Assertions over explanations. One-sentence thesis.
- Cut adjectives and filler. Use arrows (->), not prose connectors.
- Parallel structure where possible (X gives Y. Z gives W.).
- Sharpest line last, not a summary.
- Straight quotes only -- no smart quotes, no Unicode punctuation.
- Do NOT exceed 280 characters. Count carefully.
- Return ONLY the tweet text. No preamble, no quotes around it.

Insight:
{insight}"""

_LINKEDIN_PROMPT = """\
Expand this tweet into a LinkedIn post.
Rules:
- Professional framing -- not a longer tweet, but a rewrite for a professional audience.
- Warm but direct tone. No corporate jargon.
- 100-200 words. Structured: hook -> point -> implication.
- Address blindspots or objections the tweet left open.
- No insider details (assume readers will check the author's profile).
- Straight quotes only -- no smart quotes, no Unicode punctuation.
- Return ONLY the post body. No preamble.

Tweet:
{tweet}"""


class EmitResult(Secretion):
    output: str


class PraxisResult(Secretion):
    output: str


_ACTIONS = (
    "spark — append a consulting spark. Requires: label, content. Optional: tags. "
    "tweet — post to X (280 char limit). Requires: text. "
    "daily_note — append section to today's daily note. Requires: section, content. "
    "praxis — query Praxis.md. Optional: subcommand (today/upcoming/overdue/someday/all/stats/clean). "
    "publish — garden publish operations. Requires: subcommand (new/list/publish/push/index). Optional: slug. "
    "reminder — set a Due app reminder. Requires: title. Optional: date. "
    "telemetry — log published content. Requires: channel, title, source_skill. Optional: slug, tags. "
    "telegram_text — send text to Telegram. Requires: text. Optional: format (html/plain). "
    "telegram_image — send image to Telegram. Requires: path. Optional: caption. "
    "linkedin — expand tweet to LinkedIn post. Requires: tweet. Optional: topic. "
    "knowledge_signal — report whether a knowledge artifact was useful. Requires: artifact, useful. Optional: context. "
    "interphase_close — append interphase summary to daily note. Requires: shipped, tomorrow, open_threads, nudges, day_score. Optional: note_date."
)


@tool(
    name="emit",
    description=f"All outbound channels. Actions: {_ACTIONS}",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def emit(
    action: str,
    # spark
    label: str = "",
    content: str = "",
    tags: str = "",
    # tweet / linkedin / knowledge_signal
    text: str = "",
    insight: str = "",
    topic: str = "",
    tweet: str = "",
    artifact: str = "",
    useful: bool = True,
    context: str = "",
    # daily_note
    section: str = "",
    # praxis
    subcommand: str = "today",
    json_output: bool = True,
    # publish
    slug: str = "",
    # reminder
    title: str = "",
    date: str = "",
    # telemetry
    channel: str = "",
    source_skill: str = "",
    # telegram
    path: str = "",
    caption: str = "",
    format: str = "html",
    # interphase_close
    shipped: str = "",
    tomorrow: str = "",
    open_threads: str = "",
    nudges: str = "",
    day_score: int = 0,
    note_date: str = "",
) -> EmitResult | PraxisResult | EffectorResult:
    """Unified outbound secretion tool."""
    action = action.lower().strip()

    # -- spark -----------------------------------------------------------
    if action == "spark":
        if not label or not content:
            return EffectorResult(success=False, message="spark requires: label, content")
        header = f"\n## {_today_iso()}\n"
        tag_prefix = f"{tags} -- " if tags else ""
        entry = f"{header}{tag_prefix}**{label}**: {content}\n"
        _append_to_file(SPARKS_FILE, entry)
        return EffectorResult(success=True, message=f"Spark logged: {label}")

    # -- tweet (direct post) --------------------------------------------
    elif action == "tweet":
        tweet_text = text.strip()
        if not tweet_text and insight.strip():
            prompt = _COMPRESS_PROMPT.format(insight=insight.strip())
            tweet_text = synthesize(prompt, timeout=60).strip()
        if not tweet_text:
            return EffectorResult(success=False, message="tweet requires: text or insight")
        rejection = _golgi.chaperone_check(tweet_text, "tweet")
        if rejection:
            return EffectorResult(success=False, message=rejection)
        result = invoke_organelle("bird", ["tweet", tweet_text], timeout=30)
        return EffectorResult(success=True, message=result)

    # -- daily_note ------------------------------------------------------
    elif action == "daily_note":
        if not section or not content:
            return EffectorResult(success=False, message="daily_note requires: section, content")
        today = _today_iso()
        path = os.path.join(DAILY_DIR, f"{today}.md")
        if not os.path.exists(path):
            _append_to_file(path, f"# {today}\n")
        entry = f"\n## {section}\n\n{content}\n"
        _append_to_file(path, entry)
        return EffectorResult(success=True, message=f"Daily note: added '{section}'")

    # -- praxis ----------------------------------------------------------
    elif action == "praxis":
        import json as _json
        _dispatch = {
            "today": _praxis.today, "upcoming": _praxis.upcoming,
            "overdue": _praxis.overdue, "someday": _praxis.someday,
            "all": _praxis.all_items, "spare": _praxis.spare,
            "clean": _praxis.clean, "stats": _praxis.stats,
        }
        fn = _dispatch.get(subcommand)
        if fn is None:
            return PraxisResult(output=f"Unknown subcommand: {subcommand}")
        data = fn()
        result = _json.dumps(data) if json_output else str(data)
        return PraxisResult(output=result)

    # -- publish ---------------------------------------------------------
    elif action == "publish":
        from metabolon.organelles import golgi
        if subcommand == "new":
            _s, p = golgi.new(slug)
            return EffectorResult(success=True, message=f"Created {p} (draft)")
        elif subcommand == "list":
            posts = golgi.list_posts()
            lines = [f"{p['slug']:30s} {p['title'][:40]:40s} {'(draft)' if p['draft'] else ''}" for p in posts]
            return EffectorResult(success=True, message="\n".join(lines) or "No posts")
        elif subcommand == "publish":
            t = golgi.publish(slug, force=True)
            return EffectorResult(success=True, message=f"Published: {t}")
        elif subcommand == "push":
            return EffectorResult(success=True, message=golgi.push())
        elif subcommand == "index":
            return EffectorResult(success=True, message=f"Index updated -- {golgi.index()} posts")
        return EffectorResult(success=False, message=f"Unknown subcommand: {subcommand}")

    # -- reminder --------------------------------------------------------
    elif action == "reminder":
        if not title:
            return EffectorResult(success=False, message="reminder requires: title")
        try:
            result = _pacemaker.add(title, date=date or None)
            return EffectorResult(success=True, message=result)
        except Exception as exc:
            return EffectorResult(success=False, message=str(exc))

    # -- telemetry -------------------------------------------------------
    elif action == "telemetry":
        telemetry_title = title or text
        if not channel or not telemetry_title or not source_skill:
            return EffectorResult(success=False, message="telemetry requires: channel, title, source_skill")
        if not os.path.exists(TELEMETRY_FILE):
            _append_to_file(TELEMETRY_FILE, TELEMETRY_HEADER)
        row = f"| {_today_iso()} | {channel} | {slug or '-'} | {telemetry_title} | {source_skill} | {tags or '-'} |\n"
        _append_to_file(TELEMETRY_FILE, row)
        return EffectorResult(success=True, message=f"Telemetry logged: {channel} - {telemetry_title}")

    # -- telegram_text ---------------------------------------------------
    elif action == "telegram_text":
        if not text:
            return EffectorResult(success=False, message="telegram_text requires: text")
        msg = text
        if format == "html":
            msg = re.sub(r"^#{1,3}\s+(.+)$", r"<b>\1</b>", msg, flags=re.MULTILINE)
            msg = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", msg)
            msg = re.sub(r"\[(.+?)\]\((.+?)\)", r"\1 (\2)", msg)
        html_mode = format != "plain"
        result = _sv.secrete_text(msg, html=html_mode)
        return EffectorResult(success=True, message=result)

    # -- telegram_image --------------------------------------------------
    elif action == "telegram_image":
        if not path:
            return EffectorResult(success=False, message="telegram_image requires: path")
        expanded = os.path.expanduser(path)
        if not os.path.isfile(expanded):
            return EffectorResult(success=False, message=f"File not found: {expanded}")
        result = _sv.secrete_image(expanded, caption=caption)
        return EffectorResult(success=True, message=result)

    # -- linkedin (expand + publish) -------------------------------------
    elif action == "linkedin":
        if not tweet:
            return EffectorResult(success=False, message="linkedin requires: tweet")
        prompt = _LINKEDIN_PROMPT.format(tweet=tweet.strip())
        post_body = synthesize(prompt, timeout=60).strip()
        return EffectorResult(
            success=False,
            message="LinkedIn posting unavailable: agoras binary not implemented.",
            data={"post": post_body},
        )

    # -- knowledge_signal ------------------------------------------------
    elif action == "knowledge_signal":
        if not artifact:
            return EffectorResult(success=False, message="knowledge_signal requires: artifact")
        collector = SensorySystem()
        outcome = Outcome.success if useful else Outcome.error
        collector.append(Stimulus(
            tool=f"knowledge:{artifact}", outcome=outcome,
            substrate_consumed=0, product_released=0,
            response_latency=0, context=context,
        ))
        return EffectorResult(
            success=True,
            message=f"Knowledge signal: {artifact} = {'useful' if useful else 'not useful'}",
        )

    # -- interphase_close ------------------------------------------------
    elif action == "interphase_close":
        if not shipped or not tomorrow or not open_threads or not nudges or not day_score:
            return EffectorResult(success=False, message="interphase_close requires: shipped, tomorrow, open_threads, nudges, day_score")
        if note_date:
            try:
                d = _date.fromisoformat(note_date)
            except ValueError:
                return EffectorResult(success=False, message=f"Invalid date: {note_date}")
        else:
            d = _date.today()
        if not 1 <= day_score <= 5:
            return EffectorResult(success=False, message=f"day_score must be 1-5, got {day_score}")
        note_path = INTERPHASE_DAILY_DIR / f"{d.isoformat()}.md"
        note_path.parent.mkdir(parents=True, exist_ok=True)
        block = (
            f"\n## Interphase\n\n"
            f"**Shipped:** {shipped}\n"
            f"**Tomorrow:** {tomorrow}\n"
            f"**Open threads:** {open_threads}\n"
            f"**Nudges:** {nudges}\n"
            f"**Day score:** {day_score}/5\n"
        )
        if note_path.exists():
            existing = note_path.read_text()
            if "## Interphase" in existing:
                return EmitResult(output=f"## Interphase already present in {note_path.name}")
            new_text = existing.rstrip() + "\n" + block
        else:
            new_text = f"# {d.isoformat()}\n" + block
        note_path.write_text(new_text)
        return EmitResult(output=f"Interphase block written to {note_path}")

    else:
        return EffectorResult(success=False, message=f"Unknown action '{action}'.")
