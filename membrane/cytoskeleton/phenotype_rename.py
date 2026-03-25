#!/usr/bin/env python3
"""Background worker for tmux window renaming — deterministic (glycolysis).

Extracts content words from the prompt, no LLM needed.
Called by synapse.py as: python3 phenotype_rename.py <prompt> <window_id>
"""

import re
import subprocess
import sys

STOP = frozenset(
    [
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "can",
        "shall",
        "to",
        "of",
        "in",
        "for",
        "on",
        "with",
        "at",
        "by",
        "from",
        "as",
        "into",
        "about",
        "between",
        "through",
        "after",
        "before",
        "during",
        "without",
        "this",
        "that",
        "these",
        "those",
        "it",
        "its",
        "i",
        "me",
        "my",
        "we",
        "our",
        "you",
        "your",
        "he",
        "she",
        "they",
        "them",
        "what",
        "which",
        "who",
        "how",
        "when",
        "where",
        "why",
        "and",
        "or",
        "but",
        "not",
        "no",
        "if",
        "then",
        "so",
        "just",
        "also",
        "more",
        "some",
        "any",
        "all",
        "each",
        "every",
        "up",
        "out",
        "now",
        "new",
        "get",
        "make",
        "like",
        "use",
        "check",
        "let",
        "lets",
        "please",
        "hi",
        "hey",
        "hello",
        "can",
        "help",
        "want",
        "need",
        "think",
        "know",
        "see",
        "look",
        "find",
        "try",
        "run",
        "go",
        "set",
        "put",
        "add",
    ]
)

# Slash commands map to their name directly
SLASH_RE = re.compile(r"^/(\w[\w-]*)")

prompt = sys.argv[1] if len(sys.argv) > 1 else ""
window_id = sys.argv[2] if len(sys.argv) > 2 else ""

if not prompt:
    sys.exit(0)

try:
    # Slash command → use command name
    m = SLASH_RE.match(prompt.strip())
    if m:
        label = m.group(1)[:20]
    else:
        # Extract content words, take first 3
        words = re.findall(r"[a-z][a-z0-9]+", prompt.lower())
        content = [w for w in words if w not in STOP and len(w) > 2][:3]
        label = "-".join(content)[:20] if content else ""

    if label:
        target = ["-t", window_id] if window_id else []
        subprocess.run(["tmux", "rename-window"] + target + [label], timeout=2)
except Exception:
    pass
