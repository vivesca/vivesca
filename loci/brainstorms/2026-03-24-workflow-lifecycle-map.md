---
date: 2026-03-24
topic: workflow-lifecycle-map
---

# Vivesca Workflow Lifecycle Map

> Every skill is a cell. Every workflow is a lifecycle. Map them to find the gaps.
>
> This document maps all active skills in `~/skills/` to biological cell lifecycle metaphors,
> identifies workflow chains, and surfaces missing signals, dead feedback loops, and dead ends.
>
> Skills in scope: all active non-archived, non-superpowers, non-compound-engineering skills.
> Archived skills noted where relevant. CLIs referenced but not mapped as skills.

---

## Reading Guide

For each lifecycle:
- **Sense** — what triggers it (input stimulus)
- **Process** — what steps it takes
- **Present** — what it outputs
- **Missing signals** — output that doesn't connect to the next workflow
- **Missing feedback loops** — no learning from output
- **Dead ends** — output goes nowhere

Skill names map to `~/skills/<name>/SKILL.md`.

---

## Lifecycle 1: Cadence Stack — Circadian/Ultradian Rhythm

*Like a cell's clock machinery — entrainment to external signals, phased expression across timescales.*

**Cells:** `entrainment` → `arousal` → `ultradian` → `interphase` → `sorting` → `involution` → `ecdysis` → `mitosis` → `meiosis`

### Sense

| Cell | Trigger |
|------|---------|
| entrainment | Morning (manual), "gm", "weather", "how did I sleep" |
| arousal | Manual, morning queue check |
| ultradian | Any-time: "what now", "what should I do", "priority check" |
| interphase | "leaving office", "on the bus", "going home", "end of day" |
| sorting | Called by interphase (Step 1) |
| involution | ~10pm wind-down, Due reminder |
| ecdysis | Sunday evening, "weekly review", "plan the week" |
| mitosis | First Sunday of month, "monthly review" |
| meiosis | First Saturday of March/June/Sept/Dec, "quarterly review" |

### Process

- **entrainment**: zeitgeber weather + sopor sleep score + overnight health/skill-flywheel files → 60-second brief
- **arousal**: overnight-gather brief → NEEDS_ATTENTION lines + kinesin task results
- **ultradian**: ultradian-gather → time/calendar/NOW/TODO/job alerts → time-aware routing (commute / pre-meeting / free block / EOD)
- **interphase**: gather → inbox triage (sorts) → messages → brain dump → what shipped → tomorrow prep → daily note close → NOW.md sync
- **sorting**: dual Gmail queries → categorize → drill threads → filter senders → batch archive
- **involution**: tomorrow calendar → scan NOW.md → brain dump → overnight task proposals → screens-off gate
- **ecdysis**: weekly-gather → plan next week (Terry picks 3 priorities) → backward glance → job alerts → TODO prune → garden cull → weekly note
- **mitosis**: 4 parallel auditors (hepatocyte, osteocyte, microglia, dendritic-cell) + maintenance → cross-domain synthesis → monthly plan → Praxis.md update
- **meiosis**: direction audit → career trajectory → financial health → investment review → quarterly note

### Present

| Cell | Output |
|------|--------|
| entrainment | 60s brief (weather + sleep + system health) |
| arousal | NEEDS_ATTENTION items + task results surfaced |
| ultradian | Paragraph with time context + sharpest next action |
| interphase | Daily note "Interphase" section + NOW.md updated + Email Threads Tracker |
| sorting | Triaged inbox + Email Threads Tracker updated |
| involution | Daily note "Evening brain dump" section |
| ecdysis | Weekly note (~/code/vivesca-terry/chromatin/Weekly/YYYY-Www.md) |
| mitosis | Monthly Review note (~/code/vivesca-terry/chromatin/Monthly Review - YYYY-MM.md) + Praxis.md updated |
| meiosis | Quarterly note (~/code/vivesca-terry/chromatin/Quarterly/YYYY-QX.md) + Life OS updated |

### Missing Signals

1. **involution → translocation**: overnight task proposals are stated in chat ("Want me to queue an agent?") but there is NO automatic path to `translocation`/kinesin. The user must manually invoke kinesin or never queue them at all.
2. **arousal → ultradian**: arousal surfaces NEEDS_ATTENTION items at morning check, but no automatic routing to ultradian for follow-up prioritization during the day.
3. **entrainment → arousal**: both are morning skills but not chained — user invokes them independently. If entrainment finds system warnings, it doesn't cascade into arousal for deeper triage.
4. **ecdysis job alerts → adhesion**: ecdysis surfaces unchecked job alert roles but does not route them to `/adhesion` — just mentions them.
5. **meiosis → ecdysis**: quarterly direction update (Life OS) doesn't automatically propagate into the weekly planning cycle. Weekly focus picks could be inconsistent with quarterly priorities.
6. **interphase "what shipped" → expression sparks**: daily ship summary dies in the daily note; no mechanism to route it into `~/code/vivesca-terry/chromatin/Consulting/_sparks.md` for weekly forging.

