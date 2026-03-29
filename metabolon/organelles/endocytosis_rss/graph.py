"""Endocytosis LangGraph pipeline — continuous info metabolism.

Fetch → Extract (opus) → Score → Sort → Store.
Hourly via LaunchAgent. Weekly brief + monthly digest as conditional nodes.

Biological mapping:
  - fetch: receptor-mediated endocytosis (internalize ligands)
  - extract: endosomal processing (partially cleave cargo)
  - score: receptor affinity assessment
  - sort: endosome sorting (transcytose / store / degrade)
  - weekly_brief: signal transduction (convert cargo → actionable signal)
  - monthly_digest: gene expression (long-term pattern → stored knowledge)
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from metabolon.organelles.endocytosis_rss.config import EndocytosisConfig, restore_config
from metabolon.symbiont import transduce


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class Article(TypedDict, total=False):
    title: str
    link: str
    summary: str
    source: str
    date: str
    text: str
    score: str
    banking_angle: str
    talking_point: str
    extraction: dict[str, Any]  # opus-extracted card
    timestamp: str


class PipelineState(TypedDict, total=False):
    cfg: dict[str, Any]  # serialized config paths
    new_articles: list[Article]
    extracted: list[Article]
    scored: list[Article]
    stored_count: int
    weekly_brief: str
    monthly_digest: str
    run_time: str


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

_EXTRACTION_PROMPT = """You are extracting key information from an AI/tech news article
for a consultant advising banks on AI strategy.

Article:
Title: {title}
Source: {source}
Summary: {summary}
Full text (if available): {text}

