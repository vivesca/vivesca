# Style Discipline — Sentence-Level, Satellite Notes, House Style, Architectural Patterns

Loaded on demand by `induction` SKILL.md when polishing or restructuring a paper.

---

## Sentence-Level Discipline — Shorter, Simpler, Punchier

Paragraph density and sentence brevity are independent. A dense paragraph (lots of information per word) can be composed of short sentences. Aim for both.

The principle: **each sentence punches once.** Compound sentences with three nested qualifiers dilute the punch. Cut to two sentences when a thought has two beats. Cut to one when you can.

**DO:**
- Lead with the subject + active verb. "Group AI extends MRM's artefacts." Not "An extension of MRM's artefacts is what Group AI provides."
- Split when conjunctions stack. "X, and Y, with Z" → "X. Y, with Z."
- Use plain words. "The capability concentrates at Group level..." beats "The capability instantiates a Group-level concentration of..."
- Bare assertions in Recommendation and Ask. "The Board is invited to endorse." Not "The Board may wish to consider whether endorsement..."
- Parallel grammar in lists. Three-item lists must share a single grammatical form — all noun phrases ("instruction-following across long autonomous runs, adherence to authorised tool boundaries, autonomous task-completion horizons") or all verb phrases. Mixing forms ("following instructions...", "staying within...", "task-completion horizons") creates micro-friction the reader can't articulate but registers as sloppy. Surfaced 28 Apr 2026 v0.20 diction-polish pass.

**DO NOT:**
- Stack three clauses joined by "—" or "with" or "and" in a single sentence. Split.
- Use compound modifiers when one will do. "build-once-govern-once-reuse-many" earns its hyphen-string by being institutional vocabulary; "comprehensive-yet-flexible-and-scalable" doesn't.
- Mistake long-sentence sophistication for senior register. Senior register prefers short and load-bearing.
- Write what you'd say in a meeting. Spoken hedges ("I think", "perhaps") become weakness markers in writing.

**Test:** read each sentence aloud. If you run out of breath before the period, split. If you can't say what the sentence claims in 10 words or less, the sentence is doing too much.

**The asymmetry:** punchy sentences cost the writer (more thinking, more revision); long sentences cost the reader (slower comprehension, weaker punch). Pay the writer's cost.

Related marks: `feedback_executive_paper_style`, `feedback_partner_message_density`, `feedback_assert_dont_ask_in_senior_comms`.

---

## Technical-Backing Satellite Notes — Body Layman, Defense Hidden

Board papers should read accessibly for the audience that will endorse them. Most board readers are not domain specialists — they will not parse field jargon, internal acronyms, or unexplained technical terms. The body must use plain English, named institutions, and concrete examples that any senior reader can follow without a glossary.

But the paper still needs to survive technical challenge from cross-functional readers (MRM, Cyber, Legal, regulators). Bury the technical depth in **satellite notes** linked from the paper's `related:` frontmatter, not in the body.

**Pattern:**

| Layer | Audience | Content |
|---|---|---|
| Body | Board / endorsement audience | Plain English, named institutions, concrete examples |
| Defense satellite | Cross-functional reviewers (MRM, Cyber, Legal, PRA) | Technical claims, methodology, anticipated challenges with responses, source lineage |
| Reference satellite | Anyone challenging a specific external claim | Verbatim source captures, primary URLs, secondary coverage |
| Long-form parent | Regulators, follow-on paper authors | Full architectural depth, all framings, all caveats |

**When a body claim could be challenged technically, write the defense in a satellite note before the challenge arrives.** The paper links to the satellite via `related:`. The body stays clean. If the challenge arrives, the defender pulls the satellite note and answers from prepared depth.

**Example pattern from v0.19 AI Safety Board paper:**
- Body: "Model capability — what a model can do — is the assessment unit reusable across use cases."
- Defense satellite: full risk = f(capability, reach) equation, six anticipated challenges (MRM territory, Design Authority territory, capability stability under finetuning, etc.), source lineage (Szpruch, Sudjianto, Bhatti, Ang; Gary Ang; pattern-based-governance paper).
- Reference satellite: Roose NYT article on METR validating institutional weight.
- Long-form parent paper: full architectural depth.

