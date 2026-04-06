---
name: competence
description: Periodic stack improvement — scan environment for new capabilities and adopt them. CC changelog, tool updates, MCP spec changes. "upgrade stack", "what's new", "check changelog", "competence"
effort: high
epistemics: [systematic-evaluation, decision-under-uncertainty]
---

# competence

**Biology:** GO:0030420 — establishment of competence for transformation. The process by which a naturally transformable bacterium acquires the ability to take up exogenous DNA from its environment and integrate it into its genome.

**Organism:** Scan the tool environment (CC changelog, Python/uv/ruff releases, MCP spec, Temporal) for new capabilities. Evaluate each for fit. Adopt the valuable ones. The organism becomes "competent" — able to absorb improvements from its surroundings.

## When to invoke

- Monthly (pair with `/monthly`)
- After CC version bumps (evergreen cron upgrades CC daily — features land silently)
- When Terry says "what's new", "upgrade stack", "check changelog"
- When a workflow feels unnecessarily manual and a newer feature might automate it

## Procedure

### 1. Inventory current versions

```bash
claude --version                    # CC version
uv --version                       # Python tooling
ruff --version                     # Linter
ssh ganglion "claude --version"    # Ganglion CC version
temporal --version 2>/dev/null     # Temporal CLI (if installed)
```

### 2. Scan changelogs

Sources, in priority order:

| Source | How to fetch | Signal |
|--------|-------------|--------|
| CC changelog | `gh api repos/anthropics/claude-code/contents/CHANGELOG.md -H "Accept: application/vnd.github.raw" \| head -500` | New hook events, env vars, CLI flags, performance fixes |
| CC docs | `gh api repos/anthropics/claude-code/contents/docs -H "Accept: application/vnd.github.raw"` | New tool capabilities, API changes |
| uv changelog | `gh api repos/astral-sh/uv/releases/latest --jq .body \| head -200` | New commands, workflow improvements |
| ruff changelog | `gh api repos/astral-sh/ruff/releases/latest --jq .body \| head -200` | New rules, formatter changes |
| MCP spec | `gh api repos/modelcontextprotocol/specification/releases/latest --jq .body` | Protocol changes affecting vivesca MCP |

### 3. Filter for adoption candidates

For each new feature, apply this decision tree:

```
Does it solve a current friction point?
  YES → high priority, adopt now
  NO  → Does it enable a new capability we'd use weekly?
          YES → medium priority, design first
          NO  → skip (don't adopt for novelty)
```

**Adoption signals** (at least one must be true):
- Replaces a workaround we currently maintain
- Reduces token usage or latency measurably
- Adds a safety gate we're currently missing
- Enables a workflow that's currently manual

**Anti-signals** (skip if true):
- Only relevant to platforms we don't use (Windows, VS Code, Bedrock)
- Already covered by an organism tool
- Requires infrastructure we don't have

### 4. Design adoptions

For each candidate:

1. **Assess blast radius:** config change (low) vs code change (medium) vs architecture change (high)
2. **Check compatibility:** does it conflict with existing hooks, env vars, or workflows?
3. **Write a one-line spec** per adoption: what changes, where, expected effect
4. **Batch by blast radius:** ship config changes immediately, dispatch code changes to ribosome

### 5. Implement

- Config changes (settings.json, env vars): CC-direct
- Skill frontmatter updates: CC-direct
- Code changes (hooks, scripts, effectors): dispatch via `mtor` with spec files
- After implementation: verify with a smoke test

### 6. Record

Update the competence mark (`~/epigenome/marks/finding_competence_last_scan.md`):
- Date of scan
- CC version scanned up to
- Features adopted (with commit hashes)
- Features skipped (with reason)

This prevents re-scanning the same changelog entries next time.

## What NOT to do

- Don't adopt features just because they're new
- Don't change working workflows to use "the new way" unless the new way is measurably better
- Don't scan every dependency — focus on the 5 tools that matter (CC, uv, ruff, Temporal, MCP spec)
- Don't block on low-priority adoptions — batch them for the next cycle

## Related skills

- `integrin` — scans for breakage (health), not growth (competence)
- `autopoiesis` — self-repair loop, not capability absorption
- `evergreen` — version bumps (cron), not feature adoption (judgment)
- `histology` — architecture audit, not environmental scanning
