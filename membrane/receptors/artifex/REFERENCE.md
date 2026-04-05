# Artifex Extended Reference

Detailed patterns for principles 20-23. Source: evaluation of vercel-labs/agent-skills (2026-04-05).

## Knowledge-Base Skill Architecture

### Directory Structure

```
skills/
  my-guidelines/
    SKILL.md              # Lean index (~150 lines): When to Apply, Quick Reference table, How to Use
    AGENTS.md             # Compiled flat doc: all rules expanded inline (build artifact, not hand-written)
    metadata.json         # Version, author, date, abstract, references
    rules/
      _sections.md        # Category taxonomy: number, title, impact, description
      _template.md        # New rule scaffold
      async-parallel.md   # Individual rule: frontmatter + explanation + examples
      async-defer.md
      bundle-imports.md
      ...
    references/
      implementation.md   # Step-by-step workflow (consult from SKILL.md)
      css-recipes.md      # Paste-targets: exact code to copy, not explanation
      patterns.md         # Extended patterns and edge cases
```

### Three audiences, three files

| File | Audience | Content |
|------|----------|---------|
| `SKILL.md` | Smart agents (CC, Gemini) | Lean index. Agent reads this, follows links to rules/ on demand |
| `AGENTS.md` | Flat-context agents (Codex, Cursor, ribosome) | Everything compiled inline. No progressive disclosure needed |
| `rules/*.md` | Humans, validators, eval extractors | Atomic units. Git-diffable, individually testable |

### Build pipeline

```
rules/*.md (source)
  -> parse frontmatter + content
  -> validate (title, impact, examples, section mapping)
  -> group by section (filename prefix -> _sections.md number)
  -> sort within sections (impact first, then alphabetical)
  -> compile:
       --compact  -> ### headings + - bullets (coaching format)
       --full     -> #### per rule with impact tags
       --critical -> CRITICAL+HIGH only (small context windows)
  -> extract test cases:
       Incorrect/Correct code blocks -> JSON eval dataset
```

Reference implementation: `~/germline/effectors/compile-coaching`

### Rule file format

```markdown
---
title: Promise.all() for Independent Operations
impact: CRITICAL
impactDescription: 2-10x improvement
tags: async, parallelization, promises
---

## Promise.all() for Independent Operations

When async operations have no interdependencies, execute them concurrently.

**Incorrect (sequential execution, 3 round trips):**

```python
user = await fetch_user()
posts = await fetch_posts()
comments = await fetch_comments()
```

**Correct (parallel execution, 1 round trip):**

```python
user, posts, comments = await asyncio.gather(
    fetch_user(), fetch_posts(), fetch_comments()
)
```
```

Key conventions:
- **Impact levels:** CRITICAL, HIGH, MEDIUM, LOW
- **impactDescription:** Quantified where possible ("reduces retry rate from 3 to 1")
- **Filename prefix** maps to section: `async-` -> Eliminating Waterfalls, `code-` -> Code Patterns
- **Incorrect/Correct labels** must use those exact words for test case extraction
- **Tags:** freeform, used for search/filtering

### Structural validation

Every rule file must have:
- Non-empty `title` in frontmatter
- `impact` from the valid set (CRITICAL/HIGH/MEDIUM/LOW)
- Filename prefix that maps to a section in `_sections.md`
- Non-empty body

Run as pre-commit hook or before compilation. Catches drift before it causes silent failures.

### Test case extraction

Incorrect/Correct code blocks become eval test cases:

```json
{
  "ruleTitle": "Promise.all() for Independent Operations",
  "impact": "CRITICAL",
  "type": "bad",
  "language": "python",
  "code": "user = await fetch_user()\nposts = await fetch_posts()"
}
```

Feed through peira: give the "bad" example to the GLM, measure whether it produces something matching the "good" pattern. This turns coaching from vibes into measured compliance.

### Anti-pattern catalog

Separate from individual rules. Rules teach what's correct. The anti-pattern catalog teaches failure modes that occur *despite* knowing the correct rule.

Add as `rules/_common_mistakes.md` (excluded from compilation by `_` prefix) or as a dedicated section in SKILL.md.

Format:
```markdown
**Mistake:** Directional VT in a layout
**Why it fails:** Layouts persist across navigations -- enter/exit never fires
**You'd think:** "I'll put the VT wrapper in the shared layout for DRY"
**Instead:** Place it in each page component
```

The "You'd think" line is what makes this useful -- it names the reasoning that leads to the mistake.

## State-Gather-Then-Branch Architecture

The deploy-to-vercel skill demonstrates this:

```markdown
## Step 1: Gather Project State

Run all four checks before deciding which method to use:

1. `git remote get-url origin` -- has git remote?
2. `cat .vercel/project.json` -- linked to Vercel?
3. `vercel whoami` -- CLI authenticated?
4. `vercel teams list` -- which teams?

## Step 2: Choose a Deploy Method

### Linked + has git remote -> Git Push
(self-contained instructions)

### Linked + no git remote -> `vercel deploy`
(self-contained instructions)

### Not linked + CLI authenticated -> Link first, then deploy
(self-contained instructions)

### Not linked + CLI not authenticated -> Install, auth, link, deploy
(self-contained instructions)

### No-Auth Fallback
(self-contained instructions)
```

Properties that make this work:
1. **State checks are parallel and cheap** -- run all before deciding
2. **Each branch is self-contained** -- no "see above" or cross-references
3. **Branches are exhaustive** -- every state combination has a path
4. **Fallback is explicit** -- the last branch handles the worst case

Apply to any skill with 3+ execution paths. Avoid nested if/else prose -- use ### headings as the branching mechanism.

## References Subdirectory Patterns

### Explanation vs Recipe

| Type | Content | Example |
|------|---------|---------|
| SKILL.md | When and why | "Use slide animations for hierarchical navigation" |
| references/implementation.md | Step-by-step how | "Step 1: Audit. Step 2: Add CSS. Step 3: Wire up" |
| references/recipes.md | Exact paste-targets | "Copy this CSS block into your stylesheet" |
| references/patterns.md | Edge cases and variations | "For same-route segments, use key + name + share" |

Rules: SKILL.md says **"do not write your own animation CSS"** and points to the recipes file. The recipe is canonical -- the agent copies it verbatim. This separation means the recipe can be validated independently and the SKILL.md stays scannable.

### Audit-First Implementation

For skills that modify existing code/systems, Step 1 is always an audit that produces a map:

```markdown
## Step 1: Audit

Scan the codebase and produce a map:

| Current State | Target State | Pattern to Apply |
|---------------|-------------|-----------------|
| /             | /detail/[id] | directional slide |
| /tab/[a]      | /tab/[b]     | crossfade |
```

Every subsequent step references this map. The map IS the spec -- if it's wrong, the implementation will be wrong regardless of execution quality.

Apply to: transposase renames, regulatory audits, migration skills, any skill that transforms existing state.
