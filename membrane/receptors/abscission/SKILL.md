---
description: Extract a germline effector into a standalone repo + PyPI package. Use when a package passes the distribution test (strangers install, independent release, different deps, clean boundary).
triggers:
  - graduate
  - extract package
  - standalone repo
---

# Graduation — Effector → Standalone Package

## Distribution test (all 4 must pass)
1. Strangers would actually install it
2. Independent release cycle matters
3. Different dependency footprint from host
4. Clean import boundary

## Steps

### 1. Extract
```bash
cp -r ~/germline/effectors/<name> ~/code/<name>
cd ~/code/<name>
rm -rf .venv __pycache__ */__pycache__ .pytest_cache
```

### 2. Init repo
```bash
git init && git branch -m main
echo '__pycache__/\n*.pyc\n.venv/\n*.egg-info/\ndist/\nbuild/\n.pytest_cache/' > .gitignore
```

### 3. Single-source version
In `pyproject.toml`: `dynamic = ["version"]` + `[tool.hatch.version] path = "<pkg>/__init__.py"`.
Remove hardcoded `version =` from `[project]`.

### 4. Tests must pass before push
```bash
uv run pytest assays/ -q
```
Fix: version assertions (don't hardcode), test prompts (match dispatch gates), mock methods (cancel→terminate etc.).

### 5. Create repo + push
```bash
gh repo create vivesca/<name> --public --source=. --push --description "..."
```

### 6. Check ganglion branches
Before removing from germline, check for unmerged ribosome work:
```bash
ssh ganglion "cd ~/germline && for b in \$(git branch | grep ribosome); do
  changes=\$(git log main..\$b --oneline -- effectors/<name>/ | head -1)
  [ -n \"\$changes\" ] && echo \"\$b: \$changes\"
done"
```
Save reference patches for any worth porting.

### 7. Publish to PyPI
```bash
uv build && PYPI_TOKEN=$(op item get "pypi-token" --vault Agents --fields credential --reveal) && uv publish --token "$PYPI_TOKEN"
```

### 8. Remove from germline
```bash
cd ~/germline && git rm -r effectors/<name>/ && git commit -m "refactor: extract <name> to standalone repo (vivesca/<name>)"
git push origin main
```

### 9. Install on both machines
```bash
uv tool install <name> --upgrade
ssh ganglion "export PATH=\$HOME/.local/bin:\$HOME/.cargo/bin:\$PATH && uv tool install <name> --upgrade"
```
Also clone on ganglion: `ssh ganglion "git clone https://github.com/vivesca/<name>.git ~/code/<name>"`

### 10. Add CI
Copy `.github/workflows/ci.yml` from vivesca/mtor as template.

### 11. Add `mtor publish` or equivalent
If the package has a CLI, add a publish command that bumps + builds + publishes + upgrades both machines.

### 12. Update references
- MEMORY.md
- Any skills referencing the old path
- axon.py deny messages if relevant

## Anti-patterns from the mtor graduation
- Don't forget to check ganglion branches — ribosome work lives there
- Don't hardcode versions in tests — read from the module
- Run tests BEFORE first push, not after
- Cancel running ribosome tasks targeting the old path immediately
