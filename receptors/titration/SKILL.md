---
name: titration
description: Forced-naming-as-design-constraint method — titrate a concept, a system, or architecture against biology or design patterns to surface gaps. "Titrate this", "cell completeness audit", "what are we missing", "run titration".
user_invocable: true
model: sonnet
context: fork
---

# Titration — Forced Naming as Design Constraint

Titration adds a known reagent to an unknown solution until the reaction reveals the gap. Here: biology (or design patterns) is the reagent; your system is the solution; the break IS the finding.

`/morphogenesis` does one cycle on one name. `/titration` runs the full method across an entire system.

## Three Modes

### 1. Single Concept
Same cycle as `/morphogenesis`, explicitly framed as titration.
```
NAME   → honest biological mapping (verb first, process noun)
STUDY  → 3-5 properties the biology actually has
COMPARE → which properties does the implementation have / lack?
BREAK  → where the analogy fails is the design gap, not a flaw in the method
BUILD  → implement the highest-value gap now
```
Invoke when: one component needs a name or an existing name hasn't been mined.

### 2. System Audit — Organelle Completeness
Map the system against the canonical cell organelle set. Score each: **mapped / partial / gap**.

| Organelle | Function | System equivalent | Score |
|-----------|----------|-------------------|-------|
| Membrane | Selective permeability; receptor surface | ? | |
| Nucleus | Genome; policy; canonical rules | ? | |
| ER (rough) | Translation; protein synthesis | ? | |
| Golgi | Post-processing; packaging; addressing | ? | |
| Mitochondria | Energy production; ATP; yield signal | ? | |
| Lysosomes | Degradation; quality control; recycling | ? | |
| Cytoskeleton | Shape; transport tracks; structural integrity | ? | |
| Ribosomes | Execution units; workers | ? | |
| Vacuole | Storage; buffering excess | ? | |
| Centrosome | Division coordination; timing | ? | |

Output: completed table + top 3 gaps ranked by operational impact.

### 3. Andrews 21 Patterns
Titrate against the 21 design patterns. Reference: `~/notes/Reference/andrews-21-patterns-titration.md`.
Score each pattern: **implemented / partial / absent**. Surface the highest-leverage absences.

## Key Principles

- **The break is the insight.** Where the analogy fails is not a problem — it is the finding. Mine it.
- **One abstraction level.** Cell only. Don't mix in organ-level (liver) or ecosystem-level (rainforest). Mixing levels produces decorative metaphors, not design gaps.
- **Cosplay test.** If renaming a component doesn't generate a new design question, revert. The name must do work.
- **Boundary rule.** Cell concept = bio name. Runtime mechanic = platform name. `nucleus` is a bio name; `sqlite` is a platform name. Both can coexist in the same component.

## Anti-patterns

- Stopping at the match (match = 10% of value; gap = 90%)
- Forcing a mapping that doesn't hold — the naming test IS the design test
- Running titration without committing to the output table — gaps not written down are gaps not closed
