"""endosomal — email classification and triage logic.

Biology: endosomes mature through stages — early (triage), late
(process), recycling (route). Each stage processes cargo further
before determining its fate.

This organelle contains the pure business logic for email classification:
deterministic keyword matching (glycolysis) and pipeline orchestration.
No MCP tool wrappers — those live in the enzyme.
"""

from __future__ import annotations

# Endosomal maturation stages: early → late → recycling
STAGES = ("triage", "process", "route")
CATEGORIES = ("action_required", "borderline", "monitor", "archive_now")


# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------


def extract_sender(email_text: str) -> str:
    """Extract the sender address from email headers.

    Scans for a 'From:' header line and returns the lowercased address.
    Returns empty string if no From header is found.
    """
    for line in email_text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("from:"):
            # Handle both "From: Name <addr>" and "From: addr" forms
            from_value = stripped[5:].strip()
            if "<" in from_value and ">" in from_value:
                start = from_value.index("<") + 1
                end = from_value.index(">")
                return from_value[start:end].strip().lower()
            return from_value.lower()
    return ""


def sender_is_automated(sender: str) -> bool:
    """Signal: sender domain is a known automated/bulk sender — archive_now.

    This is the outermost membrane check (cheapest, highest yield).
    Known automated senders: transactional ESPs, notification systems,
    calendar noise, and social network bots.
    """
    if not sender:
        return False

    local, _, domain = sender.partition("@")

    # Local-part patterns that always indicate automated senders
    # regardless of domain (noreply@*, no-reply@*, donotreply@*)
    _AUTO_LOCALS = ("noreply", "no-reply", "donotreply", "do-not-reply", "do_not_reply")
    if local in _AUTO_LOCALS:
        return True

    # Domain-level automated sender lists
    # Bulk/transactional ESPs — every message is system-generated
    _AUTO_DOMAINS = frozenset(
        (
            "amazonses.com",
            "sendgrid.net",
            "mailchimp.com",
            "constantcontact.com",
            # Calendar noise
            "mail.google.com",
            "calendar.google.com",
            # Social network notification firehoses
            "linkedin.com",
            "github.com",
            "notion.so",
        )
    )
    return domain in _AUTO_DOMAINS


def extract_subject(email_text: str) -> str:
    """Extract the Subject header value from email text.

    Returns the raw subject string or empty string if not found.
    """
    for line in email_text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("subject:"):
            return stripped[8:].strip()
    return ""


def classify_subject(subject: str) -> str:
    """Signal: subject-line patterns — second glycolysis pass.

    Ordered by confidence: action signals before archive noise before monitor.
    Returns a category string or empty string if no pattern fires.
    """
    if not subject:
        return ""

    subject_lower = subject.lower()

    # Action required — explicit urgency markers in subject
    if "[action required]" in subject_lower or "[urgent]" in subject_lower:
        return "action_required"

    # Archive — calendar noise (invitations are automated scheduling artifacts)
    if subject_lower.startswith("invitation:") or subject_lower.startswith("updated invitation:"):
        return "archive_now"

    # Monitor — digest/periodic content (informational, no action)
    if any(w in subject_lower for w in ("digest", "weekly", "monthly")):
        return "monitor"

    # Borderline — reply/forward threads (conversations, might surface action)
    if subject_lower.startswith("re:") or subject_lower.startswith("fwd:"):
        return "borderline"

    return ""


