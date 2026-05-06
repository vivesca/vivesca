"""Skip benchmark scaffolds during normal pytest collection.

Files under harness_experiment/<task>/ are scaffolds where test_*.py is the
spec and an agent (CC, Codex, OpenCode, etc.) is expected to PRODUCE the
implementation (e.g. stack.py). They are not regular CI tests.

Run explicitly with `pytest assays/harness_experiment/<task>/` (this
conftest only blocks recursive collection from above).
"""

from __future__ import annotations

collect_ignore_glob = ["task*"]
