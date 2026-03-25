# Enforcement Ladder

Five layers for ensuring Claude Code follows rules, in descending strength.

## The Ladder

| # | Layer | Mechanism | Type |
|---|---|---|---|
| 1 | **OS Sandbox** (macOS Seatbelt) | Kernel-enforced filesystem/network restrictions on Bash | Hard gate |
| 2 | **Hooks** (Pre/PostToolUse) | Code runs before/after every tool call; exit 2 = block | Hard gate |
| 3 | **Permission rules** (settings.json) | deny/ask/allow evaluated before tool runs; managed > project > user | Hard gate |
| 4 | **Always-in-context** (CLAUDE.md + MEMORY.md) | Model reads every turn; rules + gotchas | Soft gate |
| 5 | **On-demand context** (Skills → Vault/solutions) | Model reads when invoked or looked up | Soft gate |

Three hard gates (deterministic, can block), two soft gates (advisory, model compliance).

## Placement Heuristic

**How bad is the failure mode?**

- OS-level containment (network, filesystem scope) → sandbox config
- Destructive/irreversible tool calls → hook (exit 2)
- Tool access control (which tools, which patterns) → permission rules
- Behavioural rules the model must follow every turn → CLAUDE.md + MEMORY.md
- Domain-specific or lookup-only → skill or vault/solutions

## Hard vs Soft Gate Details

**Hard gates** are deterministic — they block regardless of model behaviour:
- **Sandbox:** Kernel-level. Bash can't escape filesystem/network restrictions even if the model tries. You don't configure this directly — it's always active.
- **Hooks:** Your code runs. `bash-guard.js` blocks `rm -rf` before the model can execute it. PreToolUse runs *before* the permission system, so hook decisions take precedence.
- **Permission rules:** Config-level. `deny` rules in settings.json are evaluated deny → ask → allow. Supports tool-specific patterns (Bash wildcards, Read/Edit gitignore patterns, WebFetch domains). Managed settings (enterprise) can't be overridden by user/project.

**Soft gates** depend on model compliance — they work most of the time but can drift under context pressure:
- **CLAUDE.md + MEMORY.md:** Both always in context. CLAUDE.md = rules ("do this"), MEMORY.md = gotchas ("this breaks"). Same enforcement strength; the split is a filing convention. MEMORY.md has a 200-line truncation risk.
- **Skills:** Only loaded on invocation. If a guard matters outside the skill's invocation path (e.g., "should I suggest X?"), duplicate to MEMORY.md.
- **Vault/solutions:** Weakest — only read on active lookup. Good for reference, not enforcement.

## Escalation Rule

**High-precision mechanical rules** (regex-matchable, near-zero false positives): Hook on first violation. Examples: tool selection (use resurface not python for session search), command flags (use --chat with wacli), dangerous operations (rm -rf without safe_rm). The deny message IS the teaching mechanism.

**Fuzzy or judgment-dependent rules** (detection is noisy or context-dependent): MEMORY.md first, hook after 2 entries in `rule-violation-log.md`. Examples: "check current state before analyzing feasibility," "don't fold to pushback without verifying."

**Key insight (Oxford council, Feb 2026):** The general-case argument for graduated enforcement (hysteresis, false positive tolerance) is weaker in our setup because hooks fire on an AI agent, not humans — no morale cost, no workaround culture, no resentment. And our hooks use high-precision regex, not noisy classifiers. Lean aggressive.

## Not in the Ladder (Niche / Enterprise)

- **`--append-system-prompt`:** Appends to base system prompt (higher priority than CLAUDE.md). Useful for CI/pipeline injection but not for interactive sessions.
- **Managed settings:** Enterprise MDM-only. `allowManagedPermissionRulesOnly`, `disableBypassPermissionsMode`, etc. Not relevant for single-developer setups.
- **Skill-scoped hooks:** Hooks in skill frontmatter that fire only during that skill's lifecycle. Niche — useful for progressive context loading.

## Anti-Pattern: Misclassifying Mechanical as Fuzzy (Feb 2026)

- `.venv/bin/python` in plist → caused 5-day silent oura-sync outage
- Claude initially pushed back on hooking: "wait for two violations" (fuzzy-rule logic)
- Wrong branch: the rule is regex-matchable (`/\.venv/` in `.plist` content) with zero false positives → mechanical → hook on first violation
- **Test:** "Can I write a regex that catches this with zero false positives?" If yes → mechanical. Don't apply fuzzy thresholds to mechanical rules.

## Example: GARP Quiz Double-Suggestion Bug (Feb 2026)

- Skill had "check before nagging" (layer 5) — only fires when quiz is invoked
- New session suggested quiz without loading skill — guard didn't fire
- Fix: added MEMORY.md entry (layer 4) to check `rai.py today` before suggesting
- Not worth a hook — no clean tool-call target (it's a recommendation, not an action)
