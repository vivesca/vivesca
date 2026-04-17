---
name: gist
description: Create, update, and manage secret GitHub gists. Use when sharing code/text for mobile copy-paste, or when user says "gist", "/gist".
effort: low
user_invocable: true
triggers:
  - gist
  - /gist
  - tg-clip
---

# Gist Management

> **STOP — before running any `gh gist create` command:**
> 1. Write content to `/tmp/<filename>` first — never pipe via `echo`/`printf`/`<<<`
> 2. All gists MUST be `--public=false`
> 3. Verify content after creation via `gh api gists/<id>`

All gists MUST be secret (`--public=false`). Never create public gists.

## Operations

### Create

```bash
gh gist create --public=false -f <filename> <filepath> -d "<description>"
```

**Always write content to `/tmp/<filename>` first, then create from that path.** Never pipe content via `<<<`, `printf`, or `echo` — zsh escapes `!` and other metacharacters even in single quotes, resulting in `boss/!` instead of `boss!` in the gist.

### Update

**`gh gist edit -f <name> < file` silently fails.** Stdin piping does not work — the gist appears updated but content is unchanged.

**Workaround:** Delete and recreate.

```bash
gh gist delete <id> --yes
gh gist create --public=false -f <filename> <filepath> -d "<description>"
```

Always verify after update via API (not `gh gist view`, which can also escape characters):

```bash
gh api gists/<new-id> --jq '.files["<filename>"].content'
```

### List active gists

```bash
gh gist list --limit 20
```

### Cleanup

Delete gists after use. Don't leave drafts, internal notes, or sensitive content in GitHub.

```bash
gh gist delete <id> --yes
```

## Routing: tg-clip vs gist

**Default to `tg-clip`** — sends text to Telegram as a code block with one-tap copy button.

```bash
# Simple (content only)
tg-clip "text to copy"

# With label
tg-clip "Option 1" "the actual prompt or text to copy"

# From stdin
echo "text" | tg-clip
echo "text" | tg-clip "label"
```

**Use gists only when:**
- Text exceeds 4096 chars (Telegram limit)
- Need a permalink to share with others
- Need to preserve formatting (markdown rendering)

## LinkedIn Posts

Gist is the right format for LinkedIn (markdown preserved, mobile copy-paste). But **only create the gist when the post is finalized and ready to publish** — not during drafting or quorate review. The vault note is the draft home; the gist is the send buffer.

## When NOT to use either

- Short inline answers (just type them)
- Permanent documentation (use vault notes)
- Anything with secrets/credentials (even secret gists are accessible via URL)
- LinkedIn drafts still in review (wait until finalized)
