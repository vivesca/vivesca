"""perfusion — are all tissues receiving blood?

Measures whether outputs are reaching all north stars or whether some
are ischaemic (starved). Reads today's manifests and completed topic
keys to build a coverage map, then identifies the least-perfused star.

In biology, perfusion is blood flow through tissue capillaries.
Poor perfusion = tissue death, even if the heart pumps fine.
The organism equivalent: pulse can run all day, but if Career gets
11 agents and Marriage gets 0, the marriage star is ischaemic.
"""

import datetime
from pathlib import Path

from metabolon.vasomotor import log, record_event

NORTH_STAR_FILE = Path.home() / "epigenome" / "chromatin" / "North Star.md"
CARDIAC_LOG = Path.home() / "tmp" / "pulse-manifest.md"
TOPIC_LOCK = Path.home() / "tmp" / "pulse-topics-done.txt"


def north_star_names() -> list[str]:
    """Extract north star names from the canonical file."""
    if not NORTH_STAR_FILE.exists():
        return []
    stars = []
    for line in NORTH_STAR_FILE.read_text().splitlines():
        if line.startswith("## ") and not line.startswith("## Meta"):
            stars.append(line[3:].strip())
    return stars


def coverage_map() -> dict[str, int]:
    """Count today's manifest mentions per north star. Returns {star: count}."""
    stars = north_star_names()
    coverage: dict[str, int] = {s: 0 for s in stars}

    # Scan live manifest + today's archived manifests
    texts: list[str] = []
    if CARDIAC_LOG.exists():
        texts.append(CARDIAC_LOG.read_text().lower())
    today = datetime.date.today().isoformat()
    for p in (Path.home() / "tmp").glob(f"pulse-{today}*.md"):
        texts.append(p.read_text().lower())
    combined = "\n".join(texts)

    for star in coverage:
        keywords = [w.lower() for w in star.split() if len(w) > 3 and not w[0].isdigit()]
        coverage[star] = sum(combined.count(kw) for kw in keywords)

    return coverage


def least_perfused() -> str | None:
    """Return the north star with least coverage, or None."""
    cov = coverage_map()
    if not cov:
        return None
    return min(cov, key=cov.get)  # type: ignore[arg-type]


def ischaemic_stars(threshold: int = 2) -> list[str]:
    """Return stars below the ischaemia threshold."""
    return [star for star, count in coverage_map().items() if count < threshold]


def perfusion_report() -> dict:
    """Full perfusion status for injection into systole context."""
    cov = coverage_map()
    ischaemic = [s for s, c in cov.items() if c < 2]
    least = min(cov, key=cov.get) if cov else None  # type: ignore[arg-type]
    record_event("perfusion_check", coverage=cov, ischaemic=ischaemic, focus=least)
    return {
        "coverage": cov,
        "ischaemic": ischaemic,
        "focus_star": least,
    }
