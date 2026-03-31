from __future__ import annotations
from __future__ import annotations

import sys

import click

from metabolon.lysin.fetch import fetch_sections, fetch_summary
from metabolon.lysin.format import format_json, format_text


@click.command()
@click.argument("term")
@click.option("--full", is_flag=True, help="Include all article sections")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def main(term: str, full: bool, as_json: bool):
    """Fetch real biology for a term. Grounds hybridization in source material."""
    try:
        article = fetch_summary(term)
        if full:
            article.sections = fetch_sections(article.title)
        if as_json:
            click.echo(format_json(article, full=full))
        else:
            click.echo(format_text(article, full=full))
    except LookupError as e:
        click.echo(f"Not found: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
