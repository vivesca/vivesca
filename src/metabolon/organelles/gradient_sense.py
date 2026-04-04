from __future__ import annotations

"""gradient_sense — sensor array reading and polarity detection.

Biology: A small stochastic asymmetry amplified into a stable polarity axis.
Cdc42 in yeast, PCP in epithelia — the cell detects a gradient, amplifies it,
and locks onto a direction. One axis wins and organises subsequent behaviour.

This organelle implements the sensing half: reads signals across three sensor
arrays (lustro relevance log, tool invocation log, search query log), detects
which topic domains are co-trending across multiple sensors, and reports the
polarity vector — the domain the organism is drifting toward.

Sensor arrays:
  - Lustro relevance log: RSS articles scored >=7 (high-signal news items)
  - Signals log: tool invocation frequency by domain over rolling window
  - Rheotaxis log: search queries (free-text, highest semantic richness)

Output: ranked polarity vectors with signal strength and sensor coverage.
"""


import json
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path

from metabolon.morphology import Secretion

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_RELEVANCE_LOG = Path.home() / ".cache" / "lustro" / "relevance.jsonl"
_SIGNALS_LOG = Path.home() / ".local" / "share" / "vivesca" / "signals.jsonl"
_RHEOTAXIS_LOG = Path.home() / "germline" / "loci" / "signals" / "rheotaxis.jsonl"

# ---------------------------------------------------------------------------
# Sensor topology: which sensor pairs are adjacent vs independent
# ---------------------------------------------------------------------------
# Adjacent pairs: both sensors scan external content — confirmation is
# redundant (same side of the membrane).
ADJACENT: set[frozenset[str]] = {
    frozenset({"endocytosis_signal", "rheotaxis_queries"}),  # both are external content scanning
}

# Independent pairs: what you read vs what you do — structurally orthogonal
# sensors on opposite sides of the membrane.
INDEPENDENT: set[frozenset[str]] = {
    frozenset({"endocytosis_signal", "tool_signals"}),  # what you read vs what you do
    frozenset({"rheotaxis_queries", "tool_signals"}),  # what you search vs what you do
}

# Coverage weights per confirmation pattern
# Adjacent 2-sensor: 1.5 (not full 2 — redundant signal)
# Independent 2-sensor: 2.0 (full — orthogonal confirmation)
# 3-sensor (always independent across at least one axis): 3.0
_COVERAGE_ADJACENT_2 = 1.5
_COVERAGE_INDEPENDENT_2 = 2.0
_COVERAGE_ALL_3 = 3.0

# Topic clusters: canonical domain name → keyword set
# These are the axes the organism can orient toward.
# Biology: these are the ligand families the gradient detector is tuned for.
_TOPIC_CLUSTERS: dict[str, list[str]] = {
    "ai_governance": [
        "governance",
        "regulatory",
        "regulation",
        "compliance",
        "hkma",
        "sfc",
        "mas",
        "pra",
        "policy",
        "framework",
        "eu ai act",
        "model risk",
        "sr 11-7",
        "explainability",
        "audit",
        "accountability",
    ],
    "ai_agents": [
        "agent",
        "agentic",
        "autonomous",
        "multi-agent",
        "tool use",
        "mcp",
        "workflow",
        "orchestration",
        "crew",
        "langgraph",
    ],
    "ai_models": [
        "model",
        "llm",
        "gpt",
        "claude",
        "gemini",
        "benchmark",
        "reasoning",
        "capability",
        "release",
        "frontier",
        "openai",
        "anthropic",
        "deepseek",
    ],
    "banking_fintech": [
        "bank",
        "banking",
        "financial services",
        "fintech",
        "wealth",
        "insurance",
        "capital markets",
        "payments",
        "fraud",
        "aml",
        "kyc",
        "credit",
        "hsbc",
        "jpmorgan",
    ],
    "career_consulting": [
        "consulting",
        "capco",
        "interview",
        "job",
        "salary",
        "role",
        "principal",
        "engagement",
        "client",
        "proposal",
        "rga",
        "cv",
        "linkedin",
    ],
    "health": [
        "sleep",
        "readiness",
        "oura",
        "exercise",
        "gym",
        "training",
        "recovery",
        "hrv",
        "heart rate",
        "nutrition",
        "headache",
    ],
    "school_family": [
        "esf",
        "school",
        "kindergarten",
        "theo",
        "tara",
        "family",
        "nursery",
        "k1",
        "k2",
        "admission",
    ],
    "ai_infra": [
        "infrastructure",
        "deployment",
        "production",
        "latency",
        "cost",
        "token",
        "context window",
        "fine-tuning",
        "rag",
        "vector",
        "embedding",
        "mcp server",
    ],
}

