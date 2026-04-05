---
title: "Edit a file" ≠ "rewrite a file."
impact: CRITICAL
impactDescription: GLM replaced 87-line file with 3 lines
tags: fileops
---

## "Edit a file" ≠ "rewrite a file."

When told to add a frontmatter field or prepend a note, READ the existing file first, then PATCH it. GLM-5.1 replaced elencho's 87-line SKILL.md with 3 lines of frontmatter (2026-04-03). The original content was destroyed. Always: `cat` → modify → `write_file` with full original content preserved. If the file has >20 lines, use `apply_patch` or surgical insertion, never full rewrite from memory.
