# CE Plugin File Locations

## Problem

Finding Compound Engineering skill and command source files takes multiple attempts. The plugin is installed via the marketplace but the files aren't in an obvious location.

## Location

```
~/.claude/plugins/cache/every-marketplace/compound-engineering/<version>/
├── agents/
├── commands/
│   ├── workflows/    ← /workflows:compound, /workflows:plan, etc.
│   └── *.md          ← /changelog, /lfg, /slfg, etc.
├── skills/           ← compound-docs, agent-browser, etc.
├── CLAUDE.md
└── README.md
```

Current version: `2.30.0` (check `~/.claude/plugins/installed_plugins.json` for exact version).

## Key Distinction

- **`commands/`** = user-invocable slash commands (workflows live here)
- **`skills/`** = reference skills loaded into context (not directly invoked)

The system prompt lists both together, which can be misleading.

## Quick Access

```bash
ls ~/.claude/plugins/cache/every-marketplace/compound-engineering/*/
```

## Third-Party Plugins

Install any GitHub-hosted skills repo as a plugin:

```bash
/plugin marketplace add <github-user>/<repo>
/plugin install <repo>@<github-user>-<repo>
/plugin update <repo>@<github-user>-<repo>   # upgrade
```

Installed: `evals-skills@hamelsmu-evals-skills` — 7 skills for LLM eval workflows (audit, error analysis, judge design, RAG eval, synthetic data, annotation UI). Invoke as `/evals-skills:<skill-name>`. Relevant for Capco AI consulting.
