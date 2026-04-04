
import sys
from datetime import UTC, datetime, timedelta
from importlib import metadata
from pathlib import Path

from typer import Exit, Option, Typer, echo

from metabolon.organelles.endocytosis_rss.config import (
    EndocytosisConfig,
    default_sources_text,
    restore_config,
)
from metabolon.organelles.endocytosis_rss.state import lockfile, refractory_elapsed, restore_state

app = Typer(help="endocytosis_rss — receptor-mediated endocytosis (RSS ingestion)")


def version_callback(value: bool) -> None:
    if value:
        echo(f"lustro {_get_version()}")
        raise Exit()


@app.callback()
def main_callback(
    version: bool = Option(False, "--version", callback=version_callback, is_eager=True),
) -> None:
    pass


def _get_version() -> str:
    try:
        return metadata.version("metabolon")
    except metadata.PackageNotFoundError:
        return "dev"


def _file_age(path: Path, now: datetime) -> str:
    if not path.exists():
        return "missing"
    modified = datetime.fromtimestamp(path.stat().st_mtime, tz=now.tzinfo)
    delta = now - modified
    if delta.total_seconds() < 60:
        return "just now"
    if delta.total_seconds() < 3600:
        return f"{int(delta.total_seconds() // 60)}m ago"
    if delta.total_seconds() < 86400:
        return f"{int(delta.total_seconds() // 3600)}h ago"
    return f"{delta.days}d ago"


def _parse_aware(value: str) -> datetime | None:
    try:
        dt = datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


