# Consilium — High-Value Use Cases & ROI Evidence

Tracks real sessions where consilium meaningfully changed the output vs what Claude alone would have produced.

---

## Case 1: Interview Deck Red-Team (Mar 12, 2026)

**Mode:** `--deep --xpol` (~$1.05, ~9 min)
**Task:** Review 8-slide interview deck for MTR Senior Manager AI role. Find weaknesses before submission.

### What consilium caught that Claude missed

**1. Capco/HR dealbreaker — triage escalation**
Claude had placed the "you're joining Capco while interviewing for MTR" issue in "consider later." Council unanimously escalated it to DO NOW #1 — categorical HR dealbreaker that could kill the interview regardless of technical performance. Marlie Fong (HR interviewer) would flag Terry as flight risk. Claude had underweighted the HR axis entirely.

**2. Metric credibility landmines (Slide 6)**
"99% accuracy" for a GenAI RAG system is a massive red flag for a technical interviewer. All 5 models independently flagged this in the blind phase without prompting. Claude hadn't flagged it. Fix: add measurement methodology to each metric sub-label (agent-rated, system-logged, etc.).

**3. Slides 3→5 narrative arc diagnosis**
Council identified that the friction already exists in the deck (Compliance blocked Option A on Slide 3), but is presented as a sterile table rather than a contested decision. The fix is verbal — bridge Slide 3 to Slide 5 explicitly — not a new story. Claude had been framing this as "add a conflict story" which would have felt fabricated. Council's diagnosis was more precise.

**4. Sonnet's critique of the judge**
The cross-pollination pass was where the most nuanced value appeared. Sonnet's critique identified where the judge's own advice would make things worse (fabricated conflict script, Capco risk misweighted, HKUST name-drop overconfidence). This layer wouldn't exist in a single-pass council — the xpol pass earned its $0.15.

### What consilium got wrong
- Initial judge synthesis prescribed a fabricated "held the line" script — caught and corrected in the xpol critique pass
- HKUST alumni name-drop flagged as "brilliant soft power" — xpol correctly identified it as superficial risk
- Do Now list added content without removing any, internally inconsistent on pacing — also caught in critique

### ROI verdict
**High.** ~$1 changed three concrete actions: escalated Capco narrative to urgent, added metric methodology to slides, sharpened the Slide 7 MTR specificity. The xpol pass justified the cost delta over `--council`.

---

## Case 2: Interview Deck Red-Team Round 2 — "Specificity Trap" (Mar 12, 2026)

**Mode:** `--deep --xpol` (~$1.05, ~9 min)
**Task:** Second pass on the same deck after v2 edits (compressed text, added metric sub-labels). Expected validation. Got surprises.

### What consilium caught that Claude missed

**1. Specificity trap — adding detail created new attack surfaces**
Claude treated the v2 edits as improvements. Council identified that adding metric methodology labels ("agent-rated", "timed") didn't fix credibility — it illuminated methodological weaknesses. "Agent-rated 99% accuracy" is construct invalidity: it measures acceptance, not ground-truth correctness. "Timed 20-second" compared to an anecdotal "2-minute" baseline is measurement asymmetry. Claude had treated labelling as resolution; council saw it as exposure.

**2. "Safety-critical" is an MTR landmine**
The phrase appeared on Slides 5 and 7. All 5 models independently flagged it in the blind phase without prompting. At MTR, safety-critical means passengers die or trains derail. Applying it to a call-centre RAG chatbot reads as tone-deaf to a Chief Manager of a railway operator. Claude hadn't flagged this once across two reviews.

**3. Voicebot hardware claim — unanimous technical trap**
Slide 3 mentioned deploying on "existing voicebot server hardware." Council (unanimously, blind) identified that legacy voicebot hardware runs on CPUs/DSPs for audio processing; LLM inference requires VRAM/GPUs. If uncaveated, Daniel Cheung would immediately probe model size, quantization level, and p99 latency. Claude had read the hardware mention as a positive (resourcefulness, cost savings) rather than an interrogation target.

**4. PCPD vs PDPO — precision error under governance claim**
Slide 5 said "PCPD-compliant." PCPD is the regulator; PDPO is the law. For a candidate whose entire pitch rests on governance rigour (FCPA, CIA, HKMA sandbox), using the wrong acronym for the applicable privacy law is a self-undermining credibility puncture. Claude missed it across both prior reviews.