Extract to JSON (no markdown fences):
{{
  "claim": "The single most important claim or development (1 sentence)",
  "banking_relevance": "Why a bank client would care (1 sentence)",
  "stat": "Key number/metric if present, or null",
  "source_quality": "tier1/tier2/noise",
  "action": "watch/brief/ignore",
  "tags": ["tag1", "tag2"]
}}"""


def _extract_one(article: Article) -> dict[str, Any]:
    """Extract structured card from one article using opus via channel."""
    prompt = _EXTRACTION_PROMPT.format(
        title=article.get("title", ""),
        source=article.get("source", ""),
        summary=article.get("summary", ""),
        text=(article.get("text", "") or "")[:3000],
    )
    try:
        raw = transduce("opus", prompt, timeout=120)
        text = raw.strip()
        if text.startswith("```"):
            import re
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        # Find JSON object
        brace_start = text.find("{")
        brace_end = text.rfind("}")
        if brace_start >= 0 and brace_end > brace_start:
            text = text[brace_start : brace_end + 1]
        return json.loads(text)
    except Exception as exc:
        print(f"endocytosis-graph: extraction failed for {article.get('title', '?')[:60]}: {exc}",
              file=sys.stderr)
        return {"claim": article.get("summary", ""), "error": str(exc)}


def fetch_node(state: PipelineState) -> dict[str, Any]:
    """Fetch new articles from all sources. Reuses existing internalize logic."""
    from metabolon.organelles.endocytosis_rss.cli import _fetch_locked
    from metabolon.organelles.endocytosis_rss.state import restore_state, persist_state
    from metabolon.organelles.endocytosis_rss.log import (
        _title_prefix, cycle_log, is_noise, recall_title_prefixes,
        record_cargo, serialize_markdown,
    )
    from metabolon.organelles.endocytosis_rss.relevance import (
        assess_cargo, receptor_signal_ratio, record_affinity,
    )
    from metabolon.organelles.endocytosis_rss.fetcher import archive_cargo
    from metabolon.organelles.endocytosis_rss.sorting import select_for_log
    from metabolon.organelles.endocytosis_rss.cli import (
        refractory_elapsed, _get_last_scan_date, _source_since_date, lockfile,
    )

    cfg = restore_config()
    fetch_state = restore_state(cfg.state_path)
    now = datetime.now(UTC)

    cycle_log(cfg.log_path, cfg.data_dir, cfg.config_data.get("max_log_lines", 500), now)
    global_since_date = _get_last_scan_date(fetch_state)
    title_prefixes = recall_title_prefixes(cfg.log_path)

    from metabolon.organelles.endocytosis_rss.fetcher import (
        internalize_rss, internalize_web, internalize_json_api,
        internalize_x_account, internalize_x_bookmarks,
        internalize_linkedin, release_bookmarks,
    )

    all_new: list[Article] = []
    results: dict[str, list[dict]] = {}
    _nodriver_profile = Path(
        cfg.config_data.get("nodriver_profile_dir",
                            Path.home() / ".config" / "lustro" / "nodriver-profile")
    )

    for source in cfg.sources:
        name = source["name"]
        cadence = source.get("cadence", "daily")
        tier = source.get("tier", 2)
        signal_ratio = receptor_signal_ratio(name)

        if not refractory_elapsed(fetch_state, name, cadence, now=now, signal_ratio=signal_ratio):
            continue

        print(f"Fetching: {name}...", file=sys.stderr)
        since_date = _source_since_date(fetch_state, name, global_since_date, cadence=cadence, now=now)

        # Route to appropriate fetcher
        articles: list[dict] | None = None
        if source.get("bookmarks"):
            articles = internalize_x_bookmarks(since_date, bird_path=cfg.resolve_bird())
        elif "api" in source:
            articles = internalize_json_api(source["api"], since_date,
                                            title_key=source.get("api_title_key", "title"),
                                            link_key=source.get("api_link_key", "link"),
                                            date_key=source.get("api_date_key", "date"))
        elif "rss" in source:
            articles = internalize_rss(source["rss"], since_date,
                                       full_fetch=bool(source.get("full_fetch", False)),
                                       stealth_fetch=bool(source.get("stealth_fetch", False)),
                                       profile_dir=_nodriver_profile)
            if articles is None and "url" in source:
                articles = internalize_web(source["url"], selector=source.get("selector"),
                                           stealth=bool(source.get("stealth_web", False)),
                                           profile_dir=_nodriver_profile)
        elif "handle" in source:
            articles = internalize_x_account(source["handle"], since_date,
                                              bird_path=cfg.resolve_bird())
        else:
            articles = internalize_web(source.get("url", ""),
                                        selector=source.get("selector"),
                                        stealth=bool(source.get("stealth_web", False)),
                                        profile_dir=_nodriver_profile)

        if not articles:
            z_key = f"_zeros:{name}"
            fetch_state[z_key] = str(int(fetch_state.get(z_key, 0)) + 1)
            if name not in fetch_state:
                fetch_state[name] = now.isoformat()
            persist_state(cfg.state_path, fetch_state)
            continue

        # Deduplicate
        new_articles = []
        for article in articles:
            if is_noise(article["title"]):
                continue
            prefix = _title_prefix(article["title"])
            if prefix in title_prefixes:
                continue
            new_articles.append(article)
            title_prefixes.add(prefix)

        for article in new_articles:
            article["source"] = name
            article["timestamp"] = now.isoformat()
            all_new.append(article)

        if new_articles:
            results[name] = new_articles
            fetch_state[name] = now.isoformat()
            fetch_state.pop(f"_zeros:{name}", None)

        persist_state(cfg.state_path, fetch_state)

    # Log to news log (existing behavior)
    if results:
        sorted_results: dict[str, list[dict]] = {}
        for source_name, source_articles in results.items():
            survivors = select_for_log(source_articles)
            if survivors:
                sorted_results[source_name] = survivors
        if sorted_results:
            today = now.strftime("%Y-%m-%d")
            md = serialize_markdown(sorted_results, today)
            record_cargo(cfg.log_path, md)

    print(f"endocytosis-graph: fetched {len(all_new)} new articles", file=sys.stderr)
    return {"new_articles": all_new, "run_time": now.isoformat()}


def extract_node(state: PipelineState) -> dict[str, Any]:
    """Opus extraction on each new article — endosomal processing."""
    articles = state.get("new_articles", [])
    if not articles:
        return {"extracted": []}

    extracted: list[Article] = []
    for article in articles:
        card = _extract_one(article)
        article_with_extraction = {**article, "extraction": card}
        extracted.append(article_with_extraction)
        print(f"  Extracted: {article.get('title', '?')[:60]}", file=sys.stderr)

    print(f"endocytosis-graph: extracted {len(extracted)} articles", file=sys.stderr)
    return {"extracted": extracted}


def score_node(state: PipelineState) -> dict[str, Any]:
    """Score articles for consulting relevance. Uses existing assess_cargo."""
    from metabolon.organelles.endocytosis_rss.relevance import assess_cargo, record_affinity

    articles = state.get("extracted", [])
    scored: list[Article] = []

    for article in articles:
        # Skip if already scored during fetch
        if article.get("score") and article["score"] != "0":
            scored.append(article)
            continue
        scores = assess_cargo(
            article.get("title", ""),
            article.get("source", ""),
            article.get("summary", ""),
        )
        article["score"] = str(scores.get("score", 0))
        article["banking_angle"] = str(scores.get("banking_angle", ""))
        article["talking_point"] = str(scores.get("talking_point", ""))
        record_affinity(article, scores)
        scored.append(article)

    return {"scored": scored}


def store_node(state: PipelineState) -> dict[str, Any]:
    """Persist extracted cards to cache for downstream consumption."""
    articles = state.get("scored", [])
    cfg = restore_config()
    cards_dir = cfg.cache_dir / "cards"
    cards_dir.mkdir(parents=True, exist_ok=True)

    stored = 0
    for article in articles:
        extraction = article.get("extraction", {})
        if not extraction or extraction.get("error"):
            continue
        # Build card filename from date + title hash
        import hashlib
        title = article.get("title", "untitled")
        date = article.get("date", datetime.now().strftime("%Y-%m-%d"))
        slug = hashlib.sha256(title.encode()).hexdigest()[:8]
        card_path = cards_dir / f"{date}_{slug}.json"
        card_data = {
            "title": title,
            "source": article.get("source", ""),
            "link": article.get("link", ""),
            "date": date,
            "score": article.get("score", "0"),
            "banking_angle": article.get("banking_angle", ""),
            "talking_point": article.get("talking_point", ""),
            "extraction": extraction,
            "timestamp": article.get("timestamp", ""),
        }
        card_path.write_text(json.dumps(card_data, indent=2, ensure_ascii=False), encoding="utf-8")
        stored += 1

    print(f"endocytosis-graph: stored {stored} cards", file=sys.stderr)
    return {"stored_count": stored}


def should_synthesize_weekly(state: PipelineState) -> str:
    """Check if it's Saturday — time for weekly brief."""
    now = datetime.now()
    if now.weekday() == 5:  # Saturday
        return "weekly_brief"
    return END


