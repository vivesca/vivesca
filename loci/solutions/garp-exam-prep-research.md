# GARP RAI Exam Prep: Evidence-Based Study Guide

**Created:** 2026-03-08
**Exam:** GARP Risk & AI (RAI) Certificate — April 4, 2026 (27 days)
**Format:** 80 MCQ, 4 hours (confirmed: not 100 as initially stated — GARP official page)
**Topic weights:** AI & Risk Overview ~10%, Tools & Techniques ~30%, Risks & Risk Factors ~20%, Responsible & Ethical AI ~20%, Data & AI Model Governance ~20%
**Study budget:** 15-20 min/day via quiz CLI

---

## 1. The Foundational Hierarchy (What the Research Agrees On)

Ranked by effect size (Dunlosky et al. 2013, meta-analytic consensus):

| Strategy | Effectiveness | Evidence |
|---|---|---|
| Practice testing (retrieval) | **High** | g = 0.61 vs all alternatives |
| Distributed/spaced practice | **High** | Robust across 100+ studies |
| Interleaved practice | **Moderate-High** | 50-125% improvement in some studies |
| Elaborative interrogation | Moderate | Ask "why is this true?" |
| Self-explanation | Moderate | Explaining forces gap detection |
| Highlighting/underlining | **Low** | No better than reading alone |
| Re-reading | **Low** | "Relatively economical but ineffective" |
| Summarising | Low-Moderate | Depends heavily on skill level |

**Bottom line:** Your quiz CLI is already the right tool. Practice testing consistently outperforms all passive review methods. The research is unambiguous here.

Sources:
- Dunlosky et al. (2013): https://www.psychologicalscience.org/publications/journals/pspi/learning-techniques.html
- Meta-analysis (g=0.61): https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2018.02412/full

---

## 2. Spaced Repetition — Optimal Intervals Without Software

### Core principle
The spacing effect is one of the most replicated findings in cognitive science. Massed practice (cramming) produces rapid gains that decay fast; spaced practice produces slower apparent gains but vastly superior retention.

### The 10-20% Rule
The optimal inter-session interval (ISI) is approximately **10-20% of the retention interval (RI)**. Since the exam is ~27 days away, this means reviewing material every 2-5 days is optimal for retention at exam date.

### Practical without-software implementation
Use a 3-box index card / folder system (Leitner-style, no app required):

- **Box 1 (Daily):** New material + topics you got wrong
- **Box 2 (Every 2-3 days):** Topics you got right once
- **Box 3 (Weekly):** Topics you've got right consistently

With a quiz CLI, the equivalent is: track which question categories you got wrong, and weight tomorrow's session toward those. You don't need Anki — topic-level tracking is sufficient.

### Key nuance: expanding vs fixed intervals
Expanding intervals (e.g., review after 1 day, then 3 days, then 7 days) are slightly better than fixed intervals for generalization, but fixed intervals beat massed practice by a large margin. Don't over-engineer — even "review weekly" beats cramming.

Sources:
- PMC review of spaced repetition mechanisms: https://pmc.ncbi.nlm.nih.gov/articles/PMC5126970/
- PNAS optimization study: https://www.pnas.org/doi/10.1073/pnas.1815156116
- Kang (2016) spaced repetition review: https://2024.sci-hub.box/4823/fee5d6268a5c6b5cd491c0318c9ecdd6/kang2016.pdf

---

## 3. Active Recall vs. Passive Review

### The data
Students using active recall retain **50-80% of material after one week** vs **10-15% with passive reading alone**. Roediger & Agarwal (2011) found students who took practice tests remembered 50% more than those who re-studied. In some comparisons, one retrieval practice session outperformed four re-study sessions.

### Why effortful retrieval works (Bjork's "desirable difficulties")
The key insight from Robert Bjork's lab: **performance and learning are not the same thing**. Re-reading feels productive because it's easy — you recognise material and mistake that recognition for knowing it. Retrieval feels harder because it is harder, and that difficulty is precisely what drives encoding.

The "generation effect": producing an answer, even an incorrect one, creates stronger memory traces than passively consuming the correct answer.

### Practical implication for your quiz CLI
- **Never look at the answer first**, even when you're unsure. Attempt retrieval, then check.
- If you got a question wrong, re-attempt it from memory 10-15 minutes later in the same session.
- Flag "lucky guesses" separately from genuine knowledge — treat them like wrong answers for scheduling purposes.

