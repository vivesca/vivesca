import re
from dataclasses import dataclass

ROUTING_RULES = [
    (r"\b(rust|cargo|crate)\b", "codex", "Rust -> Codex (sandbox + DNS)"),
    (r"\b(multi.?file|cross.?file|refactor)\b", "codex", "Multi-file -> Codex (repo nav)"),
    (
        r"\b(algorithm|function|logic|compute|calculate)\b",
        "gemini",
        "Algorithmic -> Gemini (free, high benchmark)",
    ),
    (
        r"\b(boilerplate|bulk|routine|template|scaffold)\b",
        "opencode",
        "Boilerplate -> OpenCode (GLM-5.1 via Zhipu Coding Plan)",
    ),
]
DEFAULT_TOOL = "goose"


@dataclass(frozen=True)
class RouteDecision:
    tool: str
    reason: str
    pattern: str | None = None


def route_description(description: str, forced_backend: str | None = None) -> RouteDecision:
    if forced_backend:
        return RouteDecision(tool=forced_backend, reason="Forced by CLI option")

    for pattern, tool, reason in ROUTING_RULES:
        if re.search(pattern, description, flags=re.IGNORECASE):
            return RouteDecision(tool=tool, reason=reason, pattern=pattern)

    return RouteDecision(tool=DEFAULT_TOOL, reason="Default route")
