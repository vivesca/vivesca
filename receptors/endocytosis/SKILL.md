---
name: endocytosis
description: LLM knowledge mining — extract implicit model knowledge into permanent reference skills as actionable heuristics. Three tiers: single-model interview (quick), quorum adversarial refinement (deep), field validation. Specimen-based mining uses people (Einstein, Munger), traditions (Stoicism, kaizen), and failures (LTCM, Challenger) as concrete entry points — heuristics sort into existing skills, not new containers. Post-mining skill-map review reveals architectural gaps. Use when a topic would benefit from stable, always-loaded heuristics that the model knows but surfaces inconsistently.
user_invocable: true
tags: [meta, knowledge, skills]
context: fork
---

# /endocytosis — LLM Knowledge Mining

> *Fodina: Latin "mine" — the place you extract ore.*

Extract implicit knowledge from LLM weights into permanent, version-controlled reference skills. The model knows things it won't reliably surface — mining makes that knowledge explicit and deterministic.

**What we extract are moves, not rules.** Moves are dynamic, contextual, impermanent — they resist static filing. Skills are containers for moves, which is itself a useful fiction (see `sunyata`). This is why the best heuristics end up "homeless" between categories — they're too kinetic for any single container.

**Output format: heuristics, not theory.** Every mined skill should be actionable — failure modes to watch for, distinctions that change approach, decision points where the wrong default hurts. Minimal framing to make the heuristics cohere, but the test is: "does reading this change what I do?" If it's only interesting but not behaviour-changing, it's too theoretical.

## What to Mine (The Meta-Skill)

The ability to spot minable knowledge is itself a judgment call. Look for:

**Signals that a topic is worth mining:**
- **Inconsistent depth** — the model gives brilliant insight sometimes, shallow output other times. The inconsistency IS the signal that extractable structure exists in the weights.
- **Stable cognitive operations** — things that don't change with tooling. Planning, debugging, evaluating, simplifying — these are the *verbs* of knowledge work. They underlie domain-specific skills and transfer everywhere.
- **Cross-skill leverage** — a reference skill would make multiple other skills better (like bouleusis improves rector, [[premise-audit]], [[mental-models]]). The more skills it wires into, the higher the mining ROI.
- **Repeated re-explanation** — you keep articulating the same concept across sessions without it sticking.

**What to extract — not "how X works" but "what to consider when doing X".** Ten types of actionable knowledge to look for during extraction:

| Type | Example | When it helps |
|------|---------|---------------|
| **Rules** | "Don't park deliverables" | You know what to do but might not do it |
| **Checklists** | "5 quality axes for wrap-ups" | You don't know what to consider |
| **If-then triggers** | "If 'TODO: consider...' in wrap → decide now or delete" | Conditional — fires on recognition |
| **Distinctions** | "Log vs. insight — different audiences, different destinations" | Prevents conflating things that look similar |
| **Anti-patterns / smells** | "Deferred action disguised as capture" | Recognising what's going wrong |
| **Spectrums** | "Scale wrap depth with session complexity" | Prevents binary thinking — there's a dial |
| **Ordering / priority** | "Route: skill > memory > daily note" | Sequence matters |
| **Signals** | "Inconsistent model depth = extractable structure exists" | What to notice before deciding what to do |
| **Defaults with override** | "Always checkpoint at gear shifts — unless session <10 min" | Rule + explicit escape clause |
| **Reframes** | "Wrap-up is state transfer, not documentation" | Changes how you see the task, makes other heuristics cohere |

Most mines naturally contain several types. During extraction, **name the type** — it sharpens what you're pulling out and prevents drift into explanation.

**Don't mine:**
- Volatile knowledge (API versions, tool flags) — that's docs, not heuristics
- Procedural knowledge (how to run X) — that's a regular skill
- Knowledge the model doesn't actually have depth on — test with one probing question first
- Topics where the existing pieces already cover it well enough — diminishing returns
- Abstract words (adjectives, verbs) — too compressed, one insight per word. Specimens need enough internal structure to probe deeply
- Unnamed phenomena — resist extraction because they haven't been crystallized into transmissible form. Some knowledge needs to be lived, not described
- Abstract words (adjectives, verbs) — too compressed, one insight per word
- Low choice-density media (phone books, logs, raw data) — information without choices = nothing to mine

**Stories hold what skills can't.** Writing a story then mining it produces heuristics that all map to existing skills — no new gaps. But the story captures the felt quality of multiple moves operating together, which the skill format can't decompose. Skills are for retrieval; stories are for transmission of what resists decomposition. Complementary formats.

