---
name: ui-transformation
description: UI transformation workflow template for major visual redesigns. This skill should be used when undertaking significant UI changes, landing page redesigns, or visual identity overhauls. Triggers on "redesign", "UI transformation", "visual overhaul", or major frontend changes.
---

# UI Transformation Workflow

A reusable 10-phase workflow for major UI transformation projects. Emphasizes the compound-engineering principle: **80% planning and review, 20% execution**.

## When to Use

- Major visual redesigns (landing pages, dashboards, marketing sites)
- Brand refresh implementations
- UI modernization projects
- Design system migrations
- Any frontend change where "getting it right" matters more than speed

## Core Principle

> Plans are prompts. A good plan enables one-shot implementation.

Invest heavily upfront in understanding requirements, gathering references, and getting feedback. The implementation phase should be straightforward execution of a well-vetted plan.

## The 10-Phase Workflow

### Phase 1: Collaborative Brainstorm
**Command:** `/workflows:brainstorm` or manual dialogue

**Purpose:** Refine the idea through collaborative dialogue before any research.

**Activities:**
- Ask clarifying questions (one at a time, prefer multiple choice)
- Understand: purpose, constraints, success criteria, target audience
- Identify non-negotiables vs nice-to-haves
- Establish visual direction (modern, minimal, bold, playful, etc.)
- Get user alignment on scope

**Output:** Clear feature description with constraints and success criteria

**Tips:**
- Don't skip this phase - misunderstanding requirements is the #1 cause of rework
- Ask "what does success look like?" early
- Identify any existing brand guidelines or design constraints

---

### Phase 2: Reference Gathering
**Purpose:** Ground the design in real-world examples before planning.

**Activities:**
1. **Brand Assets** - Collect existing logos, colors, fonts from the organization
   - Check for brand guidelines documents
   - Look at existing marketing materials
   - Note any protected brand elements

2. **Competitor Analysis** - Screenshot and analyze competitor UIs
   - Use browser automation to capture screenshots
   - Note patterns: layout, typography, color usage, CTAs
   - Identify what works and what to avoid

3. **Inspiration Collection** - Find design inspiration
   - Dribbble, Behance, Awwwards for visual patterns
   - Similar product landing pages
   - Industry-specific UI conventions

4. **Technical Constraints** - Identify framework and component availability
   - What UI framework is in use? (Tailwind, Bootstrap, etc.)
   - Available component libraries
   - Existing design tokens or CSS variables

**Output:** Reference document with screenshots, links, and analysis

**Tips:**
- Actually look at competitor sites - don't assume you know what they look like
- Note specific elements to adopt or avoid ("their CTA placement is effective", "avoid their cluttered hero section")
- Check that inspiration is achievable with available tech stack

---

### Phase 3: Planning
**Command:** `/workflows:plan`

**Purpose:** Transform refined idea + references into a structured implementation plan.

**Activities:**
- The plan command auto-detects if brainstorm happened (uses that context)
- Runs parallel research agents:
  - `repo-research-analyst` - Analyzes existing codebase patterns
  - `best-practices-researcher` - Finds industry standards
  - `framework-docs-researcher` - Gets relevant framework documentation
- Generates plan with appropriate detail level (MINIMAL / MORE / A LOT)

**Output:** Plan file at `plans/<feature-name>.md`

**Structure for UI plans:**
```markdown
## Overview
[What we're building and why]

## Visual Direction
[Design philosophy, references, inspiration]

## Technical Approach
### Component Structure
[Key components to create/modify]

### Styling Strategy
[How colors, typography, spacing will be implemented]

## Implementation Phases
### Phase 1: Foundation
- [ ] Set up design tokens/variables
- [ ] Create base components

### Phase 2: Core UI
- [ ] Hero section
- [ ] Main content areas
- [ ] Navigation changes

### Phase 3: Polish
- [ ] Animations/transitions
- [ ] Responsive adjustments
- [ ] Accessibility checks

## Acceptance Criteria
- [ ] Visual match to design/references
- [ ] Responsive across breakpoints
- [ ] Performance targets met
- [ ] Accessibility standards met
```

---

### Phase 4: Deepen Plan
**Command:** `/deepen-plan plans/<feature-name>.md`

**Purpose:** Enhance each section with parallel research agents for depth.

**Activities:**
- Spawns sub-agents for each plan section
- Discovers and applies relevant skills (frontend-design, dhh-rails-style, etc.)
- Checks `docs/solutions/` for relevant past learnings
- Adds:
  - Best practices for each component
  - Performance considerations
  - Edge cases and gotchas
  - Code examples and patterns

**Output:** Enhanced plan with "Research Insights" sections

**When to use:**
- Complex UI with many components
- Unfamiliar framework/library
- High-stakes project (marketing site, customer-facing)
- When you want maximum grounding before implementation

**When to skip:**
- Simple changes with clear requirements
- Time-sensitive fixes
- Already familiar territory

---

### Phase 5: Plan Review
**Command:** `/plan_review plans/<feature-name>.md`

**Purpose:** Multiple specialized reviewers catch issues before implementation.

**Activities:**
- Runs multiple review agents in parallel
- Default reviewers: DHH, Kieran, Code Simplicity
- For UI projects, also consider:
  - `design-implementation-reviewer`
  - `frontend-design` skill
  - `performance-oracle` (for performance-critical UIs)

**Output:** Consolidated feedback from all reviewers

**Action on feedback:**
- Address critical issues before proceeding
- Document deferred improvements for later
- Get user approval on any scope changes