### Missing Feedback Loops

1. **Cadence performance**: no review of "did the weekly plan match what happened?" — ecdysis has no retrospective on *last* week's 3 priorities, only a "quick glance back."
2. **Mitosis auditor quality**: the 4 auditors (hepatocyte, osteocyte, microglia, dendritic-cell) are agent-type skills, not SKILL.md files — their outputs are synthesized but their individual accuracy is never validated.
3. **Monthly plan execution**: mitosis writes a monthly plan and updates Praxis.md, but there is no check at next mitosis run on whether last month's priorities were achieved.
4. **NOW.md staleness**: ultradian reads NOW.md but there's no automatic trigger to update it when items change state outside of interphase.

### Dead Ends

- `involution` overnight task proposals → die in chat unless manually queued via `translocation`
- `meiosis` quarterly note → written and archived, never referenced by any other skill unless manually
- `mitosis` monthly plan notes → same static archive pattern; no downstream signal

---

## Lifecycle 2: Content Pipeline — Signal Propagation

*Like vesicle secretion: compress the cargo (exocytosis), release at the membrane (budding), signal the receptor (secretion).*

**Cells:** `exocytosis` → `budding` → `secretion`

### Sense

| Cell | Trigger |
|------|---------|
| exocytosis | Sharp standalone claim surfaces in conversation; also downstream of expression |
| budding | Manual: "garden post", "publish", "new post"; or exocytosis fires → budding expands |
| secretion | budding published + tweet has been posted and observed |

### Process

- **exocytosis**: compress insight to 280 chars → `bird tweet "text"` → one attempt only
- **budding**: `publish new "Title"` → scaffold → write prose → quality gate (skip for standard posts) → `publish publish <slug> --push`
- **secretion**: confirm tweet existed → rewrite for LinkedIn audience (longer, blindspot-aware) → `agoras` CLI

### Present

| Cell | Output |
|------|--------|
| exocytosis | Tweet posted on X (@zkMingLi) |
| budding | Published post on terryli.hm garden |
| secretion | LinkedIn post |

### Missing Signals

1. **exocytosis → engagement feedback**: "observe — did anyone push back?" exists as a design instruction, but there is NO mechanism to capture tweet reaction/engagement back into the system. The signal is stated but unimplemented.
2. **secretion → expression**: LinkedIn performance is invisible — nothing feeds what resonated back into `expression` sparks or `chemotaxis` pattern scans.
3. **budding → exocytosis gate**: the exocytosis skill says "if it needs explaining → garden it, don't tweet it." But budding posts don't automatically surface a tweet opportunity back.

### Missing Feedback Loops

1. **Content resonance**: no mechanism to know whether a garden post, tweet, or LinkedIn post generated a conversation, inquiry, or opportunity. The full pipeline (tweet → garden → LinkedIn) is fire-and-forget.
2. **Content compounding**: expression produces `maturity: draft` assets. There's no review cycle to promote them to `maturity: reviewed` or track which drafts became published posts.
3. **Funnel tracking**: expression tracks a "funnel metric" (Sources → Sparks → Assets → Promoted → Used), but "Used" is manually inferred from daily notes — not a real feedback signal.

### Dead Ends

- `secretion` (LinkedIn post) is the terminal step — no capture of response
- `expression` weekly report asks "Did you use anything from last week's batch?" but this question has no mechanical answer path; it requires Terry to remember and respond

---

## Lifecycle 3: Build Pipeline — Molecular Assembly

*Like transcription → translation → protein folding: design → plan → execute → fold into final shape.*

**Cells:** `nucleation` → `transcription` → `translation` → `folding` → `modification`

### Sense

| Cell | Trigger |
|------|---------|
| nucleation | User says "build X", "implement X", "add a feature" |
| transcription | Shape unclear; "let's build", "I want to add", "what if we..." |
| translation | Design approved; "plan this", "break this down" |
| folding | Plan exists; "build", "implement", "do it" |
| modification | Artifact needs multi-model refinement; "refine", "polish" |

### Process

- **nucleation**: solutions KB check → scope check → weight class → route to transcription/translation/in-session/delegation
- **transcription**: context scan → pressure test → clarifying questions (one at a time) → approaches → design → capture brainstorm doc
- **translation**: context scan → plan (file map + TDD tasks) → write to ~/docs/plans/
- **folding**: pre-flight → execute via opifex → verify (hard gate) → review (tiered depth) → ship → companion skill
- **modification**: parallel independent review (Gemini/Codex/Claude) → synthesize consensus → apply edits → validate → present

### Present

