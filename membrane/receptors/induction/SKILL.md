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
---

# Induction — Writing That Instructs a Committee's Decision

In embryology, induction is the process where a signaling tissue secretes a diffusible factor that instructs the fate of a receiving tissue. A board paper is the same: a single artifact diffuses into a committee and patterns the decision that emerges. The paper does not argue in real time. It must arrive pre-loaded with everything required to convert pre-existing intent into a vote.

**Two entry points.** (1) Direct invocation when sitting down to draft an artifact for a committee that *decides* — OpCo, AIRCo, RMM, steering committees, board sub-committees, partner reviews. (2) Reference consultation from `expression` (forging committee-targeted assets), `censor` (high-weight criteria spine for executive papers), and `secretion` (before packaging committee deliverables).

The wording layer lives in marks (`feedback_executive_paper_style`, `feedback_partner_message_density`, `feedback_assert_dont_ask_in_senior_comms`, `feedback_echo_sponsor_language`, `feedback_naming_is_strategy`). This skill owns the upstream tradecraft.

**Detail loaded on demand from `references/`:**
- **`references/before-drafting.md`** — Canon (Bezos, Buffett, AR), AR copy/don't-copy, garden mining, pre-flight verification (stakeholder profile + named-entity existence checks).
- **`references/style-discipline.md`** — Sentence-level discipline, satellite-note pattern, UK/US house style + pre-send sweep, five architectural patterns for multi-pillar papers.
- **`references/review-loop.md`** — Pre-circulation tradecraft, multi-persona review (Pass A/B/C), pre-knockout grep discipline, named principal personas + delivery-vector knockout, three-round iteration loop, rejection-rule capture (challenge → three-layer → route).
- **`references/continuous-link.md`** — Continuous-link mode (live O365 / Google Docs share); discrete-send assumptions break; per-save discipline.

---

## When to Reach for This Skill

**Trigger when drafting:**
- HSBC executive papers (AIRCo, RMM, ExCo, OpCo, board sub-committee submissions)
- Capco partner-level proposals where the decision sits with a panel, not an individual
- Any client deliverable framed as "for endorsement" or "for approval"
- Internal Capco escalations to a partner committee
- Regulator-facing position papers where the regulator is a panel

**Do NOT reach for this skill for:**
- 1:1 senior emails (use `cursus` and the email marks)
- Garden posts (use `expression` and the garden marks)
- Networking outreach (use `message` and `cursus`)
- Working group discussion papers where no decision is requested (different genre — those are inputs to deliberation, not outputs)

---

## §0a. Lineage Pre-Flight (HARD, runs at session start before drafting any versioned paper artefact)

**When the user references a versioned paper artefact** ("write v0.X", "iterate on v0.Y", "Board paper for Z", or any session-start framing implying paper iteration), STOP and run the lineage check before any drafting:

1. **Identify the topic keyword(s).** What is this paper about? (e.g., "AI safety", "AI at scale", "capability spine", "Board paper", "[client name]")
2. **Grep chromatin/immunity for adjacent filename patterns.** Run: `ls ~/epigenome/chromatin/immunity/*<keyword>* | tail -20` for each plausible keyword. Look for any filename pattern that could contain a related lineage. **Filename-namespace difference is not evidence of separate lineage** — the same artefact may have multiple naming conventions across iterations.
3. **Read the highest-version file in any matching lineage.** Don't just list filenames — read the most recent version's frontmatter at minimum, body if architecture is unclear from frontmatter.
4. **Decide explicitly:**
   - **Refine on top of highest version** (default if mature lineage exists). Sub-version: v0.X.1 or v0.(X+1).
   - **Fresh derivation** (only if the existing lineage is structurally wrong for the new ask). Document the rationale in the new file's frontmatter so future-you doesn't lose it.
5. **State the decision in chat before drafting.** "Found existing v0.X at <path>; refining on top" or "Found v0.X but starting fresh because <reason>." This makes the decision auditable.

**Why this gate exists.** Failure mode confirmed across 2 consecutive sessions (29-30 Apr 2026): user references "v0.X of paper Y"; CC accepts framing literally and starts iterating without grepping for existing artefact lineage. Result on 30 Apr: eleven versions of an "ai-at-scale" series re-derived architecture already on disk in mature `hsbc-group-ai-safety-board-paper-capability-spine-v0.21.md` (sent to Doug+Beth+Simon 27 Apr). Filename-namespace difference (new series vs spine series) didn't visually surface the lineage to CC. Mark-only routing (`finding_check_existing_mature_versions_before_iterating.md` PROTECTED) is the layer-4 fallback; this skill gate is the higher-leverage layer-3 answer.

