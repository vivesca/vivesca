import contextlib
import datetime
import json
import re

from metabolon.locus import phantoms_db

"""checkpoint — immune checkpoint filter for task dispatch.

Deterministic gate that runs before any task is dispatched or before an
agent:terry item is written to Praxis.  No LLM calls.  No side effects.

Background: 24% phantom rate discovered in Mar 2026 audit — ~11.5h of
false review debt from 12 phantom files.  Five phantom patterns banned:

1. Unsolicited external commitments (conference abstracts, applications)
2. Writing in Terry's voice (LinkedIn posts, bios, About pages)
3. Self-referential audit loops (designing, auditing, filing as review)
4. Reports for self-caused problems (path audits, routing rescue)
5. Unverified premise chains (Art 50 / CoP pattern)

The gate answers three questions:

  Q1. Sourced?   Did Terry or a Terry-approved task request this?
  Q2. Automated? Is this Automated per division-of-labour (not Sharpening/
                 Presence/Collaborative)?
  Q3. Phantom?   Does this create an obligation requiring Terry's
                 name / voice / presence?

Skip if: Q1=no AND Q3=yes.
Skip if: Q2=no (wrong category).
Also enforce: max 3 agent:terry items per systole.
"""

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PHANTOM_TRACKER = phantoms_db

# ---------------------------------------------------------------------------
# Phantom obligation patterns
# ---------------------------------------------------------------------------

# Task descriptions matching these patterns create obligations requiring
# Terry's name/voice/presence — they are phantom unless Terry asked.
_PHANTOM_PATTERNS: list[re.Pattern] = [
    # External commitments
    re.compile(
        r"\b(conference|abstract|submission|application|proposal|nomination)\b", re.IGNORECASE
    ),
    re.compile(r"\b(submit|apply|register|enroll|enrol)\b.*\b(terry|you)\b", re.IGNORECASE),
    # Writing in Terry's voice
    re.compile(
        r"\b(linkedin|twitter|tweet|blog post|about page|bio|biography)\b"
        r".*\b(draft|write|post|publish)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(draft|write|compose)\b.*\b(linkedin|bio|about|profile)\b", re.IGNORECASE),
    re.compile(r"\bin terry[''s]* voice\b", re.IGNORECASE),
    re.compile(r"\bpersonal statement\b", re.IGNORECASE),
    # Self-referential system audits filed as review items
    re.compile(
        r"\b(audit|review|inspect)\b.*\b(yourself|itself|this system|vivesca|poiesis|pulse)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bself.?audit\b", re.IGNORECASE),
    # Reports for self-caused problems
    re.compile(r"\b(rescue report|path audit|routing error|merge plan)\b", re.IGNORECASE),
    # External commitment verbs without explicit sourcing
    re.compile(
        r"\b(reach out to|cold email|message|pitch)\b.*\b(on behalf|for terry)\b", re.IGNORECASE
    ),
]

# Tasks matching these patterns are Presence/Sharpening/Collaborative,
# not Automated — wrong category regardless of sourcing.
_NON_AUTOMATED_PATTERNS: list[re.Pattern] = [
    # Presence
    re.compile(r"\b(theo|tara|family|kids?|partner|spouse)\b", re.IGNORECASE),
    re.compile(r"\b(attend|be there|show up|client meeting|in.?person)\b", re.IGNORECASE),
    # Sharpening — Terry keeps these to stay sharp
    re.compile(r"\b(drill|anki|flashcard|memoris[ez]|study from memory)\b", re.IGNORECASE),
    re.compile(r"\b(form.*view|form.*opinion|read.*source)\b", re.IGNORECASE),
    # Collaborative — needs Terry at keyboard
    re.compile(r"\b(brainstorm|probe|strategic.?thinking)\b.*\bwith terry\b", re.IGNORECASE),
]

# These signal the task is Automated (research, synthesis, code, monitoring).
# Used to fast-path approval when task is clearly in scope.
_AUTOMATED_SIGNALS: list[re.Pattern] = [
    re.compile(
        r"\b(research|synthesize|synthesis|summarize|analyse|analyze|"
        r"monitor|fetch|compile|draft for review)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(code|script|tool|automate|generate|extract)\b", re.IGNORECASE),
]

# Max agent:terry tags per systole (hard limit from feedback_poiesis_dispatch_rule.md)
MAX_TERRY_PER_SYSTOLE = 3


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def should_suppress(task: dict) -> tuple[bool, str]:
    """Check if a task should be dispatched.

    Args:
        task: dict with keys:
            description (str)  — free-text task description, required
            sourced (bool)     — True if Terry or a Terry-approved task
                                 explicitly requested this (default False)
            category (str)     — "Automated", "Sharpening", "Presence",
                                 "Collaborative", "Dropped", or "" (unknown)
            creates_obligation (bool) — True if output requires Terry's
                                        name/voice/presence (default None
                                        triggers heuristic detection)

    Returns:
        (approved: bool, reason: str)
        approved=True  → dispatch this task
        approved=False → skip, reason explains why
    """
    description: str = task.get("description", "")
    sourced: bool = bool(task.get("sourced", False))
    category: str = (task.get("category") or "").strip().lower()
    creates_obligation: bool | None = task.get("creates_obligation")  # None = auto-detect

    if not description:
        return False, "no description provided"

    # --- Q2: Category filter (Automated only) --------------------------------
    if category in ("presence", "sharpening", "collaborative", "dropped"):
        return False, f"wrong category: '{category}' — only Automated tasks are dispatched"

    # Non-automated pattern heuristic (only when category not explicit)
    if not category or category != "automated":
        for pat in _NON_AUTOMATED_PATTERNS:
            if pat.search(description):
                return (
                    False,
                    "non-Automated category detected: "
                    f"'{pat.pattern}' matched — skip or reclassify",
                )

    # --- Q3: Obligation detection --------------------------------------------
    if creates_obligation is None:
        # Heuristic: does this task match phantom patterns?
        creates_obligation = _is_phantom(description)

    # --- Q1 + Q3: The gate ---------------------------------------------------
    if not sourced and creates_obligation:
        reason = _phantom_reason(description)
        return (
            False,
            "phantom obligation blocked: task not sourced from Terry and "
            f"creates obligation requiring his name/voice/presence. {reason}",
        )

    return True, "approved"


