---
name: skill-forge
description: Iterative skill creation — research existing patterns, draft the SKILL.md, validate with mock invocations, refine to production quality.
product: a verified, production-ready SKILL.md ready to register in the organism
trigger: creating a skill that needs to be correct on first invocation (client-facing, high-volume, or safety-critical)
---

## Lead (opus)
Holds the skill's design intent. Ensures the skill does one thing well and the interface is unambiguous.
Makes the judgment call on whether the skill is production-ready or needs another iteration.

## Workers (sonnet, parallel then sequential)
- **researcher**: reads existing skills for patterns, checks if similar skills exist, surveys the domain the skill will operate in — produces a 1-page pattern brief
- **drafter**: writes the SKILL.md from the researcher's brief and lead's design intent — tool list, judgment rules, protocol, output spec
- **tester**: constructs 3-5 mock invocations representing edge cases, runs them mentally against the draft, reports where the skill would fail or produce ambiguous output
- **refiner**: incorporates tester feedback, tightens the protocol, sharpens the output spec, eliminates ambiguity

## Protocol
1. Lead states the skill's one job and its primary consumer (human vs. pipeline vs. agent)
2. Researcher surveys patterns in parallel with lead drafting the design intent
3. Drafter writes SKILL.md v1 from research + design intent
4. Tester runs mock invocations against v1, reports failures
5. If tester finds critical failures: refiner produces v2, tester re-validates
6. Lead reviews final version: is the judgment bracketed correctly? Is the interface unambiguous?
7. Lead writes the skill to disk, registers it
8. Colony dissolves

## Cost gate
~$2-4 per skill. Justified when: skill will be invoked repeatedly (amortizes), skill output feeds downstream automation, or skill is the sole mechanism for a high-stakes action. Quick utility skills = single bud writes the SKILL.md directly.

## Dissolution rule
Dissolves after lead approves the final SKILL.md and it is written to disk. Failed validations do not trigger dissolution — the colony persists until the skill passes or the lead kills the effort.
