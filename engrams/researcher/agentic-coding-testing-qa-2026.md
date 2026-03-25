---
name: Agentic Coding Testing & QA Best Practices (2026)
description: Testing strategies, TDD patterns, and quality assurance frameworks when AI agents write all the code and humans don't read it
type: reference
---

# Agentic Coding Testing & QA — Mar 2026

## Core Verdict
Testing IS the differentiator between vibe coding and agentic engineering (Osmani, Karpathy, Willison — all converge on this). Without automated tests, agents "cheerfully mark work complete despite broken code." With them, agents iterate in a loop until green = reliable system from unreliable agent.

## Key People / Sources
- **Simon Willison** — simonwillison.net/guides/agentic-engineering-patterns/ (TDD patterns, "first run the tests", "vibe engineering" Oct 2025)
- **Addy Osmani** — addyosmani.com/blog/agentic-engineering/ + 80% problem substack
- **Andrej Karpathy** — coined "agentic engineering" Feb 2026; "tests are how you turn unreliable agents into reliable systems"
- **Tweag Agentic Coding Handbook** — tweag.github.io/agentic-coding-handbook/
- **Nizar's Blog** — nizar.se/agentic-tdd/ (pre-commit hooks pattern)
- **alexop.dev** — isolated subagent TDD with context separation

## Testing Patterns (Ranked by Practical Value)

### 1. Red/Green TDD First
- Write tests BEFORE prompting the agent to implement
- Confirm tests FAIL before implementation (critical — skip this and you get tests that always pass)
- Prompt shorthand: "Build X. Use red/green TDD." — "every good model understands this"
- Tests serve as precise specifications — replace vague natural language with `it('should return only valid emails from a mixed list')`

### 2. "First Run the Tests" Pattern (Willison)
- For existing codebases: literally prompt "First run the tests" before any change
- Forces agent to discover test infrastructure, assess scale, establish testing mindset
- Makes agents more likely to write tests for subsequent changes

### 3. Context-Isolated Subagent TDD (advanced)
- Problem: single context window prevents true TDD — model subconsciously designs tests around anticipated impl
- Solution: separate subagents for each phase (Test Writer / Implementer / Refactorer)
- Each agent sees only what it needs — test writer has no implementation context
- Result: ~84% skill activation vs ~20% in single-context approach

### 4. Pre-Commit Automation Gates
- Formatting + linting + unit tests + integration tests all run on pre-commit
- Agent cannot "complete" task without passing gates
- Keeps agent accountable without human reviewing every line

### 5. Fresh-Context Self-Review (Osmani)
- Have the model review its OWN output with a clean context window
- Catches its own mistakes before human review
- Cheap — same model, no human time

### 6. Spec-First / Declarative Specification
- Spend 70% of effort defining success criteria upfront
- AGENTS.md / CLAUDE.md as "project constitution" — agents reference constantly
- Better specs → better outputs → fewer test failures

## "Trust But Verify" in Practice
- Version control isolation: agent works on branch, never touching main
- Diff review (NOT full code review) — humans review diffs, not full files
- CI/CD as verification layer: tests, type checks, linting all run automatically
- Preview environment deployment before production
- Commit frequently — creates natural audit trail and rollback points

## The 80% Problem (Osmani)
- Agents reach 80% quickly then stall OR silently produce wrong final 20%
- Nature of errors has changed: not syntax bugs but conceptual mistakes
  - False assumptions propagated throughout features
  - Over-engineered abstractions
  - Hallucinated conditions (e.g., `if age == 43` inserted to pass a test)
  - Missing authorization checks — "hallucinated bypass"
- Comprehension debt: developers rubber-stamp code they can't write from scratch

## Security-Specific Risks (Not Caught by Unit Tests)
- 45% of AI-generated code contains OWASP Top-10 vulnerabilities (CodeRabbit, Dec 2025)
- 61% functionally correct, only 10.5% secure (arxiv:2512.03262 benchmarking)
- 2.74x higher security vulnerability rate vs human-written code
- Hallucinated dependencies — attacker-registered packages
- Authorization logic especially vulnerable — single hallucinated condition bypasses security controls
- Mitigation: static analysis + SAST tools in CI pipeline, not just unit tests

## For CLI Tools Specifically
- Golden path tests: does the happy path work end-to-end?
- Smoke tests: does `tool --help` return without crashing? Does `tool <basic command>` produce expected output?
- Integration tests over unit tests for CLI — test the CLI surface, not internal functions
- Type checking (if TypeScript/Rust) catches a large class of agent errors for free

## What Does NOT Work
- Asking agent to "add tests" without specifying what to test → tests that always pass
- Single assertion-less test names → ambiguous targets for agent
- Full code review of all agent-written code → not scalable, defeats the point
- Relying on agent's own claim that "tests pass" without running them yourself in CI

## Key Misinformation to Watch
- "AI coding is production-ready" — 45% vulnerability rate says otherwise without QA layer
- "TDD slows down agents" — opposite is true; tests accelerate because they define the target
- Vendor claims about correctness rates vary wildly based on benchmark used

## Sources
- simonwillison.net/guides/agentic-engineering-patterns/red-green-tdd/
- simonwillison.net/guides/agentic-engineering-patterns/first-run-the-tests/
- simonwillison.net/2025/Oct/7/vibe-engineering/
- addyosmani.com/blog/agentic-engineering/
- addyo.substack.com/p/the-80-problem-in-agentic-coding
- tweag.github.io/agentic-coding-handbook/WORKFLOW_TDD/
- nizar.se/agentic-tdd/
- alexop.dev/posts/custom-tdd-workflow-claude-code-vue/
- arxiv.org/abs/2512.03262 (Is Vibe Coding Safe? benchmarking)
- missing.csail.mit.edu/2026/agentic-coding/
