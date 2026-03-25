category: performance-issues
tags: [agent-safety, shell-scripting, search-performance]
module: Shell Tools
date: 2026-01-27
problem_type: performance_issue
component: Shell / Agent
symptoms:
  - "Broad searches (grep/rg/find) on root or large folders hang the agent session"
  - "Unconstrained searches waste tokens and time"
root_cause: Tool Over-Permissiveness
resolution_type: shell_shadowing
severity: high
---

# Mandatory Search Guard: Shadow Binaries for Agent Safety

## Problem
Standard search tools (`grep`, `rg`, `find`) are too powerful in an agentic context. When an agent is unsure of a file's location, it often resorts to a "lazy" broad search starting from the root (`/`) or home directory (`~`). On modern systems with massive directories (like `~/Library` or `node_modules`), these searches hang the terminal session, waste tokens, and lead to timeouts.

## Solution
Implemented a "Shell-Level Gatekeeper" that shadows standard binaries using `PATH` precedence. This approach moves safety from "instruction-based" (soft) to "execution-based" (hard/unbypassable).

### 1. The Gatekeeper Logic (`agent-gate.py`)
A Python script that intercepts command-line arguments, expands paths, and validates them against a denylist.

**Key Features:**
- **Denylist Enforcement:** Blocks searches on `/`, `~`, `~/Library`, `~/Downloads`, and `~/.Trash`.
- **Massive Directory Heuristic:** Checks directory size/depth before allowing recursive searches.
- **Sentinel Passthrough:** Uses environment variables (`_AGENT_GATE_INTERNAL`) to prevent infinite recursion during execution.
- **Low Overhead:** Uses `os.execvpe` to replace the current process with the real binary, ensuring zero performance penalty after validation.

### 2. Shadowing Pattern (Installation)
The gatekeeper is installed by creating scripts or symlinks in a priority `PATH` directory (e.g., `~/bin/`).

```bash
# Example symlink pattern
ln -s ~/bin/agent-gate ~/bin/grep
ln -s ~/bin/agent-gate ~/bin/rg
ln -s ~/bin/agent-gate ~/bin/find
```

When the agent runs `grep`, it hits `~/bin/grep` first, which invokes the gatekeeper.

### 3. Clear Feedback Loop
Instead of a silent hang or generic error, the agent receives a specific failure message:
`❌ SEARCH BLOCKED: Broad search on '/Users/terry' is prohibited.`
`[SUGGESTION]: Narrow your scope: rg "pattern" ./src`

## Why This Works
1. **Unbypassable:** Unlike `CLAUDE.md` instructions which can be ignored or "forgotten" in long contexts, the shell will always execute the shadowed binary.
2. **Standard Tool Compatible:** The agent continues to use familiar tools (`grep`, `rg`) without needing to learn custom "safe" scripts.
3. **Environment Aware:** The gatekeeper can be configured per-machine or per-project.

## Related Docs
- [Slow Root Search Performance (2026-01-26)](./slow-root-search-CLITools-20260126.md) - The predecessor approach using manual script invocation.

## Prevention & Best Practices
- **Agent Middleware:** Enforce safety at the execution layer (shell/API) rather than just the prompt layer.
- **Tool Shadowing:** Wrap high-risk commands (destructive `rm`, broad `find`, network-heavy `curl`) with validation logic.
- **PATH Hygiene:** Ensure `~/bin` or `~/.local/bin` is early in the `PATH` for all agent sessions.
- **Never name custom scripts after system utilities.** `~/bin/dig` (a research script) shadowed `/usr/bin/dig` (DNS). A DNS query `dig +short pinchlime.com` silently hit the custom script instead, producing an LLM hallucination sent to Telegram. The failure mode was "plausible wrong output" — not an error — so it went undetected until the content was obviously wrong. Before creating `~/bin/<name>`, always run `which <name>` and `type <name>` to check for collisions.
