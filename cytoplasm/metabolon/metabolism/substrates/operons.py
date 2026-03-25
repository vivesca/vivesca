"""OperonSubstrate — heartbeat monitor for the organism's behavioural repertoire.

Scans signal history for enzyme activity, maps back to operons, and flags
any expressed operon whose enzymes haven't fired within its expected cadence.

The city audit revealed this gap: operons are maps without a heartbeat.
Nothing noticed "we haven't done monitor in 72 hours." This substrate
closes that gap — pure sensing, no mutation.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from metabolon.metabolism.signals import SensorySystem
from metabolon.operons import OPERONS, Operon

# Default staleness thresholds (days) by substrate hint in the operon.
# Operons declare substrates like "daily period", "monthly cycle", etc.
# We parse these into cadence expectations.
_CADENCE_KEYWORDS: dict[str, int] = {
    "daily": 2,
    "zeitgeber": 2,
    "weekly": 10,
    "infradian": 35,
    "monthly": 35,
}
_DEFAULT_STALENESS_DAYS = 14


def _infer_cadence(operon: Operon) -> int:
    """Infer expected cadence in days from operon substrate hints."""
    substrate_text = " ".join(operon.substrates).lower()
    for keyword, days in _CADENCE_KEYWORDS.items():
        if keyword in substrate_text:
            return days
    return _DEFAULT_STALENESS_DAYS


class OperonSubstrate:
    """Substrate for operon recency monitoring."""

    name: str = "operons"

    def __init__(self, collector: SensorySystem | None = None):
        self.collector = collector or SensorySystem()

    def sense(self, days: int = 30) -> list[dict]:
        """Map signal recency to expressed operons."""
        since = datetime.now(UTC) - timedelta(days=days)
        signals = self.collector.recall_since(since)

        # Build tool -> most recent timestamp
        tool_last_seen: dict[str, datetime] = {}
        for s in signals:
            if s.tool in tool_last_seen:
                if s.ts > tool_last_seen[s.tool]:
                    tool_last_seen[s.tool] = s.ts
            else:
                tool_last_seen[s.tool] = s.ts

        now = datetime.now(UTC)
        sensed: list[dict] = []

        for operon in OPERONS:
            if not operon.expressed:
                continue

            cadence = _infer_cadence(operon)

            # Find most recent enzyme firing
            last_fired: datetime | None = None
            fired_enzyme: str | None = None
            for enzyme in operon.enzymes:
                ts = tool_last_seen.get(enzyme)
                if ts is not None and (last_fired is None or ts > last_fired):
                    last_fired = ts
                    fired_enzyme = enzyme

            days_since = (now - last_fired).total_seconds() / 86400 if last_fired else None

            sensed.append(
                {
                    "reaction": operon.reaction,
                    "product": operon.product,
                    "enzymes": operon.enzymes,
                    "cadence_days": cadence,
                    "last_fired": last_fired.isoformat() if last_fired else None,
                    "fired_enzyme": fired_enzyme,
                    "days_since": round(days_since, 1) if days_since is not None else None,
                    "stale": (days_since > cadence if days_since is not None else True),
                }
            )

        return sensed

    def candidates(self, sensed: list[dict]) -> list[dict]:
        """Operons that are stale — overdue relative to their cadence."""
        return [entry for entry in sensed if entry["stale"]]

    def act(self, candidate: dict) -> str:
        """Propose attention — this substrate observes, it doesn't mutate."""
        reaction = candidate["reaction"]
        days = candidate["days_since"]
        cadence = candidate["cadence_days"]

        if days is None:
            return f"dormant signal: {reaction} — no enzyme activity in window"

        return f"stale: {reaction} — {days:.0f}d since last fire (cadence: {cadence}d)"

    def report(self, sensed: list[dict], acted: list[str]) -> str:
        """Format an operon heartbeat report."""
        lines: list[str] = []
        lines.append(f"Operon substrate: {len(sensed)} expressed operon(s) sensed")
        lines.append("")

        # Healthy operons
        healthy = [e for e in sensed if not e["stale"]]
        if healthy:
            lines.append("-- Healthy --")
            for e in healthy:
                lines.append(
                    f"  {e['reaction']}: {e['days_since']:.0f}d ago "
                    f"via {e['fired_enzyme']} (cadence: {e['cadence_days']}d)"
                )

        # Stale operons
        stale = [e for e in sensed if e["stale"]]
        if stale:
            lines.append("")
            lines.append("-- Stale --")
            for e in stale:
                if e["days_since"] is not None:
                    lines.append(
                        f"  {e['reaction']}: {e['days_since']:.0f}d ago "
                        f"(cadence: {e['cadence_days']}d) — {e['product']}"
                    )
                else:
                    lines.append(
                        f"  {e['reaction']}: never fired "
                        f"(cadence: {e['cadence_days']}d) — {e['product']}"
                    )

        # Actions
        if acted:
            lines.append("")
            lines.append("-- Actions --")
            for action in acted:
                lines.append(f"  {action}")

        return "\n".join(lines)
