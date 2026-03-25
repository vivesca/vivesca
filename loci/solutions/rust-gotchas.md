# Rust Gotchas

Project-agnostic Rust patterns that bite repeatedly. Hot-context shortcuts are in MEMORY.md; detail lives here.

---

## Chained `.unwrap_or()` references outer scope, not intermediate

**Symptom:** Processing seems to work but a transformation silently reverts — e.g., stripping `#anchor` from a string produces the original string instead of the stripped one.

**Root cause:** When chaining method calls, `.unwrap_or(x)` captures `x` at the call site. If you're building a chain where each step should fall back to the *previous step's result*, you must break the chain.

```rust
// BUGGY — second unwrap_or falls back to `trimmed` (original), not `after_hash`
let result = trimmed
    .split_once('#').map(|(h, _)| h).unwrap_or(trimmed)
    .split_once('^').map(|(h, _)| h).unwrap_or(trimmed); // ← wrong: trimmed, not after_hash

// CORRECT — intermediate binding captures the first transform
let after_hash = trimmed
    .split_once('#')
    .map(|(h, _)| h)
    .unwrap_or(trimmed);
let result = after_hash
    .split_once('^')
    .map(|(h, _)| h)
    .unwrap_or(after_hash); // ← correct: falls back to after_hash
```

**Real case:** `normalize_target()` in nexis v0.2.0 — `[[Note#Section]]` links reported broken even when `Note.md` existed, because the anchor wasn't stripped. Fixed in v0.2.1 by introducing `after_hash` intermediate.

---

## Regex crate: no lookahead/lookbehind

`(?=...)`, `(?!...)`, `(?<=...)`, `(?<!...)` are unsupported. Delegates (Codex/Gemini) routinely port these from Python regex without checking.

**Fix:** Use capture groups. E.g., to match optional prefix: `(!?)\[\[...\]\]` — group 1 is `"!"` or `""`.

Always `cargo clippy` after delegation involving regex.

---

## Cargo incremental build silently skips recompilation

`cargo build` / `cargo run` may print `Finished` without recompiling, even after source changes. Observed with `cargo run` piping stderr.

**Fix:** `cargo clean -p <crate>` then rebuild.

---

## Codex sandbox: no network (crates.io blocked)

`cargo build` / `cargo fetch` fail with DNS errors inside Codex. Codex can write correct source but can't verify compilation.

**Workflow:** Write source in Codex → build in normal shell: `cargo build --release`.

---

## `cd` into target repo before `codex exec`

Running `codex exec` from a different directory gives read-only access to the target. Always:

```bash
cd ~/code/myproject && codex exec --full-auto "..."
```

Drop `--skip-git-repo-check` when already inside the target repo.

---

## Always add `.gitignore` before the first `git add -A` on a new Rust project

`cargo new` creates a `target/` dir immediately. If you `git init && git add -A` before adding `.gitignore`, the entire build cache gets committed (280+ files). Fix retroactively:

```bash
echo '/target' > .gitignore
git rm -r --cached target/
git add .gitignore
git commit -m "chore: add .gitignore, remove target from tracking"
```

**Prevention:** `echo '/target' > .gitignore` immediately after `cargo new`, before any git init.

*Real case: nexum v0.1.0 initial commit, 2026-03-06.*