**Why the split works:**
- Body register stays Board-grade — accessible, punchy, no jargon
- Technical depth is preserved for any reviewer who needs it
- Defender enters challenge meetings with prepared answers, not improvised depth
- Future paper authors inherit the technical lineage via the satellite chain

**When to write the satellite:** as soon as you write a body claim that is layman-translated from a technical reality. The translation cost is not trivial. The defense satellite captures what was simplified and what the unsimplified version says.

**Anti-pattern:** writing the body in technical register because "the audience needs to understand the depth." The audience is the audience for the body. Defense audience is different. Layer them.

---

## House Style Follows the Audience's Headquarter

Default rule: **the paper's English house style follows the headquarter of the institution it serves, not the writer's location, not Capco's location, not the regulator's location.** HSBC Group → UK English. JPMorgan / Citi / Goldman / a US-domiciled fintech → US English. DBS / OCBC → UK English (Singapore inherits Commonwealth conventions). HSBC HK or StanChart HK → UK English (the Group HQ governs, not the local entity). Mixed audience → default to the most-senior reader's HQ.

The obvious spelling switches (-ize/-or vs -ise/-our) are not the discriminator — drafts of any provenance usually get those right. The high-signal markers are subtler, and they are what a native house-style reader's eye lands on first.

**Step 0 — identify the HQ before drafting.** Group HQ of the institution that owns the decision the paper is asking for. If unsure, check the audience's company filings or domicile of the most-senior named reader. Lock the variant before §1 of this skill, not after.

### UK English (HSBC, UK-domiciled, Commonwealth, Singapore)

**DO:**
- **Punctuation outside quotation marks** unless part of the quoted material. `the Board endorsed "capability spine".`
- **Single quotes first level**, double nested. Inverse of US.
- **Plural verb on collective nouns** as bodies of people: "the team are", "the Board are inclined", "Group AI are sponsoring". Singular when treating as single entity.
- **Date format** `27 April 2026`. No comma.
- **Double-L on inflected verbs:** modelled, labelled, cancelled, travelling, signalling, levelled.
- **Lexical:** programme (scheme; software → program), licence (n) / license (v), practice (n) / practise (v), enrol, fulfil, instil, judgement, organisation, recognise, prioritise, utilise, optimise, behaviour, defence, centre.
- **"Different from"** not "different than".

**DO NOT:**
- Default to "whilst/amongst/amidst" as UK signal — they read as archaism in modern Group prose. Plain "while/among" is correct.
- Mix `-ize` and `-ise` within the same paper.
- Use Oxford comma reflexively — UK is Oxford-optional, but consistency within the paper matters.

### US English (US-domiciled banks, US fintech, US regulators)

**DO:**
- **Punctuation inside quotation marks** for commas and periods. `the Board endorsed "capability spine."`
- **Double quotes first level**, single nested.
- **Singular verb on collective nouns:** "the Board is", "the team is".
- **Date format** `April 27, 2026`. Comma after day.
- **Single-L on inflected verbs:** modeled, labeled, canceled, traveling, signaling.
- **Lexical:** program, license (both n+v), practice (both n+v), enroll, fulfill, instill, judgment, organization, recognize, prioritize, utilize, optimize, behavior, defense, center.
- **Oxford comma is house default** for executive prose at most US institutions.

### Pre-send sweep

After locking the variant, grep for the wrong-variant tells:

```bash
# Drafting in UK — sweep for US leakage
grep -nE '\b(behavior|organize|optimize|recognize|analyze|defense|labor|color|favor|center|program(?!me)|practice as a verb|utilize|gotten|modeling|labeling|canceling|traveling|signaling|judgment)\b' <paper>
grep -nE '\b(January|February|March|April|May|June|July|August|September|October|November|December) [0-9]{1,2},' <paper>
grep -nE '[",]"|\."' <paper>   # punctuation inside quotes

# Drafting in US — sweep for UK leakage
grep -nE '\b(behaviour|organise|optimise|recognise|analyse|defence|labour|colour|favour|centre|programme|licence|practise|utilise|modelling|labelling|cancelled|travelling|signalling|judgement|whilst|amongst)\b' <paper>
grep -nE '\b[0-9]{1,2} (January|February|March|April|May|June|July|August|September|October|November|December) [0-9]{4}\b' <paper>
```

