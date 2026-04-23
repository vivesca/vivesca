---
name: exocytosis
description: >
  Publish to terryli.hm garden. Secretome -> Astro -> deploy.
  "garden post", "new post", "publish post", "blog post"
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

- **Garden posts** (terryli.hm): AI can expand from sparks in real conversations. Zero-touch publishing OK — ideas are Terry's, prose is logistics. **Pure prose only** — no headers, no bullets, no code blocks. Just paragraphs. See `feedback_garden_prose_only.md`.
- **Front-stage** (LinkedIn, outreach, interviews): AI drafts from garden posts or live conversation, Terry reviews and edits for voice before shipping.
- **Content pipeline:** Garden is the backlog. When ready for LinkedIn, scan `~/epigenome/chromatin/terryli.hm.md` index and pick what fits the moment.

## Commands

```bash
# Create a new draft post (opens in $EDITOR)
publish new "Title of Post"

# List all posts with date, draft status, word count
publish list

# Publish a draft (flips draft: true → false)
publish publish <slug>

# Publish and sync immediately (bypasses 5-min LaunchAgent)
publish publish <slug> --push

# Sync vault → blog → push now (bypasses 5-min LaunchAgent)
publish push

# Revise a published post (bumps modDatetime, sets revisionNote)
publish revise <slug> --note "What changed and why"

# Open a post in $EDITOR
publish open <slug>

# Regenerate ~/epigenome/chromatin/terryli.hm.md vault index
publish index
```

## Workflow

**New post from session insight:**
1. `publish new "Title"` — scaffolds with correct frontmatter
2. Write the post
3. **Censor gate** — run `/censor post` on the draft. Uses the garden anti-slop reject list (news-reporting, structural markdown, hedge words, no-position, tutorial-voice). If any reject-pattern fires, fix before publishing. If all checks pass, proceed.
4. **Publish immediately** (`publish publish <slug> --push`), live instantly
5. Or omit `--push` to let the LaunchAgent pick it up within 5 min

**Brainstorming for garden posts:** Skip the full brainstorm skill. One angle-check question max ("who's the reader?" or "what's the hook?"), then draft. Garden posts are low-risk — censor is the gate.

**Revise an existing post:**
```bash
publish revise autonomous-vs-monitored-agents --note "Added Karpathy follow-up example"
```
Shows revised date + note on the post automatically.

**Find the slug:**
```bash
publish list | grep <keyword>
```

## Auto-Publish Protocol (silent-pass verifier)

When a publishable insight surfaces in a session:
1. Draft the post (session context as material)
2. Run censor (`article` criteria) — **silent on pass.** Only surface censor output to Terry if it fails. Pass = publish immediately, no commentary.
3. **Pass** → `publish publish <slug>` (no "censor passed" message — just ship)
4. **Needs work** → one revision pass → censor again (show the issues this time)
5. **Still failing** → `echo "Garden post failed censor: <title>" | deltos "garden"` — do NOT publish silently

**Insight detection — draft autonomously when ALL of:**
- A non-obvious observation emerged naturally (not manufactured)
- Clear one-sentence thesis
- In Terry's lane: AI, work, tools, personal systems, consulting
- No factual claims needing verification
- No real names, companies, or time-sensitive content that could embarrass

When in doubt: draft and let censor decide. Censor is the gate, not the intent check.

## Gotchas

- **`publish new` scaffolds with `draft: false`** — so `publish publish <slug>` immediately returns "Already published". This is correct behaviour (new posts go live immediately). If you need to draft privately first, manually set `draft: true` in frontmatter after `publish new`. If the post already has `draft: false` and you want to update content, use Write tool to overwrite the file directly — `publish publish` is a no-op on already-published posts.
- `serde_yaml` is deprecated upstream but works fine — may need migration eventually
- Frontmatter revision uses string matching, not full YAML round-trip — keys must be consistently formatted (no extra whitespace)
- Slug derived from title: lowercase, spaces → `-`, non-alphanumeric stripped
- `publish index` regenerates `~/epigenome/chromatin/terryli.hm.md` — also runs automatically on every blog sync
- **Quality degrades after ~5 posts per session.** Posts 1-5 tend to be genuine sparks; posts 6+ become thinner and forced. Cap at 5 per session. If the well is running dry, stop — don't manufacture.

## Files

- Binary: `~/germline/effectors/publish` (Python, replaced Rust publish)
- Posts: `~/epigenome/chromatin/secretome/`
- Index: `~/epigenome/chromatin/terryli.hm.md`
