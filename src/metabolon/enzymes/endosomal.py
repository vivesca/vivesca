from __future__ import annotations

"""endosomal — Gmail email triage.

Actions: search|thread|categorize|archive|mark_read|label|send|filter
"""


from fastmcp.tools.function_tool import tool
from mcp.types import ToolAnnotations

from metabolon.cytosol import synthesize
from metabolon.morphology import EffectorResult, Secretion
from metabolon.organelles import endosomal as endosomal_organelle
from metabolon.organelles import gmail


class EndosomalResult(Secretion):
    output: str


_ACTIONS = (
    "search — search Gmail. Requires: query. "
    "thread — get full thread content. Requires: thread_id. "
    "categorize — classify email text. Requires: email_text. "
    "archive — batch archive messages. Requires: message_ids. "
    "mark_read — batch mark messages as read. Requires: message_ids. "
    "label — create a Gmail label. Requires: name. "
    "send — send or reply to email. Optional: to, subject, body, reply_to_message_id, attach, cc. "
    "filter — create a Gmail filter rule. Optional: from_sender, subject_pattern, add_label, archive, mark_read, dry_run."
)


@tool(
    name="endosomal",
    description=f"Gmail email triage. Actions: {_ACTIONS}",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def endosomal(
    action: str,
    query: str = "",
    thread_id: str = "",
    email_text: str = "",
    message_ids: list[str] | None = None,
    name: str = "",
    to: str = "",
    subject: str = "",
    body: str = "",
    reply_to_message_id: str = "",
    attach: list[str] | None = None,
    cc: str = "",
    from_sender: str = "",
    subject_pattern: str = "",
    add_label: str = "",
    archive: bool = False,
    mark_read: bool = False,
    dry_run: bool = True,
) -> EndosomalResult | EffectorResult:
    """Unified Gmail tool."""
    action = action.lower().strip()
    _message_ids = message_ids or []

    if action == "search":
        if not query:
            return EffectorResult(success=False, message="search requires: query")
        result = gmail.search(query)
        return EndosomalResult(output=result)

    elif action == "thread":
        if not thread_id:
            return EffectorResult(success=False, message="thread requires: thread_id")
        result = gmail.get_thread(thread_id)
        return EndosomalResult(output=result)

    elif action == "categorize":
        if not email_text:
            return EffectorResult(success=False, message="categorize requires: email_text")
        category = endosomal_organelle.classify(email_text)
        if category:
            return EndosomalResult(output=category)
        prompt = endosomal_organelle.CLASSIFY_PROMPT_TMPL.format(email_text=email_text)
        raw = synthesize(prompt, timeout=60)
        category = raw.strip().lower().replace("-", "_")
        if category in endosomal_organelle.CATEGORIES:
            return EndosomalResult(output=category)
        return EndosomalResult(output=f"Unclassified: {category}")

    elif action == "archive":
        if not _message_ids:
            return EffectorResult(success=False, message="archive requires: message_ids")
        result = gmail.archive(_message_ids)
        return EffectorResult(success=True, message=result)

    elif action == "mark_read":
        if not _message_ids:
            return EffectorResult(success=False, message="mark_read requires: message_ids")
        result = gmail.mark_read(_message_ids)
        return EffectorResult(success=True, message=result)

    elif action == "label":
        if not name:
            return EffectorResult(success=False, message="label requires: name")
        result = gmail.create_label(name)
        return EffectorResult(success=True, message=result)

    elif action == "send":
        if not reply_to_message_id and (not to or not subject or not body):
            return EffectorResult(
                success=False,
                message="New emails require to, subject, and body. Replies require reply_to_message_id.",
            )
        result = gmail.send_email(
            to=to,
            subject=subject,
            body=body,
            cc=cc,
            reply_to_message_id=reply_to_message_id,
            attachments=attach,
        )
        return EffectorResult(success=True, message=result)

    elif action == "filter":
        if not from_sender and not subject_pattern:
            return EffectorResult(
                success=False, message="Provide at least one of: from_sender, subject_pattern."
            )
        if not add_label and not archive and not mark_read:
            return EffectorResult(
                success=False,
                message="Provide at least one action: add_label, archive, or mark_read.",
            )
        if dry_run:
            return EffectorResult(
                success=True,
                message=f"[DRY RUN] Would create filter: from={from_sender}, subject={subject_pattern}, label={add_label}, archive={archive}, mark_read={mark_read}",
            )
        result = gmail.create_filter(
            from_sender=from_sender,
            subject_pattern=subject_pattern,
            add_label=add_label,
            archive=archive,
            mark_read=mark_read,
        )
        return EffectorResult(success=True, message=result)

    else:
        return EffectorResult(
            success=False,
            message=f"Unknown action '{action}'. Valid: search, thread, categorize, archive, mark_read, label, send, filter",
        )