Sources:
- Bjork desirable difficulties: https://bjorklab.psych.ucla.edu/wp-content/uploads/sites/13/2016/04/EBjork_RBjork_2011.pdf
- Roediger & Agarwal (2011): https://pdf.retrievalpractice.org/guide/Roediger_Agarwal_etal_2011_JEPA.pdf
- Retrieval practice UCSD guide: https://psychology.ucsd.edu/undergraduate-program/undergraduate-resources/academic-writing-resources/effective-studying/retrieval-practice.html

---

## 4. Interleaving vs. Blocked Practice

### The finding
Interleaving (mixing topics within a session) consistently outperforms blocked practice (doing all questions on topic A, then all on topic B) for **long-term retention and transfer**. The effect size is large: one Nature study found interleaved physics students performed 50% better on delayed tests.

PMC meta-analysis: students using interleaved practice saw **50% improvement on Test 1 and 125% improvement on Test 2** vs blocked practice. The effect is consistent across math, physics, language learning, and category discrimination tasks.

### The catch: it feels harder
Students consistently rate interleaving as more difficult and believe they learned less from it. This is the desirable difficulties effect in action — the subjective difficulty is the mechanism, not a sign something is wrong.

### The exception: exam day
Blocking has a narrow advantage if you need to consolidate a topic for same-day recall. In the final 24-48 hours before the exam, topic-by-topic review may be appropriate.

### Implementation
In your quiz CLI: mix questions across the five RAI topic areas within each session. Avoid studying all governance questions, then all tools questions. Shuffle.

Sources:
- InnerDrive interleaving review: https://www.innerdrive.co.uk/blog/blocking-or-interleaving/
- NPJ Science of Learning (physics): https://www.nature.com/articles/s41539-021-00110-x
- PMC full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC8589969/

---

## 5. The Testing Effect — Core Mechanism

### What it is
The "testing effect" refers to the finding that retrieving information from memory produces stronger long-term retention than re-studying the same information, even when both groups spend equal time. This is sometimes called "retrieval practice" or "test-enhanced learning."

### Effect sizes
- Adesope et al. meta-analysis: mean effect g = 0.61 (medium-large) comparing retrieval practice to all other methods
- MCQ format specifically: shows strong testing effects, comparable to short-answer in most studies; some meta-analyses favour MCQ, others favour short-answer — both are clearly superior to re-reading

### Key moderators
1. **Feedback matters enormously.** Testing with feedback significantly outperforms testing without feedback. After each question, you should know not just whether you were right, but why the correct answer is correct and why the distractors are wrong.
2. **Retrievability window:** The testing effect is strongest for questions you can get right about 50-80% of the time. Too easy (>80%) = not effortful enough. Too hard (<40%) = discouraging and also less effective. Your quiz difficulty should hover in the 60-75% accuracy zone.

Sources:
- Frontiers meta-analysis: https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2018.02412/full
- Roediger et al. classroom study: https://pdf.retrievalpractice.org/guide/Roediger_Agarwal_etal_2011_JEPA.pdf
- ScienceDirect retrieval practice effects: https://www.sciencedirect.com/science/article/pii/S0959475225001434

---

## 6. Session Length and Frequency

### What the research says
Cognitive science does not specify a precise optimal duration but converges on:
- Attention and encoding quality begins degrading after **25-45 minutes** of focused effort
- Multiple short sessions outperform single long sessions for retention
- The **spacing effect dominates** — daily 20-min sessions across 27 days beats four 3-hour sessions on the final weekend

### 15-20 minutes: is it enough?
Yes — with one condition: the session must be high-intensity retrieval practice, not passive review. 15-20 minutes of focused quiz attempts is more valuable than 45 minutes of re-reading notes. The research on "pacing" and session efficiency supports this strongly.

### Frequency recommendation
- **Daily** is optimal given 27 days
- Even if a session is brief (10-12 min), doing it is better than skipping
- Don't extend sessions when tired — quality collapses, and you'll encode with less fidelity

Sources:
- Psychology Today on optimal gap between sessions: https://www.psychologytoday.com/us/blog/memory-medic/201504/what-is-the-optimally-efficient-gap-between-study-sessions
- Session optimization overview: https://medium.com/@alekseyrubtsov/optimizing-study-sessions-short-vs-long-b73fe7039ead
- ERIC increasing retention without increasing time: https://files.eric.ed.gov/fulltext/ED505647.pdf

---

## 7. Sleep and Memory Consolidation

### Core finding
Sleep consolidates newly encoded memories — this is one of the most robust findings in neuroscience. The hippocampus replays new information during slow-wave sleep, transferring it to more stable cortical storage.

