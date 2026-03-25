import textwrap
import json
from metabolon.lysin.fetch import BioArticle

def format_text(article: BioArticle, full: bool = False) -> str:
    """Format article as human-readable text for titration."""
    lines = []
    lines.append("═══════════════════════════════════════")
    lines.append(f"LYSIN: {article.title}")
    lines.append("═══════════════════════════════════════")
    lines.append("")
    lines.append("DEFINITION")
    lines.append(textwrap.fill(article.definition, width=80))
    lines.append("")
    lines.append("MECHANISM")
    lines.append(textwrap.fill(article.mechanism, width=80))
    lines.append("")
    lines.append("SOURCE")
    lines.append(article.url)
    lines.append("═══════════════════════════════════════")
    
    if full and article.sections:
        lines.append("")
        lines.append("SECTIONS")
        for section in article.sections:
            lines.append(f"## {section['title']}")
            lines.append(textwrap.fill(section['text'], width=80))
            lines.append("")
            
    return "\n".join(lines)

def format_json(article: BioArticle, full: bool = False) -> str:
    """Format article as JSON."""
    data = {
        "title": article.title,
        "definition": article.definition,
        "mechanism": article.mechanism,
        "url": article.url,
    }
    if full:
        data["sections"] = article.sections
    return json.dumps(data, indent=2)
