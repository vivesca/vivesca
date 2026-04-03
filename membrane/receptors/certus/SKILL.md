---
name: certus
description: Accountability gate before high-stakes submission — self-critique under simulated rejection. Use before declaring deliverables "done" for external audiences.
disable-model-invocation: true
---

# Certus — "Are You Sure?" Gate

Before any high-stakes deliverable is submitted to the user or sent externally, run this gate.

## When to Trigger

- Presentation decks for interviews or clients
- Proposals, SOWs, or client-facing documents
- Important emails or messages to stakeholders
- PRs to shared/production repos
- Any deliverable where the user said "submit when ready" or gave autonomous authority

**Not for:** internal notes, vault updates, personal scripts, draft-stage work the user will iterate on.

## The Gate (3 passes minimum)

### Pass 1: Domain Translation
- Does every term make sense to the **target audience**, not just the author?
- Would a reader from a different industry understand the acronyms?
- Are examples and analogies anchored in the audience's world, or the author's?

### Pass 2: Claim Defensibility
- Can every metric, number, or factual claim be defended if challenged?
- Are there any "red flag" claims that invite skeptical follow-up? (e.g., unqualified accuracy percentages, unsubstantiated architecture claims)
- Is anything presented as fact that's actually assumption?

### Pass 3: Discoverable Risk
- If the audience reads every slide/page (including appendices, footers, backup), does anything create an attack surface?
- Does any transparency feel like a confession rather than a strength?
- Would a skeptical reader use any part of this against the author?

## Escalation

If the deliverable is high-stakes enough (interview, client pitch, board presentation), recommend `consilium --deep` before the gate. The gate catches what consilium misses (jargon, audience mismatch) and consilium catches what the gate misses (structural flaws, strategic positioning).

## After the Gate

State what you checked, what you changed, and what risk remains. Don't declare "ready" without naming at least one thing you're uncertain about — if you can't find uncertainty, you haven't looked hard enough.
