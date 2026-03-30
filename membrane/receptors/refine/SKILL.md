---
name: refine
description: Iterative improvement — polish, anneal, stress-test. Mode-routed.
user_invocable: true
triggers:
  - refine
  - polish
  - review
  - stress-test
  - modification
  - annealing
  - proofreading
context: fork
model: sonnet
---

# /refine

Iterative improvement — polish, anneal, stress-test. Mode-routed.

## Router

| When | Sub-workflow | What it does | Doc |
|------|-------------|--------------|-----|
| Multi-model polish | **modification** | Iterative refinement of artifacts | `modification.md` |
| Hot-to-cool convergence | **annealing** | Start wild, cool to convergence | `annealing.md` |
| Stress-test | **proofreading** | Find strongest counterarguments and failure modes | `proofreading.md` |

## How to use

1. Match the user's request to a row above
2. Read the matching doc (e.g., `modification.md` in this directory)
3. Follow the sub-workflow instructions
