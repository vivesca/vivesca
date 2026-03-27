from metabolon.locus import chromatin

"""secretory -- efferent (outward) actions from skills.

Biology: efferent nerves carry signals outward from the CNS to
effectors (muscles, glands). These tools are the deterministic
outward actions that skills invoke after LLM judgment.

Five shared emit clusters cover ~20 skills:
  emit_telemetry   -- append row to Content Telemetry.md
  emit_spark       -- append consulting spark to _sparks.md
  emit_daily_note  -- append section to today's daily note
  emit_praxis      -- read/mutate Praxis.md (wraps todo-cli)
  emit_publish     -- publish spore (wraps publish CLI)

Plus individual effectors:
  emit_tweet       -- post to X (wraps bird CLI)
  emit_reminder    -- set Due alarm (wraps pacemaker organelle)
  emit_vault_note  -- write/append a vault note

Content secretion tools (formerly skills):
  exocytosis_tweet -- compress insight to <=280 chars and post to X
  secretion        -- expand tweet to LinkedIn post and publish
"""

import contextlib
import os
import re
from datetime import datetime, timedelta, timezone

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.cytosol import invoke_organelle, synthesize
from metabolon.morphology import EffectorResult, Secretion
from metabolon.organelles import pacemaker as _pacemaker
from metabolon.organelles import praxis as _praxis
from metabolon.organelles import secretory_vesicle as _secretory_vesicle

HKT = timezone(timedelta(hours=8))
NOTES = str(chromatin)

# -- Chaperones: quality control before export --------------------------------
# Cell biology: chaperones verify protein folding before secretion.
# Misfolded proteins → ER-associated degradation (ERAD), not export.

_SPECIAL_CHARS = re.compile(
    r"[\u2014\u2013\u2018\u2019\u201c\u201d\u2192\u2190\u2026]"
)  # em/en dash, smart quotes, arrows, ellipsis
_PII_PATTERNS = re.compile(
    r"\b(?:\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4})\b"  # card numbers
    r"|\b[A-Z]\d{6}\(?[0-9A]\)?\b"  # HKID
    r"|\b\d{3}-\d{2}-\d{4}\b",  # SSN
    re.IGNORECASE,
)


def _chaperone_check(text: str, channel: str) -> str | None:
    """Pre-export quality control. Returns error message if misfolded, None if OK."""
    if _PII_PATTERNS.search(text):
        return "ERAD: PII detected — blocked export"
    if channel in ("tweet", "telegram") and _SPECIAL_CHARS.search(text):
        return f"ERAD: special characters in {channel} output (Blink constraint)"
    if channel == "tweet" and len(text) > 280:
        return f"ERAD: tweet too long ({len(text)} chars, max 280)"
    return None


def _today_iso() -> str:
    return datetime.now(HKT).strftime("%Y-%m-%d")