def _get_last_scan_date(state: dict[str, str]) -> str:
    dates = []
    for value in state.values():
        dt = _parse_aware(value)
        if dt is not None:
            dates.append(dt)
    if dates:
        # Subtract one day so articles published on the same calendar day as the
        # last scan are not filtered out (date comparison is <=, not <).
        return (max(dates) - timedelta(days=1)).strftime("%Y-%m-%d")
    return (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d")


_CADENCE_LOOKBACK: dict[str, int] = {
    "daily": 2,
    "twice_weekly": 5,
    "weekly": 10,
    "biweekly": 20,
    "monthly": 35,
}


def _source_since_date(
    state: dict[str, str],
    name: str,
    fallback: str,
    cadence: str = "daily",
    now: datetime | None = None,
) -> str:
    """Per-source since_date: own last-scan timestamp, or cadence-appropriate lookback for new sources."""
    val = state.get(name)
    if val:
        dt = _parse_aware(val)
        if dt is not None:
            # Subtract one day so same-day articles are not filtered by the <= comparison.
            return (dt - timedelta(days=1)).strftime("%Y-%m-%d")
    # New source: use cadence-aware lookback instead of global since_date
    # (global date is "today" when other sources ran today, causing new sources to find nothing)
    lookback_days = _CADENCE_LOOKBACK.get(cadence, 2)
    if now is None:
        now = datetime.now(UTC)
    lookback = (now - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    # Use whichever gives more history
    return min(fallback, lookback)


@app.command()
def internalize(
    no_archive: bool = Option(False, "--no-archive", help="Skip archiving full article text"),
) -> None:
    cfg = restore_config()
    with lockfile(cfg.state_path):
        _fetch_locked(cfg, no_archive)


def _fetch_locked(cfg: EndocytosisConfig, no_archive: bool) -> None:
    state = restore_state(cfg.state_path)
    from metabolon.organelles.endocytosis_rss.cargo import (
        append_cargo,
        rotate_cargo,
    )
    from metabolon.organelles.endocytosis_rss.cargo import (
        recall_title_prefixes as recall_cargo_prefixes,
    )
    from metabolon.organelles.endocytosis_rss.fetcher import (
        archive_cargo,
        internalize_json_api,
        internalize_linkedin,
        internalize_rss,
        internalize_web,
        internalize_x_account,
        internalize_x_bookmarks,
        release_bookmarks,
    )
    from metabolon.organelles.endocytosis_rss.log import (
        _title_prefix,
        is_noise,
        recall_title_prefixes,
    )
    from metabolon.organelles.endocytosis_rss.relevance import (
        BATCH_SIZE,
        assess_cargo_batch,
        receptor_signal_ratio,
        record_affinity,
    )
    from metabolon.organelles.endocytosis_rss.state import persist_state

    now = datetime.now(UTC)

    global_since_date = _get_last_scan_date(state)
    title_prefixes = recall_cargo_prefixes(cfg.cargo_path)
    title_prefixes |= recall_title_prefixes(cfg.log_path)
    results: dict[str, list[dict[str, str]]] = {}
    failed_sources: list[str] = []
    archived_count = 0
    bookmark_ids_to_clear: list[str] = []
    _nodriver_profile = Path(
        cfg.config_data.get(
            "nodriver_profile_dir",
            Path.home() / ".config" / "lustro" / "nodriver-profile",
        )
    )

    for source in cfg.sources:
        name = source["name"]
        cadence = source.get("cadence", "daily")
        tier = source.get("tier", 2)

        # Receptor downregulation: measure the source's signal-to-noise ratio
        # and extend the refractory period for chronically noisy sources so the
        # cell is not flooded with irrelevant ligands.
        signal_ratio = receptor_signal_ratio(name)
        if not refractory_elapsed(state, name, cadence, now=now, signal_ratio=signal_ratio):
            echo(f"Skipping: {name} (cadence)", err=True)
            continue

        echo(f"Fetching: {name}...", err=True)
        fetch_failed = False
        since_date = _source_since_date(state, name, global_since_date, cadence=cadence, now=now)
        if source.get("bookmarks"):
            articles = internalize_x_bookmarks(since_date, bird_path=cfg.resolve_bird())
        elif "api" in source:
            articles = internalize_json_api(
                source["api"],
                since_date,
                title_key=source.get("api_title_key", "title"),
                link_key=source.get("api_link_key", "link"),
                date_key=source.get("api_date_key", "date"),
            )
            if articles is None:
                fetch_failed = True
                failed_sources.append(f"{name} (json api error)")
                articles = []
        elif "rss" in source:
            articles = internalize_rss(
                source["rss"],
                since_date,
                full_fetch=bool(source.get("full_fetch", True)),
                stealth_fetch=bool(source.get("stealth_fetch", False)),
                profile_dir=_nodriver_profile,
            )
            if articles is None:
                if "url" in source:
                    echo(f"  RSS dead, falling back to web: {source['url']}", err=True)
                    articles = internalize_web(
                        source["url"],
                        selector=source.get("selector"),
                        stealth=bool(source.get("stealth_web", False)),
                        profile_dir=_nodriver_profile,
                        link_template=source.get("link_template"),
                    )
                if articles is None:
                    fetch_failed = True
                    failed_sources.append(f"{name} (RSS dead)")
            articles = articles or []
        elif "handle" in source:
            articles = internalize_x_account(
                source["handle"], since_date, bird_path=cfg.resolve_bird()
            )
        elif "linkedin" in source:
            articles = internalize_linkedin(
                source["linkedin"],
                since_date,
                agent_browser_bin=cfg.config_data.get("agent_browser_bin", "agent-browser"),
            )
            if articles is None:
                fetch_failed = True
                failed_sources.append(f"{name} (linkedin error)")
                articles = []
        else:
            articles = internalize_web(
                source.get("url", ""),
                selector=source.get("selector"),
                stealth=bool(source.get("stealth_web", False)),
                profile_dir=_nodriver_profile,
                link_template=source.get("link_template"),
            )
            if articles is None:
                fetch_failed = True
                failed_sources.append(f"{name} (web error)")
                articles = []

        if fetch_failed:
            f_key = f"_fail:{name}"
            state[f_key] = str(int(state.get(f_key, 0)) + 1)

        new_articles = []
        for article in articles:
            if is_noise(article["title"]):
                continue
            prefix = _title_prefix(article["title"])
            if prefix in title_prefixes:
                continue
            new_articles.append(article)
            title_prefixes.add(prefix)

        # Batch scoring: collect articles into batches and score in bulk
        scored_articles = []
        for batch_start in range(0, len(new_articles), BATCH_SIZE):
            batch = new_articles[batch_start : batch_start + BATCH_SIZE]
            batch_tuples = [(a.get("title", ""), name, a.get("summary", "")) for a in batch]
            batch_scores = assess_cargo_batch(batch_tuples)
            for article, scores in zip(batch, batch_scores):
                if scores.get("unscored"):
                    print(
                        f"  UNSCORED (Opus down): {article.get('title', '')[:60]}",
                        file=sys.stderr,
                    )
                    continue
                article["source"] = name
                article["timestamp"] = now.isoformat()
                article["score"] = str(scores.get("score", 0))
                article["banking_angle"] = str(scores.get("banking_angle", ""))
                article["talking_point"] = str(scores.get("talking_point", ""))
                record_affinity(article, scores)
                scored_articles.append(article)
        new_articles = scored_articles

        if not no_archive:
            for article in new_articles:
                if article.get("link"):
                    archive_cargo(article, name, tier, cfg.article_cache_dir, now)
                    archived_count += 1

        if source.get("bookmarks"):
            for article in new_articles:
                tid = article.pop("_tweet_id", "")
                if tid:
                    bookmark_ids_to_clear.append(tid)

        if new_articles:
            results[name] = new_articles
            state[name] = now.isoformat()
            state.pop(f"_zeros:{name}", None)
        else:
            if name not in state:
                state[name] = now.isoformat()
            z_key = f"_zeros:{name}"
            zeros = int(state.get(z_key, 0)) + 1
            state[z_key] = str(zeros)
            _zero_threshold = {
                "daily": 5,
                "twice_weekly": 4,
                "weekly": 3,
                "biweekly": 3,
                "monthly": 5,
            }.get(cadence, 5)
            if zeros >= _zero_threshold:
                echo(
                    f"  Warning: {name} has {zeros} consecutive zero-article fetches",
                    err=True,
                )

        # Persist after each source so state survives mid-run timeouts.
        persist_state(cfg.state_path, state)

    persist_state(cfg.state_path, state)
    if failed_sources:
        echo(f"Fetch errors ({len(failed_sources)}): {', '.join(failed_sources)}", err=True)
    if not results:
        echo("No new articles found.", err=True)
        raise Exit(code=0)

    # Endosome sorting: route each source's cargo to fate compartments.
    # Only store + transcytose cargo survives to the news log; degrade cargo
    # is silently dropped (lysosomal fate — not persisted).
    from metabolon.organelles.endocytosis_rss.sorting import select_for_log

    sorted_results: dict[str, list[dict[str, str]]] = {}
    degraded_count = 0
    for source_name, source_articles in results.items():
        survivors = select_for_log(source_articles)
        dropped = len(source_articles) - len(survivors)
        degraded_count += dropped
        if survivors:
            sorted_results[source_name] = survivors

    if degraded_count:
        echo(f"Endosome: {degraded_count} low-signal items degraded (not logged).", err=True)

    if not sorted_results:
        echo("No articles survived endosome sorting.", err=True)
        raise Exit(code=0)

    # Write JSONL canonical cargo store
    flat_cargo = []
    for source_name, source_articles in sorted_results.items():
        for article in source_articles:
            article["fate"] = "transcytose" if int(article.get("score", 0)) >= 7 else "store"
            flat_cargo.append(article)
    append_cargo(cfg.cargo_path, flat_cargo)
    rotate_cargo(cfg.cargo_path, cfg.data_dir / "archive", retain_days=14, now=now)

    total = sum(len(v) for v in sorted_results.values())
    echo(f"Logged {total} new articles.", err=True)
    if bookmark_ids_to_clear:
        release_bookmarks(bookmark_ids_to_clear, bird_path=cfg.resolve_bird())
    raise Exit(code=0)


@app.command()
def probe_receptors() -> None:
    cfg = restore_config()
    state = restore_state(cfg.state_path)
    from metabolon.organelles.endocytosis_rss.fetcher import probe_receptors

    web_sources = [s for s in cfg.sources if "handle" not in s and not s.get("bookmarks")]
    x_accounts = [s for s in cfg.sources if "handle" in s]
    x_bookmarks = [s for s in cfg.sources if s.get("bookmarks")]
    probe_receptors(
        web_sources, x_accounts, state, bird_path=cfg.resolve_bird(), x_bookmarks=x_bookmarks
    )
    raise Exit(code=0)


@app.command()
def digest(
    month: str | None = Option(None, "--month", help="Target month YYYY-MM"),
    dry_run: bool = Option(False, "--dry-run", help="Show themes only"),
    themes: int | None = Option(None, "--themes", help="Max themes"),
    model: str | None = Option(None, "--model", help="Model ID"),
    tag: list[str] | None = Option(None, "--tag", "-t", help="Filter by tag (repeatable)"),
    weekly: bool = Option(
        False,
        "--weekly",
        help="Secrete weekly digest (past 7 days, scored list + LLM synthesis)",
    ),
) -> None:
    cfg = restore_config()

    # Weekly secretion pathway: scored list + LLM synthesis, matches Sunday-night schedule.
    # Substrate was already scored during fetch; dry_run skips file write + LLM.
    if weekly:
        from metabolon.organelles.endocytosis_rss.digest import metabolize_weekly

        try:
            item_count, output_path = metabolize_weekly(
                cfg=cfg,
                tags=tag or [],
                dry_run=dry_run,
            )
        except Exception as exc:
            echo(f"Error: {exc}", err=True)
            raise Exit(code=1) from exc

        echo(f"Weekly digest: {item_count} items above threshold.", err=True)
        if output_path is not None:
            echo(f"Written: {output_path}", err=True)
        raise Exit(code=0)

    # Monthly thematic digest pathway: LLM-powered theme identification.
    from metabolon.organelles.endocytosis_rss.digest import metabolize_digest

    try:
        themes_result, output_path = metabolize_digest(
            cfg=cfg,
            month=month,
            dry_run=dry_run,
            themes=themes,
            model=model,
            tags=tag or [],
        )
    except RuntimeError as exc:
        echo(f"Error: {exc}", err=True)
        raise Exit(code=1) from exc

    echo(f"Found {len(themes_result)} themes.", err=True)
    for i, theme in enumerate(themes_result, 1):
        name = theme.get("theme", f"Theme {i}")
        count = len(theme.get("article_indices", []))
        echo(f"{i}. {name} ({count} articles)", err=True)

    if dry_run:
        import json

        echo(json.dumps(themes_result, indent=2, ensure_ascii=False))
        raise Exit(code=0)

    if output_path is not None:
        echo(f"Digest written: {output_path}", err=True)
    raise Exit(code=0)


@app.command()
def inscribe(
    lines: int = Option(50, "--lines", "-n", help="Number of lines"),
) -> None:
    cfg = restore_config()
    if not cfg.log_path.exists():
        echo(f"Not found: {cfg.log_path}")
        raise Exit(code=1)
    log_lines = cfg.log_path.read_text(encoding="utf-8").splitlines()
    while log_lines and not log_lines[-1].strip():
        log_lines.pop()
    n = max(0, lines) if lines else 0
    if n and n < len(log_lines):
        log_lines = log_lines[-n:]
    echo("\n".join(log_lines))
    raise Exit(code=0)


@app.command()
def breaking(
    dry_run: bool = Option(False, "--dry-run"),
) -> None:
    cfg = restore_config()
    from metabolon.organelles.endocytosis_rss.breaking import scan_breaking

    result = scan_breaking(cfg=cfg, dry_run=dry_run)
    raise Exit(code=result)


@app.command()
def scout(
    count: int | None = Option(None, "--count", help="Number of tweets to scan"),
) -> None:
    cfg = restore_config()
    from metabolon.organelles.endocytosis_rss.discover import scout_sources

    result = scout_sources(cfg=cfg, count=count, bird_path=cfg.resolve_bird())
    raise Exit(code=result)


@app.command()
def sources(
    tier: int | None = Option(None, "--tier", help="Filter sources by tier"),
) -> None:
    cfg = restore_config()
    rows: list[tuple[str, str, int, str]] = []

    for section_name, section in cfg.sources_data.items():
        if not isinstance(section, list):
            continue
        for source in section:
            if not isinstance(source, dict):
                continue
            source_tier = int(source.get("tier", 2))
            if tier is not None and source_tier != tier:
                continue
            # Determine display type
            if source.get("bookmarks"):
                source_type = "bkmk"
            elif source.get("handle"):
                source_type = "x"
            elif source.get("api"):
                source_type = "api"
            elif source.get("rss"):
                source_type = "rss"
            elif source.get("linkedin"):
                source_type = "lnkd"
            else:
                source_type = "web"
            name = str(source.get("name") or source.get("handle", ""))
            rows.append(
                (
                    name,
                    source_type,
                    source_tier,
                    str(source.get("cadence", "-")),
                )
            )

    if not rows:
        echo("No sources configured.")
        raise Exit(code=0)

    echo(f"{'Name':<36} {'Type':<4} {'Tier':>4} {'Cadence':<12}")
    echo("-" * 64)
    for name, source_type, source_tier, cadence in rows:
        echo(f"{name[:36]:<36} {source_type:<4} {source_tier:>4} {cadence:<12}")
    echo(f"\nTotal: {len(rows)} sources")
    raise Exit(code=0)


@app.command()
def relevance(
    top: int | None = Option(
        None, "--top", help="Show top N highest-scored items from the last 7 days"
    ),
) -> None:
    from metabolon.organelles.endocytosis_rss.relevance import affinity_stats, top_cargo

    if top is not None:
        items = top_cargo(limit=top)
        if not items:
            echo("No recent relevance data found.")
            raise Exit(code=0)
        for index, item in enumerate(items, 1):
            title = item.get("title", "Untitled")
            source = item.get("source", "Unknown")
            score = item.get("score", 0)
            angle = item.get("banking_angle", "")
            line = f"{index}. [{score}/10] {title} — {source}"
            if angle and angle != "N/A":
                line = f"{line} ({angle})"
            echo(line)
        raise Exit(code=0)

    stats = affinity_stats()
    if stats.get("status") == "insufficient_data":
        echo("Relevance stats unavailable: insufficient_data")
        raise Exit(code=0)

    echo("Relevance scoring stats")
    echo(f"Total scored: {stats['total_scored']}")
    echo(f"Total engaged: {stats['total_engaged']}")
    echo(f"Average engaged score: {stats['avg_engaged_score']:.2f}")
    echo(f"False positives (count): {stats['false_positives_count']}")
    echo("False negatives:")
    for title in stats["false_negatives"]:
        echo(f"- {title}")
    raise Exit(code=0)


@app.command()
def status() -> None:
    cfg = restore_config()
    now = datetime.now().astimezone()

    echo(f"endocytosis_rss Status  ({now.strftime('%Y-%m-%d %H:%M %Z')})")
    echo("=" * 44)

    echo(f"\nConfig dir:    {cfg.config_dir}")
    echo(f"Sources file:  {_file_age(cfg.sources_path, now)}")
    echo(f"State file:    {_file_age(cfg.state_path, now)}")
    echo(f"News log:      {_file_age(cfg.log_path, now)}")

    state = restore_state(cfg.state_path)
    if state:
        echo(f"Sources:       {len(state)} tracked")
        latest = max(
            (
                dt
                for ts in state.values()
                if isinstance(ts, str)
                for dt in [_parse_aware(ts)]
                if dt
            ),
            default=None,
        )
        if latest is not None:
            echo(f"Last fetch:    {latest.strftime('%Y-%m-%d %H:%M')}")

    if cfg.article_cache_dir.exists():
        files = list(cfg.article_cache_dir.glob("*.json"))
        size_kb = sum(f.stat().st_size for f in files) / 1024
        echo(f"Article cache: {len(files)} files, {size_kb:.0f} KB")
    else:
        echo(f"Article cache: missing ({cfg.article_cache_dir})")

    if not cfg.sources_path.exists():
        echo("\nRun 'vivesca endocytosis init' to set up configuration.", err=True)
        raise Exit(code=1)
    raise Exit(code=0)


@app.command()
def init() -> None:
    cfg = restore_config()
    cfg.config_dir.mkdir(parents=True, exist_ok=True)
    cfg.cache_dir.mkdir(parents=True, exist_ok=True)
    cfg.data_dir.mkdir(parents=True, exist_ok=True)
    cfg.article_cache_dir.mkdir(parents=True, exist_ok=True)

    if not cfg.sources_path.exists():
        cfg.sources_path.write_text(default_sources_text(), encoding="utf-8")
        created = "created"
    else:
        created = "exists"

    echo(f"Config directory: {cfg.config_dir}")
    echo(f"Sources file: {cfg.sources_path} ({created})")
    echo(f"Cache directory: {cfg.cache_dir}")
    echo(f"Data directory: {cfg.data_dir}")
    raise Exit(code=0)


@app.command()
def summary(
    date: str | None = Option(None, "--date", help="Date YYYY-MM-DD (default: today)"),
    output: str | None = Option(None, "--output", "-o", help="Write to file instead of stdout"),
) -> None:
    """Generate a daily markdown summary from the JSONL cargo store."""
    cfg = restore_config()
    from metabolon.organelles.endocytosis_rss.log import generate_daily_markdown

    target_date = date or datetime.now(UTC).strftime("%Y-%m-%d")
    md = generate_daily_markdown(cfg.cargo_path, target_date)

    if not md.strip():
        echo(f"No cargo for {target_date}.", err=True)
        raise Exit(code=0)

    if output:
        Path(output).write_text(md, encoding="utf-8")
        echo(f"Written: {output}", err=True)
    else:
        echo(md)
    raise Exit(code=0)


@app.command(name="weekly-summary")
def weekly_summary(
    output: str | None = Option(None, "--output", "-o", help="Write to file instead of stdout"),
    tag: list[str] | None = Option(None, "--tag", "-t", help="Filter by tag (repeatable)"),
) -> None:
    """Scored weekly summary from JSONL cargo — grouped by day, no LLM."""
    cfg = restore_config()
    from metabolon.organelles.endocytosis_rss.digest import generate_weekly_markdown

    md = generate_weekly_markdown(cfg=cfg, tags=tag or [])

    if not md.strip():
        echo("No cargo for the past 7 days.", err=True)
        raise Exit(code=0)

    if output:
        Path(output).write_text(md, encoding="utf-8")
        echo(f"Written: {output}", err=True)
    else:
        echo(md)
    raise Exit(code=0)


@app.command()
def migrate() -> None:
    """One-time migration: convert markdown news log to JSONL cargo store."""
    cfg = restore_config()
    from metabolon.organelles.endocytosis_rss.migration import migrate_markdown_to_jsonl

    if cfg.cargo_path.exists():
        from metabolon.organelles.endocytosis_rss.cargo import recall_cargo

        existing = len(recall_cargo(cfg.cargo_path))
        if existing > 0:
            echo(f"Cargo store already has {existing} entries. Aborting.", err=True)
            raise Exit(code=1)

    count = migrate_markdown_to_jsonl(cfg.log_path, cfg.cargo_path)
    echo(f"Migrated {count} entries from {cfg.log_path} to {cfg.cargo_path}", err=True)
    raise Exit(code=0)


def main() -> int:
    if len(sys.argv) == 1:
        sys.argv.append("fetch")
    try:
        app()
        return 0
    except Exit as e:
        return e.exit_code if e.exit_code is not None else 0


if __name__ == "__main__":
    sys.exit(main())
