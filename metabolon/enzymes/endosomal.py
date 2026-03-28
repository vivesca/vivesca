"""sorting -- Golgi email triage: classify, drill, archive, filter.

Biology: the Golgi apparatus sorts incoming proteins by their
destination signals and routes them to the right compartment.
Email triage is the same operation -- each message carries a
signal (sender, subject, content) that determines its route.

This enzyme is a thin MCP wrapper around the endosomal organelle,
which contains all classification and pipeline logic.

Tools:
  endosomal_search     -- search inbox or recent archived mail
  endosomal_thread     -- get full thread content
  endosomal_categorize -- classify email text into triage bucket
  endosomal_archive    -- batch archive messages
  endosomal_mark_read  -- batch mark messages as read
  endosomal_send       -- send or reply to email (replies always quote original)
  endosomal_label      -- create a Gmail label
  endosomal_filter     -- create a Gmail filter rule (dry-run by default)
"""

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.cytosol import invoke_organelle, synthesize
from metabolon.morphology import EffectorResult, Secretion
from metabolon.organelles import endosomal

GOG = "gog"


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
    result = invoke_organelle(GOG, ["gmail", "thread", "get", thread_id, "--full"], timeout=60)
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
    category = endosomal.classify(email_text)
    if category:
        return EndosomalCategoryResult(category=category, valid=True)

    # Symbiont fallback — only for ambiguous cases
    prompt = endosomal.CLASSIFY_PROMPT_TMPL.format(email_text=email_text)
    raw = synthesize(prompt, timeout=60)
    category = raw.strip().lower().replace("-", "_")
    return EndosomalCategoryResult(
        category=category,
        valid=category in endosomal.CATEGORIES,
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
    name="endosomal_send",
    description="Send or reply to a Gmail message. Replies always include quoted original.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
)
def endosomal_send(
    to: str = "",
    subject: str = "",
    body: str = "",
    reply_to_message_id: str = "",
    attach: list[str] | None = None,
    cc: str = "",
) -> EffectorResult:
    """Send a new email or reply to an existing message.

    For replies: set reply_to_message_id. Recipients auto-populated via --reply-all.
    Replies always include --quote (quoted original).
    For new emails: set to, subject, and body.
    """
    args = ["gmail", "send"]

    if reply_to_message_id:
        args.extend(["--reply-to-message-id", reply_to_message_id, "--reply-all", "--quote"])
    if to:
        args.extend(["--to", to])
    if subject:
        args.extend(["--subject", subject])
    if body:
        args.extend(["--body", body])
    if cc:
        args.extend(["--cc", cc])
    for path in attach or []:
        args.extend(["--attach", path])

    if not reply_to_message_id and (not to or not subject or not body):
        return EffectorResult(
            success=False,
            message="New emails require to, subject, and body. Replies require reply_to_message_id.",
        )

    result = invoke_organelle(GOG, args, timeout=60)
    return EffectorResult(success=True, message=result or "Email sent.")


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
