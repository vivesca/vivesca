#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = ["anthropic"]
# ///
"""Headless garden post pipeline. Reads queue, generates, judges, publishes."""

import json
import re
import subprocess
from pathlib import Path

import anthropic

_LLM_MODELS_PATH = Path.home() / ".config" / "llm-models.json"


def _model_id(key: str) -> str:
    """Resolve a registry key to its model ID string, falling back to the key itself."""
    try:
        registry = json.loads(_LLM_MODELS_PATH.read_text())
        return registry[key]["model"]
    except Exception:
        return key


QUEUE = Path.home() / "notes/Writing/Blog/Queue.md"
STYLE_GUIDE = Path.home() / "code/blog/CLAUDE.md"

JUDGE_PROMPT = """Evaluate this garden post against these criteria:
- clear_thesis (HIGH): Is there one clear main point?
- evidence (HIGH): Are claims supported with examples or reasoning?
- hook (MED): Does the opening draw the reader in?
- conclusion (MED): Does it end with a clear takeaway?
- concise (LOW): Is every paragraph earning its place?

Reply with exactly: PASS or FAIL, then one sentence explaining the verdict."""

GENERATE_PROMPT = """Write a garden post for terryli.hm.

Topic: {topic}

Style rules (from blog/CLAUDE.md):
{style_excerpt}

Requirements:
- 150-300 words
- Pure prose — no headers, no bullet points
- Open with something that makes the reader pause
- One clear thesis, earned through the writing
- End with a takeaway, not a summary

Return ONLY the post body. No title, no frontmatter."""


def notify(msg: str) -> None:
    from metabolon.organelles.secretory_vesicle import secrete_text

    secrete_text(msg, html=False, label="garden")


def get_next_topic() -> tuple[int, str] | None:
    lines = QUEUE.read_text().splitlines()
    for i, line in enumerate(lines):
        if line.startswith("- [ ] "):
            return i, line[6:].strip()
    return None


def mark_done(line_num: int) -> None:
    lines = QUEUE.read_text().splitlines()
    lines[line_num] = lines[line_num].replace("- [ ] ", "- [x] ", 1)
    QUEUE.write_text("\n".join(lines) + "\n")


def generate(topic: str, style_excerpt: str, extra: str = "") -> str:
    client = anthropic.Anthropic()
    prompt = GENERATE_PROMPT.format(topic=topic + extra, style_excerpt=style_excerpt)
    msg = client.messages.create(
        model=_model_id("sonnet"),
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text.strip()


def judge(post: str) -> tuple[bool, str]:
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=_model_id("haiku"),
        max_tokens=100,
        messages=[{"role": "user", "content": f"{JUDGE_PROMPT}\n\nPost:\n{post}"}],
    )
    verdict = msg.content[0].text.strip()
    return verdict.upper().startswith("PASS"), verdict


def publish(title: str, body: str) -> str:
    from metabolon.organelles.golgi import new, publish as garden_publish

    slug, post_path = new(title)
    content = post_path.read_text()
    post_path.write_text(content.rstrip() + "\n\n" + body + "\n")
    garden_publish(slug, force=True)
    return slug


def main() -> None:
    entry = get_next_topic()
    if not entry:
        notify("Garden queue empty — nothing to generate")
        return

    line_num, topic = entry
    style_excerpt = STYLE_GUIDE.read_text()[:2000]

    post = generate(topic, style_excerpt)
    passed, verdict = judge(post)

    if not passed:
        post = generate(
            topic, style_excerpt, f"\n\nPrevious attempt failed: {verdict}. Fix the issues."
        )
        passed, verdict = judge(post)

    mark_done(line_num)

    if passed:
        title = topic.split(" — ")[0][:60]
        try:
            slug = publish(title, post)
            notify(f"Published: {title} → terryli.hm/posts/{slug}")
        except Exception as e:
            notify(f"Garden publish failed: {e}")
    else:
        notify(f"Garden post skipped (judge failed twice): {topic[:50]}")


if __name__ == "__main__":
    main()
