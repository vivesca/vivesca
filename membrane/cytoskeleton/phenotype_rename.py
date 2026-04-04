#!/usr/bin/env python3
"""Background worker for tmux window renaming — deterministic (glycolysis).

Extracts content words from the prompt, no LLM needed.
Called by synapse.py as: python3 phenotype_rename.py <prompt> <window_id>
"""

from __future__ import annotations

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

# High-signal action verbs — kept as first token when leading the prompt
ACTIONS = frozenset(
    [
        "fix",
        "debug",
        "refactor",
        "deploy",
        "build",
        "test",
        "update",
        "migrate",
        "revert",
    ]
)

# Extensions that signal a file-path token
_EXT_RE = re.compile(
    r"\.(py|md|js|sh|ts|rs|go|rb|yaml|yml|json|toml|txt|cfg|ini|html|css|sql"
    r"|jsx|tsx)$",
    re.IGNORECASE,
)

# Slash commands map to their name directly
SLASH_RE = re.compile(r"^/(\w[\w-]*)")


def _split_token(word: str) -> list[str]:
    """Split a token on ``_`` and camelCase boundaries, return lowercase parts."""
    parts = re.sub(r"([a-z])([A-Z])", r"\1 \2", word).split("_")
    return [p.strip().lower() for p in parts if p.strip()]


def _extract_path_basenames(prompt: str) -> list[str]:
    """Return basename parts from tokens that look like file paths."""
    basenames: list[str] = []
    for tok in prompt.split():
        if "/" in tok or tok.startswith("~") or _EXT_RE.search(tok):
            parts = tok.replace("~", "").rstrip("/").split("/")
            basename = parts[-1] if parts else ""
            basename = _EXT_RE.sub("", basename)
            basenames.extend(_split_token(basename))
    return basenames


def _extract_quoted(prompt: str) -> list[str]:
    """Return words from the first quoted string in *prompt*."""
    m = re.search(r"""['"]([^'"]+)['"]""", prompt)
    if not m:
        return []
    return re.findall(r"[a-z][a-z0-9]*", m.group(1).lower())


def _tokenize(prompt: str) -> list[str]:
    """Tokenize with snake_case / camelCase splitting, lowercase."""
    expanded = re.sub(r"([a-z])([A-Z])", r"\1 \2", prompt)
    expanded = expanded.replace("_", " ")
    expanded = expanded.lower()
    expanded = re.sub(r"[^a-z0-9]+", " ", expanded)
    return expanded.split()


def _content_words(words: list[str]) -> list[str]:
    """Filter out stopwords and short words."""
    return [w for w in words if w not in STOP and len(w) > 2]


def _first_action(words: list[str]) -> str | None:
    """Return the first word if it is an action verb, else *None*."""
    for w in words:
        if w in ACTIONS:
            return w
        if w not in STOP and len(w) > 2:
            break
    return None


def _build_label(prompt: str) -> str:
    prompt = prompt.strip()
    if not prompt:
        return ""

    # Slash command → use command name
    m = SLASH_RE.match(prompt)
    if m:
        return m.group(1)[:20]

    # --- Priority 1: quoted strings ---
    quoted_words = _extract_quoted(prompt)
    if quoted_words:
        content = _content_words(quoted_words)[:3]
        if content:
            return "-".join(content)[:20]

    # Tokenize full prompt for action-verb detection and general fallback
    all_words = _tokenize(prompt)
    action = _first_action(all_words)

    # --- Priority 2: file-path basenames ---
    path_names = _extract_path_basenames(prompt)
    if path_names:
        path_content = _content_words(path_names)
        if not path_content:
            path_content = [w for w in path_names if len(w) > 2]
        if path_content:
            tokens: list[str] = []
            if action:
                tokens.append(action)
            tokens.extend(path_content[: 3 - len(tokens)])
            return "-".join(tokens)[:20]

    # --- Priority 3: action verb + content words ---
    content = _content_words(all_words)
    if content:
        return "-".join(content[:3])[:20]

    return ""


prompt = sys.argv[1] if len(sys.argv) > 1 else ""
window_id = sys.argv[2] if len(sys.argv) > 2 else ""

if not prompt:
    sys.exit(0)

try:
    label = _build_label(prompt)
    if label:
        target = ["-t", window_id] if window_id else []
        subprocess.run(["tmux", "rename-window", *target, label], timeout=2)
except Exception:
    pass
