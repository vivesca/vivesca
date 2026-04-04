---
name: pondus
description: "AI model benchmark aggregator CLI. Use when comparing models, checking benchmark scores, or looking up leaderboard rankings."
user_invocable: true
disable-model-invocation: true
---

# Pondus

Opinionated AI model benchmark aggregator. Rust CLI, open-source.

- **Repo:** `~/code/pondus` | [GitHub](https://github.com/terry-li-hm/pondus) | [crates.io](https://crates.io/crates/pondus)
- **Version:** 0.6.1 (Mar 2026)
- **Install:** `cargo install pondus`

## Architecture

```
src/
├── main.rs          # CLI (clap derive): sources, compare, rank, recommend subcommands
├── models.rs        # Core types: ModelScore, SourceResult, MetricValue, SourceStatus
├── alias.rs         # Model name → canonical alias resolution (exact + prefix matching)
├── cache.rs         # JSON file cache in dirs::cache_dir()/pondus/ (macOS: ~/Library/Caches/pondus/)
├── config.rs        # Config from ~/.config/pondus/config.toml
├── output.rs        # Table/JSON/YAML output formatting
├── recommend.rs     # recommend subcommand: task taxonomy → source ranking → top N output
└── sources/
    ├── mod.rs       # Source trait + registry
    ├── aa.rs        # Artificial Analysis (REST API primary, scrape fallback)
    ├── arena.rs     # LMSYS Arena (agent-browser scrape, JSON fallback)
    ├── seal.rs      # Scale SEAL (agent-browser scrape)
    ├── swebench.rs  # SWE-bench (GitHub JSON API)
    ├── swebench_r.rs # SWE-rebench (agent-browser scrape)
    ├── aider.rs     # Aider polyglot (raw YAML from GitHub)
    ├── livebench.rs # LiveBench (HuggingFace datasets-server API)
    ├── tbench.rs    # Terminal-Bench (agent-browser scrape)
    └── mock.rs      # Test mock source
```

## Source Trait Pattern

Every source implements `Source`:
```rust
pub trait Source {
    fn name(&self) -> &str;
    fn fetch(&self, config: &Config, cache: &Cache) -> Result<SourceResult>;
}
```

`SourceResult` contains `Vec<ModelScore>` where each score has:
- `model`: normalized lowercase name (for alias matching)
- `source_model_name`: original name from source
- `metrics`: `HashMap<String, MetricValue>` (source-specific keys)
- `rank`: optional ordering

## Key Patterns

### AA uses REST API (v0.5.0+)
Primary: `GET https://artificialanalysis.ai/api/v2/data/llms/models` with `x-api-key` header.
Returns 394 models (vs 76 from scrape) including older/superseded models.
API key: `[artificial-analysis] api_key` in config.toml, or `AA_API_KEY` env var.
Falls back to agent-browser scrape if no key configured.
Response parsed via typed structs (`AaApiResponse` → `AaApiModel` → `AaApiEvaluations`).
Free tier: 1000 req/day.

### Scrape sources use agent-browser accessibility snapshots
Four sources scrape via `agent-browser snapshot` which returns an accessibility tree, not HTML.
Parse structured elements (`- row "..."`, `- cell "..."`, `- link "..."`) not flat text.

**Cell parser pattern** (used in Arena, SWE-rebench):
```rust
// Collect cells from row, extract values by position
if trimmed.starts_with("- cell \"") {
    if let Some(val) = extract_cell_value(cell_line) {
        cells.push(val);
    }
}
```

**Forward parser pattern** (used in SEAL):
Finds ±score anchors first, then walks backwards to find rank + model name.

### Alias resolution
`alias.rs` maps source model names → canonical names in two phases:
1. **Exact match** from `aliases.toml` lookup table
2. **Prefix match** fallback (v0.6.1 rule): `source_name.starts_with(alias)` with longest-match-wins. Allowed suffixes after alias: `(` or space (parenthetical qualifier), or `-digit` (date/version). **`-letter` suffix is blocked** — prevents `o3` from swallowing `o3-pro`, `o3-mini`. Add explicit aliases in models.toml for deployment-name patterns like `gpt-5.2-chat-latest`.

**Aggregate vs check:** `rank --aggregate` uses raw normalized model names (no alias resolution) — sources group by their own `model` field. `check` and `compare` use alias resolution. Fix alias bugs in models.toml; they only affect `check`/`compare`, not aggregate ranks.

### Cache
JSON files in `~/Library/Caches/pondus/` (macOS). TTL-based. Each source caches its parsed data.
**Clear a source cache:** `rm ~/Library/Caches/pondus/<source>.json`

## Source-Specific Gotchas

| Source | Gotcha |
|---|---|
| **AA** | API primary (394 models), scrape fallback (76 models). API key in config or `AA_API_KEY` env. API model names have parenthesized suffixes like `"(Reasoning)"` — prefix match resolves them. Scrape: intelligence index is cell[3]. |
| **Arena** | Multiple leaderboard tables (Text, Vision, Image Gen, Video Gen). Image/video models filtered by keyword. First table detected by `- row "1 "`. Claude Sonnet 4.6 outranks Opus on Arena (creative writing bias). |
| **SEAL** | Benchmark cards use `±` in score values. Model names may have trailing `*` (footnotes) — stripped. Scores averaged across benchmarks per model. |
| **SWE-bench** | Tests agent+model scaffolds, not raw models. Deduplicates by keeping highest `resolved_rate` per `source_model_name`. 367→301 after dedup. |
| **SWE-rebench** | Tests raw model performance. Same model scores 20-30pts lower than SWE-bench (no agent scaffold). |
| **LiveBench** | HuggingFace datasets-server API, batch limit 100 (not 1000). Dataset frozen since April 2025 — effectively dead. Warns automatically when in scope. |
| **Terminal-Bench** | `AGENT__Model` format: canonical uses model part only (agent prefix stripped in v0.6.0). |
| **Aider** | Raw YAML from GitHub. Cost metric has legitimate zeros (free models) and extreme max (o1 at $186). |
| **Terminal-Bench** | `AGENT / Model` format breaks alias matching. Only 8 entries. |

## Build Gotchas

- **Stale binary:** `cargo build`/`cargo run` may say "Finished" without recompiling. Fix: `cargo clean -p pondus` then build.
- **Cargo.lock:** Must be committed before `cargo publish` (rejects dirty working dir).
- **Cache location:** `dirs::cache_dir()` on macOS = `~/Library/Caches`, not `~/.cache`.
- **PyPI publish:** `uv run --with build python3 -m build && uvx twine upload dist/*` (uv doesn't read ~/.pypirc).

## Publishing Checklist

1. Bump version in both `Cargo.toml` and `pyproject.toml`
2. `git add Cargo.toml pyproject.toml Cargo.lock && git commit`
3. `cargo publish`
4. `rm -rf dist/ && uv run --with build python3 -m build && uvx twine upload dist/*`
5. `git push`

## Data Quality

Audit script at `/tmp/pondus_audit.py` (not committed). Checks:
1. Score sanity (zeros, negatives, extreme outliers)
2. Arena ELO range
3. Source freshness (which models present)
4. Cross-source consistency (SWE-bench vs SWE-rebench deltas)
5. LiveBench value assessment

Analysis note: `~/epigenome/chromatin/Pondus - Benchmark Analysis Feb 2026.md`

## Delegation Pattern

AA API integration was delegated to Codex (GPT-5.3-codex) — good fit for agentic repo-navigation tasks.
Codex wrote the typed structs, config wiring, and fetch logic. Claude fixed the prefix match boundary char (space) that Codex couldn't test without the live API.
Lesson: delegate the implementation, review the integration points.

## Aggregate Reliability Notes (Mar 2026)

Audited via `pondus check <model> --show-matches`. Findings:
- **TOML keys with dots** (`[kimi-k2.5]`) are parsed as nested keys by TOML. Must quote: `["kimi-k2.5"]`.
- **`cargo build --release` ≠ `cargo install --path .`** — build updates `target/release/` but not the installed binary in `~/.cargo/bin/`. Always install after build to avoid stale binary confusion.
- **Kimi K2.5** only has 1 reasoning source (AA). Mainly a coding model (swebench, swe-rebench). Using it in a reasoning-focused council (consilium) is thinly validated — preference over DeepSeek R1 is on lab diversity grounds, not reasoning benchmark depth.
- **GLM-5** has 2 reasoning sources (AA + Arena) and 4 total — best-validated Chinese model in the aggregate as of Mar 2026.
- **`--tag reasoning` sources**: AA, Arena, LiveBench, Seal. LiveBench frozen since Apr 2025 — effectively stale.

## Council Composition Rationale (consilium, Mar 2026)

Swapped DeepSeek R1 → Kimi K2.5 based on:
- R1 (Jan 2025) unranked on AA, weakest on Aider vs Kimi
- `pondus rank --aggregate --tag reasoning` confirms: GLM-5 rank 3 (0.818, 2 sources), Kimi K2.5 rank 1 on AA (0.972) but only 1 reasoning source
- Lab diversity: Moonshot (Kimi) + Zhipu (GLM) + xAI (Grok) + Anthropic (judge) = 4 distinct orgs
- Current council (Mar 2026): GPT-5.2-pro, Gemini-3.1-pro-preview, Grok-4, DeepSeek-V3.2, GLM-5 (Kimi removed: connection failures)

### Role review (2026-03-03)

Reviewed whether to swap judge (Opus 4.6) ↔ critique (Gemini 3.1 Pro Preview). Kept current setup.

**Benchmark snapshot** (AA intelligence index):
- Gemini 3.1 Pro Preview: AA #1 (57), Arena #4 (ELO 1500) — strongest on AA
- Claude Opus 4.6: AA #3 (53), Arena #2 (ELO 1503) — strongest on Arena
- GLM-5: AA #6 (50), Arena #14 (1451)
- GPT-5.2 (xhigh): AA #5 (51), Arena #7 (1481)
- Kimi K2.5: AA #9 (47), no Arena entry — coding-strong, reasoning thinly validated
- Grok-4: AA #15 (42) — weakest panelist; Arena match unreliable (matched grok-4-1-fast-search, different endpoint)

**Why Opus stays as judge:** Judge independence from the council is the primary architectural property. Opus is not a panelist — it reads all 5 voices without skin in the game. Gemini IS a panelist; promoting it to judge creates a model evaluating its own panel output. The 4-point AA gap doesn't justify breaking independence.

**Gemini as critique:** Imperfect — it's both a panelist and the critique layer, so it may re-assert its own position when reviewing Opus's synthesis. Acceptable because: (a) judge independence is the structural guarantee, critique is advisory; (b) no strong non-panelist alternative exists.

**Grok-4 as weakest panelist:** Keep for lab diversity (xAI training pipeline ≠ others). No stronger xAI model available.

**Fix shipped:** Added `CONSILIUM_MODEL_CRITIQUE_ENV` env var so critique model is now configurable, matching the judge env var pattern.

## recommend subcommand (v0.7+)

`pondus recommend <task>` answers "which model should I use for this?" — maps task types to relevant benchmark sources, fetches, and ranks top N.

```bash
pondus recommend coding                          # top 5 by SWE-bench (primary) + Terminal-Bench + Aider + SWE-rebench
pondus recommend intelligence                    # top 5 by AA intelligence index
pondus recommend intelligence --effort max       # filter to max-effort (reasoning) AA variants only
pondus recommend agentic                         # Terminal-Bench (primary) + SEAL
pondus recommend general                         # Arena ELO
pondus recommend cost                            # OpenRouter, cheapest first (prompt + completion combined)
pondus recommend coding --top 10 --format table
pondus recommend --list-tasks                    # print available tasks with descriptions
pondus recommend --list-tasks --format json      # machine-readable
```

**Task taxonomy:**

| Task | Primary source | Other sources | Sort |
|---|---|---|---|
| `coding` | SWE-bench | Terminal-Bench, Aider, SWE-rebench | resolved_rate ↓ |
| `agentic` | Terminal-Bench | SEAL | tasks_completed ↓ |
| `intelligence` | Artificial Analysis | — | intelligence_index ↓ |
| `general` | Arena | — | elo_score ↓ |
| `cost` | OpenRouter | — | prompt+completion ↑ |

**Key behaviour:**
- Models with no data for that task are excluded entirely
- When a model appears in multiple sources: each source gets its own column, no averaging
- Ranking is by primary source first; secondary sources used as tiebreaker
- `--effort` flag (max/standard/all) only applies when AA is in scope (intelligence task)
- `--format table|json|markdown` reuses existing format flag

**Gotcha (coding/agentic):** SWE-bench tests agent+model scaffolds — top results show compound names like `live-swe-agent-+-claude-4.5-opus`. These are not raw model scores. SWE-rebench tests raw models without scaffolding (20-30pt lower).

## compare --effort flag (v0.6+)

```bash
pondus compare opus-4.6 sonnet-4.6 --effort max       # compare only max-effort (reasoning) AA variants
pondus compare opus-4.6 sonnet-4.6 --effort standard  # standard effort only
pondus compare opus-4.6 sonnet-4.6 --effort all       # default, shows all effort levels
```

## Watching New Models (`pondus watch`)

Track a newly-released model until all benchmark sources index it:

```bash
# One-shot coverage check
pondus watch gpt-5.4 --once

# Hourly polling until all sources covered (run in tmux, survives session)
pondus watch gpt-5.4 --interval 3600

# Review current status any time
pondus check gpt-5.4 --format table
pondus watch gpt-5.4 --once   # same but shows ✓/✗ per source
```

Output shows which sources have data (✓) and which don't (✗), plus rank/score where available. Exits 0 when all covered, 1 if any missing (--once mode). Runs in background via `run_in_background: true` — dies on reboot, just relaunch in tmux if needed.

**GPT-5.4 watch status (as of Mar 6, 2026):** 1/8 sources (Arena only). Recheck daily until aider, swebench, AA, tbench catch up. Note: OpenRouter access opened Mar 6. GPT-5.4-Pro was trialled in consilium but removed (907s latency — unusable). GPT-5.2-pro remains M1.

## Future Work (low priority)

- Terminal-Bench: strip `AGENT /` prefix for alias matching
- LiveBench: deprecate or flag as stale
- `--time-decay` weighting for older benchmark results
