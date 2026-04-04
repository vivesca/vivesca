"""Bank-specific statement parsers."""

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, TypeAlias

if TYPE_CHECKING:
    from metabolon.respirometry.schema import ConsumptionEvent, RespirogramMeta

type Parser = Callable[[Path], "tuple[RespirogramMeta, list[ConsumptionEvent]]"]

_REGISTRY: dict[str, Parser] = {}


def _build_registry() -> dict[str, Parser]:
    from metabolon.respirometry.parsers.boc import extract_boc
    from metabolon.respirometry.parsers.ccba import extract_ccba
    from metabolon.respirometry.parsers.hsbc import extract_hsbc
    from metabolon.respirometry.parsers.mox import extract_mox
    from metabolon.respirometry.parsers.scb import extract_scb

    return {
        "mox": extract_mox,
        "hsbc": extract_hsbc,
        "ccba": extract_ccba,
        "scb": extract_scb,
        "boc": extract_boc,
    }


def get_parser(bank: str) -> Parser | None:
    """Get the parser function for a given bank."""
    global _REGISTRY
    if not _REGISTRY:
        _REGISTRY = _build_registry()
    return _REGISTRY.get(bank)
