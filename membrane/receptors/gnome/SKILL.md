---
name: gnome
description: Capture structured decisions with past-decision surfacing (bouncer pattern). Use when user says "gnome", "/gnome", "I need to decide", or is weighing options with trade-offs.
user_invocable: true
---

# Gnome

Capture decisions to `~/notes/decisions/` with the **bouncer pattern**: before logging anything new, search past decisions and surface similar ones. Recurrence = implicit outcome tracking — if you're back on a topic you already decided, that IS the signal. When logging, tag which `topica` models applied — builds the feedback loop.

*Gnōmē (γνώμη): in Aristotle, the crystallised residue of having judged — recalled to govern new situations. Sits upstream of both epistēmē (measurable → judex) and boulē (uncertain → consilium).*

## Commands

### `/gnome <topic and rationale>` (default — bouncer + capture)

Free-text capture. User provides topic and reasoning in natural language; Claude structures it into a decision note.

**Examples:**
- `/gnome Accept Capco offer — better comp, AI-focused role, consulting career path`
- `/gnome Use QMD over Oghma for decision search — static docs, auto-indexed, no extra infra`
- `/gnome` (bare — Claude asks "What are you deciding?")

**Logic:**

0. **ROUTE FIRST:**
   > consilium = outcome is uncertain, needs perspectives. judex = outcome is measurable, needs evidence.
   - Can you run both options and compare with a measurable criterion? → `judex` (see `~/skills/judex/SKILL.md`)
   - Does it involve genuine trade-offs, values, or domain judgment? → `consilium`
   - Is it a committed choice that just needs capturing? → proceed below

1. Run `date +%Y-%m-%d` to get today in HKT
2. If bare `/gnome` with no arguments, ask: "What are you deciding?"
3. Extract the core topic from user's input (first clause before em-dash or period)

4. **BOUNCER CHECK:**
   - Run `qmd query "<topic>" -n 3` in Bash
   - Scan results for paths containing `decisions/`
   - If a past decision matches:
     - Read the matching decision note
     - Present: "You decided **[decision]** on **[date]**. Confidence: **[level]**. Context: [brief summary]. New situation, or are we re-litigating?"
     - If new situation → proceed to step 5
     - If re-litigating → show the full past decision, ask what changed. If user wants to revise, update the existing note's `status: revised` and create a new decision note.

5. **STRUCTURE** the user's free-text input into a decision note. Extract:
   - **Decision** — what was decided (one sentence)
   - **Context** — why this decision was needed now (from user's input or ask briefly)
   - **Options considered** — if user mentioned alternatives, list them. If not, don't force it — some decisions are "do X or don't"
   - **Rationale** — why this option over others (from user's input)
   - **Confidence** — infer from language ("obviously" = high, "I think" = medium, "not sure but" = low). If ambiguous, ask with one quick AskUserQuestion (high/medium/low)
   - **Domain** — infer from topic: career, technical, financial, personal, client
   - **Review date** — only add if user explicitly requests it or the decision is clearly time-bound. Do NOT default.
   - **Tags** — 1-3 relevant tags inferred from content

6. **COMPLIANCE CHECK:** If domain is `client`, add this line above the Context section:
   > *Compliance note: Patterns and principles only — no client names, project codes, or proprietary data.*

7. Generate slug from topic: lowercase, kebab-case, max 5 words
8. Write to `~/notes/decisions/YYYY-MM-DD-<slug>.md` using the template below
9. Confirm: "Decision logged: `decisions/YYYY-MM-DD-<slug>.md`"
10. If the decision involved complex trade-offs, offer: "Want to stress-test this with `/consilium --redteam`?"

**Template:**

```markdown
---
date: YYYY-MM-DD
type: decision
decision: "One-sentence summary"
domain: career|technical|financial|personal|client
confidence: high|medium|low
status: active
tags:
  - tag1
  - tag2
---

# Decision Title

## Context

[Why this decision was needed now]

## Options Considered

1. **Chosen option** — [rationale]
2. **Rejected option** — [why rejected]

## Decision

[What was decided and why]

## Confidence

[Level] — [brief justification]

**Related:** [[relevant note]] | [[other note]]
```

### `/gnome search <query>`

Search past decisions semantically.

**Logic:**
1. Run `qmd query "<query>" -n 5` in Bash
2. Filter results to paths containing `decisions/`
3. If no decision results found, also check `~/notes/Councils/` for council outputs that may contain decisions
4. Present results with: date, decision summary (from frontmatter `decision:` field), confidence, domain
5. Offer to read any full decision note

### `/gnome review`

Surface decisions with a review date that has passed.

**Logic:**
1. Run `date +%Y-%m-%d` to get today
2. Use Grep tool to search `~/notes/decisions/` for `review_date:` in files
3. For each file with `review_date:`, read the frontmatter and parse the date
4. Filter for `review_date` <= today AND `status: active`
5. If none due: "No decisions up for review."
6. For each due review:
   - Read the full decision note
   - Present: original decision, confidence, date decided, context summary
   - Ask: "Looking back — confirmed, revised, or regretted?"
   - Update the note's `status:` field accordingly
   - If revised or regretted, offer to create a new `/gnome` entry

## Notes

- **Storage:** `~/notes/decisions/YYYY-MM-DD-<slug>.md` — Obsidian vault, QMD auto-indexes every 2h
- **Indexing lag:** New decisions won't appear in bouncer searches for up to 2h. This is fine — the bouncer matters for decisions spaced days/weeks apart, not minutes.
- **No manual outcome tracking.** The bouncer IS the outcome tracker: if you come back to the same topic, the previous decision either held (you never return) or failed (you're back). Recurrence = implicit failure signal.
- **Consilium integration:** For complex decisions, use `/consilium` first to deliberate, then `/gnome` to log the outcome. Council outputs in `~/notes/Councils/` complement but don't replace decision notes.
- **Keep it fast.** Capture should take <30 seconds. If you're spending 2 minutes filling in fields, the skill is failing. Free-text in, structured note out.

## Calls
- `qmd` — bouncer search and decision lookup
- `judex` — when outcome is measurable
- `consilium` — when trade-offs need deliberation
