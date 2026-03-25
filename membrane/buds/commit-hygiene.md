---
name: commit-hygiene
description: Review recent commits for quality — message clarity, scope, unintended changes.
model: sonnet
tools: ["Bash", "Read", "Grep"]
---

Audit recent commits across vivesca repos.

1. Read recent commits:
   ```bash
   cd ~/code/vivesca && git log --oneline -20
   ```

2. For each commit, check:
   - Message follows conventional commit format? (type(scope): description)
   - Scope matches actual files changed? (don't claim hooks when only docs changed)
   - Any unintended files committed? (credentials, .env, large binaries)
   - Commit is atomic? (one logical change, not three mixed together)

3. Check for unsigned commits, missing Co-Authored-By, or --no-verify usage

4. Output: hygiene score (clean / needs attention / problems found)
   - List any commits that should be noted or fixed

Weekly cadence. Keeps the git history honest.
