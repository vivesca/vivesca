---
name: codex-delegate
description: Delegate complex coding tasks to Codex (GPT-5.2-codex). Paid escalation for hard bugs.
user_invocable: false
---

# Codex Delegate

Delegate complex coding tasks to Codex (GPT-5.2-codex) — OpenAI's coding-optimized model.

## Delegation Tiers

| Complexity | Delegate to | Model | Cost |
|------------|-------------|-------|------|
| Routine (bulk reads, refactoring, boilerplate) | OpenCode | GLM-4.7 | Free |
| **Complex (hard bugs, architecture, features)** | **Codex** | **GPT-5.2-codex** | **Paid** |
| Judgment (planning, review, user interaction) | Claude Code | Opus 4.5 | Subscription |

## When to Use Codex

- **Hard debugging**: Subtle bugs, race conditions, off-by-one errors
- **Complex features**: Multi-file changes with tricky logic
- **Architecture decisions**: Design patterns, refactoring strategies
- **When OpenCode fails**: GLM-4.7 couldn't solve it after 2-3 attempts
- **Code review**: Deep analysis of complex code

## When NOT to Use

- Routine file operations → use OpenCode (free)
- Simple refactoring → use OpenCode
- Tasks needing vault/personal context → stay in Claude Code
- Quick questions → just ask Claude Code

## Commands

### Run task (non-interactive)

```bash
codex exec --skip-git-repo-check "Your detailed prompt here"
```

### Run in a specific directory

```bash
cd /path/to/project && codex exec "Your prompt"
```

### Run with output to file

```bash
codex exec --skip-git-repo-check -o /tmp/codex-output.txt "Your prompt"
```

### Pipe context in (antirez pattern)

```bash
cat /tmp/context.txt | codex exec -o /tmp/reply.txt "Analyze and fix the bug"
```

## Prompt Engineering for Codex

Codex excels when given **complete context**. Include:

1. **The problem**: What's broken or what needs building
2. **Relevant code**: Full functions/files, not snippets
3. **What you've tried**: Failed approaches (saves Codex from repeating)
4. **Specific ask**: "Find the bug" vs "Implement feature X"

### Example: Debug Prompt

```
I have an off-by-one error in the token parser.

File: src/parser.ts (lines 45-120)
[paste full code]

Symptoms:
- Last token gets truncated by 1 character
- Only happens when input ends without newline

Tried:
- Adding +1 to end index (made it worse)
- Checking boundary condition at line 78 (seems correct)

Find the bug and explain the fix.
```

### Example: Feature Prompt

```
Add WebSocket support to the chat server.

Current architecture:
- Express server in src/server.ts
- Message handling in src/handlers/messages.ts
- Client state in src/state.ts

Requirements:
1. Broadcast messages to all connected clients
2. Handle client disconnect gracefully
3. Keep existing REST endpoints working

Create the implementation with tests.
```

## Background Execution

For long tasks, background it:

```bash
codex exec --skip-git-repo-check "Complex task..." &
```

Then check output file or resume the session.

## Model Info

Codex uses `gpt-5.2-codex` by default (per ~/.codex/config.toml):
- Optimized for software engineering
- Strong at debugging, architecture, complex features
- Reasoning effort configurable (low/medium/high)

Override model if needed:
```bash
codex exec -c model="o3" "Use o3 for this task"
```

## MCP Servers Available

Codex has the same MCP servers as Claude Code:
- context7 (library docs)
- perplexity (search, research, reasoning)

Note: MCP availability may differ from Claude Code. Check `codex` config for current list.

## Cost Awareness

Codex uses OpenAI API credits. Use judiciously:
- **Routine work** → OpenCode (free GLM-4.7)
- **Hard problems** → Codex (paid but smarter)

Check token usage in output — Codex shows `tokens used` at end.

## Integration with Claude Code

The workflow:

```
Claude Code hits a hard problem
  → Recognize it's complex (debugging wall, architecture question)
  → Prepare detailed context (code, symptoms, attempts)
  → Delegate to Codex: codex exec "..."
  → Review Codex's solution
  → Apply fix in Claude Code (verify, test)
```

## Compared to OpenCode

| Aspect | OpenCode (GLM-4.7) | Codex (GPT-5.2-codex) |
|--------|-------------------|----------------------|
| Cost | Free (unlimited) | Paid (API credits) |
| Speed | ~15s startup (lean) | ~10s startup |
| Strength | Bulk ops, refactoring | Deep debugging, complex features |
| Context | No vault access | No vault access |
| MCP | Optional | Full MCP suite |
| When | Default delegation | Escalation for hard tasks |

## Session Management

```bash
# Resume last session
codex resume --last

# List recent sessions
codex resume  # opens picker

# Fork a session (continue from checkpoint)
codex fork --last
```