def _append_to_file(path: str, content: str) -> None:
    """Append content to a file, creating it if needed."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as f:
        f.write(content)


# -- Cluster 1: Content Telemetry ----------------------------------------
# Used by: budding, exocytosis, secretion
# After publishing content, log channel + metadata for tracking.

TELEMETRY_FILE = os.path.join(NOTES, "Meta", "Content Telemetry.md")
TELEMETRY_HEADER = (
    "# Content Telemetry\n\n"
    "| date | channel | slug | title | source-skill | tags |\n"
    "|------|---------|------|-------|--------------|------|\n"
)


@tool(
    name="emit_telemetry",
    description="Log published content to Content Telemetry.md.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def emit_telemetry(
    channel: str,
    title: str,
    source_skill: str,
    slug: str = "-",
    tags: str = "-",
) -> EffectorResult:
    """Append a telemetry row after publishing content."""
    if not os.path.exists(TELEMETRY_FILE):
        _append_to_file(TELEMETRY_FILE, TELEMETRY_HEADER)

    row = f"| {_today_iso()} | {channel} | {slug} | {title} | {source_skill} | {tags} |\n"
    _append_to_file(TELEMETRY_FILE, row)
    return EffectorResult(success=True, message=f"Telemetry logged: {channel} - {title}")


# -- Cluster 2: Sparks ---------------------------------------------------
# Used by: chemoreception, chemotaxis, phagocytosis, interphase, expression
# Consulting sparks: ideas worth capturing for the forge.

SPARKS_FILE = os.path.join(NOTES, "Consulting", "_sparks.md")


@tool(
    name="emit_spark",
    description="Append a consulting spark to _sparks.md.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def emit_spark(label: str, content: str, tags: str = "") -> EffectorResult:
    """Log a consulting spark -- an idea worth forging later."""
    header = f"\n## {_today_iso()}\n"
    tag_prefix = f"{tags} -- " if tags else ""
    entry = f"{header}{tag_prefix}**{label}**: {content}\n"
    _append_to_file(SPARKS_FILE, entry)
    return EffectorResult(success=True, message=f"Spark logged: {label}")


# -- Cluster 3: Daily note -----------------------------------------------
# Used by: cytokinesis, interphase, involution
# Append a named section to today's daily note.

DAILY_DIR = os.path.join(NOTES, "Daily")


@tool(
    name="emit_daily_note",
    description="Append a section to today's daily note.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def emit_daily_note(section: str, content: str) -> EffectorResult:
    """Append a named section (## heading + body) to the daily note."""
    today = _today_iso()
    path = os.path.join(DAILY_DIR, f"{today}.md")

    if not os.path.exists(path):
        _append_to_file(path, f"# {today}\n")

    entry = f"\n## {section}\n\n{content}\n"
    _append_to_file(path, entry)
    return EffectorResult(success=True, message=f"Daily note: added '{section}'")


# -- Cluster 4: Praxis ---------------------------------------------------
# Used by: cytokinesis, mitosis, polarization, polymerization, phagocytosis
# Wraps todo-cli for deterministic Praxis.md operations.


class PraxisResult(Secretion):
    """Praxis/TODO state."""

    output: str


@tool(
    name="emit_praxis",
    description="Read/query Praxis.md. Subcommands: today, upcoming, overdue, someday, all, stats, clean.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def emit_praxis(subcommand: str = "today", json_output: bool = True) -> PraxisResult:
    """Query Praxis.md state via praxis organelle."""
    import json as _json

    _dispatch = {
        "today": _praxis.today,
        "upcoming": _praxis.upcoming,
        "overdue": _praxis.overdue,
        "someday": _praxis.someday,
        "all": _praxis.all_items,
        "spare": _praxis.spare,
        "clean": _praxis.clean,
        "stats": _praxis.stats,
    }
    fn = _dispatch.get(subcommand)
    if fn is None:
        return PraxisResult(output=f"Unknown subcommand: {subcommand}")
    data = fn()
    result = _json.dumps(data) if json_output else str(data)
    return PraxisResult(output=result)


# -- Cluster 5: Garden publish --------------------------------------------
# Used by: budding, expression
# Wraps the publish CLI for terryli.hm garden operations.


@tool(
    name="emit_publish",
    description="Spore operations: new, list, publish, revise, push.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def emit_publish(subcommand: str, slug: str = "") -> EffectorResult:
    """Garden publish operations via Python organelle (formerly sarcio)."""
    from metabolon.organelles import golgi

    if subcommand == "new":
        _s, path = golgi.new(slug)
        return EffectorResult(success=True, message=f"Created {path} (draft)")
    elif subcommand == "list":
        posts = golgi.list_posts()
        lines = [
            f"{p['slug']:30s} {p['title'][:40]:40s} {'(draft)' if p['draft'] else ''}"
            for p in posts
        ]
        return EffectorResult(success=True, message="\n".join(lines) or "No posts")
    elif subcommand == "publish":
        title = golgi.publish(slug, force=True)
        return EffectorResult(success=True, message=f"Published: {title}")
    elif subcommand == "push":
        msg = golgi.push()
        return EffectorResult(success=True, message=msg)
    elif subcommand == "index":
        count = golgi.index()
        return EffectorResult(success=True, message=f"Index updated -- {count} posts")
    else:
        return EffectorResult(success=False, message=f"Unknown subcommand: {subcommand}")


# -- Individual effectors -------------------------------------------------


@tool(
    name="emit_tweet",
    description="Post to X (@zkMingLi). 280 char limit.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def emit_tweet(text: str) -> EffectorResult:
    """Post a tweet via bird CLI."""
    rejection = _chaperone_check(text, "tweet")
    if rejection:
        return EffectorResult(success=False, message=rejection)
    result = invoke_organelle("bird", ["tweet", text], timeout=30)
    return EffectorResult(success=True, message=result)


@tool(
    name="emit_reminder",
    description="Set a Due app reminder via pacemaker.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def emit_reminder(title: str, date: str = "") -> EffectorResult:
    """Add a reminder to Due via pacemaker organelle (Python direct, no subprocess)."""
    try:
        result = _pacemaker.add(title, date=date or None)
        return EffectorResult(success=True, message=result)
    except Exception as exc:
        return EffectorResult(success=False, message=str(exc))


@tool(
    name="emit_vault_note",
    description="Write or append to a vault note.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def emit_vault_note(
    path: str,
    content: str,
    mode: str = "append",
) -> EffectorResult:
    """Write to a vault note. Path relative to ~/epigenome/chromatin/.

    mode: 'append' adds to end, 'write' overwrites.
    """
    full_path = os.path.join(NOTES, path)

    if mode == "write":
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w") as f:
            f.write(content)
    else:
        _append_to_file(full_path, content)

    return EffectorResult(
        success=True,
        message=f"Vault note {'written' if mode == 'write' else 'appended'}: {path}",
    )


# -- Content secretion tools ----------------------------------------------
# exocytosis_tweet: compress an insight to <=280 chars and post to X
# secretion: expand a tweet to a LinkedIn post and publish

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


@tool(
    name="exocytosis_tweet",
    description="Compress insight to <=280 chars and post to X (@zkMingLi).",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False),
)
def exocytosis_tweet(insight: str, topic: str = "") -> EffectorResult:
    """Compress an insight to <=280 chars and post to X.

    Uses invoke_llm to compress, then bird tweet to post.
    Logs to Content Telemetry.md on success.
    On 226 block: returns fallback Telegram + intent URL.
    """
    prompt = _COMPRESS_PROMPT.format(insight=insight)
    text = synthesize(prompt, timeout=60)

    # Strip accidental wrapping quotes
    text = text.strip().strip('"').strip("'").strip()

    rejection = _chaperone_check(text, "tweet")
    if rejection:
        return EffectorResult(success=False, message=f"{rejection}. Text: {text}")

    try:
        result = invoke_organelle("bird", ["tweet", text], timeout=30)
    except ValueError as exc:
        err = str(exc)
        if "226" in err:
            # 226 block -- provide fallback
            import urllib.parse

            intent = "https://x.com/intent/tweet?text=" + urllib.parse.quote(text)
            with contextlib.suppress(Exception):
                _secretory_vesicle.secrete_text(text)
            return EffectorResult(
                success=False,
                message=f"226 block. Intent URL: {intent}",
                data={"text": text, "intent_url": intent},
            )
        raise

    # Log telemetry
    title = (text[:50] + "...") if len(text) > 50 else text
    src = topic or "exocytosis"
    emit_telemetry(channel="tweet", title=title, source_skill=src)

    return EffectorResult(success=True, message=result, data={"text": text})


@tool(
    name="secretion",
    description="Expand tweet to LinkedIn post and publish via agoras.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False),
)
def secretion(tweet: str, topic: str = "") -> EffectorResult:
    """Expand a tweet into a LinkedIn post and publish.

    Gate: requires the tweet to have been posted first.
    The tweet tests the claim; LinkedIn expands with blindspots addressed.
    """
    if not tweet or not tweet.strip():
        return EffectorResult(
            success=False,
            message="Gate: tweet text required. Post the tweet first, then pass it here.",
        )

    prompt = _LINKEDIN_PROMPT.format(tweet=tweet.strip())
    post_body = synthesize(prompt, timeout=60)
    post_body = post_body.strip()

    return EffectorResult(
        success=False,
        message="LinkedIn posting unavailable: agoras binary does not exist and no Python organelle equivalent has been implemented.",
        data={"post": post_body},
    )
