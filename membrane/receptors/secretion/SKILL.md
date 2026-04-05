---
name: secretion
description: Package and release a consulting deliverable — quality-gate, format, ship. Use when a report, deck, or memo is ready for client delivery. "ship deliverable", "release report", "package for client"
user_invocable: true
model: sonnet
context: fork
epistemics: [communicate, evaluate]
---

# Secretion — Packaging and Releasing the Deliverable

Cellular secretion: the cell synthesizes a product, packages it into vesicles, and releases it to the extracellular environment. The product is transformed during packaging — it leaves in export form, not synthesis form.

This skill governs the final stage of consulting output: the artifact has been synthesized (in drafts, iterations, annealing). Now it must be packaged for the client's environment and released correctly.

Note: `secretion` exists as an MCP tool (raw file output). This skill is the judgment layer — quality gate, format verification, and delivery decision — that wraps the tool.

## When to Use

- A consulting deliverable (report, deck, memo, model) is ready for client release
- A document has been drafted and iterated and needs to become an artifact
- Output is being sent to an external consumer (not internal organism)
- Quality checkpoint before anything leaves the organism

## Method

### Step 1 — Verify synthesis completeness

Before packaging, confirm the content is done:
- [ ] All sections present (match agreed scope)
- [ ] Claims verified (no asserted facts without source)
- [ ] Numbers checked (totals, percentages, dates)
- [ ] Recommendations actionable (not just observations)

If synthesis is incomplete: do not enter packaging. Return to the draft.

### Step 2 — Package for the recipient

External consumers are not organism-native. Transform accordingly:

| Organism form | Export form |
|--------------|-------------|
| Markdown with internal links | PDF or clean DOCX |
| Biology naming (receptor, organelle) | Plain language (tool, process) |
| Shorthand from context | Explained on first use |
| ASCII formatting | Rich formatting appropriate to medium |

Check: would the client understand this without having been in the room?

### Step 3 — Quality gate (three reads)

1. **Structural read:** does it flow? Is the argument traceable from problem to recommendation?
2. **Factual read:** are the claims defensible? Would you stand behind each one in a client meeting?
3. **Recipient read:** read as the client. What will they underline? What will confuse them? What will they push back on?

Flag, fix, or note-for-discussion anything that fails a read.

### Step 4 — Release

Use the secretion MCP tool for file output. Confirm:
- Correct filename (client-facing, dated, versioned if needed)
- Correct destination (shared drive, email, platform)
- Correct recipient list (no internal-only versions to external list)

### Step 5 — Log the release

```
Deliverable: [name]
Released: [date]
Recipient: [client / stakeholder]
Format: [PDF / DOCX / Notion / etc.]
Version: [v1.0 / final / etc.]
Outstanding items: [anything flagged but not fixed]
```

## Anti-patterns

- **Packaging incomplete synthesis:** the vesicle ships, the product isn't ready. Client-facing quality problems are harder to recover from than internal ones.
- **Organism-native language in export:** biology names, internal shorthand, and tool references that mean nothing to the client. Always translate.
- **No quality gate:** shipping immediately after synthesis. Every deliverable needs at least one structural read by a fresh perspective.
- **Not logging the release:** if you can't answer "what did we send and when," you can't manage revisions.

## Motifs
- [verify-gate](../motifs/verify-gate.md)
