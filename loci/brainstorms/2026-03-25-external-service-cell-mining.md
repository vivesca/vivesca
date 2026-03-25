# External Service Cell-Level Mining

Six design improvements from forcing cell-level names onto external services (25 Mar 2026).
Rule: mine the name, skip the rename. The constraint generates the insight.

## 1. sopor → chemoreceptor: receptor specificity

**Biology:** Chemoreceptors detect SPECIFIC molecules at SPECIFIC concentrations. Tuned to particular signals (O2, CO2, glucose). Don't dump all chemicals.

**Current:** Pulls full Oura data — sleep, readiness, HRV, everything.

**Gap:** Receptor specificity. Each query should ask for ONE signal with a threshold.

**Build:** Add threshold-based queries to sopor.
- `sopor readiness --threshold 70` → fires only if below
- `sopor hrv --delta` → returns change from baseline, not absolute
- Default: return the specific signal asked for, not the full dump

**Size:** ~20 lines wrapper. Sopor CLI may already support filtering — check first.

## 2. fasti → circadian oscillator: rhythm phases

**Biology:** Circadian oscillators are SELF-SUSTAINING — tick without external input. ENTRAIN to cues but don't depend on them. Produce RHYTHMIC output — phases, not events.

**Current:** Reads Google Calendar events. Event list.

**Gap:** Time sense should be rhythmic. "Deep work phase" vs "meeting at 3pm." Events entrain the rhythm; they aren't the rhythm.

**Build:** Phase overlay on fasti output.
- Define phases: photoreception (morning), deep-work, transition, wind-down, dormancy
- Map events INTO phases, not the other way around
- Surface: "You're in deep-work phase. Next transition: 2pm (meeting)"
- Phase boundaries shift based on calendar density

**Size:** ~40 lines. Phase definitions + event-to-phase mapper.

## 3. keryx → gap junction: contact-type distinction

**Biology:** Gap junctions are DIRECT channels between ADJACENT cells. Small molecules pass freely. Bidirectional. Always open. Only between physically touching cells (close relationships).

**Current:** Reads WhatsApp, drafts replies (never sends).

**Gap:** No distinction between contact types. Messages from Tara (gap junction — always open, bidirectional, low-friction) treated same as professional contacts (receptor-mediated — formal, packaged, selective).

**Build:** Contact classification in keryx.
- Gap junction contacts: family, close friends → surface immediately, low-friction draft style
- Receptor contacts: professional, acquaintances → batch, formal draft style
- Classification: simple list in config, not LLM-mediated

**Size:** ~15 lines. Contact list + routing logic.

## 4. oghma → chromatin: accessibility states

**Biology:** Chromatin controls gene ACCESSIBILITY without changing the DNA. Open chromatin (euchromatin) = actively expressed. Closed chromatin (heterochromatin) = silenced but preserved. Epigenetic marks control which regions are open.

**Current:** Memory database with histone_mark for tagging. Memories are either found or not.

**Gap:** No accessibility states. Memories don't have open/closed distinction. Old memories clutter active searches. Archival memories should be preserved but not surfaced unless specifically requested.

**Build:** Accessibility states in oghma.
- Open (euchromatin): actively surfaced in searches (default for recent)
- Closed (heterochromatin): preserved, only surfaced with explicit `--archived` flag
- Marks control transitions: `histone_mark --close` silences a memory, `--open` reactivates
- Auto-close: memories not accessed in N days → heterochromatin
- Search default: euchromatin only. `--all` includes heterochromatin.

**Size:** ~30 lines. State field + query filter + auto-close cron.

## 5. deltos → secretory vesicle: packaging

**Biology:** Secretory vesicles PACKAGE content before export. Wrapped in membrane, labeled for destination, fuse with target membrane. Content is formatted for the recipient.

**Current:** Sends raw text/images to Telegram. Chaperone checks quality but no packaging step.

**Gap:** No destination-aware formatting. Same content sent to Telegram, WhatsApp, garden looks identical. Each destination has different conventions (Telegram: concise. Garden: structured. LinkedIn: professional framing).

**Build:** Packaging layer in deltos/secretory.
- Before send: detect destination → apply destination-specific formatting
- Telegram: strip markdown, add emoji context, keep short
- Garden: add frontmatter, structure as post
- LinkedIn: professional framing (already in secretion tool)
- Packaging is deterministic (template-based), not LLM-mediated

**Size:** ~25 lines per destination. Template functions.

## 6. noesis → chemotaxis: gradient-following search

**Biology:** Chemotaxis follows GRADIENTS. Cell senses which direction has more of the target molecule, moves toward it. If gradient reverses, it reverses. Not random search — directed navigation.

**Current:** Three tiers (ask/search/research). Each tier is independent. No gradient-following between results.

**Gap:** No iterative refinement guided by result quality. First search returns weak results → user manually reformulates. Chemotaxis says: sense the gradient and auto-adjust.

**Build:** Gradient-following in noesis.
- After first search: score result quality (deterministic: result count, source authority, keyword density)
- If below threshold: auto-reformulate query toward stronger signal
- Direction hints: extract entities/terms from best results, inject into next query
- Max 3 iterations, then surface best + "gradient direction" for human refinement
- This is deterministic reformulation, not LLM-mediated

**Size:** ~50 lines. Quality scorer + query reformulator + iteration loop.

---

**Priority by value:**

1. **oghma/chromatin** — accessibility states transform memory from flat to layered. High daily impact.
2. **noesis/chemotaxis** — gradient search reduces manual reformulation. Medium daily impact.
3. **fasti/circadian** — rhythm phases change how time is sensed. Medium daily impact.
4. **sopor/chemoreceptor** — threshold queries reduce noise. Small daily impact.
5. **keryx/gap junction** — contact classification. Small daily impact.
6. **deltos/secretory vesicle** — destination packaging. Small daily impact.
