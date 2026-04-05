---
title: Execute the spec, not adjacent work
impact: HIGH
impactDescription: prevents scope creep
tags: spec
---

## Execute the spec, not adjacent work

If the spec says "create install.sh and slim down Dockerfile", do EXACTLY that. Don't write tests for unrelated modules, don't edit unrelated effectors, don't add queue items. The spec is the task. Everything not in the spec is wasted work. Read the spec's "Files changed" section — those are the ONLY files you should touch.
