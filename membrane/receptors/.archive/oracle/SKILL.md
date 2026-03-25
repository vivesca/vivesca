---
name: oracle
description: Bundle prompt + files for other LLMs (GPT-5.2 Pro via browser, or API). Use for deep analysis requiring another model's perspective or capabilities.
user_invocable: false
github_url: https://github.com/steipete/oracle
---

# Oracle

Bundle prompts + selected files into one-shot requests for other models. Output is advisory — verify against code + tests.

## Prerequisites

- `oracle` CLI installed: `npx -y @steipete/oracle --help`
- For browser mode: ChatGPT session in browser

## Primary Use Case

Browser mode with GPT-5.2 Pro for "long think" analysis (10 min to 1 hour is normal).

## Commands

### Preview (No Tokens)

```bash
# Summary preview
oracle --dry-run summary -p "<task>" --file "src/**" --file "!**/*.test.*"

# Full preview
oracle --dry-run full -p "<task>" --file "src/**"

# Token report
oracle --dry-run summary --files-report -p "<task>" --file "src/**"
```

### Browser Run (Main Path)

```bash
oracle --engine browser --model gpt-5.2-pro -p "<analysis task>" --file "src/**"
```

### API Run

```bash
oracle --engine api --model anthropic/claude-sonnet-4 -p "<task>" --file "src/**"
```

## File Selection

```bash
# Include pattern
--file "src/**"

# Exclude pattern
--file "!**/*.test.*"
--file "!**/node_modules/**"
```

## Golden Path

1. Pick tight file set (fewest files with needed context)
2. Preview with `--dry-run` + `--files-report`
3. Use browser mode for GPT-5.2 Pro workflow
4. If detached/timeout: reattach to stored session, don't re-run

## Notes

- Avoid `pnpx` (sqlite binding issues) — use `npx`
- Long-running is normal for browser mode
- Treat output as advisory, verify against actual code
