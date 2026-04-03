---
name: judge
description: "Review client-facing deliverables (SOWs, proposals, decks, reports) against quality criteria before sending. NOT for code review."
user_invocable: false
---

# Judge Skill

Reusable quality review for skill outputs. Call this after generating drafts, analyses, or any output that benefits from a second pass.

## Trigger

Called by other skills, not directly by user. Skills invoke this at the end of their workflow:

```
Execute main task → Call /judge → Iterate if needed → Output
```

## Inputs

- **output** — The content to judge (required)
- **goal** — What the output was supposed to achieve (required)
- **domain** — Which criteria to use: `outreach`, `job-eval`, `technical`, `article`, `default` (optional, auto-detect if not specified)
- **max_iterations** — How many revision cycles before giving up (default: 2)

## Workflow

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
| outreach, message, linkedin, email, networking | outreach |
| job, role, position, application, evaluate | job-eval |
| code, technical, implementation, architecture | technical |
| article, blog, essay, writing | article |
| (none matched) | default |

## Integration Example

Other skills call judge like this:

```markdown
## Workflow (in /outreach)

1. Gather context about recipient
2. Draft personalized message
3. **Review with judge:**
   - Call judge with output=draft, goal="personalized networking message", domain="outreach"
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
