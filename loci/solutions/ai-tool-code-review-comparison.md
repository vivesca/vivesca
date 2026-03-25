# AI Tool Code Review Comparison

**Date:** 2026-02-22
**Task:** Review photoferry (4.2K Rust + 402 Swift) for import correctness
**Ground truth:** `cargo check` — 2 warnings (dead `find_sidecar` fn, dead `sidecar`/`sidecar_strength` fields)

## Round 1: Bundled Source in Prompt (158KB)

| | **CC Opus 4.6** | **Codex (GPT-5.3)** | **Gemini 3 Pro** | **OpenCode (GLM-5)** |
|---|---|---|---|---|
| **Time** | 82s | ~80s | ~30s | N/A |
| **Tokens** | 87K | 61K | N/A (free) | N/A |
| **Tool uses** | 13 | 4 | 0 (pure inference) | 0 |
| **Approach** | Read files + `cargo check` + grep | `cargo check` (sandbox fail) → `rg` | Pure static analysis on bundled source | Degenerate output |
| **Report?** | Yes, structured | Yes, structured | Yes, structured | No — gibberish |
| **True positives** | 3/3 | 3/3 + bonus | 2/3 | 0 |
| **False positives** | 0 | 0 | ~8 | N/A |

Note: Codex ignored bundled source and used its own tools — proving bundling was unnecessary.

## Round 2: Short Prompt + File Access (~250 chars)

| | **Gemini (auto-routed)** | **OpenCode (GLM-5)** |
|---|---|---|
| **Approach** | `read_file` + `grep_search` (no shell access) | No output |
| **Report?** | Yes, structured | No — 4 lines (model routing only) |
| **True positives** | 4: `find_sidecar`, `classify_extension`, `Person`, `hmac` | 0 |
| **False positives** | **0** (fixed from Round 1!) | N/A |
| **Complications** | Repeated Flash 429s, no `run_shell_command` available | GLM-5 produced nothing — ran from `~` with no project context |

**Key improvement:** Gemini v2 with file access eliminated all 8 false positives from v1. Path-qualified import errors were caused by single-pass reasoning on bundled source without ability to verify.

## Round 3: Forced Pro + Correct Working Directory

| | **Gemini 3 Pro (forced `-m gemini-3-pro-preview`)** | **OpenCode (GLM-5) from `~/code/photoferry`** |
|---|---|---|
| **Approach** | `read_file` + `grep_search`, no Flash 429 noise | No output |
| **Report?** | Yes — cleanest report of all rounds (56 lines) | No — 4 lines (model routing only) |
| **True positives** | 5: `find_sidecar`, `build_url`, `classify_extension`, `parse_sidecar`/metadata structs, `hmac` | 0 |
| **False positives** | **0** | N/A |
| **Quality** | Best signal-to-noise of all runs. Actionable recommendations with specific visibility fixes (`pub(crate)`, `fn`, `#[cfg(test)]`). | GLM-5 non-functional for code review even with correct cwd |

**Key finding:** Forcing Pro skips Flash 429 backoff noise, produces a cleaner and more thorough report. `-m gemini-3-pro-preview` is the correct flag (not `-m gemini-3-pro`, which 404s).

## Final Rankings

| | **CC Opus 4.6** | **Codex (GPT-5.3)** | **Gemini 3 Pro (forced)** | **OpenCode (GLM-5)** |
|---|---|---|---|---|
| **Accuracy** | 1st | 1st (tied) | 1st (tied) | Failed |
| **Thoroughness** | 1st | 2nd | 2nd (tied) | N/A |
| **Speed** | 3rd (82s) | 3rd (80s) | 1st (~60s) | N/A |
| **Report quality** | Detailed with explanations | Detailed with bonus findings | **Best** — cleanest, most actionable | N/A |
| **Cost** | $$$ (Max plan) | Free | Free | Free |
| **Best for** | Nuanced analysis, dependency chain reasoning | Cost-effective accurate review | **Best overall for code review** (when forced to Pro) | Not viable |

## Key Findings

### Opus 4.6 (Claude Code)
- Matched compiler ground truth exactly (3 findings, 0 false positives)
- Correctly explained *why* `hmac` is unused (pbkdf2 re-exports HMAC internally)
- Most thorough: 13 tool calls, read every file, ran cargo check, verified with grep

### Codex (GPT-5.3)
- `cargo check` failed due to Swift toolchain sandbox permissions — pivoted to `rg` cross-referencing
- Zero false positives despite no compiler assistance
- Found additional valid suggestions: `build_url`, `classify_extension` could be private
- Best cost/accuracy ratio (free + accurate)

### Gemini 3 Pro
- **v1 (bundled source):** 30s, but ~8 false positives from flagging valid Rust path-qualified imports as "missing"
- **v2 (file access, auto-routed):** 0 false positives — verified findings with `grep_search` before reporting. But Flash 429s added latency and noise.
- **v3 (forced Pro):** Best report overall — 0 false positives, cleanest output, actionable visibility recommendations. Force Pro with `-m gemini-3-pro-preview` (not `-m gemini-3-pro`, which 404s).
- No shell access (`run_shell_command` not available) — can't run `cargo check`. Limited to `read_file`, `grep_search`, `list_directory`.

### OpenCode (GLM-5)
- **v1 (158KB prompt):** Degenerate multilingual gibberish — context overflow
- **v2 (250 char prompt, cwd=`~`):** Silent failure — no output, no project context
- **v3 (250 char prompt, cwd=`~/code/photoferry`):** Same silent failure — 4 lines, model routing only
- **GLM-5 is not viable for code review via `opencode run`.** Three attempts, three failures. The issue is the model, not the prompt or cwd.

## Lessons

1. **Don't bundle source into prompts when tools have file access.** Let them read files — it's more accurate (Gemini false positives disappeared in v2) and avoids context overflow (OpenCode v1). Codex proved this by ignoring bundled source entirely.
2. **For Rust: compiler-assisted review >> static analysis.** `cargo check` finds real dead code with zero false positives. Only CC and Codex attempted it.
3. **Codex sandbox blocks Swift toolchain** — `cargo check` fails when swift-rs needs SwiftPM cache access. Codex recovered gracefully by pivoting to grep.
4. **Gemini CLI: force Pro with `-m gemini-3-pro-preview`.** Auto-routing bounces between Flash (429s) and Pro, adding noise. Forcing Pro is faster and produces better reports. Note: `-m gemini-3-pro` returns 404.
5. **Gemini CLI has no shell execution** — only `read_file`, `grep_search`, `list_directory`. Can't run compilers or linters. Limits it to static analysis, but still sufficient for accurate review.
6. **CC scout (Haiku) was wrong agent type for this task** — spent all turns on compilation, never produced a report. Opus with general-purpose agent was correct.
7. **Always read full tool output** — initially reported Codex as "cut off" when it had 300+ more lines of complete analysis.
8. **OpenCode CLI is fine; GLM-5 headless is broken.** OpenCode + GPT-4.1-mini works perfectly (instant responses, tool use). GLM-5 via ZhipuAI Coding Plan API produces zero events in headless mode — even for "Say hello". The API hangs silently. GLM-5 may only work in interactive OpenCode terminal, not `opencode run`.
