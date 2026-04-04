"""Environment utilities — shared helpers for subprocess environment management.

Provides a single place for the CLAUDECODE-contamination guard so callers
don't each re-implement the same os.environ filter.
"""


import os

# Keys that must not leak into child processes (they confuse Claude Code
# into thinking the child IS Claude Code and applying wrong behaviours).
_DEFAULT_EXCLUDE: frozenset[str] = frozenset({"CLAUDECODE"})


def clean_env(*, exclude: set[str] | None = None) -> dict[str, str]:
    """Return a copy of the current environment with specified keys removed.

    By default removes CLAUDECODE to prevent contamination of child processes.
    Pass a custom ``exclude`` set to filter additional keys.

    Usage::

        from metabolon.morphology.env import clean_env
        subprocess.run(cmd, env=clean_env())
    """
    blocked = exclude if exclude is not None else _DEFAULT_EXCLUDE
    return {k: v for k, v in os.environ.items() if k not in blocked}