**Trigger.** Any paper, deck, memo, or cover note destined for an institutional reader. Identify HQ → lock variant → sweep before circulation. The rule applies to body, footnotes, references, version stamps, metadata, and email cover.

**Active routing for current chains.**
- HSBC Group / Doug / Beth / Rice / AIRCo / RMM / Board sub-committees / Bertie UK clearance → **UK**.
- PRA / FCA → **UK**.
- HKMA / SFC / MAS → **UK** (Commonwealth).
- Federal Reserve / OCC / SEC / CFTC → **US**.
- Capco internal (US-headquartered, FIS-owned) → **US** for internal-only artefacts; defer to client HQ when client-facing.

Related marks: `feedback_executive_paper_style`, `feedback_hsbc_is_the_buyer`, `feedback_uk_house_style_for_uk_chain_papers`.

---

## Architectural Discipline — Five Patterns for Multi-Pillar Papers

When a paper carries multiple workstreams, capabilities, or pillars, five patterns recur. Apply before the second iteration; the cost of fixing structure later compounds.

**1. Single-spine architecture.** One north-star metric; every sub-structure ladders to it. If two pillars look like they have separate goals, they are masquerading as parallel objectives — find the shared metric. Eunomia case (May 2026): Pillar 1 looked like cycle compression, Pillar 2 looked like function buildout; rewriting around "cycle time 150 → <100" as the single spine, with Pillar 2 as substrate that makes Pillar 1 sustainable, collapsed the paper from two-paper-grafted-together to one disciplined argument.

**2. Goal / mechanism / metric — separate the three.** Goal = strategic outcome (AI adoption at scale, safely). Mechanism = how (governance streamlining + safety capability). Metric = measurable proxy (cycle time). Senior register treats the metric as proxy, not as the destination. "100 days" reads as commitment; "the year-end north star is below 100" reads as ambition. Forward-looking work shouldn't claim the achieved state — "aims to cut" not "cuts"; "toward under 100" not "to under 100."

**3. Drop numbered scaffolding once names carry.** "Pillar 1 — X" / "Cap 1 — Y" / "Stream 1 — Z" reads as Section 1, Section 2 — junior register. Keep the categorical noun only if it earns its keep; otherwise let the names carry. "Two pillars deliver the number" is filler that can be dropped if pillar paragraphs introduce themselves naturally. Test: if the reader can navigate the paper using names alone, the numbers are scaffolding.

**4. Capability vs substrate — don't conflate practice with delivery mechanism.** What the function *does* (red-teaming, frontier scanning) is a capability; what the function *uses* (vendor tooling, consulting bridge, bench staff) is substrate. Capability paragraphs lead with the practice; tools and bench named as the delivery mechanism after the practice is established. Conflation makes the paper read as procurement-list rather than function-design.

**5. Provenance lives in appendix, not body.** Date attributions ("set on 1 May 2026 by [team]"), source citations, and audit-trail mechanics are reference material — they tell the reader where claims come from, not what to think. Body for what the reader needs to form a position; appendix for what they might want to verify. Test: would a reader who skips this still grasp the recommendation? If yes, it can move.

**Coherent terminology at every level.** When a paper has top-level halves and sub-level units, pick distinct terms — "tracks" + "streams" collide if "stream" and "workstream" are also used. Audit: grep for near-synonyms; eliminate or differentiate.

**Order by importance, not chronology.** Body sections lead with the structural mechanism that does the work; foundation/prerequisite work goes last. Reader sees what Eunomia is for before they see what it cleans up. Timeline milestones can keep chronological order — body discussion follows importance.

Related marks: `feedback_executive_paper_style`, `feedback_propose_concepts_not_edits`, `feedback_simplify_dont_engineer`.
