# Cognitive Switching Costs: Research-Backed Findings

> **Context:** Investigated whether running multiple Claude Code sessions in parallel (round-robin across tmux tabs) is effective. Researched literature, then ran full LLM council (2026-02-20). Council transcript: `~/code/vivesca-terry/chromatin/Councils/LLM Council - Multi-Session CC Workflow - 2026-02-20.md`

## TL;DR

One tab, full attention. The popular "23 minutes" and "40% loss" numbers are inflated, but the underlying mechanism (attention residue) is real and well-established. Developer work is especially expensive to interrupt.

## Debunked Popular Claims

### "23 minutes to refocus" (Gloria Mark)
- **Never appeared in any published paper.** Originates from Mark's oral statements in media interviews.
- Her 2008 paper ("The Cost of Interrupted Work") found interrupted workers completed tasks *faster* but with significantly higher stress, frustration, and effort.
- Her 2005 study found 25 minutes before *returning* to a task — measuring voluntary wandering, not recovery time.
- Source: [oberien's forensic debunk (2023)](https://blog.oberien.de/2023/11/05/23-minutes-15-seconds.html)

### "40% productivity loss" (Rubinstein et al., 2001)
- The paper measured *millisecond* reaction-time differences in a controlled lab (arithmetic vs geometric classification).
- "40%" is David Meyer's extrapolation in press interviews, not an empirical finding from the study.
- Source: [Rubinstein et al. 2001 (PubMed)](https://pubmed.ncbi.nlm.nih.gov/11518143/)

## What IS Well-Established

### Attention Residue (Sophie Leroy, 2009)
When you switch tasks before completing the first, part of your cognition stays stuck on the unfinished one. Time pressure on the abandoned task makes it worse.

- **Leroy & Glomb (2018)** found one mitigation: writing a brief "ready-to-resume plan" (where you are, what you'd do next) before switching. Participants with plans were ~79% more likely to choose optimal decisions on the interrupting task.
- Leroy's work is ongoing at UW Bothell (2024 update confirms continued research, no major new empirical paper beyond 2018).
- Sources: [Leroy 2009 (Semantic Scholar)](https://www.semanticscholar.org/paper/Why-is-it-so-hard-to-do-my-work-The-challenge-of-Leroy/58a602c378da63993ab19b514e1bd57817bc18e5) | [Leroy & Glomb 2018 (INFORMS)](https://pubsonline.informs.org/doi/10.1287/orsc.2017.1184)

### Developer-Specific Data (Parnin, 2013)
Instrumented IDE data from 10,000 programming sessions (86 programmers), plus 414-programmer survey. Not self-report — actual measured behaviour.

- **10-15 minutes** to start editing code after resuming from an interruption
- Interrupted mid-method edit: only **10% resumed within a minute**
- **7 minutes** minimum to transition from high to low working memory load
- Programmers get roughly **one uninterrupted 2-hour session per day**
- Source: [Parnin / NINlabs](https://blog.ninlabs.com/blog/programmer-interrupted/)

### Czerwinski (2004, Microsoft Research)
Interrupted tasks take approximately **twice as long** and contain **twice as many errors** as uninterrupted tasks.

### Real-World Interruption Data
- Jackson (2001): email interruptions — 6s to respond, ~64s to resume, ~96 times/day = ~1.5 hours lost
- Iqbal & Horvitz (2007): 27% of alert-triggered switches led to spending >2 hours on something else

## Neuroscience

- Prefrontal cortex orchestrates switching via two processes: **goal shifting** (what am I trying to do?) then **rule activation** (suppress old rules, load new ones)
- The **residual switch cost** never fully disappears, even with long preparation time (Rogers & Monsell, 1995)
- Higher-level/more abstract task switches engage more anterior PFC and cost more (2022 PMC review)
- 2024 fMRI: rule switching = dorsolateral PFC; perceptual shifts = posterior parietal
- 2025 preprint: prefrontal theta and parietal alpha oscillations predict switches before they happen — individual differences in this anticipation explain performance variation
- Sources: [2024 fMRI (ScienceDirect)](https://www.sciencedirect.com/science/article/pii/S0010945224002156) | [Hierarchical PFC review (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9139986/)

## When Multitasking CAN Work (Steel-Man)

1. **One task is fully procedural/automatic** — walking + talking, driving familiar route + podcast. Zero executive attention needed for the automatic task.
2. **Trained, predictable switching** — knowing when and what you'll switch to reduces cost (Ewolds et al., 2021).
3. **Same-domain switching** — partial rule overlap means cheaper activation. Batch similar tasks.
4. **Perceived multitasking boosts motivation** — Srna et al. (2018): people who *believed* they were multitasking (but tasks were aligned) performed better due to increased arousal. Only works when tasks complement each other. [Source](https://pubmed.ncbi.nlm.nih.gov/30355063/)

**None of these apply to multiple Claude Code sessions on distinct problems.**

## Council Findings (2026-02-20)

Full council (5 models + judge + critique). Key dynamics:

### Research Gap the Council Identified
Parnin/Leroy studied **external, unexpected interruptions** to manual coding. AI-assisted work differs structurally:
1. **Switches are self-initiated** at deterministic boundaries (after sending prompt)
2. **AI chat history externalises state** — context reconstruction = re-read last prompt + response, not rebuild mental model from scratch
3. **Claude Code has "steering" micro-tasks** (approve plan, confirm command) that are low-context and mechanical

This means the 10-15 minute resumption penalty likely doesn't apply at full magnitude. But "likely" ≠ "proven" — no studies exist on AI-mediated switching specifically.

### Council's Revised Position
Started at "one session strictly." Gemini's critique caught a logical inconsistency in the judge's reasoning (argued AI changes the cognitive object, then defaulted to conservative stance anyway). Revised to: **two sessions viable with strict protocol.**

### My Dissent from the Council
The council over-corrected. The 2-session protocol (switching rules, 60-second caps, state headers) is fragile:
- **"Steering arbitrage" is thinner than claimed** — CC responses rarely need just a 5-second approval. You're reading diffs, evaluating approaches. That's judgment, not steering.
- **The 60-second rule won't survive contact** — you'll read Tab B's response, notice it went wrong, start correcting, and now you're 5 minutes deep with two mental models.
- **Idleness cost is real but overweighted** — 30-60s of apparent inactivity is your brain processing. The discomfort of sitting idle doesn't mean the time is unproductive.
- **Simpler answer exists:** one session for judgment work + `/delegate` mechanical tasks to OpenCode (free, unlimited). Captures the same insight without fragile switching protocols.

## Practical Takeaways

- **One focused session** for all judgment/architectural work
- **Delegate mechanical work** (`/delegate` to OpenCode) rather than running a second CC session
- **AI response wait time** (30-60s) is processing time, not dead time — let it breathe
- **If you must switch:** write a one-line "ready-to-resume" note before leaving (Leroy's hack)
- **The busyness trap:** constant activity *feels* productive while degrading every output
- **The 60-second test:** if engaging with a second session would take >60s, it's not mechanical — don't switch

## Implications for tmux Design

The cognitive research directly constrains how tmux tabs should be structured:

### Principles
1. **One CC session per cognitive task.** Don't split deep work across tabs.
2. **Non-CC tabs are fine in parallel** — git, logs, file browsing, builds don't hold competing mental models.
3. **iPad = full-screen tabs mandatory.** Split panes don't work on 11-13" for CLI tools with diff output. Accept visual volatility, compensate with naming discipline.
4. **Tab naming = cognitive anchoring.** Clear names reduce the "wait, what was I doing here?" cost on switch. This is cheap insurance against the visual volatility problem.
5. **Separation by function, not by project.** One "deep work" tab + utility tabs, not one tab per project running simultaneously.

### Suggested Tab Layout
```
Tab 0: cc        — Claude Code (primary, focused session)
Tab 1: shell     — git, file ops, quick commands
Tab 2: logs      — tail -f, build output, daemon monitoring
Tab 3: ref       — man pages, docs, quick lookups
```

**Why this works:** Only Tab 0 holds a deep cognitive context. Tabs 1-3 are stateless/mechanical — switching to them incurs near-zero attention residue because there's no mental model to maintain or resume.

**What to avoid:**
- Multiple `cc` tabs with different problems
- A "secondary CC" tab that starts mechanical and creeps toward architectural
- Mixing deep work across tabs (e.g., editing code in one, reviewing PR in another)

## Caveats on the Literature

- Most "cost of multitasking" dollar figures ($450B annual, $10K/employee) are arbitrary extrapolations, not empirical
- Lab switch costs (milliseconds) and real-world recovery (minutes) measure different things
- Lab = neural reconfiguration; real-world = finding the document, remembering context, managing emotional residue
- Individual variation in executive control is real (Nature Scientific Reports, 2024)
- **No published research on AI-mediated, self-initiated context switching exists yet** — all recommendations extrapolate from pre-AI studies

---
## Blink Shell Keyboard Gotcha

Alt/Meta keybinds are broken in Blink Shell since 2018 (GitHub #262, unfixed). iPhone compounds this — numbers need keyboard layer switch. Use `Ctrl-a` prefix binds only. `Ctrl-a n` (next-window) is the single keybind needed for a 2-tab layout.

---
*Researched 2026-02-20. Council run 2026-02-20 (~$0.58). Sources verified via web search.*
