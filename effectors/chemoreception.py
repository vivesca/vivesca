#!/usr/bin/env python3
"""
UserPromptSubmit hook: keyword-based retrieval over ~/epigenome/chromatin/Reference/.
Scans markdown files for relevance to the user prompt, injects top matches
as context. Lightweight — no embeddings, just TF-IDF-style scoring.
"""

import json
import math
import re
import sys
import time
from collections import Counter
from pathlib import Path

REFERENCE_DIR = Path.home() / "code" / "epigenome" / "chromatin" / "Reference"
DEBOUNCE_FILE = Path.home() / ".claude" / "retrieval-hook-state.json"
DEBOUNCE_SECONDS = 300  # 5 min debounce
TOP_K = 3
MIN_SCORE = 1.5  # minimum relevance score to inject

# Skip these — too noisy or meta
SKIP_PATTERNS = {"knowledge-structure.md", ".obsidian", ".DS_Store"}

# Common stop words to filter from queries
STOP_WORDS = {
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
}


def tokenize(text: str) -> list[str]:
    """Extract meaningful tokens from text."""
    words = re.findall(r"[a-z][a-z0-9_-]+", text.lower())
    return [w for w in words if w not in STOP_WORDS and len(w) > 2]


def should_debounce() -> bool:
    """Check if we ran recently enough to skip."""
    try:
        if DEBOUNCE_FILE.exists():
            last = float(DEBOUNCE_FILE.read_text().strip())
            if time.time() - last < DEBOUNCE_SECONDS:
                return True
    except (ValueError, OSError):
        pass
    return False


def update_debounce():
    """Record that we just ran."""
    try:
        DEBOUNCE_FILE.parent.mkdir(parents=True, exist_ok=True)
        DEBOUNCE_FILE.write_text(str(time.time()))
    except OSError:
        pass


def collect_documents() -> dict[str, str]:
    """Collect all markdown files under Reference/ with their content."""
    docs = {}
    if not REFERENCE_DIR.exists():
        return docs

    for md_file in REFERENCE_DIR.rglob("*.md"):
        rel = str(md_file.relative_to(REFERENCE_DIR))
        if any(skip in rel for skip in SKIP_PATTERNS):
            continue
        try:
            content = md_file.read_text(errors="replace")
            if len(content) > 50:  # skip near-empty files
                docs[rel] = content
        except OSError:
            continue

    return docs


def score_documents(query_tokens: list[str], docs: dict[str, str]) -> list[tuple[str, float]]:
    """Score documents against query using TF-IDF-style relevance."""
    if not query_tokens or not docs:
        return []

    query_counts = Counter(query_tokens)
    n_docs = len(docs)

    # Build document frequency for IDF
    doc_freq: Counter = Counter()
    doc_token_cache: dict[str, Counter] = {}
    for path, content in docs.items():
        # Include filename tokens (weighted higher via repetition)
        name_tokens = tokenize(Path(path).stem.replace("-", " ").replace("_", " "))
        content_tokens = tokenize(content[:3000])  # cap content scan for speed
        all_tokens = content_tokens + name_tokens * 3  # boost filename matches
        token_counts = Counter(all_tokens)
        doc_token_cache[path] = token_counts
        doc_freq.update(token_counts.keys())

    # Score each document
    scored = []
    for path, token_counts in doc_token_cache.items():
        score = 0.0
        for term, qf in query_counts.items():
            tf = token_counts.get(term, 0)
            if tf == 0:
                continue
            df = doc_freq.get(term, 1)
            idf = math.log(n_docs / df) + 1
            score += (1 + math.log(tf)) * idf * qf
        if score > 0:
            scored.append((path, score))

    scored.sort(key=lambda x: -x[1])
    return scored[:TOP_K]


def format_suggestions(scored: list[tuple[str, float]]) -> str:
    """Format top matches as context injection."""
    lines = []
    for path, score in scored:
        full_path = REFERENCE_DIR / path
        # Extract first heading and first ~200 chars of content
        try:
            content = full_path.read_text(errors="replace")
        except OSError:
            continue

        # Find first heading
        heading = ""
        for line in content.splitlines():
            if line.startswith("#"):
                heading = line.lstrip("#").strip()
                break

        # Extract a useful snippet (skip frontmatter)
        body = content
        if body.startswith("---"):
            end = body.find("---", 3)
            if end > 0:
                body = body[end + 3 :]
        snippet = " ".join(body.split()[:40])

        display = heading or Path(path).stem
        lines.append(f"- [[{Path(path).stem}]] ({path}): {display}")
        if snippet:
            lines.append(f"  {snippet}...")

    return "\n".join(lines)


def main():
    # Read hook input from stdin
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        return

    prompt = hook_input.get("prompt", "")
    if not prompt or len(prompt) < 10:
        return

    if should_debounce():
        return

    query_tokens = tokenize(prompt)
    if len(query_tokens) < 2:
        return

    docs = collect_documents()
    if not docs:
        return

    scored = score_documents(query_tokens, docs)
    # Filter by minimum score
    scored = [(p, s) for p, s in scored if s >= MIN_SCORE]
    if not scored:
        return

    update_debounce()

    suggestions = format_suggestions(scored)
    output = {
        "result": "continue",
        "metadata": {
            "system-prompt-suffix": (
                f"<reference-suggestions>\n"
                f"Potentially relevant Reference docs (retrieval-hook, keyword-match):\n"
                f"{suggestions}\n"
                f"Read with Read tool if relevant to the current task.\n"
                f"</reference-suggestions>"
            )
        },
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
