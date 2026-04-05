---
title: Mock where looked up, not defined
impact: HIGH
impactDescription: test passes locally, fails in CI
tags: code
---

## Mock where looked up, not defined

Read imports first. `import subprocess` at top = patch `<module>.subprocess`.