def classify(email_text: str) -> str:
    """Deterministic classification — glycolysis (no symbiont).

    Three-pass membrane cascade: sender → subject → body keywords.
    Each pass is cheaper than the next; we short-circuit as early as possible.
    Returns empty string only for genuinely ambiguous emails (symbiont fallback).

    Pass 1 (receptor): sender domain lookup — O(1) set membership
    Pass 2 (glycolysis): subject pattern matching — fast string ops
    Pass 3 (Krebs): body keyword scan — linear scan, highest coverage
    """
    # -- Pass 1: sender domain receptor --
    sender = extract_sender(email_text)
    if sender_is_automated(sender):
        return "archive_now"

    # -- Pass 2: subject pattern glycolysis --
    subject = extract_subject(email_text)
    subject_verdict = classify_subject(subject)
    if subject_verdict:
        return subject_verdict

    # -- Pass 3: body keyword Krebs cycle --
    lower = email_text.lower()

    # Action required — strong action signals
    if any(
        w in lower
        for w in (
            "urgent",
            "asap",
            "deadline",
            "action required",
            "please respond",
            "by end of day",
            "by eod",
            "by cob",
            "approval needed",
            "sign off",
            "your approval",
            "please review",
            "please confirm",
            "action needed",
            "time-sensitive",
            "time sensitive",
            "overdue",
            "past due",
            "awaiting your",
            "needs your",
            "requires your",
        )
    ):
        return "action_required"

    # Archive — noise, automated, bulk
    if any(
        w in lower
        for w in (
            "unsubscribe",
            "newsletter",
            "no-reply",
            "noreply",
            "do-not-reply",
            "donotreply",
            "automated message",
            "this is an automated",
            "marketing",
            "promotional",
            "special offer",
            "limited time",
            "click here to",
            "view in browser",
            "email preferences",
            "account statement",
            "transaction alert",
            "payment received",
            "receipt for",
            "order confirmation",
            "shipping confirmation",
            "delivery notification",
            "tracking number",
            "calendar invitation",
            "has been shared with you",
            "security alert",
            "sign-in",
            "login attempt",
            "verify your",
            "password reset",
            "two-factor",
            "2fa",
            "otp",
        )
    ):
        return "archive_now"

    # Monitor — informational but potentially relevant
    if any(
        w in lower
        for w in (
            "fyi",
            "for your information",
            "no action",
            "heads up",
            "just letting you know",
            "wanted to share",
            "thought you",
            "announcement",
            "update:",
            "weekly update",
            "status update",
            "minutes from",
            "meeting notes",
            "recap",
        )
    ):
        return "monitor"

    # Borderline — explicit requests
    if any(
        w in lower
        for w in (
            "please",
            "could you",
            "can you",
            "would you",
            "request",
            "when you get a chance",
            "at your convenience",
            "thoughts?",
            "what do you think",
            "your input",
            "feedback",
            "opinion",
            "suggestion",
        )
    ):
        return "borderline"

    # Genuinely ambiguous — return empty for symbiont fallback
    return ""


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


def endosomal_pipeline(email_text: str) -> dict:
    """Full endosomal pipeline: triage → process → fate.

    In cell biology, endosomes mature through stages. Each stage
    processes the cargo further before determining its fate.
    """
    # Stage 1: Triage (early endosome) — classify
    category = classify(email_text)

    # Stage 2: Process (late endosome) — extract action if needed
    action = None
    if category == "action_required":
        # Extract the key ask
        lines = email_text.strip().split("\n")
        action = next(
            (line for line in lines if "?" in line or "please" in line.lower()),
            lines[0] if lines else "",
        )

    # Stage 3: Fate (recycling endosome) — determine destination
    fate = {
        "action_required": "surface immediately",
        "borderline": "batch for review",
        "monitor": "note and archive",
        "archive_now": "archive silently",
    }.get(category, "archive silently")

    return {
        "stage": "complete",
        "category": category,
        "action": action,
        "fate": fate,
    }


# ---------------------------------------------------------------------------
# Symbiont fallback prompt
# ---------------------------------------------------------------------------

CLASSIFY_PROMPT_TMPL = """\
You are an email triage assistant. Classify the following email into exactly one of these categories:

- action_required: needs a reply, decision, or follow-up action
- borderline: ambiguous -- could be ignored or could need action
- monitor: informational, worth tracking but no action needed now
- archive_now: noise, newsletters, automated notifications, no action

Respond with ONLY the category name, nothing else.

EMAIL:
{email_text}
"""
