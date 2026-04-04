
"""Overnight metabolism pipeline: metabolise → draft → publish.

An actus pipeline — each product is the next substrate.
Runs autonomously. Human reviews products, not process.
"""


import json
import os
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

from metabolon.locus import blog_published

PUBLISHED = blog_published
LOGDIR = Path.home() / "tmp"
VIVESCA = Path.home() / "code" / "vivesca"

DRAFT_PROMPT = """You are writing a spore for terryli.hm. Voice: clear, direct, slightly wry. Short paragraphs. Prose, not bullets for the main argument. 800-1200 words. End with a concrete takeaway.

This post is part of a series following "The Missing Metabolism", "Taste Is the Metabolism", "Everything Is Energy", and "The Constitution Eats Itself" — all about vivesca, an information metabolism engine.

Here is a crystallised insight from a cross-model metabolism session:

{result}

Write the complete spore. Include frontmatter:
---
title: "{title}"
description: "one-line description"
pubDatetime: {timestamp}
draft: false
tags: [ai, agents, design, vivesca]
---
"""


def _acquire_catalyst():
    """Import and return the shared symbiont module — the reaction catalyst."""

    from metabolon import symbiont

    return symbiont


def _sterile_env() -> dict:
    """Return a clean environment — no CLAUDECODE contamination."""
    return {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}


def metabolise(
    seed: str, slug: str, expander: str = "gemini", pusher: str = "claude"
) -> str | None:
    """Reaction 1: seed → crystallised insight."""
    outfile = LOGDIR / f"metabolised-{slug}.md"
    try:
        result = subprocess.run(
            [
                "uv",
                "run",
                "vivesca-dev",
                "metabolise",
                seed,
                "--expander",
                expander,
                "--pusher",
                pusher,
                "-o",
                str(outfile),
            ],
            capture_output=True,
            text=True,
            timeout=600,
            cwd=str(VIVESCA),
            env=_sterile_env(),
        )
        if outfile.exists():
            return outfile.read_text().strip()
        return result.stdout.strip() if result.stdout else None
    except Exception as e:
        print(f"  metabolise error: {e}")
        return None


def compose_post(result: str, title: str, slug: str, model: str = "glm") -> Path | None:
    """Reaction 2: crystallised insight → spore."""
    symbiont = _acquire_catalyst()
    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    prompt = DRAFT_PROMPT.format(result=result, title=title, timestamp=timestamp)
    try:
        content = symbiont.transduce(model, prompt, timeout=120)
        post_path = PUBLISHED / f"{slug}.md"
        post_path.write_text(content)
        return post_path
    except Exception as e:
        print(f"  compose_post error: {e}")
        return None


def publish(slug: str) -> bool:
    """Reaction 3: spore → live on terryli.hm."""
    try:
        result = subprocess.run(
            ["publish", "publish", slug, "--push"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return result.returncode == 0
    except Exception as e:
        print(f"  publish error: {e}")
        return False


def metabolize_pipeline(
    seeds: list[dict], expander: str = "gemini", pusher: str = "claude"
) -> dict:
    """Run the full pipeline on a list of seeds.

    Each seed is a dict with 'seed', 'slug', 'title'.
    Returns summary dict with 'published', 'failed', 'no_convergence' lists.
    """
    results = {"published": [], "failed": [], "no_convergence": []}

    for item in seeds:
        slug = item["slug"]
        title = item["title"]
        print(f"[{slug}]")

        crystal = metabolise(item["seed"], slug, expander, pusher)
        if not crystal:
            print("  ✗ no convergence")
            results["no_convergence"].append(slug)
            continue

        post_path = compose_post(crystal, title, slug)
        if not post_path:
            print("  ✗ compose_post failed")
            results["failed"].append(slug)
            continue

        if publish(slug):
            print("  ✓ published")
            results["published"].append(slug)
        else:
            print("  ✗ publish failed")
            results["failed"].append(slug)

        time.sleep(5)

    summary_path = LOGDIR / "overnight-metabolise-summary.json"
    summary_path.write_text(json.dumps(results, indent=2))
    print(
        f"\nSummary: {len(results['published'])} published, "
        f"{len(results['failed'])} failed, "
        f"{len(results['no_convergence'])} no convergence"
    )
    return results
