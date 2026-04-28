---
name: transcription
description: Collaborative design before building — one question at a time. "let's build", "I want to add", "design first"
effort: high
user_invocable: true
triggers:
  - transcription
  - "let's build"
  - "I want to add"
  - "what if we"
  - design
  - plan
epistemics: [design, plan]
---

# /transcription — Design Before Building

Turn an idea into a design through dialogue. Hard gate: **no implementation until design is approved.**

## When to Use

- Before building any feature, tool, skill, or non-trivial change
- When the user says "let's build", "I want to add", "what if we..."
- When you're about to start coding and realise the shape isn't clear yet
- **Not needed for:** bug fixes with obvious cause, config changes, renaming

## Scope Check (10 seconds)

Glance at the idea. Classify:

- **Light** — bounded, low ambiguity, few decisions. 1-2 questions, maybe no doc.
- **Standard** — some decisions to make, multiple approaches possible. 3-5 questions, short spec.
- **Deep** — cross-cutting, ambiguous, or strategic. Full dialogue, proper spec.

Match ceremony to scope. A config tweak doesn't need a requirements doc. A new actus does.

## The Dialogue

### 1. Context scan

Before asking anything, scan for what already exists. Match depth to scope:
- **Light:** Quick search for the topic, check for prior art, move on.
- **Standard/Deep:** Search relevant code, docs, recent brainstorms. Read the most relevant existing artifact. Note patterns to follow.

### 1.5. Divergent ideation (when the problem space is open)

**Trigger:** user asks "what should we build?", "what would you improve?", "ideate", or the request is open-ended without a specific target. Skip this when the user already knows what they want.

Generate many ideas before critiquing any:

1. **Diverge with frames.** Dispatch 3-5 parallel sub-agents, each biased toward a different angle:
   - pain/friction in current workflows
   - missing capability or unmet need
   - inversion — remove or automate a painful step
   - assumption-breaking — reframe the problem
   - leverage — what compounds future work
   Each agent generates 5-8 raw candidates grounded in codebase context. No filtering yet.

2. **Merge and synthesize.** Deduplicate. Then scan for cross-cutting combinations — ideas from different frames that together are stronger than either alone. Add 2-3 combined ideas.

3. **Adversarial filter.** Critique the full merged list. For each rejected idea, write a one-line reason. Score survivors on: groundedness, expected value, novelty, pragmatism, leverage, implementation burden. Keep 5-7 survivors.

4. **Present and choose.** Show survivors ranked. User picks one → proceed to step 2 with that idea as the target.

### 2. Pressure test (standard/deep only)

Before generating approaches, challenge the request:
- Is this the real problem, or a proxy?
- What happens if we do nothing?
- Are we duplicating something that already covers this?
- Is there a reframing that creates more value without more carrying cost?

State your view. If the answer is "don't build this," say so.

### 3. Clarifying questions

**One question per message.** No batching. Prefer multiple choice when natural options exist. Start broad (problem, users, value), narrow to specifics (constraints, edge cases, non-goals).

**Gray-area categories (vivesca synthesis — inspired by `compound-engineering/ce-brainstorm` scope-classification approach, extended into a question-generation taxonomy).** Before asking, classify the build by category and pull questions from the matching pool — don't ask generic "what about errors?" prompts:

- **Visual feature** → layout, density, interactions, empty states, loading states
- **API / CLI** → response shape, flag set, error verbosity, idempotency, `--json` envelope
- **Content system** → structure, tone, depth, flow, metadata
- **Organization / sweep task** → grouping criteria, naming, duplicate handling, exception cases

Pick the 2-3 categories that fit. Surface each as locked decisions that downstream researcher and planner read directly — no "ask again later."

Each answer reshapes the next question. This is the point — divergent exploration, not a pre-planned interview.

Exit when the shape is clear OR the user says "enough, let's go."

**Negative existential claims:** If you assert something is absent ("there's no auth middleware", "the API doesn't have X"), verify against source before writing it into the spec — or label it "unverified assumption." These are the highest-risk hallucinations in planning.

### 4. Approaches

Propose **2-3 approaches** with trade-offs. Lead with your recommendation and why. Include:
- Brief description (2-3 sentences)
- Pros, cons, key risks
- When each is best suited

If one approach is clearly best, say so directly and skip the menu.

### 5. Design presentation

Present the design incrementally — section by section, confirming as you go. Scale each section to its complexity: a sentence if obvious, a paragraph if nuanced.

Cover what's relevant: architecture, components, data flow, error handling, interactions. Skip sections that add nothing.

### 6. Capture (if warranted)

**Light scope:** No doc needed. The conversation IS the record.

**Standard/Deep:** Write a requirements doc to `~/germline/loci/brainstorms/YYYY-MM-DD-<topic>.md`:

```markdown
---
date: YYYY-MM-DD
topic: <kebab-case>
---

# <Topic>

## Problem
[Who, what, why — 2-3 sentences]

## Requirements
- R1. [Concrete behaviour or constraint]
- R2. ...

## Scope Boundaries
- [Deliberate non-goals]

## Key Decisions
- [Decision]: [Rationale]

## Outstanding Questions

### Before Planning (blocks — must be answered before handoff)
- [Question that blocks implementation]

### Deferred to Planning (better answered during codebase exploration)
- [Question that can wait]

Planning cannot start while "Before Planning" questions remain unanswered. Don't disguise blocking ambiguity as deferred questions.
```

Omit empty sections. A 10-line doc that says the right things beats a 100-line doc padded with ceremony.

## Handoff

When the design is approved:
- **Completeness check:** "What would `/mitogen` still have to invent if this design phase ended now?" If the answer is anything structural, the design isn't done.
- If a requirements doc was written, state the path
- Recommend next step: `ribosome "implement the design"` or `/mitogen` for complex multi-task dispatch
- **Do not start implementing.** The user decides when to cross that line.

## Principles

- **One question at a time.** The constraint that prevents LLM question-vomit.
- **YAGNI on carrying cost.** Simple is good. Low-cost polish is also good. Avoid speculative complexity.
- **State your view.** This is a thinking partner, not an interviewer. Recommend, challenge, push back.
- **Each answer reshapes the next question.** Pre-planned question lists miss the point. React to what you learn.
- **Scale ceremony to scope.** Light work gets light process. Deep work gets deep process. Never the reverse.

## Motifs
- [state-branch](../motifs/state-branch.md)
- [check-before-build](../motifs/check-before-build.md)
- [verify-gate](../motifs/verify-gate.md)
