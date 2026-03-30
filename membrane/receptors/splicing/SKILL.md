---
name: splicing
description: Trim always-loaded context files for signal dilution. "genome trim", "coaching trim", "context audit"
user_invocable: true
model: sonnet
context: fork
---

# Splicing — Context Signal Audit

The spliceosome removes introns from pre-mRNA, leaving only coding exons. This skill removes diluted, duplicated, or misplaced rules from always-loaded context files — genome.md, coaching notes, MEMORY.md. Removed items aren't destroyed; they relocate to epistemics or memory where retrieval is situational, not unconditional.

**Why it matters:** Every line in an always-loaded file costs tokens every session and dilutes signal. A rule that's violated while loaded = the doc is too long (feedback_genome_signal_dilution.md).

---

## Targets

| File | Role | Budget |
|---|---|---|
| `~/germline/genome.md` | Constitutional rules, every session | <100 lines |
| `~/epigenome/marks/feedback_glm_coaching.md` | GLM coaching, every goose dispatch | <40 lines |
| `~/epigenome/marks/MEMORY.md` | Memory index, every session | <200 lines |

## Classification

For each non-blank, non-heading content line:

| Class | Meaning | Action |
|---|---|---|
| **A (exon)** | Actively constrains behavior | Keep |
| **B (weak exon)** | Too vague to enforce | Sharpen to A or move to epistemics |
| **C (intron)** | Duplicated elsewhere (memory, hooks, epistemics) | Delete — the copy is the authority |
| **D (pseudogene)** | Aspirational, volatile, or not actionable | Move to epistemics or memory |

### Tests for each class

- **A test:** "If I removed this line, would behavior change next session?" If yes → A.
- **C test:** grep MEMORY.md, hooks, epistemics for the same rule. If found → C.
- **D test:** "Does this line contain a date, name, or status that will change?" If yes → D.
- **B test:** "Can I write a hook or test that detects violation?" If no → B.

## Process

1. Read the target file
2. Classify every content line (produce the table)
3. For each C/D: identify destination (epistemics file, memory file, or safe-delete)
4. For each B: propose sharpened version or relocation
5. Present table + proposed edits. CC reviews before applying.
6. After applying: `wc -l` the file and compare to budget

## Coaching-specific rules

The coaching file (`feedback_glm_coaching.md`) has extra constraints:
- **Only GLM-facing items.** CC-facing guidance (spec writing, mode selection, routing) goes to `feedback_translocon_spec_writing.md`.
- **Compress entries.** One line per pattern where possible. Examples eat tokens.
- **Retire entries.** If GLM hasn't violated a pattern in 5+ dispatches, delete it.

## When to run

- After any session that adds 3+ lines to genome.md or coaching
- Monthly as part of `/infradian` (weekly review)
- When `feedback_genome_signal_dilution.md` pattern is observed (rule violated while file is loaded)
