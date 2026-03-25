# /xlfg External Swarm Learnings

## Gotcha 1: Commit the plan before creating worktrees

Plans written to the main working tree (uncommitted) are NOT visible in worktrees — worktrees share git history, not the working directory. Delegates fall back to finding old plans.

**Fix:** Commit the plan immediately after `/ce:plan` writes it, BEFORE `lucus new`:
```bash
cd <repo> && git add docs/plans/<plan>.md && git commit -m "plan: <feature>"
# THEN: lucus new <branch>
```

Or: copy the plan file into each worktree manually after creation.

## Gotcha 2: OpenCode sandbox blocks writes outside its worktree

OpenCode's sandbox only allows writes to its worktree dir + /tmp. Any delegate task that writes to `~/skills/`, `~/.config/`, or any other path outside the worktree will be auto-rejected.

**Implication:** Docs/skill updates that live outside the repo cannot be delegated to OpenCode. Do them in-session or use Codex (which has broader sandbox permissions).

## Gotcha 3: Worktrees don't inherit uncommitted files from main working tree

Any file created/modified in the main worktree after the branch point (uncommitted) is invisible to sibling worktrees. Only committed history is shared.

**Pattern:** /xlfg workflow should be:
1. `/ce:plan` → plan written to `docs/plans/`
2. **`git commit` the plan**
3. `/deepen-plan` → enhances plan
4. **`git commit` the deepened plan**
5. THEN `lucus new` per task
