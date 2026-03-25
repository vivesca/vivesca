---
category: integration-issues
tags: [opencode, sync-script, security, plugins, mcp]
symptoms: "/lfg command fails; API keys exposed; sync script overwriting config; duplicate MCP servers"
---

# LFG Namespace, Sync Robustness, and Secret Migration

## Problem Symptom
1. Running `/lfg` failed because the command template hardcoded a legacy namespace `/ralph-wiggum:ralph-loop`.
2. Sensitive API keys (Brave, Tavily, etc.) were stored in plaintext in `opencode.json`.
3. The `sync-claude-to-opencode.sh` script failed under Claude Code v2 metadata and would overwrite the target config instead of merging, causing tool loss.
4. Duplicate `gmail` MCP entries existed in both `settings.json` and `opencode.json`, causing sync redundancy.

## Root Cause Analysis
- **Namespace Typo:** A legacy reference in the `compound-engineering` source was never updated to the current `ralph-loop` name.
- **Converter Limitation:** The OpenCode converter lacked a "syntax bridge" to transform legacy namespaces during plugin installation.
- **Sync Logic:** The bash script used an outdated `jq` path for enabled plugins and performed a destructive write instead of a merge.
- **Missing Agents:** Confirmed that agents `rails-console-explorer` and `appsignal-log-investigator` are referenced in the plugin but missing from the repository source.

## Working Solution
1. **Source Fix:** Corrected `plugins/compound-engineering/commands/lfg.md` to use `/ralph-loop:ralph-loop`.
2. **Converter Bridge:** Added `transformContentForOpenCode` to `claude-to-opencode.ts` to automatically map legacy strings during conversion.
3. **Secret Migration:** 
   - Moved keys to `~/.secrets` (gitignored).
   - Added `source ~/.secrets` to `~/.zshrc`.
   - Removed `environment` blocks from `opencode.json` to allow shell inheritance.
4. **Sync Script v2:** 
   - Updated `ENABLED_PLUGINS` logic to support Claude v2 metadata.
   - Implemented a `jq -s '.[0] * .[1]'` merge step to combine plugin configs with local manual overrides.
5. **Config Cleanup:** Deleted the redundant `gmail` MCP from `opencode.json` so it is managed only via `settings.json`.

## Prevention Strategies
- **Secret Inheritance:** Never store keys in JSON configs; rely on terminal environment inheritance.
- **Robust Merging:** Use `jq` merging in sync scripts to prevent configuration regression.
- **Namespace Transformation:** Converters must maintain a mapping of legacy-to-current namespaces for cross-plugin compatibility.

## Cross-References
- **GitHub PR:** [EveryInc/compound-engineering-plugin/pull/126](https://github.com/EveryInc/compound-engineering-plugin/pull/126)
- **Local Config Repo:** `~/claude-config`
- **Missing Agents Issue:** Upstream repository bug in `/reproduce-bug` template.
