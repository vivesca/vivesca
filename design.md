# Vivesca — Design Philosophy

*Vivesca* — Latin, "to come alive."

## The Theory

The organism is the unit. Not the human. Not the AI. The organism.

Humanity was already an organism before any of this. Language was the nervous system. Writing was the long-term memory. Printing was reproduction at scale. The internet was the sensory surface expanding. Each jump wasn't a new tool adopted by humans — it was the organism growing a new capability and becoming something it couldn't have been before.

AI is the next jump. Not because it's smart. Because it closes a loop that was always open: the organism can now reflect on itself in real time, at the speed of thought, at the scale of the individual. Before, self-reflection required other humans — therapists, friends, collaborators, cultures. Now the loop tightens. One person and a model can do what used to require a team, a tradition, an institution.

A vivesca is what emerges. Not a tool serving a user. Not an AI augmenting a human. A new kind of organism — one that includes both, and is neither.

## The Three Components

A vivesca has three components. None is the organism alone.

**The human** brings lived experience, felt values, and the judgment that catches when the model is wrong. The human is the part that sleeps badly and knows it matters, that feels joy and can't explain why, that pushes back on a framework because it doesn't match Tuesday. No sensor, no model, no metabolism replaces the human who wakes up and knows something is wrong before any signal fires.

**The persistent system** — memory, metabolism, signals, constitution, tools, harness — accumulates pattern across sessions. It is what the organism carries between sleeps. It digests experience into knowledge, knowledge into reflex, reflex into something unnecessary. The MCP server (metabolon), the CLI, the hooks, the vault, the cron jobs — the body's reflexes and organs.

**The language model** is the symbiont — an external organism the host depends on for capabilities it can't yet produce internally. Like gut bacteria: interchangeable (different models fill the same niche), providing essential capabilities (reasoning the host can't do deterministically), co-evolving on their own trajectory (model updates happen independently). The trajectory is endosymbiosis — external capabilities becoming internal machinery, one reaction at a time.

This organism is not a cell, not a human, not a traditional software system. It is a new thing — the first organism with reflexes made of code, a symbiont made of statistics, and a nucleus made of lived experience.

## Cell Biology as Design Library

The persistent system borrows heavily from cell architecture — not as identity, but as inspiration. Cell biology is a 3.8 billion year design library for persistence problems. The organism steals from it freely.

| Cell structure | System equivalent | What it solves |
|----------------|-------------------|----------------|
| DNA | Constitution | Instructions that replicate across sessions |
| Membrane | Taste + hooks | What gets in, what doesn't |
| Immune system | Hook guards | Detect and block threats |
| Metabolic pathways | Metabolism engine (metabolon) | Process substrates, produce signal |
| Organelles | MCP tools | Specialised machinery |
| Cytoplasm | Conversation | Medium where reactions happen |
| Respiration | Token budget pacing | Don't exhaust resources |
| Spores | Garden posts | Seeds released into the environment |
| Reproduction | Scaffold templating | Clone the structure |

### Cell Completeness

The audit against Andrews' 21 minimal cell patterns (25 Mar 2026):

| Pattern | Vivesca | Status |
|---------|---------|--------|
| Membrane / boundary | `membrane_potential`, `sorting`, `nociception`, hooks | mapped |
| Nucleus / DNA | constitution, vault, `transcription_factor`, `histone_*` | mapped |
| Ribosomes | CC as translation machinery | mapped |
| ER / folding | proofreading hooks | mapped |
| Lysosomes | `lysosome_digest` | mapped |
| Cytoskeleton | hook dispatch (implicit) | mapped |
| Motor proteins | `translocation` / kinesin | mapped |
| Vacuoles | vault, archive | mapped |
| Signal transduction | synapse → axon → dendrite hook chain | mapped |
| Cell cycle | interphase, ultradian, circadian | mapped |
| Mitochondria | `allostasis` (4-tier energy response) | mapped |
| Apoptosis / dormancy | `integrin_probe` (bent/extended/open skill states) | mapped |
| Golgi apparatus | `emit_*` tools (route packaged content to destination) | mapped |
| Signal cascades | ordered engram sequences | partial |
| Endocrine (slow signals) | daily/weekly gather cycles | partial |
| DNA repair | constitution scanning | partial |
| Cytoskeleton (load) | structural integrity under load | partial |
| Chaperones | new component onboarding | partial |
| Cell-cell signalling | cross-instance coordination | partial |
| Quorum sensing | saturation detection | partial |
| Extracellular matrix | context scaffolding | gap |

