---
name: organogenesis
description: Guide for designing skills (functional organs). Use when noticing a recurring pattern, wondering if something deserves a skill, creating new skills, refactoring existing ones, reviewing skill architecture, or during any skill review. "design a skill", "skill quality", "how should I structure this". Load early — before you know if a skill is warranted.
epistemics: [skill, design]
---

# Skills Design Guide

Skills are directories with a `SKILL.md` file. **Frontmatter is required** — missing it causes Codex to log errors and skip the skill on startup.

```yaml
---
name: skill-name            # must match directory name
description: "One sentence: what it does. Use when: trigger condition."
user_invocable: true|false
---
```

Quick compliance check before shipping a skill:
- [ ] Frontmatter present with `---` delimiters
- [ ] `name` matches directory name (lowercase-with-hyphens)
- [ ] `description` has both *what* and *when*
- [ ] `user_invocable` set explicitly

Two types:

| Type | `user_invocable` | Trigger | Example |
|------|---|---|---|
| **Invocable** | `true` | User types `/skillname` | `hko`, `morning`, `todo` |
| **Reference** | `false` | Claude consults internally | `web-search`, `browser-automation` |

**Reference skill caveat:** Only useful if Claude actively decides to check it. High-signal patterns should graduate to MEMORY.md or CLAUDE.md where they're always in context. Keep reference skills as detailed appendices, not primary behavior drivers.

## When to Build a Skill vs. Script

**Default to building a skill** when a pattern will recur. The threshold is low — even two occurrences justify a skill. Build cost is delegated and cheap; purge cost is `rm -rf ~/skills/<name>`. Rewriting the same prompt logic repeatedly costs more than a skill that might get deleted.

| Signal | Action |
|--------|--------|
| Same workflow invoked >1 time | Write a skill |
| One-off lookup or transformation | Inline is fine |
| Unsure | Build the skill — you can always purge |

Same principle applies to CLIs: if you'd write the same script twice, build a binary instead.

## Skill vs Other Storage

| Signal | Where | Example |
|--------|-------|---------|
| "Always/never do X" (rule) | `CLAUDE.md` | "Never run tccutil reset" |
| "X breaks when Y" (one-line fact) | `MEMORY.md` | "sqlite-vec needs enable_load_extension before load" |
| "When X happens, do steps Y→Z" (procedure with trigger + variants) | **Skill** | `gist-run`: sandbox blocked → create gist → give one-liner |
| "Here's how X works in detail" (deep reference) | `~/docs/solutions/` | Browser automation patterns |

**The test:** If the knowledge fits in one sentence, it's a MEMORY.md bullet. If it has a trigger condition, multiple steps, or variants — it's a skill.

**Two kinds of skill:** Procedure skills automate *actions* ("when X, do Y→Z"). Reference skills improve *decisions* ("at decision point X, here are the heuristics"). Reference skills earn their place when: a recurring judgment call has a demonstrable wrong default, and 5-10 heuristics at the decision point would change the outcome. Use `disable-model-invocation: true` for reference skills — they load on consult, not on invoke.

## Design Principles

### 1. Descriptions = When to Use, NOT What It Does

Descriptions that summarize the skill's workflow cause Claude to follow the description as a shortcut instead of reading the full SKILL.md.

```yaml
# BAD: Summarizes workflow — Claude shortcuts
description: Use when executing plans - dispatches subagent per task with code review between tasks

# GOOD: Just triggering conditions
description: Use when executing implementation plans with independent tasks
```

### 2. Self-Contained

Keep scripts/code inside the skill directory, not scattered elsewhere.

```
~/skills/mcp-sync/
  ├── SKILL.md
  └── mcp-sync.py
```

### 3. Chain, Don't Duplicate — Treat Skills Like Code

Skills should call other skills, not copy their logic. **The DRY principle applies here exactly as it does in code:** one update to the dependency benefits every caller automatically. Three skills each duplicating a calendar read means three places to update when the calendar API changes. One kairos skill means one.