---

### Phase 6: Apply Feedback
**Purpose:** Incorporate review feedback into the plan.

**Activities:**
- Update plan based on reviewer comments
- Resolve any conflicts between reviewers
- Re-run specific reviewers if major changes made
- Get final user approval

**Output:** Final approved plan ready for implementation

---

### Phase 7: Implementation
**Command:** `/workflows:work plans/<feature-name>.md`

**Purpose:** Execute the plan systematically.

**Activities:**
1. **Setup**
   - Create feature branch (or use git-worktree)
   - Create todo list from plan tasks
   - Set up dev server if needed

2. **Execute**
   - Work through tasks in order
   - Mark todos as complete
   - Check off items in plan file (`[ ]` -> `[x]`)
   - Make incremental commits at logical units
   - Run tests continuously

3. **Quality Check**
   - Run linting
   - Consider reviewer agents for complex changes
   - Verify all acceptance criteria met

**Key practices:**
- Don't reinvent - match existing patterns
- Test as you go, not at the end
- Commit at logical checkpoints

---

### Phase 8: Deploy
**Purpose:** Get changes live for visual testing.

**Activities:**
- Push to remote branch
- Deploy to staging/preview environment
- Verify deployment successful
- Get deployment URL for testing

**Commands vary by platform:**
```bash
# Railway
railway up

# Vercel
vercel --prod

# Heroku
git push heroku feature-branch:main
```

---

### Phase 9: Visual Testing
**Purpose:** Verify implementation matches design intent.

**Activities:**
1. **Browser Automation Testing**
   - Use `agent-browser` or Claude in Chrome
   - Navigate to deployed URL
   - Capture screenshots of key views
   - Compare against design references

2. **Cross-Device Testing**
   - Test responsive breakpoints
   - Check mobile, tablet, desktop views
   - Verify no layout breaks

3. **Interaction Testing**
   - Test hover states, animations
   - Verify links and buttons work
   - Check form interactions

**Common issues to look for:**
- Color/typography mismatches
- Spacing inconsistencies
- Responsive breakpoint issues
- Animation timing problems
- Missing hover/focus states

**Output:** List of bugs/issues to fix

---

### Phase 10: Fix and Iterate
**Purpose:** Address issues found in visual testing.

**Activities:**
- Fix each identified bug
- Commit with clear descriptions
- Redeploy
- Re-test to verify fixes
- Repeat until visual testing passes

**When complete:**
- Create PR with before/after screenshots
- Run `/workflows:compound` to document learnings

---

## Post-Workflow: Document Learnings
**Command:** `/workflows:compound`

**Purpose:** Capture what was learned for future projects.

**Triggers:**
- After saying "that worked", "it's fixed", "looks good"
- When a tricky problem was solved
- Any non-obvious solution worth remembering

**What gets documented:**
- Problem encountered and solution
- Gotchas and edge cases discovered
- Patterns that worked well
- Performance optimizations found

---

## Time Investment Guide

| Phase | Typical Time | Notes |
|-------|--------------|-------|
| 1. Brainstorm | 15-30 min | Don't rush - understanding saves time |
| 2. References | 20-40 min | Actual research, not assumptions |
| 3. Plan | 10-20 min | Automated with research agents |
| 4. Deepen | 15-30 min | Skip for simple projects |
| 5. Review | 5-15 min | Parallel agents, quick |
| 6. Apply Feedback | 10-20 min | Depends on feedback volume |
| 7. Implement | 40-80% of total | Should be straightforward execution |
| 8. Deploy | 5-10 min | Mostly automated |
| 9. Visual Test | 15-30 min | Browser automation helps |
| 10. Fix/Iterate | Variable | Fewer if planning was good |

**Total:** ~80% in phases 1-6 (planning), ~20% in phases 7-10 (execution)

---

## Checklist Summary

### Before Starting Implementation
- [ ] Requirements clarified through dialogue
- [ ] Brand assets collected
- [ ] Competitor/inspiration references gathered
- [ ] Technical constraints identified
- [ ] Plan created and deepened
- [ ] Plan reviewed by multiple agents
- [ ] Feedback incorporated
- [ ] User approved final plan

### During Implementation
- [ ] Working on feature branch
- [ ] Todos tracked and updated
- [ ] Plan checkboxes marked as done
- [ ] Incremental commits at logical points
- [ ] Tests running continuously

### After Implementation
- [ ] Deployed to testable environment
- [ ] Visual testing completed
- [ ] All bugs fixed
- [ ] PR created with screenshots
- [ ] Learnings documented with /workflows:compound

---

## Common Pitfalls

1. **Skipping brainstorm** - "I know what they want" leads to rework
2. **Assuming references** - Actually look at competitors/inspiration
3. **Under-planning** - A thin plan leads to implementation uncertainty
4. **Over-planning** - Know when "good enough" is good enough
5. **Testing at the end** - Visual bugs compound; catch early
6. **Not documenting learnings** - Same problems get solved repeatedly

---

## Related Skills and Commands

- `/workflows:brainstorm` - Phase 1 dialogue
- `/workflows:plan` - Phase 3 planning
- `/deepen-plan` - Phase 4 research enhancement
- `/plan_review` - Phase 5 multi-agent review
- `/workflows:work` - Phase 7 implementation
- `/workflows:compound` - Post-workflow documentation
- `agent-browser` skill - Visual testing
- `frontend-design` skill - UI best practices
