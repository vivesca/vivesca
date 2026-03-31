"""Behavioural repertoire — the organism's enzyme catalogue.

Each operon is packaged expertise for catalysing one reaction,
named as verb+object. An operon doesn't guarantee its product —
it increases the probability of the desired reaction.

Operons can be authored (spliced in by the human) or crystallised
(precipitated from repeated signal patterns). The organism is
juvenile — most operons are currently authored. As the signalling
network matures, more will crystallise from experience.

Dormant operons are transcribed but not yet translated.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Operon:
    """One catalytic capability in the organism's repertoire."""

    reaction: str
    product: str
    precipitation: str = "authored"  # "authored" | "crystallised"
    substrates: list[str] = field(default_factory=list)
    enzymes: list[str] = field(default_factory=list)
    expressed: bool = True


OPERONS: list[Operon] = [
    # ── Anabolism (building up) ───────────────────────────────
    Operon(
        reaction="prepare",
        product="Terry is ready for a specific engagement",
        substrates=["upcoming engagement on calendar", "explicit request"],
        enzymes=["opsonization", "prepare-cv", "prep-sense", "prep-record-drill"],
    ),
    Operon(
        reaction="ribosome",
        product="Consulting IP compounded from accumulated sparks",
        substrates=["infradian cycle", "spark accumulation threshold"],
        enzymes=["ribosome"],
    ),
    Operon(
        reaction="vesicle",
        product="Spore shipped in Terry's voice",
        substrates=["idea survives exocytosis compression", "ribosome output ready"],
        enzymes=["sarcio"],
    ),
    Operon(
        reaction="scan",
        product="Transferable patterns surfaced from landscape and peers",
        substrates=["infradian/monthly cycle", "entering new domain", "feeling behind"],
        enzymes=["dialexis", "rheotaxis_search"],
    ),
    Operon(
        reaction="evaluate",
        product="Opportunity assessed against constraints and goals",
        substrates=["job posting received", "opportunity surfaces"],
        enzymes=["evaluate-job"],
    ),
    Operon(
        reaction="network",
        product="Right signal delivered to right receptor in right context",
        substrates=["incoming signal", "strategic outreach opportunity"],
        enzymes=["message", "agoras", "nodus", "ligand_bind"],
    ),
    Operon(
        reaction="homeostasis",
        product="Financial and career status audited, drift detected",
        substrates=["monthly cycle", "explicit request"],
        enzymes=["homeostasis", "fiscus"],
    ),
    Operon(
        reaction="triage",
        product="Incoming routed to action, defer, or apoptosis",
        substrates=["daily period", "inbox accumulation"],
        enzymes=["period", "stilus", "gog"],
    ),
    # ── Homeostasis (health maintenance) ──────────────────────
    Operon(
        reaction="monitor",
        product="Health signals synthesised into picture and recommendation",
        substrates=["zeitgeber routine", "symptom reported", "readiness check"],
        enzymes=["circadian_sleep", "membrane_potential", "sopor"],
    ),
    Operon(
        reaction="move",
        product="Exercise matched to today's readiness",
        substrates=["before exercise", "low readiness detected"],
        enzymes=["check-exercise-readiness"],
    ),
    Operon(
        reaction="log",
        product="Symptom recorded and matched against known patterns",
        substrates=["symptom reported"],
        enzymes=["nociception_log", "sopor", "histone_search"],
    ),
    # ── Secretion (output to environment) ─────────────────────
    Operon(
        reaction="exocytosis",
        product="Insight compressed to 280 chars and secreted to X",
        precipitation="crystallised",
        substrates=["sharp standalone claim surfaces", "spore published"],
        enzymes=["bird", "exocytosis_text"],
    ),
    Operon(
        reaction="research",
        product="Topic thoroughly researched and synthesised across sources",
        precipitation="crystallised",
        substrates=["question requiring external knowledge", "unfamiliar domain"],
        enzymes=[
            "rheotaxis_search",
            "endocytosis_extract",
        ],
    ),
    # ── Dormant (transcribed, not translated) ─────────────────
    Operon(
        reaction="decide",
        product="Decision made with trade-offs weighed against constraints",
        substrates=["explicit decision needed", "competing options"],
        enzymes=["transcription-factor"],
        expressed=False,
    ),
    Operon(
        reaction="reflect",
        product="Learnings extracted and compounded into durable knowledge",
        substrates=["session end", "gear shift", "infradian review"],
        enzymes=["telophase"],
        expressed=True,
    ),
    Operon(
        reaction="plan",
        product="Family activity organised considering everyone's needs",
        substrates=["weekend approaching", "holiday", "explicit request"],
        enzymes=["circadian_list", "cibus", "histone_search"],
        expressed=False,
    ),
    Operon(
        reaction="gift",
        product="Gift chosen that delights this specific person",
        substrates=["birthday approaching", "holiday", "milestone"],
        enzymes=["histone_search", "circadian_list", "rheotaxis_search"],
        expressed=False,
    ),
]


def dormant() -> list[Operon]:
    """Operons transcribed but not yet translated."""
    return [e for e in OPERONS if not e.expressed]


def expressed() -> list[Operon]:
    """Operons currently being translated."""
    return [e for e in OPERONS if e.expressed]


def crystallised() -> list[Operon]:
    """Operons that precipitated from experience."""
    return [e for e in OPERONS if e.precipitation == "crystallised"]


def by_enzyme(enzyme: str) -> list[Operon]:
    """Operons that use a given enzyme."""
    return [e for e in OPERONS if enzyme in e.enzymes]


def co_regulated(operon: Operon) -> list[Operon]:
    """Operons that share a substrate with this one — co-regulation.

    In biology, operons sharing a regulatory signal fire together.
    When one operon is triggered by a substrate, related operons
    should cascade.
    """
    if not operon.substrates:
        return []
    shared = [
        o
        for o in OPERONS
        if o.reaction != operon.reaction
        and o.expressed
        and any(s in o.substrates for s in operon.substrates)
    ]
    return shared


def unclaimed_enzymes(known_enzymes: list[str]) -> list[str]:
    """Enzymes that exist but no operon claims them."""
    claimed = {e for op in OPERONS for e in op.enzymes}
    return [e for e in known_enzymes if e not in claimed]
