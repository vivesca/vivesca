---
name: induction
description: Committee-paper tradecraft — writing artifacts that move boards, OpCo, AIRCo, RMM, steering committees, board sub-committees, and partner panels to decide. Owns pre-conditions, recommendation-first sequence, dissent absorption, pre-circulation. Use directly when drafting a paper for a deciding committee, or as a reference consulted by expression, censor, secretion.
user_invocable: true
epistemics: [communicate, persuade, evaluate]
triggers:
  - induction
  - board paper
  - committee paper
  - executive paper
  - opco
  - aircco
  - steering paper
  - decision paper
---

# Induction — Writing That Instructs a Committee's Decision

In embryology, induction is the process where a signaling tissue secretes a diffusible factor that instructs the fate of a receiving tissue. A board paper is the same: a single artifact diffuses into a committee and patterns the decision that emerges. The paper does not argue in real time. It must arrive pre-loaded with everything required to convert pre-existing intent into a vote.

**Two entry points.** (1) Direct invocation when sitting down to draft an artifact for a committee that *decides* — OpCo, AIRCo, RMM, steering committees, board sub-committees, partner reviews. (2) Reference consultation from `expression` (forging committee-targeted assets), `censor` (high-weight criteria spine for executive papers), and `secretion` (before packaging committee deliverables). The `expression` skill owns weekly forging. The `censor` skill owns post-hoc quality gating. The `secretion` skill owns packaging and release. This skill owns the principles that make the artifact land.

The wording layer lives in marks (`feedback_executive_paper_style`, `feedback_partner_message_density`, `feedback_assert_dont_ask_in_senior_comms`, `feedback_echo_sponsor_language`, `feedback_naming_is_strategy`). This skill owns the upstream tradecraft.

---

## 0a. Lineage Pre-Flight (HARD, runs at session start before drafting any versioned paper artefact)

**When the user references a versioned paper artefact** ("write v0.X", "iterate on v0.Y", "Board paper for Z", or any session-start framing implying paper iteration), STOP and run the lineage check before any drafting:

1. **Identify the topic keyword(s).** What is this paper about? (e.g., "AI safety", "AI at scale", "capability spine", "Board paper", "[client name]")
2. **Grep chromatin/immunity for adjacent filename patterns.** Run: `ls ~/epigenome/chromatin/immunity/*<keyword>* | tail -20` for each plausible keyword. Look for any filename pattern that could contain a related lineage. **Filename-namespace difference is not evidence of separate lineage** — the same artefact may have multiple naming conventions across iterations (e.g., `ai-at-scale-v0.X` and `hsbc-group-ai-safety-board-paper-capability-spine-v0.X` can be the same artefact lineage).
3. **Read the highest-version file in any matching lineage.** Don't just list filenames — read the most recent version's frontmatter at minimum, body if architecture is unclear from frontmatter.
4. **Decide explicitly:**
   - **Refine on top of highest version** (default if mature lineage exists). Sub-version: v0.X.1 or v0.(X+1).
   - **Fresh derivation** (only if the existing lineage is structurally wrong for the new ask). Document the rationale in the new file's frontmatter so future-you doesn't lose it.
5. **State the decision in chat before drafting.** "Found existing v0.X at <path>; refining on top" or "Found v0.X but starting fresh because <reason>." This makes the decision auditable.

**Why this gate exists.** Failure mode confirmed across 2 consecutive sessions (29 Apr, 30 Apr 2026): user references "v0.X of paper Y" or "Board paper for Z"; CC accepts framing literally and starts iterating without grepping for existing artefact lineage. Result on 30 Apr: eleven versions of an "ai-at-scale" series re-derived architecture already on disk in mature `hsbc-group-ai-safety-board-paper-capability-spine-v0.21.md` (sent to Doug+Beth+Simon 27 Apr, multiple knockouts done). Filename-namespace difference (new series vs spine series) didn't visually surface the lineage to CC. Mark-only routing (`finding_check_existing_mature_versions_before_iterating.md` PROTECTED, 30 Apr; `feedback_ask_what_user_wants_before_iterating_on_form.md` PROTECTED, 29 Apr) is the layer-4 fallback; this skill edit is the higher-leverage layer-3 answer per retrospective §3a layer-hierarchy walk.

**Absolute ban — match and refuse:**

If you find yourself about to write the first line of a new versioned paper artefact without having run the grep + read + explicit-decision steps above, STOP. Run them, log the decision inline, then proceed.

**DO:**
- Grep at the FIRST tool call after user references a paper artefact, before any drafting.
- Read the highest-version file's frontmatter + recent commits (`git log -10 --oneline -- <filepath>`) to understand current state.
- State the decision explicitly in chat: "Found existing v0.X at <path>; refining" or "No existing lineage; fresh derivation."

**DO NOT:**
- Trust filename-namespace separation as evidence of separate lineage. Two different naming conventions can describe the same artefact.
- Skip the grep because "Terry would have mentioned if there's a prior version." 30 Apr session: Terry mentioned spine v0.21 only after eleven re-derivations.
- Defer the grep to "first half-hour into work." First five minutes, not first half-hour.

---

## 0. Body-Edit Gate (HARD, runs before applying ANY committee-paper body edit)



**Before applying any edit to a committee-paper body — Board paper, satellite, cover note — you must pass five tests against the diff.** Same shape as `evaluate-ai-repo` §-1: deterministic gate at the trigger, not after-the-fact correction.

If any test fails, **do not apply or recommend** — revise or revert before write. The gate fires when *proposing* an option to Terry as well as when writing the diff. Recommending option (c) to apply an edit, then walking the tests after Terry pushes back, is the same failure mode as applying-without-gate. If applying despite a flag, name the flag and the override reason in the staging log entry.

