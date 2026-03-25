"""vivesca metabolism — self-evolving tool descriptions.

One mechanism, any substrate. The SUBSTRATES registry maps target names
to Substrate implementations. New targets register by adding to it.
"""

from metabolon.metabolism.fitness import Emotion, compute_emotion
from metabolon.metabolism.gates import GateResult, reflex_check
from metabolon.metabolism.repair import ImmuneRequest, immune_response
from metabolon.metabolism.signals import SensorySystem, Stimulus
from metabolon.metabolism.substrate import Substrate
from metabolon.metabolism.substrates import get_receptor_catalog
from metabolon.metabolism.variants import Genome

SUBSTRATES = get_receptor_catalog

__all__ = [
    "SUBSTRATES",
    "Emotion",
    "GateResult",
    "Genome",
    "ImmuneRequest",
    "SensorySystem",
    "Stimulus",
    "Substrate",
    "compute_emotion",
    "immune_response",
    "reflex_check",
]