| Cell | Output |
|------|--------|
| nucleation | Routing decision (weight class) |
| transcription | Design doc (~/docs/brainstorms/YYYY-MM-DD-<topic>.md) |
| translation | Plan file (~/docs/plans/YYYY-MM-DD-<topic>-plan.md) |
| folding | Working code + PR + tool-index entry + companion SKILL.md |
| modification | Refined artifact + diff + score summary |

### Missing Signals

1. **translation → folding**: plan is written and path is stated, but no automatic handoff — user must manually invoke `/folding`.
2. **folding → modification**: if the shipped artifact is a document/spec/CV (not code), the natural next step is modification, but no signal connects them.
3. **folding companion skill**: "create SKILL.md in this session" is stated as a recommendation, not a hard gate. No verification that it happened.
4. **opifex execution logs → planning quality**: opifex logs every execution (`~/.local/share/opifex/log.jsonl`) with success rates, fallbacks, and failures, but **no skill reads these logs** to improve transcription/translation quality over time.

### Missing Feedback Loops

1. **Plan drift**: no comparison between the original translation plan and what folding actually executed. Changes made during execution don't flow back to update the plan.
2. **Review severity tracking**: folding generates Blocker/Major/Minor severity tags, but these aren't tracked across projects to identify which classes of errors recur.
3. **Solutions KB population**: folding/nucleation say "capture non-obvious solves to ~/docs/solutions/" — but this is conditional on "non-obvious," an unmonitored heuristic.

### Dead Ends

- `~/docs/brainstorms/` design docs — written by transcription, read by translation, then static
- `~/docs/plans/` plan files — executed by folding, then static archive
- `opifex log --stats` exists but no skill reads it for improvement signals

---

## Lifecycle 4: Weekly Intelligence — IP Synthesis

*Like gene expression: environmental sparks → transcription into consulting IP → translation into publishable form.*

**Cells:** `expression` → `budding` (content output), `chemotaxis` (input), `chemoreception` (supplemental input)

### Sense

| Cell | Trigger |
|------|---------|
| expression | Weekly ("forge", "weekly forge", "run the forge") |
| chemotaxis | Monthly (part of mitosis) or ad-hoc; "peer scan", "landscape scan" |
| chemoreception | On-demand: stale transduction, pre-meeting, specific development |

### Process

- **expression**: verify sparks/Thalamus exist → Opus planning pass → 6 parallel Sonnet workers (content, policy, architecture, use-case, experiment, intelligence) → synthesis → cleanup
- **chemotaxis**: scope scan targets → parallel researcher subagents → synthesize patterns → classify (stack/capco/governance/universal) → write Specula vault note → create action items
- **chemoreception**: read Transduction index → if stale/meeting: live gather → governance translation pass → meeting routing

### Present

| Cell | Output |
|------|--------|
| expression | Consulting IP assets + weekly report + LinkedIn seeds in _sparks.md |
| chemotaxis | Specula/YYYY-MM Peer Scan.md + classified action items |
| chemoreception | Transduction snapshot update + governance gap rows + meeting prep bullets |

### Missing Signals

1. **chemotaxis → expression**: chemotaxis patterns classified as `stack` go to "Skill update or rector task" — but no mechanism propagates these patterns INTO expression's spark intake. The connection is manual.
2. **expression → opsonization**: expression synthesis creates cross-pollination maps and talk seeds, but no signal fires to opsonization to say "new IP available for meeting prep."
3. **chemoreception → expression**: chemoreception adds governance gap rows to the regulatory gap assessment, but doesn't generate a spark in `_sparks.md` for the expression forge to pick up.
4. **expression intelligence worker → ecdysis**: the weekly intelligence brief in `~/code/vivesca-terry/chromatin/Consulting/_weekly/` is never referenced in weekly planning (ecdysis) — two parallel views of "what happened this week" with no connection.

### Missing Feedback Loops

1. **IP utilization**: was any consulting IP asset from expression actually used in a client conversation? No skill tracks this. The "Used: N" field in the funnel metric is inferred manually.
2. **Chemotaxis pattern decay**: patterns identified in a peer scan don't have a freshness date. No review mechanism flags stale patterns that were never actioned.
3. **Spark quality**: expression workers process sparks, but there's no signal back to the spark collection mechanism if spark yield drops. The daily spark agent runs via kinesin, but its quality isn't monitored.

### Dead Ends

- `~/code/vivesca-terry/chromatin/Consulting/_weekly/YYYY-WNN.md` intelligence briefs — filed and forgotten unless Terry reads them manually
- `Specula/YYYY-MM Peer Scan.md` peer scan outputs — accumulate but no systematic review
- expression's "talk seeds" (combinations of experiment + use case + insight) — identified but no downstream path to actually submit a conference talk proposal

---

## Lifecycle 5: Intake — Content Classification

*Like phagocytosis: foreign body detected → engulf → classify → digest → store useful components.*

**Cells:** `phagocytosis` → routes to `adhesion` (job URLs) or vault note (everything else)

### Sense