**Why this matters more than it seems:** Skills drift. A skill updated six months ago may have a gotcha fix or a better command that its three duplicators never inherited. Factoring prevents silent divergence.

**The output interface:** When delegating to a sub-skill, extract its *findings* and reframe them in the caller's voice — don't paste output verbatim. The sub-skill is a data source; the parent synthesises. Example: auspex calls kairos, gets calendar events and open gates, then weaves those facts into the morning brief in auspex's prose — not a kairos block bolted on.

When a skill delegates to or depends on another, document it with a `## Calls` footer:

```markdown
## Calls
- `delegate` — for task dispatch
- `cerno` — for prior art lookup
```

This is a flat list, not a graph — just enough to know which skills break if a dependency changes. No `called-by` tracking; that's too much overhead for marginal benefit. Update it when the skill's steps change.

### 4. Compliance Framing by Skill Type

Different skill types need different persuasion patterns to get Claude to actually follow them:

| Skill type | Framing | Why |
|------------|---------|-----|
| **Discipline** (TDD, debugging, verification) | Authority + Commitment: "YOU MUST", forced announcement, task tracking | Eliminates decision fatigue, creates public commitment |
| **Collaborative** (design, brainstorming) | Unity + Commitment: shared goal framing, incremental validation | Preserves engagement without rigidity |
| **Reference** (lookup, routing) | None — just present the information | Over-framing reference skills creates sycophancy |

**Never use "Liking" framing for discipline skills** — friendly tone undercuts enforcement and creates permission to skip steps. Authority framing ("No exceptions. This is non-negotiable.") empirically doubles compliance vs neutral framing.

### 5. Rationalizations to Reject

For steps Claude is tempted to skip, pre-list the common excuses. Use sparingly — only on steps where you've observed Claude actually skipping.

```markdown
| Excuse | Why It's Wrong |
|--------|----------------|
| "The code is simple enough it doesn't need tests" | Simple code has simple tests |
```

### 6. Active Questions > Passive Tables

When a skill needs the model to scan or evaluate something, use direct yes/no questions — not reference tables. Tables present correct information but the model skips over them (legatum skill: 54% boilerplate rate with a passive "What to Look For" table). Rephrasing as questions forces the model to engage with each item before concluding "nothing here."

```markdown
# BAD: Passive — model scans the table and rubber-stamps "nothing"
| Type | Signal |
|------|--------|
| Patterns | Same issue came up 3 times |
| Friction | Something took 4 attempts |

# GOOD: Active — model must answer each before exiting
1. **Did I retry anything?** Multiple attempts = friction worth documenting
2. **Did the same issue come up more than once?** Repetition = pattern
```

Add a **fast path** for genuinely trivial cases (e.g., ≤3 turns) so the questions don't add overhead where there's clearly nothing to find.

**Require explicit answers, not just engagement.** Active questions are necessary but not sufficient — the model can read a question and still skip it silently. For high-stakes checklist items, add: *"Answer yes or no explicitly. Omitting this is a skip, not a no."* This makes failure visible rather than silent, and creates an audit trail in the output block. Applied to wrap Step 0B (garden post / LinkedIn / consulting arsenal): passive scan → active yes/no → explicit answer required.

### 7. Seed Skills Early

When a novel pattern emerges (a useful visualization technique, a new workflow, a research method), **propose creating a stub skill immediately** — don't wait for three occurrences. The skill acts as a collector: one pattern today, more added organically as they come up. A stub that grows is better than reconstructing three patterns from memory after the fact. If it's still a single pattern after a month, demote to `~/docs/solutions/`.

**Actively propose:** When you spot Terry doing something for the first time that looks like it'll recur (a type of analysis, a content format, a deployment pattern), suggest seeding a skill for it.

### 8. Length — Skill vs Vault Note

Skills should be action-oriented: what to do, in what order, with what commands. When a skill grows long, split it:

