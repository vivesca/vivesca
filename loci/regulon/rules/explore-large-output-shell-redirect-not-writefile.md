---
title: Large output → shell redirect, not write_file
impact: MEDIUM
tags: explore
---

## Large output → shell redirect, not write_file

If the report has >100 lines, write it via `python3 -c "..." > file.md` or `cat << 'EOF' > file.md`. The `write_file` tool argument parser chokes on large JSON payloads (error -32602). Shell redirects bypass this limit.