| Cell | Trigger |
|------|---------|
| phagocytosis | User shares URL or pasted content |
| adhesion | LinkedIn job URL (routed from phagocytosis), or "evaluate this role" |

### Process

- **phagocytosis**: classify URL pattern → fetch → route by content type → skip logic → handler (article/repo/profile/video/company) → vault note + telemetry
- **adhesion**: navigate JD → check duplicates → load context → analyze fit dimensions → factor pipeline health → check red flags → recommendation → Judge review → vault note → job tracking → optional application

### Present

| Cell | Output |
|------|--------|
| phagocytosis | Structured vault note + telemetry row in Analyze Telemetry.md |
| adhesion | Role vault note + Job Hunting tracker update + optional application start |

### Missing Signals

1. **phagocytosis → expression sparks**: articles and insights saved to vault could directly seed `~/code/vivesca-terry/chromatin/Consulting/_sparks.md`, but no mechanism routes them there. The connection is manual at best.
2. **adhesion APPLY → polymerization**: when adhesion recommends APPLY, it asks if user wants to proceed, but doesn't automatically create a Praxis.md follow-up task for application steps.
3. **adhesion anti-signals**: red flag patterns come from `[[Job Hunting]] → Anti-Signals`, but there is no mechanism to UPDATE anti-signals from adhesion outcomes (the debrief skill that did this is archived).

### Missing Feedback Loops

1. **Phagocytosis telemetry**: Analyze Telemetry.md accumulates rows but no skill reads it. Telemetry is write-only — no analysis of classification accuracy or skip/note ratio over time.
2. **Adhesion pattern learning**: passed-on roles accumulate in Job Hunting "Passed On" section with one-line reasons, but no skill performs pattern analysis to identify systematic mismatches.
3. **Application outcome tracking**: adhesion creates vault notes for roles and adds them to job tracking, but no skill reviews outcomes (did we get the interview? did we get the offer?) to close the loop.

### Dead Ends

- `Analyze Telemetry.md` — write-only archive, never read by any skill
- `Job Hunting "Passed On"` section — accumulates without pattern analysis
- Role vault notes after outcome — filing cabinet without longitudinal review

---

## Lifecycle 6: Coaching — Capability Development

*Like cell differentiation: each session specializes capacity in a different direction — meeting prep, physical, cognitive.*

**Cells:** `restriction-point` → `differentiation`, `opsonization`, `autophagy`

### Sense

| Cell | Trigger |
|------|---------|
| restriction-point | "check readiness", or called before differentiation |
| differentiation | Going to gym; manual invocation |
| opsonization | "meeting prep", "prep for meeting", "prep for coffee" |
| autophagy | "/autophagy", "growth mode", "coach me on this" |

### Process

- **restriction-point**: sopor today + vault health notes → threshold check (<70/70-75/>75) → one-sentence recommendation
- **differentiation**: check restriction-point → find latest gym log → prescribe exercises → track sets + timestamps + rest → progress check → write session log
- **opsonization**: gather meeting context → generate MCQ (one at a time) → coach on best answer → session summary + key talking points → optional save
- **autophagy**: enter "Terry forms view first" mode → for each question: ask what Terry's read is → wait → challenge/extend/correct → no leading, no filling

### Present

| Cell | Output |
|------|--------|
| restriction-point | One sentence: readiness score + workout recommendation |
| differentiation | Gym log file (~/code/vivesca-terry/chromatin/Health/Gym Log - YYYY-MM-DD.md) |
| opsonization | Session summary + key talking points; optional Meeting Prep note |
| autophagy | Behavioral mode only — no persistent output |

### Missing Signals

1. **restriction-point → differentiation gate**: restriction-point outputs one sentence, but this is NOT a hard gate for differentiation — it is advisory. Differentiation says "run check-exercise-readiness skill" and "honour thresholds" but there's no enforcement mechanism.
2. **differentiation → restriction-point**: gym log captures working weights and "notes for next session," but restriction-point doesn't read these. Next readiness check starts from scratch (sopor only).
3. **opsonization → daily note**: meeting prep sessions have no automatic notation in the daily note ("prepped for X meeting"). The outcome is isolated.
4. **autophagy → cytokinesis**: autophagy sessions explicitly produce no output. The design says "if latter, session failed" — but there's no signal to cytokinesis to flag this.

### Missing Feedback Loops

1. **Gym progression analysis**: gym logs accumulate in ~/code/vivesca-terry/chromatin/Health/ but no skill reads them periodically for plateau detection or progression analysis. Differentiation reads the LATEST log, not trends.
2. **Post-meeting debrief**: opsonization prepares for meetings but there is no structured post-meeting capture skill. What questions came up? What landed? What missed? This was handled by the archived `debrief` skill.
3. **Autophagy session quality**: the skill has a self-test ("did Terry produce something or consume?") but no tracking mechanism. Growth mode sessions can fail without detection.
4. **Meeting prep accuracy**: opsonization's MCQs are scenario-based but there's no comparison between what was drilled and what actually came up in the meeting.

