---
name: delegation-reference
description: Reference for AI tool delegation routing, commands, and effective prompting. Consult when deciding which tool to delegate to.
user_invocable: false
---

# Delegation Reference

Claude orchestrates, delegates execute. Match task complexity to the right tool.

## Routing Table

| Complexity | Delegate to | Model | Cost | Use for |
|------------|-------------|-------|------|---------|
| Routine | OpenCode | GLM-5 | Free | Bulk ops, refactoring, tests, boilerplate |
| Complex | Codex | GPT-5.2-codex | Paid | Hard bugs, complex features, architecture |
| Complex | Cursor Agent | GPT-5, Sonnet-4 | Free/Subscription | Complex tasks, MCP integration |
| Judgment | Claude Code | Opus 4.5 | Subscription | Planning, review, vault access, user interaction |

## Decision Flow

```
Task arrives
  │
  ├─ Routine? (bulk files, refactoring, tests)
  │   → OpenCode (free, unlimited)
  │
  ├─ Complex? (hard bugs, multi-file features, architecture)
  │   → Cursor Agent (GPT-5, Sonnet-4) or Codex (paid escalation)
  │
  └─ Needs judgment/context? (planning, vault, user decisions)
      → Stay in Claude Code
```

## OpenCode (Default Delegation)

GLM-5 via BigModel — free and unlimited (Coding Max plan).

**Delegate:** Reading/writing files, bash/git, refactoring, cleanup, tests, docs, boilerplate, codebase exploration.

**Command:**
```bash
OPENCODE_HOME=~/.opencode-lean opencode run -m zhipuai-coding-plan/glm-5 --title "Task" "prompt"
```

See `delegate` skill for details.

## Codex (Escalation for Hard Tasks)

GPT-5.2-codex — paid but significantly smarter for complex engineering.

**Escalate when:** OpenCode failed 2-3 times, deep debugging, complex multi-file features, architecture decisions.

**Command:**
```bash
codex exec --skip-git-repo-check "Detailed problem description with full context"
```

See `codex-delegate` skill for details.

## Cursor Agent (Alternative for Complex Tasks)

GPT-5, Sonnet-4 — free/subscription tier with MCP server support.

**Use when:** Complex tasks requiring MCP integration, OpenCode failed 2-3 times, want GPT-5 or Sonnet-4.

**Command:**
```bash
agent --print "Detailed prompt with full context"
```

Plan mode: `agent --plan "Planning task"`

## Claude Code (Orchestrator)

Claude only does: User interaction, delegation decisions, reviewing output, judgment calls, vault/personal context.

## Effective Task Delegation

Five elements for a good delegation prompt (from Ethan Mollick's [Management as AI Superpower](https://www.oneusefulthing.org/p/management-as-ai-superpower)):

1. **Goal & motivation** — What to achieve and why
2. **Boundaries** — What's allowed vs. off-limits
3. **Acceptance criteria** — Definition of "done"
4. **Intermediate checkpoints** — Show outline/draft before full execution
5. **Self-check list** — What to verify before submitting

**Self-verification pattern:** Where possible, give the agent a way to verify its own work (test commands, API keys for validation, expected outputs). This eliminates a round-trip of human inspection.
