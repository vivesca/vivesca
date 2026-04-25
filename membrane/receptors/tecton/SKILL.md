---
name: tecton
description: Reference for vault note structure — atomicity, interlinking, hub vs. detail, when to split, where notes live. Not user-invocable — consult when creating or refactoring vault notes.
user_invocable: false
triggers:
  - tecton
  - vault note
  - note structure
  - split note
  - interlink
  - atomic note
---

# Vault Note Structure

Reference skill for how to structure notes in `~/epigenome/chromatin/`. Covers atomicity, interlinking, placement, and anti-patterns. Consult before creating a new note or when a note feels too large.

## Core Principles

1. **One concern per note.** A note that covers two distinct topics should be two notes with a wikilink between them. Signal: if the title needs "and" or "/", it's probably two notes.

2. **Hub notes are workbenches, not just pointers.** Tracker notes (NOW.md, Capco Transition) hold live status. MOC-style hubs (e.g. an index of related notes) are *where connections get made*, not just listed — a place to challenge, reposition, and surface new relationships between notes. Hub grows? Split it.

3. **Link generously.** Dense `[[wikilinks]]` let Claude walk the graph for context. Sparse links = dead ends. Every note should have a **Related:** line.

4. **Facts age, rules don't.** Time-sensitive facts (dates, amounts, status) belong in vault notes, not CLAUDE.md. CLAUDE.md = rules. Vault = reference.

5. **Dated updates over status blocks.** Use `**Update (Feb X):**` headers in note bodies as the natural changelog — grep-surfaceable, no separate status section needed.

6. **Balance structure and chaos.** Too much structure = friction, ideas suffocate. Too much chaos = anxiety, thoughts are lost. The Goldilocks Zone: enough structure to navigate, enough openness to connect unexpectedly.

7. **Notes are living entities.** Not static files. They can change, split, merge, or resolve. A note written today may need splitting in three months — that's healthy, not failure.

8. **Atomicity is contextual, not dogma.** Don't force a note to be atomic — let it emerge. Two large notes in tension often *collide* into something more atomic. The signal to split is friction, not a rule.

9. **Wait for the squeeze to create hub notes.** Don't build MOC/hub notes prematurely. When a topic accumulates enough related notes that navigation feels hard, *that's* the moment to gather them. Early hub notes are empty shells.

## Note Types

| Type | Purpose | Example |
|------|---------|---------|
| **Reference** | Stable facts, numbers, technical detail | `AML Triage Model - Reference.md` |
| **Angles / Positioning** | How to talk about something, audience-specific framing | `AML Triage Model - Capco Angles.md` |
| **Tracker / Hub** | Live status, pointers to child notes | `Capco Transition.md`, `NOW.md` |
| **Profile** | Person or org — background, relationship, context | `Bertie Haskins Profile.md` |
| **Story / STAR** | Interview/narrative ready — what happened, impact | `The AML Alert Prioritisation Story.md` |
| **Daily** | Activity log — what happened this session | `2026-03-03.md` |
| **Conversation Card** | 30-second refresh before a meeting | `Responsible AI and MRM.md` |

## Where Notes Live

- `~/epigenome/chromatin/` — general vault root (project-agnostic, career, personal)
- `~/epigenome/chromatin/Capco/` — Capco-facing: positioning, client work, onboarding
- `~/epigenome/chromatin/Capco/Conversation Cards/` — pre-meeting refresh cards
- `~/epigenome/chromatin/Career/` — CV, interview prep, performance reviews
- `~/epigenome/chromatin/Daily/` — daily logs
- `~/epigenome/chromatin/Research/` — external research, clippings

**Rule:** If a note is about a CNCBI project operationally → vault root. If it's about how to use that project at Capco → `notes/Capco/`.

## When to Split a Note

Split when:
- Title needs "and" or "/"
- Note covers both facts and positioning (split into Reference + Angles)
- Note covers both status and detail (split into Hub + child)
- Note is >150 lines and growing

Don't split when:
- Note is actively being iterated (wait until stable)
- The two concerns are always read together (keep, add clear sections)

**When splitting: always interlink.** Split notes lose context at the seams — the protocol makes more sense because of the EF context; the research makes more sense because of the protocol. Counter this by: (1) dense **Related:** lines on every child note, (2) a "child notes" pointer in the hub body, (3) cross-references at the point where context would otherwise be lost (e.g. "For *why* this works, see [[Research note]]"). Split for navigation clarity; interlink so nothing becomes opaque in isolation.

## Relationship Builders (strongest to weakest)

| Tool | Strength | Use for |
|------|----------|---------|
| **Direct links** `[[note]]` | Strongest | Explicit connections between specific notes |
| **MOC / hub note** | High | Curating a topic area — non-exclusive, fluid |
| **Proximity within MOC** | Medium | Deliberate positioning of related notes together |
| **Tags** | Weak | Quick filtering; don't scale past ~50 notes per tag |
| **Folders** | Last resort | Private data, project staging, clearly-bounded collections |

