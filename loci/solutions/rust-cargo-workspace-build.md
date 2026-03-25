# Rust Cargo Workspace Build Paths

When a project is part of a workspace (`~/code/Cargo.toml` lists it as a member), `cargo build --release` run from the project dir still outputs to the **workspace root's target dir**, not the project's own target.

## Pattern

```
~/code/Cargo.toml          ← workspace root
~/code/iter/Cargo.toml     ← member
~/code/iter/src/main.rs

cargo build --release (run from ~/code/iter/)
→ binary lands at: ~/code/target/release/iter
→ NOT at:          ~/code/iter/target/release/iter
```

## Install step

```bash
cp ~/code/target/release/<name> ~/bin/<name>
```

Not `~/code/<name>/target/release/<name>` — that path doesn't exist.

## Date
2026-03-08
