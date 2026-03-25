"""Operon map resource — the organism's catalytic repertoire.

Resources:
  vivesca://operons — current operon status (expressed/dormant/crystallised)
"""

from __future__ import annotations


def express_operon_map() -> str:
    """Build the operon map from the operons registry."""
    try:
        from metabolon.operons import OPERONS
    except ImportError:
        return "Operon map not available."

    lines: list[str] = []

    live = [e for e in OPERONS if e.expressed]
    dormant = [e for e in OPERONS if not e.expressed]
    crystallised = [e for e in OPERONS if e.precipitation == "crystallised"]

    lines.append("# Operon Map\n")
    lines.append(
        f"**{len(OPERONS)}** operons: "
        f"{len(live)} expressed, {len(dormant)} dormant, "
        f"{len(crystallised)} crystallised\n"
    )

    if live:
        lines.append("## Expressed\n")
        lines.append("| Operon | Product | Precipitation | Enzymes |")
        lines.append("|--------|---------|---------------|---------|")
        for e in live:
            enzymes = ", ".join(f"`{t}`" for t in e.enzymes) if e.enzymes else "—"
            product = e.product[:60] + "..." if len(e.product) > 60 else e.product
            lines.append(f"| **{e.reaction}** | {product} | {e.precipitation} | {enzymes} |")

    if dormant:
        lines.append("\n## Dormant\n")
        lines.append("| Operon | Product | Precipitation |")
        lines.append("|--------|---------|---------------|")
        for e in dormant:
            product = e.product[:60] + "..." if len(e.product) > 60 else e.product
            lines.append(f"| **{e.reaction}** | {product} | {e.precipitation} |")

    return "\n".join(lines)