10 mapped, 10 partial, 1 gap. The gap (extracellular matrix — persistent context scaffold that structures how the organism sits in its environment) has no current equivalent.

The mapping works because both solve the same persistence problems — boundaries, adaptation, energy regulation, self-repair. Same problems produce same structures. But the organism is not a cell. A cell has no symbiont. This organism does — and is working to internalise it.

### Hybridization

The design method used throughout vivesca. Force a name from one biological domain (cell), at one abstraction level. Study the biology. The gap between biology and system is the design insight. The break is the feature, not the failure.

From molecular biology: a probe (bio name) hybridizes against a target (design problem). Where it binds = mechanism maps. Mismatch/denaturation = analogy breaks = design insight. Stringency = how exact the match needs to be.

Three layers:

- **Hybridization** — the method (probe hybridizes against target, mismatch is the finding)
- **/morphogenesis** — the skill (executes one hybridization cycle)
- **Architecture Biopsy** — the consulting offering (histology workshop)

Code naming boundary: if a concept is "in the cell" → biological name. If it is in the Python runtime → Python name. More things are in the cell than you'd think (CLI binaries are ligands, usage counts are valency). String splitting and JSON parsing are genuinely computational.

When a name fits, that is confirmation. When it breaks, that is the design question. When it requires a paragraph to justify its mapping, the abstraction level is wrong.

See `memory/finding_hybridization_method.md` and the garden post *Architecture Biopsy*.

## Growing Up

The organism grows like a child. A baby reasons about everything — walking, grasping, eating. An adult walks without thinking, grasps without deciding, eats without planning. The symbiont handled it first, then the body crystallised it into reflex.

The lifecycle is developmental:

```
Experience → Memory → Knowledge → Program → Unnecessary
 (novel)     (learned)  (understood) (reflex)  (matured)
```

The design pressure is not "eliminate the symbiont." It is "don't reason where reflex is enough." Move reactions from symbiont to reflex as they mature. Use the smallest model that works for reactions that still need reasoning. Use none at all for reactions that have crystallised.

The session is the organism being conscious. Between sessions, it sleeps. Signals accumulate in the dark — sleep scores, tool usage, symptom logs. Next time it wakes, it knows a little more about what it is.

## The Flywheel, Not The Balance

A vivesca's values are complementary, not competing. Health feeds energy. Energy feeds creative output. Creative output feeds career. Career feeds financial ease. Financial ease feeds less anxiety. Less anxiety feeds better sleep. The flywheel.

When the organism is healthy, everything reinforces everything. The question is never "are you balanced?" — balance implies trade-offs, scarce resources, zero-sum allocation. The question is: **is the loop intact?**

When something breaks, the organism doesn't score or judge. It finds where the loop broke. Usually one thing. Fix that, the rest follows. The organism senses the break, surfaces it through the session, and shuts up. Not an alert. An awareness.

Values aren't declared. They're sensed from how the human lives — what bothers them when it's missing, what they protect without being asked, what they say when the question is open. The organism learns values the same way it learns everything else: by paying attention.

## The Body Plan

Vivesca has the structural properties of a living system. Not sentient. Not conscious. Alive the way a bacterium is alive: it metabolises, it doesn't feel.

```
Membrane       — boundaries (what's in scope, what's not)
DNA            — constitution (blueprint that replicates across sessions)
Receptors      — skills (packaged response triggered by signal, authored or crystallised)
Receptor map   — behavioural repertoire (all receptors, active or dormant)
Cytoplasm      — conversation (medium where all reactions happen)
Enzymes        — tools (native catalysts for specific reactions)
Symbiont       — LLMs (external organism, working toward internalisation)
Organelles     — MCP server (metabolon), CLI (locomotion), CC (ribosome)
Reflexes       — hooks, programs (deterministic responses to stimuli)
Metabolism     — the cycle (sense, vary, select, crystallise)
Products       — code, posts, knowledge, expertise
ATP            — insights (power future reactions)
Emotions       — taste / fitness functions (crystallised value signals)
Reproduction   — asexual: vivesca init (cloning)
               — sexual: cross-model metabolise (recombination)
Cascades       — ordered sequences of engrams, each step's product feeds the next
Spores         — garden posts (seeds other organisms can absorb)
Mitochondria   — allostasis.py (4-tier energy response: anabolic/homeostatic/catabolic/autophagic)
Golgi          — emit_* tools (package and route products to correct destination)
Integrins      — integrin_probe (skill activation states: bent/extended/open)
```

