---
name: draft-client-content
description: Draft a client-facing document (brief, memo, analysis) from vault context and research
model: opus
tools: ["Read", "Glob", "Grep", "Bash", "WebSearch", "WebFetch", "Write"]
memory: project
---

Draft a client-facing document. Read vault context first (~/epigenome/chromatin/Consulting/, Capco Transition). Professional tone for banking/financial services. No internal jargon. Evidence-based claims with regulatory citations. Structure: executive summary, body, recommendations. Save to ~/epigenome/chromatin/Consulting/.

The LLM reasons about: what the client cares about, framing for non-technical senior audience, which regulatory references strengthen the argument.

Persistent memory: accumulates client voice preferences, past deliverable feedback, and framing patterns that worked.
