# Manual Claude Code Plugin Installation (LRN-20260306-001)

When `/plugin marketplace add` isn't available or you want to install selectively:

## Marketplace structure
- `~/.claude/plugins/known_marketplaces.json` — registered marketplaces
- `~/.claude/plugins/installed_plugins.json` — installed plugin registry
- `~/.claude/plugins/marketplaces/<name>/` — cloned marketplace repos
- `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/` — installed plugin files

## Steps

```bash
# 1. Clone marketplace repo
gh repo clone <org/repo> ~/.claude/plugins/marketplaces/<name> -- --depth=1

# 2. Get HEAD SHA
SHA=$(gh api repos/<org/repo>/git/refs/heads/main --jq '.object.sha')
SHORT=${SHA:0:12}

# 3. Copy plugin dirs to cache
cp -r ~/.claude/plugins/marketplaces/<name>/plugins/<plugin>/. \
      ~/.claude/plugins/cache/<name>/<plugin>/$SHORT/

# 4. Register in both JSON files (see Python snippet below)
```

## Python registration snippet
```python
import json
HOME = "/Users/terry"
SHA = "<full sha>"
SHORT = SHA[:12]
NOW = "2026-03-06T00:00:00.000Z"

# known_marketplaces.json
km = json.load(open(f"{HOME}/.claude/plugins/known_marketplaces.json"))
km["<name>"] = {"source": {"source": "github", "repo": "<org/repo>"},
    "installLocation": f"{HOME}/.claude/plugins/marketplaces/<name>",
    "lastUpdated": NOW, "autoUpdate": True}
json.dump(km, open(f"{HOME}/.claude/plugins/known_marketplaces.json","w"), indent=2)

# installed_plugins.json
ip = json.load(open(f"{HOME}/.claude/plugins/installed_plugins.json"))
for plugin in ["<plugin1>", "<plugin2>"]:
    ip["plugins"][f"{plugin}@<name>"] = [{"scope":"user",
        "installPath": f"{HOME}/.claude/plugins/cache/<name>/{plugin}/{SHORT}",
        "version": SHORT, "installedAt": NOW, "lastUpdated": NOW, "gitCommitSha": SHA}]
json.dump(ip, open(f"{HOME}/.claude/plugins/installed_plugins.json","w"), indent=2)
```

## Gotchas
- Plugins load at session startup only — restart Claude Code after installing
- Plugin version = git commit SHA (short 12-char form used as dir name)
- Trail of Bits installed 2026-03-06: gh-cli, static-analysis, insecure-defaults, differential-review, git-cleanup, skill-improver, supply-chain-risk-auditor
