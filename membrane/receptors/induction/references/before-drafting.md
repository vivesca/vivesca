# Before Drafting — What to Read, How to Mine, How to Verify

Loaded on demand by `induction` SKILL.md when drafting a committee paper.

---

## The Canon — What to Read When Stuck

These are the references when a paper feels limp:

- **Bezos six-pager** — narrative memo replacing slides at Amazon S-team. Forces complete sentences and removes the option to bullet around weak thinking. Read for the silent-reading discipline and the "FAQ" appendix as dissent absorption.
- **McKinsey one-pager / pyramid principle** — Barbara Minto's SCQA (Situation, Complication, Question, Answer). Useful when forced to compress to a single page; the pyramid forces you to lead with the answer.
- **Buffett's Berkshire shareholder letters** — masterclass in writing to a board of one (himself, retroactively). Plain prose, declarative voice, hard numbers, no jargon. Read for tonal calibration in HSBC executive papers.
- **OpCo / RMM minutes (HSBC)** — the closest live reference for the audience Terry writes to. Mimic the cadence and the attribution patterns. Group-wide language. No bold. No tables in body. Citations as footnote-style references, not URLs.
- **Andy Grove, *Output Management*** — meeting design. Useful upstream of the paper: what kind of meeting is this, and what therefore must the paper do?
- **The audience institution's Annual Report + earnings call transcript** — primary source for house-style conventions, vocabulary anchors, risk taxonomy capitalisation, acronym patterns, and Group voice. For HSBC: `chromatin/immunity/hsbc-ar2025-full-markdown-agentic.md` (citable agentic-tier extraction) + `chromatin/immunity/hsbc-fy25-earnings-call-ai-qa-2026-04-25.md`. **Read selectively, not wholesale** — see "Annual Report — What to Copy, What Not to Copy" below.

Ghost-write *as* the institution, not as the consultant. The paper should read as if it could have been drafted by an internal director.

---

## Annual Report — What to Copy, What Not to Copy

The audience's Annual Report is the institution's **most public statement of how it talks about itself**. It looks like the canonical source — and for some things it is. For other things it actively misleads. Distinguish two axes:

**Copy (house style, vocabulary, anchors):**
- House style conventions: UK English, "the Group" capitalisation, "Group-wide" hyphenation, acronym first-mention with single-quoted parens (`'GenAI'`, `'MRM'`, `'PRA'`), spaced em-dashes, possessive forms.
- Vocabulary anchors: identify 3–5 phrases the AR uses repeatedly for the relevant risk domain. Adopt verbatim where a sentence in the paper benefits from institutional voice. For HSBC AI papers: `agentic AI (autonomous systems powered by AI agents)`, `oversight and challenge`, `Three Lines of Defence`, `heightened scrutiny`, `capabilities, methodologies and tools`, `colleagues` (not `employees`), `Risk and Control Solutions function`.
- Strategic verbatim quotes when grounding a claim in Group voice — bare attribution, no page numbers. The verbatim quote IS the citation. See `feedback_no_parenthetical_page_citations_in_committee_papers`.
- Risk taxonomy capitalisation: `Model risk`, `Financial crime risk`, `Data risk`.

**Do NOT copy (register mismatch — AR is shareholder-defensive, paper is decision-instructing):**
- "We continue to..." verb pattern → committee paper uses present declarative.
- "to help [verb]" hedge → committee paper asserts directly.
- Long compound sentences with three nested qualifiers → punch once per sentence (see "Sentence-Level Discipline").
- Modal hedges ("may", "could", "expect to", "aim to") → bare assertion in Recommendation/Ask (`feedback_assert_dont_ask_in_senior_comms`).
- Filler qualifiers ("appropriate", "robust", "ongoing", "comprehensive") → genome `executive_paper_style` anti-pattern.
- First-person plural voice → committee paper is third-party institutional ("the Board is invited", "the Group adopts").
- Defensive framing ("we seek to ensure", "we work to balance") → committee paper is decisive.

**Activation gate (run before any committee-paper send):**

Pass 1 — house-style alignment: paper matches AR conventions per the House Style reference.

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

## Mine First-Party Prior Thinking — Garden Before Drafting

Before drafting any paper whose topic overlaps with active garden themes (`~/epigenome/chromatin/secretome/` + `~/epigenome/secretome/`), mine the garden as a first-party source. The garden contains the principal author's already-articulated framings, distinctions, and one-liners — material the paper's audience has not seen, written without committee filter, often sharper on premises and definitions than fresh draft prose.