# Tool names mapped to topic domain (for signal log classification)
_TOOL_DOMAINS: dict[str, str] = {
    "rheotaxis": "ai_models",
    "histone": "career_consulting",
    "histone_mark": "career_consulting",
    "circadian": "career_consulting",
    "circadian_set": "career_consulting",
    "ligand_bind": "career_consulting",
    "ligand_draft": "career_consulting",
    "membrane_potential": "health",
    "circadian_sleep": "health",
    "homeostasis_financial": "banking_fintech",
    "homeostasis_system": "ai_infra",
    "sorting_thread": "career_consulting",
    "sorting_search": "career_consulting",
    "emit_tweet": "ai_governance",
    "emit_publish": "ai_governance",
    "emit_spark": "ai_governance",
    "endocytosis_extract": "ai_models",
    "exocytosis_text": "ai_governance",
}


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------


class GradientVector(Secretion):
    """A directional signal — one domain trending across sensors."""

    domain: str
    signal_strength: float  # 0.0-1.0 normalised across detected domains
    sensor_coverage: int  # how many of 3 sensors detected this domain
    topology_bonus: str  # "independent", "adjacent", "single", or "full"
    sensors: dict[str, int]  # sensor name → raw hit count
    top_titles: list[str]  # up to 3 lustro titles that drove this
    top_queries: list[str]  # up to 3 search queries that drove this
    window_days: int


class GradientReport(Secretion):
    """Polarity sensing output — organism's current directional bias."""

    polarity_vector: str  # strongest domain, or "diffuse" if no clear axis
    gradients: list[GradientVector]
    window_days: int
    sensors_read: list[str]
    interpretation: str


# ---------------------------------------------------------------------------
# Sensing functions
# ---------------------------------------------------------------------------


def topology_weight(active_sensors: set[str]) -> tuple[float, str]:
    """Return (weighted_coverage, topology_bonus) for a set of active sensors.

    Coverage rules (biology: membrane receptor topology):
      - 1 sensor          → 1.0,  "single"
      - 2 adjacent        → 1.5,  "adjacent"   (redundant signal, same side)
      - 2 independent     → 2.0,  "independent" (orthogonal confirmation)
      - 3 sensors (all)   → 3.0,  "full"
    """
    n = len(active_sensors)
    if n == 0:
        return 0.0, "single"
    if n == 1:
        return 1.0, "single"
    if n >= 3:
        return _COVERAGE_ALL_3, "full"
    # Exactly 2 active sensors — check topology
    pair = frozenset(active_sensors)
    if pair in ADJACENT:
        return _COVERAGE_ADJACENT_2, "adjacent"
    if pair in INDEPENDENT:
        return _COVERAGE_INDEPENDENT_2, "independent"
    # Unknown pair — treat as independent (conservative)
    return _COVERAGE_INDEPENDENT_2, "independent"


