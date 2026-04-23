import sys
from datetime import UTC, datetime
from pathlib import Path

import click

from epsin.config import load_sources
from epsin.extractors import resolve
from epsin.models import Item, Source
from epsin.output import format_check_results, format_jsonl, format_sources_table


@click.group()
@click.option("--config", type=click.Path(exists=True), default=None, help="Override sources config path")
@click.pass_context
def main(ctx: click.Context, config: str | None) -> None:
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = Path(config) if config else None


@main.command()
@click.option("--source", "source_name", default=None, help="Fetch single source by name")
@click.option("--tag", default=None, help="Filter by tag")
@click.option("--since", default=None, help="Only items after date (YYYY-MM-DD)")
@click.option("--full", is_flag=True, default=False, help="Include full article markdown")
@click.pass_context
def fetch(ctx: click.Context, source_name: str | None, tag: str | None, since: str | None, full: bool) -> None:
    config_path = ctx.obj["config_path"]
    sources = load_sources(config_path)

    if source_name:
        sources = [s for s in sources if s.name == source_name]

    if tag:
        sources = [s for s in sources if tag in s.tags]

    since_dt: datetime | None = None
    if since:
        try:
            since_dt = datetime.strptime(since, "%Y-%m-%d").replace(tzinfo=UTC)
        except ValueError:
            click.echo(f"Invalid --since date: {since}. Use YYYY-MM-DD.", err=True)
            sys.exit(1)

    all_items: list[Item] = []
    for source in sources:
        extractor = resolve(source)
        try:
            items = extractor.fetch(source, full=full)
        except Exception as exc:
            click.echo(f"Error fetching {source.name}: {exc}", err=True)
            continue

        if since_dt:
            items = [
                i for i in items
                if i.date and _parse_item_date(i.date) >= since_dt
            ]

        all_items.extend(items)

    format_jsonl(all_items)


def _parse_item_date(date_str: str) -> datetime:
    try:
        return datetime.fromisoformat(date_str)
    except (ValueError, TypeError):
        return datetime.min.replace(tzinfo=UTC)


@main.group()
@click.pass_context
def sources(ctx: click.Context) -> None:
    pass


@sources.command("list")
@click.pass_context
def sources_list(ctx: click.Context) -> None:
    config_path = ctx.obj["config_path"]
    all_sources = load_sources(config_path)
    format_sources_table(all_sources)


@sources.command("add")
@click.argument("url")
@click.pass_context
def sources_add(ctx: click.Context, url: str) -> None:
    click.echo(f"Auto-detect for {url} not yet implemented. Add manually to sources.yaml.", err=True)
    sys.exit(1)


@sources.command("check")
@click.pass_context
def sources_check(ctx: click.Context) -> None:
    import httpx

    config_path = ctx.obj["config_path"]
    all_sources = load_sources(config_path)

    results: list[tuple[str, str, str]] = []
    headers = {"User-Agent": "Mozilla/5.0 (compatible; Epsin/0.1)"}

    for source in all_sources:
        rss_status = "—"
        web_status = "—"

        if source.rss:
            try:
                with httpx.Client(headers=headers, timeout=10, follow_redirects=True) as client:
                    resp = client.get(source.rss)
                    rss_status = str(resp.status_code)
            except httpx.HTTPError as exc:
                rss_status = f"ERR:{exc}"

        try:
            with httpx.Client(headers=headers, timeout=10, follow_redirects=True) as client:
                resp = client.get(source.url)
                web_status = str(resp.status_code)
        except httpx.HTTPError as exc:
            web_status = f"ERR:{exc}"

        results.append((source.name, rss_status, web_status))

    format_check_results(results)


if __name__ == "__main__":
    main()
