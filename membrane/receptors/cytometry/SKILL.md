---
name: cytometry
description: Classify subsystems as self-governing vs human-gated. Use when auditing which components need human approval. "autonomy audit", "classify autonomy"
user_invocable: true
triggers:
  - cytometry
  - autonomy audit
  - classify autonomy
  - self-governing
model: sonnet
context: fork
epistemics: [monitor, evaluate]
---

# Cytometry — Autonomy Classification

Flow cytometry sorts cells into populations by measurable properties. This skill sorts organism subsystems into autonomy populations: what self-regulates, what waits for instructions, what requires human judgment by design.

**Sibling structural audits:** `/histology` (client workshop format). For diagnostics: `/auscultation` → `/palpation` → `/integrin`.

## The Audit

For each subsystem in `vivesca://anatomy`:

### 1. SENSE — How does it activate?

| Signal | Classification |
|--------|---------------|
| Fires autonomously (LaunchAgent, hook, cron) | Self-governing |
| Fires only when a session requests it | Needs a mayor |
| Hard-gated by design (NEVER send, taste required) | Intentionally gated |

### 2. CLASSIFY — Sort into populations

```
SELF-GOVERNING (truly autonomic)
  Test: Would this subsystem notice a problem and act without Terry?

NEEDS A MAYOR (tools that wait for instructions)
  Test: Does this subsystem have initiative, or only capability?

INTENTIONALLY GATED (human judgment required by design)
  Test: Is the gate a design choice or an unfinished feature?
```

### 3. MEASURE — Quantify the split

Report the ratio: `X% self-governing, Y% needs mayor, Z% intentionally gated`

Compare to prior audit if available (check for previous cytometry results in session history).

### 4. DIAGNOSE — Find the actionable gaps

For each "needs a mayor" subsystem, ask:
- **Could a heartbeat fix this?** (periodic check for staleness → the mismatch-repair substrate pattern)
- **Could a hook fix this?** (deterministic trigger on an observable event)
- **Does it genuinely need taste?** (if yes, move to "intentionally gated")

The interesting finding is always in the middle column. Self-governing is done. Gated is by design. "Needs a mayor" is where the organism is pretending to be more autonomous than it is.

### 5. ACT — Pick one gap and close it

Don't audit and file. Audit and fix the highest-leverage gap in one pass. The mismatch-repair heartbeat substrate was born from the first cytometry audit — the pattern should repeat.

## Output Format

```markdown
## Cytometry Report — {date}

**Population split:** X self-governing / Y needs mayor / Z gated (of N total)

### Self-Governing
- subsystem: mechanism (LaunchAgent|hook|substrate)

### Needs a Mayor
- subsystem: why (no trigger|no heartbeat|session-only)
  → Rx: {hook|heartbeat|taste gate}

### Intentionally Gated
- subsystem: gate reason

### Highest-leverage gap
{One subsystem to fix now, with proposed mechanism}
```

## Provenance

Born from a late-night thought experiment: "what if vivesca is a city?" The city metaphor asked whether the organism genuinely self-regulates or just has a mayor (Terry) who thinks he's a cell. The audit found the organism was ~30% self-governing, ~50% waiting for the mayor. The mismatch-repair heartbeat substrate was the first fix. This skill makes the audit repeatable.
