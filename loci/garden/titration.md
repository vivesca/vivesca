# Titration

The method: force every component of your system to carry a name from one biological domain -- cell biology -- at one abstraction level. Then study what the biological name actually means. The gap between what the biology does and what your system does is the design insight.

That's titration.

Not metaphor. Not inspiration. A constraint with a protocol: pick a name, read the mechanism, find the break.

---

Synectics (Gordon, 1961) uses cross-domain analogies for creative brainstorming. Make the strange familiar, the familiar strange. Get unstuck.

Titration is not synectics. Four differences.

First: permanent constraint, not one-time exercise. You don't titrate in a workshop. You titrate when you name a file, a function, a skill. Every noun in the system carries the constraint.

Second: single domain, single abstraction level. Synectics mixes freely -- a cell here, a rocket there, a musical metaphor thrown in. That's the point of synectics. Titration requires a single domain because mixing levels lets you optimize for comfort. When biology is the only choice, you can't retreat to an easier register. "Middleware" is unavailable. You have to find the cell-level name or admit you don't have one yet.

Third: the break is the insight. Synectics succeeds when the analogy lands -- when the unfamiliar suddenly feels familiar. Titration is the reverse. It uses the break. The place where the analogy doesn't fit is where the engineering gap lives.

Fourth: naming IS architecture. Synectics is ideation. The output is ideas, which may or may not become design. With titration, the name commits. You named a component exocytosis. Now it must export. You named something a membrane. Now it must decide what enters and what doesn't.

---

Why biology? Because biological names encode mechanism.

"Endocytosis" decomposes: endo + cyto + osis. Inside, cell, process. A process of bringing things inside the cell. The name is a compressed spec. You don't need to read a textbook. The roots tell you what it does and roughly how.

Software names don't do this. "Middleware" is a spatial metaphor with no mechanism. "Pipeline" is a plumbing metaphor with no specifics. "Service" is a contract with no substance. These names describe relationships without describing mechanisms. They label slots.

Biological names carry 3.8 billion years of R&D. Every mechanism that survived did so because it worked under pressure. The names are filed claims on solutions to real problems. When you borrow one, you get the mechanism as a guide.

---

Two examples from my own system.

First: a planning skill that needed a name. I called it "translation."

In biology, translation is the process of carrying mRNA to a ribosome and synthesising a protein from that sequence. The ribosome reads a specification (mRNA) and produces a physical structure (protein).

I studied the mechanism. The ribosome doesn't just read the sequence -- it checks. There's a codon-anticodon matching step. Mismatches trigger pauses. The process has confidence built in at every step.

Now I looked at my planning skill. It read a specification and produced a plan. It had no equivalent of confidence checking. It would translate regardless of whether the source sequence was ambiguous or incomplete.

AlphaFold predicts protein structure from sequence. It also outputs pLDDT scores -- per-residue confidence. "I predict this region folds this way, and I'm confident about it" versus "I predict this, but this region is uncertain." The structure prediction is separate from the confidence in the prediction.

My planning skill had no pLDDT equivalent. It produced plans with no signal about which parts were solid and which were guesses.

The biology surfaced something the engineering hadn't noticed. I built foldability scoring into the planning skill. When the translation was uncertain, it flagged it.

The match: read spec, produce structure. The break: confidence at each step, not just at the output. The break was the feature.

Second: a completeness audit.

I titrated every major cell organelle against the system. Nucleus: present (the human's will). Ribosome: present (the skill that executes from spec). Membrane: present (hooks and taste filters). Endoplasmic reticulum: present (the staging area before output). Golgi apparatus: present (sorting and labelling before export).

Then mitochondria: the organelle that converts substrates into usable energy. My system had no energy budget. It would run 100 parallel tasks as readily as one. Nothing managed depletion or recovery. Mitochondria was missing.

Then apoptosis: programmed cell death. The signal that a cell should retire. Skills that had drifted, hooks that were redundant, pathways that had been superseded -- nothing removed them. They accumulated. Apoptosis was missing.

The naming forced the question. The biology told me what the answer should look like.

---

The boundary matters.

Some names map cleanly. The match is confirmation: this component is doing what the biology says it should do.

Some names break. The break is the insight: here is where the design has a gap the engineering hadn't named.

Some things genuinely don't map. Python runtime mechanics, async event loops, file system paths. Nothing in cell biology does what a garbage collector does. Forcing a biological name here would obscure more than it revealed.

The honesty test: does the mapping reveal something, or does it obscure something? Stop when it obscures.

---

The chemical titration procedure is the metaphor that holds all of this.

In titration, you add a reagent of known concentration to an unknown sample. You watch for the break point -- the equivalence point -- where the reaction completes. Before the break, the reagent is being consumed: the analogy holds. At the break, you have the answer. After the break, excess reagent precipitates out: the mapping has gone past useful.

Adding biology to a software system works the same way. Before the equivalence point: confirmation, design alignment, mechanism guidance. At the break: the insight you needed. After it: forced mappings that obscure the mechanism rather than reveal it.

The break is not the failure. The break is the feature. That's the whole point of titration.
