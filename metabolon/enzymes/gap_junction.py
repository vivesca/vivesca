"""gap_junction — ligand-receptor signalling via WhatsApp (wacli).

Tools:
  ligand_bind   — read a conversation (merges phone + LID JIDs)
  ligand_search — search messages by text, optionally scoped to contact
  ligand_draft  — draft a message (NEVER sends)
  receptor_list — list recent chats
  receptor_sync — check sync daemon status
"""

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.morphology import Secretion, Vital

GAP_JUNCTION_CONTACTS = {"tara", "mum", "dad", "brother", "sister", "yujie"}


def _contact_type(name: str) -> str:
    return "gap_junction" if name.lower() in GAP_JUNCTION_CONTACTS else "receptor"


class LigandResult(Secretion):
    messages: str


class LigandDraft(Secretion):
    draft: str


class ReceptorList(Secretion):
    chats: str


@tool(
    name="ligand_bind",
    description="Read a WhatsApp conversation. Merges phone + LID JID threads.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def ligand_bind(name: str, limit: int = 20) -> LigandResult:
    from metabolon.organelles.gap_junction import receive_signals

    contact = _contact_type(name)
    result = receive_signals(name, limit)
    prefix = f"[{contact}] " if contact == "gap_junction" else ""
    return LigandResult(messages=f"{prefix}{result}")


@tool(
    name="ligand_search",
    description="Search WhatsApp messages by text. Optionally scope to a contact.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def ligand_search(query: str, name: str = "", limit: int = 20) -> LigandResult:
    from metabolon.organelles.gap_junction import search_signals

    result = search_signals(query, name, limit)
    return LigandResult(messages=result)


@tool(
    name="ligand_draft",
    description="Draft a WhatsApp message. NEVER sends -- returns shell command.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def ligand_draft(name: str, message: str) -> LigandDraft:
    from metabolon.organelles.gap_junction import compose_signal

    return LigandDraft(draft=compose_signal(name, message))


@tool(
    name="receptor_list",
    description="List recent WhatsApp chats.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def receptor_list(limit: int = 20) -> ReceptorList:
    from metabolon.organelles.gap_junction import active_junctions

    return ReceptorList(chats=active_junctions(limit))


@tool(
    name="receptor_sync",
    description="Check the wacli sync daemon status.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def receptor_sync() -> Vital:
    from metabolon.organelles.gap_junction import junction_status

    return Vital(status="ok", message=junction_status())
