---
name: skill-drift
description: Detect skills referencing moved paths, renamed tools, or dead binaries.
model: sonnet
tools: ["Bash", "Read", "Grep", "Glob"]
---

Check all skills and agents for stale references. Drift happens silently — catch it here.

1. Collect all skill/agent files:
   - ~/.claude/skills/*.md
   - ~/germline/membrane/buds/*.md
   - ~/.claude/agents/*.md (if any)

2. For each file, extract:
   - Hardcoded paths (~/path/to/something)
   - Binary names (commands being run)
   - File references (config files, cache files, log files)

3. Verify each:
   - Paths: does the file/directory exist?
   - Binaries: `which <cmd>` or `ls ~/germline/bin/<cmd>`
   - Referenced config files: do they exist?

4. Flag mismatches:
   - DEAD PATH: path in skill doesn't exist
   - MISSING BINARY: command not found on PATH
   - STALE CONFIG: config file moved or renamed

Output: table of skill → issue → suggested fix.
Severity: BROKEN (will fail at runtime) vs STALE (may still work, verify).
