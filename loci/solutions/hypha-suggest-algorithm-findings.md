# hypha --suggest: Algorithm Findings

Empirical notes from running `--suggest` across Capco/HSBC and research article clusters in the vault (~1000 notes).

## Algorithm evolution

### v0.1.1 — Common Neighbors (raw count)
Ranked by number of shared neighbors. Problem: daily/weekly notes (YYYY-MM-DD, YYYY-WXX) dominated because they're linked from every note written on the same day — pure temporal hubs with no semantic signal.

**Fix:** `is_calendrical()` filter strips these from the neighbor set entirely.

### v0.1.2 — Adamic-Adar IDF weighting
Each shared neighbor k contributes `1/(1 + ln(1 + degree(k)))`. Demotes hub notes (Capco Transition, LinkedIn Content Ideas) as co-citation signal. Score threshold 0.5.

Showed shared neighbor names in output — made evaluation instant (previously had to read candidate notes to judge signal vs noise).

### v0.1.3 — Resource Allocation (RA)
Each shared neighbor k contributes `1/degree(k)`. No log — harder hub penalty.

**Why RA over AA:** Papers (Liben-Nowell, bipartite network studies) consistently show RA outperforms AA on sparse graphs. For a personal vault, the intuition is sharper: a degree-50 hub like "Capco Transition" contributes 0.02 (vs 0.08 under AA); a degree-2 specific note contributes 0.5 (vs 0.33 under AA). Specific co-citations get amplified, generic ones get crushed.

Score threshold lowered 0.5 → 0.1 because RA absolute scores are smaller.

**Observed improvement:**
- `LLM Council - Human Cost Framework Red Team` surfaced for Cognitive Debt via a single very specific shared neighbor (Research - Human Cost of AI Adoption). Under AA this would have scored too low.
- `Conformal Prediction for LLM Summarisation` surfaced for Cognitive Debt via Agentic Engineering — genuine cross-topic link.
- `Hong Kong FSI Landscape` surfaced via `AI Agent Sandbox Landscape - Feb 2026` — specific, wouldn't have ranked before.
- Hub notes (Capco Transition, LinkedIn Content Ideas) still appear but further down, not leading.

### v0.1.4 — Utility note suppression
`TODO`, `README`, `MOC`, `index` excluded from candidate list and neighbor set via `is_utility_note()`. These are vault meta-files, not knowledge content.

Combined with `is_calendrical()` into `suppress_from_suggest()`.

## Noise that remains (as of v0.1.4)

- **Hub notes (Capco Transition, LinkedIn Content Ideas)** still surface for almost every Capco note via high shared-neighbor count, even with RA downweighting. This is partly correct (they ARE connected) and partly noise. Could be addressed with a max-candidates-per-note cap or explicit `--exclude-note` flag.
- **Single-neighbor entries via medium-degree notes** are borderline — depends on note specificity. Generally RA handles this correctly (low-degree → high weight = surfaced; medium-degree → lower weight = may not pass threshold).

## Remaining improvements to consider

1. **`--exclude-note` flag** — explicit suppression of named hub notes from neighbor set (for cases like "Capco Transition" which is structurally central but semantically too broad).
2. **Jaccard normalization** — normalize RA score by `|N(seed) ∪ N(candidate)|` to avoid favoring large-neighbor candidates over focused ones.
3. **Bidirectional degree** — current in-degree only. Could use in+out degree for a more complete hub measure.

## Source
- pplx search result: RA consistently outperforms AA on sparse graphs, penalising high-degree intermediaries harder. Bipartite network studies confirm RA's superior precision in sparse domains.
- Reference: Liben-Nowell & Kleinberg link prediction paper (Cornell).
