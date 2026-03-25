# Skill + CLI Boundary Pattern

When a skill needs both LLM judgment and deterministic logic (scheduling, state management, library access), split into two components with a clear contract.

## The Split

| Component | Owns | Examples |
|-----------|------|---------|
| **Skill** (`.md`) | LLM judgment — generation, evaluation, pedagogy, natural language | Question generation, answer evaluation, explanations |
| **CLI** (`.py`) | Deterministic logic — scheduling algorithms, atomic state updates, library access | FSRS spaced repetition, session planning, composition guards |

## Design Rules

1. **CLI outputs a plan, skill executes it.** The CLI's `session` command returns structured data (topics, modes, source file locations). The skill reads this and acts on it. Clean contract = less prompt engineering.

2. **Strip CLI to minimum commands.** If Claude can do it natively (read files, grep, basic math), don't put it in the CLI. Only CLI what needs a library (FSRS) or atomicity (update JSON + markdown in one operation).

3. **Co-locate in one repo.** Skill + CLI + data schema docs in one place (`~/garp-rai/`). Symlink into `~/skills/` and `~/scripts/` for discoverability.

4. **Skill documents all components.** The skill file is the entry point — it should reference the CLI commands, data files, and their relationships. Reader should understand the full system from the skill alone.

## Anti-patterns

- **CLI doing LLM work:** Don't template questions in Python. Let the skill (with full context) generate them.
- **Skill doing scheduling math:** Don't parse FSRS intervals in the prompt. Let the CLI compute and output "drill M3-fairness-measures, read lines 45-90 of Module 3".
- **AskUserQuestion for formulaic choices:** If the skill can infer the answer (confidence from answer quality), don't interrupt the user with a menu.

## Origin

Built during GARP RAI quiz refactor (Feb 17, 2026). Monolithic 366-line skill → 118-line skill + 454-line CLI. The skill got 3x shorter and more reliable.
