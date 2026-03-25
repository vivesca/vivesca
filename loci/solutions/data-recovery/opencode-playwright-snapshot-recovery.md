# Recovering Content from OpenCode Playwright Snapshots

## Problem

Content extracted via OpenCode + Playwright was saved to `/tmp` files that got deleted. The vault notes only had placeholders like `[Content extracted from /tmp/garp_m4_52.txt]`.

## Solution

OpenCode persists full Playwright accessibility tree snapshots in:

```
~/.local/share/opencode/tool-output/
```

Each file (~70-90KB) contains the page's accessibility tree in YAML-like format. Text content lives in `paragraph`, `heading`, and `listitem` nodes.

### Extraction Script

```python
import re

def extract_text_from_snapshot(filepath):
    with open(filepath) as f:
        lines = f.read().split('\n')

    text_parts = []
    for line in lines:
        stripped = line.strip()

        m = re.match(r'^- paragraph \[ref=\w+\]: (.+)$', stripped)
        if m:
            text_parts.append(m.group(1))
            continue

        m = re.match(r'^- heading "(.+)" \[level=(\d+)\]', stripped)
        if m:
            level = int(m.group(2))
            heading = m.group(1)
            if heading in ['Lessons', 'Rate Your Confidence', 'Category', 'Table of Contents']:
                continue
            text_parts.append('\n' + '#' * min(level + 1, 4) + ' ' + heading)
            continue

        m = re.match(r'^- listitem \[ref=\w+\]: (.+)$', stripped)
        if m:
            text_parts.append('- ' + m.group(1))

    result = '\n\n'.join(text_parts)
    cutoff = result.find('Rate Your Confidence')
    if cutoff > 0:
        result = result[:cutoff].strip()
    return result
```

### Finding the Right Files

1. `grep -rl 'keyword' ~/.local/share/opencode/tool-output/` to find relevant snapshots
2. Check `Page URL` near top of each file for the section identifier
3. Prefer larger files (more complete snapshots)

## Key Insight

Claude Code's `.claude/file-history/` only snapshots files when Claude Code itself edits them — it won't capture content written by external tools like OpenCode to /tmp. But OpenCode's own tool-output directory persists indefinitely.

## Date

2026-02-10
