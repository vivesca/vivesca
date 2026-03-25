"""sorting -- Golgi email triage: classify, drill, archive, filter.

Biology: the Golgi apparatus sorts incoming proteins by their
destination signals and routes them to the right compartment.
Email triage is the same operation -- each message carries a
signal (sender, subject, content) that determines its route.

Tools:
  endosomal_search     -- search inbox or recent archived mail
  endosomal_thread     -- get full thread content
  endosomal_categorize -- classify email text into triage bucket
  endosomal_archive    -- batch archive messages
  endosomal_mark_read  -- batch mark messages as read
  endosomal_label      -- create a Gmail label
  endosomal_filter     -- create a Gmail filter rule (dry-run by default)
"""

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.cytosol import invoke_organelle, synthesize
from metabolon.morphology import EffectorResult, Secretion

GOG = "gog"

# Endosomal maturation stages: early → late → recycling
# Early endosome: triage (classify)
# Late endosome: process (extract action items)
# Recycling endosome: archive or surface for action
STAGES = ("triage", "process", "route")
CATEGORIES = ("action_required", "borderline", "monitor", "archive_now")


def endosomal_pipeline(email_text: str) -> dict:
    """Full endosomal pipeline: triage → process → fate.

    In cell biology, endosomes mature through stages. Each stage
    processes the cargo further before determining its fate.
    """
    # Stage 1: Triage (early endosome) — classify
    category = _classify(email_text)

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


def _extract_sender(email_text: str) -> str:
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


def _sender_is_automated(sender: str) -> bool:
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


def _extract_subject(email_text: str) -> str:
    """Extract the Subject header value from email text.

    Returns the raw subject string or empty string if not found.
    """
    for line in email_text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("subject:"):
            return stripped[8:].strip()
    return ""


def _classify_subject(subject: str) -> str:
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


def _classify(email_text: str) -> str:
    """Deterministic classification — glycolysis (no symbiont).

    Three-pass membrane cascade: sender → subject → body keywords.
    Each pass is cheaper than the next; we short-circuit as early as possible.
    Returns empty string only for genuinely ambiguous emails (symbiont fallback).

    Pass 1 (receptor): sender domain lookup — O(1) set membership
    Pass 2 (glycolysis): subject pattern matching — fast string ops
    Pass 3 (Krebs): body keyword scan — linear scan, highest coverage
    """
    # -- Pass 1: sender domain receptor --
    sender = _extract_sender(email_text)
    if _sender_is_automated(sender):
        return "archive_now"

    # -- Pass 2: subject pattern glycolysis --
    subject = _extract_subject(email_text)
    subject_verdict = _classify_subject(subject)
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


_CLASSIFY_PROMPT_TMPL = """\
You are an email triage assistant. Classify the following email into exactly one of these categories:

- action_required: needs a reply, decision, or follow-up action
- borderline: ambiguous -- could be ignored or could need action
- monitor: informational, worth tracking but no action needed now
- archive_now: noise, newsletters, automated notifications, no action

Respond with ONLY the category name, nothing else.

EMAIL:
{email_text}
"""


# -- Result schemas --------------------------------------------------------


class EndosomalSearchResult(Secretion):
    """Raw output from a Gmail search."""

    output: str


class EndosomalThreadResult(Secretion):
    """Full thread content."""

    output: str


class EndosomalCategoryResult(Secretion):
    """Triage verdict for one email."""

    category: str
    valid: bool


# -- Tools -----------------------------------------------------------------


