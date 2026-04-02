from __future__ import annotations

"""talking_points — generate talking points from consulting IP library.

Given a client name and meeting context, searches the consulting IP library
for relevant assets and generates structured talking points.

Each talking point has: thesis, evidence, positioning, and source asset.
"""


import re
from dataclasses import dataclass, field
from pathlib import Path

CONSULTING_DIR = Path.home() / "epigenome" / "chromatin" / "Consulting"


@dataclass
class TalkingPoint:
    thesis: str  # One-sentence assertion
    evidence: str  # Supporting data or finding
    positioning: str  # How to frame for this client
    source_asset: str  # Path to IP asset this came from
    relevance_score: float = 0.0  # 0-1, how relevant to client context

    def to_markdown(self) -> str:
        return (
            f"**{self.thesis}**\n"
            f"  Evidence: {self.evidence}\n"
            f"  Position: {self.positioning}\n"
            f"  Source: {self.source_asset}"
        )


@dataclass
class TalkingPointCard:
    client: str
    meeting_context: str
    points: list[TalkingPoint] = field(default_factory=list)
    generated_at: str = ""

    def to_markdown(self) -> str:
        lines = [
            f"# Talking Points: {self.client}",
            f"**Context:** {self.meeting_context}",
            f"**Generated:** {self.generated_at}",
            "",
        ]
        for i, tp in enumerate(self.points, 1):
            lines.append(f"## {i}. {tp.thesis}")
            lines.append(f"- **Evidence:** {tp.evidence}")
            lines.append(f"- **Position:** {tp.positioning}")
            lines.append(f"- **Source:** `{tp.source_asset}`")
            lines.append("")
        return "\n".join(lines)


def _scan_consulting_assets() -> list[dict]:
    """Scan consulting directory for IP assets with frontmatter."""
    assets = []
    if not CONSULTING_DIR.exists():
        return assets

    for subdir in ["Policies", "Architectures", "Use Cases", "Experiments"]:
        asset_dir = CONSULTING_DIR / subdir
        if not asset_dir.exists():
            continue
        for f in asset_dir.glob("*.md"):
            try:
                content = f.read_text(encoding="utf-8")
                # Extract title from first heading
                title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
                title = title_match.group(1) if title_match else f.stem

                # Extract frontmatter domain/type if present
                domain = ""
                asset_type = subdir.rstrip("s").lower()
                fm_match = re.search(r"domain:\s*(.+)", content)
                if fm_match:
                    domain = fm_match.group(1).strip()

                assets.append({
                    "path": str(f),
                    "title": title,
                    "type": asset_type,
                    "domain": domain,
                    "content_preview": content[:500],
                    "filename": f.name,
                })
            except Exception:
                continue
    return assets


def _score_relevance(asset: dict, client: str, context: str) -> float:
    """Score how relevant an asset is to a client+context."""
    score = 0.0
    text = (asset.get("content_preview", "") + " " + asset.get("title", "")).lower()
    client_lower = client.lower()
    context_lower = context.lower()

    # Client name match
    if client_lower in text:
        score += 0.3

    # Context keyword overlap
    context_words = set(re.findall(r"\b\w{4,}\b", context_lower))
    text_words = set(re.findall(r"\b\w{4,}\b", text))
    overlap = context_words & text_words
    if context_words:
        score += 0.4 * (len(overlap) / len(context_words))

    # Domain match
    domain = asset.get("domain", "").lower()
    if domain and any(w in context_lower for w in domain.split()):
        score += 0.2

    # Banking/AI bonus for FS clients
    fs_signals = {"bank", "hsbc", "insurance", "wealth", "capital", "payment"}
    if any(s in client_lower for s in fs_signals):
        if any(w in text for w in ["banking", "financial", "regulatory", "hkma", "compliance"]):
            score += 0.1

    return min(1.0, score)


def generate_talking_points(
    client: str,
    context: str,
    max_points: int = 5,
) -> TalkingPointCard:
    """Generate talking points for a client meeting.

    Args:
        client: Client name (e.g., "HSBC").
        context: Meeting context or agenda (e.g., "AI governance review kickoff").
        max_points: Maximum talking points to generate.
    """
    from datetime import datetime, timedelta, timezone
    HKT = timezone(timedelta(hours=8))

    assets = _scan_consulting_assets()

    # Score and rank
    scored = []
    for asset in assets:
        score = _score_relevance(asset, client, context)
        if score > 0.1:
            scored.append((score, asset))
    scored.sort(key=lambda x: -x[0])

    # Build talking points from top assets
    points = []
    for score, asset in scored[:max_points]:
        # Extract first substantive paragraph as evidence
        content = asset.get("content_preview", "")
        paragraphs = [p.strip() for p in content.split("\n\n") if len(p.strip()) > 50]
        evidence = paragraphs[0][:200] if paragraphs else asset.get("title", "")

        points.append(TalkingPoint(
            thesis=asset["title"],
            evidence=evidence,
            positioning=f"Relevant {asset['type']} for {client} context",
            source_asset=asset.get("filename", ""),
            relevance_score=score,
        ))

    return TalkingPointCard(
        client=client,
        meeting_context=context,
        points=points,
        generated_at=datetime.now(HKT).strftime("%Y-%m-%d %H:%M"),
    )
