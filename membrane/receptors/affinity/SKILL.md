---
name: affinity
description: "Iterative multi-model stress-testing that hardens deliverables against a specific audience. Draft \u2192 persona-driven review \u2192 selective fix \u2192 tighten. Like B cell affinity maturation: each round of mutation + selection produces higher binding to the target."
triggers:
  - "stress test this"
  - "harden this"
  - "make this bulletproof"
  - "review from Simon's perspective"
  - "would this survive a room of"
  - "affinity"
  - "/affinity"
epistemics:
  - feedback_executive_paper_style
  - feedback_partner_message_density
---

# Affinity

Iterative multi-model stress-testing that hardens deliverables against a specific audience. Named for B cell affinity maturation: somatic hypermutation + selection pressure produces progressively stronger binding to the antigen (the skeptical reader).

## When to use

- Executive papers, proposals, or pitch documents before they reach a decision-maker
- Any deliverable where rejection is costly and the audience is known
- When "good enough" isn't — the document needs to survive hostile scrutiny

## When NOT to use

- Internal working notes (overkill)
- Code review (use scrutor/correctness-reviewer)
- Quick comms (use censor for quality gate)
- When the audience isn't known or the stakes are low

## The Loop

### 1. Identify the antigen (audience persona)

Define who will read this and what their default disposition is. Be specific:
- Role, seniority, domain expertise
- What makes them skeptical
- What they care about (not what you care about)
- What would make them say no

Example: "Senior risk executive, 20 years MRM, sits on AI Risk Committee, skeptical of consultants, cares about regulatory defensibility and operational viability."

### 2. Generate diversity (multi-model review)

Run the deliverable through multiple models WITH the persona prompt. Minimum viable: quorate council + one cold-reader. Optimal: quorate + 2 cold-readers from different model families.

```bash
# Council for structural/logical analysis
quorate council --deep --context <file> "<persona prompt + specific challenges>"

# Cold readers for stakeholder simulation
codex exec -c model=gpt-5.5 "<persona + review prompt>"
gemini -m gemini-3.1-pro-preview -p "<persona + review prompt>"

# Opus for same-model blind spot detection (optional)
# Use Agent tool with fresh context
```

The persona prompt template:
```
You are [ROLE] reading this [DOCUMENT TYPE] cold. You have [EXPERIENCE].
You are [DISPOSITION]. Read [FILE] and give me:
(1) Honest first reaction in 2 sentences.
(2) Strongest point.
(3) Weakest point or biggest logical gap.
(4) One question you would ask the authors in a meeting.
(5) Would you approve [ACTION]? Why or why not? Be blunt.
```

### 3. Selection pressure (synthesize + agree/disagree)

Present ALL critiques to the user. For each:
- **Agree** — the critique identifies a real gap. Fix it.
- **Partially agree** — the concern is valid but the proposed fix is wrong. Fix differently.
- **Disagree** — the critique misreads the document or applies a wrong frame. Note why and skip.
- **Already addressed** — the reviewer read a stale version. Note and skip.

This is the human judgment step. Not all mutations survive selection. The user decides what binds better.

### 4. Hypermutation (surgical fixes)

Apply agreed fixes. Rules:
- Surgical, not wholesale rewrite
- Each fix addresses one specific critique
- Don't over-rotate — fixing one weakness shouldn't create another
- If a fix requires more than one paragraph, it's a structural issue — consider whether the document's architecture needs rethinking

### 5. Tighten (remove internal stresses)

Iterative additions always bloat. After all fixes are applied:
- Cut ~15-20% of word count
- Remove repetition introduced by additions
- Ensure every section earns its place
- Check transitions between sections
- Verify the arc: problem → insight → mechanism → evidence → ask

### 6. Verify completeness

Check whether the document now has:
- [ ] Novelty statement — what's new hits in the first 60 seconds
- [ ] Efficiency/value quantification — even rough math
- [ ] Honest acknowledgment of limitations — what's hypothesis vs. proven
- [ ] Crisp closing ask — what does the reader DO after reading
- [ ] Evidence that maps to claims (not generic, not padding)

### 7. Optional: final round

If the changes were substantial, run one more cold-reader on the updated version to verify the fixes landed and didn't introduce new gaps. This is the "affinity check" — did binding actually improve?

## Model Selection

Each model catches different things:
- **Quorate council** — structural/logical gaps, overclaims, missing layers
- **Codex/GPT** — practical "would I fund this" verdict, operational gaps
- **Gemini** — regulatory viability, implementation reality, "is this just repackaging"
- **Opus (fresh agent)** — same-model blind spots, internal inconsistencies, what the author missed

The combination produces better results than any single review. Minimum: quorate + one cold-reader. Optimal: quorate + two cold-readers from different families.

## Cost

- quorate council --deep: ~$0.50
- Each cold-reader (Codex/Gemini): ~$0.10-0.30
- Total for full loop: ~$1-2
- Time: 15-30 minutes (mostly waiting for models)

## Success Metric

The deliverable is "mature" when:
- A cold-reader's strongest critique is something the document already addresses
- Budget verdict shifts from "no" to "pilot yes"
- No reviewer identifies a structural gap — only refinement suggestions remain

## See Also

- `/quorate` — the deliberation engine (step 2)
- `/censor` — binary quality gate (lighter, for comms not proposals)
- `/modification` — multi-model cooling (similar but without persona simulation)
- `/opsonization` — preparing a person for a meeting (complementary)
