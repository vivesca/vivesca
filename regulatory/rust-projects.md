---
paths:
  - "code/**/*.rs"
  - "code/**/Cargo.toml"
---

## Rust Project Rules

- Binaries: `cargo install --path <crate>` not `cp`.
- **NEVER `git add -A` from `~/code/`.** Stage specific files. Burned: 6300-file commit.
- Delegate prompts → `/tmp/prompt.txt`.
- Never `&` with `run_in_background: true`.
- Each CLI → own private GitHub repo: `gh repo create terry-li-hm/<name> --private`.
