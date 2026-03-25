---
name: obsidian-cli
description: Obsidian vault operations using obsidian-cli. Use for moving notes (updates wikilinks), frontmatter editing, or opening notes in Obsidian app.
user_invocable: false
github_url: https://github.com/Yakitrak/obsidian-cli
---

# Obsidian CLI

CLI for Obsidian vault operations. Primary use case: moving/renaming notes with automatic wikilink updates.

## When to Use

- **Move/rename notes** — Updates all wikilinks across vault (direct file ops don't)
- **Open note in Obsidian app** — When user wants to view in native app
- **Frontmatter operations** — View or modify YAML frontmatter
- **Fuzzy search** — When you don't know exact note name

For simple read/write operations, prefer direct file access (faster, no CLI overhead).

## Prerequisites

- `obsidian-cli` installed (`/opt/homebrew/bin/obsidian-cli`)
- Default vault configured (Terry's vault: `/Users/terry/notes`)

## Commands

### Check Default Vault
```bash
obsidian-cli print-default
```

### Set Default Vault
```bash
# Takes vault name as arg (path auto-discovered from Obsidian config)
obsidian-cli set-default notes
```

### Open Note in Obsidian
```bash
obsidian-cli open "Note Name"
obsidian-cli open "folder/Note Name"
```

### Create Note
```bash
obsidian-cli create "New Note" --content "Initial content"
obsidian-cli create "folder/New Note" --content "Content here"
```

### Print Note Contents
```bash
obsidian-cli print "Note Name"
```

### Move/Rename Note (KEY FEATURE)
```bash
# Rename note (updates all wikilinks!)
obsidian-cli move "Old Name" "New Name"

# Move to different folder
obsidian-cli move "Note Name" "archive/Note Name"

# Move and rename
obsidian-cli move "drafts/Old Name" "published/New Name"
```

### Delete Note
```bash
obsidian-cli delete "Note Name"
```

### Fuzzy Search
```bash
obsidian-cli search "partial name"
```

### Search Content
```bash
obsidian-cli search-content "search term"
```

### Daily Note
```bash
obsidian-cli daily  # Creates/opens today's daily note
```

### Frontmatter Operations
```bash
# View frontmatter
obsidian-cli frontmatter "Note Name"

# Set frontmatter field
obsidian-cli frontmatter "Note Name" --set "status=active"

# Remove frontmatter field
obsidian-cli frontmatter "Note Name" --remove "draft"
```

## Key Use Case: Renaming with Link Updates

When renaming a note that's linked from other notes:

**Wrong way** (breaks links):
```bash
mv "~/notes/Old Name.md" "~/notes/New Name.md"
```

**Right way** (updates links):
```bash
obsidian-cli move "Old Name" "New Name"
```

This scans the vault and updates all `[[Old Name]]` references to `[[New Name]]`.

## When NOT to Use

- Simple file reads → Use `Read` tool directly
- Simple file writes → Use `Write` tool directly
- Searching file contents → Use `Grep` tool
- Listing files → Use `ls` or `Glob`

The CLI adds overhead. Only use when you need its special capabilities (move with link updates, frontmatter, open in app).

## Integration

- Works alongside direct file operations — choose the right tool for the job
