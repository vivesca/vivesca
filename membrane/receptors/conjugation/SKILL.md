---
name: conjugation
description: Borrow patterns from one system to improve another. "conjugation", "borrow"
user_invocable: true
model: sonnet
context: fork
---

# Conjugation — Horizontal Gene Transfer Between Systems

Bacterial conjugation: two cells form a direct bridge and transfer genetic material. The recipient gains new capabilities without reproduction. This is how antibiotic resistance spreads — not inheritance, but lateral transfer.

Applied: deliberately import a working pattern from one system into another. Not copy-paste — targeted transfer of the mechanism that made it work.

## When to Use

- Another system (yours or observed) handles a problem well that this system handles poorly
- You're designing a new capability and something analogous exists elsewhere
- Post-conversation with another practitioner — you spotted a pattern worth importing
- The organism has grown and a pattern from an earlier version should propagate forward

## Method

### Step 1 — Identify the donor pattern

Name it precisely:
- What problem does it solve?
- What is the mechanism (not the implementation)?
- Why does it work? (the principle, not the behavior)

Example: "endocytosis's poll-then-extract loop solves high-volume intake without blocking. Mechanism: async fetch + synchronous extraction queue. Works because it decouples arrival rate from processing rate."

### Step 2 — Identify the recipient gap

Where in the current organism does the same problem exist without a good solution? Be specific — name the file, process, or receptor.

### Step 3 — Translate, don't transplant

The donor pattern runs in foreign cytoplasm. Direct transplant fails. Extract the principle and re-express it in organism idiom:
- Organism naming conventions
- Organism data structures
- Organism error handling patterns

### Step 4 — Pilot in one location

Pick the smallest site where the pattern applies. Implement there first. Verify it works. Measure if it actually solves the problem.

### Step 5 — Propagate if validated

Once pilot works: identify all other sites where the same gap exists. Apply the translated pattern. Consistent expression > isolated cleverness.

## Conjugation Log

Keep a brief record of imported patterns:
| Pattern | Donor system | Recipient site | Date | Outcome |
|---------|-------------|---------------|------|---------|
| Poll-then-extract | endocytosis | future intake | — | — |

## Anti-patterns

- **Transplanting without translating:** copy-paste from another codebase. Foreign DNA is incompatible. Always re-express.
- **Conjugating for novelty:** importing a pattern because it's interesting, not because there's a gap. Horizontal transfer should solve a real problem.
- **Never recording the transfer:** patterns that aren't logged drift back out. The conjugation log is the organism's HGT record.
