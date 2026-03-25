"""noesis — chemotaxis through web-grounded search (Perplexity API).

Tools:
  chemotaxis_search   — quick gradient sensing (~$0.006)
  chemotaxis_ask      — thorough environmental survey (~$0.01)
  chemotaxis_research — deep chemotactic exploration (~$0.40, EXPENSIVE)
"""

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.morphology import Secretion


class ChemotaxisResult(Secretion):
    """Chemotactic signal — web search synthesis with citations."""

    synthesis: str


@tool(
    name="chemotaxis_search",
    description="Quick web search (~$0.006). Cited synthesis for factual lookups.",
    annotations=ToolAnnotations(readOnlyHint=False),
)
def chemotaxis_search(query: str) -> ChemotaxisResult:
    """Quick chemotactic gradient sensing."""
    from metabolon.organelles.chemotaxis_engine import recall as _search

    result = _search(query)
    return ChemotaxisResult(synthesis=result)


@tool(
    name="chemotaxis_ask",
    description="Thorough web search (~$0.01). Structured survey with citations.",
    annotations=ToolAnnotations(readOnlyHint=False),
)
def chemotaxis_ask(query: str) -> ChemotaxisResult:
    """Thorough environmental survey."""
    from metabolon.organelles.chemotaxis_engine import ask as _ask

    result = _ask(query)
    return ChemotaxisResult(synthesis=result)


@tool(
    name="chemotaxis_research",
    description="Deep research (~$0.40). EXPENSIVE — depth must justify cost. Saves to ~/genome/.",
    annotations=ToolAnnotations(readOnlyHint=False),
)
def chemotaxis_research(query: str) -> ChemotaxisResult:
    """Deep chemotactic exploration (expensive)."""
    from metabolon.organelles.chemotaxis_engine import research as _research

    result = _research(query)
    return ChemotaxisResult(synthesis=result)


def _gradient_score(result: str) -> int:
    """Score search result quality for gradient-following. Higher = stronger signal."""
    score = 0
    if len(result) > 500:
        score += 1
    if len(result) > 1500:
        score += 1
    if result.count("http") > 2:
        score += 1  # multiple citations
    if "no results" in result.lower() or "i don't" in result.lower():
        score -= 2
    return score


def gradient_recall(query: str, threshold: int = 2, max_iterations: int = 3) -> ChemotaxisResult:
    """Chemotaxis: gradient-following iterative search.

    Searches, scores result quality, and if below threshold,
    extracts key terms from best results and reformulates.
    Deterministic reformulation, not LLM-mediated.
    """
    best_result = ""
    best_score = -1

    from metabolon.organelles.chemotaxis_engine import recall as _search

    for _i in range(max_iterations):
        result = _search(query)
        score = _gradient_score(result)

        if score > best_score:
            best_result = result
            best_score = score

        if score >= threshold:
            break

        # Gradient: extract capitalized terms from result for reformulation
        import re

        terms = set(re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", result))
        if terms:
            # Add strongest signal terms to query
            refinement = " ".join(list(terms)[:3])
            query = f"{query} {refinement}"

    prefix = (
        f"[gradient: {best_score}/{threshold}, {_i + 1} iterations]\n\n"
        if best_score < threshold
        else ""
    )
    return ChemotaxisResult(synthesis=f"{prefix}{best_result}")
