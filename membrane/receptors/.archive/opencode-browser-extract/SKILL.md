---
name: opencode-browser-extract
description: Extract web page content via OpenCode + Playwright MCP. For authenticated pages, saves Claude tokens.
user_invocable: false
---

# OpenCode Browser Extraction

Use OpenCode (GLM-4.7) with Playwright MCP to extract web page content. Saves Claude tokens for mechanical extraction tasks.

## Prerequisites

Playwright MCP must have extended timeouts in `~/.opencode/mcp.json`:

```json
"playwright": {
  "command": "npx",
  "args": [
    "-y",
    "@playwright/mcp@latest",
    "--extension",
    "--timeout-action",
    "60000",
    "--timeout-navigation",
    "60000"
  ]
}
```

Without these timeouts, complex pages (like GARP Learning) will timeout during JS evaluation.

## Working Pattern

**Numbered steps work best.** GLM follows explicit numbered instructions more reliably than prose.

```bash
# BEST: Numbered steps (most reliable)
timeout 150 opencode run "1. playwright_browser_navigate to [URL] 2. playwright_browser_click OK 3. playwright_browser_evaluate JS: document.body.innerText.slice(0,8000) 4. Write to /tmp/output.txt"

# OK: Prose style (less reliable, may timeout before file write)
timeout 120 opencode run "Playwright: go to [URL], click OK if dialog, JS: document.body.innerText.slice(0,8000), save to /tmp/output.txt"
```

**Why numbered steps work:**
- GLM executes each step in sequence without overthinking
- Explicit tool names (`playwright_browser_navigate`) reduce hallucination
- File write step executes before timeout

**Timeout guidance:**
- Use `timeout 150` for numbered steps (needs time for all 4 steps)
- Exit code 124 often still succeeds if Write step shows in output

## What Works

- Single-page extraction
- Simple navigation + extract + save
- Pages that load within 60 seconds
- Authenticated pages (uses Chrome session via --extension)

## What Doesn't Work Well

- Multi-step sequences (GLM starts planning "subagents")
- Very long prompts with many instructions
- Pages with 60+ second load times

## Hybrid Pattern (Best for Complex Tasks)

When extracting multiple pages:

1. **Claude in Chrome** extracts text → saves to `/tmp/section_N.txt`
2. **OpenCode** appends files to vault (cheap file ops)

```bash
# OpenCode for file operations only
opencode run "Append contents of /tmp/s1.txt, /tmp/s2.txt to /path/to/note.md"
```

## Tab Management (IMPORTANT)

Each OpenCode + Playwright session creates new Chrome tabs. Parallel sessions multiply this quickly.

**Best practices:**
- **Limit parallelism:** Max 2-3 concurrent OpenCode sessions on iMac
- **Clean up after:** Close tabs after extraction completes
- **Sequential for reliability:** One section at a time works better than parallel

**Quick tab cleanup:**
```bash
# Get tab IDs
# Use mcp__browser-tabs__get_tabs to list, then close_tab_by_id for each duplicate
```

Or manually: Cmd+W to close tabs in Chrome.

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| JS evaluate timeout | Default Playwright timeout too short | Add `--timeout-action 60000` |
| URL typos (garpleearning) | GLM hallucination | Usually self-corrects, or spell out carefully |
| "Using subagents" stall | Prompt too complex | Simplify to single task |
| Chrome tabs accumulating | Playwright creates new tabs | Clean up manually after each session |
| Parallel sessions conflict | Multiple sessions share browser | Run sequentially or limit to 2-3 |
| Exit code 124 | Timeout (often on "Done" message) | File may still be created - check |

## Example: GARP Learning Extraction

```bash
# Single section (numbered steps - recommended)
timeout 150 opencode run "1. playwright_browser_navigate to https://garplearning.benchprep.com/app/rai26#read/section/60-model-validation 2. playwright_browser_click OK 3. playwright_browser_evaluate JS: document.body.innerText.slice(0,8000) 4. Write to /tmp/garp_m5_60.txt"
```

## Batch Extraction Script

For extracting many sections overnight:

```bash
#!/bin/bash
# Save as ~/scripts/garp-batch-extract.sh

SECTIONS=(
  "learning-objectives-13:lo"
  "10-introduction-2:10"
  "20-data-governance:20"
  # Add more sections...
)

for item in "${SECTIONS[@]}"; do
  section="${item%%:*}"
  slug="${item##*:}"
  echo "Extracting $section -> /tmp/garp_m5_$slug.txt"
  timeout 150 opencode run "1. playwright_browser_navigate to https://garplearning.benchprep.com/app/rai26#read/section/$section 2. playwright_browser_click OK 3. playwright_browser_evaluate JS: document.body.innerText.slice(0,8000) 4. Write to /tmp/garp_m5_$slug.txt"
  sleep 5  # Brief pause between extractions
done
```

Run overnight: `nohup ~/scripts/garp-batch-extract.sh > /tmp/garp-extract.log 2>&1 &`

## Overnight Batch Reliability (Observed Feb 2026)

**Expect ~35-40% success rate** for overnight batch runs. Failure modes observed:

| Failure Type | Frequency | Symptom |
|--------------|-----------|---------|
| Playwright MCP disconnect | ~30% | "Bridge extension isn't connected" |
| Auth session timeout | ~15% | Login page returned instead of content |
| JS evaluate timeout | ~10% | Exit code 124, no file created |
| GLM hallucination | ~5% | Typos in URL, wrong tool names |

**Mitigation strategies:**
1. **Run in 2 passes:** First pass overnight, second pass next morning for failures
2. **Skip existing files:** Script checks `if [[ -f "$output_file" ]]` to avoid re-downloading
3. **Shorter batches:** 20-30 sections more reliable than 70+
4. **Keep Chrome active:** Playwright MCP connection more stable with Chrome in foreground

**Alternative for high-value content:** Use Claude in Chrome directly (100% reliable, higher token cost)
