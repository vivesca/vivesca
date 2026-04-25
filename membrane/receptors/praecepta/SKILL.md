---
name: praecepta
description: "Heuristic library — simple action rules replacing per-case reasoning. Consult when deciding, advising, or a known pattern fires. Complements topica (lenses) and bouleusis (planning)."
user_invocable: false
disable-model-invocation: true
---

# Praecepta — The Heuristic Library

From Latin *praecepta* — "precepts, practical rules." The collection of simple rules that trade per-case optimisation for cognitive efficiency.

**Thesis (Gigerenzer):** In uncertain environments, simple heuristics don't just save time — they often *outperform* complex analysis. More parameters = more overfitting to noise. Simple rules exploit the structure of the environment by ignoring irrelevant information.

**Why it works (bias-variance):** The less data you have relative to the number of variables, the simpler your model should be. With millions of rows, let XGBoost find the signal. With 50 cases, one variable beats twenty — the complex model is fitting noise. Most human decisions (career, health, relationships) are small-sample, high-noise, shifting-environment. That's where simple rules dominate.

**Not user-invocable.** Consult when: making decisions under uncertainty, advising Terry, evaluating options, or when two approaches seem equivalent and reasoning won't resolve it.

**Relationship to other skills:**
- **topica** — analytical lenses ("think about X this way"). Praecepta = action defaults ("just do X").
- **bouleusis** — planning theory. Praecepta fires *before* planning — it's the rule that says "don't plan, just act."
- **mandatum** — delegation theory. Delegation heuristics live here; mandatum has the deeper framework.
- **transcription-factor** (trigger: gnome) — decision capture. Praecepta provides the defaults that gnome overrides when stakes warrant deliberation.

---

## When Simple Rules Beat Complex Reasoning

| Condition | Why | Example |
|-----------|-----|---------|
| **High uncertainty** | Complex models overfit to noise when data is sparse | Career choices, startup bets |
| **Many cues, few matter** | Most information is irrelevant — simple rules find the signal | Medical triage, hiring |
| **High volume, low stakes per decision** | Reasoning cost exceeds decision value | Daily habits, email triage |
| **Time pressure** | No time for full analysis | Emergency response, negotiation |
| **Stable environment structure** | The rule can exploit regularities that persist | "Finish the course", traffic rules |
| **Unquantifiable trade-offs** | No common unit to compare — analysis is theatre | Career vs family, integrity vs convenience |

## When to Override and Reason From First Principles

- **Known, data-rich, stable domain** — actuarial tables, chess endgames, tax optimisation
- **Catastrophic + irreversible stakes** — worth the reasoning cost even if slow
- **Environment has shifted** — heuristic tuned to old structure (e.g., career advice from a pre-AI era)
- **Two heuristics conflict** — need to reason about which applies
- **You have genuine expertise** — in your domain, you've earned the right to override defaults

---

## Anatomy of a Good Heuristic

Every entry below has four parts:

1. **Trigger** — when does it fire? (Situation, not domain)
2. **Rule** — what do you do? (One sentence)
3. **Why it works** — the structural reason, not just "it's been said before"
4. **Breaks when** — known failure mode

---

## Decision & Action

| Heuristic | Trigger | Rule | Why it works | Breaks when |
|-----------|---------|------|-------------|-------------|
| **Reversibility gate** | Any decision with stakes | Reversible → move fast. Irreversible → slow down. | Reversible decisions have free correction; deliberation cost > error cost | You mistake irreversible for reversible (reputational damage, public statements) |
| **If you can't decide, no** | Torn between yes and no | Default to no. | Genuine opportunities create pull, not ambivalence. Ambivalence = insufficient signal. | Applies to additions, not subtractions. "Should I quit?" is different from "should I take this?" |
| **Satisfice, don't maximise** | Choosing among similar options | Take the first option that clears your threshold. Stop looking. | Maximising has diminishing returns + opportunity cost of search. After "good enough", more looking costs more than it finds. | Breaks for rare, high-stakes, one-shot decisions (house, spouse, co-founder) |
| **Optionality** | Fork in the road, unclear future | Choose the path that preserves more future choices. | Options have value under uncertainty. Don't collapse the possibility space prematurely. | Can become paralysis if you never commit. Options decay — some must be exercised. |
| **Spreadsheet test** | Two options, elaborate comparison | If you need a spreadsheet to decide, the options are close enough that it doesn't matter. Just pick. | The analysis is signalling parity, not revealing a winner. | Breaks when the spreadsheet reveals a clear outlier you'd missed |

## Delegation & Trust

> For deeper delegation theory: consult `mandatum` skill.

