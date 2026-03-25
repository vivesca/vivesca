"""keryx — ligand-receptor signalling via WhatsApp (wacli).

Tools:
  ligand_bind   — bind to a conversation (read messages)
  ligand_draft  — draft a ligand for release (NEVER sends directly)
  receptor_list — list available receptors (recent chats)
  receptor_sync — check receptor synchronisation state
"""

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.morphology import Secretion, Vital

# Gap junction contacts: direct, bidirectional, low-friction (family, close friends)
# Receptor contacts: formal, packaged, selective (professional, acquaintances)
GAP_JUNCTION_CONTACTS = {"tara", "mum", "dad", "brother", "sister", "yujie"}


def _contact_type(name: str) -> str:
    """Classify contact as gap junction (close) or receptor (formal)."""
    return "gap_junction" if name.lower() in GAP_JUNCTION_CONTACTS else "receptor"


class LigandResult(Secretion):
    """Bound ligand — messages from a conversation receptor."""

    messages: str


class LigandDraft(Secretion):
    """Draft ligand — prepared for manual release."""

    draft: str


class ReceptorList(Secretion):
    """Available receptors — recent WhatsApp conversations."""

    chats: str


@tool(
    name="ligand_bind",
    description="Read a WhatsApp conversation. Merges phone + LID JID threads.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def ligand_bind(name: str, limit: int = 20) -> LigandResult:
    """Bind to a conversation receptor and read its ligands."""
    contact = _contact_type(name)
    from metabolon.organelles.gap_junction import receive_signals

    result = receive_signals(name, limit)
    prefix = f"[{contact}] " if contact == "gap_junction" else ""
    return LigandResult(messages=f"{prefix}{result}")


@tool(
    name="ligand_draft",
    description="Draft a WhatsApp message. NEVER sends — returns shell block for manual execution.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def ligand_draft(name: str, message: str) -> LigandDraft:
    """Draft a ligand for manual secretion."""
    from metabolon.organelles.gap_junction import compose_signal

    result = compose_signal(name, message)
    return LigandDraft(draft=result)


@tool(
    name="receptor_list",
    description="List recent WhatsApp chats.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def receptor_list(limit: int = 20) -> ReceptorList:
    """List available conversation receptors."""
    from metabolon.organelles.gap_junction import active_junctions

    result = active_junctions(limit)
    return ReceptorList(chats=result)


@tool(
    name="receptor_sync",
    description="Check the wacli sync daemon status.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def receptor_sync() -> Vital:
    """Check receptor synchronisation state."""
    from metabolon.organelles.gap_junction import junction_status

    result = junction_status()
    return Vital(status="ok", message=result)
