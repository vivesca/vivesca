# Rust Tooling Ecosystem (as of early 2026)

## Reliable Sources for This Topic
- blessed.rs/crates — hand-curated community consensus; WebFetch works; authoritative for "blessed" designations
- nnethercote.github.io/perf-book/profiling.html — Rust Performance Book; authoritative for profiling tools
- nexte.st — official cargo-nextest docs; WebFetch works
- dystroy.org/bacon — official bacon docs; WebFetch works
- blog.rust-lang.org — official Inside Rust blog for Cargo release notes
- embarkstudios.github.io/cargo-deny — cargo-deny official docs
- rustprojectprimer.com — Rust Project Primer; good secondary source; WebFetch works
- logrocket.com/blog — good for tool comparisons; WebFetch works

## The "Blessed" Stack (Beyond rustup/cargo/clippy/rustfmt/rust-analyzer)

### 1. Test Runner: cargo-nextest
- **Status:** Pre-1.0 (v0.9.94 as of Apr 2025) but production-ready; powers Rust at largest tech companies
- **Speed:** Up to 3x faster than `cargo test` via parallel execution model
- **Key limitation:** No doctest support — still requires `cargo test --doc` as a separate step
- **Verdict:** Community consensus "blessed" choice; no real alternative in the ecosystem
- blessed.rs explicitly marks nextest as recommended

### 2. File Watcher: bacon (not cargo-watch)
- **cargo-watch maintainer explicitly recommends bacon (or watchexec) over cargo-watch**
- cargo-watch is effectively on life support — no further development
- bacon is Rust-specific: understands workspace structure, parses compiler output, supports test filtering
- watchexec is the general-purpose alternative (cross-language, if you need that)
- **Verdict:** bacon is unambiguously preferred by the community in 2025-2026

### 3. Security Auditing: cargo-deny (not cargo-audit alone)
- cargo-audit: minimum viable security baseline — checks RustSec advisory DB only
- cargo-deny: superset — advisory scanning + license checking + dependency policy enforcement + banned crates
- Both use same RustSec Advisory Database as vulnerability source
- cargo-deny has a compatibility mode that outputs cargo-audit-identical output
- **Verdict:** cargo-deny for most projects (especially anything library/OSS). cargo-audit only if you want zero config, minimal setup.
- blessed.rs lists BOTH as "blessed" for different reasons: audit (simple check), deny (policy enforcement)

### 4. Dependency Management: Three-tool stack
- **cargo add / cargo rm:** Built into Cargo since 1.62/1.66. cargo-edit NO LONGER needed for these.
- **cargo upgrade:** Still requires cargo-edit (the one remaining reason to install it). `cargo update` only bumps Cargo.lock; `cargo upgrade` bumps Cargo.toml version requirements.
- **Unused dep detection — pick one:**
  - **cargo-machete:** Fast (regex-based), good for CI. Slight false positives. Recommended by rustprojectprimer.com as "go-to".
  - **cargo-shear:** AST-based via rust-analyzer parser. Workspace-aware. Newer (453 stars). Feature-complete per maintainer. Used by turbopack, openai/codex.
  - **cargo-udeps:** Most accurate (requires compilation). Requires nightly. Broken with recent Cargo versions and workspaces as of early 2026 — least viable option currently.
- **Verdict:** cargo-edit for `cargo upgrade` only. cargo-machete for quick CI sweeps; cargo-shear as a more accurate alternative.

### 5. Profiling Tools
- **CPU profiling — macOS:** samply (command-line → Firefox Profiler UI) or Instruments (Xcode). samply works on macOS, Linux, Windows. Instruments needs system allocator swap for memory profiling.
- **CPU profiling — Linux:** perf + Hotspot/Firefox Profiler, or samply.
- **Flamegraphs:** cargo-flamegraph — generates SVG. Works Linux (perf) + macOS/FreeBSD (DTrace).
- **Verdict:** samply is the "easy default" cross-platform pick in 2026. cargo-flamegraph for quick SVG generation. Rust Performance Book endorses samply + platform-native tools.
- **Heap profiling:** dhat (blessed.rs), heaptrack/bytehound (Linux).
- **Benchmarking:** criterion (blessed.rs) is the standard. divan is an emerging alternative with allocation profiling built in.

### 6. Binary Size Tools
- **cargo-bloat:** Identifies what's contributing to binary size (by crate, function). Standard tool.
- **twiggy:** WebAssembly-focused — analyzes call graphs. Use for WASM targets specifically.
- **For native binaries:** cargo-bloat is the primary tool. `cargo build --release` + `strip` + profile settings first.
- **cargo-wizard:** Can configure Cargo.toml for minimum binary size optimization profiles automatically. Notable 2024 addition (featured in Cargo 1.x cycle as plugin of the cycle).
- **Verdict:** cargo-bloat for native; twiggy for WASM.

### 7. Build Caching: sccache
- **sccache:** Mozilla's distributed compiler cache. Still active and widely used. Best for CI/CD with remote storage (S3, GCS). Reported ~40% build time reduction in benchmarks.
- **Limitation:** Incremental compilation artifacts often unique → lower hit rates. Better for clean builds than incremental.
- **Rust 1.90.0 (Sep 2025):** LLD is now the default linker on x86_64-unknown-linux-gnu. 7x faster linking → 40% overall compilation improvement for incremental rebuilds. **This is bigger than sccache for local dev.**
- **Emerging:** "Wild" linker (Rust-written) — benchmarks faster than mold/LLD; watch this space.
- **Verdict:** sccache for CI caching. LLD (now default on Linux) for local dev. mold if you need maximum speed and can afford the RAM.

## Notable Tools in 2025-2026

- **cargo-hack:** Validates feature flag combinations — essential for library crates. `cargo hack --feature-powerset clippy`
- **cargo-msrv:** Finds the minimum supported Rust version for a project.
- **cargo-wizard:** Autoconfigures Cargo.toml for performance/size/build-speed profiles. Low friction.
- **insta:** Snapshot testing library — blessed.rs recommended for snapshot tests.
- **typos-cli:** Fast spell checker; Cargo team proposed adopting it for Cargo itself.
- **just:** Command runner (alternative to Makefile). Widely adopted in Rust projects for task running.
- **cargo-expand:** Expands macros — essential for macro debugging.
- **cargo-show-asm:** Shows generated assembly for a function — blessed.rs listed.

## Rust 2025 Toolchain Changes (Important)
- Rust 1.85 (Feb 2025): Rust 2024 edition stabilized; rustfmt "style editions" introduced
- Rust 1.87 (May 2025): Ten years of Rust; doctests now combined into single executable (improves perf)
- Rust 1.90 (Sep 2025): LLD default on Linux; major link-time improvement

## Misinformation to Watch
- cargo-udeps is often still listed as a recommended tool but is broken with recent Cargo + workspaces
- cargo-watch is still listed in many tutorials but maintainer has deprecated it in favor of bacon
- "cargo upgrade" is NOT the same as "cargo update" — cargo-edit is still needed for the former
- The "40x faster" nextest claims are exaggerated; 2-3x is the realistic range for typical test suites

## Methodology That Worked
- blessed.rs is the single most authoritative community consensus source — check it first
- Rust Performance Book (nnethercote.github.io/perf-book) is authoritative for profiling tool recommendations
- blog.rust-lang.org/inside-rust "This Development-cycle in Cargo" posts have "Plugin of the cycle" recommendations — useful signal
- GitHub issue #194 on cargo-deny (making it the official RustSec frontend) gives historical context
- cargo-shear GitHub README has a "Trophy Cases" section showing real adoption — good credibility signal
