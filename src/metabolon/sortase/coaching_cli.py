import click
from rich.console import Console
from rich.table import Table

from metabolon.sortase.coaching import (
    add_coaching_note,
    load_coaching_notes,
    search_coaching,
)

console = Console()


@click.group()
def coaching() -> None:
    """Manage GLM coaching notes."""


@coaching.command("list")
def coaching_list() -> None:
    """Show all coaching categories and note count."""
    entries = load_coaching_notes()
    if not entries:
        console.print("No coaching notes found.")
        return

    table = Table(title="Coaching Notes")
    table.add_column("Category")
    table.add_column("Notes", justify="right")
    for entry in entries:
        table.add_row(entry["category"], str(len(entry["notes"])))
    console.print(table)


@coaching.command("add")
@click.option("--category", required=True, help="Category heading to add the note under.")
@click.option("--note", required=True, help="Coaching note text to append.")
def coaching_add(category: str, note: str) -> None:
    """Append a new coaching note under a category."""
    add_coaching_note(category=category, note=note)
    console.print(f"[green]Added note to '{category}'[/green]")


@coaching.command("search")
@click.argument("query")
def coaching_search(query: str) -> None:
    """Search coaching notes by keyword."""
    results = search_coaching(query=query)
    if not results:
        console.print(f"No matches for '{query}'")
        return

    table = Table(title=f"Results for '{query}'")
    table.add_column("Category")
    table.add_column("Matching Notes")
    for result in results:
        notes_text = "\n".join(result["notes"])
        table.add_row(result["category"], notes_text)
    console.print(table)
