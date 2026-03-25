# Skill Architecture Decisions

Captured Feb 2026. Reference for future skill design questions.

## Flat vs Hierarchical Skills

**Decision: Keep skills flat and atomic.**

Claude Code's skill loading is flat (`~/.claude/skills/<name>/SKILL.md`). No native sub-skill support. Simulating hierarchy requires a router skill that adds a round-trip vs direct invocation.

The `-` naming convention (`linkedin-lookup`, `linkedin-research`) provides logical grouping without infrastructure.

## Token Cost of Skill Index

**Decision: Yellow zone — monitor, don't prune yet.**

- ~97 skills = ~90% of the 4K token skill budget (auto-scales at 2% of context window)
- Budget is tight but within limits; compaction is not yet driven by skill index
- CLAUDE.md and MEMORY.md remain larger contributors to context pressure
- Real levers if pressure increases: cull + `disable-model-invocation: true` on reference skills
- Wait for the pain — prune only when skill index meaningfully contributes to early compaction

## Discoverability vs Token Tradeoff

Three tiers identified — **worth acting on now given yellow-zone budget**:

1. **Must be in index:** User-invocable skills (user types `/morning`)
2. **Could remove with CLAUDE.md pointer:** Proactive reference skills (`web-search`, `research-protocol`) — one CLAUDE.md line is cheaper than a full skill entry
3. **Could remove with no pointer:** Reference skills called by other skills (`browser`, `linkedin-research`) — calling skill handles discovery

At ~97 skills (~90% budget), the cost-discoverability tradeoff is no longer trivially in favour of full inclusion. Apply tier 2/3 culls to recover headroom. Revisit threshold: next action point is if compaction visibly triggers earlier due to skill index.

## Superpowers vs CE — When to Use Which (LRN-20260305-001)

Captured Mar 2026 from vectura build session.

**CE strengths:** `learnings-researcher` + `repo-research-analyst` surface institutional gotchas in existing codebases. Worth the cost when history exists. Final review agents (security-sentinel, kieran-*-reviewer) are more thorough than superpowers' generic reviewer.

**Superpowers strengths:** Lighter on-ramp (no research agents on blank repos). Two-stage per-task review (spec compliance → code quality) is more rigorous than CE's single reviewer — catches over-building. Better for new projects.

**Routing rule (now in rector):**
- New project / fresh codebase → superpowers start to finish
- Existing codebase + in-session execution → CE research → superpowers writing-plans + subagent-driven → CE final review
- Existing codebase + external delegation → CE plan → external swarm → CE review

## Plugin Skill Overrides (LRN-20260305-002)

**CLOSED 2026-03-20. Override does NOT work.**

Plugin skills (e.g. superpowers:*) live in `~/.claude/plugins/cache/`. The plugin namespace takes precedence over `~/.claude/skills/superpowers/`. Placing a file at `~/skills/superpowers/<skill-name>/SKILL.md` does not shadow the plugin version. Claude Code reports the plugin cache path as the skill's base directory regardless.

Test: marker file at `~/skills/superpowers/subagent-driven-development/SKILL.md` was present at session load time. Invoking `/superpowers:subagent-driven-development` loaded the 12KB plugin version from cache — marker file content ("MARKER FILE — Plugin Skill Override Test") did not appear. Full test log: `~/tmp/copia-plugin-override-test-w45.md`.

**Conclusion:** To customise superpowers skill behaviour, intercept in rector before the skill is invoked. The `~/skills/superpowers/` path is not consulted for plugin-namespaced skills.

## cargo publish — Clean Working Tree Required (LRN-20260305-003)

`cargo publish` fails if there are uncommitted files, even in subdirectories (e.g. `docs/`). Commit everything before publishing. Use `--allow-dirty` only if you genuinely want to exclude files from the published crate.
