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

## Split with evergreen

**Evergreen** (daily cron, deterministic): version bumps for CC, uv, ruff, Rust, npm globals, ganglion sync. No judgment needed — if latest > current, upgrade.

**Competence** (manual/monthly, judgment): feature adoption. Read changelogs, evaluate fit, design integrations, dispatch implementation. This is the part that needs CC.

If a version bump introduces a new FEATURE worth adopting, evergreen installs the version but competence decides whether to use the feature.

## 7. External skill drift detection (endosymbionts)

Skills imported from external repos (`endosymbiont: true` in frontmatter) need monitored drift. Manual "clone from time to time" is the failure mode — fragile, forgettable, doesn't scale to N vendored skills.

### Skill frontmatter contract

Every endosymbiont skill must declare:

```yaml
endosymbiont: true
upstream: <org>/<repo>             # e.g. run-llama/llamaparse-agent-skills
upstream_path: <path/in/repo>      # e.g. skills/llamaparse
upstream_commit: <12-char SHA>     # SHA at time of last sync
upstream_check: YYYY-MM-DD         # date of last drift check
upstream_license: <SPDX>           # for license compliance
```

The active `SKILL.md` body is upstream content verbatim, followed by a `<!-- VIVESCA OVERLAY -->` HTML comment marker, followed by our additions. Drift detection diffs only the upstream-managed lines (above the marker).

A pristine `SKILL.md.upstream` sibling file holds the last-synced upstream content for byte-level diff.

### Drift sweep procedure

Run as part of monthly `/competence` cycle, or ad-hoc when an upstream is known to have changed:

```bash
# Walk all endosymbiont skills
for skill in ~/germline/membrane/receptors/*/SKILL.md; do
  awk '/^endosymbiont: true/{print FILENAME; exit}' "$skill"
done | while read skill; do
  dir=$(dirname "$skill")
  upstream=$(awk -F': ' '/^upstream:/{print $2; exit}' "$skill")
  upstream_path=$(awk -F': ' '/^upstream_path:/{print $2; exit}' "$skill")
  current_commit=$(awk -F': ' '/^upstream_commit:/{print $2; exit}' "$skill")
  latest_commit=$(curl -s "https://api.github.com/repos/$upstream/commits?path=$upstream_path&per_page=1" | python3 -c "import json,sys; c=json.load(sys.stdin); print(c[0]['sha'][:12] if c else 'none')")
  if [ "$current_commit" != "$latest_commit" ]; then
    echo "DRIFT: $skill — $current_commit → $latest_commit"
  fi
done
```

### Adoption decision per drift

For each detected drift:

1. **Fetch new upstream content.** Save as `SKILL.md.upstream.new`.
2. **Diff `.upstream` vs `.upstream.new`.** Read the changes — what did upstream actually change?
3. **Classify the delta:**
   - **Auto-apply candidate:** description/trigger updates, dep version bumps, additional examples, license clarifications. Low risk.
   - **Review-required:** logic changes, new tool args, breaking API changes, removed sections, license changes. High risk.
4. **Apply.** Replace upstream-managed body in active SKILL.md with new upstream content. Preserve frontmatter additions and the post-`<!-- VIVESCA OVERLAY -->` section verbatim. Update `upstream_commit:` and `upstream_check:` frontmatter fields.
5. **Replace `.upstream`** with `.upstream.new` so next drift check has clean baseline.
6. **Commit** with message `<skill> drift sync: <old-sha> → <new-sha> (<changeset summary>)`.

### When NOT to sync

- **Major version bump** that breaks our overlay or downstream callers — pin to last-known-good SHA, log as deferred, plan migration explicitly.
- **License change** away from permissive — stop. Consult Terry. Possibly fork pre-change SHA permanently.
- **Upstream archived / deleted** — fork the last good commit into our repo, mark `endosymbiont: vendored` (no further drift checks).

### What this section is NOT for

- First-party MCP servers (those live in `vivesca` and have their own version pinning).
- Skills we wrote from scratch — those are organism-native, not endosymbionts.
- Coaching files / marks / epistemics — those follow the marks-decay pattern, not upstream-tracking.

---

## Related skills

- `integrin` — scans for breakage (health), not growth (competence)
- `autopoiesis` — self-repair loop, not capability absorption
- `evergreen` — version bumps (cron), not feature adoption (judgment)
- `histology` — architecture audit, not environmental scanning
