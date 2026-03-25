---
name: annealing
description: Iterative artifact refinement — start hot (wild), cool to convergence. "annealing", "polish draft", "refine spec", "iterative improvement", "cool down".
user_invocable: true
model: sonnet
context: fork
---

# Annealing — Simulated Cooling for Artifact Refinement

Metallurgical annealing: heat metal to disorder, cool slowly so atoms settle into optimal low-energy configuration. Applied here: start with a maximally disordered (expansive, unconstrained) draft, then cool through successive passes until the artifact is dense, accurate, and stable.

## When to Use

- A doc or spec exists but feels bloated or incoherent
- A draft was written fast and needs to earn its final form
- You've iterated manually but the artifact keeps growing, not sharpening
- Post-brainstorm: the superpowers session produced volume, now converge

## The Cooling Schedule

### Temperature: HOT (pass 1) — Expand without constraint

Read the artifact as-is. Then rewrite from memory with zero fidelity constraint. Let it be longer, stranger, more honest. Surface what the careful draft suppressed.

Goal: expose the underlying structure by releasing the surface.

### Temperature: WARM (pass 2) — Structural alignment

Compare the hot draft to the original. Extract the best of each:
- Original: what was precise and correctly scoped
- Hot draft: what was honest and structurally true

Produce a merged draft. Cut anything that appears in neither.

### Temperature: COOL (pass 3) — Compression

Read the warm draft. Apply one rule: every sentence must earn its place. Cut or condense anything that:
- Restates what came before
- Hedges without adding information
- Would survive removal unnoticed

Target: 40-60% of warm draft word count.

### Temperature: COLD (final) — Stability check

Read the cool draft aloud (or simulate). Flag:
- Anything that sounds wrong when spoken
- Any gap a reader would stumble on
- The one sentence that is doing the most work — verify it is correct

Ship the cold draft.

## Anti-patterns

- **Skipping HOT:** going straight to compression loses the honest layer. Annealing requires disorder first.
- **Re-heating after cold:** if the cold draft needs major revision, it wasn't ready to cool. Return to WARM, not HOT.
- **Cooling too fast:** one mega-pass of editing is quenching, not annealing. Produces brittle output.