**5. "Capco Principal Consultant" on Slide 8 signals visiting expert**
The closing slide named the Capco transition. Council flagged this as reinforcing an external-consultant identity when MTR wants a long-term internal owner. Marlie (HR) would read it as "flight risk who's already leaving." Claude had not flagged it as a Slide 8 visual problem — only as a verbal Q&A issue.

**6. Architecture vs. governance conflation (Slide 5)**
Council (and judge) identified that "Architecture Principles" on Slide 5 are actually risk/governance controls. "Human-in-the-Loop" and "Audit Trail" are control frameworks, not architectural decisions. For a role titled AI & Data Architecture, this signals IT auditor, not architect. The xpol critique usefully pushed back on this: enterprise architecture frameworks (TOGAF, SABSA) do treat data sovereignty and auditability as architectural constraints — so the fix is verbal reframing, not slide replacement.

**7. Happy path / decision authority ambiguity**
Slide 4 shows clean stakeholder alignment. Council identified this reads as "effective facilitator" not "architectural decision-maker." Senior Manager candidates at infrastructure operators are expected to show judgment under adversity. The fix: clarify decision authority in the opening 60 seconds ("I held the architectural decision rights — not just the business case") and have one productive conflict story for Marlie.

### What consilium got wrong / overcorrected
- Judge initially prioritised voicebot hardware prep as #1 (requires research). Sonnet's critique correctly reordered: "Remove safety-critical" is a 30-second slide edit with zero risk — should be #1.
- Judge buried PCPD/PDPO in "Consider Later." Sonnet's critique escalated it to "Do Now" — correct, given the governance-rigour premise.
- Judge's scripted Slide 7 verbal bridge ("the cross-border data residency...are the exact muscles I'm bringing") foregrounds the gap (no physical-world AI experience) rather than the offer. Risky framing that the main synthesis missed.
- The "38× adoption growth" metric was not flagged by any model — a blind spot. If the denominator is unclear, Daniel can collapse the stat by asking what the pilot-to-full-rollout count actually was.

### ROI verdict
**High — and surprising.** Claude had reviewed this deck twice in-session and made v2 edits. Council on the v2 found four new issues Claude had never raised (safety-critical, hardware trap, PCPD, Capco close) and correctly identified that Claude's own "improvements" (metric labels) had created new vulnerabilities. The second $1 found more value than the first. Pattern: **consilium on a revised artifact is often more valuable than the first pass** — edits expose structure that was previously hidden.

### Key learning
**Adding specificity to claims invites audit of methodology.** When you label a metric's provenance, you're inviting the question "is that provenance valid?" Claude defaults to "more information = better." Council stress-tests whether the information survives scrutiny.

---

## Patterns Emerging

**When consilium > Claude alone:**
- High-stakes career decisions where blind spots are costly
- "Stress test this" tasks where adversarial framing surfaces what you don't want to hear
- Anything with an HR/political dimension Claude tends to treat as secondary
- When the question is "what am I missing?" not "what should I do?"
- **After Claude has already made revisions** — second pass on an edited artifact often finds more than the first (edits expose structure)
- Anything involving domain-specific terminology that could be wrong (regulations, technical specs, operator context) — blind consensus catches errors Claude normalises

**When consilium is overkill:**
- Clear factual questions
- Tasks with a single correct answer
- When you've already converged and just need execution

**Recurring pattern: Claude defaults to "more detail = better"**
Council stress-tests whether the detail survives scrutiny. Labelling a metric's methodology is only an improvement if the methodology is valid. Adding a hardware claim is only a strength if you can defend the specs. Claude approves; council audits.

**Round count — 2 is the sweet spot:**
- Round 1 on original: structural findings, highest yield
- Round 2 on edited artifact: edits expose new bones, often finds as much as Round 1
- Round 3+: diminishing returns, more overcorrection noise than signal — only run as deliberate experiment
- Full data: MTR deck experiment (Mar 12 2026) — 3 rounds × $1 = $3 total. Round 1: 4 findings. Round 2: 4 findings. Round 3: 2 real findings in a sea of overcorrection.

**Mode selection:**
- `--deep --xpol` for career/strategic decisions — the xpol critique pass catches where the judge itself is wrong, worth the extra ~$0.15 and ~2 min
- `--council` for bounded decisions (e.g. pick one of four options) — the deliberation converges quickly, xpol adds diminishing returns
- `--quick` for naming, brainstorming, surface perspectives only