def weekly_brief_node(state: PipelineState) -> dict[str, Any]:
    """Synthesize weekly brief from this week's extracted cards."""
    cfg = restore_config()
    cards_dir = cfg.cache_dir / "cards"
    if not cards_dir.exists():
        return {"weekly_brief": ""}

    # Read this week's cards
    from datetime import timedelta
    now = datetime.now()
    week_start = (now - timedelta(days=now.weekday() + 2)).strftime("%Y-%m-%d")  # last Sunday

    cards: list[dict] = []
    for path in sorted(cards_dir.glob("*.json")):
        if path.stem >= week_start:
            try:
                cards.append(json.loads(path.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                continue

    if not cards:
        return {"weekly_brief": ""}

    # Build input from extractions
    items = []
    for card in sorted(cards, key=lambda c: int(c.get("score", "0")), reverse=True):
        ext = card.get("extraction", {})
        items.append(
            f"- [{card.get('score', '?')}/10] {card.get('title', '?')} ({card.get('source', '?')})\n"
            f"  Claim: {ext.get('claim', 'N/A')}\n"
            f"  Banking: {ext.get('banking_relevance', 'N/A')}\n"
            f"  Stat: {ext.get('stat', 'N/A')}"
        )

    prompt = (
        "You write concise weekly AI briefings for a consultant advising banks on AI strategy. "
        "Be specific — names, dates, numbers. No filler.\n\n---\n\n"
        f"Below are {len(cards)} pre-extracted article cards from this week, scored for consulting relevance.\n\n"
        "Write a brief with:\n"
        "1. **Top 3 signals** — the most actionable developments (2-3 sentences each)\n"
        "2. **Themes** — 3-5 recurring patterns\n"
        "3. **Watch list** — 2-3 things to track next week\n\n"
        "Under 500 words. Banking/fintech lens.\n\n"
        + "\n".join(items)
    )

    brief = transduce("opus", prompt, timeout=180)

    # Write to chromatin
    from metabolon.locus import chemosensory
    week_label = now.strftime("%Y-W%W")
    output_path = chemosensory / f"weekly-ai-digest-{week_label}.md"
    output_path.write_text(brief, encoding="utf-8")
    print(f"endocytosis-graph: weekly brief written to {output_path}", file=sys.stderr)

    return {"weekly_brief": brief}


def should_synthesize_monthly(state: PipelineState) -> str:
    """Check if it's the 1st — time for monthly digest."""
    now = datetime.now()
    if now.day == 1:
        return "monthly_digest"
    return END


def monthly_digest_node(state: PipelineState) -> dict[str, Any]:
    """Synthesize monthly digest from weekly briefs."""
    from metabolon.locus import chemosensory

    now = datetime.now()
    year = now.strftime("%Y")

    # Read this month's weekly briefs
    briefs: list[tuple[str, str]] = []
    for path in sorted(chemosensory.glob(f"weekly-ai-digest-{year}-W*.md")):
        content = path.read_text(encoding="utf-8")
        briefs.append((path.name, content))

    if not briefs:
        return {"monthly_digest": ""}

    combined = "\n\n---\n\n".join(f"# {name}\n\n{content}" for name, content in briefs)
    prompt = (
        "You write monthly AI landscape digests for a consultant advising banks. "
        "Be specific — names, dates, numbers. No filler.\n\n---\n\n"
        f"Below are {len(briefs)} weekly AI briefs from this month.\n\n"
        "Write a monthly digest with:\n"
        "1. **Month in review** — 3-5 sentence executive summary\n"
        "2. **Top themes** — 5-8 themes with trend direction (accelerating/stable/fading)\n"
        "3. **Strategic implications** — what this means for bank AI strategy\n"
        "4. **Next month outlook** — what to prepare for\n\n"
        "Under 800 words.\n\n" + combined
    )

    digest = transduce("opus", prompt, timeout=180)

    month_label = now.strftime("%Y-%m")
    output_path = chemosensory / f"monthly-ai-digest-{month_label}.md"
    output_path.write_text(digest, encoding="utf-8")
    print(f"endocytosis-graph: monthly digest written to {output_path}", file=sys.stderr)

    return {"monthly_digest": digest}


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    """Build the endocytosis LangGraph pipeline."""
    graph = StateGraph(PipelineState)

    graph.add_node("fetch", fetch_node)
    graph.add_node("extract", extract_node)
    graph.add_node("score", score_node)
    graph.add_node("store", store_node)
    graph.add_node("weekly_brief", weekly_brief_node)
    graph.add_node("monthly_digest", monthly_digest_node)

    graph.add_edge(START, "fetch")
    graph.add_edge("fetch", "extract")
    graph.add_edge("extract", "score")
    graph.add_edge("score", "store")
    graph.add_conditional_edges("store", should_synthesize_weekly,
                                {"weekly_brief": "weekly_brief", END: END})
    graph.add_conditional_edges("weekly_brief", should_synthesize_monthly,
                                {"monthly_digest": "monthly_digest", END: END})
    graph.add_edge("monthly_digest", END)

    return graph


def run() -> dict[str, Any]:
    """Run the full pipeline once. Called by CLI/cron."""
    graph = build_graph()
    app = graph.compile()
    result = app.invoke({})
    return result


if __name__ == "__main__":
    run()
