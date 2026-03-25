"""Bank-specific statement parsers."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, TypeAlias

if TYPE_CHECKING:
    from metabolon.spending.schema import StatementMeta, Transaction

Parser: TypeAlias = Callable[[Path], "tuple[StatementMeta, list[Transaction]]"]

_REGISTRY: dict[str, Parser] = {}


def _build_registry() -> dict[str, Parser]:
    from metabolon.spending.parsers.boc import parse_boc
    from metabolon.spending.parsers.ccba import parse_ccba
    from metabolon.spending.parsers.hsbc import parse_hsbc
    from metabolon.spending.parsers.mox import parse_mox
    from metabolon.spending.parsers.scb import parse_scb

    return {
        "mox": parse_mox,
        "hsbc": parse_hsbc,
        "ccba": parse_ccba,
        "scb": parse_scb,
        "boc": parse_boc,
    }


def get_parser(bank: str) -> Parser | None:
    """Get the parser function for a given bank."""
    global _REGISTRY
    if not _REGISTRY:
        _REGISTRY = _build_registry()
    return _REGISTRY.get(bank)
