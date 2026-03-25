---
name: debridement
description: Remove dead code, config, and files — controlled cleanup of necrotic tissue. "debridement", "dead code", "cleanup", "remove stale", "necrotic tissue".
user_invocable: true
model: sonnet
context: fork
---

# Debridement — Removing Necrotic Tissue

Surgical debridement: remove dead, damaged, or infected tissue to allow healthy tissue to heal. Not cosmetic — necrotic tissue actively impedes healing and harbors infection.

This is different from autophagy (self-reflection, understanding what to shed) and ecdysis (molting a whole layer). Debridement is targeted surgical removal of confirmed-dead tissue.

## When to Use

- A refactor left unreachable code paths
- Config files reference services that no longer exist
- Feature flags for shipped features still in the codebase
- Commented-out code older than one sprint
- Files that exist but nothing imports or calls

## Method

### Step 1 — Identify candidates (don't remove yet)

```bash
# Dead Python code (nothing imports)
grep -rL "import module_name" --include="*.py" .

# Unreferenced config keys
# Compare config keys to actual usage in code

# Stale LaunchAgents (processes that no longer exist)
ls ~/Library/LaunchAgents/ | while read f; do
  program=$(plutil -p ~/Library/LaunchAgents/$f | grep ProgramArguments)
  echo "$f: $program"
done

# Git-tracked files with zero recent activity
git log --diff-filter=M --since="90 days ago" --name-only -- . | sort | uniq

# Commented blocks > 10 lines
grep -n "^#" --include="*.py" -r . | awk -F: '{print $1}' | uniq -c | sort -rn
```

### Step 2 — Classify each candidate

| Class | Definition | Action |
|-------|------------|--------|
| **Confirmed dead** | Nothing references it, no future use | Remove |
| **Dormant** | Nothing references it now, may be needed | Mark with `# DORMANT: reason` and date |
| **Latent** | Referenced but unreachable | Trace reference chain, then remove |

Do not remove dormant tissue without marking it. Someone planted it for a reason.

### Step 3 — Remove in atomic commits

One removal per commit. Commit message: `debridement: remove X (reason: Y)`.

Never bundle debridement with feature work. Surgical removal is traceable; bundled removal is not.

### Step 4 — Verify the organism still runs

After each removal: smoke test the affected surface. Dead code sometimes has live callers that static analysis missed.

## Debridement vs Autophagy vs Ecdysis

| Skill | Mechanism | Scope |
|-------|-----------|-------|
| autophagy | Self-reflection on what no longer serves | Conceptual, whole-system |
| ecdysis | Shedding an entire layer/interface | Large-scale, structural |
| debridement | Surgical removal of confirmed-dead tissue | Targeted, code/file level |

## Anti-patterns

- **Removing dormant as dead:** dormant tissue was intentional. Mark it, don't delete it blindly.
- **Bulk debridement:** removing 40 files in one commit. Untraceable. One removal, one commit.
- **Skipping the smoke test:** dead code sometimes has callers that compilers miss. Test after each cut.
