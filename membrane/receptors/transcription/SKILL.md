---
name: transcription
description: Collaborative design before building — one question at a time, right-sized spec.
user_invocable: true
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

### 2. Pressure test (standard/deep only)

Before generating approaches, challenge the request:
- Is this the real problem, or a proxy?
- What happens if we do nothing?
- Are we duplicating something that already covers this?
- Is there a reframing that creates more value without more carrying cost?

State your view. If the answer is "don't build this," say so.

### 3. Clarifying questions

**One question per message.** No batching. Prefer multiple choice when natural options exist. Start broad (problem, users, value), narrow to specifics (constraints, edge cases, non-goals).

Each answer reshapes the next question. This is the point — divergent exploration, not a pre-planned interview.

Exit when the shape is clear OR the user says "enough, let's go."

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

### Before Planning
- [Question that blocks implementation]

### Deferred
- [Question better answered during planning or building]
```

Omit empty sections. A 10-line doc that says the right things beats a 100-line doc padded with ceremony.

## Handoff

When the design is approved:
- If a requirements doc was written, state the path
- Recommend next step: `/translation` to break it into steps, or `/folding` directly if the plan is obvious
- **Do not start implementing.** The user decides when to cross that line.

## Principles

- **One question at a time.** The constraint that prevents LLM question-vomit.
- **YAGNI on carrying cost.** Simple is good. Low-cost polish is also good. Avoid speculative complexity.
- **State your view.** This is a thinking partner, not an interviewer. Recommend, challenge, push back.
- **Each answer reshapes the next question.** Pre-planned question lists miss the point. React to what you learn.
- **Scale ceremony to scope.** Light work gets light process. Deep work gets deep process. Never the reverse.
