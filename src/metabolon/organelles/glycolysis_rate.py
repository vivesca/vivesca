"""glycolysis_rate — symbiont dependency ratio tracker.

Glycolysis = energy extracted without the symbiont (pure deterministic code).
Measures what fraction of organism capabilities run without LLM calls.

Registry-based v1: capabilities are classified here and updated as the
organism evolves. The methylation cycle can update classifications when
a capability crystallises from LLM to deterministic.
"""

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
    "inflammasome_probes": "deterministic",  # _PROBES list — pure Python health checks
    "infection_logging": "deterministic",  # record_infection() → SQLite
    "chromatin_recall": "deterministic",  # vector DB recall, no LLM
    "rss_fetch": "deterministic",  # endocytosis RSS — HTTP + parse
    "rss_sorting": "deterministic",  # sorting.py — tag rules
    "respirometry_parse": "deterministic",  # bank statement parsers
    "circadian_read": "deterministic",  # Oura API read — pure HTTP
    "membrane_potential": "deterministic",  # readiness threshold logic
    "fasti_calendar": "deterministic",  # calendar read via applescript
    "disk_lysosome": "deterministic",  # cargo-sweep + rm — pure subprocess
    "nociception_log": "deterministic",  # file append
    "infection_summary": "deterministic",  # DB query + aggregate
    "anabolism_signals": "deterministic",  # git log + file reads
    "angiogenesis_detect": "deterministic",  # infection log scan — pattern match
    "sporulation": "deterministic",  # checkpoint save/load — file I/O
    "histone_store": "deterministic",  # SQLite insert/query
    "exocytosis_telegram": "deterministic",  # Telegram API call
    "exocytosis_tweet": "deterministic",  # Twitter API call
    "gap_junction_read": "deterministic",  # WhatsApp read — pure HTTP
    "endosomal_gmail": "deterministic",  # Gmail API — pure HTTP
    "pinocytosis_fetch": "deterministic",  # HTTP fetch, no LLM
    "chemotaxis_perplexity": "deterministic",  # Perplexity API — routes query, no internal LLM
    "setpoint_acclimatise": "deterministic",  # threshold drift — pure math
    "circadian_clock": "deterministic",  # cron scheduling
    "perfusion_routing": "deterministic",  # star routing table lookup
    "glycolysis_rate": "deterministic",  # this module — self-referential
    # --- Symbiont-dependent (mitochondrial) ---
    "homeostasis_financial": "symbiont",  # synthesize() LLM call over financial notes
    "repair_diagnosis": "symbiont",  # immune_response() → LLM metaprompt
    "methylation_crystallise": "symbiont",  # LLM judgment → permanent rule
    "taste_judge": "symbiont",  # constitutional gate — LLM scoring
    "transduction_digest": "symbiont",  # content synthesis via LLM
    "potentiation": "symbiont",  # LLM drill generation
    "engram_anam": "symbiont",  # semantic search → LLM synthesis
    "ligand_draft": "symbiont",  # email drafting via LLM
    "rheotaxis_synthesis": "symbiont",  # multi-source synthesis via LLM
    "proprioception_gradient": "symbiont",  # skill gap analysis via LLM
    "germination_brief": "symbiont",  # project brief synthesis via LLM
    "entrainment_brief": "symbiont",  # circadian brief via LLM
    "emit_spark": "symbiont",  # idea generation via LLM
    "emit_praxis": "symbiont",  # praxis update via LLM
    "poiesis_wave": "symbiont",  # creative synthesis via LLM
    # --- Hybrid (deterministic match + symbiont fallback) ---
    "adaptive_repair": "hybrid",  # inflammasome: deterministic patterns first, LLM fallback
    "angiogenesis_propose": "hybrid",  # detect = deterministic, propose = LLM
    "endocytosis_relevance": "hybrid",  # scoring heuristic + LLM rerank
    "rss_breaking": "hybrid",  # rule filter + LLM significance check
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
        results.append(
            {
                "date": date_str,
                "glycolysis_pct": entry.get("glycolysis_pct"),
                "deterministic_count": entry.get("deterministic_count"),
                "symbiont_count": entry.get("symbiont_count"),
                "hybrid_count": entry.get("hybrid_count"),
            }
        )

    return list(reversed(results))


