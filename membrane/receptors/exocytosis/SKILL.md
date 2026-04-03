---
name: exocytosis
description: >
  Publish to terryli.hm garden. Secretome (chromatin) -> Astro -> deploy.
  CLI: ~/germline/effectors/publish. Posts: ~/epigenome/chromatin/secretome/.
triggers:
  - "garden post"
  - "new post"
  - "publish post"
  - "blog post"
  - "exocytosis"
---

# exocytosis — Garden Publishing

Manages posts in `~/epigenome/chromatin/secretome/`. `publish push` syncs to
Astro repo (`~/code/terryli-hm/`), commits, and pushes to deploy.

## Voice & Content Tiers

- **Garden posts** (terryli.hm): AI can expand from sparks in real conversations. Zero-touch publishing OK — ideas are Terry's, prose is logistics.
- **Front-stage** (LinkedIn, outreach, interviews): AI drafts from garden posts or live conversation, Terry reviews and edits for voice before shipping.
- **Content pipeline:** Garden is the backlog. When ready for LinkedIn, scan `~/notes/terryli.hm.md` index and pick what fits the moment.

## Commands

```bash
# Create a new draft post (opens in $EDITOR)
sarcio new "Title of Post"

# List all posts with date, draft status, word count
sarcio list

# Publish a draft (flips draft: true → false)
sarcio publish <slug>

# Publish and sync immediately (bypasses 5-min LaunchAgent)
sarcio publish <slug> --push

# Sync vault → blog → push now (bypasses 5-min LaunchAgent)
sarcio push

# Revise a published post (bumps modDatetime, sets revisionNote)
sarcio revise <slug> --note "What changed and why"

# Open a post in $EDITOR
sarcio open <slug>

# Regenerate ~/notes/terryli.hm.md vault index
sarcio index
```

## Workflow

**New post from session insight:**
1. `sarcio new "Title"` — scaffolds with correct frontmatter
2. Write the post
3. **Judge gate — skip for standard garden posts.** Judge (article criteria) has never failed a garden post (always scores 88-94). Only run judge when: factual claims need verification, sensitive topic, or front-stage content. For normal opinion/reflection posts → publish directly.
4. **Publish immediately** (`sarcio publish <slug> --push`), live instantly
5. Or omit `--push` to let the LaunchAgent pick it up within 5 min

**Brainstorming for garden posts:** Skip the full brainstorm skill. One angle-check question max ("who's the reader?" or "what's the hook?"), then draft. Garden posts are low-risk — judge is the gate.

**Revise an existing post:**
```bash
sarcio revise autonomous-vs-monitored-agents --note "Added Karpathy follow-up example"
```
Shows revised date + note on the post automatically.

**Find the slug:**
```bash
sarcio list | grep <keyword>
```

## Auto-Publish Protocol

When a publishable insight surfaces in a session:
1. Draft the post (session context as material)
2. Run judge (`article` criteria)
3. **Pass** → `sarcio publish <slug>`
4. **Needs work** → one revision pass → judge again
5. **Still failing** → `echo "Garden post failed judge: <title>" | deltos "garden"` — do NOT publish silently

**Insight detection — draft autonomously when ALL of:**
- A non-obvious observation emerged naturally (not manufactured)
- Clear one-sentence thesis
- In Terry's lane: AI, work, tools, personal systems, consulting
- No factual claims needing verification
- No real names, companies, or time-sensitive content that could embarrass

When in doubt: draft and let judge decide. Judge is the gate, not the intent check.

## Gotchas

- **`sarcio new` scaffolds with `draft: false`** — so `sarcio publish <slug>` immediately returns "Already published". This is correct behaviour (new posts go live immediately). If you need to draft privately first, manually set `draft: true` in frontmatter after `sarcio new`. If the post already has `draft: false` and you want to update content, use Write tool to overwrite the file directly — `sarcio publish` is a no-op on already-published posts.
- `serde_yaml` is deprecated upstream but works fine — may need migration eventually
- Frontmatter revision uses string matching, not full YAML round-trip — keys must be consistently formatted (no extra whitespace)
- Slug derived from title: lowercase, spaces → `-`, non-alphanumeric stripped
- `sarcio index` regenerates `~/notes/terryli.hm.md` — also runs automatically on every blog sync
- **Quality degrades after ~5 posts per session.** Posts 1-5 tend to be genuine sparks; posts 6+ become thinner and forced. Cap at 5 per session. If the well is running dry, stop — don't manufacture.

## Files

- Binary: `~/.cargo/bin/sarcio`
- Source: `~/code/sarcio/`
- Posts: `~/notes/Writing/Blog/Published/`
- Index: `~/notes/terryli.hm.md`
