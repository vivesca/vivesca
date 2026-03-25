# Delegation: Cargo workspace boundary pollution

## Problem
When delegating to Gemini/Codex with `-p ~/code/<crate>`, delegates see the parent `~/code/` Cargo workspace and modify sibling crates. Gemini changed 44 files across unrelated projects. Codex changed 30 files but at least produced the target file.

## Root cause
`~/code/` is a Cargo workspace. Delegates scan for `Cargo.toml` at root, find the workspace, and treat all member crates as in-scope.

## Fix
For crates inside `~/code/` workspace, delegate to a **standalone copy** outside the workspace:
```bash
mkdir -p ~/code/<name>-py  # or ~/tmp/<name>
cp relevant files there
opifex exec plan.md -p ~/code/<name>-py
```

Or: use `--decompose` to isolate tasks, and explicitly state "ONLY modify files in the <name>/ subdirectory" in the prompt.

## Prevention
Always check `git diff --stat` after delegation returns. Revert non-target changes immediately with `git checkout -- .` on the workspace root.

## Date
2026-03-16. Burned on moneo Rust→Python rewrite.
