#!/usr/bin/env python3
"""
UserPromptSubmit hook — detect URLs and keywords and remind about domain-specific skills.

Prevents ad-hoc WebFetch when a skill exists for the domain.
Prevents free-form experiments when peira should be used.
"""

from __future__ import annotations

import json
import re
import sys

# domain substring → skill reminder
# Extend this map as new domain-specific skills are created.
# Order matters: first match wins per URL, so put specific paths before general domains.
DOMAIN_SKILL_MAP = {
    # LinkedIn
    "linkedin.com/posts": "LinkedIn post → use `/agoras` skill (agent-browser fetch, author research, voice rules)",
    "linkedin.com/feed/update": "LinkedIn post → use `/agoras` skill (agent-browser fetch, author research, voice rules)",
    "linkedin.com/in/terrylihm": "Own LinkedIn profile → use `linkedin-profile` skill (Featured, About, Headline, announcements)",
    "linkedin.com/in/": "LinkedIn profile → use `linkedin-research` skill (agent-browser extraction)",
    "linkedin.com/jobs": "LinkedIn job → use `/adhesion` skill",
    # Video platforms
    "youtube.com/watch": "YouTube URL → use `video-digest` skill (transcript + structured digest)",
    "youtu.be/": "YouTube URL → use `video-digest` skill (transcript + structured digest)",
    "bilibili.com/video": "Bilibili URL → use `video-digest` skill (transcript + structured digest)",
    "xiaoyuzhou.fm": "Xiaoyuzhou URL → use `video-digest` skill (podcast transcript + digest)",
    # X/Twitter
    "x.com/": "X URL → use `auceps <url>` (smart bird wrapper — auto-routes, `--vault` for Obsidian, `--lustro` for lustro JSON)",
    "twitter.com/": "Twitter URL → use `auceps <url>` (smart bird wrapper — auto-routes, `--vault` for Obsidian, `--lustro` for lustro JSON)",
    # Taobao/Tmall (WebFetch can't access — login-gated)
    "e.tb.cn": "Taobao link → use `agent-browser --profile` (WebFetch blocked, login required)",
    "taobao.com": "Taobao → use `agent-browser --profile` (WebFetch blocked, login required)",
    "tmall.com": "Tmall → use `agent-browser --profile` (WebFetch blocked, login required)",
}


# keyword phrase (lowercase) → skill reminder
# Checked against full prompt text, case-insensitive.
KEYWORD_SKILL_MAP = [
    (
        r"\blaunch exp\b",
        "Experiment → invoke `peira` skill first (define metric + baseline + budget before running anything)",
    ),
    (
        r"\brun exp(eriment)?\b",
        "Experiment → invoke `peira` skill first (define metric + baseline + budget before running anything)",
    ),
    (
        r"\bcompare .{3,40} vs\b",
        "Comparison → invoke `peira` skill first (define metric + baseline + budget before running anything)",
    ),
    (
        r"\bbenchmark\b",
        "Benchmark → invoke `peira` skill first (define metric + baseline + budget before running anything)",
    ),
]


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return

    prompt = data.get("prompt", "")
    if not prompt:
        return

    reminders = []
    seen = set()

    # Keyword matching (case-insensitive)
    prompt_lower = prompt.lower()
    for pattern, reminder in KEYWORD_SKILL_MAP:
        if re.search(pattern, prompt_lower) and reminder not in seen:
            reminders.append(reminder)
            seen.add(reminder)

    # URL matching
    urls = re.findall(r'https?://[^\s<>"\']+', prompt)
    for url in urls:
        for domain_pattern, reminder in DOMAIN_SKILL_MAP.items():
            if domain_pattern in url and reminder not in seen:
                reminders.append(reminder)
                seen.add(reminder)
                break

    if reminders:
        lines = "\n".join(f"- {r}" for r in reminders)
        print(f"Skill routing:\n{lines}\nUse the indicated skill — do not proceed ad-hoc.")


if __name__ == "__main__":
    main()