### Dead Ends

- `autophagy` sessions: growth mode insights die in session unless cytokinesis captures them (which requires manual invocation)
- `Meeting Prep - [Context].md` notes: optional save, often not written; no reference back to outcome
- `differentiation` gym logs after being written: longitudinal analysis never happens unless Terry manually reads them

---

## Lifecycle 7: Async Work — Background Processing

*Like endocytotic vesicles: package the work, detach from current activity, process independently, return results.*

**Cells:** `polarization` → (kinesin/overnight) → `arousal`; `translocation` (dispatcher)

### Sense

| Cell | Trigger |
|------|---------|
| polarization | "burn tokens", "overnight", "vigilia", "going to sleep" |
| translocation | Dispatching any specific background job; involution proposals |
| arousal | Morning: "arousal", "overnight results", "queue status", "what ran" |

### Process

- **polarization**: pre-flight consumption check → guard on → north stars filter → shape filter → division of labour filter → brainstorm sub-goals → dispatch waves (background, bypassPermissions) → route outputs (self-sufficient vs needs review) → copia report
- **translocation**: kinesin CLI wrapper — list/run/cancel/results. Adds tasks to opencode-queue.yaml and LaunchAgent plists.
- **arousal**: overnight-gather brief → NEEDS_ATTENTION flagging + skill-flywheel misses + kinesin run summaries

### Present

| Cell | Output |
|------|--------|
| polarization | Copia report (~/code/vivesca-terry/chromatin/Copia Reports/YYYY-MM-DD.md) + Praxis.md review items + self-sufficient outputs archived |
| translocation | Background job dispatched; results in ~/.cache/kinesin-runs/ |
| arousal | Morning brief with NEEDS_ATTENTION items surfaced |

### Missing Signals

1. **involution → translocation (THE KEY GAP)**: involution explicitly proposes overnight agent tasks ("Want me to queue an agent to research X tonight?"), but `translocation`/kinesin is NEVER invoked within involution. The proposal dies in chat. There is no structured handoff.
2. **arousal → ultradian**: NEEDS_ATTENTION items from arousal don't automatically feed into the ultradian situational snapshot later in the day.
3. **polarization quality → expression**: copia reports track what was produced, but don't automatically seed `~/code/vivesca-terry/chromatin/Consulting/_sparks.md` with produced IP. Two parallel production pipelines with no connection.

### Missing Feedback Loops

1. **Polarization output quality**: copia reports show what was produced, but no review of: "was this output actually used by Terry?" The flywheel could be spinning and producing unread IP.
2. **Kinesin task accuracy**: kinesin tasks run on a schedule, but no skill reviews whether scheduled tasks are still relevant. Tasks added months ago may be stale.
3. **Overnight ROI**: no mechanism to calculate: "for every polarization run, N items were produced, M were reviewed by Terry, K were promoted." The flywheel has no measurement.

### Dead Ends

- `~/code/vivesca-terry/chromatin/Copia Reports/YYYY-MM-DD.md` — filed and not reviewed by any other skill
- Kinesin results in `~/.cache/kinesin-runs/` — ephemeral unless `output_dir` is set; arousal surfaces them once, then they're gone
- `~/tmp/polarization-session.md` — archived per-run but no longitudinal trace

---

## Lifecycle 8: System Intelligence — Self-Modification

*Like autophagy of the cell itself: scan existing components, identify what to recycle, rebuild better.*

**Cells:** `cytometry`, `morphogenesis`, `endocytosis`

### Sense

| Cell | Trigger |
|------|---------|
| cytometry | "what needs me?", "autonomy audit", "city audit", after adding new subsystems |
| morphogenesis | "mine the name", "rename and inspire", new bio name or existing bio name not mined |
| endocytosis | Topic identified as worth mining; inconsistent model depth detected |

### Process

- **cytometry**: for each subsystem in anatomy: sense (how it activates) → classify (self-governing/needs mayor/gated) → measure ratio → diagnose gaps → act (pick highest-leverage gap and close it)
- **morphogenesis**: name → study (biology, 3-5 properties) → compare (which properties does implementation have/lack) → design (rank missing properties) → build (highest-value gap now)
- **endocytosis**: probe → push past surface → find bones → distill to reference skill → wire to existing skills → optional garden post; three tiers (single-model / quorum refinement / field validation)

### Present

| Cell | Output |
|------|--------|
| cytometry | Cytometry report (vault) + one gap implemented |
| morphogenesis | Design insight + optionally implemented gap |
| endocytosis | Reference skill file + wiring to existing skills + optional garden post |

### Missing Signals