| Heuristic | Trigger | Rule | Why it works | Breaks when |
|-----------|---------|------|-------------|-------------|
| **Trusted source + bounded scope + low stakes = don't review** | Deciding how much to verify delegated work | Check credentials, check scope, check stakes. If all three are low-risk, trust the output. | Verification has a cost. Paying it when it can't change the outcome is waste. | Source is unvetted, scope is unbounded, or stakes are catastrophic |
| **Verify at edges, not internals** | Reviewing output (code, prescriptions, reports) | Define what correct looks like. Test the boundaries. Don't audit every internal decision. | Internals are the delegate's domain. You hired them for their judgment there. | When edge tests can't catch the failure mode (subtle logical errors, ethical violations) |
| **Finish the course** | Delegated to an expert for a bounded engagement | Follow the prescribed course. Don't second-guess mid-stream. | You're paying for their judgment. Interrupting based on your amateur assessment defeats the purpose. | Side effects are severe, or new information materially changes the situation |
| **Three failures, then review** | Delegation is underperforming | Give the delegate three attempts before switching to oversight mode. | One failure is noise. Three is signal. | The failure mode is catastrophic (don't wait for three bridge collapses) |

## Communication

| Heuristic | Trigger | Rule | Why it works | Breaks when |
|-----------|---------|------|-------------|-------------|
| **Default to direct** | Unsure whether to be diplomatic or blunt | Say the thing. Add tact, don't add fog. | Indirectness creates ambiguity. Ambiguity creates more messages. | Cultural context demands indirectness (face-saving cultures, hierarchical relationships) |
| **One message, one ask** | Writing an email or message with multiple needs | Split into separate messages, or bold the one ask. | Multiple asks = no ask. The reader addresses the easiest and ignores the rest. | Rapid-fire messages annoy more than one structured message |
| **24-hour rule** | Angry or frustrated and about to send | Wait. Re-read tomorrow. | Emotional state decays faster than you think. Tomorrow-you will edit 80% of it. | Genuinely time-critical (safety, legal deadline) |
| **Match the medium to the weight** | Choosing how to communicate something | Lightweight → chat. Important → call or face-to-face. Permanent → written. | Medium signals weight. Firing someone over Slack tells them how little it mattered to you. | Over-weighting routine comms wastes time (not everything needs a meeting) |

## Career

| Heuristic | Trigger | Rule | Why it works | Breaks when |
|-----------|---------|------|-------------|-------------|
| **Optimise for learning rate early, leverage late** | Career stage decisions | 20s–30s: pick the job where you learn fastest. 40s+: pick the job where your existing knowledge has the most leverage. | Early career: compound knowledge. Late career: deploy knowledge. | You're financially constrained (learning doesn't pay rent) |
| **Work with people, not logos** | Choosing between offers | Pick the team, not the brand. | Your day is your manager + 5 closest colleagues. The logo is on your CV; the people are in your life. | The logo genuinely opens doors you can't get otherwise (specific credential play) |
| **20% pay cut test** | Evaluating a role | Would you take this job at 20% less? If no, you're buying the comp, not the work. | Comp wears off; work compounds. If the work isn't the draw, you'll resent it in 18 months. | You're explicitly doing a financial optimisation phase (paying off debt, building runway) |
| **Revealed preference** | Evaluating an employer | Watch what they do, not what they say. Budgets, promotions, and fires reveal values. | Stated values are marketing. Resource allocation is strategy. | New leadership — past actions may not predict future direction |

## Engineering

