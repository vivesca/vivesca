---
name: skill-sync
description: "MUST run after creating/modifying skills. Syncs to Claude Code, OpenCode, and Codex."
user_invocable: true
---

# Skill Sync

Ensure both AI platforms have access to the same skills.

## Locations

| Platform | Skills Directory |
|----------|-----------------|
| Source | `~/skills/` |
| Claude Code | `~/.claude/skills/` |
| OpenCode | `~/.opencode/skills/` |
| Codex | `~/.codex/skills/` |
| Codex (agents) | `~/.agents/skills/` |

## Commands

### `/skill-sync`
Sync all skills and clean up stale symlinks.

```bash
# Use absolute paths to avoid symlink bugs
SKILLS_DIR="$HOME/skills"
TARGETS=("$HOME/.claude/skills" "$HOME/.opencode/skills" "$HOME/.codex/skills" "$HOME/.agents/skills")

# 1. Ensure target directories exist
for dir in "${TARGETS[@]}"; do
  mkdir -p "$dir"
done

# 2. Remove stale symlinks (point to non-existent targets)
for dir in "${TARGETS[@]}"; do
  for link in "$dir"/*; do
    [ -L "$link" ] && [ ! -e "$link" ] && rm "$link"
  done
done

# 3. Clean up any nested symlinks inside skill directories (bug recovery)
for skill in "$SKILLS_DIR"/*/; do
  name=$(basename "$skill")
  [ -L "$skill/$name" ] && rm "$skill/$name"
done

# 4. Sync skills (dirs with SKILL.md)
for item in "$SKILLS_DIR"/*; do
  name=$(basename "$item")
  [ "$name" = "TEMPLATE.md" ] && continue
  [ "$name" = ".git" ] && continue
  [ "$name" = ".archive" ] && continue

  # Skip symlinks in source (aliases handled by their targets)
  [ -L "$item" ] && continue

  # Only sync directories with SKILL.md
  if [ -d "$item" ] && [ -f "$item/SKILL.md" ]; then
    for dir in "${TARGETS[@]}"; do
      ln -sfn "$item" "$dir/$name"
    done
  fi
done
```

**Key fixes:**
- Uses `ln -sfn` (no-dereference) to handle existing symlinks correctly
- Absolute paths throughout to avoid cwd-related bugs
- Cleans up nested symlinks inside skill dirs (recovery from previous bug)
- Skips `.git`, `.archive`, and source symlinks

### `/skill-sync check`
Show stale symlinks and missing skills.

### `/skill-sync new <name>`
Create a new skill with proper structure and sync to all platforms:

1. Create `~/skills/<name>/SKILL.md` from template
2. Symlink to all three platforms
3. Open for editing

## Template

New skills use `~/skills/TEMPLATE.md` as the starting point.

## After Creating/Modifying Skills

Always run:
```bash
cd ~/skills && git add -A && git commit -m "Update <skill-name>" && git push
```

## Notes

- Source of truth is always `~/skills/`
- Symlinks point TO source, not copies
- Both platforms read SKILL.md format (Agent Skills spec)
