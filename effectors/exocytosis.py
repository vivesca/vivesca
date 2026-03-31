#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Headless garden post pipeline. Reads queue, generates, judges, publishes."""

import argparse
import configparser
from pathlib import Path

from metabolon.symbiont import transduce

_CONF_PATH = Path(__file__).parent / "exocytosis.conf"
_conf = configparser.ConfigParser()
_conf.read(_CONF_PATH)

_JUDGE_RETRY_COUNT = _conf.getint("judge", "judge_retry_count", fallback=1)


QUEUE = Path.home() / "epigenome/chromatin/Writing/Blog/Queue.md"
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
    prompt = GENERATE_PROMPT.format(topic=topic + extra, style_excerpt=style_excerpt)
    return transduce("goose", prompt, timeout=120)


def judge(post: str) -> tuple[bool, str]:
    verdict = transduce("glm", f"{JUDGE_PROMPT}\n\nPost:\n{post}", timeout=60)
    return verdict.upper().startswith("PASS"), verdict


def publish(title: str, body: str) -> str:
    from metabolon.organelles.golgi import new
    from metabolon.organelles.golgi import publish as garden_publish

    slug, post_path = new(title)
    content = post_path.read_text()
    post_path.write_text(content.rstrip() + "\n\n" + body + "\n")
    garden_publish(slug, force=True)
    return slug


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    entry = get_next_topic()
    if not entry:
        notify("Garden queue empty — nothing to generate")
        return

    line_num, topic = entry
    style_excerpt = STYLE_GUIDE.read_text()[:2000]

    post = generate(topic, style_excerpt)
    passed, verdict = judge(post)

    for _ in range(_JUDGE_RETRY_COUNT):
        if passed:
            break
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
