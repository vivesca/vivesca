"""ExecutiveSubstrate -- cortical metabolism of constitutional rules.

Deliberative: senses rules and their signal evidence.
"""

class ExecutiveSubstrate:
    """Cortical substrate: audits constitution rules."""

    name: str = 'constitution'

    def sense(self, days: int = 30) -> list:
        """Read constitution rules and cross-reference with signal evidence."""
        return []

    def candidates(self, sensed: list) -> list:
        """Rules without evidence are candidates."""
        return []

    def act(self, candidate: dict) -> str:
        """Propose action for rules without evidence."""
        return ''

    def report(self, sensed: list, acted: list) -> str:
        """Format a constitution audit report."""
        return ''