**Don't fall for dogma.** "Links only" is as rigid as "folders only." Use the right tool. Folders aren't bad — they're just overused. Use them for: private notes (health, finances), temporary project staging (extract good ideas back to the main vault after), clearly-bounded note types (images, people, quotes).

## Interlinking Patterns

Every note should have a **Related:** line at the top (below frontmatter):
```
**Related:** [[Note A]] | [[Note B]] | [[Note C]]
```

When one note supersedes another's facts, add a pointer at the stale location rather than deleting:
```
(Feb 25–Feb 26 actuals: 34.33% — see [[AML Triage Model - Reference]])
```

Conversation Cards and positioning notes → link to the Reference note for facts. Never repeat numbers inline without linking to the source.

### Three-question checklist before saving any new note

Systematic gap: CC tends to link the *most obvious neighbour* (the file the note is directly about) but under-link primary sources and adjacent context. Before finalising any new note, answer all three:

1. **Primary sources?** Which verbatim artefacts (emails, Teams messages, meeting notes, deck transcriptions) does this note reason from? Link them.
2. **Stakeholders?** Which people does this note touch? Link their profile notes.
3. **Adjacent context?** Which other notes would a fresh session want to land on from this one? Link them.

If any of the three is empty, the note is likely under-linked. Pause and fill before committing. This applies to every new note: draft correspondence, project analyses, findings, profiles, even feedback marks.

## Anti-Patterns

- **God note:** One 1000+ line note covering multiple concerns (e.g. `Capco - Principal Consultant, AI Solution Lead.md`). Tolerate when actively iterating; split after stabilising.
- **Orphan note:** Created but not linked from anywhere — invisible to graph traversal. Always add to at least one Related: line.
- **Stale inline facts:** Numbers repeated in multiple notes without linking to a canonical source. One source of truth; others link.
- **CLAUDE.md fact creep:** Time-sensitive data (dates, amounts, status) written into CLAUDE.md instead of vault. Facts age; rules don't.

## Evidence Quality Tagging

For research-backed notes, annotate each claim with its evidence quality inline. Makes the note honest and prevents treating soft extrapolations as hard facts on re-read.

```
| Claim | Research | Confidence |
|-------|----------|------------|
| ... | Warneken & Tomasello (2014) — directly tested on toddlers | `[strong]` — replicated, specific to domain |
| ... | Vygotsky ZPD applied to cleanup routines | `[inferred]` — established theory, practitioner extrapolation |
```

Quality levels:
- `[strong]` — well-replicated, multiple studies, or consensus review papers
- `[moderate]` — single study or small sample; directionally reliable
- `[inferred]` — reasonable extrapolation from adjacent research; not directly tested

Add a one-paragraph "what the evidence is and isn't" section at the bottom distinguishing the well-supported mechanism from the inferred strategies. Example: [[Theo - Tidying Research]].

## Execution

Vault restructuring (splits, interlinks, renames) is reversible and local. When Terry confirms or asks to do it — **just do it, no mid-task confirmation pauses.** Don't ask "now?" or "want me to proceed?" — execute directly.

## Learnings

- **Capco vs. vault root split (Mar 2026):** Operational project notes (CNCBI work) → vault root. Capco-facing angles/positioning → `notes/Capco/`. Caught when `AML Triage Model - Reference.md` was initially placed in `notes/Capco/`.
- **Seed skills early.** Don't wait for three note-structure corrections — the pattern is clear after the first. (This skill exists because of that.)
- **Split but interlink (Mar 2026):** When splitting a hub note, the split is only half the work — dense cross-references at the seams are what keep the notes useful in isolation. See "When splitting: always interlink" above.
- **Evidence quality tagging (Mar 2026):** Research notes without confidence levels cause future misreading — inferred strategies look like strong findings. Tag inline, explain why. See Evidence Quality Tagging section above.
- **Atomicity test — lifecycle, not reference count (Apr 2026):** Break a note into its own file when the content has an independent lifecycle (own update cadence, own reuse-of-parts, own open-by-itself value) — not merely when it's referenced from multiple places. See `feedback_vault_note_atomicity_principles.md` for the three-test rubric with Apr 2026 worked examples (stakeholder profiles broken; LinkedIn-posts subnote merged; Mar 2026 stakeholder map kept alongside current profiles).
- **Two-layer naming is valid (Apr 2026):** `contact_*_hsbc.md` (first-meeting intake stubs) and `*-hsbc-profile.md` (ongoing reading lenses) coexist with different naming conventions deliberately. Don't enforce naming consistency across layers that serve different purposes.
