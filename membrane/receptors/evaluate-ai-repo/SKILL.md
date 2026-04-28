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

**Star velocity ≠ maturity.** When a tool surfaces from a single viral tweet (5k+ stars in <30 days, repo <2 months old), the star count is a hype signal, not an adoption signal. Run the maintainer-health gate first — if it fails, every downstream test is wasted effort. 2026-04-27 case: Obscura headless browser, 5,713 stars in 14 days, 1 real maintainer + 4 drive-by PRs, all commits on a single day post-tweet. Stealth claim and Turnstile bypass both failed on first contact. See `chromatin/Obscura - Rust Headless Browser for AI Agents.md`.

**Cherry-pick infrastructure, skip philosophy:**
- ✅ Adopt: Hooks, tools, utilities (plumbing)
- ❌ Skip: Learning systems, workflow patterns (philosophy you've already customized)

## Workflow

### -1. Source-Grounded Claims Gate (HARD, runs before every gap or capability claim)

**Before listing ANY weakness, gap, or limitation of the tool, you must be able to cite the specific source line that grounds it.** Format every gap as:

> Per `<file>:<line>` (or README §<heading>, or CHANGELOG entry), the tool does/doesn't do X.

If you can't cite, don't list. Speculation about what tools "typically lack" populated from training-era category priors is not a gap claim — it's a hypothesis that needs grounding before it leaves your output.

**Absolute ban — match and refuse:**

If you find yourself producing a numbered or bulleted list of gaps without source citations, **STOP**. Read the README + CHANGELOG + relevant source file first. Re-list only what you can cite.

**Why this gate exists.** Failure mode confirmed across 9+ retrospectives in 24 hours (28 Apr 2026): CC produces gap lists from category priors ("RAG tools generally chunk by fixed size", "small embedding models lack X", "MCP servers usually don't support HTTP"), then has to retract when actual source is read. Marks alone (`feedback_verify_tool_existence_before_denying.md`, `finding_claim_gaps_without_source_reading.md`) have not deterred recurrence. This gate fires at the trigger — when the skill is entered for tool evaluation — instead of relying on Terry's challenge to catch it.

Same rule applies in reverse to capability claims ("the tool supports X") — verify before asserting. The genome's "Tool behavior: NEVER state how tools/flags/infra work without verifying docs/source first" already covers this; the bidirectional gate here is its skill-level operationalisation.

**DO:**
- Open README, CHANGELOG, key source files BEFORE drafting the eval.
- Quote the line that grounds each claim. Inline if short, by reference (`store.js:54-67`) if not.
- When a claim cannot be sourced, mark it as "speculation" and verify before promoting.

**DO NOT:**
- Produce category-prior gap lists. "Tools in this category usually X" is not "this tool does X."
- Treat absence-of-mention as evidence-of-absence. README silence ≠ feature absence — grep the source.
- Defer source-reading to "when the user asks for proof." Read first, list second.

### 0. Maintainer-Health Gate (run first, fail fast)

For tools that surfaced from viral content (Twitter/HN/LinkedIn frenzy), gate before cloning:

```bash
curl -sL https://api.github.com/repos/OWNER/REPO | python3 -c "import json,sys; d=json.load(sys.stdin); print('age_days:', (__import__('datetime').datetime.now() - __import__('datetime').datetime.fromisoformat(d['created_at'].rstrip('Z'))).days); print('stars:', d['stargazers_count']); print('archived:', d['archived'])"
curl -sL "https://api.github.com/repos/OWNER/REPO/contributors?per_page=30" | python3 -c "import json,sys; d=json.load(sys.stdin); print('contribs_with_2plus_commits:', sum(1 for c in d if c['contributions']>=2))"
curl -sL "https://api.github.com/repos/OWNER/REPO/commits?per_page=30" | python3 -c "import json,sys; d=json.load(sys.stdin); dates=[c['commit']['author']['date'][:10] for c in d]; print('commit_date_spread:', len(set(dates)), 'distinct days'); print('newest:', dates[0], 'oldest:', dates[-1])"
```

**Fail any:**
- `contribs_with_2plus_commits < 3` (solo-maintainer cliff)
- `commit_date_spread <= 1 day` (hype-driven burst, no sustained work)
- `age_days < 30 AND stars > 5000` (pure viral signal, not validated adoption)
- `archived == true`

→ KEEP REJECTED, schedule a 3-month re-assay via `/schedule`. Don't waste cycles testing claims of a tool that may not exist in 6 weeks.

### 1. Test the Headline Claim Before the Diff

If the tool's pitch is one specific capability (e.g., "bypasses Cloudflare Turnstile," "10x faster than X," "drop-in replacement"), test that claim against the canonical adversarial benchmark FIRST, before mapping components or considering integration. A failed claim test invalidates everything downstream.

For browser/scraping tools: `bot.sannysoft.com` (detection table), `nowsecure.nl` (Cloudflare Turnstile). For LLM frameworks: a known-hard prompt or eval. For perf claims: re-measure on real targets, not the author's chosen benchmark.

### 2. Clone and Explore

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