## Specimen-Based Mining

Mining abstract topics ("what is judgment?") works but plateaus. **Specimens** are concrete things you examine to reveal general structure — a thinker, a tradition, a failure. The specimen is drilled into, not preserved. Language matters: "anchor" implies fixity and invites anchoring bias; "specimen" keeps the relationship honest — you're studying it to learn about the class, then discarding the container.

**A specimen is anything with embedded choices.** Mining yield can't be predicted — the only way to know is to mine and see. Two heuristics for picking specimens:

1. **Maximize distance** from what you've already mined. Distance between cultural clusters is the best predictor of new gaps. Each culture is a different aggregation of human experience — different constraints produced different observations.
2. **Prefer integrated specimens.** Person (decades of choices) → tradition (centuries) → culture (millennia). Each level aggregates more choices under more constraints. A thinker's life mines richer than a code snippet because the choices constrain each other across a lifetime, revealing deeper structure. People, traditions, failures, fiction, disciplines, games, natural phenomena — the type doesn't matter. The process is always: probe → extract moves → sort → check gaps. Below are specimen types we've validated, but this list is itself provisional (see `sunyata`):

| Specimen | Example | Typical output |
|----------|---------|----------------|
| **People** | Einstein, Feynman, Munger | Positive heuristics, architectural gaps |
| **Traditions** | Stoicism, Talmud, Daoism, Buddhism | Same — deep, refined |
| **Failures** | LTCM | Anti-patterns ("don't" entries), enrichment |
| **Fiction** | 火鳳燎原, Harry Potter | Enrichment + sharp distinctions |
| **Disciplines** | Physics, chemistry | Unconscious practitioner moves |

**Specimen types produce different heuristic shapes.** People and traditions yield positive heuristics ("do this") and reveal architectural gaps (homeless heuristics). Failures yield anti-patterns ("don't do this") and reinforce existing skills without revealing new gaps — because failures show where known principles were violated, not where new principles are needed. Mix both types for a complete picture.

**Not good specimens:** Domains (too broad, already `[[analogical-transfer]]`), countries (too vague — unless scoped to a tradition), eras (conditions more than moves).

**Process:** Mine the specimen → extract heuristics → sort each heuristic into its natural home skill. The specimen is the drill bit, not the container. **No new skill per specimen.**

**Post-mining: revisit the skill map.** After each specimen, review the heuristic-to-skill mapping. When a heuristic maps to TWO existing skills equally, that's a signal — a concept lives in the cracks between skills. Log these "homeless" heuristics. After 3-4 specimens, review the collection: do they cluster into a concept that deserves its own skill? If yes, the mining has diagnosed a gap in the skill architecture. This is the real payoff — specimens stress-test the skill network, not just enrich it.

