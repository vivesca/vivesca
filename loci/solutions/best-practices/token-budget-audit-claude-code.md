---
module: GLOBAL
date: 2026-02-07
problem_type: best_practice
component: claude_code
symptoms:
  - "Sessions feel slow or expensive without obvious cause"
  - "Context window fills up faster than expected"
  - "System prompt is bloated with rarely-used reference material"
root_cause: missing_context
resolution_type: process_change
severity: medium
tags: [token-optimization, claude-code, system-prompt, plugins, claude-md]
related_files:
  - ~/CLAUDE.md
  - ~/epigenome/chromatin/CLAUDE.md
  - ~/.claude.json
  - ~/.claude/plugins/installed_plugins.json
  - ~/skills/delegation-reference/SKILL.md
  - ~/skills/dev-workflow-reference/SKILL.md
  - ~/skills/web-search/SKILL.md
---

# Token Budget Audit for Claude Code

## Problem

Claude Code sessions carry significant hidden token overhead from the system prompt — CLAUDE.md, git status, MCP server instructions, plugin tools, and skill descriptions. This overhead is paid on every turn, compounding across a session. Without auditing, it's easy to accumulate 10,000+ wasted tokens per session.

**2026-02-07 audit result: ~14,000+ tokens/session saved** across 8 categories: git status (~2,000), CLAUDE.md extraction (~2,400), vault CLAUDE.md trimming (~2,300), search MCP consolidation (~3,300 from 12 removed tool defs), plugin removal (~2,500+ from 6 plugins), Serena plugin (~800), skill audit/removal (~3,200 from 8 skills), skill description shortening (~500).

## Audit Checklist

### 1. Git Status at Home Directory (~2,000 tokens)

**Check:** Is `~` a git repo? If so, does it serve a purpose?

```bash
cd ~ && git log --oneline -5 && git remote -v
```

If no commits and no remotes, it's vestigial. `rm -rf ~/.git` eliminates the massive untracked-files blob from every session's system prompt. If it IS needed, add a `.gitignore` that excludes everything except tracked files.

### 2. CLAUDE.md Reference Bloat (~2,400 tokens saved)

**Principle:** CLAUDE.md should contain context, rules, and behavioral instructions. Reference material (tables, command syntax, decision trees) should live in non-user-invocable skills loaded on demand.

**Extract candidates:**
- Routing tables (delegation tiers, tool priority chains)
- Command syntax blocks (individual tool commands)
- Workflow selection guides
- Review agent tables
- Detailed process documentation (solutions KB structure, git worktree setup)

**Technique:** Create `user_invocable: false` reference skills. Each adds ~1 line to the skill list but removes 50-100 lines from CLAUDE.md. Replace extracted sections with 1-2 line pointers: "See `skill-name` skill for details."

**Test:** Before and after token count:
```python
import tiktoken
enc = tiktoken.encoding_for_model('gpt-4')
text = open('CLAUDE.md').read()
print(f'{len(enc.encode(text))} tokens')
```

### 3. Unused Plugins (~800+ tokens each)

**Check:** List installed plugins and evaluate usage:

```bash
cat ~/.claude/plugins/installed_plugins.json | python3 -c "
import json, sys
d = json.load(sys.stdin)
for name in d.get('plugins', {}):
    print(name)
"
```

Each plugin injects: tool descriptions + MCP server instructions + tool definitions. Plugins with verbose instructions (Serena: ~800 tokens + 30 tool defs) add up fast.

**Decision criteria for removal:**
- Do you use this plugin's unique capabilities weekly?
- Are the capabilities covered by native Claude Code tools?
- Can it be reinstalled quickly if needed later?

**Remove by:** Editing `installed_plugins.json` to delete the plugin entry. Config directories (e.g., `~/.serena/`) can stay for easy reinstall.

### 4. MCP Server Consolidation (~3,300 tokens saved)

Review `~/.claude.json` for MCP servers. Each server adds tool definitions (~50 tokens/tool) plus server instructions to the system prompt.

**Search tool overlap:** Multiple search providers (Brave, Exa, Serper, Perplexity, Tavily) solve the same problem. Perplexity aggregates across Google, Bing, and proprietary indices — making standalone Google search largely redundant. Tavily adds structured extraction and crawling. Two search providers cover all use cases.

**Audit approach:**
```bash
# Count tools per MCP server
python3 -c "
import json
cfg = json.load(open('$HOME/.claude.json'))
for name, srv in cfg.get('mcpServers', {}).items():
    print(f'{name}: {srv.get(\"command\", \"\")}')
"
```

**Decision criteria for search MCP removal:**
- Does it offer a unique capability not covered by remaining tools?
- Perplexity covers: web search, reasoning, deep research, citations
- Tavily covers: search, extract, crawl, map, research
- Built-in WebSearch covers: basic web queries with auto-sourcing

**2026-02-07 removal:** Brave Search (7 tools), Exa (3 tools), Serper (2 tools) = 12 tool definitions removed. Kept: Perplexity + Tavily + built-in WebSearch.

### 5. Vault CLAUDE.md Trimming (~2,300 tokens saved)