### Timing: when to study relative to sleep
- **Declarative memory** (facts, concepts — what the RAI exam tests): consolidation is **enhanced when sleep follows within a few hours of learning**, regardless of time of day
- Studying in the evening and sleeping soon after is marginally better than morning study for factual retention at 24-hour recall
- However, at 7-day recall, the afternoon vs evening study difference largely disappears — both consolidate equally well given regular sleep

### The most important sleep finding
**Sleep deprivation before learning** impairs encoding more severely than sleep deprivation after learning. Prioritise 7-8 hours before any study session. Staying up late to "fit in" more study is counterproductive — the material won't consolidate without adequate sleep anyway.

### Practical implication
- Study in the evening if possible (marginally better for next-day recall of declarative content)
- Maintain consistent sleep schedule — sleep quality matters as much as timing
- Don't sacrifice sleep for extra study time in the final week

Sources:
- PMC: Sleep after learning aids memory recall: https://pmc.ncbi.nlm.nih.gov/articles/PMC10807868/
- PLOS One timing study: https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0040963
- Physiological Reviews comprehensive review: https://journals.physiology.org/doi/full/10.1152/physrev.00054.2024

---

## 8. Metacognition — Knowing What You Don't Know

### The calibration problem
Most learners are systematically overconfident. They mistake fluency (reading smoothly, following an explanation) for knowledge (being able to retrieve and apply). This is the "fluency illusion" — familiarity with material feels like mastery.

### Evidence on calibration
Research on certainty-based marking (CBM) shows that requiring learners to rate their confidence alongside each answer:
- Accurately distinguishes partial knowledge from guessing
- Improves self-assessment accuracy over time
- Encourages deeper cognitive engagement than MCQ alone

### Implementation: confidence-tagging your quiz answers
Before checking the answer, rate each question:
- **C (confident):** You know this solidly
- **U (unsure):** You made your best guess
- **G (guess):** You had no idea

Track the outcomes:
- **C + correct** = genuine knowledge (safe to deprioritise)
- **U + correct** = lucky guess (treat as wrong for scheduling)
- **C + wrong** = dangerous overconfidence (highest priority review)
- **U/G + wrong** = genuine gap (normal priority review)

The most dangerous category is C+wrong. These are topics where your confidence will lead you to under-study precisely what you need most.

### The Dunning-Kruger implication for RAI
AI/ML is a domain where practitioners often have high confidence from surface familiarity. Concepts like "bias," "fairness," "explainability," and "model governance" are often used colloquially in ways that diverge from how GARP operationalises them. Flag any question where you answer confidently based on general AI experience rather than RAI curriculum definitions.

Sources:
- CBM research (PMC): https://pmc.ncbi.nlm.nih.gov/articles/PMC3604960/
- Certainty-based marking physiology: https://journals.physiology.org/doi/full/10.1152/advan.00087.2025
- Metacognition and exam prep (PMC): https://pmc.ncbi.nlm.nih.gov/articles/PMC10956609/

---

## 9. Professional Certification MCQ — Specific Advice

### What's different about certification MCQs
Professional cert MCQ (RAI, FRM, CFA) has distinct features vs university exams:
1. **Distractors are constructed by domain experts** — they target common misconceptions and near-misses, not obvious wrong answers
2. **Definitional precision matters** — the difference between a correct and incorrect answer often rests on one word (e.g., "model risk" vs "model uncertainty")
3. **No partial credit** — knowing 80% of a concept earns the same as knowing 0%
4. **Time pressure is real** — 80 questions in 4 hours = 3 min/question; building fluency through practice matters

### GARP RAI-specific notes (from David Harper analysis)
- Tools & Techniques is the **largest section (~30% = ~24 questions)** — highest ROI for study time
- The exam is relatively new (second cycle) — expect some conceptual questions to be less refined than FRM/CFA
- No coding required; math is at introductory graduate level
- Ethics/governance questions tend toward definitional rather than applied

### MCQ technique (not covered by most study guides)
- **Process of elimination first** — identify definitively wrong answers before choosing
- **Watch for absolute qualifiers** ("always," "never," "only") — usually make an answer wrong in complex domains
- **Two-pass strategy:** answer what you know, flag uncertain ones, return with fresh eyes in pass 2
- **Don't change answers without a reason** — first instinct is typically better unless you've recalled a specific piece of knowledge that changes your assessment