**When to trigger.** Topic alignment, not paper-cycle recurrence. AI-governance paper × AI-governance garden = high yield. Cyber paper × AI-governance garden = low yield. Skip when topic-mismatched.

**How to mine (two-pass).**

1. **Title + frontmatter description grep.** Catches direct hits. `awk '/^description:/{print}'` across the secretome dir surfaces the description-tagged subset in seconds.
2. **Semantic search (qmd).** Catches concept-adjacent posts whose titles use different vocabulary than the paper's frame. Pure grep misses these.

**What to lift.** Premises, conceptual cuts, single-phrase formulations. Never wholesale paragraphs — register mismatch (garden is essayistic, board is constitutional). For each candidate borrow, run `feedback_carve_out_language_in_stakeholder_papers.md` and `finding_board_paper_ask_scope_only_unique_decisions.md` before pasting.

**Two routings if a strong idea doesn't fit the current paper.** (a) Cover note or backchannel with extra airtime (Bertie heads-up class). (b) Follow-up paper with broader scope (CAIO follow-up class). Strong ideas without a current home park with named routing, not "later."

See `finding_garden_as_paper_input_source.md` for the methodology origin.

---

## Pre-flight Verification — Run Before Any Paper-Shaping Reasoning

**The failure mode.** Within minutes of a paper-shaping session starting, CC forms a reasoning frame about audience, scope, named entities. Once formed, that frame justifies many downstream decisions (which arguments will land, which examples to use, which references to keep). When the frame is wrong, every downstream decision is wrong — and the corrections only surface when the principal user catches them, sometimes after 30+ turns. This pattern recurs across multiple sessions despite protected marks requiring profile reads at session start (`feedback_read_stakeholder_profiles_before_paper_strategy.md`); the marks are loaded but unactivated. Activation-not-capture, classic shape.

**The fix.** Two deterministic pre-flight checks before forming any reasoning frame about the paper:

**Pre-flight 1 — Stakeholder profile read.** For every named principal who will read the paper (audience) or who is positioned in the body (sponsor, named team), grep `~/epigenome/chromatin/immunity/` for `<principal>-profile.md` and read it before forming any voice / audience / register claim. Don't assume background, career, or familiarity — if profile exists, read it; if not, surface the gap. Eunomia case (May 2026): CC ran 30+ turns assuming David Rice was Anthropic-native (justifying technical model-cadence claims, classical-reference depth, Sonnet 4.5/4.6 fluency); profile recorded 18-year HSBC banking insider. All downstream "this lands for him" reasoning was wrong frame. Cost: paper had to be re-evaluated against the right reader profile after correction. Pre-flight cost: 2-minute grep + skim.

**Pre-flight 2 — Named-entity existence check.** Before asserting that an entity (governance body, programme, role, framework) exists at the institution, grep chromatin for the entity name. If references show "proposed by", "to be established", or "Stage N of <plan>", the entity is not yet existing — the body should reflect that or reference the proposing plan. Eunomia case: Stream 4 (Tiering and parallel routing) was added to body with structural-compression-load claim, asserting the Group AI Design Authority as if it operated. Chromatin search after Terry's probe revealed DA is a Project 100 Days proposal, not an existing entity. Stream 4 dropped; substance moved to cutting-room-floor. Same family as stakeholder-profile failure: assert without verifying entity is real / current.

**Trigger.** Both checks fire at paper-shaping session start, before forming any reasoning frame. State which profiles were read and which entities were verified inline at first turn. If a check returns "no profile" or "entity not yet existing", surface the gap before reasoning forward. The deterministic action is "grep + read + state finding"; the failure mode is "skip and assume."

**Skill cross-reference.** This pre-flight is the same activation pattern as the `marks library skim` rule in genome.md ("when starting work on a tool, skill, or domain, grep marks for the tool/skill name and skim top 2-3 hits before proceeding"). Profile pre-flight is the principal-specific version; entity pre-flight is the institution-specific version. Both work the same way: not by remembering, but by looking.

Related marks: `feedback_read_stakeholder_profiles_before_paper_strategy.md` (PROTECTED), `finding_activation_not_capture_is_the_session_gap.md` (PROTECTED, instance log).