def is_terry_tag_approved(
    task_description: str,
    current_terry_count: int,
    sourced: bool = False,
    creates_obligation: bool | None = None,
) -> tuple[bool, str]:
    """Check whether an agent:terry tag is justified for an output.

    This is the second-pass gate applied when an agent wants to tag an output
    for Terry's review (i.e., add it to Praxis with agent:terry).

    Args:
        task_description: What the output is / what review is needed.
        current_terry_count: How many agent:terry items have been added this systole.
        sourced: Did Terry or an approved task request this?
        creates_obligation: Does this require Terry's name/voice/presence?
                            None = auto-detect.

    Returns:
        (approved: bool, reason: str)
    """
    if current_terry_count >= MAX_TERRY_PER_SYSTOLE:
        return False, (
            f"systole terry cap reached: {current_terry_count}/{MAX_TERRY_PER_SYSTOLE} "
            "agent:terry items already queued — route to archive instead"
        )

    approved, reason = should_suppress(
        {
            "description": task_description,
            "sourced": sourced,
            "creates_obligation": creates_obligation,
        }
    )
    if not approved:
        return False, reason

    # Additional: is this really a review item, or is it studying/doing?
    if _is_study_or_action(task_description):
        return False, (
            "not a review item — study tasks, mechanical verification, and "
            "physical actions do not require Terry's review tag; archive instead"
        )

    return True, "agent:terry approved"


def sweep_praxis_for_phantoms(praxis_text: str) -> list[dict]:
    """Scan Praxis.md text for likely phantom agent:terry items.

    Returns a list of dicts: {line_number, line, reason, created_at, age_days}
    for items that fail the dispatch gate heuristic.  Caller decides what to
    do with them.  Does NOT modify the file — pure analysis.

    Uses a local JSON tracker to persist when a phantom was first seen,
    providing the 'age' signal for urgency weighting.
    """
    tracker = {}
    if PHANTOM_TRACKER.exists():
        with contextlib.suppress(Exception):
            tracker = json.loads(PHANTOM_TRACKER.read_text())

    today = datetime.date.today()
    results = []
    dirty = False

    for i, line in enumerate(praxis_text.splitlines(), start=1):
        content = line.strip()
        lower = content.lower()
        if "agent:terry" not in lower:
            continue
        if any(sig in lower for sig in ["[x]", "done", "completed"]):
            continue  # already resolved

        # Run heuristic gate (sourced=False conservative assumption)
        approved, reason = should_suppress(
            {
                "description": content,
                "sourced": False,
                "creates_obligation": None,
            }
        )
        if not approved:
            # Track when this phantom was first seen
            # Use content as key (unique enough for Praxis)
            if content not in tracker:
                tracker[content] = today.isoformat()
                dirty = True

            created_at_str = tracker[content]
            try:
                created_at = datetime.date.fromisoformat(created_at_str)
            except ValueError:
                created_at = today

            age_days = (today - created_at).days

            results.append(
                {
                    "line_number": i,
                    "line": content,
                    "reason": reason,
                    "created_at": created_at_str,
                    "age_days": max(0, age_days),
                }
            )

    if dirty:
        try:
            PHANTOM_TRACKER.parent.mkdir(parents=True, exist_ok=True)
            PHANTOM_TRACKER.write_text(json.dumps(tracker, indent=2))
        except Exception:
            pass

    return results


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _is_phantom(description: str) -> bool:
    """Return True if description matches any phantom obligation pattern."""
    return any(pat.search(description) for pat in _PHANTOM_PATTERNS)


def _phantom_reason(description: str) -> str:
    """Return the first phantom pattern that matched, for diagnostics."""
    for pat in _PHANTOM_PATTERNS:
        if pat.search(description):
            return f"matched pattern: /{pat.pattern}/"
    return ""


def _is_study_or_action(description: str) -> bool:
    """Return True if this looks like a study task or physical action, not review."""
    _study_or_action: list[re.Pattern] = [
        re.compile(r"\b(study|learn|read|memoris[ez]|drill|flashcard)\b", re.IGNORECASE),
        re.compile(r"\b(go to|call|visit|pick up|drop off|sign|attend)\b", re.IGNORECASE),
        re.compile(
            r"\b(verify|check|confirm|validate)\b.*\b(complete|done|ready|pass)\b", re.IGNORECASE
        ),
    ]
    return any(pat.search(description) for pat in _study_or_action)
