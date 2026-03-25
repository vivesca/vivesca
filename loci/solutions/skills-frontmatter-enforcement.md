# Skills Frontmatter Enforcement

Skills in `~/skills/` require YAML frontmatter in SKILL.md files:
```yaml
---
name: skill-name
description: One-line description for skill routing.
user_invocable: false   # or true
---
```

Claude Code loads skills at startup and logs errors for missing frontmatter. Skills without it still load but route incorrectly.

## Current State (2026-03-03)

No enforcement layer. Discovered lacuna and hkicpa were missing frontmatter after creating them — only caught by checking claude startup logs. Convention degrades silently.

## Proposed Enforcement: pre-commit hook in ~/skills/

Add `.git/hooks/pre-commit` to the `~/skills/` repo:

```python
#!/usr/bin/env python3
"""Validate YAML frontmatter in all new/modified SKILL.md files."""
import subprocess, sys

result = subprocess.run(
    ['git', 'diff', '--cached', '--name-only'],
    capture_output=True, text=True
)
skill_files = [f for f in result.stdout.splitlines() if f.endswith('SKILL.md')]

errors = []
for path in skill_files:
    try:
        with open(path) as f:
            content = f.read()
        if not content.startswith('---'):
            errors.append(f"{path}: missing YAML frontmatter (must start with ---)")
    except FileNotFoundError:
        pass  # deleted file, skip

if errors:
    print("❌ Skills frontmatter check failed:")
    for e in errors:
        print(f"  {e}")
    sys.exit(1)
```

Install:
```bash
cat > ~/skills/.git/hooks/pre-commit << 'EOF'
<script above>
EOF
chmod +x ~/skills/.git/hooks/pre-commit
```

Note: Git hooks don't survive `git clone` — must reinstall after fresh clone. Consider adding install instructions to ~/skills/README.md.
