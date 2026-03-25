# Guardrail Regression Testing Landscape (Feb 2026)

## The Gap Probitas Fills
Offline, deterministic, YAML-defined regression testing of AI agent guardrail rules, with a `rules_exercised / total_deterministic_rules` coverage metric and a SHA-256 audit-trail report. No existing tool provides this complete package.

## Candidate Verdicts

### OPA `opa test --coverage` — Closest technical analogue, wrong domain
- Coverage is **line-level** (Rego expression evaluation), NOT rule-level (which named guardrail rules were exercised)
- Fully deterministic, no LLM needed, YAML test data supported via `import data.test_cases`
- Requires learning Rego; no native domain model for tool_call, pii_detect, regex_block, entitlement, budget
- Would need to re-implement the rule engine inside Rego policy files
- **Verdict: Wrong abstraction layer. Could be bent to do this but 5-10x setup cost.**
- Source: https://www.openpolicyagent.org/docs/policy-testing

### NeMo Guardrails (NVIDIA) — No deterministic testing mode
- All evaluation is LLM-dependent; no offline/CI mode
- No coverage metric, no YAML test case schema
- Runtime guardrail library for conversational systems, not a test framework
- **Verdict: Wrong category entirely.**
- Source: https://docs.nvidia.com/nemo/guardrails/latest/evaluation/evaluate-guardrails.html

### Guardrails AI — Enforcement middleware, no testing story
- Library for wrapping LLM calls with validators; not independently testable rule definitions
- No YAML test cases, no coverage metric, no CI-native offline mode
- "Guardrails Index" (Feb 2025) benchmarks guardrail effectiveness, not your specific config
- **Verdict: Different category. Middleware, not a test harness.**

### Promptfoo — Tests LLM outputs / external guardrail services, not rule logic
- Tests whether external guardrail services (Bedrock, Azure Content Filter) respond correctly — still calls those services
- No "guardrail coverage" metric; focus is comparative benchmarking
- No concept of tool_call.args, metadata.role, estimated_cost as first-class inputs
- **Verdict: Adjacent but orthogonal. Tests external service behavior, not your own rule correctness.**
- Source: https://www.promptfoo.dev/docs/guides/testing-guardrails/

### LangSmith — Observability/eval platform, wrong execution model
- Requires running the agent (requires LLM calls); evaluates agent behavior over time
- No YAML-defined policy rules; no guardrail coverage metric
- Managed SaaS, not a local CLI
- **Verdict: Different category. Tests agent output quality, not rule correctness.**

### Cedar (AWS) / Bedrock AgentCore Policy — Formal verification, not test-case execution
- Cedar Analysis uses model checking to prove over-permissive policies; not test-case pass/fail
- AgentCore Policy is a runtime enforcement service (AWS), not offline CI
- No YAML test case schema, no coverage metric, requires Cedar language (not probitas YAML)
- **Verdict: Wrong abstraction layer. Formal verification != regression testing.**
- Source: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy.html

### Casbin — Authorization library, wrong domain
- Policy testing = writing unit tests that call the enforcer; no coverage metric, no YAML format
- Domain: application AuthZ (RBAC/ABAC), not AI agent tool call guardrails
- **Verdict: Wrong domain.**

### Avido AI — Closest in intent, different axis
- Tests guardrail robustness via adversarial prompts (red-teaming); calls guardrail services
- No YAML policy test cases; no deterministic rule-level coverage metric; SaaS not CLI
- **Verdict: Tests robustness (does it block attacks?), not correctness (do your rules fire when they should?).**
- Source: https://avidoai.com/blog/llm-guardrail-testing

### "Just use pytest" — DIY version of probitas
- CAN achieve same outcome with custom conftest fixtures + coverage plugin
- Missing out of the box: guardrail coverage metric, YAML test cases, SHA-256 audit bundle, `kind: semantic` carve-out
- Probitas is the prebaked domain-specific version
- **Verdict: Real alternative for teams willing to build it. Probitas saves ~afternoon of setup + is readable by non-engineers.**

### APort — Watchlist; enforcement focus only
- Intercepts every AI agent tool call against versioned policy at ~40ms; enforcer not tester
- No regression testing mode documented; marketed via CTF challenge (late 2025)
- **Verdict: Monitor for whether a testing mode emerges.**

## Key Differentiators That Don't Exist Elsewhere
1. `rules_exercised / total_deterministic_rules` as a named metric — unique
2. `kind: semantic` explicit carve-out from coverage — honest; unique
3. YAML-native policy AND tests (same schema as frenum) — no Rego, no code
4. First-class domain model: tool_call, metadata.role, metadata.estimated_cost, pii_detect, regex_block, entitlement, budget
5. SHA-256 evidence bundle (policy hash + results hash) — audit trail for compliance

## Reliable Sources for This Domain
- openpolicyagent.org/docs/policy-testing — authoritative for OPA
- docs.nvidia.com/nemo/guardrails — authoritative for NeMo
- guardrailsai.com/docs — authoritative for Guardrails AI
- promptfoo.dev/docs — authoritative for Promptfoo
- avidoai.com/blog — best single article on the testing gap in financial services
- budecosystem.com/llm-guardrails-guardrail-testing-validating-tools-and-frameworks/ — good survey article

## Methodology Notes
- Search for "guardrail coverage" + "guardrail regression testing" surfaces probitas itself (PyPI) — confirms no prior art with this exact framing
- OPA coverage docs: fetch openpolicyagent.org/docs/policy-testing directly; WebFetch works
- NeMo eval docs: fetch docs.nvidia.com/nemo/guardrails/latest/evaluation/ directly; WebFetch works
- Promptfoo guardrail docs: fetch promptfoo.dev/docs/guides/testing-guardrails/ directly; WebFetch works
- Bedrock AgentCore: WebFetch on docs.aws.amazon.com works but content sparse (preview product)