1. **New skill creation → cytometry**: when `nucleation`/`folding` creates a new skill (SKILL.md), there is no signal to cytometry to re-run the autonomy audit. The population count changes but no audit fires.
2. **cytometry → morphogenesis**: cytometry identifies "needs a mayor" subsystems, but the natural next step (mine the bio name for that subsystem to find design insights) is never triggered.
3. **endocytosis wiring → skill updates**: the wiring checklist step ("add cross-references to skills that would benefit") is aspirational — there's no verification that wiring actually happened.

### Missing Feedback Loops

1. **Cytometry trend**: individual cytometry reports exist in vault but no skill does trend analysis (are we trending toward more self-governing? Less?). Each report is a snapshot without comparison to prior state.
2. **Endocytosis decay tracking**: `memory/decay-tracker.md` tracks when mined skills are consulted, but this file is not automatically maintained — it requires manual log entries per the skill definition.
3. **Morphogenesis outcomes**: no record of which implementations resulted from morphogenesis mining vs. were noted and deferred. "Build now, not next time" is stated but not enforced or tracked.

### Dead Ends

- Cytometry "highest-leverage gap" fix: stated as mandatory ("Audit and fix"), but the fix doesn't always ship
- Endocytosis mining queue items marked [x] but field validation (Tier 3) is passive — tracked in decay-tracker which isn't reviewed
- Morphogenesis "noted for future" items: seen in the skill's examples table; no queue

---

## Lifecycle 9: Decision Architecture — Judgment Crystallization

*Like synaptic strengthening: repeat firing of the right decision patterns makes future decisions faster and more reliable.*

**Cells:** `quorum` → `transcription-factor`, supported by `proofreading`

### Sense

| Cell | Trigger |
|------|---------|
| quorum | Trade-offs, strategy, naming, domain judgment calls |
| proofreading | "stress-test this", "find counterarguments" |
| transcription-factor | "I need to decide", "weighing options", or after quorum deliberation |

### Process

- **quorum**: classify difficulty (Opus) → propose mode → confirm → run council (backgrounded) → parse [DECISION] → synthesize for user
- **proofreading**: take idea → find strongest counterarguments (not obvious ones) → failure modes → hidden assumptions → verdict
- **transcription-factor**: route check (measurable → evaluation-theory? uncertain → quorum? committed → proceed) → bouncer check (past decisions on same topic) → structure decision → compliance check → write decision note

### Present

| Cell | Output |
|------|--------|
| quorum | Council output in ~/code/vivesca-terry/chromatin/Councils/ + decision recommendation |
| proofreading | Top 3 challenges ranked by severity (chat only) |
| transcription-factor | Decision note (~/code/vivesca-terry/chromatin/decisions/YYYY-MM-DD-<slug>.md) |

### Missing Signals

1. **quorum → transcription-factor**: quorum produces a council recommendation but does NOT automatically route to transcription-factor for capture. The user must remember to log the decision separately.
2. **proofreading → modification**: proofreading surfaces counterarguments to a plan/idea, but no signal connects to modification to apply the feedback as refinement passes.
3. **transcription-factor → quorum escalation**: transcription-factor's compliance check has a domain gate (client data), but there's no automatic escalation trigger for high-stakes or irreversible decisions. The quorum route is offered only as an optional offer.

### Missing Feedback Loops

1. **Decision outcomes**: transcription-factor's bouncer pattern detects recurrence (returning to a decided topic = implicit failure signal), but there's no explicit "how did this turn out?" review. Outcomes are inferred from recurrence, not captured.
2. **Council performance**: quorum outputs accumulate in ~/code/vivesca-terry/chromatin/Councils/ but no skill reviews them for quality, consistency, or whether the recommended decisions turned out to be correct.
3. **Proofreading persistence**: proofreading output dies in chat unless cytokinesis captures it. The strongest counterarguments to a plan have no persistent home.

### Dead Ends

- `proofreading` output → chat only, dies with session
- `~/code/vivesca-terry/chromatin/Councils/` → accumulates without longitudinal review
- `~/code/vivesca-terry/chromatin/decisions/` → reviewed only via transcription-factor bouncer, not periodically

---

## Lifecycle 10: Knowledge Management — Vault Metabolism

*Like cellular metabolism: intake → process → store → retrieve → recycle.*

**Cells:** `phagocytosis` (intake), `endocytosis` (extract), `cytokinesis` (consolidate), `polymerization` (manage tasks)

### Sense

| Cell | Trigger |
|------|---------|
| phagocytosis | External content shared |
| endocytosis | LLM knowledge identified as worth extracting |
| cytokinesis | End of session, gear-shift checkpoint |
| polymerization | "todo", "add todo", "check todo", "overdue" |

### Process

- **phagocytosis**: classify → route → fetch → handler → vault note + telemetry
- **endocytosis**: probe model → distill to heuristics → write reference skill → wire → optional publish
- **cytokinesis**: ask Terry + run gather tool → merge findings → route to memory/skills/Praxis/publish/solutions → housekeeping (commit + archive + session log + Tonus update)
- **polymerization**: todo-cli commands → intake gate → moneo alarms → archive completed