Sources:
- David Harper RAI analysis: https://davidharper.substack.com/p/garps-risk-and-ai-rai-certificate
- GARP official exam format: https://www.garp.org/rai/program-exam

---

## 10. Common Myths to Actively Avoid

| Myth | Reality | Source |
|---|---|---|
| Highlighting = studying | No better than reading; creates false sense of engagement | Dunlosky 2013 |
| Re-reading = reviewing | Familiarity ≠ retrieval; re-reading produces weak retention | Dunlosky 2013 |
| More hours = better outcome | Hours of passive review vs hours of retrieval practice are not equivalent | Roediger & Agarwal 2011 |
| Cramming works | Massed practice produces rapid but rapidly-decaying retention | Spacing effect research |
| Feeling of learning = learning | Fluency illusion: easy reading feels like mastery | Bjork desirable difficulties |
| Hard = bad | Difficulty during retrieval is the mechanism, not a warning sign | Bjork 2011 |
| Tired study still counts | Sleep deprivation impairs encoding severely; better to sleep and study tomorrow | Physiological Reviews 2024 |

Sources:
- APS Dunlosky study techniques review: https://www.psychologicalscience.org/news/releases/which-study-strategies-make-the-grade.html
- Structural Learning testing effect: https://www.structural-learning.com/post/testing-effect-retrieval-practice
- Bjork desirable difficulties theory: https://researchschool.org.uk/durrington/news/bjorks-desirable-difficulties

---

## 11. The 27-Day Action Plan

### Daily protocol (15-20 min)
1. **Open your quiz CLI** — do not review notes first
2. **Set session to mixed/interleaved topics** (don't filter to one subject)
3. **For each question:** attempt first, rate confidence (C/U/G), then check answer + explanation
4. **End of session:** note which categories had C+wrong answers — these get double coverage next session
5. **Evening study if possible** (marginally better for next-day consolidation)

### Weekly structure
- Days 1-5: Interleaved across all 5 topic areas
- Day 6: Focus on weakest topic area (blocked, as a diagnostic)
- Day 7: Rest or very light review (sleep consolidation)

### Topic prioritisation (by exam weight)
1. Tools & Techniques — ~30% of exam, prioritise
2. Risks & Risk Factors, Responsible AI, Data Governance — ~20% each
3. AI & Risk Overview — ~10%, don't over-invest

### The final 48 hours
- Day before exam: light review of high-confidence topics only; do not introduce new material
- Night before: normal sleep schedule, not a late session
- Morning of: brief review of key definitions only (no new questions)
- Avoid: caffeine loading, cramming, skipping meals

### What to avoid building into your routine
- Reviewing notes before quizzing (undermines the retrieval challenge)
- Doing all questions in the same topic order each session
- Checking answers after every question (check in batches of 5-10 for slightly more difficulty)
- Re-reading the GARP curriculum as a substitute for questions

---

## Key Sources (consolidated)

1. Dunlosky et al. (2013) — study technique meta-analysis: https://www.psychologicalscience.org/publications/journals/pspi/learning-techniques.html
2. Bjork & Bjork (2011) — desirable difficulties: https://bjorklab.psych.ucla.edu/wp-content/uploads/sites/13/2016/04/EBjork_RBjork_2011.pdf
3. PMC — spaced repetition mechanisms: https://pmc.ncbi.nlm.nih.gov/articles/PMC5126970/
4. PNAS — spaced repetition optimization: https://www.pnas.org/doi/10.1073/pnas.1815156116
5. Roediger & Agarwal (2011) — testing effect in classrooms: https://pdf.retrievalpractice.org/guide/Roediger_Agarwal_etal_2011_JEPA.pdf
6. Frontiers — testing effect meta-analysis: https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2018.02412/full
7. NPJ Science of Learning — interleaving physics study: https://www.nature.com/articles/s41539-021-00110-x
8. PMC — interleaving vs blocked (full): https://pmc.ncbi.nlm.nih.gov/articles/PMC8589969/
9. InnerDrive — interleaving practical guidance: https://www.innerdrive.co.uk/blog/blocking-or-interleaving/
10. PLOS One — sleep timing study: https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0040963
11. Physiological Reviews — sleep consolidation comprehensive: https://journals.physiology.org/doi/full/10.1152/physrev.00054.2024
12. PMC — confidence-based marking: https://pmc.ncbi.nlm.nih.gov/articles/PMC3604960/
13. GARP official RAI exam page: https://www.garp.org/rai/program-exam
14. David Harper RAI analysis: https://davidharper.substack.com/p/garps-risk-and-ai-rai-certificate
