from __future__ import annotations

import configparser
import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from metabolon.organelles.endocytosis_rss.config import EndocytosisConfig
from metabolon.symbiont import transduce

# ---------------------------------------------------------------------------
# Signal transduction: load thresholds from conf, fall back to hardcoded defaults.
# Conf file: ~/germline/endocytosis.conf
# Signal source for LLM review: ~/.cache/endocytosis/engagement.jsonl
# ---------------------------------------------------------------------------

_ENDOCYTOSIS_CONF = Path.home() / "germline" / "endocytosis.conf"


def _load_thresholds() -> tuple[int, int, int]:
    """Read thresholds from endocytosis.conf; return hardcoded defaults if absent."""
    transcytose_default = 7
    store_default = 5
    theme_count_default = 8
    if not _ENDOCYTOSIS_CONF.exists():
        return transcytose_default, store_default, theme_count_default
    cp = configparser.ConfigParser()
    cp.read(_ENDOCYTOSIS_CONF)
    sec = "thresholds"
    transcytose = cp.getint(sec, "weekly_transcytose_threshold", fallback=transcytose_default)
    store = cp.getint(sec, "weekly_store_threshold", fallback=store_default)
    theme_count = cp.getint(sec, "default_theme_count", fallback=theme_count_default)
    return transcytose, store, theme_count


WEEKLY_TRANSCYTOSE_THRESHOLD, WEEKLY_STORE_THRESHOLD, DEFAULT_THEME_COUNT = _load_thresholds()


def _resolve_month(month: str | None) -> str:
    if month:
        return month
    return datetime.now().astimezone().strftime("%Y-%m")


def _llm_call(model: str, system: str, user: str) -> str:
    """Route through symbiont/channel. No API key needed."""
    # Combine as a single prompt — avoid "System:/User:" labels which
    # trigger prompt-injection refusal at large input sizes.
    prompt = f"{system}\n\n---\n\n{user}"
    result = transduce(model, prompt, timeout=180)
    if not result.strip():
        raise RuntimeError(f"LLM returned empty response (model={model})")
    return result


