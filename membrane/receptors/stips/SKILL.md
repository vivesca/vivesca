---
name: stips
description: Check OpenRouter credits and usage. Use when user says "stips", "openrouter credits", "or credits", or quorate returns 402.
effort: low
user_invocable: true
---

# stips

OpenRouter CLI — credits, usage, key management.

`~/code/stips` · [crates.io](https://crates.io/crates/stips) · [github](https://github.com/terry-li-hm/stips)

## Commands

```bash
stips                      # credit balance (default)
stips credits              # credit balance
stips credits --json       # credit balance as JSON
stips usage                # daily / weekly / monthly spend
stips usage --json         # usage as JSON
stips key open             # open openrouter.ai/keys in browser
stips key save <key>       # save API key to macOS keychain
```

## Environment Variables

- `OPENROUTER_API_KEY` — override keychain (useful in CI or non-macOS)
- `OPENROUTER_BASE_URL` — override API base URL (default: https://openrouter.ai)

## Keychain

Key stored under service `openrouter-api-key`, account `openrouter`.

## Low balance

Warns (stderr) when remaining < $5, but exits 0. Top up at https://openrouter.ai/credits.