| Heuristic | Trigger | Rule | Why it works | Breaks when |
|-----------|---------|------|-------------|-------------|
| **Make it work → right → fast** | Building anything | Get it running first. Clean it second. Optimise third. Never in reverse. | Premature optimisation / abstraction creates complexity before you understand the problem. | Performance-critical path where slow = broken (real-time systems) |
| **Rubber duck threshold** | Stuck debugging > 30 min | Explain the problem out loud (or to a prompt). | Verbalising forces you to linearise your mental model. The gap between what you think you know and what you actually know becomes obvious. | The problem is genuinely novel (no amount of explanation will surface what you haven't seen) |
| **Test at boundaries** | Deciding what to verify | Test inputs, outputs, edge cases. Don't test internal wiring. | Internal implementation is the author's judgment. Boundaries are the contract. | When internal complexity is the risk (security, concurrency) |
| **If it hurts, do it more** | A process is painful (deploys, merges, testing) | Increase the frequency. Pain = feedback signal that the batch size is too large. | Frequent small batches surface problems early and cheaply. | The pain is inherent, not batch-related (hardware failure, regulatory approval) |
| **Delete before you abstract** | Tempted to create a helper/utility | Can you delete the duplication instead of abstracting it? Three similar lines > one premature abstraction. | Abstractions have maintenance cost. Wrong abstractions are worse than duplication. | Genuine duplication across 5+ call sites with identical logic |

## Health

| Heuristic | Trigger | Rule | Why it works | Breaks when |
|-----------|---------|------|-------------|-------------|
| **Sleep > exercise > diet** | Deciding what to fix first | Fix in that order. | Sleep affects everything downstream. Exercise affects appetite and mood. Diet is the fine-tuning. | Specific medical condition requires diet-first (diabetes, allergies) |
| **The exercise you'll do** | Choosing a fitness regime | The best exercise is the one you'll actually do consistently. | Consistency beats intensity. A daily walk beats a weekly HIIT session you skip half the time. | Training for a specific goal (marathon, powerlifting) requires specificity |
| **Finish the course** | Prescribed a bounded medication course | Take everything until it runs out. Don't self-adjust. | You're not a pharmacologist. The doctor prescribed a system, not individual drugs. | Severe side effects, or the prescriber explicitly said "stop when symptoms resolve" |

## Finance

| Heuristic | Trigger | Rule | Why it works | Breaks when |
|-----------|---------|------|-------------|-------------|
| **Automate first** | Setting up savings/investments | Pay yourself first. Automate the transfer. Spend what's left. | Willpower is unreliable. Systems beat discipline. | Income is volatile (freelance — need manual adjustment) |
| **Time in > timing** | Deciding when to invest | Get in. Stay in. Don't try to time it. | Missing the 10 best days in a decade halves your returns. Nobody reliably predicts which days those are. | You have specific, time-bounded liquidity needs |
| **Don't invest in what you can't explain** | Evaluating an investment | If you can't explain the thesis in one sentence, you're speculating, not investing. | Complexity hides risk. If you don't understand it, you can't evaluate when to exit. | Diversified index funds — you don't need to understand every company |
| **Too good to be true** | Evaluating a deal/return | It is. Walk away. | Asymmetric information: the person offering the deal knows more than you. Consistent above-market returns have a hidden cost. | Genuinely novel opportunities (early crypto, early equity) — but these are rare and you should know you're gambling |

## Honesty & Integrity

| Heuristic | Trigger | Rule | Why it works | Breaks when |
|-----------|---------|------|-------------|-------------|
| **Default to truth** | Choosing whether to shade the truth | Tell it. Absorb the short-term cost. | One version of events, no bookkeeping, compounding reputation. Lying has O(n²) maintenance cost. | Protecting someone from harm (surprise party, not "does this look bad") |
| **Front-stage / back-stage** | Choosing register | Internal: say what you think. External: say what's useful and true. Never: say what's useful and false. | Honesty ≠ radical transparency. The audience determines the frame, not the content. | Emergency — sometimes you need to be blunt externally too |

---

## Meta-Heuristics (Rules About Rules)

| Meta-rule | Meaning |
|-----------|---------|
| **More uncertainty → simpler rule** | Complex models overfit. Simple rules are robust to noise. |
| **Cheap wrong > expensive right** | A heuristic that's wrong 20% of the time but free to apply beats analysis that's right 95% but costs an hour. |
| **Good heuristics have clear triggers** | If you can't say *when* it fires, it's a principle, not a heuristic. Principles inspire; heuristics act. |
| **Update from failures, not successes** | Successes confirm everything. Failures reveal which heuristic was wrong. |
| **Domain-specific beats general** | When two heuristics conflict, the one tuned to *this* domain wins. |
| **Heuristics are defaults, not laws** | They exist to be overridden — but only deliberately, with a reason. The override cost should be > 0. |
| **Acquire heuristics from experts and failures** | Read Gigerenzer, talk to practitioners, and debrief your own mistakes. Don't theorise heuristics — harvest them. |

---

## How to Build Your Library

1. **Notice when you're reasoning about something routine** — that's a missing heuristic
2. **Harvest from experts** — doctors, engineers, mentors. Their heuristics encode decades of pattern matching
3. **Harvest from failures** — every post-mortem should produce at least one new rule
4. **Test in low-stakes environments** — adopt tentatively, confirm through use
5. **Prune what doesn't fire** — unused heuristics are clutter, not wisdom
6. **Name them** — a heuristic without a name is hard to invoke under pressure

## Key References

- **Gigerenzer** — *Simple Heuristics That Make Us Smart*, *Risk Savvy*. The empirical case.
- **Sull & Eisenhardt** — *Simple Rules*. The organisational case.
- **Munger** — *Poor Charlie's Almanack*. The investor's heuristic library.
- **Taleb** — *Antifragile*. Via negativa: what to remove > what to add.
- **Simon** — *satisficing*. The original: "good enough" as optimal strategy under bounded rationality.