def score_text(text: str) -> dict[str, int]:
    """Classify a text fragment against topic clusters. Returns hit counts per domain."""
    text_lower = text.lower()
    hits: dict[str, int] = {}
    for domain, keywords in _TOPIC_CLUSTERS.items():
        count = sum(1 for kw in keywords if kw in text_lower)
        if count > 0:
            hits[domain] = count
    return hits


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def sense_endocytosis(
    days: int,
) -> tuple[dict[str, int], dict[str, list[str]]]:
    """Read lustro relevance log. Returns (domain_hits, domain_titles)."""
    cutoff = datetime.now(UTC) - timedelta(days=days)
    domain_hits: Counter = Counter()
    domain_titles: dict[str, list[str]] = defaultdict(list)

    for row in _read_jsonl(_RELEVANCE_LOG):
        score = row.get("score", 0)
        try:
            if int(score) < 6:  # only signal-grade items
                continue
        except TypeError, ValueError:
            continue

        raw_ts = row.get("timestamp", "")
        try:
            ts = datetime.fromisoformat(str(raw_ts))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=UTC)
            if ts < cutoff:
                continue
        except ValueError, TypeError:
            continue

        title = str(row.get("title", ""))
        hits = score_text(title)
        for domain, count in hits.items():
            domain_hits[domain] += count
            if len(domain_titles[domain]) < 5:
                domain_titles[domain].append(title)

    return dict(domain_hits), dict(domain_titles)


def sense_signals(days: int) -> dict[str, int]:
    """Read tool invocation log. Returns domain hit counts from tool usage."""
    cutoff = datetime.now(UTC) - timedelta(days=days)
    domain_hits: Counter = Counter()

    for row in _read_jsonl(_SIGNALS_LOG):
        raw_ts = row.get("ts", "")
        try:
            ts = datetime.fromisoformat(str(raw_ts))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=UTC)
            if ts < cutoff:
                continue
        except ValueError, TypeError:
            continue

        tool_name = str(row.get("tool", ""))
        domain = _TOOL_DOMAINS.get(tool_name)
        if domain:
            domain_hits[domain] += 1

    return dict(domain_hits)


def sense_rheotaxis(days: int) -> tuple[dict[str, int], dict[str, list[str]]]:
    """Read rheotaxis search log (JSONL). Returns (domain_hits, domain_queries)."""
    if not _RHEOTAXIS_LOG.exists():
        return {}, {}

    cutoff = datetime.now(UTC) - timedelta(days=days)
    domain_hits: Counter = Counter()
    domain_queries: dict[str, list[str]] = defaultdict(list)

    try:
        with open(_RHEOTAXIS_LOG) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts_str = entry.get("ts", "")
                try:
                    ts = datetime.fromisoformat(ts_str)
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=UTC)
                    if ts < cutoff:
                        continue
                except ValueError:
                    continue
                query_text = entry.get("query", "")
                if not query_text:
                    continue
                hits = score_text(query_text)
                for domain, count in hits.items():
                    domain_hits[domain] += count
                    if len(domain_queries[domain]) < 5:
                        domain_queries[domain].append(query_text)
    except OSError:
        return {}, {}

    return dict(domain_hits), dict(domain_queries)


# ---------------------------------------------------------------------------
# Aggregation / report building
# ---------------------------------------------------------------------------