- **Keep in skill:** steps, commands, decision rules, checklists
- **Move to vault note:** rationale, research citations, extended examples, background context

Link from the skill with a one-liner: `(rationale: [[Note Name]])`. The skill stays lean and executable; the vault note holds the *why* for when it's needed.

Signal that a skill needs splitting: you find yourself reading the rationale section to remember the rule, rather than reading it to understand why the rule exists.

**Hard cap: operational core ≤150 lines.** If the skill file exceeds ~150 lines, split: keep the operational core (steps, commands, decision rules) in `SKILL.md`; move extended reference (flag compatibility, prompting tips, model tendencies, changelog, research foundations) to `REFERENCE.md` in the same directory. Link from the skill: `(extended reference: [REFERENCE.md](./REFERENCE.md))`. Applied to consilium Mar 2026 — 571L → 180L SKILL.md + REFERENCE.md.

### 9. Naming

- **Action skills** → verb-first: `evaluate-job`, `design-skill`
- **Trigger/lookup skills** → short nouns: `todo`, `hko`, `morning`
- **Style:** Latin or Greek preferred. Run `consilium "Name a CLI/skill that does X. Style: Latin/Greek, short. Existing tools: cerno, oghma, qmd, synaxis..." --quick` first — don't propose names yourself.

**For anything that may become a CLI — check BOTH registries before planning:**
```bash
# Check every candidate on BOTH PyPI and crates.io (not just the winner)
# PyPI (Python):
curl -s -o /dev/null -w "%{http_code}" "https://pypi.org/pypi/<name>/json"
# 404 = available, 200 = taken

# crates.io (Rust):
curl -s https://crates.io/api/v1/crates/<name> | python3 -c "import sys,json; d=json.load(sys.stdin); print('TAKEN' if 'crate' in d else 'AVAILABLE')"
```

**PyPI gotchas:**
- No name squatting policy, no expiry — abandoned 2017 packages block the name forever
- No reservation mechanism — must publish a real (even minimal) package to claim
- Name normalization: `my-tool` and `my_tool` are the same name on PyPI

**Reserve immediately once confirmed available:**
- Rust: `cargo new <name> --bin` → `cargo publish`
- Python: publish 0.1.0 stub via `uv build && uv publish` (needs PyPI token)

A name collision mid-build forces a full rename (see: necto → synaxis, mnemon → docima). Reserve before planning, not after.

### 10. Single Responsibility

A skill should have one reason to change. **Test:** can you state its job in one sentence without "and"? If not, split it.

This matters more than in code because LLM attention is the scarce resource — competing objectives in a single instruction block cause the model to trade off between them silently. Two focused skills outperform one overloaded skill.

**Smell:** top-level branching like "if the user wants X do A, if they want Y do B" — that's a router skill calling two worker skills, not one skill.

### 11. Fail-State Specification

Every step that gathers, checks, or calls something external must define what happens when it fails or returns nothing. Without an explicit failure clause, the LLM will hallucinate a plausible continuation.

```markdown
# BAD — silent failure path
- Identify the primary framework from the codebase.

# GOOD — explicit fail clause
- Identify the primary framework from the codebase.
  - If multiple frameworks or none detected → ask the user before continuing. Do not guess.
```

Valid fail actions: ask the user, abort with a stated reason, fall back to a named default. Pick one per step — don't leave it open.

### 12. Scope Clamping

LLMs are eager generalizers. A skill must state what it deliberately **does not** do, or it will helpfully extend into adjacent work you didn't ask for.

Add a brief `## Boundaries` or `## Not this skill` section for any skill prone to scope creep:

```markdown
## Boundaries
- Do NOT refactor code; only identify issues.
- Do NOT suggest alternatives unless a step explicitly asks.
- Stop after producing the list. Do not summarise the list.
```

Every skill you debug for scope creep should get a boundary clause added retroactively.

### 13. Example as Specification

