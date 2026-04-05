import json
import textwrap
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from metabolon.lysin.fetch import BioArticle


def format_text(article: BioArticle, full: bool = False) -> str:
    lines = []
    source_tag = ", ".join(article.sources) if article.sources else "unknown"
    lines.append("═══════════════════════════════════════")
    lines.append(f"LYSIN: {article.title}")
    lines.append(f"Source: {source_tag}")
    lines.append("═══════════════════════════════════════")
    lines.append("")
    lines.append("DEFINITION")
    lines.append(textwrap.fill(article.definition, width=80))
    lines.append("")
    lines.append("MECHANISM")
    lines.append(textwrap.fill(article.mechanism, width=80))
    lines.append("")
    lines.append("URL")
    lines.append(article.url)
    lines.append("═══════════════════════════════════════")

    if full and article.sections:
        lines.append("")
        lines.append("SECTIONS")
        for section in article.sections:
            lines.append(f"\n## {section['title']}")
            lines.append(textwrap.fill(section["text"], width=80))

    return "\n".join(lines)


def format_json(article: BioArticle, full: bool = False) -> str:
    data = {
        "title": article.title,
        "definition": article.definition,
        "mechanism": article.mechanism,
        "url": article.url,
        "sources": article.sources,
    }
    if full:
        data["sections"] = article.sections
    return json.dumps(data, indent=2)