def snapshot() -> dict:
    """Run measure_rate() and append to snapshots.jsonl with ISO timestamp."""
    rate = measure_rate()
    entry = {
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        **rate,
    }
    _SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _SNAPSHOT_PATH.open("a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


# ---------------------------------------------------------------------------
# Conversion suggestions
# Heuristics for identifying symbiont capabilities that could become deterministic.
# ---------------------------------------------------------------------------

_CONVERSION_HEURISTICS = {
    # If the capability only does structured data transformation, it can be deterministic
    "structured_output_only": [
        # Tasks that just format/structure existing data
        "format_data",
        "transform_output",
        "parse_structured",
    ],
    # If the capability has clear rules, it can be rule-based
    "rule_based_candidate": [
        # Tasks with predictable patterns
        "classify_by_keywords",
        "extract_patterns",
        "validate_structure",
    ],
}

# Capabilities that are potentially convertible from symbiont to deterministic
_CONVERTIBLE_CAPABILITIES = {
    "taste_judge": {
        "reason": "Scoring could be rule-based with explicit criteria",
        "effort": "medium",
        "dependencies": ["criteria_definition", "test_cases"],
    },
    "potentiation": {
        "reason": "Drill generation could use templates with slot filling",
        "effort": "high",
        "dependencies": ["template_library", "content_database"],
    },
    "endocytosis_relevance": {
        "reason": "Already hybrid; deterministic scoring could be improved",
        "effort": "low",
        "dependencies": ["scoring_weights_tuning"],
    },
    "rss_breaking": {
        "reason": "Already hybrid; keyword-based detection could replace LLM check",
        "effort": "low",
        "dependencies": ["keyword_list_maintenance"],
    },
    "angiogenesis_propose": {
        "reason": "Proposals could use templates based on infection type",
        "effort": "medium",
        "dependencies": ["proposal_templates", "infection_taxonomy"],
    },
}


def suggest_conversions() -> list[dict]:
    """Identify symbiont/hybrid capabilities that could become deterministic.

    Returns a list of conversion suggestions, each with:
    - capability: name of the capability
    - current_type: "symbiont" or "hybrid"
    - reason: why it might be convertible
    - effort: "low", "medium", or "high"
    - dependencies: what's needed to make it deterministic
    - priority: computed score (higher = more valuable to convert)

    Priority is based on:
    - How often the capability is used (estimated)
    - Effort required (lower effort = higher priority)
    - Whether it's already hybrid (easier conversion path)
    """
    suggestions = []

    for name, info in _CONVERTIBLE_CAPABILITIES.items():
        current_type = _REGISTRY.get(name)
        if current_type not in ("symbiont", "hybrid"):
            continue

        # Compute priority score
        effort_score = {"low": 3, "medium": 2, "high": 1}.get(info.get("effort", "high"), 1)
        hybrid_bonus = 2 if current_type == "hybrid" else 0
        priority = effort_score + hybrid_bonus

        suggestions.append(
            {
                "capability": name,
                "current_type": current_type,
                "reason": info.get("reason", ""),
                "effort": info.get("effort", "unknown"),
                "dependencies": info.get("dependencies", []),
                "priority": priority,
            }
        )

    # Sort by priority (highest first)
    suggestions.sort(key=lambda x: x["priority"], reverse=True)
    return suggestions


def get_conversion_report() -> dict:
    """Generate a summary report of conversion opportunities.

    Returns:
        - total_symbiont: count of symbiont capabilities
        - total_hybrid: count of hybrid capabilities
        - conversion_candidates: count of identified conversion candidates
        - potential_glycolysis_gain: estimated glycolysis % increase if all converted
        - suggestions: list of conversion suggestions
    """
    rate = measure_rate()
    suggestions = suggest_conversions()

    # Calculate potential gain
    # Each conversion: symbiont -> deterministic adds 1, hybrid -> deterministic adds 0.5
    potential_gain = 0.0
    for s in suggestions:
        if s["current_type"] == "symbiont":
            potential_gain += 1.0
        elif s["current_type"] == "hybrid":
            potential_gain += 0.5

    total = rate["total"]
    current_deterministic_equivalent = rate["deterministic_count"] + rate["hybrid_count"] * 0.5
    new_deterministic_equivalent = current_deterministic_equivalent + potential_gain
    potential_glycolysis_pct = round(
        (new_deterministic_equivalent / total * 100) if total else 0.0, 1
    )

    return {
        "total_symbiont": rate["symbiont_count"],
        "total_hybrid": rate["hybrid_count"],
        "conversion_candidates": len(suggestions),
        "potential_glycolysis_gain": round(potential_glycolysis_pct - rate["glycolysis_pct"], 1),
        "potential_glycolysis_pct": potential_glycolysis_pct,
        "suggestions": suggestions,
    }