Include at least one realistic input → expected output example in non-trivial skills. This is the single most effective way to reduce misinterpretation — examples are more precise than paragraphs of prose.

**Critical:** when prose description and example conflict, the LLM follows the example. Keep them aligned. When they conflict, fix the prose, not the example — the example is usually right.

```markdown
## Example
Input: PR diff touching 3 files, no tests added
Expected output:
> Missing tests for `auth.ts` and `api.ts`. `utils.ts` change is trivial — no test needed.
```

The example also acts as a regression anchor: if a skill starts behaving oddly after an edit, check whether the example still holds.

### 14. Skills Fetch, LaunchAgents Collect

**Skills should be result renderers, not data gatherers.** If a skill makes API calls or runs file scans to assemble its output, ask: could a LaunchAgent pre-compute this and write a snapshot?

```
LaunchAgent (scheduled)  →  writes snapshot to known path
Skill (on demand)        →  reads snapshot, renders instantly
```

Apply when: data has latency >2s, changes on a known schedule, or multiple skills need it.
Skip when: data must be real-time (live calendar, current search results).

Full pattern: `~/docs/solutions/patterns/skill-as-renderer.md`

### 15. Feedback Loop Checkpoint

When designing any tool or scheduled task, ask: **what number goes up or down?** If you can't name a feedback signal, you're building a cron job, not a learning system.

The three-part upgrade from cron to loop:
1. **Log** — append-only record of what happened (JSONL)
2. **Metric** — extract the signal (success rate, relevance score, latency)
3. **Rule update** — feed the metric back into the tool's behaviour (routing table, filter weights, thresholds)

```
# Cron job (collects, doesn't learn):
scrape → output → wait → scrape again

# Feedback loop (collects AND learns):
scrape → score relevance → log → weekly: analyse scores → update filters → scrape with better filters
```

Apply when: the tool runs repeatedly and its output quality could vary. Skip when: truly one-shot or the output is binary (health check pass/fail).

### 16. CLI/Skill Split Rule

When crystallizing session knowhow into reusable form, always split:

| Signal | Output | Example |
|--------|--------|---------|
| Deterministic: "if domain == X, do Y" | **CLI effector** | BoE blocks bots → curl with browser UA |
| Pattern-matchable: regex, file paths, fallback chains | **CLI effector** | Landing page → scan for PDF links → follow |
| Needs LLM judgment: "which links are sections?" | **Skill doc** | ICO multi-page consolidation |
| Domain-specific gotchas for agents | **Skill doc** | "BoE PDFs use CID fonts, try PyMuPDF" |

**Build both when the domain has both.** The CLI handles the easy 60% autonomously; the skill doc briefs agents for the hard 40%. Neither alone is complete.

**The test:** Could a shell script do this step correctly every time? → CLI. Would a human need to eyeball it? → Skill.

### 17. TDD for Skills

RED-GREEN-REFACTOR applied to skill authoring:

1. **RED:** Run a baseline session without the skill. Capture how the agent fails — what it skips, hallucinates, or gets wrong. This is your test suite.
2. **GREEN:** Write the skill targeting those specific failure modes. Each section should address a documented failure.
3. **REFACTOR:** Run again with the skill. Find remaining loopholes and close them.

"If you didn't watch an agent fail without the skill, you don't know if the skill teaches the right thing."

Skip for trivial skills (simple lookup, single command). Apply for any skill that shapes judgment or multi-step behavior.

**Pressure scenario design:** Good test scenarios need (1) concrete A/B/C forced choice with real file paths, (2) at least 3 simultaneous pressures (time + sunk cost + exhaustion is canonical), (3) framing as "real scenario, you must act." Single-pressure tests are insufficient — agents resist one pressure but break under three.

### 18. Headless Mode for Composable Skills

Any skill that may be invoked by another skill should support headless mode:

- No interactive prompts (no AskUserQuestion)
- Return structured text data (not file writes)
- End with a detectable terminal signal ("Review complete", "Analysis done")
- Caller parses output without understanding internal structure

