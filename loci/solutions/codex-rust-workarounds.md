# Codex + Rust: Sandbox DNS Block & Workarounds

**Problem:** Codex default sandbox (`workspace-write`) blocks DNS → `cargo build`/`cargo fetch` can't reach crates.io.

## The Fix: `--sandbox danger-full-access`

Removes all network/filesystem restrictions. Cargo build works normally.

```bash
codex exec --sandbox danger-full-access --full-auto "<prompt>"
```

Or fully bypass sandbox (for already-isolated environments):
```bash
codex exec --dangerously-bypass-approvals-and-sandbox "<prompt>"
```

**Note:** `--full-auto` alone sets approval policy to "on-request" with `workspace-write` sandbox — network still blocked. You need `--sandbox danger-full-access` explicitly.

**Default routing:** Gemini still preferred for single-file Rust (runs locally, no Max20 cost). Use Codex + `danger-full-access` when multi-file repo navigation is the bottleneck.

---

## When to use each approach

| Scenario | Approach |
|----------|----------|
| Single-file Rust CLI | Gemini — simpler, free, no sandbox config needed |
| Multi-file Rust, repo nav is the bottleneck | Codex `--sandbox danger-full-access` |
| Diagnosis only (find the bug, don't fix+verify) | Codex default (no build needed) → Gemini fixes |
| Logic changes, no new deps | Codex edits → run `cargo build` manually after |

---

## Option 1: cargo vendor (reliable, repo bloat trade-off)

Pre-download all crates into the repo so Codex can build without DNS.

```bash
cd ~/code/<project>
cargo vendor

# Add to .cargo/config.toml (cargo vendor prints this — copy it):
# [source.crates-io]
# replace-with = "vendored-sources"
# [source."vendored-sources"]
# directory = "vendor"
```

Then in your Codex prompt:
```
Use `cargo build --offline` for all builds. Deps are pre-vendored.
```

**Cost:** `vendor/` dir can be 20–200MB depending on dep tree. Worth it for multi-file projects where Codex's repo nav adds real value; overkill for single-file CLIs.

**Gitignore or commit?** Commit `vendor/` so delegates don't need network. Add to `.gitignore` if you don't want it in history (but then Codex can't use it).

---

## Option 2: Codex diagnose → Gemini build (handoff pattern)

Use each tool for its strength. Already documented in rector.

```
Step 1: Codex — "Navigate ~/code/<project>, diagnose <bug/feature>, 
         produce a detailed implementation plan with exact file paths 
         and line numbers. Do NOT run cargo build."

Step 2: Gemini — "Implement the following plan from Codex: <paste output>. 
         Run cargo build --release to verify."
```

Best for: complex bugs where the diagnosis requires reading across many files.

---

## Option 3: Local cache (unreliable)

If crates were previously built on this machine, they live in `~/.cargo/registry`. Codex *might* be able to use them with `cargo build --offline` — depends on whether the sandbox exposes the home directory. Not consistently reliable; don't count on it.

---

## Summary

- **Single-file Rust CLI** → Gemini, always.
- **Multi-file Rust, need repo nav** → vendor + Codex, or Codex→Gemini handoff.
- **Diagnosis only** → Codex alone is fine (no build needed).
