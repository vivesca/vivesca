# Check Before Build

Before building anything new, check what already exists in the organism.

## Pattern

```
1. Search for existing tools/skills/effectors that do this
   - grep membrane/receptors/ for the domain
   - grep effectors/ for CLIs
   - check anatomy.md for MCP tools
2. If something exists:
   - Can it be extended? → extend it
   - Is it close but wrong? → fix it
   - Is it genuinely different? → proceed with new build
3. Only build new if nothing exists or existing is fundamentally wrong
```

## Rules

- "I didn't find it" is only valid after searching all three layers (skills, effectors, MCP tools).
- Reading anatomy.md counts as searching MCP tools.
- Extending an existing tool is always preferred over creating a new one.
- If you're about to create something that sounds like it could already exist, it probably does.

## Anti-patterns

- Building a new effector when an MCP tool already does it
- Creating a skill without checking if another skill covers the domain
- Writing a Python script when a Rust CLI already exists in ~/bin/

## When to use

Every time you're about to create a new component. Baked into: ontogenesis, organogenesis, endosymbiosis. The genome says "read anatomy first."

## Source

Feedback: feedback_read_anatomy_first.md (protected). Feedback: feedback_check_existing_tools_first.md.