The vault CLAUDE.md (`~/epigenome/chromatin/CLAUDE.md`) loads as a system-reminder on every turn. It had accumulated procedural content, reference material, and duplicated context from the main CLAUDE.md.

**Trimming technique — linked notes:**
- Move procedures to standalone Obsidian notes (e.g., `[[Interview Scheduling Protocol]]`)
- Move reference material to existing skills (e.g., weekly reset → `/weekly` skill)
- Move tool quirks to MEMORY.md (persists across sessions, lower overhead)
- Keep only: current situation, key note links, behavioral rules, active focus areas

**What stayed:** Identity, vault purpose, decision-making style, workflow discipline, current situation, key reference links, formatting prefs, job application protocols.

**What moved:** Interview scheduling (→ standalone note), LinkedIn stats interpretation (→ standalone note), Sunday reset checklist (→ `/weekly` skill), engineering lessons (→ linked note), Gmail/platform quirks (→ MEMORY.md), messaging preferences (→ already in main CLAUDE.md).

**Result:** 3,228 → 904 tokens (~72% reduction).

### 6. Plugin Audit (~2,500+ tokens saved)

Plugins inject MCP tools, instructions, and server definitions. Many "official" plugins are empty shells — they register as installed but provide no skills, agents, or unique tools.

**Audit methodology:**
```bash
# For each plugin, check what it actually provides
ls <plugin_install_path>/.mcp.json 2>/dev/null    # MCP tools
cat <plugin_install_path>/.claude-plugin/plugin.json  # skills, agents, instructions
```

**Empty shell indicators:**
- `.claude-plugin/plugin.json` has empty `skills`, `agents`, `commands` arrays
- No `.mcp.json` (no MCP tools)
- No unique functionality beyond what native Claude Code provides

**2026-02-07 audit results (11 → 5 plugins):**
- Removed: `frontend-design`, `code-review`, `feature-dev` (empty shells), `github` (duplicates `gh` CLI), `rust-analyzer-lsp` (no Rust projects), `ralph-loop` (only needed for `/lfg`, individual workflows work without it)
- Kept: `context7` (live docs), `playwright` (browser automation), `vercel` (deployment), `compound-engineering` (workflows/agents), `obsidian` (vault operations)

### 7. Skill Count

Each skill adds a description line to the system prompt. 100+ skills = significant overhead. Periodically audit for:
- Deprecated skills that should be removed
- Skills that overlap (merge them)
- Skills that are never invoked (archive them)

### 8. Skill Audit and Removal

**Audit methodology:**
- Cross-reference skill directories against actual Skill tool invocations in session transcripts (`~/.claude/projects/-Users-terry/*.jsonl`)
- Match `"skill": "..."` patterns in transcripts against `~/skills/` directory names
- Categorize never-invoked skills: reference (keep), superseded (remove), dead weight (remove)

**2026-02-07 results (75 → 67 skills):**
- Removed: `warp-cli` (not in tool stack), `memu` (abandoned, had entire Rust project with build artifacts), `claude-code` (meta-skill, never triggered — later recreated with model routing), `sync-ecc` (one-off adoption), `parallel-council` (superseded by `/frontier-council`), `flash-browse` (covered by `agent-browser` + `visual-browser`), `codebase-cleanup` (covered by direct OpenCode delegation), `plan` (covered by `/workflows:plan`)
- Surprise: `memu` skill had 458 files including compiled Rust binaries checked into git

### 9. Skill Description Shortening (~500 tokens saved)

**Problem:** Skill descriptions in YAML frontmatter appear in the system prompt skill list. Verbose descriptions (155-298 chars) with redundant trigger phrases waste tokens.

**Fix:** Shorten to 64-111 chars. Remove "Use when user says..." preambles, keep 1-2 key triggers max, focus on core "what it does".

**Example:**
- Before (298 chars): "Frontier Council with 4 frontier models (GPT-5.2, Gemini 3 Pro, Grok 4, Kimi K2.5) deliberating, then Claude Opus 4.5 judging. Creates actual deliberation..."
- After (103 chars): "4 frontier models deliberate, then Claude judges. For high-stakes decisions needing diverse AI perspectives."

## When to Re-Audit

- After installing new plugins or MCP servers
- When sessions feel sluggish or context-limited
- Quarterly as a maintenance habit
- After a major CLAUDE.md rewrite

## Prevention

- **Before adding a plugin:** Estimate its token cost (tool count × ~50 tokens + instruction overhead)
- **Before adding to CLAUDE.md:** Ask "will I need this every session, or only when doing X?" If only X, make it a skill.
- **Reference material test:** If a section is a lookup table or command reference, it's a skill candidate. If it shapes behavior every session, it stays in CLAUDE.md.

## Serena Plugin — When to Reinstall

Removed 2026-02-07. Reinstall (`/install serena`) when:
- Working on a large codebase (1000+ files) with deep class hierarchies
- Heavy refactoring needing cross-reference tracking (`find_referencing_symbols`)
- Navigating an unfamiliar inherited codebase where symbol analysis beats grep
- Config preserved at `~/.serena/` — reinstall is zero-friction
