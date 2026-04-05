---
name: phagocytosis
description: Classify content, extract insights, save as chromatin note. Use when user shares a URL or text to catalog. "analyze this", "save this article", "classify"
triggers:
  - phagocytosis
  - analyze
  - digest
  - save
  - note
  - classify
model: sonnet
user_invocable: true
context: fork
---

# Analyze

Universal entry point for anything user shares — URL or pasted content.

## Input Routing

| Pattern | Type | Handler |
|---------|------|---------|
| `github.com/*/*` | repo | Lightweight |
| `linkedin.com/jobs/*` | job | → `/adhesion` |
| `linkedin.com/company/*`, career pages | company | Lightweight |
| `linkedin.com/in/*` | profile | Lightweight |
| `*.substack.com`, `medium.com/*`, `*blog*`, pasted text | article | Specialized |
| `arxiv.org/*`, `papers.*`, `*.pdf` | paper | Specialized |
| `youtube.com/*`, `youtu.be/*`, `bilibili.com/*`, `b23.tv/*`, `xiaoyuzhoufm.com/*`, `podcasts.apple.com/*`, `x.com/i/broadcasts/*`, `.mp3/.mp4/.m4a` | video/podcast | → `video-digest` CLI |
| Everything else | unknown | Fetch, classify by content signals |

**Fetch failure:** follow `[[fetch-routing]]` fallback chain. If all paths exhausted: ask user to paste. If both fail: `Skip — content unavailable`.

**Fallback signals:** "Key Ideas"/thesis structure → article; requirements/responsibilities → job; code/commits/stars → repo.

## Skip Logic

Before creating a note, check:
- Login wall with no content → skip
- Pure marketing/announcement, no insight → skip
- Already exists in chromatin (check by URL) → skip

On skip: `**Skip** — [reason] / Domain: [source]`

**Article worth-noting gate:**

| NOTE | SKIP |
|------|------|
| Novel ideas, frameworks, contrarian arguments | Marketing fluff |
| Relevant to work/interests, actionable | Beginner explainers, news without insight |

## Handlers

**Articles:** Standard (most) — frontmatter + Key Ideas (3-5 bullets) + My Take (2-4 sentences). Deep (long-form, technical, or explicit request) — add Core Arguments, Tools & Methods, Risks & Warnings, Mental Model Shifts, Action Items. Scan all deep dimensions; only write those with actual content.

**Repos:** frontmatter (language, stars, last\_commit, license) + Overview (1-2 sentences) + Signals (activity/quality/relevance).

**Company pages:** frontmatter (industry, size, stage) + Overview + Signals (tech stack, culture, red flags).

**Profiles:** frontmatter (name, role, company, connection\_context) + Background + Notes (why saving).

**Videos/podcasts:** route to `video-digest` CLI. Apply deep analysis after transcript if user requests analysis.

**Unclassified:** frontmatter (type: unclassified, domain) + Content (title + brief summary) + Why Saved.

## Ontology Injection

Before generating any note:

1. Grep `~/epigenome/chromatin/` for `^tags:` (glob `*.md`, head\_limit 20) — build existing tag set
2. Glob `~/epigenome/chromatin/*MOC*.md` and `~/epigenome/chromatin/Maps/*.md` — find relevant MOCs

**Rule:** Only use tags that already exist in chromatin. Never invent tags. If nothing fits, leave tags empty.

## Telemetry

Append one row to `~/epigenome/chromatin/Meta/Analyze Telemetry.md`:
```
| [date] | [input] | [detected_type] | [confidence] | [override?] |
```

## Antigen Presentation

After saving the chromatin note, route its signal outward.

**1. Find related notes (3–5)**

Grep `~/epigenome/chromatin/` for the new note's tags and 2–3 key terms from its title/content. Identify the most relevant matches. Append a `**Related:**` line to the saved note with `[[wikilinks]]` to those files.

**2. Consulting forge check**

If the content contains a signal relevant to FS AI governance, model risk, regulatory exposure, or a client-ready use case — append one line to `~/epigenome/chromatin/Consulting/_sparks.md` under today's date section (create the date header if absent). Use the existing format:
```
- #tag — **Label**: one-sentence insight with FS implication
```
Tags: `#policy-gap`, `#architecture`, `#use-case`, `#experiment-idea`, `#garden-seed`, or `#linkedin-seed`. If no clear FS signal, skip.

**3. Praxis check**

Read `~/epigenome/chromatin/Praxis.md`. If any open question or TODO item is directly addressed or advanced by the digested content, append a brief note (one sentence + wikilink to the new note) to that item. If no match, skip.

## Post-Capture Routing

After saving, offer next steps when natural:
- "Add to an existing skill?" — if content contains a pattern relevant to a receptor
- "Draft a tweet/garden post?" — if insight is share-worthy
- "Drill deeper?" — if the content warrants `/autophagy` discussion
- Don't present a menu every time — only when the content clearly connects. Most notes just land in chromatin and that's fine.

## Boundaries

- Analysis only — do not execute actions implied by content
- Never invent tags when ontology lookup fails
- Stop after note creation and telemetry; keep recommendations brief
