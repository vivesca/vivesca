from __future__ import annotations


"""Autonomic thresholds with calibration.

A threshold is a pain level that triggers an autonomic response (clean disk,
throttle budget). It calibrates: each time the organism responds, the level
at which it acted shifts the threshold toward observed behaviour. No LLM
judgment involved — sense, respond, calibrate.

Bistable switch (hysteresis)
-----------------------------
Real biological switches — the lac operon, CDK1/Cdc25 feedback, ion channels —
have separate activation and deactivation thresholds. The gap between them is
the hysteresis band. Inside the band the switch holds its previous state,
resisting noise near the boundary. This prevents rapid toggling (oscillation)
when a signal hovers at the crossover point.

`Threshold` supports this pattern via optional `hysteresis` parameter:

    Threshold("disk", default=15, hysteresis=0.25)   # 25 % dead-band
    # activation  = 15.0
    # deactivation = 15 * (1 - 0.25) = 11.25

A value that crossed the activation level keeps the gate open until it falls
below the deactivation level. Callers that do not pass `hysteresis` get
identical activation == deactivation (backward-compatible binary behaviour).

Part of the autonomic layer (see: vigilis, pacing gates, signal collection).
Cortical components (evolution, constitution, memory) use deliberation instead.

Storage: ~/.local/share/vivesca/setpoints/{name}.json
Events:  ~/.local/share/vivesca/setpoints/{name}-events.jsonl
"""


import json
from datetime import date, datetime

from pydantic import BaseModel

from metabolon.locus import setpoints_dir

SETPOINTS_DIR = setpoints_dir