@tool(
    name="endosomal_search",
    description="Search Gmail. Query uses Gmail search syntax.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def endosomal_search(query: str) -> EndosomalSearchResult:
    """Run a Gmail search and return plain-text results.

    query must be a single Gmail search string, e.g.:
      "is:unread in:inbox"
      "newer_than:1d -in:inbox -from:briefs@cora.computer"

    Negation queries (-in:inbox) MUST be passed as one string argument.
    """
    result = invoke_organelle(GOG, ["gmail", "search", query, "--plain"], timeout=30)
    return EndosomalSearchResult(output=result)


@tool(
    name="endosomal_thread",
    description="Get full Gmail thread content by thread ID.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def endosomal_thread(thread_id: str) -> EndosomalThreadResult:
    """Retrieve the full content of a thread (--full flag)."""
    result = invoke_organelle(GOG, ["gmail", "thread", "get", thread_id, "--full"], timeout=30)
    return EndosomalThreadResult(output=result)


@tool(
    name="endosomal_categorize",
    description="Classify email text into: action_required, borderline, monitor, archive_now.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def endosomal_categorize(email_text: str) -> EndosomalCategoryResult:
    """Classify one email into a triage bucket.

    Glycolysis first (deterministic keyword matching), symbiont fallback
    only for genuinely ambiguous emails that the cytosol can't classify.
    """
    category = _classify(email_text)
    if category:
        return EndosomalCategoryResult(category=category, valid=True)

    # Symbiont fallback — only for ambiguous cases
    prompt = _CLASSIFY_PROMPT_TMPL.format(email_text=email_text)
    raw = synthesize(prompt, timeout=60)
    category = raw.strip().lower().replace("-", "_")
    return EndosomalCategoryResult(
        category=category,
        valid=category in CATEGORIES,
    )


@tool(
    name="endosomal_archive",
    description="Batch archive Gmail messages by ID.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def endosomal_archive(message_ids: list[str]) -> EffectorResult:
    """Archive one or more messages (removes from inbox)."""
    if not message_ids:
        return EffectorResult(success=False, message="No message IDs provided.")
    result = invoke_organelle(GOG, ["gmail", "archive", "--force", *message_ids], timeout=30)
    return EffectorResult(
        success=True, message=result or f"Archived {len(message_ids)} message(s)."
    )


@tool(
    name="endosomal_mark_read",
    description="Batch mark Gmail messages as read by ID.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def endosomal_mark_read(message_ids: list[str]) -> EffectorResult:
    """Mark one or more messages as read."""
    if not message_ids:
        return EffectorResult(success=False, message="No message IDs provided.")
    result = invoke_organelle(GOG, ["gmail", "mark-read", "--force", *message_ids], timeout=30)
    return EffectorResult(
        success=True, message=result or f"Marked {len(message_ids)} message(s) as read."
    )


@tool(
    name="endosomal_label",
    description="Create a Gmail label (e.g. 'Category/Name').",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def endosomal_label(name: str) -> EffectorResult:
    """Create a Gmail label. Use Category/Name format for nested labels."""
    result = invoke_organelle(GOG, ["gmail", "labels", "create", name], timeout=15)
    return EffectorResult(success=True, message=result or f"Label created: {name}")


@tool(
    name="endosomal_filter",
    description="Create a Gmail filter rule. dry_run=True by default -- set False to apply.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
)
def endosomal_filter(
    from_sender: str = "",
    subject_pattern: str = "",
    add_label: str = "",
    archive: bool = False,
    mark_read: bool = False,
    dry_run: bool = True,
) -> EffectorResult:
    """Create a Gmail filter. Runs --dry-run unless dry_run=False.

    At least one of from_sender or subject_pattern must be set.
    At least one action (add_label, archive, mark_read) must be set.
    """
    if not from_sender and not subject_pattern:
        return EffectorResult(
            success=False, message="Provide at least one of: from_sender, subject_pattern."
        )
    if not add_label and not archive and not mark_read:
        return EffectorResult(
            success=False, message="Provide at least one action: add_label, archive, or mark_read."
        )

    args = ["gmail", "settings", "filters", "create"]
    if from_sender:
        args.extend(["--from", from_sender])
    if subject_pattern:
        args.extend(["--subject", subject_pattern])
    if add_label:
        args.extend(["--add-label", add_label])
    if archive:
        args.append("--archive")
    if mark_read:
        args.append("--mark-read")
    if dry_run:
        args.append("--dry-run")

    result = invoke_organelle(GOG, args, timeout=15)
    prefix = "[DRY RUN] " if dry_run else ""
    return EffectorResult(success=True, message=f"{prefix}{result or 'Filter applied.'}")
