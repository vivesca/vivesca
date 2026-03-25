# AI Code Review with Multiple Agents — Lessons Learned

Source: photoferry review (Feb 2026) — Codex (GPT-5.2), OpenCode (GLM-5), Gemini CLI (3-flash/3-pro)

## Signal-to-Noise

- 3 tools produced **28 findings total**. After triage: **3 real bugs, 1 already fixed, ~10 over-engineering suggestions, ~14 noise**.
- Signal-to-noise ratio: ~15-20%. Budget triage time accordingly.
- One finding (Live Photo fallback tracking) was flagged as "HIGH" by OpenCode — **but the feature already existed**. All three reviewers missed the existing `ManifestLivePhotoFallback` struct and `live_photo_fallback_entries` tracking. AI reviewers scan for patterns they expect to find missing; they don't reliably verify existing implementations before flagging gaps.

## Tool Comparison (for code review)

| Tool | Strengths | Weaknesses | Finding quality |
|------|-----------|------------|----------------|
| **Codex** (GPT-5.2) | Sharpest code-level bugs (FFI, panics, early-return logic). Structured output with file:line refs. | Can't build Swift projects — static review only | **Best** — 11 findings, highest hit rate |
| **OpenCode** (GLM-5) | Product-level risks (data loss, auditability). Good migration checklist. | Most noise. Suggests adding support for cameras the user doesn't own. Stale file risk (didn't overwrite existing REVIEW file) | **Good breadth** — 13 findings, but ~40% noise |
| **Gemini CLI** (auto) | Caught `df -k` brittleness others missed. Clean exec summary. | Hammered by 429 `MODEL_CAPACITY_EXHAUSTED` on gemini-3-flash-preview. Only 4 findings — depth severely degraded by rate limits | **Thinnest** — rate limits are the bottleneck, not capability |

**Ranking for code review: Codex > OpenCode > Gemini CLI** (Gemini may improve when capacity stabilizes).

## Patterns

### AI reviewers always suggest MORE code
They never say "this is fine, leave it alone." Every review suggests new structs, new tracking fields, new error paths. The extension list findings (#15) are textbook: suggesting support for Olympus/Panasonic/Fuji/Hasselblad RAW formats the user doesn't own. The refactoring suggestions target a working personal tool.

**Counter-pattern:** After receiving AI reviews, ask "would I have noticed this as a bug during actual use?" If no, it's probably not worth fixing.

### Consensus filtering works
Findings flagged by 2+ tools are higher confidence than single-tool findings. In this review, the only consensus finding (Live Photo >2 variants) was valid. Single-tool findings need manual judgment — some are brilliant (Codex's sidecar `?` bug), others are noise.

### AI reviewers don't verify before asserting absence
The #1 false positive was "Live Photo fallbacks not tracked in manifest" — a feature that existed with dedicated structs, merge logic, and dedup. The reviewers checked the import function but not the manifest schema. Always verify HIGH findings against the actual codebase before acting.

## Second Data Point: rai.py Audit (Feb 2026)

Source: rai.py (~800 lines Python) — Codex (GPT-5.2) + OpenCode (GLM-4.7)

| Tool | Findings | Real bugs | False positives | Signal rate |
|------|----------|-----------|-----------------|-------------|
| **Codex** (GPT-5.2) | 12 | 11 | 1 (deferred low) | **92%** |
| **OpenCode** (GLM-4.7) | 25 | 0 | 25 | **0%** |

GLM-4.7 failure modes on rai.py:
- **Claimed Python integers overflow** (finding #4) — they're arbitrary precision
- **Flagged division-by-zero on guarded sites** (finding #5) — `if total else 0` already present
- **Said `with os.fdopen()` leaks file descriptors** (finding #10) — it's a context manager
- **Flagged "race condition" on single-user CLI** (finding #6) — Claude runs commands sequentially
- **Said "missing timeout on file reads"** (finding #8) — local markdown files

**Key insight:** GLM-4.7 generates plausible-looking audit reports but doesn't actually verify assertions against the code. Codex reads the code, GLM pattern-matches against common vulnerability templates. The 0% signal rate makes GLM-4.7 **actively harmful for audits** — triaging 25 false positives costs more time than it saves.

**Two-phase prompt fix:** Re-ran with "Phase 1: find potential bugs. Phase 2: re-read the code to verify each one before reporting. Drop anything that doesn't survive." Result: 4 findings, 1 real (25% signal). The real find was a genuine edge case (empty History section silently drops records). Massive improvement from 0% → 25%, though still below Codex's 92%.

**Updated ranking: Codex >> OpenCode (GLM-4.7) for code audits.** GLM-4.7 can contribute with a verification prompt but needs hand-holding. Without it, it's pure noise.

## Two-Phase Prompt: Generalized Pattern

The rai.py audit revealed that weaker models fail at code review because they **pattern-match vulnerability templates without reading the code**. The fix is a two-phase prompt that forces verification:

```
Phase 1: Read <file> thoroughly. Context: <personal CLI / server / library>.
         List all potential bugs. DO NOT report yet.

Phase 2: For EACH potential finding, re-read the specific lines to verify:
         - Does the bug actually exist in the current code?
         - Is there already a guard/check that handles it?
         - Is it relevant for <context>?
         Only report findings that survive verification.
```

**Why it works:** Phase 1 lets the model cast a wide net (high recall). Phase 2 forces it to re-read the code and evaluate each candidate (high precision). Without Phase 2, weaker models report Phase 1 candidates as final findings — hence the 0% signal.

**Results across models:**

| Model | Naive prompt | Two-phase prompt | Improvement |
|-------|-------------|-----------------|-------------|
| Codex (GPT-5.2) | 92% signal | ~95%+ (not tested, already high) | Marginal |
| OpenCode (GLM-4.7) | 0% signal | 25% signal | 0% → 25% |

**Applicability beyond code audit:** The two-phase pattern works for any task where weaker models produce plausible-sounding but unverified claims:
- Architecture reviews: find assumptions → verify against requirements
- Security scans: locate auth patterns → validate token flow
- Documentation gaps: list undocumented functions → check if docs exist elsewhere

**Key rule:** If the model tier is below Codex/Opus, require two-phase prompting. Strong models handle naive prompts; weak models need the verification scaffold.

## Operational Notes

- **Delete existing REVIEW files before re-running.** OpenCode's run didn't overwrite the previous `REVIEW-opencode.md`. Use unique names or `rm` first.
- **Gemini CLI capacity is unpredictable.** `gemini-3-flash-preview` hit `MODEL_CAPACITY_EXHAUSTED` repeatedly. Budget extra time or force a specific model with `-m gemini-3-pro` (but that uses more quota).
- **Cost:** ~$0.50 (Codex) + $0 (OpenCode) + $0 (Gemini) = $0.50 for 3 actionable bugs. Reasonable ROI but a focused single-tool review (Codex alone) would have caught 2 of the 3.
- **Parallel launch works well.** All three tools ran simultaneously via `run_in_background: true`. Triage while waiting for stragglers.