class Threshold:
    """An autonomic threshold that calibrates from observed behaviour.

    Bistable switch with optional hysteresis.  When *hysteresis* > 0 the
    switch exhibits separate activation and deactivation thresholds — the
    biological equivalent of a Schmitt trigger or lac-operon bistability.
    The gate opens when the signal exceeds the activation level and stays
    open until the signal drops below the (lower) deactivation level.

    Parameters
    ----------
    name:
        Identifier used for persistent storage.
    default:
        Activation threshold (and deactivation threshold when hysteresis=0).
    clamp:
        Lower and upper bounds for acclimatisation.
    window:
        Number of recent events used when acclimatising.
    min_samples:
        Minimum observations before acclimatisation fires.
    hysteresis:
        Fractional dead-band width in [0, 1).  deactivation_threshold =
        activation_threshold * (1 - hysteresis).  Default 0 preserves
        original binary (no dead-band) behaviour.
    """

    def __init__(
        self,
        name: str,
        default: float,
        clamp: tuple[float, float] = (0.0, 1000.0),
        window: int = 5,
        min_samples: int = 2,
        hysteresis: float = 0.0,
    ):
        if not (0.0 <= hysteresis < 1.0):
            raise ValueError(f"hysteresis must be in [0, 1), got {hysteresis}")
        self.name = name
        self.default = default
        self.clamp = clamp
        self.window = window
        self.min_samples = min_samples
        self.hysteresis = hysteresis
        self._state_store = SETPOINTS_DIR / f"{name}.json"
        self._events = SETPOINTS_DIR / f"{name}-events.jsonl"
        # In-memory gate state — the stable latch in the bistable switch.
        # None means "never evaluated"; will be set on first is_activated() call.
        self._gate_open: bool | None = None

    # ------------------------------------------------------------------
    # Threshold band — activation / deactivation poles of the bistable switch
    # ------------------------------------------------------------------

    @property
    def activation_threshold(self) -> float:
        """Upper pole: value must exceed this for the gate to open."""
        return self.read()

    @property
    def deactivation_threshold(self) -> float:
        """Lower pole: value must drop below this for the gate to close.

        Equal to activation_threshold when hysteresis == 0 (backward-compatible
        binary behaviour). When hysteresis > 0 the gap between the two poles is
        the dead-band that prevents boundary oscillation.
        """
        return self.read() * (1.0 - self.hysteresis)

    # ------------------------------------------------------------------
    # Bistable gate evaluation
    # ------------------------------------------------------------------

    def is_activated(self, value: float) -> bool:
        """Evaluate the bistable gate for *value*.

        Implements hysteretic switching:
        - If the gate is currently open, it stays open until *value* falls
          below the deactivation threshold (lower pole).
        - If the gate is currently closed (or unset), it opens only when
          *value* exceeds the activation threshold (upper pole).
        - Inside the dead-band (deactivation < value <= activation) the
          previous state is preserved — the Schmitt-trigger property.

        When hysteresis == 0 the two thresholds are equal and the gate
        behaves as a simple binary comparator (original behaviour).
        """
        activate = self.activation_threshold
        deactivate = self.deactivation_threshold

        if self._gate_open is None:
            # First evaluation: initialise from current signal — no flip
            self._gate_open = value >= activate

        if self._gate_open:
            # Gate is open (active state): only close when signal falls
            # below the deactivation level (lower pole of bistable switch)
            if value < deactivate:
                self._gate_open = False
        else:
            # Gate is closed (inactive state): only open when signal rises
            # above the activation level (upper pole)
            if value >= activate:
                self._gate_open = True

        return self._gate_open

    def refractory_gate(self) -> None:
        """Reset in-memory latch state (e.g. between test runs or daily resets)."""
        self._gate_open = None

    # ------------------------------------------------------------------
    # Persistence and calibration (unchanged from original design)
    # ------------------------------------------------------------------

    def read(self) -> float:
        """Current threshold value. Falls back to default if missing/corrupt."""
        try:
            data = json.loads(self._state_store.read_text())
            return float(data.get("value", self.default))
        except Exception:
            return self.default

    def record(self, prior_load: float, post_response: float, **extra: object) -> None:
        """Record an autonomic response and calibrate."""
        event = {
            "ts": datetime.now().isoformat(),
            "before": round(prior_load, 1),
            "after": round(post_response, 1),
            "threshold": self.read(),
            **extra,
        }
        SETPOINTS_DIR.mkdir(parents=True, exist_ok=True)
        with self._events.open("a") as f:
            f.write(json.dumps(event) + "\n")

        self._acclimatise()

    def _acclimatise(self) -> None:
        """Calibrate threshold toward observed behaviour."""
        try:
            lines = self._events.read_text().splitlines()[-self.window :]
            events = [json.loads(ln) for ln in lines]
        except Exception:
            return

        before_values = [e["before"] for e in events if "before" in e]
        if len(before_values) < self.min_samples:
            return

        adapted_setpoint = round(sum(before_values) / len(before_values), 1)
        adapted_setpoint = max(self.clamp[0], min(self.clamp[1], adapted_setpoint))
        self._write(adapted_setpoint, f"acclimatised from {len(before_values)} observations")

    def _write(self, value: float, reason: str) -> None:
        SETPOINTS_DIR.mkdir(parents=True, exist_ok=True)
        data = {"value": value, "reason": reason, "updated": date.today().isoformat()}
        self._state_store.write_text(json.dumps(data))

    def status(self) -> SetpointStatus:
        """Current state for reporting."""
        try:
            lines = self._events.read_text().splitlines()
            n_events = len(lines)
        except Exception:
            n_events = 0

        return SetpointStatus(
            name=self.name,
            value=self.read(),
            default=self.default,
            observations=n_events,
            acclimatised=n_events >= self.min_samples,
            hysteresis=self.hysteresis,
            activation_threshold=self.activation_threshold,
            deactivation_threshold=self.deactivation_threshold,
            gate_open=self._gate_open,
        )


class SetpointStatus(BaseModel):
    """Snapshot of a threshold for reporting."""

    name: str
    value: float
    default: float
    observations: int
    acclimatised: bool
    # Bistable switch metadata
    hysteresis: float = 0.0
    activation_threshold: float | None = None
    deactivation_threshold: float | None = None
    gate_open: bool | None = None