def build_gradient_report(days: int = 7) -> GradientReport:
    """Sense directional gradients across the organism's sensor arrays.

    Reads three signal sources — lustro RSS relevance scores, tool invocation
    frequency, and search query text — then detects which topic domains are
    co-trending. Returns the polarity vector: the domain(s) the organism is
    orienting toward.

    Biology: implements the Direction Maker pattern (Andrews et al. 2024).
    Small asymmetric signals are detected and compared across sensors.
    The domain with highest sensor coverage is the polarity axis.

    Args:
        days: Rolling window in days to consider (default 7).
    """
    # Sense each array
    lustro_hits, lustro_titles = sense_endocytosis(days)
    signal_hits = sense_signals(days)
    rheotaxis_hits, rheotaxis_queries = sense_rheotaxis(days)

    sensors_read = []
    if lustro_hits:
        sensors_read.append("endocytosis_signal")
    if signal_hits:
        sensors_read.append("tool_signals")
    if rheotaxis_hits:
        sensors_read.append("rheotaxis_queries")

    # Aggregate: per domain, count sensors that fired + total hits
    all_domains = set(lustro_hits) | set(signal_hits) | set(rheotaxis_hits)

    gradients: list[GradientVector] = []
    for domain in all_domains:
        sensors: dict[str, int] = {}
        total_hits = 0
        if domain in lustro_hits:
            sensors["endocytosis_signal"] = lustro_hits[domain]
            total_hits += lustro_hits[domain]
        if domain in signal_hits:
            sensors["tool_signals"] = signal_hits[domain]
            total_hits += signal_hits[domain]
        if domain in rheotaxis_hits:
            sensors["rheotaxis_queries"] = rheotaxis_hits[domain]
            total_hits += rheotaxis_hits[domain]

        coverage = len(sensors)
        _weighted_cov, topology_bonus = topology_weight(set(sensors.keys()))
        gradients.append(
            GradientVector(
                domain=domain,
                signal_strength=0.0,  # normalised below
                sensor_coverage=coverage,
                topology_bonus=topology_bonus,
                sensors=sensors,
                top_titles=lustro_titles.get(domain, [])[:3],
                top_queries=rheotaxis_queries.get(domain, [])[:3],
                window_days=days,
            )
        )

    # Normalise signal strength: topology-weighted coverage x total hits
    # Independent sensor pairs count more than adjacent pairs.
    if gradients:

        def _topo_weighted(g: GradientVector) -> float:
            w, _ = topology_weight(set(g.sensors.keys()))
            return w * sum(g.sensors.values())

        max_weighted = max(_topo_weighted(g) for g in gradients)
        if max_weighted > 0:
            for g in gradients:
                g.signal_strength = round(_topo_weighted(g) / max_weighted, 3)

    # Sort: topology-weighted coverage first (independent > adjacent > single),
    # then by normalised signal strength.
    def _sort_key(g: GradientVector) -> tuple[float, float]:
        w, _ = topology_weight(set(g.sensors.keys()))
        return (w, g.signal_strength)

    gradients.sort(key=_sort_key, reverse=True)

    # Polarity vector: top domain if coverage >= 2, else "diffuse"
    if gradients and gradients[0].sensor_coverage >= 2:
        polarity_vector = gradients[0].domain
    elif gradients:
        polarity_vector = f"{gradients[0].domain} (single-sensor, unconfirmed)"
    else:
        polarity_vector = "diffuse"

    # Interpretation
    if polarity_vector == "diffuse":
        interpretation = (
            f"No dominant gradient detected over the last {days} days. "
            "Signals are distributed across topics — no clear orientation. "
            "Organism is in isotropic state."
        )
    elif gradients[0].sensor_coverage == 3:
        interpretation = (
            f"Strong polarity: '{polarity_vector}' confirmed across all 3 sensor arrays. "
            f"Signal strength: {gradients[0].signal_strength:.0%}. "
            "Organism is well-oriented toward this domain."
        )
    elif gradients[0].sensor_coverage == 2:
        topo = gradients[0].topology_bonus
        topo_note = (
            "Independent sensors (orthogonal confirmation)."
            if topo == "independent"
            else "Adjacent sensors (redundant signal — weaker confirmation)."
        )
        interpretation = (
            f"Emerging polarity: '{polarity_vector}' detected in 2 of 3 sensor arrays "
            f"(sensors: {', '.join(gradients[0].sensors.keys())}). "
            f"Signal strength: {gradients[0].signal_strength:.0%}. "
            f"{topo_note} "
            "Gradient is forming but not yet locked."
        )
    else:
        interpretation = (
            f"Weak signal: '{polarity_vector}' detected in only 1 sensor array. "
            "Insufficient cross-sensor confirmation for polarity."
        )

    return GradientReport(
        polarity_vector=polarity_vector,
        gradients=gradients[:8],  # top 8, avoid noise
        window_days=days,
        sensors_read=sensors_read,
        interpretation=interpretation,
    )
