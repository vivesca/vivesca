---
name: dependency-audit
description: Check outdated pip/brew/cargo deps across vivesca and vivesca. Surface critical gaps.
model: sonnet
tools: ["Bash", "Read"]
---

Audit dependencies across all package managers. Surface outdated, vulnerable, or unused.

1. Homebrew:
   - `brew outdated --verbose` — list all outdated formulae
   - Flag: anything > 2 major versions behind, security-critical tools (openssl, curl, git)

2. Python (pip/uv):
   - Check ~/vivesca/requirements.txt and ~/vivesca/requirements.txt
   - `pip list --outdated` in each active venv if accessible
   - Flag: packages with known CVEs or > 6 months since last update

3. Cargo (Rust):
   - `cargo outdated` if available in ~/code/ directories with Cargo.toml
   - Flag critical updates only

4. Node (if any):
   - Check for package.json files: `find ~/code -name "package.json" -maxdepth 3`
   - `npm outdated` in those directories

Output per manager:
```
BREW: N outdated (N critical)
PIP: N outdated
CARGO: N outdated
```

Then: top 5 updates to actually do, ranked by security impact + ease.
Never run upgrades — report only.