**Absolute ban — match and refuse:** If you find yourself about to write the first line of a new versioned paper artefact without having run the grep + read + explicit-decision steps above, STOP. Run them, log the decision inline, then proceed.

**DO NOT** trust filename-namespace separation as evidence of separate lineage. **DO NOT** skip the grep because "Terry would have mentioned if there's a prior version." **DO NOT** defer the grep to "first half-hour into work." First five minutes, not first half-hour.

---

## §0. Body-Edit Gate (HARD, runs before applying ANY committee-paper body edit)

**Before applying any edit to a committee-paper body — Board paper, satellite, cover note — you must pass these tests against the diff.** Same shape as `evaluate-ai-repo` §-1: deterministic gate at the trigger, not after-the-fact correction.

If any test fails, **do not apply or recommend** — revise or revert before write. The gate fires when *proposing* an option to Terry as well as when writing the diff. If applying despite a flag, name the flag and the override reason in the staging log entry.

| # | Test | Failure looks like | Cite |
|---|---|---|---|
| 1 | **Register fit** — committee-paper voice (declarative, third-party, bare assertion) | hedges (`we continue to`, `may`, `could`, `expect to`, `aim to`); modal qualifiers; first-person plural; consultancy markers (`as-is/to-be`, `framework`, `lever`); AR-style filler (`appropriate`, `robust`, `ongoing`, `comprehensive`) | `finding_ar_house_style_vs_ar_register.md`, `feedback_senior_register_observes_doesnt_argue.md` |
| 2 | **Vocabulary fit** — Board reader vocabulary, not internal jargon | `Data Fabric`, `as-is/to-be`, internal product names, business-unit acronyms not yet defined; consulting-shop terminology that doesn't appear in the audience's AR or earnings call | `feedback_dont_pollute_board_body_with_relational_asks.md` |
| 3 | **Dilution** — does the edit weaken the paragraph's load-bearing claim? | adds a second story alongside the existing one; introduces an enrichment dimension that competes with the load-bearing claim; weakens a precise verb to a softer one | `feedback_dont_pollute_board_body_with_relational_asks.md`, `feedback_paper_vs_comms_layer_split.md` |
| 4 | **Density ceiling** — is the paragraph already at body-length ceiling? | adding net words to a paragraph already at or above target length | `feedback_board_cut_as_compression_test_for_long_papers.md` |
| 5 | **Citation register** — verbatim quote + bare attribution; never `(p.X)` | `(Annual Report, p.106)`, `(p. 58)`, footnote-style page references, academic-citation parentheticals | `feedback_no_parenthetical_page_citations_in_committee_papers.md` |
| 6 | **Quantified-claim audience translation** — if importing a number from a source deck (sponsor's slide, internal report, AIRCo deck) into a paper for a *different* audience, the unit must mean the same thing in target register | "300 use cases delivered" reads as 300 production deployments to Board; in source-deck context = 300 task configurations within ONE approved capability container; **"if-true-headline test":** would this number, read literally in target register, be a headline-grade achievement? If yes but it's treated as routine in source context, the units don't match — DO NOT import the number, import the operating-model frame only | `finding_sponsor_slide_quantified_claim_audience_context.md` |
| 7 | **Rationale-annotations companion check** — before proposing ANY edit to a hardened paper artefact, check for and read the rationale-annotations companion file (`*-rationale-annotations.md` or any per-paragraph WHY/decision-log sibling). If present, it marks load-bearing phrases as "non-negotiable" / "knockout-pass-survived" / "deliberate political design". An edit that contradicts a non-negotiable marker fails this gate. Applies most strictly to defensive fixes — multi-LLM panels converge on defensive fixes regardless of whether the original was load-bearing | proposing softening of "carries independent authority to constrain deployment" without first reading the companion file | `finding_feed_rationale_layer_to_quorate.md`, `finding_gating_authority_check_before_tactical_fix.md` |
| 8 | **Diagnosis-validation against source paragraph** — when reviewer feedback claims the body or Ask has a defect, paste the cited source paragraph(s) verbatim from the *current* artefact into your analysis BEFORE evaluating whether the diagnosis is real. Convergence is not evidence; the source text is. Especially load-bearing for endorsement-register papers, where cold-read reviewers default to operating-model template (RACI/criteria/escalation belong inside the doc) and miss closing-loop commitments like "detailed implementation plan will follow within N weeks" | ratifying "n=3 reviewers say Ask is under-specified" without quoting the source paragraph that already contains the closing-loop commitment | `feedback_read_the_target_before_recommending_additions.md`, `feedback_council_without_rationale_file.md`, `finding_overnight_autonomy_on_converged_artefacts.md` |
| 9 | **Source-authority classification** — before asserting *any* institutional-weight characterisation of a cited source ("authoritative", "single-source", "private benchmark", "academic", "governmental", "weak", "strong", "canonical", "foreign", "domestic", "industry-led", "regulator-backed"), fetch the source's first page or About/Sponsor/Commissioning element and grep for the secretariat / commissioning body / sponsor / publishing institution. **No source-weight claim from training-data recall alone.** | dismissing the International AI Safety Report as "Canadian-chaired UN-style synthesis" without grepping the secretariat (DSIT-secretariat lineage was on page 1) | `feedback_verify_against_primary_source.md`, `finding_assert_before_verifying_pattern_needs_gate_28apr.md` |

**Absolute ban — match and refuse:** If you find yourself about to write the diff to a committee-paper body file (`hsbc-*-paper-*.md`, `hsbc-*-spine-*.md`, `*-board-paper-*.md`, satellite or cover note) without having walked these tests, **STOP**. Walk the tests, log the result inline as a one-liner before the staging log entry. If any test fails, do not apply.

**The bare-question challenge as self-test.** Terry's high-leverage move is "does it make the paper better?" Five words, neutral, on artefact-utility terms. Run it on yourself before applying — the diff has to survive your own version of that question.

**DO** walk the tests in order before writing the staging log entry, not after. **DO** log the result inline: `Gate: 1✓ register; 2✓ vocab; 3✓ dilution; 4✓ density; 5✓ citation`. **DO NOT** apply the edit then run the gate retroactively. **DO NOT** skip the gate on satellite or cover note.

---

## §1. Decide Before You Draft: Five Pre-Conditions

A paper that influences was already going to win before it was circulated. The drafting effort confirms a decision the room was already reaching. If any of these five are missing, do not draft yet — fix the precondition first.

1. **Sponsor pre-aligned.** The senior in the room who owns the agenda item has read or heard the thesis and signalled assent. Surprising your sponsor in the meeting is malpractice.
2. **Decision asked.** The paper requests one specific thing: approval, endorsement, mandate, or a named dissent. "For information" papers do not influence — they decorate.
3. **Dissent absorbed.** The two or three members most likely to object have been pre-consulted; their language and concerns appear inside the paper, attributed or naturalised.
4. **Framing claimed.** The paper names the problem in the language the committee will then use afterwards. Whoever names the problem owns the solution space.
5. **Evidence load-bearing at the top.** The first 200 words contain the strongest factual claim, and that claim is sourced. Everything below is scaffolding.

Pre-circulation is not optional politeness — it is the mechanism. The meeting ratifies; it does not deliberate.

---

## §2. Sequence the Paper Around the Decision, Not the Argument

Most consultants write the paper as a journey: context, analysis, options, recommendation. Committees do not read journeys. They read the recommendation, then triangulate backwards to check for fatal flaws.

The committee reads in this order whether you intend it or not:

1. Title and one-line standfirst (what is being decided)
2. The recommendation (what they are being asked to approve)
3. The named risk (what could embarrass them if approved)
4. The sponsor's name (whose neck is on the block)
5. Selected evidence (only if anything above looks weak)

Write in that order. Lead with the decision. Place context behind the recommendation, not in front of it. The Bezos six-pager, the McKinsey one-pager, and a well-drafted OpCo minute all share this inversion: conclusion first, narrative second.

---

## §3. Anti-Patterns — Match and Refuse

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

## §4. The 200-Word Test

Before circulating any draft, write the 200-word version. If the 200-word version cannot stand alone as the paper, the longer version is hiding weakness behind length. The 200-word version contains:

- The decision being asked (one sentence)
- The recommendation (one sentence)
- The single load-bearing fact (one sentence)
- The named alternative and why it loses (one sentence)
- The dissent already absorbed (one sentence)
- The sponsor and the timing (one sentence)

Six sentences. If any of the six is missing, the long version will not survive the room either.

---

## Detail Pointers

**Before drafting any paper:** read `references/before-drafting.md` for canon, garden mining, and pre-flight verification (stakeholder profile + named-entity existence checks).

**While polishing or restructuring:** read `references/style-discipline.md` for sentence-level discipline, satellite-note pattern, UK/US house style + pre-send sweep, and the five architectural patterns for multi-pillar papers.

**Before circulating:** read `references/review-loop.md` for pre-circulation tradecraft, multi-persona review passes (A/B/C), pre-knockout grep discipline, named principal personas, the three-round iteration loop, and rejection-rule capture protocol.

**When the artefact is shared as a live link:** read `references/continuous-link.md` for the per-save discipline that replaces discrete-send assumptions.

---

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
