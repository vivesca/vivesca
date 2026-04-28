---
name: rust
description: "Rust CLI development — new project scaffold, daily dev workflow, pre-publish checklist. Use when starting or publishing a Rust CLI."
user_invocable: true
---

# Rust CLI

Three modes: **new** (scaffold), **dev** (daily workflow), **publish** (checklist). Pick the one that matches where you are.

## Triggers

- `/rust new <name>` — scaffold a new CLI project
- `/rust dev` — start a dev session (bacon + reminders)
- `/rust publish` — pre-publish checklist
- `/rust` with no args — ask which mode

## Full reference

`~/docs/solutions/rust-toolchain-setup.md` — installed tools, gotchas, linker config. Read it before doing anything non-obvious.

---

## Mode: New CLI

### 1. Name it via quorate (mandatory)

```bash
consilium "Name a new Rust CLI tool that does X. Latin or Greek preferred. Check crates.io availability." --quick
```

Never propose names without running this first. necto → synaxis was a crates.io collision that cost a full rename.

### 2. Reserve the name on crates.io immediately

Before writing any code — publish a stub to lock the name:

```bash
cargo new <name> --bin
cd <name>
# Add minimal Cargo.toml metadata (name, version, description, license, repository)
cargo publish
```

`fn main() {}` is enough. A name collision mid-build costs a full rename. Grab it first.

### 3. Scaffold

### 3. Cargo.toml — release profile + metadata

Add immediately (before any code):

```toml
[package]
name = "<name>"
version = "0.1.0"
edition = "2024"
description = "<one line>"
license = "MIT"
repository = "https://github.com/terry-li-hm/<name>"
keywords = ["cli", ...]
categories = ["command-line-utilities"]

[profile.release]
opt-level = "z"       # size over speed (right for CLIs)
lto = true
codegen-units = 1
panic = "abort"
strip = true
```

Cuts binary ~46% vs default (e.g. 2.8MB → 1.5MB).

### 4. Agent-native design (mandatory for all CLIs)

Every CLI must work as both a human tool AND an agent tool:

```rust
let is_tty = std::io::stdout().is_terminal();

if is_tty {
    // Pretty output: colours, spinners, tables
} else {
    // Plain output: newline-delimited, no ANSI, machine-parseable
}
```

Import: `use std::io::IsTerminal;`

TTY = human signal. Non-TTY = agent consumer. Design for both from day one.

**Finer distinction — pipe vs file redirect:** `is_terminal()` conflates pipe (`| grep`) and file redirect (`> out.txt`). If you need to distinguish them (e.g. background capture wants full output, piped scripting wants compact), use fstat:

```rust
use std::os::unix::io::AsRawFd;

fn stdout_is_file_redirect() -> bool {
    let fd = std::io::stdout().as_raw_fd();
    unsafe {
        let mut stat: libc::stat = std::mem::zeroed();
        libc::fstat(fd, &mut stat) == 0 && (stat.st_mode & libc::S_IFMT) == libc::S_IFREG
    }
}
```

Then: TTY → human UX, pipe (`S_IFIFO`) → compact/scriptable, file (`S_IFREG`) → full output for capture.

### 5. Test scaffold (mandatory)

Create immediately — no CLI ships without a baseline:

```bash
cargo add --dev assert_cmd predicates
mkdir tests
```

```rust
// tests/cli_test.rs
use assert_cmd::prelude::*;
use predicates::prelude::*;
use std::process::Command;

#[test]
fn test_version() -> Result<(), Box<dyn std::error::Error>> {
    Command::cargo_bin!("<name>").arg("--version").assert()
        .success().stdout(predicate::str::contains("<name>"));
    Ok(())
}

#[test]
fn test_help() -> Result<(), Box<dyn std::error::Error>> {
    Command::cargo_bin!("<name>").arg("--help").assert().success();
    Ok(())
}

#[test]
fn test_no_args_fails() -> Result<(), Box<dyn std::error::Error>> {
    Command::cargo_bin!("<name>").assert().failure();
    Ok(())
}
```

Run immediately: `cargo nextest run` — must pass before any feature work begins.

### 7. Common deps

```bash
cargo add serde --features derive
cargo add serde_json
cargo add toml
cargo add dirs          # XDG home dir
cargo add clap --features derive  # if complex CLI
```

### 6. Config file convention (if needed)

Follow XDG: `~/.config/<name>/config.toml`. Use `dirs::home_dir()` + manual join. `dirs::config_dir()` gives the XDG path directly.

Provide `--init` to generate a default config. Fall back to hardcoded defaults if config absent — never error on missing config.

### 7. GitHub + crates.io

```bash
gh repo create terry-li-hm/<name> --public --source=. --remote=origin --push
cargo publish --dry-run   # check before real publish
cargo publish
```

---

## Mode: Dev

### Daily driver

```bash
bacon          # background clippy/test watcher — leave running in a pane
```

Bacon reruns clippy (and optionally tests) on every save. Much better than cargo-watch (dead) or manual runs.

### Commands to know

```bash
cargo clippy                        # lint
cargo clippy --fix --allow-dirty   # auto-fix
cargo fmt                           # format (also runs via hook on file edit)
cargo nextest run                   # fast test runner (2-3× cargo test)
cargo test --doc                    # doctests (nextest doesn't support these)
cargo expand <item>                 # expand macros (debug #[derive(...)] issues)
cargo machete                       # find unused deps
```

### Rust regex gotcha

The `regex` crate supports lookahead/lookbehind. The `fancy-regex` crate does too. But the **`regex` crate used as a Rust dependency** (not the tool) has no lookahead. Delegates (Codex/Gemini) routinely port Python regexes that use `(?=...)` — always `cargo clippy` after delegation.

---

## Mode: Publish

Run in order. All must pass before bumping version.

```bash
# README exists? (one-time check — skip on subsequent releases)
ls README.md

cargo nextest run                   # all tests must pass — HARD GATE
cargo fmt --check                   # formatting clean?
cargo clippy -- -D warnings         # zero warnings
cargo machete                       # unused deps
cargo outdated -R                   # stale deps worth knowing
cargo deny check                    # CVEs + license policy
# For library crates only:
cargo semver-checks                 # breaking changes
cargo hack --feature-powerset clippy -- -D warnings  # all feature combos
# Ship:
# Personal CLI (no downstream users) — one command does everything:
cargo release patch --no-confirm --execute
# Library / shared tool — keep publish as a separate manual gate:
# cargo release version patch --execute && cargo publish
```

### Version bump strategy

- `patch` — bug fixes, minor tweaks
- `minor` — new features, backwards-compatible
- `major` — breaking changes (rare for personal CLIs)

`cargo release patch --no-confirm --execute` bumps version, commits, tags, and publishes in one shot. Fine for personal CLIs. Use the two-step for anything with real downstream users.

### Before publish — smoke test as real CLI

```bash
cargo install --path .  # install from local source
<name> --version        # verify binary is in PATH and works
<name> <args>           # run actual use case — not ./target/release/<name>
```

Never test a CLI tool via `./target/release/<name>` only — that skips the install path. Always verify the installed binary behaves correctly before publishing.

### After publish (REQUIRED — don't skip)

```bash
cargo install <name>    # verify it installs cleanly from crates.io
<name> <args>           # run an actual use case with the installed binary
```

This is a hard gate — not optional. `./target/release/<name>` and `cargo install --path .` don't test the published artifact. Only `cargo install <name>` does.

**Create a skill** — every personal CLI gets `~/skills/<name>/SKILL.md`. Covers: commands, keychain/config location, gotchas, repo link. This is how the tool stays usable across sessions.

---

## Delegation

For heavy implementation work, delegate rather than implement in Sonnet:

| Task | Route |
|------|-------|
| Complex algorithm, self-contained | Gemini (`gemini -p "..." --yolo`) |
| Multi-file feature, navigate repo | Codex (`codex exec --full-auto "..."`) |
| Architecture / judgment | Stay in Sonnet |

Always include in delegate prompts: "Implement fully. No stubs, no placeholders. Run `cargo clippy` and `cargo nextest run` after."

After delegation: `cargo clippy` — delegates often port Python regexes with lookahead that the Rust regex crate doesn't support.

---

## Gotchas quick ref

- **`cargo-nextest` install:** `cargo install --locked cargo-nextest` (--locked required)
- **flamegraph crate:** `cargo install flamegraph` (NOT `cargo-flamegraph`)
- **cargo-watch dead** → bacon
- **cargo-audit superseded** → cargo-deny
- **cargo-udeps broken** → cargo-machete
- **`cargo add`/`rm` built into cargo** — only install cargo-edit for `cargo upgrade`
- **`cargo build` may not recompile** despite source changes — `cargo clean -p <crate>` then rebuild
- **str slicing + CJK/emoji** → panics at non-char-boundary; use `.chars().take(n)` or `.is_char_boundary(idx)`

Full reference: `~/docs/solutions/rust-toolchain-setup.md`

## Motifs
- [verify-gate](../motifs/verify-gate.md)

## Triggers

- rust
- rust new
- rust crate
- rust cli
- cargo new
- rust scaffold
