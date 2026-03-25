---
module: Claude Configuration
date: 2026-02-04
problem_type: best_practice
component: tooling
symptoms:
  - "Wanted queryable knowledge base for AI workflow learnings"
  - "Every's compound-engineering plugin assumed Rails project structure"
  - "learnings-researcher agent couldn't find solutions without docs/solutions/"
root_cause: config_error
resolution_type: workflow_improvement
severity: medium
tags: [compound-engineering, setup, knowledge-base, learnings-researcher, schema-adaptation]
---

# Setting Up Compound Engineering for Personal Workflows

## Problem

The compound-engineering plugin from Every provides powerful knowledge compounding — each solved problem makes future problems easier via the `learnings-researcher` agent. However, it assumes:

1. A Rails project structure with specific component types
2. `docs/solutions/` exists in the project root
3. YAML frontmatter uses Rails-specific enums

For a personal workflow (AI tooling, browser automation, skill development), these assumptions don't fit.

## Solution

### 1. Adapt the Schema

Create `docs/solutions/schema.md` with enums that match your work:

**Components:**
- `claude_code` — Claude Code CLI, settings, hooks
- `browser_automation` — Playwright, agent-browser, Chrome
- `mcp_server` — MCP tools and servers
- `skill` — Skill definitions and routing
- `cli_tool` — wacli, gog, bird, gh, etc.
- `vault` — Obsidian vault, notes
- `delegation` — OpenCode, Codex delegation
- `search` — Grep, Glob, file discovery
- `api` — External API quirks

**Problem types:** Keep the original set, they're generic enough.

**Root causes:** Adapt to your failure modes:
- `wrong_api`, `config_error`, `async_timing`, `permission_issue`
- `tool_limitation`, `missing_context`, `mental_model_error`

### 2. Create Directory Structure

```bash
mkdir -p ~/docs/solutions/{ai-tooling,browser-automation,claude-config,skills,workflow-issues,best-practices,patterns}
```

### 3. Handle Existing Structure

**Gotcha:** If `~/docs` is a broken symlink, `mkdir -p` fails silently.

```bash
# Check first
file ~/docs
# If broken symlink, remove it
rm ~/docs
# Then create
mkdir -p ~/docs/solutions/...
```

**Gotcha:** If `~/agent-config/docs/` already exists (from earlier work), merge rather than replace:

```bash
cp -r ~/docs/solutions/* ~/agent-config/docs/solutions/
rm -rf ~/docs
ln -s ~/agent-config/docs ~/docs
```

### 4. Create Critical Patterns File

`docs/solutions/patterns/critical-patterns.md` should contain hard rules that apply to ALL work. The `learnings-researcher` always checks this file.

Extract from your existing mistakes log — things that should never happen.

### 5. Seed Initial Learnings

Convert high-value entries from your mistakes log into structured solution files. Focus on:
- Problems that recur
- Non-obvious solutions
- Patterns that apply beyond one case

### 6. Symlink for Path Compatibility

The `learnings-researcher` searches `docs/solutions/` relative to working directory. If you work from `~`:

```bash
ln -s ~/agent-config/docs ~/docs
```

Now `~/docs/solutions/` works regardless of cwd.

### 7. Test the Integration

Invoke the `learnings-researcher` directly:

```
Task: Search for browser automation learnings
Agent: compound-engineering:research:learnings-researcher
```

Should return structured results from your solutions directory.

### 8. Update CLAUDE.md

Add workflow selection guide so you know when to use each command:

| Workflow | When to Use |
|----------|-------------|
| `/workflows:brainstorm` | Unclear requirements |
| `/workflows:plan` | Clear goal, need HOW |
| `/deepen-plan` | Plan needs research depth |
| `/workflows:work` | Plan approved, execute |
| `/workflows:review` | Code complete, quality check |
| `/workflows:compound` | Just solved something tricky |

## Prevention Checklist

Before setting up compound-engineering in a new environment:

- [ ] Check for existing `docs/` directory or symlink (`file ~/docs`)
- [ ] If symlink exists, check if broken (`ls -la ~/docs/`)
- [ ] Decide: separate repo or merge into existing config repo
- [ ] Adapt schema enums for your domain (not Rails-specific)
- [ ] Create critical-patterns.md with hard rules
- [ ] Test learnings-researcher finds your solutions
- [ ] Document workflow selection in CLAUDE.md

## Verification

Confirm setup works:

1. `ls ~/docs/solutions/` shows your categories
2. `learnings-researcher` returns structured results
3. `/workflows:plan` auto-checks for relevant learnings
4. `/workflows:compound` creates properly formatted entries

## Related

- [[Compound-Engineering-Lessons]] in vault
- `~/agent-config/CLAUDE.md` — workflow selection guide
- Every's compound engineering article: https://every.to/source-code/compound-engineering
