---
name: primase
description: "Write GLM-dispatchable specs from code gaps. Reference skill consulted by securin (re-spec failures) and mitogen (pre-dispatch). Not user-invocable."
effort: low
user_invocable: false
---

# Primase — spec synthesis from code gaps

Primase synthesizes RNA primers that DNA polymerase requires to begin replication. Without the primer, replication can't start. Same pattern: without a tight spec, the ribosome can't build.

Consulted by: `securin` (when re-speccing failed tasks), `mitogen` (before dispatch), any session writing specs for mtor dispatch.

## When to consult

- Before dispatching any mtor task
- When a task fails and needs a tighter spec
- When converting a feature request into a dispatchable unit

## Spec file structure

Write to `~/epigenome/chromatin/loci/plans/spec-<slug>.md`:

```markdown
---
title: "One-line description"
status: ready
priority: high|medium|low
repo: ~/code/<repo>
depends_on:
  - spec-other-thing.md    # or empty []
target_files:
  - path/to/file.py
---

# Title

## Problem
What's broken or missing. 2-3 sentences max.

## Solution
What to change. Be concrete — name the function, the approach.

## Location
Exact file, function name, line numbers. Paste the current code block
if the file is >200 lines (GLM corrupts files it can't see).

## New function / Changes
Show the code skeleton with docstring and signature.
Include the exact insertion point ("after line X", "replace lines Y-Z").

## Constraints
- Only modify <exact files>
- Do NOT modify <adjacent things GLM might touch>
- Timeout all subprocess calls
- Other guardrails specific to this change

## Tests
Add `assays/test_<name>.py`:
1. test_happy_path — ...
2. test_edge_case — ...
3. test_error_handling — ...

## Expected impact
One sentence on what changes when this lands.
```

## Rules for GLM-effective specs

1. **One function per spec.** "Implement branch-PR workflow" is too broad. Split into `create_pr`, `cleanup_branch`, etc.

2. **Paste current code.** GLM corrupts files >500 lines when working blind. Include the exact function + surrounding context + line numbers.

3. **Explicit file constraint.** "Only modify `mtor/worker/translocase.py` lines 200-250" — not "only modify mtor". GLM scope-drifts without hard boundaries.

4. **Name the insertion point.** "Add after the existing `_merge_lock` helper" not "add near the top". GLM needs anchors.

5. **Tests are mandatory.** List test names and what they verify. This gives GLM a definition of done.

6. **No multi-file tasks.** If the change touches 2+ files, write 2+ specs with `depends_on` linking them.

7. **Frontmatter matches rptor fields.** `depends_on` not `blocked_by`. Check `rptor.py:scan_specs` before inventing fields.

## Reading current code (pre-spec checklist)

Before writing the spec, CC must:
1. Read the target file at the relevant section
2. Identify the exact function/line where the change goes
3. Check for existing patterns to follow (naming, error handling style)
4. Check `git log --oneline -5` on ganglion — is the file being modified by another running task?
5. If yes → wait or pick a different file

## Anti-patterns

- Don't write specs without reading the target code first
- Don't use vague locations ("somewhere in translate")
- Don't combine unrelated changes in one spec
- Don't skip the test section — it's the definition of done
- Don't assume GLM knows the codebase — paste what it needs to see
