# opifex: use absolute paths, not ~

`opifex exec` passes paths to Codex/Gemini subprocesses. `~` doesn't expand in subprocess `cd` commands — use `/Users/terry/` instead.

```bash
# Bad — fails with "No such file or directory"
opifex exec ~/docs/plans/foo.md -p ~/code/bar

# Good
opifex exec /Users/terry/docs/plans/foo.md -p /Users/terry/code/bar
```

Burned: 2026-03-16, thalamus refactor delegation failed twice before catching this.