| # | Test | Failure looks like | Cite |
|---|---|---|---|
| 1 | **Register fit** — committee-paper voice (declarative, third-party, bare assertion) | hedges (`we continue to`, `may`, `could`, `expect to`, `aim to`); modal qualifiers; first-person plural; consultancy markers (`as-is/to-be`, `framework`, `lever`); AR-style filler (`appropriate`, `robust`, `ongoing`, `comprehensive`) | `finding_ar_house_style_vs_ar_register.md` (PROTECTED), `feedback_senior_register_observes_doesnt_argue.md` (PROTECTED) |
| 2 | **Vocabulary fit** — Board reader vocabulary, not internal jargon | `Data Fabric`, `as-is/to-be`, internal product names, business-unit acronyms not yet defined; consulting-shop terminology that doesn't appear in the audience's AR or earnings call | `feedback_dont_pollute_board_body_with_relational_asks.md` (PROTECTED) |
| 3 | **Dilution** — does the edit weaken the paragraph's load-bearing claim? | adds a second story alongside the existing one; introduces an enrichment dimension that competes with the load-bearing claim; weakens a precise verb to a softer one | `feedback_dont_pollute_board_body_with_relational_asks.md`, `feedback_paper_vs_comms_layer_split.md` |
| 4 | **Density ceiling** — is the paragraph already at body-length ceiling? | adding net words to a paragraph already at or above target length; Cap 1 already densest, edit pushes density further | `feedback_board_cut_as_compression_test_for_long_papers.md` (PROTECTED) |
| 5 | **Citation register** — verbatim quote + bare attribution; never `(p.X)` | `(Annual Report, p.106)`, `(p. 58)`, footnote-style page references, academic-citation parentheticals | `feedback_no_parenthetical_page_citations_in_committee_papers.md` (PROTECTED) |
| 6 | **Quantified-claim audience translation** — if importing a number from a source deck (sponsor's slide, internal report, AIRCo deck) into a paper for a *different* audience, the unit must mean the same thing in target register | "300 use cases delivered" reads as 300 production deployments to Board; in source-deck context = 300 task configurations within ONE approved capability container; **"if-true-headline test":** would this number, read literally in target register, be a headline-grade achievement? If yes but it's treated as routine in source context, the units don't match — DO NOT import the number, import the operating-model frame only | `finding_sponsor_slide_quantified_claim_audience_context.md` (PROTECTED) |
| 7 | **Rationale-annotations companion check** — before proposing ANY edit (body, Recommendation, Ask, frontmatter) to a hardened paper artefact, check for and read the rationale-annotations companion file (`*-rationale-annotations.md` or any per-paragraph WHY/decision-log sibling alongside the paper). If present, the file marks load-bearing phrases as "non-negotiable" / "knockout-pass-survived" / "deliberate political design". An edit that contradicts a non-negotiable marker fails this gate. Applies most strictly when the proposed edit is a defensive fix (softening a claim, adding hedges, cross-referencing for safety) — multi-LLM panels and adversarial reviewers converge on defensive fixes regardless of whether the original was load-bearing; the companion file is the only ground truth for what's settled | proposing "soften 'carries independent authority to constrain deployment' to 'calibration input'" without first reading the companion file, which marks that exact sentence "Independent-authority sentence is non-negotiable... without it the paper is a soft-power memo. Reviewers tested its register weight in the v0.17 risk-knockout pass; it survived" | `finding_feed_rationale_layer_to_quorate.md` (PROTECTED), `finding_gating_authority_check_before_tactical_fix.md` (PROTECTED) |
| 8 | **Diagnosis-validation against source paragraph** — when reviewer feedback (single reviewer, multi-LLM panel, or N-cold-read consensus) claims the body or Ask has a defect ("Ask under-specified", "X is too dense", "decision rights vague"), paste the cited source paragraph(s) verbatim from the *current* artefact into your analysis BEFORE evaluating whether the diagnosis is real. Convergence is not evidence; the source text is. Especially load-bearing for endorsement-register papers, where cold-read reviewers default to operating-model template (RACI/criteria/escalation belong inside the doc) and miss closing-loop commitments like "detailed implementation plan will follow within N weeks" — that IS the right structural answer for an endorsement Ask, not a gap | ratifying "n=3 reviewers say Ask is under-specified" across multiple turns without quoting `v0.20:66`, which already contains "A detailed implementation plan will follow within four weeks" — the closing-loop commitment that handles exactly what reviewers thought was missing; treating multi-LLM consensus on a hardened artefact as proof of a real gap | `feedback_read_the_target_before_recommending_additions.md` (PROTECTED, confirmed=2 — extended to ratifying-direction), `feedback_council_without_rationale_file.md` (PROTECTED, confirmed=2 — template-confusion extension), `finding_overnight_autonomy_on_converged_artefacts.md` (PROTECTED, confirmed=4) |
| 9 | **Source-authority classification** — before asserting *any* institutional-weight characterisation of a cited source ("authoritative", "single-source", "private benchmark", "academic", "governmental", "weak", "strong", "canonical", "foreign", "domestic", "industry-led", "regulator-backed"), fetch the source's first page or About/Sponsor/Commissioning element and grep for the secretariat / commissioning body / sponsor / publishing institution. **No source-weight claim from training-data recall alone.** Especially load-bearing when recommending whether to accept, reject, or upgrade a citation — the institutional anchor changes the recommendation. The discriminator question Terry uses ("but is X authoritative?") fires reliably; preempt it by running this test before the recommendation lands | dismissing the International AI Safety Report as "Canadian-chaired UN-style synthesis" / "foreign-academic" without grepping the secretariat, then reversing the framing under Terry's "but is the report authoritative?" — DSIT-secretariat lineage was on page 1 of the parsed report; the dismissal would have flipped to "UK-Government-commissioned" if the verification had run before the recommendation | `feedback_verify_against_primary_source.md` (PROTECTED, confirmed=4 — source-authority extension, 2026-04-28), `finding_assert_before_verifying_pattern_needs_gate_28apr.md` (PROTECTED, confirmed=5+) |

**Absolute ban — match and refuse:**

If you find yourself about to write the diff to a committee-paper body file (`hsbc-*-paper-*.md`, `hsbc-*-spine-*.md`, `*-board-paper-*.md`, satellite or cover note) without having walked these five tests, **STOP**. Walk the tests, log the result inline as a one-liner before the staging log entry. If any test fails, do not apply.

**Why this gate exists.** Failure mode confirmed across **11 retrospectives in 24 hours** (28 Apr 2026): CC produces a body edit that fails one of the tests, the regression is caught only on Terry's bare-question challenge ("does it make the paper better?", "should the paper cite the AR elegantly?", "is the 300 use case thing what they're trying to do or done already? otherwise should be a very big highlight?"). Marks alone (`feedback_dont_pollute_board_body_with_relational_asks.md`, `feedback_no_parenthetical_page_citations_in_committee_papers.md`, `finding_ar_house_style_vs_ar_register.md`, `finding_sponsor_slide_quantified_claim_audience_context.md`) have not deterred recurrence; multiple confirmed-count bumps have not deterred either. Per the cross-session pattern check protocol, this requires deterministic enforcement at the skill level, not another mark. The escalation finding `finding_assert_before_verifying_pattern_needs_gate_28apr.md` (`confirmed: 5`) routes here. **Test 6 added 2026-04-28 evening** after the 11th instance: importing Doug's slide-37 "300+ use cases delivered via single capability + single RMF approval" as quantified anchor in v0.20 Recommendation, reverted on Terry's audience-register catch. **Test 8 added 2026-04-28 ~19:30** after the 16th-shape-variant instance — ratifying "n=3 reviewers say Ask under-specified" across multiple turns without reading `v0.20:66`, which already contains the closing-loop commitment ("detailed implementation plan will follow within four weeks"). Inverse direction of Tests 1–7: those gate edits-being-applied; Test 8 gates positions-being-formed about whether reviewer feedback identifies a real defect. Cold-read reviewer convergence on endorsement-register papers is predictably template-confusion (operating-model template applied to endorsement scope) — Test 8 catches this before any edit is even proposed.

**The bare-question challenge as self-test.** Terry's high-leverage move is "does it make the paper better?" Five words, neutral, on artefact-utility terms. Run it on yourself before applying — the diff has to survive your own version of that question. If you can't articulate why the diff makes the paper better against the five tests above, the diff is not ready.

**DO:**
- Walk the five tests in order before writing the staging log entry, not after.
- Log the result inline: `Gate: 1✓ register; 2✓ vocab; 3✓ dilution; 4✓ density; 5✓ citation` (or `1✗ register: hedge "may"`, etc.).
- When a test fails, revise the diff or skip the edit. Do not apply with a flag pending.
- For relational asks (sponsor-forwarded operating-layer input), default to satellite + follow-up paper, not body. Apply test 2 + test 3 explicitly.

**DO NOT:**
- Apply the edit then run the gate retroactively. After-the-fact gating is what the marks layer already failed at.
- Treat "iteration license earned by responding to a sponsor's named ask" as override authority. Sponsor asks land in correspondence notes, satellites, follow-up papers — not Board body unless the body is the only place the answer fits.
- Skip the gate on satellite or cover note. Same five tests, scaled to register; satellites tolerate more density and more vocabulary, but `(p.X)` citations and dilution still fail.

---

## 1. Decide Before You Draft: Five Pre-Conditions

A paper that influences was already going to win before it was circulated. The drafting effort confirms a decision the room was already reaching. If any of these five are missing, do not draft yet — fix the precondition first.

1. **Sponsor pre-aligned.** The senior in the room who owns the agenda item has read or heard the thesis and signalled assent. Surprising your sponsor in the meeting is malpractice.
2. **Decision asked.** The paper requests one specific thing: approval, endorsement, mandate, or a named dissent. "For information" papers do not influence — they decorate.
3. **Dissent absorbed.** The two or three members most likely to object have been pre-consulted; their language and concerns appear inside the paper, attributed or naturalised.
4. **Framing claimed.** The paper names the problem in the language the committee will then use afterwards. Whoever names the problem owns the solution space.
5. **Evidence load-bearing at the top.** The first 200 words contain the strongest factual claim, and that claim is sourced. Everything below is scaffolding.

Pre-circulation is not optional politeness — it is the mechanism. The meeting ratifies; it does not deliberate.

---

## 2. Sequence the Paper Around the Decision, Not the Argument

Most consultants write the paper as a journey: context, analysis, options, recommendation. Committees do not read journeys. They read the recommendation, then triangulate backwards to check for fatal flaws.

The committee reads in this order whether you intend it or not:

1. Title and one-line standfirst (what is being decided)
2. The recommendation (what they are being asked to approve)
3. The named risk (what could embarrass them if approved)
4. The sponsor's name (whose neck is on the block)
5. Selected evidence (only if anything above looks weak)

Write in that order. Lead with the decision. Place context behind the recommendation, not in front of it. The Bezos six-pager, the McKinsey one-pager, and a well-drafted OpCo minute all share this inversion: conclusion first, narrative second.

---

## 3. The Canon — What to Read When Stuck

These are the references when a paper feels limp:

- **Bezos six-pager** — narrative memo replacing slides at Amazon S-team. Forces complete sentences and removes the option to bullet around weak thinking. Read for the silent-reading discipline and the "FAQ" appendix as dissent absorption.
- **McKinsey one-pager / pyramid principle** — Barbara Minto's SCQA (Situation, Complication, Question, Answer). Useful when forced to compress to a single page; the pyramid forces you to lead with the answer.
- **Buffett's Berkshire shareholder letters** — masterclass in writing to a board of one (himself, retroactively). Plain prose, declarative voice, hard numbers, no jargon. Read for tonal calibration in HSBC executive papers.
- **OpCo / RMM minutes (HSBC)** — the closest live reference for the audience Terry writes to. Mimic the cadence and the attribution patterns. Group-wide language. No bold. No tables in body. Citations as footnote-style references, not URLs.
- **Andy Grove, *Output Management*** — meeting design. Useful upstream of the paper: what kind of meeting is this, and what therefore must the paper do?
- **The audience institution's Annual Report + earnings call transcript** — primary source for house-style conventions, vocabulary anchors, risk taxonomy capitalisation, acronym patterns, and Group voice. For HSBC: `chromatin/immunity/hsbc-ar2025-full-markdown-agentic.md` (citable agentic-tier extraction) + `chromatin/immunity/hsbc-fy25-earnings-call-ai-qa-2026-04-25.md`. **Read selectively, not wholesale** — see §3b for the copy/don't-copy distinction.

Ghost-write *as* the institution, not as the consultant. The paper should read as if it could have been drafted by an internal director.

---

## 3b. Annual Report — What to Copy, What Not to Copy

The audience's Annual Report is the institution's **most public statement of how it talks about itself**. It looks like the canonical source — and for some things it is. For other things it actively misleads. Distinguish two axes:

**Copy (house style, vocabulary, anchors):**
- House style conventions: UK English, "the Group" capitalisation, "Group-wide" hyphenation, acronym first-mention with single-quoted parens (`'GenAI'`, `'MRM'`, `'PRA'`), spaced em-dashes, possessive forms.
- Vocabulary anchors: identify 3–5 phrases the AR uses repeatedly for the relevant risk domain. Adopt verbatim where a sentence in the paper benefits from institutional voice. For HSBC AI papers: `agentic AI (autonomous systems powered by AI agents)`, `oversight and challenge`, `Three Lines of Defence`, `heightened scrutiny`, `capabilities, methodologies and tools`, `colleagues` (not `employees`), `Risk and Control Solutions function`.
- Strategic verbatim quotes when grounding a claim in Group voice — bare attribution, no page numbers. The verbatim quote IS the citation. See `feedback_no_parenthetical_page_citations_in_committee_papers`.
- Risk taxonomy capitalisation: `Model risk`, `Financial crime risk`, `Data risk`.

**Do NOT copy (register mismatch — AR is shareholder-defensive, paper is decision-instructing):**
- "We continue to..." verb pattern → committee paper uses present declarative.
- "to help [verb]" hedge → committee paper asserts directly.
- Long compound sentences with three nested qualifiers → punch once per sentence (§4a).
- Modal hedges ("may", "could", "expect to", "aim to") → bare assertion in Recommendation/Ask (`feedback_assert_dont_ask_in_senior_comms`).
- Filler qualifiers ("appropriate", "robust", "ongoing", "comprehensive") → genome `executive_paper_style` anti-pattern.
- First-person plural voice → committee paper is third-party institutional ("the Board is invited", "the Group adopts").
- Defensive framing ("we seek to ensure", "we work to balance") → committee paper is decisive.

**Activation gate (run before any committee-paper send):**

Pass 1 — house-style alignment: paper matches AR conventions per §4c.

Pass 2 — register check, grep paper body for:
- `\bwe \w+` (first-person plural)
- `to help \w+` (hedge)
- `\b(may|could|expect to|aim to)\b` (modal hedge)
- `\b(appropriate|robust|ongoing|comprehensive)\b` (filler qualifier)
- `\(p\. ?[0-9]+\)` (academic-register page citation)

Each hit is a candidate register-mismatch — review and convert unless the hedging is structurally required (rare in committee papers).

**Generalises beyond HSBC.** For any client with an AR + earnings call corpus, treat them as the audience-specific reference set. Identify the equivalent vocabulary anchors in the first 10 minutes of paper drafting; bake them into the body at strategic points; reject the AR's hedging register in the paper's own voice.

**Source files for this finding:** `finding_ar_house_style_vs_ar_register.md` (Protected) and `finding_llamaparse_default_vs_agentic_tier_delta.md` (use agentic-tier extractions for verbatim citation, not default-tier).

---

## 3a. Mine First-Party Prior Thinking — Garden Before Drafting

Before drafting any paper whose topic overlaps with active garden themes (`~/epigenome/chromatin/secretome/` + `~/epigenome/secretome/`), mine the garden as a first-party source. The garden contains the principal author's already-articulated framings, distinctions, and one-liners — material the paper's audience has not seen, written without committee filter, often sharper on premises and definitions than fresh draft prose.

**When to trigger.** Topic alignment, not paper-cycle recurrence. AI-governance paper × AI-governance garden = high yield. Cyber paper × AI-governance garden = low yield. Skip when topic-mismatched.

**How to mine (two-pass).**

1. **Title + frontmatter description grep.** Catches direct hits. `awk '/^description:/{print}'` across the secretome dir surfaces the description-tagged subset in seconds.
2. **Semantic search (qmd).** Catches concept-adjacent posts whose titles use different vocabulary than the paper's frame. Pure grep misses these.

**What to lift.** Premises, conceptual cuts, single-phrase formulations. Never wholesale paragraphs — register mismatch (garden is essayistic, board is constitutional). For each candidate borrow, run `feedback_carve_out_language_in_stakeholder_papers.md` and `finding_board_paper_ask_scope_only_unique_decisions.md` before pasting.

**Two routings if a strong idea doesn't fit the current paper.** (a) Cover note or backchannel with extra airtime (Bertie heads-up class). (b) Follow-up paper with broader scope (CAIO follow-up class). Strong ideas without a current home park with named routing, not "later."

See `finding_garden_as_paper_input_source.md` for the methodology origin.

---

## 4. Anti-Patterns — Match and Refuse

If the draft contains any of these, stop and rewrite — they are paper-killers in a senior committee:

- **Recommendation buried below context.** The committee should never have to scroll to find what they are being asked to do.
- **Options without a recommendation.** Presenting three options and asking the committee to choose is abdication, not advice. Recommend one and name the trade-off.
- **Unsourced claims at the top.** The first quantified claim in the paper anchors trust. If it is wrong or unsourced, every later claim is suspect.
- **Bold, tables, brackets in the body.** Executive papers are prose. Visual emphasis signals deck thinking — wrong register for a committee paper.
- **Consultant voice.** "We recommend that the firm should consider…" — gut it. Direct voice in the institution's register: "The Group will adopt…" or "AIRCo is asked to endorse…".
- **Generic risk language.** "There are risks to this approach" — name them, attribute them, and say what cancels them.
- **Filler executive summary.** A summary that re-states the agenda is not a summary. The summary IS the paper at 200 words; the body exists for committee members who want the receipts.
- **Hedging the ask.** "We would suggest considering whether it might be appropriate to potentially…" — assert. The room can tolerate being told what to do; it cannot tolerate ambiguity about what is being asked.

---

## 4a. Sentence-Level Discipline — Shorter, Simpler, Punchier

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

## 4c. House Style Follows the Audience's Headquarter

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

## 4b. Technical-Backing Satellite Notes — Body Layman, Defense Hidden

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

## 5. The 200-Word Test

Before circulating any draft, write the 200-word version. If the 200-word version cannot stand alone as the paper, the longer version is hiding weakness behind length. The 200-word version contains:

- The decision being asked (one sentence)
- The recommendation (one sentence)
- The single load-bearing fact (one sentence)
- The named alternative and why it loses (one sentence)
- The dissent already absorbed (one sentence)
- The sponsor and the timing (one sentence)

Six sentences. If any of the six is missing, the long version will not survive the room either.

---

## 6. Pre-Circulation Tradecraft

The paper is not done when written; it is done when it has been walked through. Sequence:

1. **Sponsor read** — the senior who owns the agenda item reads first, in private, with permission to redirect. Their changes are not edits; they are alignment signals.
2. **Dissent walk-through** — the one or two members most likely to push back receive the paper in person or 1-on-1, with the question "what would make you not block this?" Their concerns become bullets in the paper.
3. **Adjacent stakeholder copy** — anyone whose territory the paper crosses gets a courtesy copy ahead of circulation, not in the meeting. Surprising a peer in committee earns a permanent enemy.
4. **Read-ahead window** — circulate at least 48 hours before the meeting. Less than 24 hours signals either disorganisation or an attempt to suppress scrutiny; either reads badly.
5. **Speak-to** — the in-meeting verbal frame. One minute. Not a re-read of the paper. The frame names the decision, names the sponsor, names the dissent absorbed, and yields. The paper does the rest.

Pre-circulation is the work. The meeting is the receipt.

**Cover note + Bertie heads-up + Doug coaching are correspondence-class artefacts.** They follow `endocrine` Compose-mode standalone-correspondence precondition: each gets its own `chromatin/immunity/YYYY-MM-DD-terry-<recipient>-<subject>.md` file with verbatim text + interlinks BEFORE send. Per `feedback_standalone_correspondence_notes.md` (PROTECTED), this catches the recurring asymmetry where outbound gets summarised in daily notes only and verbatim is later unrecoverable.

---

## 7. Multi-Persona Review — Paper-as-Code

Before the three pre-circulation steps in §6, run two structured review passes in parallel. Single-pass review by the author misses different failure modes than what each pass surfaces; running them as named lenses with separate context exposes the artefact to the same scrutiny it will face in committee.

**Pass A — Adversarial multi-persona (CE pipeline applied to paper).** Treat the paper as code. Dispatch four parallel review personas, each scoped to one lens:

| Persona | Looks for | Ships findings as |
|---|---|---|
| Correctness | Every factual claim, citation, number, date, verbatim quote — does the source say what the paper claims? Internal consistency between Recommendation, body, and Ask. | Punch list, severity-tagged. URL verifications dispatched in parallel for any external citation; vendor-spec rule applies (never quote a fact without verifying the source). |
| Coherence | Terminology drift between sections; Recommendation↔body alignment; register breaks; ambiguity where multiple readers would diverge on meaning; cross-section reference integrity. | Punch list, with the divergent readings spelled out. |
| Maintainability | Cuttable paragraphs, redundant evidence, hedge accumulation, parenthetical asides, transitional fluff that announces what the next sentence proves. The "force the floor" principle applied externally. | Cuts only — never additions; the paper is at version N for a reason. |
| Adversarial | Premise audit: what load-bearing assumption could a hostile reader challenge? Unstated assumptions; implementability hand-waves; territorial reads; weakest citation; the strongest argument against the Ask itself. **Drop overlap with existing verbal-coaching prep.** | Each finding as: ATTACK NAME / who would mount it / the move / paper's current defence / proposed reinforcement. |
| Cross-Presenter | Receptor-class routing under hostile read. Read as a reader in attribution / blame / budget-contraction mode and ask: does this paper still route to the intended decision class (deliberation, capability investment), or does it cross-present onto a kill-pathway (accountability, budget cut, team replacement)? Triggers: individuals/teams named adjacent to the gap, passive-voice failure descriptions, gap-without-owner framings. Bio source: MHC-I cross-presentation of exogenous antigen — same content, opposite receptor class, opposite decision. See `~/epigenome/marks/finding_cross_presentation_wrong_receptor_routing.md`. | Each finding as: ROUTING ATTACK / which paragraph triggers cross-presentation / which decision class it routes to / proposed reframe to keep MHC-II routing fidelity. |

Each persona gets the paper plus the project's tailored alignment checklists as constraints — so they don't propose changes that violate already-decided commitments. Outputs merge into a single deduped punch list.

**Pass B — Tailored alignment checklists.** Run in parallel with Pass A. The checklists are project-specific (HSBC: P1-P8 public-commitments, A-F master-alignment, audience-fit). Each checklist is a static gate against authority alignment. Each item: PASS / FIX / BLOCKER, with paper location and proposed insert.

**Why both passes.** They catch different failure classes. Adversarial multi-persona catches premise + factual issues a static checklist cannot — overclaim modifiers, underclaim modifiers, political-structural risk in a single sentence, citation hand-waves. Tailored checklists catch authority-alignment gaps multi-persona reviewers cannot — verbatim language the principal expects, named bodies, function placements, diction the audience uses. **Neither replaces the other.** Single-pass review ships papers with one of the two failure classes intact.

**Convergence is the win.** When the two passes name the same finding (e.g., third-party scope appears in both adversarial premise audit and Principle-6 alignment), one insert satisfies both. Treat overlap as confirmation, not redundancy.

**Pass C — Verbal coaching capture.** Findings that don't survive paper edits flow into per-stakeholder verbal-coaching notes. Adversarial findings about hostile-reader attacks become anticipated questions; uncomfortable nuances surfaced by URL verification (success rates, base-rate caveats, scope qualifiers) become Q&A lines. The paper carries the assertion; the coaching carries the defence.

**Sequencing.** Pass A and Pass B run before §6's sponsor read. Pass C output goes to the sponsor alongside the paper. By the time the sponsor reads, every reviewer-detectable failure mode has been merged or routed — sponsor-read is for alignment, not error-catching.

**See also:** `avidity.md` (stakeholder-binding rules — three principles + corollaries), `tolerance.md` (regulator-defensibility rules), `finding_ce_pipeline_complements_alignment_checklists.md` (the empirical evidence behind the both-passes rule).

---

## 8. Named Principal Personas — The Discriminator Half

§7's adversarial multi-persona pass uses generic lenses (Correctness / Coherence / Maintainability / Adversarial). Those catch craft failures. They do NOT catch "Simon would never sign this" or "Doug would route this to OpCo not AIRCo." That requires named principal-lenses.

For every paper, identify each principal in the read chain (sponsor, decision-maker, copy-list, downstream router) and dispatch the `principal-lens` agent once per principal in parallel. Each lens loads the principal's stakeholder profile from `~/epigenome/chromatin/immunity/<name>-profile.md` and returns the top-5 questions/objections that principal would raise on first read.

Current HSBC AI Safety profile coverage (April 2026):

| Principal | Profile path | Read-chain role |
|---|---|---|
| Simon Eltringham | `simon-eltringham-hsbc-profile.md` | Sponsor — Capco channel into HSBC RAI |
| Doug Robertson | `doug-robertson-hsbc-profile.md` | Decision-router — owns Simon's agenda, routes upward |
| David Rice | `david-rice-hsbc-profile.md` | First HSBC CAIO (eff. 1 Apr 2026), top of paper chain |
| Jeff Valane | `jeff-valane-hsbc-profile.md` | Cross-functional reader (Risk) |
| David Newby | `david-newby-hsbc-profile.md` | Cross-functional reader |

When dispatching: pass `profile=<absolute path>`, `paper=<absolute path>`, optionally `ask=<one-line ask interpretation>`. Run all principals in parallel — each lens has its own context.

**Profile-as-discriminator-training-data.** A principal-lens is only as good as the profile. Findings that surface a "PROFILE GAP" return value (the lens cannot determine whether the principal would defend a position) flow back into the profile as the next maintenance step. The profile improves monotonically over engagements; the discriminator improves with it.

**Adding a new principal.** Before drafting any paper for a new audience, ensure each named reader has a profile in `chromatin/immunity/`. No profile = no principal-lens = the discriminator pass cannot model that reader. This is a precondition to the iteration loop in §9.

### 8a. Delivery-Vector Knockout — Principals Who Read the Send Sequence, Not the Content

Some principals will never read the paper but will be politically affected by *how* it lands — who gets it when, in what order, whether they were briefed in advance. Bertie (Capco UK Partner with HSBC alignment ownership) is the canonical example: the paper itself is fine, but the send sequence violates a UK-clearance rule and that's a relationship breach independent of any body content.

For every paper, identify each delivery-vector principal in addition to read-chain principals. Their `principal-lens` dispatch focuses on:

- The send order (who first, who simultaneously, who told only after)
- Pre-circulation of the send plan to anyone with a standing rule about being informed
- Acknowledgement language for any rule the send sequence overrides ("we judged X for reason Y; ratify or override")
- Cross-territorial sensitivities (UK office vs HK office, headquarter vs regional)
- Visibility-map gaps (who isn't in the send list but should know it exists)

**Findings format differs.** Body-readers return paper-edit findings. Delivery-vector readers return send-sequence findings: re-time, acknowledge, override, hold, add-to-list. These do NOT consolidate into v0.N+1 paper patches — they consolidate into pre-send decisions that the human must make before any send executes.

**Trigger for adding a delivery-vector lens.** Any principal whose written rules govern the *channel* the paper travels through (UK-office clearance protocols, HRBP notification thresholds, regulator pre-notification expectations, Group Communications signoff for external-facing material). Memory file `feedback_*` of the form "always tell X before Y" = candidate.

---

## 9. The Iteration Loop — Generator / Discriminator Convergence

The drafting → review → patch cycle is GAN-shaped: the author (generator) produces a draft, the principal-lenses (discriminator) attack it, the author patches, the lenses attack again. Hard cap: three iterations. Knockout strategy across rounds: each round's draft must beat the prior round's draft *on each principal-lens's own terms*; the stronger draft survives. Inherits the loop shape from `affinity`; named-principal discriminators and knockout-survival are the induction-specific specialisations.

**Round 0 — outline interrogation, not draft.** Front-load the personas at outline stage, not review stage. Lifted from STORM (arxiv 2402.14207): turn each principal-lens into an interrogator that grills a retrieval-grounded "topic expert" agent (the author with chromatin/epistemics access) about the paper's premise, scope, and ask. Build the outline from the Q&A logs, not from the author's first instinct. The principals' questions front-load what the paper must defend; the outline is the structure that lets it. Only THEN draft. Force the floor (300 words for a Board ask) on the actual prose pass.

**Round 1, 2, 3 — review-and-patch.**

1. Dispatch all principal-lenses in parallel (`principal-lens` agent, one call per profile).
2. Dispatch §7 Pass A (adversarial multi-persona — generic lenses) and Pass B (alignment checklists) in parallel WITH the principal-lenses, not after. They catch different failure classes.
3. Merge findings into one deduped punch list. Tag each finding: NEW (this round), REPEAT (raised in a prior round, still unfixed), CONVERGED (raised previously, fix lands this round).
4. Author patches the paper. Each NEW finding becomes a paper edit OR routes to verbal-coaching capture (Pass C) OR is explicitly accepted as residual gap.
5. **Knockout test.** Re-dispatch each principal-lens with BOTH the new draft AND the prior round's draft as context. The lens picks which is stronger *for its principal*. If the new draft loses on any lens, revert that section to the prior round's wording — patches are not monotonically additive. Only knockout-winning patches carry forward. (PerFine, arxiv 2510.24469: knockout-survival across iterations beats last-edit-wins by 7-13% on profile-grounded GEval; plateaus at 3-5 iterations — empirical justification for the hard cap.)
6. Carry the surviving draft to the next round.

**Hard cap: three rounds.** Iter 1 catches major, iter 2 catches subtle, iter 3 catches edges. Iter 4+ catches nothing but burns tokens. If round 3 still leaves blocking findings, escalate to human (Terry) — do not run round 4. Cap is from Claude Forge's empirical observation; PerFine's plateau confirms.

**Failure mode: source-bias-transfer.** When the generator quotes one source heavily (typically the principal's own approved corpus — the DQM-precedent move), the paper drifts into voicing that source even where the claim is the author's. Lens check at every round: which sources got cited >2x? Do their cadences leak into uncited paragraphs? If yes, rewrite in the author's voice or attribute. (Named in STORM as an outline-stage failure; persists at draft stage too.)

**Failure mode: over-association.** Retrieval glues facts that sit near each other in source material but aren't actually causally or evidentially linked. The paper reads coherent and turns out to be claiming a relationship the sources don't support. Lens check: for every "X, therefore Y" or "X and Y" sentence, can both halves be sourced to the same evidence chain? If not, sever the conjunction. (STORM's second named failure.)

**Failure mode: chasing every NEW finding to zero in one round.** If you patch every NEW finding immediately and dispatch again, you destroy round-to-round signal. Findings need to PERSIST across rounds for the lens to learn what is structurally fixable vs structurally residual. Run two rounds minimum before deciding which findings are residual.

**Failure mode: convergence theatre.** A lens returning zero NEW findings on round 2 may mean the paper landed OR may mean the lens has nothing left to say from the profile. Cross-check: did the patches actually address the round 1 findings, or did the lens just exhaust its profile-grounded objections? If the latter, the profile needs more depth before the next paper.

**Failure mode: same lens, different prompts.** Dispatching the same principal-lens twice with subtle prompt differences and treating the variance as signal is noise-mining. Keep the dispatch deterministic — same profile, same paper, same round number visible to the lens.

**Convergence-as-confidence across principals.** When N principal-lenses independently surface the same finding, the finding is structurally true — single-principal findings are weaker than multi-principal ones. Triage in this order:

1. **Convergent BLOCKINGGs** (≥3 principals agree) — patch immediately, no further deliberation. The paper has a structural failure.
2. **Convergent NITs** (≥3 principals agree) — patch unless the cost is high; structural friction even if not blocking.
3. **Single-principal BLOCKINGGs** — load-bearing only if that principal is in the decision chain; otherwise weight by political distance.
4. **Conflicting findings** (two principals disagree on direction) — decision goes up to the author. A real disagreement between principals usually maps to a real political tension that the paper has to navigate, not paper-fix.

The principal-lens output should annotate "overlaps with [other principal]" when detectable from prior knockout files in the same directory, to make convergence detection automatic at triage time.

**Failure mode: GAN mode collapse / parallel-writer drift.** The author over-fits to the dominant lens (usually the sponsor) and the paper drifts away from the other principals. Counter: dictator pattern — sponsor has FINAL say, other lenses ADVISE. Weight findings by political distance from the author, not by frequency. Doug's one objection outweighs Simon's three when Doug is the route-decider. (AutoGen long-doc community observation: parallel writers drift on tone and re-litigate trivia; dictator + tree-of-files + hard round caps is the working pattern.)

**Stopping early.** If ALL principal-lenses return Board-ask-grade findings on round 1 (no challenges, only clarifications), the paper is over-cooked — strip it to a shorter sibling. Convergence in one round is a sign of insufficient ambition, not of paper quality.

**See also.** `affinity` skill (multi-round multi-model stress-test mechanics — induction inherits the loop shape from affinity, replaces generic personas with named principals). `avidity.md` (stakeholder-binding rules — the multi-principal generator side: gap-statement-not-pain-build, LOAD-restoration, fresh-reader corollary, cover-note-carries-extras, board-diction-is-constitutional). `tolerance.md` (regulator-defensibility rules — the supervisor selection pressure: cadence-coupling-is-red-flag, capability-without-RACI-is-unfinished, "extends not above" structural patch pattern, body-strips-Recommendation-carries-for-date-binding). `finding_paper_variants_as_sponsor_routing_optionality.md` (when one paper splits into siblings rather than converges to one artefact).

**Prior art.** STORM (Shao et al. 2402.14207) — front-load personas at outline. Co-STORM (2408.15232) — dynamic mind map + user-as-steerer for longer loops. PerFine (2510.24469) — knockout-survival critique-refine, +7-13% over RAG baselines, 3-5 iter plateau. Claude Forge (freecodecamp Mar 2026) — rhetorical-question reviewers, architecturally separated review process, hard 3-iter cap. AutoGen long-doc thread (microsoft/autogen#67) — dictator pattern beats consensus.

---

## 10. Rejection-Rule Capture — How the Discriminator Improves

The `principal-lens` agents are only as good as the profile they load and the rules they apply. The most valuable training data the system produces is **what Terry rejects** — when the author judges a knockout-proposed patch is wrong, the *reason* for that rejection encodes taste that the lens did not yet have.

Without capture, every paper's rejection knowledge dies with the session and the next paper's knockouts re-propose the same wrong patches. With capture, the discriminator gets sharper monotonically per paper cycle.

**Critical caveat: Terry is not always right.** A rejection can be a one-off context-specific judgement, a tired pattern-match to the wrong situation, or correct-for-this-paper-but-wrong-as-a-general-rule. If the protocol methylates every rejection as a rule without a check, the discriminator profiles fill with frozen Terry-states that don't generalise. The fix: rejection capture is **two-step**, not one — the rejection generates a *candidate* rule; CC challenges; agreement methylates.

**The protocol — applies at every triage point, not just at session end.**

For every patch proposed by a principal-lens that Terry rejects (or directs CC to reject):

1. **Capture the rejection text inline at triage time.** Don't defer to wrap. The reason is freshest in Terry's voice the moment the rejection is spoken: "no, that would have made Doug look like he's coopting Rice's commitment" or "that's a Capco-shape failure mode, Doug wouldn't write it that way."

2. **CHALLENGE before filing.** Before routing the rejection to a destination file, ask one sharp question: "Is this reason load-bearing as a rule, or is it pattern-matching to this situation?" Construct one specific example of where the rule would over-fire — a future paper, principal, or context where applying this rule mechanically would produce a worse outcome. Present the candidate rule + the over-fire example. Three branches:
   - **Terry agrees the rule is sharp** → file as written.
   - **Terry refines** ("yes, but only when X / except when Y") → file the refined version with the conditions explicit.
   - **Terry retracts** ("actually that was just this paper, not a rule") → don't file. The discussion itself was the calibration.

   The challenge is not adversarial — it's calibration. Both halves apply: Terry's instinct is the source signal; CC's challenge tests whether it generalises. The rule lands only after agreement. Skipping the challenge means filing rules that will misfire on the next paper, which is worse than not capturing — over-fitting beats under-fitting only when there's no reset mechanism.

3. **Capture three layers, not just the imperative.** Rules age better when their calibration boundaries travel with them. Future-CC reading the rule needs the *imperative* to act, AND the *source signal + discussion arc* to judge edge cases. Lossy capture (imperative-only) means future sessions re-discover the calibration; rich capture (three layers) lets calibration transfer.

   Three layers per rule entry:
   - **Layer 1 — Imperative.** "DO X / DO NOT Y / DO X when Z." This is what the lens fires on.
   - **Layer 2 — Source signal.** What triggered the discussion: the rejected patch, the over-fire example, Terry's instinct phrased in his words. ("Terry rejected the AISI cite under Rice's voice because Rice publicly committed to no pre-formed plan; signing a six-capability proposal preempts that listening commitment.")
   - **Layer 3 — Discussion arc + agreed framing.** What pressure-testing produced the final scope. Captures the calibration boundary — the rule's *limits* are encoded here. ("Considered: literal rule = 'cite all external methodology under principal voice = bad'. Refined to: 'don't cite under principal voice WITHOUT verifying principal has read it'. Reason: AR-routing is fine; direct citation under voice without principal-read is the actual hazard. Edge case: if principal HAS read the source, direct citation is acceptable.")

   The three-layer capture is the **co-organism principle** applied to rule formation: two intelligences with different bases (CC's model + training; Terry's organism context + taste) converge on a position with higher confidence than either input alone. The discussion arc IS the asset — it's how the convergence path stays available for future application. Imperative-only capture loses the path; three-layer capture preserves it.

4. **Route the three-layer rule to the right destination by content:**

   | Rejection content | Destination file | Mark type |
   |---|---|---|
   | About a specific principal's preference, voice, or unstated rule | The principal's profile note in `chromatin/immunity/<name>-profile.md` | append to "Voice & Preferences" or "Unstated rules" section |
   | About a generalisable craft rule (avoid X in any senior paper) | `avidity.md` (stakeholder-binding) or `tolerance.md` (regulator-defensibility) by content | new DO/DO NOT pair |
   | About a regulatory-defensibility pattern | `tolerance.md` | new pattern entry |
   | About a project-specific constraint (this engagement, not all engagements) | `~/epigenome/marks/project_<engagement>.md` | new fact entry |
   | About a personal preference / judgment pattern | `~/epigenome/marks/feedback_*.md` (existing or new) | new feedback rule |

3. **Format every captured rejection as a discriminator rule, not a description:**
   - Bad: "Terry rejected the AISI mention because it would commit Rice to AISI methodology endorsement."
   - Good: "DO NOT cite AISI evaluation methodology under Rice's voice without first verifying Rice has read the underlying AISI document. Cite via the Annual Report's own treatment instead. Reason: regulatory-defensibility — PRA reads CAIO endorsing external methodology as benchmark commitment."

4. **The lens consumes this on the next dispatch.** When `principal-lens` is dispatched for the next paper, the agent reads the principal profile (now richer) and the relevant epistemics (now richer). The discriminator is sharper without any model retraining.

**Test the loop is working.** After 3-5 paper cycles, the same class of finding should stop appearing in knockout outputs because the rules have been captured. If knockout #5 returns the same blocking finding as knockout #1, the rejection-rule capture failed somewhere — either the capture wasn't done, the capture went to the wrong destination, or the lens isn't reading the destination.

**The taste-scaling thesis.** Terry is the bottleneck only as long as the rules live in his head. Every captured rejection is one rule that no longer needs his head to fire. The skill scales when rejection capture is treated as the most important output of the triage session — more important than the patches that survive, because those land once. The captured rules land forever.

**Anti-pattern: capturing without routing.** Stockpiling rejections in a single learnings.md file fails — the next dispatch doesn't know to read that file. Capture must route to the file the lens already loads (profile note, avidity, tolerance, marks). If a rejection doesn't have an obvious destination, that's signal that a new file is needed, not that the capture should be deferred.

**Anti-pattern: capturing only in Terry's voice, not as a rule.** "Terry didn't like X" is a description, not a rule. The lens cannot fire on description. Re-write as: "DO X / DO NOT X / DO X when Y / Reason Z." Discriminator rules are imperatives, not narrations.

**Anti-pattern: skipping the challenge step.** If CC files every rejection without challenging, the rule library accumulates frozen Terry-states that misfire on the next paper. The challenge step is not optional — it's the calibration mechanism. Better to file fewer rules that survive the challenge than many rules that look like signal but aren't.

**See also.** `affinity` skill (similar capture pattern for generic-deliverable iteration). The `feedback_*.md` mark family is the existing exemplar of rejection-rule capture done right (each entry is an imperative with a Reason and How-to-apply).

---

## 11. Continuous-Link Mode — When the Artefact is Live

§1-10 implicitly assume **discrete-send mode**: the paper is finalized, circulated 48h ahead, walked through with sponsor and dissenters, then walked into the meeting. The five preconditions in §1, the pre-circulation tradecraft in §6, and the iteration loop in §9 all assume the artefact is frozen at the moment of share.

**Continuous-link mode breaks all of those assumptions.** When the artefact is shared as an O365 / Google Docs / Notion live link with framing like "I'll keep iterating", recipients watch a moving artefact, not a finalized ask. There is no circulation event; there is no quiet draft state. Each save is a fresh presentation to whoever opens the link in that window.

The induction tradecraft does not break — but it has to be re-applied per save instead of once before send. Mechanism source: `~/epigenome/marks/finding_anergy_risk_unsponsored_board_paper.md` (continuous-link refinement section) and `finding_cross_presentation_wrong_receptor_routing.md`.

**What changes per precondition:**

| §1 precondition | Discrete-send | Continuous-link |
|---|---|---|
| Sponsor pre-aligned | Sponsor signed *this version* | Sponsor signed the *trajectory* — does each save's diff honour the sponsor's last signaled direction? |
| Decision asked | One specific ask, frozen | Ask may evolve through the trajectory; the *current state* of the ask must be unambiguous on every save |
| Dissent absorbed | Dissenter language baked in pre-send | Dissenter comments arrive as Word/Docs comments mid-trajectory; absorb them into the next save, not into a notional v_n+1 |
| Framing claimed | Framing locked at circulation | Framing can drift across saves — every save audits whether the trajectory still claims the same problem-name |
| Evidence load-bearing at top | Verified pre-send | Re-verified per save if any top-200-word claim was edited |

**What changes per §7 review pass:** Adversarial multi-persona, principal-lenses, and especially the cross-presenter persona fire on **every save**, not once before notional send. The cross-presenter check is the most load-bearing in continuous-link mode — every save is a fresh presentation, so a single intermediate save with kill-pathway routing is what whoever-opens-the-link-in-that-window reads.

**Engagement-trace as co-stimulation evidence.** In discrete-send mode, sponsor co-signal is a cover note or back-channel before send. In continuous-link mode, the signal is **engagement trace**: read receipts, comments, replies, named mentions of the paper in adjacent threads. If saves keep landing and the trace stays empty, that is anergy in continuous-link form — the recipients are treating the link as not-worth-watching. The next save needs to either invite engagement explicitly or **stop iterating until back-channel signal arrives**.

**Iteration license — when to keep editing vs hold.** The cover note framing licenses iteration. Without it, every save is a presumption; with it, the trajectory itself is the artefact. But license is finite: even with "I'll keep iterating", four+ saves with no engagement = anergy regime, and edits at that point dig the hole rather than fill it. Three signals to **stop iterating and back-channel**:

1. **Engagement trace stays empty across 3+ saves** (no comments, no read receipts visible, no adjacent-thread mentions).
2. **A save introduces a substantive change** (new claim, scope shift, ask revision) — substantive changes deserve a notification, not silent landing.
3. **Routing risk surfaces in a knockout pass** that would benefit from sponsor calibration before going further. Don't auto-patch and re-land; back-channel and ask.

**Save discipline.** In continuous-link mode, treat each save as a discrete-send-equivalent for the purposes of §7 review. Run the cross-presenter check before save, not before send. The cost of running the check 5x more often is small; the cost of one rogue intermediate save being what a recipient reads is permanent.

**Routing back to discrete-send.** When the trajectory converges (sponsor co-signal arrives, ask is locked, no further iteration anticipated), explicitly transition out of continuous-link mode: "this is the version we're presenting." The transition matters because §6 pre-circulation tradecraft re-engages from that point — the speak-to, the read-ahead, the dissent walk-through.

**Anti-pattern: silent drift.** Iterating across many saves without explicit transition points produces papers that "sort of got endorsed" because everyone watched them grow. That is not endorsement. The transition out of continuous-link mode IS the endorsement event; without it, no decision has actually been ratified.

---

## 12. When to Reach for This Skill

Trigger when drafting:

- HSBC executive papers (AIRCo, RMM, ExCo, OpCo, board sub-committee submissions)
- Capco partner-level proposals where the decision sits with a panel, not an individual
- Any client deliverable framed as "for endorsement" or "for approval"
- Internal Capco escalations to a partner committee
- Regulator-facing position papers where the regulator is a panel

Do **not** reach for this skill for:

- 1:1 senior emails (use `cursus` and the email marks)
- Garden posts (use `expression` and the garden marks)
- Networking outreach (use `message` and `cursus`)
- Working group discussion papers where no decision is requested (different genre — those are inputs to deliberation, not outputs)

## Triggers

- induction
- board paper
- committee paper
- executive paper
- opco
- aircco
- airco
- steering paper
- decision paper
- live link
- live doc
- live word doc
- live document
- O365 link
- Google Docs share
- while iterating
- keep iterating
- continuous link
- O365 live
- Word doc share
