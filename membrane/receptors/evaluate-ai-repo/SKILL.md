---
name: evaluate-ai-repo
description: Evaluate AI tooling repos (configs, MCP servers, agent frameworks) for adoption. Use when deciding "should I adopt this?" for AI tools. "evaluate repo", "should I use this"
user_invocable: true
---

# Evaluate AI Tooling Repo

Systematic evaluation of AI tooling repos for adoption into a mature, personalized setup.

## When to Use

- Discovered a popular Claude Code config repo (like everything-claude-code)
- Found an MCP server collection to evaluate
- Considering agent frameworks or plugins
- Any "should I adopt this?" decision for AI tooling

## Philosophy

**39k GitHub stars ≠ value for you.** Popular repos are optimized for general users. Your personalized setup may already be better for your specific workflow.

**Cherry-pick infrastructure, skip philosophy:**
- ✅ Adopt: Hooks, tools, utilities (plumbing)
- ❌ Skip: Learning systems, workflow patterns (philosophy you've already customized)

## Workflow

### 1. Clone and Explore

```bash
git clone <repo-url> ~/repo-name
ls ~/repo-name
```

Read the guides/README first to understand their philosophy.

### 2. Map to Your Setup

Create a comparison table:

| Their Component | Your Equivalent | Gap? |
|-----------------|-----------------|------|
| (list items)    | (what you have) | Y/N  |

Focus on **gaps** — components you don't have that fill a real need.

### 3. Identify Conflicts

Watch for:
- **Split brain risk**: Two systems doing the same thing (e.g., their Instincts + your Obsidian)
- **Hook collisions**: Multiple hooks firing on same event
- **Architecture mismatch**: Their patterns assume vanilla setup, yours is customized

### 4. Evaluate with Context

Consider your current situation:
- Job hunting? → Freeze architectural changes
- Stable? → Safe to experiment
- Demo-critical project? → Don't touch working systems

### 5. Priority Order

1. **Zero-risk adoptions first** — Documentation patterns, aliases, standalone tools
2. **Infrastructure next** — Hooks, formatters, linters (low coupling)
3. **Philosophy last** — Only if fills genuine gap, not just novelty

### 6. Test Before Committing

For hooks and integrations:
```bash
# Dry run or test in isolated worktree
git worktree add ../test-branch test
cd ../test-branch
# Test the new component
```

### 7. Create Sync Skill

If repo is actively maintained, create a `/sync-*` skill to track updates:

```markdown
# Workflow
1. git pull
2. Review changelog
3. Cherry-pick improvements
```

## Red Flags

- Component requires restructuring your existing setup
- "All or nothing" architecture (can't cherry-pick)
- Overlaps significantly with what you already have
- Maintenance burden exceeds benefit

## Green Flags

- Fills a genuine gap (e.g., PreCompact hook when you only have manual WORKING.md)
- Architecture-agnostic (works regardless of your setup)
- Low coupling (can disable without breaking other things)
- Verifiable claims (e.g., "50% token reduction" — benchmark it)

## Output

After evaluation, create:
1. **Decision record** in `~/epigenome/chromatin/Decisions/` with rationale
2. **Learning** in `~/docs/solutions/` or `MEMORY.md` if non-obvious insights
3. **Sync skill** if repo worth tracking long-term

## Example: everything-claude-code

**Adopted:**
- PreCompact hook (fills gap in session continuity)
- PostToolUse hooks (100% reliable formatting)
- mgrep (semantic search, verified token reduction)

**Skipped:**
- Instincts/CLv2 (split brain with Obsidian)
- SessionStart hook (conflicts with WORKING.md)
- Generic rules (already have better in CLAUDE.md)

## Meta-Lesson

A repo optimized for everyone may be less valuable than a setup optimized for you. Adopt surgically, not wholesale.
