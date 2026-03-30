---
name: diagnose
description: System diagnosis — quick check to emergency. Severity-routed.
user_invocable: true
triggers:
  - diagnose
  - broken
  - not working
  - error
  - bug
  - debug
  - etiology
  - integrin
  - palpation
  - hemostasis
  - assay
  - experiment
context: fork
model: sonnet
---

# /diagnose

System diagnosis — quick check to emergency. Severity-routed.

## Router

| When | Sub-workflow | What it does | Doc |
|------|-------------|--------------|-----|
| Check active experiments | **assay** | Detect and probe active experiments | `assay.md` |
| Listen to logs | **auscultation** | Log patterns, error frequencies, timing | `auscultation.md` |
| Systematic diagnosis | **etiology** | Broken, stopped working, regression, error | `etiology.md` |
| Health scan | **integrin** | Receptor health — broken CLIs, dormant candidates | `integrin.md` |
| Deep probe | **palpation** | Manual deep-probe of a specific component | `palpation.md` |
| Emergency | **hemostasis** | Stop the bleeding, not fix it | `hemostasis.md` |

## How to use

1. Match the user's request to a row above
2. Read the matching doc (e.g., `assay.md` in this directory)
3. Follow the sub-workflow instructions
