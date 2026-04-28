---
name: censor
description: "Quality gate for writing — garden posts, consulting papers, client deliverables. Anti-slop reject list + structured scoring. NOT for code review."
effort: high
user_invocable: true
argument-hint: "[post|paper|article|outreach|executive]"
---

# Censor Skill

Reusable quality review for skill outputs. Call this after generating drafts, analyses, or any output that benefits from a second pass.

## Trigger

Called by other skills, not directly by user. Skills invoke this at the end of their workflow:

```
Execute main task → Call /censor → Iterate if needed → Output
```

## Inputs

- **output** — The content to censor (required)
- **goal** — What the output was supposed to achieve (required)
- **domain** — Which criteria to use: `outreach`, `job-eval`, `technical`, `article`, `executive`, `default` (optional, auto-detect if not specified)
- **research** — If true, extract verifiable claims and fact-check via elencho before evaluating (default: false). Use `deep` for full elencho mode.
- **max_iterations** — How many revision cycles before giving up (default: 2)

## Engagement Context (check first)

Before evaluating, check for a persistent engagement context file:

1. Look for `engagement-context.md` in `~/epigenome/chromatin/{client}/` where `{client}` matches the content's target (e.g., `Capco/engagement-context.md` for HSBC work)
2. If found, load its anti-patterns as additional high-weight checks — these are match-and-refuse patterns specific to this client
3. Load sensitivities as evaluation context — violations of these are automatic `needs_work`

This replaces ad-hoc mark grepping for client-specific rules. The engagement context is the single source of truth for "what will get this rejected by the client."

## Workflow

0. **Research pre-step** (only if `research` is set):
   - Extract verifiable claims from the output: regulatory references, org names/titles, dates, statistics, framework citations.
   - Run `rheotaxis "<claim>"` for each claim (CLI, 7 backends parallel). If research=`deep`, use `rheotaxis --research "<claim>"`.
   - Compile results as `## Research Notes` appended to the evaluation context — confirmations, contradictions, and unknowns.
   - This context is available to all subsequent checks, especially `factual_accuracy`.

1. **Load criteria** from `criteria/{domain}.yaml` (or auto-detect domain from goal)
   - If domain file is missing, fall back to `criteria/default.yaml`.
   - If default is also missing, return `needs_work` with issue `criteria_unavailable` and stop.

2. **Evaluate output** against each check:
   - For each criterion, assess pass/fail
   - Weight by importance (high/medium/low)
   - Note specific issues found

3. **Decide verdict:**
   - All high-weight checks pass + majority of medium → `pass`
   - Any high-weight check fails → `needs_work`
   - Only low-weight issues → `pass` with notes

4. **Return structured result:**
   ```yaml
   verdict: pass | needs_work
   score: 0-100
   issues:
     - check: personalization
       severity: high
       problem: "No specific reference to recipient's work"
       suggestion: "Mention their recent post about X"
   summary: "One-line overall assessment"
   ```

5. **If called with iteration context:**
   - Compare against previous version
   - Note what improved, what's still missing
   - If same issues persist after max_iterations, return `pass` with caveats

## Auto-Detection Logic

If domain not specified, infer from goal keywords:

| Keywords in Goal | Domain |
|------------------|--------|
| post, garden, terryli, publish, secretome | post |
| paper, strategic, executive, board, direction, memo, CAIO, C-suite, HSBC | paper |
| outreach, message, linkedin dm, email, networking | outreach |
| linkedin post, linkedin comment, linkedin announcement | linkedin-post |
| job, role, position, application, evaluate | job-eval |
| code, technical, implementation, architecture | technical |
| article, blog, essay, writing | article |
| (none matched) | default |

## Integration Example

Other skills call censor like this:

```markdown
## Workflow (in /outreach)

1. Gather context about recipient
2. Draft personalized message
3. **Review with censor:**
   - Call censor with output=draft, goal="personalized networking message", domain="outreach"
   - If needs_work: revise based on feedback
   - Max 2 iterations
4. Output final draft to user
```

## Criteria Files

Located in `criteria/` subdirectory. Each file defines domain-specific checks.

Format:
```yaml
name: Domain Name
description: What this domain covers
checks:
  - name: check_name
    question: "Yes/no question to evaluate"
    weight: high | medium | low
    examples:
      good: "Example of passing"
      bad: "Example of failing"
```

## Output Modes

**For skill integration (default):**
Return structured YAML for programmatic handling

**For user review (if called directly):**
Return readable summary with specific feedback

## Example

```yaml
verdict: needs_work
score: 72
issues:
  - check: specificity
    severity: high
    problem: "Claims are generic."
    suggestion: "Add one concrete example tied to the goal."
summary: "Direction is solid, but one high-weight gap blocks pass."
```

## Notes

- Be constructive, not just critical — always include how to fix
- High-weight failures are blockers; low-weight are suggestions
- Don't over-iterate — diminishing returns after 2 passes
- Trust the criteria files; don't invent new checks on the fly

## From Cell Biology — Senior-Comms as MHC-II Antigen Presentation

When the domain is `paper` / `executive`, three additional gates derive from the antigen-presentation mechanism. Cell biology is load-bearing here, not decorative — the mechanism predicts costs the prior rubric does not price. Sources: `~/epigenome/marks/finding_anergy_risk_unsponsored_board_paper.md` and `finding_cross_presentation_wrong_receptor_routing.md`.

**Sponsor co-stimulation gate (HARD REJECT, not deduct).** A board paper without explicit sponsor co-signal on *this version* is not a neutral miss — it induces anergy. The audience trains a discount on future versions of this topic. Biology: MHC-II Signal 1 (peptide presentation) without B7→CD28 Signal 2 (co-stimulation) produces tolerance, not immunity. Translation: paper without comms-layer = anergy. Confirm `sponsor_co_signal:` evidence is present before any senior send. Cover note + back-channel ARE the co-stimulation, not a soft layer.

**Anergy check.** If this topic was previously presented to this audience without action, the current version requires *more* co-stimulation than baseline, not equal. Each unsponsored repeat compounds the discount. Two-strike rule: v_n unsponsored and didn't land → v_n+1 needs additional sponsor signal beyond what would have sufficed cold.

**Receptor-class fidelity (cross-presentation guard).** Read the paper as a hostile reader operating in attribution / blame / budget-contraction mode. Which decision class does it route to under that read — deliberation (intended) or kill-pathway (cross-presented)? Biology: DCs can route exogenous antigen onto MHC-I → CD8 kill instead of MHC-II → CD4 deliberate; same content, opposite receptor, opposite decision. Triggers for cross-presentation: paragraphs naming individuals/teams adjacent to the gap, passive-voice failure descriptions, gap-without-owner framings, accountability-shaped sentences in a deliberation paper. Mechanistic backing for `feedback_carve_out_language_in_stakeholder_papers.md`.

## Related

- **`induction`** — when domain auto-detects to `paper` / `executive` (board, OpCo, AIRCo, committee), load the `induction` principles as the high-weight criteria spine: decision asked, sponsor pre-aligned, dissent absorbed, recommendation-first sequence, no buried ask, no options-without-recommendation, no unsourced top-line claim. A paper that fails any of these is `needs_work` regardless of prose quality.

## Motifs
- [verify-gate](../motifs/verify-gate.md)
