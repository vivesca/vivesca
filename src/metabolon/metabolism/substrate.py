"""Substrate protocol — the contract any metabolism target must satisfy.

Any artifact with three properties is a metabolism target:
1. Stimulus source — how to sense whether it's working
2. Variation mechanism — how to change it
3. Selection criterion — how to judge the change

The Substrate protocol encodes these as four phases:
    sense → candidates → act → report
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class Substrate(Protocol):
    """A metabolism target.

    Implementations wrap existing metabolism logic (fitness, sweep, audit,
    dissolve) behind a uniform interface. The CLI runs the same four-phase
    cycle regardless of what it's metabolising.
    """

    name: str

    def sense(self, days: int = 30) -> list[dict]:
        """Read artifacts and their signal evidence.

        Returns a list of dicts, each representing one artifact with
        whatever metadata the substrate needs (fitness, type, overlap, etc.).
        """
        ...

    def candidates(self, sensed: list[dict]) -> list[dict]:
        """Identify artifacts that need action.

        Filters the sensed list to those below fitness, zero signal,
        ready for promotion, etc.
        """
        ...

    def act(self, candidate: dict) -> str:
        """Execute the action (mutate, promote, prune, migrate).

        Returns a human-readable description of the action taken or proposed.
        Implementations that require async LLM calls return a proposal string
        rather than executing — keeping the protocol sync.
        """
        ...

    def report(self, sensed: list[dict], acted: list[str]) -> str:
        """Format a human-readable report of the metabolism cycle."""
        ...
