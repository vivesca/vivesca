---
name: morphogenesis
description: Mine design insights from biological names — rename a concept with a bio name, study what the biology actually does, compare to current implementation, implement the gap. Use when renaming to bio convention, or when a bio name already exists but hasn't been mined. "morphogenesis", "annotate", "what does the name tell us", "mine the name", "rename and inspire".
user_invocable: true
model: sonnet
context: fork
---

# Annotation — Mining Design from Names

Gene annotation attaches functional meaning to a genetic sequence. This skill attaches design meaning to a biological name: name → study → compare → build.

## The Cycle

```
1. NAME    → Pick the honest biological mapping (process noun, cell layer)
2. STUDY   → What does this process actually do in biology? (3-5 key properties)
3. COMPARE → Which properties does our implementation have? Which are missing?
4. DESIGN  → Each missing property is a design gap. Rank by value.
5. BUILD   → Implement the highest-value gap. Now, not next time.
```

## Validated Examples

| Name | Biology says | We had | Gap found | Built |
|------|-------------|--------|-----------|-------|
| respirometry | Measures efficiency (RQ), not just fuel level | Raw % gauge | Yield-per-token, sprint detection | Noted for future |
| consolidation | Happens during sleep, not on calendar | Weekly schedule only | Post-session trigger | Stop hook (6h debounce) |
| anamnesis | Selective — experienced doctor adjusts questions | Uniform loading | Keyword-relevance reordering | Primacy-based loading |
| histone_mark | Combinatorial — multiple marks interact | Single status dimension | Multi-dimensional marking | Noted for future |
| anabolism | Convergent — many inputs → few outputs | Scatter of artifacts | Convergence test | Noted for future |
| ecphory | Cue-trace interaction; memory-type routing; reconstructive | Uniform sweep, MEMORY.md hint only | Route by episodic/semantic + age; synthesise partial hits | Built: /ecphory skill |
| cytometry | Time-resolved kinetics — population drift not just snapshot; autonomous monitoring | Point-in-time audit, no delta | Drift delta vs prior audit; autonomous heartbeat for stale subsystems | Noted for future |
| nucleation | Heterogeneous seeding lowers activation barrier; seed hit should collapse pipeline | cerno runs but output doesn't gate pipeline depth | Seed hit → skip planning; pre-flight gates enforced not advisory | Noted for future |
| sporulation | Environmentally triggered (stress-sensing), not user-initiated; mother cell flushes before lysing | User-initiated only; no pre-sporulation flush | Auto-suggest /sporulation at budget=red; flush before checkpoint | Built: allostasis red-tier now suggests /sporulation |
| autophagy | Selective cargo-receptor degradation of damaged/excess components — quality control | Training mode (askesis) — wrong biological mapping | Rename to /askesis; build real /autophagy for cargo-receptor pruning of stale memory/skills | Noted for future (rename + new skill) |
| endocytosis (web routing) | Pathway selection is cargo-dependent; pre-flight receptor clustering before committing; endosome sorts after intake; session cleanup (receptor recycling) | Each consuming skill reimplemented fetch ad hoc; no auth pre-flight; intake/processing fused; no session close rule | Canonical routing table; auth check before attempt; gap between intake and processing stages; close rule for agent-browser | Built: [[fetch-routing]] reference doc; cross-referenced from /phagocytosis + core-commands |
| downregulation (memory pruning) | Signal-triggered not scheduled; graduated depth (surface→internalization→degradation); reversible at each stage; item still exists; homeostatic feedback | Line-count trigger (pressure not disuse); single-depth operation; no defined destination; no re-promotion path; no feedback loop | Trigger on recurrence signal not volume; name destination explicitly; define re-promotion rule | Built: destination named in SKILL.md + MEMORY.md header; re-promotion note added |

## How to Use

### When renaming
1. Don't pick the first biology word that sounds cool
2. Ask: "What is the honest verb?" (what does this thing actually DO?)
3. Find the biological process that does that verb
4. Run the cycle above before committing the name

### When a name already exists
1. Read the biology (Wikipedia is fine for the 3-5 key properties)
2. Ask: "Which of these properties does our implementation lack?"
3. The missing property IS the design insight

## Anti-patterns

- **Decorative naming:** picking a bio name because it sounds good, not because it maps honestly. Test: can you explain the mapping in one sentence?
- **Stopping at step 1:** renaming without mining. The rename is 10% of the value.
- **Forced mapping:** if no biological process honestly maps, don't force it. The naming test IS the design test.

## The Meta-Insight

The organism's naming convention isn't decoration — it's a design review tool. Every bio name is a hypothesis: "this component behaves like [biological process]." The hypothesis is testable: study the biology, check whether the implementation matches. Mismatches are design gaps. The names-carry-theory finding (2026-03-23) proved this: bio-naming hooks surfaced 5 design gaps from theory encoded in names.
