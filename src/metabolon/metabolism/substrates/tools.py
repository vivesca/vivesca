"""PhenotypeSubstrate — metabolism of MCP tool descriptions (phenotype).

Wraps the existing sweep logic (emotion computation, selection,
genome) behind the Substrate protocol. The async mutation/taste steps
remain as proposals — this layer stays sync.
"""

from datetime import UTC, datetime, timedelta

from metabolon.metabolism.fitness import Emotion, sense_affect
from metabolon.metabolism.signals import SensorySystem
from metabolon.metabolism.sweep import select
from metabolon.metabolism.variants import Genome


class PhenotypeSubstrate:
    """Substrate for tool description evolution."""

    name: str = "tools"

    def __init__(
        self,
        collector: SensorySystem | None = None,
        genome: Genome | None = None,
    ):
        self.collector = collector or SensorySystem()
        self.genome = genome or Genome()

    def sense(self, days: int = 30) -> list[dict]:
        """Read stimuli and genome, compute per-tool emotion."""
        since = datetime.now(UTC) - timedelta(days=days)
        signals = self.collector.recall_since(since)
        emotions = sense_affect(signals)
        catalogued_loci = self.genome.expressed_tools()

        sensed: list[dict] = []
        locus_population = sorted(set(list(emotions.keys()) + catalogued_loci))

        for tool in locus_population:
            emotion = emotions.get(tool)
            variants = self.genome.allele_variants(tool) if tool in catalogued_loci else []
            sensed.append(
                {
                    "tool": tool,
                    "emotion": emotion,
                    "variant_count": len(variants),
                    "in_store": tool in catalogued_loci,
                }
            )

        return sensed

    def candidates(self, sensed: list[dict]) -> list[dict]:
        """Identify tools with below-median valence or insufficient data."""
        # Reconstruct the emotions dict that select expects.
        phenotype_scores: dict[str, Emotion] = {}
        for entry in sensed:
            if entry["emotion"] is not None:
                phenotype_scores[entry["tool"]] = entry["emotion"]

        unfit_candidates = select(phenotype_scores)

        return [entry for entry in sensed if entry["tool"] in unfit_candidates]

    def act(self, candidate: dict) -> str:
        """Propose a mutation action for a candidate tool.

        Actual mutation requires async LLM calls, so this returns a
        proposal string. The sweep CLI command handles the async path.
        """
        tool = candidate["tool"]
        fitness = candidate["emotion"]

        if not candidate["in_store"]:
            return f"skip: {tool} not in genome"

        if fitness is None:
            return f"mutation needed for {tool}: no emotion data"

        if fitness.valence is None:
            return f"mutation needed for {tool}: insufficient stimuli ({fitness.activations} invocations)"

        return f"mutation needed for {tool}: valence {fitness.valence:.3f}"

    def report(self, sensed: list[dict], acted: list[str]) -> str:
        """Format a phenotype metabolism report."""
        lines: list[str] = []
        lines.append(f"Phenotype substrate: {len(sensed)} tool(s) sensed")
        lines.append("")

        # Status table
        lines.append("-- Status --")
        for entry in sensed:
            fitness = entry["emotion"]
            if fitness is not None:
                val_str = f"{fitness.valence:.3f}" if fitness.valence is not None else "N/A"
                lines.append(
                    f"  {entry['tool']}: valence={val_str} "
                    f"invocations={fitness.activations} "
                    f"success_rate={fitness.success_rate:.1%} "
                    f"variants={entry['variant_count']}"
                )
            else:
                lines.append(f"  {entry['tool']}: no signals, variants={entry['variant_count']}")

        # Actions
        if acted:
            lines.append("")
            lines.append("-- Actions --")
            for action in acted:
                lines.append(f"  {action}")

        return "\n".join(lines)
