"""glycolysis_rate — symbiont dependency ratio tracker.

Glycolysis = energy extracted without the symbiont (pure deterministic code).
Measures what fraction of organism capabilities run without LLM calls.

Registry-based v1: capabilities are classified here and updated as the
organism evolves. The methylation cycle can update classifications when
a capability crystallises from LLM to deterministic.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Capability registry
# Each entry: capability_name -> "deterministic" | "symbiont" | "hybrid"
#
# deterministic (cytosol): runs entirely in Python — probes, file checks,
#   state persistence, config reading, scheduling, infection logging
# symbiont (mitochondrial): requires LLM call — diagnosis, synthesis,
#   methylation crystallisation, content generation, hybridisation
# hybrid: deterministic match with symbiont fallback (adaptive repair)
# ---------------------------------------------------------------------------

_REGISTRY: dict[str, str] = {
    # --- Deterministic (cytosol) ---
    "inflammasome_probes": "deterministic",       # _PROBES list — pure Python health checks
    "infection_logging": "deterministic",          # record_infection() → SQLite
    "chromatin_recall": "deterministic",           # vector DB recall, no LLM
    "rss_fetch": "deterministic",                  # endocytosis RSS — HTTP + parse
    "rss_sorting": "deterministic",                # sorting.py — tag rules
    "respirometry_parse": "deterministic",         # bank statement parsers
    "circadian_read": "deterministic",             # Oura API read — pure HTTP
    "membrane_potential": "deterministic",         # readiness threshold logic
    "fasti_calendar": "deterministic",             # calendar read via applescript
    "disk_lysosome": "deterministic",              # cargo-sweep + rm — pure subprocess
    "nociception_log": "deterministic",            # file append
    "infection_summary": "deterministic",          # DB query + aggregate
    "anabolism_signals": "deterministic",          # git log + file reads
    "angiogenesis_detect": "deterministic",        # infection log scan — pattern match
    "sporulation": "deterministic",                # checkpoint save/load — file I/O
    "histone_store": "deterministic",              # SQLite insert/query
    "exocytosis_telegram": "deterministic",        # Telegram API call
    "exocytosis_tweet": "deterministic",           # Twitter API call
    "gap_junction_read": "deterministic",          # WhatsApp read — pure HTTP
    "endosomal_gmail": "deterministic",            # Gmail API — pure HTTP
    "pinocytosis_fetch": "deterministic",          # HTTP fetch, no LLM
    "chemotaxis_perplexity": "deterministic",      # Perplexity API — routes query, no internal LLM
    "setpoint_acclimatise": "deterministic",       # threshold drift — pure math
    "circadian_clock": "deterministic",            # cron scheduling
    "perfusion_routing": "deterministic",          # star routing table lookup
    "glycolysis_rate": "deterministic",            # this module — self-referential

    # --- Symbiont-dependent (mitochondrial) ---
    "homeostasis_financial": "symbiont",           # synthesize() LLM call over vault notes
    "repair_diagnosis": "symbiont",                # immune_response() → LLM metaprompt
    "methylation_crystallise": "symbiont",         # LLM judgment → permanent rule
    "taste_judge": "symbiont",                     # constitutional gate — LLM scoring
    "transduction_digest": "symbiont",             # content synthesis via LLM
    "potentiation": "symbiont",                    # LLM drill generation
    "engram_anam": "symbiont",                     # semantic search → LLM synthesis
    "ligand_draft": "symbiont",                    # email drafting via LLM
    "rheotaxis_synthesis": "symbiont",             # multi-source synthesis via LLM
    "proprioception_gradient": "symbiont",         # skill gap analysis via LLM
    "germination_brief": "symbiont",               # project brief synthesis via LLM
    "entrainment_brief": "symbiont",               # circadian brief via LLM
    "emit_spark": "symbiont",                      # idea generation via LLM
    "emit_praxis": "symbiont",                     # praxis update via LLM
    "poiesis_wave": "symbiont",                    # creative synthesis via LLM

    # --- Hybrid (deterministic match + symbiont fallback) ---
    "adaptive_repair": "hybrid",                   # inflammasome: deterministic patterns first, LLM fallback
    "angiogenesis_propose": "hybrid",              # detect = deterministic, propose = LLM
    "endocytosis_relevance": "hybrid",             # scoring heuristic + LLM rerank
    "rss_breaking": "hybrid",                      # rule filter + LLM significance check
}

_SNAPSHOT_PATH = Path.home() / ".cache" / "glycolysis" / "snapshots.jsonl"


def measure_rate() -> dict:
    """Classify each capability and compute the glycolysis percentage.

    Returns {deterministic_count, symbiont_count, hybrid_count, glycolysis_pct}.
    glycolysis_pct = deterministic / total * 100 (hybrids count as 0.5 each).
    """
    d = sum(1 for v in _REGISTRY.values() if v == "deterministic")
    s = sum(1 for v in _REGISTRY.values() if v == "symbiont")
    h = sum(1 for v in _REGISTRY.values() if v == "hybrid")
    total = d + s + h
    # Hybrids: half-deterministic, half-symbiont
    glycolysis_pct = round(((d + h * 0.5) / total * 100) if total else 0.0, 1)
    return {
        "deterministic_count": d,
        "symbiont_count": s,
        "hybrid_count": h,
        "total": total,
        "glycolysis_pct": glycolysis_pct,
    }


def trend(days: int = 30) -> list[dict]:
    """Read snapshots.jsonl and return daily glycolysis_pct trend (newest last).

    Each entry: {date, glycolysis_pct, deterministic_count, symbiont_count, hybrid_count}.
    """
    if not _SNAPSHOT_PATH.exists():
        return []

    cutoff = datetime.date.today() - datetime.timedelta(days=days)
    results = []
    seen_dates: set[str] = set()

    with _SNAPSHOT_PATH.open() as f:
        lines = f.readlines()

    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = entry.get("timestamp", "")
        date_str = ts[:10] if ts else ""
        if not date_str or date_str in seen_dates:
            continue
        try:
            entry_date = datetime.date.fromisoformat(date_str)
        except ValueError:
            continue
        if entry_date < cutoff:
            continue
        seen_dates.add(date_str)
        results.append({
            "date": date_str,
            "glycolysis_pct": entry.get("glycolysis_pct"),
            "deterministic_count": entry.get("deterministic_count"),
            "symbiont_count": entry.get("symbiont_count"),
            "hybrid_count": entry.get("hybrid_count"),
        })

    return list(reversed(results))


def snapshot() -> dict:
    """Run measure_rate() and append to snapshots.jsonl with ISO timestamp."""
    rate = measure_rate()
    entry = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        **rate,
    }
    _SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _SNAPSHOT_PATH.open("a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry
