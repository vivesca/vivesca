# Rust Toolchain Setup

Last updated: 2026-03-01

## Toolchain

- **rustc:** stable, managed via `rustup update stable`
- **cargo:** ships with rustup

## Core Components (ships with rustup)

```bash
rustup component add clippy rustfmt rust-analyzer
```

| Component | Purpose |
|-----------|---------|
| `clippy` | Linter — run before every commit |
| `rustfmt` | Formatter — PostToolUse hook auto-runs on `.rs` edits |
| `rust-analyzer` | LSP — IDE integration |

## Installed Cargo Tools

Install order: `cargo-binstall` first (downloads prebuilt binaries, skips 10min compile), then binstall the rest.

```bash
cargo install cargo-binstall
cargo binstall cargo-release cargo-semver-checks  # publishing workflow
```

| Tool | Purpose | Notes |
|------|---------|-------|
| **cargo-binstall** | Downloads prebuilt binaries instead of compiling | Meta-tool, install first |
| **bacon** | Background file watcher — live clippy/test on save | Replaces cargo-watch (dead) |
| **cargo-nextest** | Faster test runner (2–3× over cargo test) | No doctest support — run `cargo test --doc` separately |
| **cargo-deny** | Security (CVEs) + license policy + banned crates + duplicates | Superset of cargo-audit; use this |
| **cargo-edit** | `cargo upgrade` — bumps Cargo.toml version constraints | `cargo add`/`rm` built into cargo since v1.62/1.66 |
| **cargo-machete** | Find unused dependencies (fast regex-based) | cargo-udeps is broken (nightly + workspace issues); use this |
| **cargo-hack** | Test all feature flag combinations | Essential for published library crates |
| **cargo-expand** | Expand proc macros in-place | Essential for debugging `#[derive(...)]` and serde |
| **cargo-bloat** | Show what's taking space in the binary | |
| **samply** | CPU profiler — results in Firefox Profiler UI | Cross-platform default; DTrace-free on macOS |
| **flamegraph** | Generate SVG flamegraphs | Linux (perf) + macOS (DTrace) |
| **typos-cli** | Source code spell checker | Fast; Cargo team nearly adopted it officially |
| **cargo-release** | One-command version bump + git tag + publish | |
| **cargo-semver-checks** | Lint for SemVer violations before publish | |
| **cargo-outdated** | Show outdated dependencies | |

### Not installed (available when needed)

| Tool | When to install |
|------|----------------|
| **cargo-shear** | More thorough unused dep check than machete (AST-based via rust-analyzer) |
| **criterion** | Benchmarking — statistically rigorous |
| **divan** | Benchmarking alternative — built-in allocation profiling |
| **insta** | Snapshot testing with inline snapshots |
| **cargo-msrv** | Find minimum supported Rust version |
| **cargo-dist** | Distributing via GitHub Releases (beyond crates.io) |
| **cargo-zigbuild** | Cross-compiling Linux from Mac — needs `brew install zig` |
| **sccache** | Build cache for CI/CD (S3/GCS/Azure). Set `CARGO_INCREMENTAL=0` when using |
| **just** | Command runner replacing Makefiles — wrap `cargo hack`, `cargo nextest` etc. |

## Linker (free performance)

Rust 1.90 (Sep 2025) made LLD the default on Linux. macOS still needs manual config.

Add to `~/.cargo/config.toml`:

```toml
[target.aarch64-apple-darwin]
rustflags = ["-C", "link-arg=-fuse-ld=lld"]
```

7× faster linking on incremental rebuilds on Linux. macOS gains are smaller but still meaningful.

## Release Profile for Small CLIs

Add to `Cargo.toml` — cuts binary ~46% (e.g. 2.8MB → 1.5MB):

```toml
[profile.release]
opt-level = "z"       # optimize for size
lto = true            # link-time optimization
codegen-units = 1     # better optimization, slower compile
panic = "abort"       # smaller binary, no unwinding
strip = true          # strip debug symbols
```

## Hooks

PostToolUse hook at `~/.claude/hooks/post-edit-rust-format.js` runs `rustfmt` on `.rs` file edits automatically.

Clippy is too slow for per-edit (it compiles). Run manually:
- `cargo clippy` — before committing
- `cargo clippy --fix --allow-dirty` — auto-fix

## Pre-Publish Checklist

```bash
cargo fmt --check              # formatting
cargo clippy                   # linting
cargo machete                  # unused deps
cargo outdated -R              # stale deps
cargo deny check               # security CVEs + license policy
cargo semver-checks            # breaking changes (library crates)
cargo hack --feature-powerset clippy -- -D warnings  # all feature combos (library crates)
cargo release version minor --execute  # bump version
cargo publish                  # ship it
```

## Gotchas

- **`cargo-udeps` is broken** — requires nightly, doesn't work with recent Cargo/workspaces. Use `cargo-machete` instead. Many tutorials still recommend udeps — ignore them.
- **`cargo-watch` is dead** — maintainer explicitly recommends switching to bacon or watchexec.
- **`cargo-audit` superseded** — use `cargo-deny` (superset: all audit features + license policy + banned crates).
- **`cargo add`/`rm` built in** — only install `cargo-edit` for `cargo upgrade` (bumps Cargo.toml, not just Cargo.lock).
- **`cargo-nextest` doctest gap** — no doctest support. Run `cargo nextest run && cargo test --doc` in sequence. No duplicate compilation triggered.
- **`flamegraph` crate name** — `cargo install flamegraph` (NOT `cargo-flamegraph` — doesn't exist on crates.io).
- **`cargo-nextest` requires `--locked`** — `cargo install cargo-nextest` fails with a compile error. Must use `cargo install --locked cargo-nextest`. This is enforced by the crate itself via a `locked-tripwire` dependency.
- **sccache + incremental** — cache hit rate degrades with incremental compilation. Set `CARGO_INCREMENTAL=0` in CI when using sccache.
- **`str` slicing panics on multi-byte chars** — `text[start..end]` panics if boundary lands inside a multi-byte char (CJK, emoji). Use `.is_char_boundary(idx)` or `.chars().take(n)`. Hit in `resurface` with Chinese characters.

## Rust vs Python: When to Use Which

Decision made Feb 2026. Claude writes both equally well — choose based on end product.

**Use Rust for:**
- CLI tools others install (single binary, no runtime dependency)
- Performance-critical code
- Anything published to crates.io / distributed as binary

**Use Python for:**
- Prototyping and throwaway scripts
- AI/ML work (PyTorch, numpy, pandas — no Rust equivalents)
- Glue code connecting services
- Anything using uv/pip ecosystem heavily

**Key insight:** "Python is faster to write" is irrelevant when Claude writes it. Optimise for the end product, not developer ease.
