---
name: examen
description: Premise audit — surface and test load-bearing assumptions before acting. Consult before delegating a large task, committing to an approach, or making a high-stakes decision when the plan "feels right" but assumptions haven't been checked.
effort: high
user_invocable: false
---

# examen — Premise Audit

Not user-invocable. Consulted internally before high-stakes action.

*Examen: Latin "examination / tongue of a balance" — the pointer that shows whether a scale is level. Here: the check that shows whether your plan is balanced on solid ground.*

## The Core Question

> What are you assuming to be true that you haven't verified?

Plans fail not because the logic is wrong, but because a premise was wrong. The examen catches that *before* you execute. Consult `topica` — which mental model would challenge the strongest assumption here? Consult `bouleusis` — which planning failure mode (goal fog, bad world model, narrow simulation) might be at play?

## When to Run

- Before delegating a large task (wrong premise → wasted delegation)
- Before committing to an architecture or technical approach
- Before a high-stakes decision where you're reasoning from "I think X is true"
- When a plan feels right but you haven't explicitly listed what it depends on
- When a previous judex/consilium result is being acted on — verify the premises haven't changed

**Not needed for:**
- Routine, reversible decisions
- Obvious premises (gravity, the codebase being in Rust, etc.)
- When you've already run examen recently on the same plan

## The Pattern

**1. List assumptions**
Write down 3-5 things your plan or decision depends on being true. Don't filter — just list.

**2. Classify each**

| Type | Definition | Example |
|------|-----------|---------|
| **Load-bearing** | Plan fails or significantly degrades if this is wrong | "Gemini CLI can build Rust without sandbox restrictions" |
| **Incidental** | Nice to have, recoverable if wrong | "The PR will be small" |

Focus only on load-bearing ones. Incidental assumptions don't need verification.

**3. Verify load-bearing assumptions**

For each load-bearing assumption, in order:
1. `cerno "<assumption topic>"` — do we already know the answer?
2. Web search if cerno returns nothing
3. `consilium` if still uncertain and stakes are high

**4. Gate check**

> More than 2 unverified load-bearing assumptions? Stop. Verify before proceeding.

One unverified premise is a risk. Two is a pattern. Three is a plan built on air.

## Example

**Plan:** Delegate Feature A (Rust, 4 files) to Codex.

**Assumptions listed:**
1. Codex can run `cargo build --release` to validate its output ← load-bearing
2. The task is scoped to 4 files ← load-bearing
3. The PR will be straightforward to review ← incidental

**Verification:**
- Assumption 1: `cerno "codex sandbox cargo build"` → MEMORY.md returns: "Codex sandbox blocks DNS → can't run cargo build." **Assumption is FALSE.**
- Decision: switch to Gemini (runs natively, can discover compile errors).

**Result:** Caught before delegation. Saved ~2h of a failed Codex run.

## Relationship to Other Skills

- **examen** runs *before* judex or consilium — checks the premises that those skills would reason from
- **trutina** is for when you have conflicting evidence about a premise — examen surfaces the question, trutina resolves it
- **judex** is for when the outcome is measurable — but judex still assumes its own premises (e.g., "my verification criterion is correct")

## Motifs
- [verify-gate](../motifs/verify-gate.md)
