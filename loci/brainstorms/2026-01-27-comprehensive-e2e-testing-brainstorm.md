---
date: 2026-01-27
topic: comprehensive-e2e-testing
---

# Comprehensive E2E Testing with Scripted Playbooks

## What We're Building
A robust, automated end-to-end (E2E) testing suite that simulates real user behavior on the production `inmotion-faq.vercel.app` site. The system will use "Conversation Playbooks" (pre-defined multi-turn dialogues) executed via `agent-browser` and verified by **Claude 3.5 Sonnet** (as the "Judge") to ensure both technical availability and logical correctness.

## Why This Approach
The user is experiencing "silent failures" where tests pass locally but the production app either errors out ("AI service unavailable") or provides incorrect logic during manual testing. 
- **Scripted Playbooks (Approach 1)** provide a deterministic safety net for known "hard cases."
- **Production Testing** ensures we catch environment-specific issues like API timeouts, cold starts, or environment variable mismatches.
- **LLM-as-a-Judge** (specifically **Opus 4.5** or **Sonnet 3.5**) is required because banking queries are nuanced; simple keyword matching cannot verify if a Cantonese explanation of an SME loan is actually correct.

## Key Decisions
- **Execution Tool**: Use the existing `agent-browser` CLI to perform UI actions (typing, clicking, waiting).
- **Test Target**: Run primarily against the **Production** URL (`inmotion-faq.vercel.app`) to catch real-world availability issues.
- **Verification Engine**: Use **Claude 3.5 Sonnet** as the default judge for cost-efficiency, but allow Terry to trigger **Opus 4.5** for high-stakes validation or complex logic checks.
- **Playbook Generation (Opus 4.5)**: Use Opus 4.5 to proactively generate "Adversarial Playbooks"—conversations designed to find edge cases, contrast different phrasing, or stress-test multi-turn logic—before they are added to the permanent suite.
- **Data Format**: Playbooks will be stored in JSON, defining `intent`, `audience` (Retail/SME), and a sequence of `turns` (user query + expected ground truth).
- **Failure Handling**: The suite must explicitly detect "AI service unavailable" messages and flag them as high-priority infrastructure failures.

## Open Questions
- **Trigger Mechanism**: Should this run on every Vercel deployment (CI/CD) or as a manual "sanity check" command Terry runs?
- **Judge Prompting**: How much banking context does the Judge need to accurately grade the bot's answers?
- **Concurrency**: How many playbooks can we run in parallel without hitting rate limits on the live production site?

## Next Steps
→ `/workflows:plan` to design the `tests/e2e_playbooks.json` schema and the `scripts/run_e2e_suite.py` runner.
