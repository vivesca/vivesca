"""Substrate implementations — one per metabolism target."""

from __future__ import annotations

# Lazy imports to avoid circular dependencies and keep startup fast.
_RECEPTOR_CATALOG: dict[str, type] | None = None


def _build_receptor_catalog() -> dict[str, type]:
    from metabolon.metabolism.substrates.constitution import ExecutiveSubstrate
    from metabolon.metabolism.substrates.hygiene import HygieneSubstrate
    from metabolon.metabolism.substrates.memory import ConsolidationSubstrate
    from metabolon.metabolism.substrates.operons import OperonSubstrate
    from metabolon.metabolism.substrates.respiration import RespirationSubstrate
    from metabolon.metabolism.substrates.spending import SpendingSubstrate
    from metabolon.metabolism.substrates.tools import PhenotypeSubstrate
    from metabolon.metabolism.substrates.mismatch_repair import AnamScanSubstrate

    return {
        "phenotype": PhenotypeSubstrate,
        "executive": ExecutiveSubstrate,
        "consolidation": ConsolidationSubstrate,
        "respiration": RespirationSubstrate,
        "hygiene": HygieneSubstrate,
        "spending": SpendingSubstrate,
        "operons": OperonSubstrate,
        "mismatch_repair": AnamScanSubstrate,
    }


def receptor_catalog() -> dict[str, type]:
    """Return the substrate receptor catalog, building it on first call."""
    global _RECEPTOR_CATALOG
    if _RECEPTOR_CATALOG is None:
        _RECEPTOR_CATALOG = _build_receptor_catalog()
    return _RECEPTOR_CATALOG


SUBSTRATES = property(lambda self: receptor_catalog())  # for module-level access

__all__ = ["receptor_catalog"]