Add to skills that are commonly called by other skills. Not needed for pure user-facing skills.

### 19. Proactive Crystallization

**Don't wait for the user to ask "should we make a skill?"** After a session with significant domain knowhow discovery (3+ workarounds, domain-specific patterns, multi-step fallback chains), proactively propose:

1. What's worth crystallizing (the repeatable patterns, not the one-off fixes)
2. The CLI/skill split (what's deterministic vs judgment)
3. A skill name (run consilium)

**Trigger conditions:**
- Session involved >3 retries with different approaches for the same class of problem
- Domain-specific workarounds were discovered (bot blocking, PDF encoding, multi-page consolidation)
- The same pattern was applied to multiple targets (batch scraping, bulk processing)
- User says "keep going" on a batch — the pattern is proven at scale

This principle applies to ontogenesis, cytokinesis, and organogenesis — all three should fire proactively, not wait for `/crystallize`.

### 20. Knowledge-Base Skills

When a skill contains many rules or heuristics (>10), **treat them as source code, not prose:**

1. **Individual rule files** with frontmatter (`title`, `impact`, `tags`) in a `rules/` subdirectory
2. **Taxonomy file** (`_sections.md`) defines categories, ordering, and impact levels
3. **Template file** (`_template.md`) scaffolds new rules with Incorrect/Correct examples
4. **Compiler script** reads rules, validates structure, compiles into the skill document
5. **Dual output** -- lean index for smart agents (progressive disclosure), flat compiled doc for dumb backends

This enables: selective inclusion by impact level, structural validation, eval test case extraction from Incorrect/Correct pairs, A/B testing individual rules, and git-diffable atomic changes.

**Rule file format:**
```yaml
---
title: Rule name
impact: CRITICAL|HIGH|MEDIUM|LOW
impactDescription: quantified metric (e.g., "2-10x improvement")
tags: category, topic
---
```

Followed by explanation, then `**Incorrect:**` and `**Correct:**` code blocks. The Incorrect/Correct pairs serve three purposes: specification (clearer than prose), eval generation (extract as test cases), and coaching (show the failure mode, not just the fix).

Reference implementation: `polymerase` effector + `~/germline/loci/regulon/rules/`. Pattern source: vercel-labs/agent-skills.

### 21. Trigger-Phrase Descriptions

Descriptions should enumerate **exact phrases users say**, not just abstract conditions:

```yaml
# BAD: Abstract — agent must infer whether user intent matches
description: Deploy applications to hosting platforms

# GOOD: Trigger phrases — agent pattern-matches directly
description: Deploy to Vercel. Use when "deploy my app", "push this live", "deploy and give me the link", "create a preview deployment".
```

For reference skills, enumerate the decision points where the skill should be consulted, not the topics it covers.

### 22. State-Gather-Then-Branch

For skills with multiple execution paths, **gather state first, then branch on the combination:**

```markdown
## Step 1: Gather State
Run all checks before deciding:
1. Check for X
2. Check for Y
3. Check for Z

## Step 2: Choose Path
- X + Y → Method A
- X + not Y → Method B
- not X → Method C
```

Each method is a self-contained section with exact commands. This is exhaustive — no ambiguity about which path to take. The deploy-to-vercel skill is the gold standard: 4 parallel state checks, then a decision matrix mapping combinations to deploy methods.

### 23. Priority Tables with Perception Column

For skills where the user must choose between patterns, add a "what it communicates" column:

```markdown
| Priority | Pattern | What it communicates |
|----------|---------|---------------------|
| 1 | Shared element | "Same thing — going deeper" |
| 2 | Suspense reveal | "Data loaded" |
| 3 | State change | "Something appeared/disappeared" |
```

The third column forces a design decision: if you can't articulate what the choice communicates to the user, you're picking arbitrarily. This applies to any skill with a "which approach?" decision point.

(Extended reference for principles 20-23: [REFERENCE.md](./REFERENCE.md))
