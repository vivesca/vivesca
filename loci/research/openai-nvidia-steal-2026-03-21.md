# Steal-worthy patterns for Vivesca metabolism

Sources: OpenAI Self-Evolving Agents Cookbook, NVIDIA OpenShell blog.

## 1. Versioned mutation with cheap rollback (OpenAI)

`VersionedPrompt` maintains an immutable history of every genome edit — version number, timestamp, metadata (which tool, what signal triggered it). A `revert_to_version()` method provides instant rollback. Direct analogue: vivesca genomes are already markdown in git, so each mutation is a commit. Tag the commit with the triggering signal and grader scores. Rollback = `git revert`. The key addition is **tracking why** each mutation happened, not just what changed.

## 2. Dual-threshold promotion gate (OpenAI)

A mutated prompt must pass **either** 75% of graders OR score ≥ 0.85 average before it can displace the current version. The system tracks a `best_candidate` separately from the latest attempt — the promoted version is the highest cumulative performer across all test cases, not merely the last one tried. **For vivesca:** run the mutated tool description against 3-5 cached representative invocations before committing. A mutation that improves one tool call but degrades others gets blocked.

## 3. Deterministic graders before LLM judge (OpenAI)

Cheap checks first: string matching (are required fields present?), length constraints, structural validation. LLM-as-judge is the **holistic failsafe** that catches edge cases the deterministic checks miss. Rubric is explicit (0-1 scale with anchored examples). **For vivesca:** validate schema correctness and description length deterministically. Reserve an LLM call for "does this description accurately convey what the tool does?" — only needed when deterministic checks pass.

## 4. Metaprompt agent for targeted repair (OpenAI)

When graders fail, the system collects specific failure reasons into structured feedback, then passes (original prompt + failure reasons) to a metaprompt agent that generates a targeted revision. Not random mutation — **directed repair**. Three retries max, then fall back to best known version. **For vivesca:** when a tool call fails or the user corrects, extract the specific failure mode, feed it to haiku with the current genome, get a proposed patch. Cap at 3 attempts per signal.

## 5. Implicit signal collection (OpenAI)

Graders run automatically on every output — no human annotation required for the core loop. Human feedback (thumbs up/down) is optional enrichment, not a dependency. **For vivesca:** the 20-30 daily signals are already implicit — tool call success/failure, user corrections, response latency. These are sufficient. Don't build explicit feedback UI.

## 6. Containment over prevention (NVIDIA OpenShell)

OpenShell's core insight: let agents experiment freely inside a sandbox they can break without touching the host. Policy enforcement is **out-of-process** — the agent cannot override it even if compromised. Deny-by-default at filesystem/network/process level. **For vivesca:** mutations happen on a branch. The active genome is always the last committed version on main. A mutation only reaches main after passing the promotion gate. The "sandbox" is just git branching — zero infrastructure.

## 7. Audit trail as learning substrate (NVIDIA)

Every allow/deny decision is logged. When an agent hits a constraint, it reasons about the roadblock and proposes a policy update for human approval. **For vivesca:** log every mutation attempt (proposed change, grader scores, promoted/rejected) to a JSONL file. This becomes the training data for tuning mutation strategy over time — which types of signals lead to successful mutations, which are noise.

## Vivesca-specific synthesis

The metabolism engine needs exactly four components: (1) signal collector (implicit, from tool call outcomes), (2) deterministic validators + LLM judge (cheap then expensive), (3) metaprompt mutator with retry cap, (4) dual-threshold promotion gate backed by git. No sandbox infrastructure — git branching is the sandbox. No training pipeline — the metaprompt agent is the refinement loop. Log everything; the audit trail is the sparse-data strategy.