### Present

| Cell | Output |
|------|--------|
| phagocytosis | Vault note + telemetry row |
| endocytosis | Reference skill file |
| cytokinesis | Memory files + skill updates + Praxis items + tweets/posts + solution docs + Tonus.md |
| polymerization | Praxis.md entries + Praxis Archive.md |

### Missing Signals

1. **cytokinesis → phagocytosis**: cytokinesis captures insights and routes them to skills/memory, but there's no signal back to phagocytosis to improve its classification or skip logic.
2. **polymerization completion → cytokinesis**: when tasks are archived in Praxis Archive.md, no signal fires for cytokinesis to review what was completed and capture any learnings.
3. **Tonus.md** is updated by cytokinesis but no skill reads it. It's a write-only state file.

### Missing Feedback Loops

1. **Cytokinesis "residual" metric**: the audit signal (filed=N) tracks how many items were missed during the session and captured at close. This number is stated but never analyzed for trends. Is it getting smaller (better continuous capture) or staying constant?
2. **MEMORY.md demotions**: cytokinesis says "MEMORY.md ≥145 lines → demote lowest-recurrence entry," but there's no tracking of recurrence per entry. The demotions are judgment calls, not data-driven.
3. **Praxis Archive analysis**: completed tasks accumulate in Praxis Archive.md. No skill reviews them for: What got done fastest? What lingered longest? What was added but never done?

### Dead Ends

- `Tonus.md` — updated by cytokinesis, read by nobody
- `Praxis Archive.md` — completed tasks filed and never reviewed
- `~/code/vivesca-terry/chromatin/Meta/Analyze Telemetry.md` (phagocytosis) — write-only

---

## Lifecycle 11: Financial/Career Monitoring — Metabolic Homeostasis

*Like the liver: continuous monitoring of resource levels, flagging imbalances, signaling action.*

**Cells:** `homeostasis`, `adhesion`, supplemented by `restriction-point` (health), `chemoreception` (career)

### Sense

| Cell | Trigger |
|------|---------|
| homeostasis | Any-time, invoked when financial concern arises |
| adhesion | LinkedIn job URL or "evaluate this role" |

### Process

- **homeostasis**: grep vault for financial notes → cross-reference Praxis.md → flag overdue/upcoming (14-day horizon) → sort by urgency
- **adhesion**: full multi-step JD analysis with deduplication, fit scoring, pipeline health factoring, red flag checking, Judge review, vault note, tracking, optional application

### Present

| Cell | Output |
|------|--------|
| homeostasis | Prioritized list of financial action items |
| adhesion | Role vault note + job tracking + possibly application initiated |

### Missing Signals

1. **homeostasis → meiosis**: homeostasis checks financial milestones, but doesn't automatically trigger or inform meiosis's financial review section. Two separate views of finances with no connection.
2. **homeostasis scheduling**: homeostasis has no autonomous trigger — it only fires when Terry explicitly invokes it. Financial deadlines can slip unnoticed between invocations.
3. **adhesion → homeostasis**: when adhesion recommends APPLY and compensation is known, there's no signal to homeostasis to track the opportunity against financial constraints or targets.

### Missing Feedback Loops

1. **Application outcome tracking**: adhesion creates vault notes for roles and updates job tracking. But what happened to the application? No skill closes the loop on interview/offer/rejection outcomes.
2. **Pipeline health self-correction**: adhesion factors "pipeline health" (healthy = 5+ active, thin = <5) into recommendations, but there's no mechanism to recalculate pipeline health as applications progress.
3. **Anti-signal learning**: adhesion's red flag check reads anti-signals from Job Hunting tracker, but there's no mechanism to ADD to anti-signals from adhesion outcomes. The debrief skill (archived) did this.

### Dead Ends

- Role vault notes after outcome — static archive without outcome annotation
- `Job Hunting.md` "Passed On" section — reasons logged but never analyzed for patterns

---

## Cross-Lifecycle Analysis: System-Wide Gaps

### 1. The Involution→Translocation Gap (CRITICAL)

`involution` proposes overnight tasks. `translocation` dispatches them. They never connect. The proposed queue items live in chat and die there. This is the single largest handoff gap in the system — it occurs every evening.

**What's needed:** Either involution invokes `translocation`/kinesin directly, or a structured handoff protocol exists (e.g., involution writes proposed tasks to a staging file that translocation reads on next invocation).

### 2. The Sparks Starvation Problem

`expression` runs weekly and consumes `~/code/vivesca-terry/chromatin/Consulting/_sparks.md`. The sparks are supposed to be populated by a daily kinesin agent. But:
- `phagocytosis` vault notes don't route to sparks
- `interphase` "what shipped" doesn't route to sparks
- `chemotaxis` patterns don't route to sparks
- `chemoreception` governance updates don't route to sparks

