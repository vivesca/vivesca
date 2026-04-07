"""mtor — agent-first translation controller Temporal dispatch CLI."""

from __future__ import annotations

import os
from pathlib import Path

VERSION = "0.4.0"
TEMPORAL_HOST = os.environ.get("TEMPORAL_HOST", "ganglion:7233")
TASK_QUEUE = "translation-queue"
WORKFLOW_TYPE = "TranslationWorkflow"
COACHING_PATH = Path.home() / "epigenome/marks/feedback_ribosome_coaching.md"

LOG_TAIL_LINES = 30
RIBOSOME_OUTPUTS_DIR = "~/germline/loci/ribosome-outputs"

__version__ = VERSION