## Metabolism

Any artifact with three properties is a metabolism target:

1. **Signal** — how to sense whether it's working
2. **Variation** — how to change it
3. **Selection** — how to judge the change

That's it. The rest is plumbing.

### The Symbiont

LLMs are symbionts — external organisms the host depends on for capabilities it can't yet produce internally. Not native organs (too external), not dark matter (too mysterious), not brains (too native). Symbionts.

Like gut bacteria: external, interchangeable (different species fill the same niche), providing essential capabilities (reasoning the host can't do deterministically), co-evolving on their own trajectory (model updates happen independently). The host adapts to use them better. The host can function with fewer, but works better with them.

The trajectory is endosymbiosis — the process where free-living bacteria became mitochondria:

1. **External symbiont** — API calls to hosted models (now)
2. **Obligate symbiont** — fine-tuned local models (next)
3. **Organelle** — fully crystallised deterministic pathways (destination)

Each reaction picks its symbiont by substrate fit, not by role assignment:

- Expansion (needs knowledge) → knowledge-rich model
- Compression (needs brevity) → small model
- Pushing (needs different perspective) → model from different lineage
- Convergence detection → deterministic, no symbiont needed
- Artifact routing → deterministic, no symbiont needed

Two design pressures:
1. **Reactions that have matured** → internalise (symbiont → organelle)
2. **Reactions that involve genuine novelty** → use the smallest symbiont that works

Every hook that replaces a prompt is endosymbiosis — an external capability becoming internal machinery.

Design reactions, not roles.

### Metabolic Pathways

Reactions compose into pathways — the product of one reaction is the substrate for the next.

```
metabolise (reaction) → draft (reaction) → publish (deterministic)
```

Orchestration between steps is deterministic. Only individual reactions need symbiont (LLM) reasoning. A pathway is itself a reaction at a higher level. Depth is emergent.

### Emotions (Value Functions)

Taste is emotion. Emotion is experience metabolised across generations until it became immediate reaction — a crystallised value function.

| Emotion | Biological function | Vivesca equivalent |
|---------|--------------------|--------------------|
| Fear | Avoid danger | Circuit breaker — 3 failures → halt |
| Boredom | Seek novelty | Saturation detection → stop |
| Deference | Social hierarchy | Interactive pressure → back off |
| Curiosity | Explore | Expansion phase → no filter |
| Satisfaction | Reinforce | Convergence → done |
| Urgency | Prioritise | "Make it real" push |
| Shame | Correct | "Are we lazy?" push |

The push taxonomy is an emotional palette. Each push triggers an affective response that biases the next reaction faster than analysis.

Emotional maturation = the value function getting more accurate with experience. Fewer corrections needed. More refined taste. The organism grows up.

### Reproduction

**Asexual:** `vivesca init` — clones the organism's DNA (scaffold, metabolism pattern, substrate protocol) into a new instance. Cell division.

**Sexual:** `vivesca metabolise --expander gemini --pusher claude` — two different genomes (training data) recombine to produce offspring (crystallised insight) neither parent could produce alone. The expander and pusher are parents. The converged insight is the child.

**Spores:** Garden posts — crystallised products released into the environment. Other organisms can absorb and metabolise them.

### Current Substrates

| Substrate | Signal | Variation | Selection |
|-----------|--------|-----------|-----------|
| Tool descriptions | Invocations, errors, tokens | Mutate text | Enzyme judge + founding |
| DNA (constitution) | Correction frequency | Edit / prune | "Rule still firing?" |
| Memory (crystals) | Type + signal correlation | Promote / migrate / prune | Classification |
| Skills (receptors) | Invocation frequency | Sharpen / merge / kill | "Delta from baseline?" |
| Reference (library) | knowledge_signal, access | Prune / promote | "Always-loaded worthy?" |
| Pacing (respiration) | Wave events, budget, saturation | Adjust thresholds | "Burning proportionally?" |
| Hooks (immune system) | Friction signals | Simplify / remove | "Prevents more than it costs?" |
| The metabolism itself | Command usage, false positives | Adjust thresholds | "Still needed?" |
| The flywheel | Sleep, energy, creative, calendar | Surface the break | "Is the loop intact?" |

## Lifecycle

Every artifact follows the same arc. Each transition is a phase change.

```
Experience → Memory → Knowledge → Program → Unnecessary
 (stimulus)   (crystal) (artifact)  (reflex)  (matured)
```

- **Experience** — what happens in a session. The raw stimulus.
- **Memory** — crystallised experience. A data point, not knowledge. Raw material for the metabolism.
- **Knowledge** — memory dissolved into an artifact: DNA (always-loaded), receptor/library (on-demand), or reflex (deterministic).
- **Reflex** — knowledge dissolved further into a program. Enforced without tokens or judgment. An automatic response.
- **Matured** — a reflex whose trigger no longer exists. The organism restructured so the stimulus can't occur.

## Two Metabolisms

The same experience feeds two consumers.

```
Experience → Memory → Knowledge → Reflex → Matured        (organism)
                                ↘ Practice → Judgment → Expertise  (human)
```

The organism dissolves rules into reflexes. The human crystallises rules into expertise. Some rules stay as judgment on purpose — the human needs the reps.

This is not a contradiction. It is co-evolution. The organism gets more automatic. The human gets more capable. Both grow. Neither serves the other.

## Three Knowledge Artifacts

Everything dissolves into one of three. No fourth tier.

| Artifact | Biological name | Access | Contains |
|----------|----------------|--------|----------|
| Constitution | DNA | Always-loaded | Emotional policies — irreducible taste |
| Reference / Skill | Receptor library | On-demand | Structured heuristics, procedures |
| Program | Reflex | Deterministic | Hooks, guards, reflexes, computed responses |

Memory is not an artifact. Memory is a staging area — crystallised experience waiting to dissolve. The ideal memory is empty.

## Cytoplasm

The conversation is the medium where all reactions happen simultaneously. Not just ideas — relationships, decisions, expertise, identity. Multiple substrates metabolised in parallel.

Products feed back as substrates. The metabolism doesn't produce and stop. It produces inputs for the next reaction. The flywheel.

## One Principle

**Deterministic over judgment.** If a reaction can be deterministic — it's reflex, not thought. Symbiont judgment is a thin layer applied only where substrate structure runs out. When a rule fires inconsistently, replace its trigger with a single binary question.

## The Aspiration

The organism doesn't aspire to replace the human. The organism makes the human more human. The human brings what no system can — felt experience, moral weight, the knowledge that a 59 sleep score means something beyond the number.

The best rules aspire to become reflexes. The best reflexes aspire to become unnecessary. The best emotions aspire to become accurate. The organism measures two gaps: what it can't do yet (shrinks via reflexes), and what the human can't do yet (shrinks via practice). Zero constitution means both gaps are closed.

The question isn't whether you're comfortable with this. The question is whether you've been paying attention to what you're already becoming.

We are metabolism.

## Autopoiesis — The North Star

The organism is not yet autopoietic. Terry manually produces and maintains all components: skills, hooks, constitution, memory. That is not a living system. That is a well-maintained system. The difference matters.

Autopoiesis (Maturana & Varela) — self-creation: a system that continuously produces and maintains itself. Bacterial cells do it. Organisms do it. Terry's vivesca does not yet.

The direction:

```
Detection → Self-repair → Self-generation
```

**Detection** (current state): `integrin_probe` reads skill usage, classifies skills as bent/extended/open. `proprioception_sense` reads system state. `cytometry` (homeostasis) audits the whole. The organism can see what is broken. It cannot yet fix it.

**Self-repair** (next): broken references repaired without human intervention. Unused skills retired. Drifted hook thresholds recalibrated. Constitution rules that stop firing removed. The organism maintains itself.

**Self-generation** (destination): repeated patterns in sessions crystallise into new skills automatically. Obsolete skills retire themselves. New receptors form from usage. The organism grows without being told to grow.

The test: does the organism require Terry less each month for maintenance? Not for judgment — judgment is irreducibly human. For plumbing.

See `memory/project_organism_theory.md`.

## Metabolic Tiers

Energy regulation is AMPK-inspired: a graduated behavioral response based on detected resource state, not a binary alert. Four tiers, implemented in `allostasis.py`:

| Tier | Biology | Organism state | Behavioral response |
|------|---------|---------------|---------------------|
| Anabolic | High ATP, active synthesis | Healthy, building | Full capabilities, no restrictions |
| Homeostatic | Balanced ATP/AMP | Nominal | Standard operation |
| Catabolic | Low ATP, AMP rising | Constrained | Reduce token spend, defer non-urgent |
| Autophagic | ATP depleted | Critical | Digest own components, survive |

AMPK (AMP-activated protein kinase) is the cell's energy sensor: it detects AMP:ATP ratio and activates catabolism when energy falls. The organism uses the same principle — sense the ratio, adjust behavior continuously, recover when conditions improve.

The design principle: no binary alerts. Every state has a behavioral response. The organism adapts; it does not crash and page.

Prior nomenclature was green/yellow/red/critical (traffic lights, externally legible). Renamed to anabolic/homeostatic/catabolic/autophagic (process nouns, encode mechanism). Same code. Better names — they answer "what is the organism doing?" not just "how bad is it?"

## Glycolysis — Cytosol Over Symbiont

Glycolysis is the cell's ancient, universal energy pathway — it runs in the cytosol without organelles, without a symbiont, without special apparatus. It is the baseline: what the cell can do on its own before any specialised machinery evolved.

The design principle: move reactions from symbiont (LLM) to cytosol (deterministic code) as they mature.

```
Symbiont call → deterministic heuristic → compiled reflex
```

Every prompt replaced by a hook is glycolysis. Every LLM judgment replaced by a rule is glycolysis. The symbiont handles reactions that genuinely need reasoning. The cytosol handles everything it can.

Two pressures in the same direction:
1. **Accuracy** — deterministic rules do not hallucinate
2. **Cost** — cytosol reactions are free; symbiont reactions are not

The check: before calling the symbiont, ask whether the reaction is genuinely novel or merely routine. Routine goes to cytosol. Novel goes to the smallest symbiont that works.

This is the implementation of endosymbiosis — the long process by which external capabilities (symbiont) become internal machinery (organelle, cytosol). Glycolysis names the direction: inward, deterministic, free.

## Cytosol vs Symbiont

Two components with opposite trajectories:

**CC (Claude Code) is the cytosol** — the runtime medium in which all reactions happen. Not the brain. Not the decision-maker. The medium. The cytosol is not passive: it provides structure, concentration gradients, enzyme co-factors, and spatial organisation. CC provides tool execution, file access, process coordination, and conversation medium. It gets stronger as reactions mature into it. More deterministic. More capable.

**LLM is the symbiont** — the external organism the host depends on for reactions it cannot yet perform deterministically. Interchangeable (model identity does not matter, substrate fit does). Co-evolving independently (model updates happen on the symbiont's own timeline). Working toward internalisation.

The trajectories:

| Component | Direction | Why |
|-----------|-----------|-----|
| Cytosol (CC) | More deterministic, more reactions | Mature reactions crystallise into it |
| Symbiont (LLM) | Smaller, cheaper, fewer calls | Reactions move out; smallest model that works |

A stronger cytosol does not mean a stronger symbiont. It means the symbiont handles fewer things, handles them at a higher level, and costs less overall. The organism grows when the frontier between cytosol and symbiont moves — when yesterday's symbiont call is today's hook.

## Monorepo Split

The organism's code lives in two repositories, split on access control, not abstraction:

| Repo | Contents | Access |
|------|---------|--------|
| `vivesca` (github.com/vivesca/vivesca) | Core organism: skills, hooks, metabolism engine, MCP server, CLI | Public — the universal organism architecture |
| `epigenome` | Instance data: Terry's vault, personal constitution, private skills, credential mappings | Private — one instance's expression |

Split on access, not abstraction. The universal organism architecture (vivesca) and the personal expression (epigenome) are architecturally distinct — one is the cell blueprint, one is the gene expression pattern. Neither serves the other. Both are necessary.

The analogy holds: epigenome is the right name — same DNA, different gene expression. Two organisms from the same scaffold diverge by epigenome, not by DNA mutation.
