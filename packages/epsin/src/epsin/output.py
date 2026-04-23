import json
import sys

from epsin.models import Item, Source


def format_jsonl(items: list[Item]) -> None:
    for item in items:
        record = {
            "source": item.source,
            "title": item.title,
            "url": item.url,
            "date": item.date,
            "summary": item.summary,
            "tags": item.tags,
        }
        if item.content_md:
            record["content_md"] = item.content_md
        sys.stdout.write(json.dumps(record, ensure_ascii=False) + "\n")


def format_sources_table(sources: list[Source]) -> None:
    try:
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(title="Epsin Sources")
        table.add_column("Name", style="cyan")
        table.add_column("URL", style="blue")
        table.add_column("RSS", style="green")
        table.add_column("Tags", style="magenta")

        for s in sources:
            rss_status = "✓" if s.rss else "—"
            table.add_row(s.name, s.url, rss_status, ",".join(s.tags))

        console.print(table)
    except ImportError:
        for s in sources:
            rss_col = "RSS" if s.rss else "    "
            tag_col = ",".join(s.tags)
            sys.stdout.write(f"{s.name:<30} {rss_col} {s.url} [{tag_col}]\n")


def format_check_results(results: list[tuple[str, str, str]]) -> None:
    try:
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(title="Source Health Check")
        table.add_column("Source", style="cyan")
        table.add_column("RSS", style="green")
        table.add_column("Web", style="blue")

        for name, rss_status, web_status in results:
            table.add_row(name, rss_status, web_status)

        console.print(table)
    except ImportError:
        for name, rss_status, web_status in results:
            sys.stdout.write(f"{name:<30} RSS:{rss_status:>6}  Web:{web_status:>6}\n")
