---
name: audit
description: Architecture inspection — review, layout, naming, evidence. Scope-routed.
user_invocable: true
triggers:
  - audit
  - review
  - architecture
  - naming
  - histology
  - karyotyping
  - cytometry
  - debridement
  - autopoiesis
  - histochemistry
context: fork
model: sonnet
---

# /audit

Architecture inspection — review, layout, naming, evidence. Scope-routed.

## Router

| When | Sub-workflow | What it does | Doc |
|------|-------------|--------------|-----|
| Architecture review | **histology** | Map components via cell biology lens | `histology.md` |
| Visual layout | **karyotyping** | Arrange components to find structural anomalies | `karyotyping.md` |
| Autonomy audit | **cytometry** | Classify subsystems as self-governing or gated | `cytometry.md` |
| Naming sweep | **debridement** | Sweep for naming violations and stale references | `debridement.md` |
| Self-creation cycle | **autopoiesis** | Detect, repair, learn, grow, design | `autopoiesis.md` |
| Evidence check | **histochemistry** | Evidence before completion claims | `histochemistry.md` |

## How to use

1. Match the user's request to a row above
2. Read the matching doc (e.g., `histology.md` in this directory)
3. Follow the sub-workflow instructions
