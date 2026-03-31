"""Prompt templates for common agent workflows.

Prompts:
  research       — structured research brief with sources and synthesis
  compose_signal  — draft a message in Terry's voice for a given platform
  morning_brief  — morning situation report combining calendar and context
"""

from __future__ import annotations

from fastmcp.prompts import prompt


@prompt(
    name="research",
    description=(
        "Generate a structured research brief. "
        "Calls rheotaxis_search as appropriate and formats findings "
        "with executive summary, key points, sources, and recommended actions."
    ),
)
def research(
    topic: str,
    depth: str = "standard",
    context: str = "",
) -> str:
    """Structured research brief prompt."""
    context_block = f"\nBackground context: {context}\n" if context else ""
    depth_instruction = {
        "quick": "Use rheotaxis_search with depth=quick for a quick factual lookup.",
        "standard": "Use rheotaxis_search with depth=thorough for a thorough survey.",
        "deep": "Use rheotaxis_search with depth=deep for deep investigation (expensive — confirm before running).",
    }.get(depth, "Use rheotaxis_search with depth=thorough for a thorough survey.")

    return (
        f"Research the following topic and produce a structured brief.\n\n"
        f"Topic: {topic}\n"
        f"{context_block}\n"
        f"Depth: {depth} — {depth_instruction}\n\n"
        f"Format the output as:\n"
        f"1. Executive Summary (2-3 sentences)\n"
        f"2. Key Findings (bullet points)\n"
        f"3. Sources (numbered citations)\n"
        f"4. Recommended Next Steps (if applicable)\n\n"
        f"Be concise. Prioritise actionable signal over completeness."
    )


@prompt(
    name="compose_signal",
    description=(
        "Draft a message in Terry's voice for a specific platform and recipient. "
        "Produces front-stage copy ready for review — never sends directly."
    ),
)
def compose_signal(
    platform: str,
    recipient: str,
    intent: str,
    tone: str = "professional",
    context: str = "",
) -> str:
    """Draft a message ready for Terry's review and send."""
    context_block = f"\nContext: {context}\n" if context else ""
    platform_note = {
        "whatsapp": "WhatsApp — casual register, short paragraphs, no bullet points.",
        "linkedin": "LinkedIn — professional, warm, no jargon, 150 words max.",
        "email": "Email — subject line required, structured paragraphs, sign-off.",
        "telegram": "Telegram — concise, direct, markdown acceptable.",
    }.get(platform.lower(), f"{platform} — match platform norms.")

    return (
        f"Draft a message from Terry (Ho Ming Terry) for the following:\n\n"
        f"Platform: {platform_note}\n"
        f"Recipient: {recipient}\n"
        f"Intent: {intent}\n"
        f"Tone: {tone}\n"
        f"{context_block}\n"
        f"Requirements:\n"
        f"- Write in Terry's voice: direct, warm, no filler phrases\n"
        f"- Front-stage copy — Terry will review before sending\n"
        f"- Do not include meta-commentary or options; produce one clean draft\n"
        f"- If email: include a subject line prefixed with 'Subject:'"
    )


@prompt(
    name="morning_brief",
    description=(
        "Generate a morning situation report. "
        "Reads today's calendar, checks memory for pending items, "
        "and produces a prioritised daily plan."
    ),
)
def morning_brief(
    focus: str = "",
    include_budget: bool = False,
) -> str:
    """Morning brief prompt — situation report and daily plan."""
    focus_block = f"\nToday's focus area: {focus}\n" if focus else ""
    budget_instruction = (
        "\n5. Read vivesca://budget and include current token budget status."
        if include_budget
        else ""
    )

    return (
        f"Generate a morning situation report for Terry.\n\n"
        f"Steps:\n"
        f"1. Read vivesca://circadian — list today's events with times (HKT).\n"
        f"2. Use histone with action=search for any pending items or open loops from recent sessions.\n"
        f"3. Check ~/epigenome/chromatin/Tonus.md for active priorities.\n"
        f"{focus_block}"
        f"4. Produce a brief (under 300 words) covering:\n"
        f"   a. Today's schedule (events + gaps)\n"
        f"   b. Top 3 priorities for the day\n"
        f"   c. Any open loops or time-sensitive items\n"
        f"   d. One sentence on energy/logistics if relevant"
        f"{budget_instruction}\n\n"
        f"Tone: Jeeves — formal yet warm, prose over bullets, no emoji."
    )
