---
name: trutina
description: Conflicting evidence reconciliation — when sources disagree, reason about which to trust. Consult when research returns contradictory signals, two authoritative sources say opposite things, or you're unsure which claim to act on.
user_invocable: false
---

# trutina — Weighing Conflicting Evidence

Not user-invocable. Consulted internally when sources disagree.

*Trutina: Latin "weighing scale / balance" — the instrument used to determine which side carries more weight.*

## The Core Question

> Which claim has stronger warrant — and by how much?

Conflicting evidence is normal. The mistake is either (a) picking the one that confirms what you already believe, or (b) paralysing because "sources disagree." Trutina is the tiebreaker procedure.

## The Weighing Process

Run through these checks in order. Stop when one claim is clearly stronger.

**1. Date check**
Is one source significantly more recent? Technology, APIs, models, and pricing change fast. A 12-month-old claim about an API is often simply outdated, not wrong at the time.

> If one source is >6 months newer and the topic is technical → weight the newer one heavily.

**2. Source authority**
- **Primary** (official docs, first-hand observation, direct measurement) > **Secondary** (blog post, summary, LLM recall)
- **Specific** (describes a concrete case with details) > **General** (makes a broad claim without evidence)
- **Single-purpose** (written specifically about this claim) > **Incidental** (mentions it in passing)

**3. Motivated reasoning check**
Does either source have an incentive to be wrong in a particular direction? A vendor's docs understate limitations. A competitor's blog overstates weaknesses. A model trained on biased data repeats the bias.

> Flag the incentive; don't disqualify the source — just weight it accordingly.

**4. Testability check**
Is one claim empirically testable right now? If yes, run the test — this converts a conflicting-evidence problem into a judex problem. A 30-second test beats 10 minutes of source-weighing.

> If the claim is testable → stop trutina, switch to `judex`.

**5. Quorate tiebreaker**
If still unclear after steps 1-4 and the stakes are meaningful: `quorate quick` with both claims stated explicitly. "Source A says X, Source B says Y. Which is more likely correct and why?"

## Example

**Conflicting claims:**
- MEMORY.md says: "Codex sandbox blocks DNS → can't run cargo build"
- Recent Codex changelog mentions "improved sandbox networking"

**Weighing:**
1. Date: MEMORY.md entry from 2026-02-15; changelog is undated
2. Authority: MEMORY.md = first-hand observation (primary); changelog = vendor claim (motivated)
3. Motivation: Vendor has incentive to overstate improvement
4. Testable: Yes — try `cargo build` in a Codex session. 30 seconds.

**Resolution:** Test it. (Turns out: still blocked. MEMORY.md was right.)

## Relationship to Other Skills

- **examen** surfaces the question ("I'm assuming X is true") → **trutina** resolves it when evidence conflicts
- **indago** is for finding evidence — trutina is for weighing evidence you already have
- **judex** is for measuring outcomes — if trutina finds a testable claim, hand off to judex
