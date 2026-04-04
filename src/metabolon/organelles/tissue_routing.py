
"""tissue_routing — match the right symbiont strain to each subsystem.

Muscle has more mitochondria than skin. Routing follows observed performance,
not just cost tiers. Reads FROM mitophagy outcomes; never duplicates tracking.
"""


_DEFAULTS: dict[str, str] = {
    "probe": "glm",  # mechanical checks, cheap
    "repair_known": "glm",  # pattern matching, deterministic-adjacent
    "repair_novel": "sonnet",  # diagnosis needs reasoning
    "methylation": "sonnet",  # pattern crystallization
    "hybridization": "opus",  # creative design, highest judgment
    "research": "sonnet",  # web search + synthesis
    "coding": "codex",  # formulaic code, free
    "synthesis": "opus",  # content requiring taste
    "poiesis_dispatch": "sonnet",  # wave orchestration
    "quality_gate": "sonnet",  # verification
}


def default_routes() -> dict[str, str]:
    """Starting configuration — known best practices by task type."""
    return dict(_DEFAULTS)


def observed_routes() -> dict[str, str]:
    """Override defaults with best-performing model per task from mitophagy data.

    Falls back to defaults when no data is available.
    """
    routes = dict(_DEFAULTS)
    try:
        from metabolon.organelles.mitophagy import is_blacklisted, model_fitness

        by_task: dict[str, dict[str, tuple[float, int]]] = {}
        for row in model_fitness(days=7):
            task, model = row.get("task_type", ""), row.get("model", "")
            if task and model:
                by_task.setdefault(task, {})[model] = (
                    row.get("rate", 0.0),
                    row.get("attempts", 0),
                )

        for task, candidates in by_task.items():
            eligible = {m: v for m, v in candidates.items() if not is_blacklisted(m, task)}
            if eligible and task in routes:
                routes[task] = max(eligible.items(), key=lambda kv: (kv[1][0], kv[1][1]))[0]
    except Exception:
        pass
    return routes


def route(task_type: str) -> str:
    """Return recommended model for a task type.

    Priority: blacklist check on default -> observed performance -> defaults.
    """
    default_model = _DEFAULTS.get(task_type, "sonnet")
    try:
        from metabolon.organelles.mitophagy import is_blacklisted, recommend_model

        if is_blacklisted(default_model, task_type):
            return recommend_model(task_type) or default_model
    except Exception:
        pass
    return observed_routes().get(task_type, default_model)


def route_report() -> str:
    """Human-readable routing table with mitophagy performance data where available."""
    defaults = default_routes()
    observed = observed_routes()

    fitness_index: dict[tuple[str, str], dict] = {}
    blacklisted_pairs: set[tuple[str, str]] = set()
    try:
        from metabolon.organelles.mitophagy import _load_blacklist, model_fitness

        for row in model_fitness(days=7):
            fitness_index[(row.get("task_type", ""), row.get("model", ""))] = row
        for model, tasks in _load_blacklist().items():
            for t in tasks:
                blacklisted_pairs.add((model, t))
    except Exception:
        pass

    lines = ["Tissue routing — symbiont allocation by subsystem", ""]
    for task in sorted(defaults.keys()):
        default_m, active_m = defaults[task], observed.get(task, defaults[task])
        row = fitness_index.get((task, active_m))
        if row:
            annotation = f"({row['successes']}/{row['attempts']} ok, {row['rate']:.0%} over 7d)"
        elif active_m != default_m:
            annotation = f"[observed, default was {default_m}]"
        else:
            annotation = "[default, no mitophagy data]"
        flag = "  *** BLACKLISTED ***" if (active_m, task) in blacklisted_pairs else ""
        lines.append(f"  {task:<20} -> {active_m}  {annotation}{flag}")

    if blacklisted_pairs:
        lines += ["", "Blacklisted pairs:"] + [
            f"  {m} x {t}" for m, t in sorted(blacklisted_pairs)
        ]

    return "\n".join(lines)