Expression is a centralized weekly processing node with only one automated input channel (the kinesin spark agent). All other pipelines are potential spark sources that currently dead-end.

### 3. The Post-Meeting Debrief Gap

`opsonization` prepares for meetings thoroughly. Nothing captures what happened AFTER the meeting. The archived `debrief` skill covered this. Its absence means:
- Anti-signals from adhesion can't be updated
- Meeting prep accuracy can't be measured
- Key talking points that landed can't be promoted to Core Story Bank
- Patterns across meetings are invisible

### 4. The Cytokinesis Dependency

`autophagy`, `proofreading`, and growth-mode conversations all produce valuable insights with no persistence mechanism. Everything depends on `cytokinesis` running at session end to capture them. Cytokinesis is opt-in and ad-hoc. If Terry closes a session without running it, all unwritten insights are lost.

**What's needed:** Either a stronger continuous capture habit, or an automated end-of-session hook that fires cytokinesis automatically.

### 5. The Feedback Void

The system produces extensively but measures almost nothing:
- Content performance (tweets, garden, LinkedIn) — no metrics
- Consulting IP utilization (expression output) — manually inferred
- Decision quality (transcription-factor outcomes) — inferred from recurrence
- Coaching effectiveness (opsonization/autophagy) — zero measurement
- Polarization ROI (overnight production) — tracked in copia reports nobody reads

Without feedback, the system can improve through morphogenesis/cytometry/endocytosis (structural audits), but not through use-pattern learning.

---

## Skill Inventory Summary

| Skill | Lifecycle(s) | Role |
|-------|-------------|------|
| adhesion | Intake, Career | Job evaluation terminal |
| arousal | Async Work, Cadence | Morning result retrieval |
| autophagy | Coaching | Growth mode (no output) |
| budding | Content Pipeline, Intelligence | Garden publishing |
| chemoreception | Intelligence | On-demand AI briefing |
| chemotaxis | Intelligence, Cadence | Peer pattern scanning |
| cytokinesis | Knowledge Management | Session consolidation |
| cytometry | System Intelligence | Autonomy audit |
| differentiation | Coaching, Health | Gym session coaching |
| ecdysis | Cadence | Weekly planning |
| endocytosis | System Intelligence, Knowledge | LLM knowledge extraction |
| entrainment | Cadence | Morning brief |
| exocytosis | Content Pipeline | Tweet compression+post |
| expression | Intelligence, Content | Weekly IP forge |
| folding | Build Pipeline | Plan execution |
| homeostasis | Financial/Career | Financial monitoring |
| interphase | Evening Routine, Cadence | Evening triage |
| involution | Evening Routine, Cadence | Evening wind-down |
| meiosis | Cadence | Quarterly review |
| mitosis | Cadence | Monthly review |
| modification | Build Pipeline | Multi-model refinement |
| morphogenesis | System Intelligence | Bio-name design mining |
| nucleation | Build Pipeline | Dev workflow on-ramp |
| opsonization | Coaching, Career | Meeting prep drilling |
| phagocytosis | Intake, Knowledge | Content classification |
| polarization | Async Work | Overnight agent flywheel |
| polymerization | Knowledge Management | Todo management |
| proofreading | Decision Architecture | Adversarial stress-test |
| quorum | Decision Architecture | Multi-model deliberation |
| replication | Build Pipeline (research) | Agent research org |
| restriction-point | Coaching, Health | Readiness check |
| secretion | Content Pipeline | LinkedIn publishing |
| sorting | Evening Routine | Email triage |
| transcription | Build Pipeline | Design dialogue |
| transcription-factor | Decision Architecture | Decision capture |
| translation | Build Pipeline | Plan writing |
| translocation | Async Work | Background job dispatch |
| ultradian | Cadence | Any-time situational snap |

---

## Priority Gap Matrix

| Gap | Lifecycle | Impact | Effort to Fix |
|-----|-----------|--------|---------------|
| involution → translocation handoff | Evening/Async | High (nightly) | Low (one hook) |
| sparks starvation (multiple → expression) | Intelligence | High (weekly) | Medium (routing rules) |
| post-meeting debrief missing | Coaching | High (ongoing) | Medium (restore debrief) |
| cytokinesis opt-in (autophagy/proofreading die) | Knowledge | Medium (session) | Medium (end-session hook) |
| phagocytosis telemetry never read | Intake | Low | Low (cron + analysis) |
| content pipeline feedback void | Content | Medium | High (external signal needed) |
| homeostasis no autonomous trigger | Financial | Medium | Low (kinesin schedule) |
| decision outcome tracking | Decision | Medium | Medium (review cadence) |
| gym log longitudinal analysis missing | Health | Low | Low (new skill) |
| cytometry not triggered by new skills | System | Low | Low (hook on skill creation) |
