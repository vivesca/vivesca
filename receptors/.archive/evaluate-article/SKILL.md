---
name: evaluate-article
description: Evaluate articles for noteworthiness and save to vault with commentary. This skill should be used when the user shares a URL to an article, blog post, or essay. Triggers on article URLs, "read this", "what do you think of this article", or requests to evaluate/note content.
---

# Evaluate Article

Read articles shared by user, evaluate whether they're worth saving to the vault, and if so, create a note with key ideas and commentary. Acts as a reader/filter — user shares links without reading them first.

## Workflow

1. Fetch the URL with WebFetch (prompt: "Extract the full article content including title, author, date, and main body")
2. Evaluate against Worth Noting Criteria
3. If SKIP → brief dismissal in chat (2-3 lines max), done
4. If NOTE → draft note for user's vault Articles folder
5. **Interlink:** Grep vault for related notes (key concepts, themes). Add `## Related` section with 2-5 wikilinks if meaningful connections exist
6. Save note and confirm to user

**Optional:** For high-stakes notes (interview prep, writing references), add `--review` flag to run `/judge` with `article` criteria. Skip for daily triage.

## Worth Noting Criteria

| NOTE (save to vault) | SKIP (dismiss in chat) |
|----------------------|------------------------|
| Novel ideas or frameworks | Marketing fluff, product announcements |
| Relevant to user's work/interests | Paywalled with no real content |
| Contrarian or well-argued takes | Beginner explainers user already knows |
| Actionable insights or changes thinking | News without insight |
| Technical depth worth referencing later | Listicles, shallow overviews |

**Default behavior:** If user shared it, assume mild interest. Lean toward NOTE unless clearly low-value.

## Note Format

**Template:**
```markdown
---
source: [URL]
author: [Author name]
date_read: [Today's date]
tags: []
---

## Key Ideas

- [3-5 bullet points, dense, no fluff]

## My Take

[2-4 sentences: Why this matters, connections to user's context, critique if warranted]
```

**Tagging:** Add relevant tags that strongly apply to the content.

**Linking:** Add `[[wikilinks]]` to existing notes when obvious connections exist. Don't force connections.

## Skip Output

When skipping, output format:

> **Skip** — [One-line reason]
>
> TL;DR: [2-3 sentence gist if there's anything worth knowing]

Example:
> **Skip** — Product announcement for a new vector DB, no novel insights
>
> TL;DR: Pinecone launched serverless tier. Cheaper for small workloads but same core functionality.

## Edge Cases

**Paywall/login required:** Report clearly, offer to skip or wait for user to paste content

**PDF or non-HTML:** Use WebFetch; if it fails, ask user to paste the text

**Very long article:** Still create note, but be more selective with Key Ideas (max 5 bullets)

**Article already noted:** Check vault first; if exists, inform user and offer to update or skip