**Queue:**
- [x] Einstein → thought experiments, aesthetic selection, productive stubbornness, productive confusion
- [x] Feynman → explanation as understanding, playful formalism, anti-authority heuristics
- [x] Munger → inversion, latticework, circle of competence, avoiding stupidity > seeking brilliance
- [x] Stoicism → premeditatio malorum, dichotomy of control, negative visualisation
- [x] Darwin → disconfirming evidence, exhaustive enumeration, analogy as scaffolding, institutional humility
- [x] Talmudic tradition → structured disagreement, extreme cases, chain of transmission, question > answer, chavruta
- [x] LTCM → model risk blindness, leverage as fragility, genius as risk factor, correlation breakdown, illiquidity, systemic coupling (all anti-patterns → existing skills)
- [x] Laozi/Daoism → wu wei, usefulness of emptiness, yielding as strength, uncarved block, reversal at extremes, leading by not leading
- [x] Musashi → the gaze (kan-ken), no preferred weapon, rhythm/timing, crossing at a ford, becoming the opponent, the void
- [x] Sun Tzu → shì (momentum), empty/full, know them/know yourself, orthodox/unorthodox, winning without fighting, terrain
- [x] 火鳳燎原 (fiction) → appearing weak/strong, weakness as asset, information asymmetry, long game > brilliant move, unreliable narration, principles have costs
- [x] Bhagavad Gita → nishkama karma, inaction is action, situational duty, quality of action (gunas)
- [x] Chanakya/Arthashastra → four upayas (escalation), matsya nyaya (entropy), intelligence as foundation, pragmatic morality
- [x] Buddhist epistemology → dependent origination, śūnyatā, two truths, meditation as empirical investigation
- [x] Physics → symmetry, dimensional analysis, perturbation theory, conservation laws, renormalisation, phase transitions
- [x] Chemistry → catalysis, dynamic equilibrium, rate-limiting step, Le Chatelier, emergent properties
- [x] Harry Potter (fiction) → Mirror of Erised, Horcruxes, Patronus, Deathly Hallows, choices > abilities
- [x] Ubuntu/African oral tradition → ubuntu (relational cognition), griot (knowledge as performance), proverbs, circular time, indaba
- [x] Mathematics as practice → abstraction, proof by contradiction, definitions, existence vs construction, isomorphism
- [x] Alien fiction (Arrival, Three-Body, Ender's Game, Solaris, Blindsight) → sharpened existing skills, no new gaps. Unclear if ceiling, thin weights, or ordering bias
- [x] Dune → prescience trap (excessive analysis pathology), Litany Against Fear, Mentat thinking, Bene Gesserit observation, plans within plans, desert wisdom, Gom Jabbar
- [x] Management theory (Grove, Drucker, Deming, Weinberg) → TRM, orchestrator leverage, 94% system rule, management by exception, PDCA, fear-free prompting, cross-verification, contribution framing. All sorted into cohors + delegation-theory (enrichment, no new skill)
- [ ] Kaizen → (tradition specimen — queued)

## Cross-Model Mining

Run the same probe prompt on multiple models (Gemini CLI, Codex, OpenCode). Compare extractions. Each model's weights are a different lossy compression of human knowledge — the delta between extractions reveals what each model noticed that the others didn't.

**Validated:** Einstein — Gemini found 3 moves Claude missed, Claude found 2 Gemini missed. Musashi — Gemini found 3 additional moves (Mountain-Sea Pivot, Holding the Pillow, Rat's Head/Ox's Neck).

**Prompt:** `~/notes/Fodina Mining Prompt.md` (vault, versioned). CLI tool queued.

## Tier 1: Single-Model Interview

Fast, good for well-understood domains where the model has clear depth.

**Process:**
1. **Probe** — ask the model an open question about the domain ("what is planning?")
2. **Push past first answer** — the second and third layers are where structure lives. Ask "what distinguishes this from X?" or "where does this break down?"
3. **Find the bones** — look for: taxonomy (types/categories), failure modes, axes of improvement, key distinctions
4. **Distill** — capture as a reference skill with `disable-model-invocation: true`
5. **Wire** — add cross-references to skills that would benefit (this is not optional — unwired skills get forgotten)
6. **Publish** — if the insight is non-obvious, `sarcio new` for a garden post

**Step 4.5: Quality gate** — after distilling, ask: "which of these heuristics would actually change behavior?" Most mines produce 80% theory, 20% behavior-changing insight. Flag the 20%. The skill keeps everything (reference is cheap); the garden post carries only the sharp part.

**Step 6 detail: Mine → garden conversion.** Never publish the framework. Publish one distinction, grounded in a specific moment. The skill is the map; the post is the story of discovering one landmark.

**Output:** One reference skill file. ~50-100 lines. Stable knowledge, not procedures.

## Tier 2: Consilium Adversarial Refinement

Deeper. Multiple models debate the extracted knowledge, find gaps, challenge assumptions. Use for high-stakes theory or when Tier 1 output feels thin.

**Process:**
1. **Run Tier 1 first** — you need a draft to refine
2. **Feed draft to quorum** — `quorum "Review this theory of <X>. What's missing? What's wrong? What failure modes aren't listed? What distinctions are false?" --vault`
3. **Synthesise** — the council will surface blind spots, edge cases, and counterarguments. Merge into the skill.
4. **Adversarial pass** — ask specifically: "What would someone who disagrees with this framework say? What domains does it fail in?"
5. **Update skill + re-wire** if the structure changed significantly

**Output:** A battle-tested reference skill. The council catches things a single model misses: blind spots, false distinctions, missing failure modes.

## Tier 3: Field Validation

The only tier that touches reality. Tiers 1-2 are still theory — extracted and stress-tested, but untested in practice.

**Process:**
1. **Use the skill in real work** — let it load into sessions, observe when it fires
2. **Track hits and misses** — when the skill helps, note it. When it's wrong or missing something, note that too. Log in the skill's own file or `decay-tracker.md`.
3. **Revise from evidence** — after 2-4 weeks of use, update the skill based on what actually happened, not what the models thought would happen
4. **Prune false distinctions** — theory that sounded right but never proved useful in practice gets cut

**Output:** A field-tested skill. The difference between Tier 2 and Tier 3 is the difference between a peer-reviewed paper and a practitioner's handbook.

**Cadence:** Passive — runs in the background as you work. Review each mined skill in `/ecdysis` or `/mitosis`.

## Mining Queue

Topics identified as worth mining (stable theory, currently in weights only):

1. ~~Theory of debugging~~ → `[[debugging-theory]]` (done)
2. ~~Theory of simplification~~ → `[[simplification]]` (done)
3. ~~Theory of delegation~~ → `[[delegation-theory]]` (done)
4. ~~Theory of evaluation~~ → `[[evaluation-theory]]` (done)

**Cadence:** One per session. Don't batch — extraction quality degrades within a conversation (fresh context = fresh extraction). Validated: 7 specimens in one session, first 6 strong, 7th felt mechanical.

**Ordering bias.** Early specimens mine into a sparse skill map — more heuristics look homeless, more new skills get created. Later specimens mine into a dense map — most heuristics find homes, yield looks low. This is an artifact of the map's density, not the specimen's richness. The same specimen mined first vs. twentieth would produce different apparent yield. Implication: "diminishing returns" within a session is partly real (cluster saturation) and partly artifact (fuller map). To test a specimen fairly, imagine mining it into an empty map.

**Saturation is per-cluster, not per-process.** 7 Western specimens saturated after 6 — specimen 7 (LTCM) produced only enrichment. But 3 Eastern specimens (Laozi, Musashi, Sun Tzu) immediately found 3 new gaps the Western cluster never touched. The signal "more of the same" means "switch clusters," not "stop mining." Vary specimen culture/domain/era to avoid premature saturation.

## Wiring Checklist

After creating any mined skill:
- [ ] Add cross-references to all skills that would benefit (grep for related triggers)
- [ ] Update this file's Mining Queue with the new skill name
- [ ] Consider a garden post if the insight is non-obvious
- [ ] Commit skill + wiring changes in same session

## Tracking Usage

Mined skills are only valuable if they get consulted. Track in `memory/decay-tracker.md` (same as MEMORY.md entries):
- When a mined skill is consulted in a session, log it
- If a skill hasn't fired after 4 weeks → either wiring is wrong (fix cross-references) or the skill isn't useful (demote or delete)
- Tier column in Completed Mines tracks provenance strength — Tier 1 (hold lightly), Tier 2 (quorum-tested), Tier 3 (field-validated)
- The specific source (which model, which council) doesn't matter — content either proves useful or it doesn't. Track the tier, not the genealogy.

## Completed Mines

| Topic | Skill | Tier | Wired to | Garden post |
|-------|-------|------|----------|-------------|
| Planning | `[[planning-theory]]` | 1 | rector, [[premise-audit]], [[mental-models]] | [Mining Your LLM](https://terryli.hm/posts/mining-your-llm) |
| Debugging | `[[debugging-theory]]` | 1 | rector | — |
| Experimentation | [[experimentation-theory]] | 1 | peira, judex, [[premise-audit]], [[mental-models]] | [[The Persona Paradox in AI Agent Teams]] |
| Simplification | `[[simplification]]` | 1 | rector | — |
| Delegation | `[[delegation-theory]]` | 1 | rector | — |
| Evaluation | `[[evaluation-theory]]` | 1 | judex, peira | — |
| Heuristics | `[[heuristics-decision]]` | 1 | [[mental-models]], transcription-factor, mandatum, quorum | "Delegation Is Delegation", "The Heuristic Library" |
| Wrap-ups | conclusio (inlined into cytokinesis) | 1 | cytokinesis (inlined), eow, daily | — |
| Toddler school refusal | `[[parens]] (Reference)` | 1 | — (vault: Theo - Development & Parenting Notes) | — |
| Truth-seeking | `[[truth-seeking-method]]` | 1 | endocytosis, elencho, quorum, peira, rector | — |
| Judgment | `[[practical-judgment]]` | 1 | quorum, transcription-factor, [[premise-audit]], [[truth-seeking-method]], rector, praecepta | — |
| Creativity | `[[creativity]]` | 1 | brainstorming (CE skill), rector, quorum, diagnosis | — |
| Systems thinking | `[[systems-thinking]]` | 1 | rector, diagnosis, phronesis, [[creativity]], [[truth-seeking-method]] | — |
| Communication | `[[communication-cognition]]` | 1 | [[career-communication]], storyteller (deleted), agoras CLI, quorum, mandatum, opsonization | — |
| Learning | `[[learning-theory]]` | 1 | dokime, rector, endocytosis, [[parens]] (Reference), eow, daily, phronesis | — |
| Self-awareness | `[[self-awareness]]` | 1 | phronesis, enkrateia, praecepta, all operations | — |
| Self-regulation | `[[self-regulation]]` | 1 | [[self-awareness]], phronesis, sopor, ultradian, mora (deleted), [[parens]] (Reference) | — |
| Empathy | `[[empathy]]` | 1 | [[communication-cognition]], mandatum, opsonization, [[career-communication]], phronesis, [[parens]] (Reference) | — |
| Task management | negotium (unbuilt) | 1 | sched, ultradian, cytokinesis, todo | — |
| AI governance consulting | `[[gubernatio]] (Reference)` | 1 | rector, opsonization, capco-prep, quorum | "Governance Is a Tax" |
| Regulatory comparison | `[[regulatio]]` | 1 | opsonization, capco-prep, [[gubernatio]] (Reference) | — |
| Technical credibility | [[auctoritas]] (Reference) | 1 | opsonization, capco-prep, [[career-communication]], [[gubernatio]] (Reference) | — |
| Agent team orchestration | archived (skill deleted) | 1 | polarization, rector, mandatum, heuretes, opifex | — |
| Deployed system verification | `[[deployed-system-verification]]` | 1 | verify (rules), peira, [[mental-models]] | "The Pipeline Paradox" |
| Consulting communication | `[[relatio]]` | 1 | [[communication-cognition]], opsonization, capco-prep, [[gubernatio]] (Reference), [[career-communication]], auctoritas, stilus | — |
| Representation shifting | `[[representation-shifting]]` | 1 (specimen) | diagnosis, [[creativity]], [[communication-cognition]], [[mental-models]], [[analogical-transfer]] | — |
| Productive not-knowing | `[[productive-not-knowing]]` | 1 (specimen) | [[self-awareness]], [[truth-seeking-method]], [[premise-audit]], phronesis, quorum, kritike | — |
| Extreme-case testing | `[[extreme-case-testing]]` | 1 (specimen) | [[truth-seeking-method]], peira, [[premise-audit]], aporia, [[mental-models]] | — |
| Cognition is relational | `ubuntu` | 1 (specimen) | quorum, sympatheia, adversaria, kenosis | — |
| Existence before construction | `existence` | 1 (specimen) | aporia, diagnosis, metanoia, nishkama, invariance | — |
| Working with momentum | `wuwei` | 1 (specimen) | enkrateia, metanoia, parsimonia, phronesis, reductio | — |
| Mastery as disappearance | `kenosis` | 1 (specimen) | parsimonia, aporia, mandatum, mathesis | — |
| Adversarial perspective | `[[adversarial-perspective]]` | 1 (specimen) | sympatheia, reductio, quorum, metanoia, aporia | — |
| Action without attachment | `nishkama` | 1 (specimen) | enkrateia, wuwei, kenosis, phronesis, aporia | — |
| Categories are provisional | `sunyata` | 1 (specimen) | aporia, metanoia, [[mental-models]], systema, parsimonia | — |
| Find what doesn't change | `invariance` | 1 (specimen) | metanoia, reductio, sunyata, systema | — |
| Excessive analysis pathology | `prescience` | 1 (specimen) | reductio, aporia, adversaria, nishkama, wuwei | — |
| Management for agent teams | archived (skill deleted) + delegation-theory (enrichment) | 1 (4 specimens: Grove, Drucker, Deming, Weinberg) | mandatum, rector, opifex, heuretes | — |
| Cadence design | `[[cadence-design]]` | 1 (Newport + practice) | commute, weekly, monthly, quarterly, planning-theory, self-regulation | — |

## Relationship to Other Skills

- **[[knowledge-structure]]** — designs skills (structure, naming). endocytosis is specifically about *extracting knowledge from model weights* into skills.
- **quorum** — the engine for Tier 2 refinement. endocytosis tells you *when and how* to use it for knowledge extraction.
- **[[knowledge-routing]]** — routes knowledge to the right layer. endocytosis always produces reference skills, not MEMORY.md or docs.
- **[[mental-models]]** — mental models catalog. Mined skills often feed new entries into [[mental-models]].
