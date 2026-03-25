---
title: Anthropic Official Skill Authoring Best Practices
category: skills
tags: [skills, authoring, best-practices, anthropic]
source: obra/superpowers v4.3.0 (writing-skills/anthropic-best-practices.md)
date: 2026-02-14
---

# Anthropic Skill Authoring Best Practices

Extracted from official Anthropic documentation, bundled in obra/superpowers.

## Key Principles

### Context window is a public good
Only add context Claude doesn't already have. Challenge each piece: "Does Claude really need this explanation?"

### Degrees of freedom
Match specificity to task fragility:
- **High freedom** (text instructions): Multiple valid approaches, context-dependent
- **Medium freedom** (pseudocode/templates): Preferred pattern exists, some variation OK
- **Low freedom** (exact scripts): Fragile operations, consistency critical

Analogy: Narrow bridge with cliffs = low freedom. Open field = high freedom.

### Progressive disclosure
- SKILL.md = overview + navigation (loaded when triggered)
- Reference files = loaded on-demand (zero context cost until read)
- Keep SKILL.md body under 500 lines
- References should be one level deep (no A→B→C chains)
- Long reference files (100+ lines): add table of contents at top

### CSO (Claude Search Optimization)
- Description = WHEN to use (triggering conditions only)
- Never summarize workflow in description (Claude shortcuts it)
- Use concrete triggers, symptoms, situations
- Write in third person
- Include error messages, symptoms, tool names as keywords

### Token efficiency
- getting-started skills: <150 words
- Frequently-loaded skills: <200 words
- Other skills: <500 words
- Move flag details to `--help`, use cross-references, compress examples

### Testing
- Test with all models you plan to use (Haiku needs more guidance, Opus less)
- Create 3+ evaluations before writing extensive docs
- Evaluation-driven: identify gaps → create tests → establish baseline → write minimal skill → iterate
- Observe how Claude navigates skills (unexpected paths, missed connections, ignored content)

## Patterns

### Template pattern
Provide output format templates. Match strictness to requirements.

### Examples pattern
Input/output pairs for output quality. Better than descriptions alone.

### Conditional workflow
Guide through decision points: "Creating new? → Creation workflow. Editing? → Editing workflow."

### Feedback loops
Run validator → fix errors → repeat. Greatly improves output quality.

### Verifiable intermediate outputs
Plan-validate-execute: create structured plan file → validate with script → execute.
Use for: batch operations, destructive changes, complex validation, high-stakes.

## Anti-patterns
- Time-sensitive information (use "old patterns" section with `<details>`)
- Inconsistent terminology (pick one term, use throughout)
- Too many options (provide default + escape hatch)
- Deeply nested references (keep one level deep)
- Assuming tools are installed (be explicit about dependencies)
- Windows-style paths (always forward slashes)

## Source
Full document at `~/code/superpowers/skills/writing-skills/anthropic-best-practices.md`
