# LLM Instruction Compliance Hierarchy

Discovered 2026-03-18 during skill flywheel build. Topica (centralised mental model reference) had 1 invocation in 14 days despite being referenced by 13 skills. The "consult topica" instruction was consistently skipped.

## The hierarchy (most to least reliable)

1. **Hooks** (mechanical enforcement) — can't be skipped, code blocks/nudges. But shallow: can only match on tool name, file path, regex. Can force Claude to *say* something but not to *think* about it.

2. **Inline instructions** (at point of use) — closer to where the decision happens, lower activation energy than a cross-reference. But still skippable — an instruction in a skill file has no enforcement.

3. **Centralised reference** ("consult X") — requires noticing the instruction, loading a second skill, scanning a table, applying it. Each step is a dropout point. Empirically: ~0% compliance.

4. **Nightly reconciliation** (delayed but comprehensive) — catches what slipped through all layers. Not real-time, but covers blind spots the others can't see.

## Implications

- If you need an LLM to *do* something reliably → hook.
- If you need it to *consider* something → inline at point of use + hook to verify it considered it.
- Centralised reference docs are maintenance artifacts, not delivery mechanisms. They're useful as source-of-truth for humans maintaining the system, not for LLMs consuming instructions.
- The combination of all three layers + reconciliation is the best achievable. No single mechanism is sufficient.

## The biological analogy

- Hooks = reflexes (fast, mechanical, can't be overridden)
- Instructions = hormones (suggestive, influence behaviour, can be ignored)
- Nightly reconciliation = conscious reflection (slow, comprehensive, catches what automatic systems missed)
- Complex organisms need all three. So do complex AI tooling stacks.

## Related

- `gyrus` skill — flywheel design pattern
- `mimesis` skill — cross-domain analogical transfer
- `taxis` skill — enforcement architecture
- `~/docs/solutions/enforcement-ladder.md` — escalation path for repeated violations