def recall_archived_articles(article_cache_dir: Path, month: str) -> list[dict[str, Any]]:
    if not article_cache_dir.exists():
        return []
    articles: list[dict[str, Any]] = []
    for path in sorted(article_cache_dir.glob(f"{month}*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        payload["_file"] = path.name
        articles.append(payload)
    return articles


def recall_news_entries(cargo_path: Path, month: str) -> list[dict[str, str]]:
    """Recall cargo entries for a given month from the JSONL store."""
    from metabolon.organelles.endocytosis_rss.cargo import recall_cargo

    entries: list[dict[str, str]] = []
    for item in recall_cargo(cargo_path, month=month):
        entries.append({
            "title": str(item.get("title", "")),
            "source": str(item.get("source", "")),
            "date": str(item.get("date", "")),
            "link": str(item.get("link", "")),
            "summary": str(item.get("summary", "")),
        })
    return entries


def _parse_theme_json(raw: str) -> list[dict[str, Any]]:
    text = raw.strip()
    if not text:
        raise ValueError("LLM returned empty response for theme identification")
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    # Extract JSON array even if surrounded by prose
    bracket_start = text.find("[")
    bracket_end = text.rfind("]")
    if bracket_start >= 0 and bracket_end > bracket_start:
        text = text[bracket_start : bracket_end + 1]
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"LLM returned non-JSON (first 200 chars): {raw[:200]!r}"
        ) from exc
    if not isinstance(parsed, list):
        raise ValueError("theme response is not a list")
    return [item for item in parsed if isinstance(item, dict)]


_MAX_PROMPT_CHARS = 120_000  # ~30K tokens — comfortably fits haiku; newest items kept


def _build_items(
    articles: list[dict[str, Any]],
    log_entries: list[dict[str, str]],
) -> list[str]:
    """Format articles + log entries as numbered items, newest first."""
    # Sort articles by date descending so truncation drops oldest
    dated_articles = sorted(
        enumerate(articles),
        key=lambda pair: pair[1].get("date", ""),
        reverse=True,
    )
    items: list[str] = []
    for orig_idx, article in dated_articles:
        text_preview = ""
        text = article.get("text")
        if isinstance(text, str) and text:
            text_preview = " ".join(text.split()[:200])[:500]
        items.append(
            f"[{orig_idx}] {article.get('date', '')} | {article.get('source', '')}"
            f" | {article.get('title', '')}\n"
            f"    Summary: {article.get('summary', '')}\n"
            f"    Preview: {text_preview}"
        )

    offset = len(articles)
    dated_entries = sorted(
        enumerate(log_entries),
        key=lambda pair: pair[1].get("date", ""),
        reverse=True,
    )
    for orig_idx, entry in dated_entries:
        items.append(
            f"[{offset + orig_idx}] {entry.get('date', '')} | {entry.get('source', '')}"
            f" | {entry.get('title', '')}\n"
            f"    Summary: {entry.get('summary', '')}"
        )
    return items


def sense_themes(
    model: str,
    articles: list[dict[str, Any]],
    log_entries: list[dict[str, str]],
    max_themes: int,
) -> list[dict[str, Any]]:
    items = _build_items(articles, log_entries)

    # Truncate items to fit in context window (newest-first, so oldest dropped)
    kept: list[str] = []
    total_chars = 0
    for item in items:
        if total_chars + len(item) > _MAX_PROMPT_CHARS:
            break
        kept.append(item)
        total_chars += len(item)

    system = (
        "You identify thematic clusters in AI news for a consultant"
        " advising banks on AI strategy.\n\n"
        f"Rules:\n- Identify {max_themes} themes most relevant"
        " to AI in banking/financial services\n"
        "- Each theme should have 3+ articles supporting it\n"
        '- Themes should be specific (not "AI progress")\n'
        "- Include cross-cutting themes (regulation, open-source vs proprietary, infrastructure)\n"
        "- Return valid JSON only, no markdown fences"
    )
    user = (
        f"Below are {len(kept)} items (from {len(articles)} articles + "
        f"{len(log_entries)} log entries, newest first, truncated to fit).\n\n"
        f"Identify up to {max_themes} thematic clusters. Return JSON:\n"
        "[\n"
        "  {\n"
        '    "theme": "Theme title",\n'
        '    "description": "2-3 sentence description",\n'
        '    "article_indices": [0, 3, 7],\n'
        '    "banking_relevance": "Why this matters for banks/fintech"\n'
        "  }\n"
        "]\n\n"
        "Articles:\n" + "\n\n".join(kept)
    )
    raw = _llm_call(model, system, user)
    return _parse_theme_json(raw)


def synthesize_theme(
    model: str,
    theme: dict[str, Any],
    articles: list[dict[str, Any]],
    log_entries: list[dict[str, str]],
) -> str:
    all_items: list[dict[str, Any]] = [*articles, *log_entries]
    selected: list[dict[str, Any]] = []
    for raw_idx in theme.get("article_indices", []):
        if not isinstance(raw_idx, int):
            continue
        if 0 <= raw_idx < len(all_items):
            selected.append(all_items[raw_idx])

    context_parts: list[str] = []
    for item in selected:
        text = item.get("text")
        if isinstance(text, str) and text:
            text_block = " ".join(text.split()[:3000])
        else:
            text_block = str(item.get("summary", "(no text available)"))
        context_parts.append(
            f"### {item.get('source', 'Unknown')} — {item.get('title', 'Untitled')}\n"
            f"Date: {item.get('date', 'unknown')} | Link: {item.get('link', 'n/a')}\n\n"
            f"{text_block}"
        )

    system = (
        "You produce evidence briefs for an AI consultant advising banks.\n"
        "Ground every claim in provided sources. Mark [paraphrased] when needed.\n"
        "Focus on banking/financial-services implications."
    )
    user = (
        f"Theme: {theme.get('theme', 'Untitled Theme')}\n"
        f"Description: {theme.get('description', '')}\n"
        f"Banking relevance: {theme.get('banking_relevance', '')}\n\n"
        "Produce an evidence brief with sections:\n"
        "## Theme\n### Summary\n### Claims & Evidence\n### Open Questions\n"
        "### Banking & Fintech Implications\n### Key Quotes\n\n"
        "Source articles:\n\n" + "\n\n---\n\n".join(context_parts)
    )
    return _llm_call(model, system, user)


def secrete_digest(
    output_dir: Path,
    month: str,
    themes: list[dict[str, Any]],
    theme_briefs: list[str],
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{month} AI Thematic Digest.md"
    now = datetime.now().astimezone()
    lines = [
        f"# AI Thematic Digest — {month}",
        "",
        f"Generated: {now.strftime('%Y-%m-%d %H:%M %Z')}",
        f"Themes: {len(themes)}",
        "",
        "---",
        "",
        "## Table of Contents",
        "",
    ]
    for i, theme in enumerate(themes, 1):
        name = str(theme.get("theme", f"Theme {i}"))
        anchor = re.sub(r"[^a-z0-9 ]", "", name.lower()).replace(" ", "-")
        lines.append(f"{i}. [{name}](#{anchor})")

    lines.extend(["", "---", ""])
    for brief in theme_briefs:
        lines.extend([brief, "", "---", ""])

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def _build_source_tags_map(cfg: EndocytosisConfig) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for source in cfg.sources:
        name = source.get("name", "")
        tags = source.get("tags", ["ai"])
        if name:
            result[name] = tags if isinstance(tags, list) else [tags]
    return result


def _filter_by_tags(
    items: list[dict[str, Any]],
    tags: list[str],
    source_tags: dict[str, list[str]],
    source_key: str = "source",
) -> list[dict[str, Any]]:
    tag_set = set(tags)
    return [
        item for item in items if tag_set & set(source_tags.get(item.get(source_key, ""), ["ai"]))
    ]


# ---------------------------------------------------------------------------
# Weekly digest — lightweight endosome sorting, no LLM required.
# Substrate was already scored during fetch; this is pure membrane secretion.
# ---------------------------------------------------------------------------


def _resolve_week_label(week_date: datetime | None = None) -> tuple[str, str, str]:
    """Return (iso_date_start, iso_date_end, week_label) for the past 7 days.

    week_date: anchor datetime (defaults to now). The window is [anchor-7d, anchor].
    week_label format: YYYY-WNN (ISO year + zero-padded ISO week number).
    """
    if week_date is None:
        week_date = datetime.now(UTC)
    end_date = week_date
    start_date = end_date - timedelta(days=7)
    # ISO week label — use the end date's ISO calendar to label the digest
    iso_year, iso_week, _ = end_date.isocalendar()
    week_label = f"{iso_year}-W{iso_week:02d}"
    return (
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d"),
        week_label,
    )


def recall_log_entries(cargo_path: Path, since_date: str) -> list[dict[str, str]]:
    """Recall cargo entries from the JSONL store since a given date.

    Returns a list of dicts with: title, source, date, link, banking_angle,
    summary, _transcytose ('1' if score >= transcytose threshold or fate == 'transcytose').
    """
    from metabolon.organelles.endocytosis_rss.cargo import recall_cargo

    entries: list[dict[str, str]] = []
    for item in recall_cargo(cargo_path, since=since_date):
        score = int(item.get("score", 0))
        transcytose = score >= WEEKLY_TRANSCYTOSE_THRESHOLD or item.get("fate") == "transcytose"
        entries.append({
            "title": str(item.get("title", "")),
            "source": str(item.get("source", "")),
            "date": str(item.get("date", "")),
            "link": str(item.get("link", "")),
            "banking_angle": str(item.get("banking_angle", "")),
            "summary": str(item.get("summary", "")),
            "_transcytose": "1" if transcytose else "0",
        })
    return entries


def recall_affinity_entries(since_date: str) -> list[dict[str, Any]]:
    """Load scored cargo from the affinity log for the weekly window.

    Affinity log has richer metadata (score, banking_angle, talking_point)
    than the markdown log. Used to enrich weekly digest items.
    """
    from metabolon.organelles.endocytosis_rss.relevance import AFFINITY_LOG, _read_jsonl

    cutoff = datetime.strptime(since_date, "%Y-%m-%d").replace(tzinfo=UTC)
    items: list[dict[str, Any]] = []
    for entry in _read_jsonl(AFFINITY_LOG):
        raw_ts = entry.get("timestamp", "")
        try:
            ts = datetime.fromisoformat(str(raw_ts))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=UTC)
        except (ValueError, TypeError):
            continue
        if ts >= cutoff:
            items.append(entry)
    return items


def _build_affinity_index(affinity_entries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Index affinity log entries by title for O(1) enrichment lookups."""
    index: dict[str, dict[str, Any]] = {}
    for entry in affinity_entries:
        title = str(entry.get("title", "")).strip()
        if title and title not in index:
            index[title] = entry
    return index


def secrete_weekly_digest(
    output_path: Path,
    week_label: str,
    since_date: str,
    until_date: str,
    entries: list[dict[str, str]],
    affinity_index: dict[str, dict[str, Any]],
) -> Path:
    """Secrete the weekly digest to markdown.

    Groups entries by source. Transcytose items (★) are surfaced first with
    banking_angle and talking_point for client conversations.
    Items with score < WEEKLY_STORE_THRESHOLD from the affinity log are omitted
    (lysosomal fate — degraded, not secreted).
    """
    now = datetime.now().astimezone()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Separate transcytose (★) items for the headline section
    transcytose_entries = [e for e in entries if e.get("_transcytose") == "1"]

    # Group all entries by source, filtering by score threshold
    by_source: dict[str, list[dict[str, str]]] = {}
    for entry in entries:
        title = entry["title"]
        # Look up score in affinity index; fall back to transcytose marker
        affinity = affinity_index.get(title, {})
        score = int(affinity.get("score", 0))
        if score == 0 and entry.get("_transcytose") == "1":
            # ★ items scored >= 7 at log time; use threshold as floor
            score = WEEKLY_TRANSCYTOSE_THRESHOLD
        if score < WEEKLY_STORE_THRESHOLD:
            # Low-signal cargo: lysosomal fate, not secreted in weekly digest
            continue
        source = entry.get("source", "Unknown")
        by_source.setdefault(source, []).append({**entry, "_score": str(score)})

    # Sort each source's entries by score descending
    for source in by_source:
        by_source[source].sort(key=lambda e: int(e.get("_score", "0")), reverse=True)

    lines: list[str] = [
        f"# Weekly AI Digest — {week_label}",
        "",
        f"Period: {since_date} to {until_date}",
        f"Generated: {now.strftime('%Y-%m-%d %H:%M %Z')}",
        "",
        "---",
        "",
    ]

    # Headline section: transcytose items surface to the client membrane first
    if transcytose_entries:
        lines.append("## Transcytose — High Signal (score >= 7)")
        lines.append("")
        lines.append("_Items that crossed the membrane: ready for client conversation._")
        lines.append("")
        for entry in transcytose_entries:
            title = entry["title"]
            link = entry.get("link", "")
            source = entry.get("source", "")
            affinity = affinity_index.get(title, {})
            banking_angle = entry.get("banking_angle") or str(affinity.get("banking_angle", ""))
            talking_point = str(affinity.get("talking_point", ""))
            title_md = f"[{title}]({link})" if link else title
            lines.append(f"- **{title_md}** — _{source}_")
            if banking_angle and banking_angle not in ("N/A", ""):
                lines.append(f"  - Banking angle: {banking_angle}")
            if talking_point and talking_point not in ("N/A", ""):
                lines.append(f"  - Talking point: {talking_point}")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Per-source sections: grouped cargo
    if by_source:
        lines.append("## By Source")
        lines.append("")
        for source, source_entries in sorted(by_source.items()):
            lines.append(f"### {source}")
            lines.append("")
            for entry in source_entries:
                title = entry["title"]
                link = entry.get("link", "")
                score = entry.get("_score", "0")
                marker = "★ " if entry.get("_transcytose") == "1" else ""
                title_md = f"[{title}]({link})" if link else title
                summary = entry.get("summary", "")
                summary_part = f" — {summary}" if summary else ""
                lines.append(f"- {marker}**{title_md}** [{score}/10]{summary_part}")
            lines.append("")
    else:
        lines.append("_No items met the score threshold this week._")
        lines.append("")

    # Scheduling note: wire for Sunday night so Monday brief has fresh signal
    lines.extend(
        [
            "---",
            "",
            "<!-- Schedule: run Sunday ~22:00 HKT so Monday morning brief has fresh signal -->",
            "<!-- Command: vivesca endocytosis digest --weekly -->",
            "",
        ]
    )

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def _synthesize_weekly_brief(model: str, scored_content: str, week_label: str) -> str:
    """LLM synthesis of the scored weekly items into a concise brief."""
    system = (
        "You write concise weekly AI briefings for a consultant advising banks on AI strategy. "
        "Be specific — names, dates, numbers. No filler."
    )
    user = (
        f"Below is the scored weekly AI digest for {week_label}.\n\n"
        "Write a brief with:\n"
        "1. **Top 3 signals** — the most actionable developments this week (2-3 sentences each)\n"
        "2. **Themes** — 3-5 recurring patterns across sources\n"
        "3. **Watch list** — 2-3 things to track next week\n\n"
        "Keep it under 500 words. Banking/fintech lens.\n\n"
        f"{scored_content}"
    )
    return _llm_call(model, system, user)


def metabolize_weekly(
    cfg: EndocytosisConfig,
    week_date: datetime | None = None,
    tags: list[str] | None = None,
) -> tuple[int, Path | None]:
    """Secrete the weekly digest — scored list + LLM synthesis brief.

    Returns (item_count, output_path).
    """
    since_date, until_date, week_label = _resolve_week_label(week_date)
    model_id = cfg.digest_model

    # Internalize log entries for the window
    entries = recall_log_entries(cfg.cargo_path, since_date)

    if tags:
        source_tags = _build_source_tags_map(cfg)
        entries = [
            e for e in entries if set(tags) & set(source_tags.get(e.get("source", ""), ["ai"]))
        ]

    # Enrich with affinity log for score + talking_point data
    affinity_entries = recall_affinity_entries(since_date)
    affinity_index = _build_affinity_index(affinity_entries)

    # Secrete to ~/epigenome/chromatin/chemosensory/weekly-ai-digest-YYYY-WNN.md
    from metabolon.locus import chemosensory

    output_dir = chemosensory
    output_path = output_dir / f"weekly-ai-digest-{week_label}.md"

    written_path = secrete_weekly_digest(
        output_path=output_path,
        week_label=week_label,
        since_date=since_date,
        until_date=until_date,
        entries=entries,
        affinity_index=affinity_index,
    )

    # Count items that made it through the score threshold
    item_count = sum(
        1
        for e in entries
        if (
            int(affinity_index.get(e["title"], {}).get("score", 0)) >= WEEKLY_STORE_THRESHOLD
            or e.get("_transcytose") == "1"
        )
    )

    # LLM synthesis: append brief to the scored digest
    if item_count > 0 and written_path is not None:
        try:
            scored_content = written_path.read_text(encoding="utf-8")
            brief = _synthesize_weekly_brief(model_id, scored_content, week_label)
            # Prepend the synthesis brief before the scored list
            with written_path.open("w", encoding="utf-8") as f:
                f.write(brief)
                f.write("\n\n---\n\n")
                f.write(scored_content)
        except Exception as exc:
            import sys
            print(f"endocytosis: weekly synthesis failed: {exc}", file=sys.stderr)
            # Scored digest still exists, just without synthesis

    return item_count, written_path


def _recall_weekly_digests(month: str) -> list[tuple[str, str]]:
    """Read weekly digest files for a given month. Returns [(filename, content)]."""
    from metabolon.locus import chemosensory

    year, month_num = month.split("-")
    # Find weekly digests whose ISO week falls in this month
    results: list[tuple[str, str]] = []
    for path in sorted(chemosensory.glob(f"weekly-ai-digest-{year}-W*.md")):
        # Parse week number, check if it overlaps the target month
        week_str = path.stem.split("-W")[-1]
        try:
            week_num = int(week_str)
        except ValueError:
            continue
        # Approximate: week N maps to month via ISO calendar
        week_date = datetime.strptime(f"{year}-W{week_num:02d}-1", "%Y-W%W-%w").date()
        if week_date.strftime("%Y-%m") == month or (
            week_date.month == int(month_num)
        ):
            results.append((path.name, path.read_text(encoding="utf-8")))
    return results


def metabolize_digest(
    cfg: EndocytosisConfig,
    month: str | None,
    dry_run: bool,
    themes: int | None,
    model: str | None,
    tags: list[str] | None = None,
) -> tuple[list[dict[str, Any]], Path | None]:
    target_month = _resolve_month(month)
    max_themes = themes if themes is not None else DEFAULT_THEME_COUNT
    model_id = model or cfg.digest_model

    # Try weekly digests first — much smaller input, already curated
    weekly_digests = _recall_weekly_digests(target_month)
    if weekly_digests:
        return _metabolize_from_weeklies(
            weekly_digests=weekly_digests,
            model_id=model_id,
            max_themes=max_themes,
            dry_run=dry_run,
            output_dir=cfg.digest_output_dir,
            target_month=target_month,
        )

    # Fallback: raw articles (for months without weekly digests)
    articles = recall_archived_articles(cfg.article_cache_dir, target_month)
    log_entries = recall_news_entries(cfg.cargo_path, target_month)

    if tags:
        source_tags = _build_source_tags_map(cfg)
        articles = _filter_by_tags(articles, tags, source_tags)
        log_entries = _filter_by_tags(log_entries, tags, source_tags)
    if not articles and not log_entries:
        raise RuntimeError(
            f"No data found for {target_month}. Run `vivesca endocytosis fetch` first."
        )

    identified_themes = sense_themes(
        model=model_id,
        articles=articles,
        log_entries=log_entries,
        max_themes=max_themes,
    )
    if dry_run:
        return identified_themes, None

    briefs = [
        synthesize_theme(model_id, theme, articles, log_entries)
        for theme in identified_themes
    ]
    output_path = secrete_digest(
        output_dir=cfg.digest_output_dir,
        month=target_month,
        themes=identified_themes,
        theme_briefs=briefs,
    )
    return identified_themes, output_path


def _metabolize_from_weeklies(
    weekly_digests: list[tuple[str, str]],
    model_id: str,
    max_themes: int,
    dry_run: bool,
    output_dir: Path,
    target_month: str,
) -> tuple[list[dict[str, Any]], Path | None]:
    """Synthesize monthly themes from weekly digest files."""
    combined = "\n\n---\n\n".join(
        f"# {name}\n\n{content}" for name, content in weekly_digests
    )

    system = (
        "You identify thematic clusters across weekly AI news digests for a consultant"
        " advising banks on AI strategy.\n\n"
        f"Rules:\n- Identify {max_themes} themes most relevant"
        " to AI in banking/financial services\n"
        "- Each theme should appear across multiple weeks\n"
        '- Themes should be specific (not "AI progress")\n'
        "- Include cross-cutting themes (regulation, open-source vs proprietary, infrastructure)\n"
        "- Return valid JSON only, no markdown fences"
    )
    user = (
        f"Below are {len(weekly_digests)} weekly AI digests from {target_month}.\n\n"
        f"Identify up to {max_themes} thematic clusters. Return JSON:\n"
        "[\n"
        "  {\n"
        '    "theme": "Theme title",\n'
        '    "description": "2-3 sentence description of the month-long trend",\n'
        '    "weeks_present": ["W10", "W12"],\n'
        '    "banking_relevance": "Why this matters for banks/fintech"\n'
        "  }\n"
        "]\n\n"
        "Weekly digests:\n" + combined
    )
    raw = _llm_call(model_id, system, user)
    identified_themes = _parse_theme_json(raw)

    if dry_run:
        return identified_themes, None

    # Synthesize briefs from the weekly content (no raw articles needed)
    briefs: list[str] = []
    for theme in identified_themes:
        brief = _llm_call(
            model_id,
            "You write concise monthly theme briefs for a banking AI consultant.",
            f"Theme: {theme.get('theme', '')}\n"
            f"Description: {theme.get('description', '')}\n"
            f"Banking relevance: {theme.get('banking_relevance', '')}\n\n"
            f"Source material (weekly digests):\n{combined}\n\n"
            "Write a 3-5 paragraph brief covering: what happened, why it matters "
            "for banks, and what to watch next month. Be specific with names and dates.",
        )
        briefs.append(brief)

    output_path = secrete_digest(
        output_dir=output_dir,
        month=target_month,
        themes=identified_themes,
        theme_briefs=briefs,
    )
    return identified_themes, output_path
