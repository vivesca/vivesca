"""vivesca metabolism — self-evolving tool descriptions.

One mechanism, any substrate. The SUBSTRATES registry maps target names
to Substrate implementations. New targets register by adding to it.
"""

from metabolon.metabolism.substrates import receptor_catalog

SUBSTRATES = receptor_catalog

__all__ = [
    "SUBSTRATES",
]
