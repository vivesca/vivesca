---
module: Context Management
date: 2026-01-25
problem_type: workflow_issue
component: vault
symptoms:
  - "Asked Terry for context that was already in vault"
  - "Redundant questions about known contacts/companies"
  - "Wasted conversation turns on discoverable information"
root_cause: missing_context
resolution_type: process_change
severity: medium
tags: [vault, context, search-first, efficiency]
---

# Check vault before asking for context

## Problem

Claude asks Terry "who is X?" or "what's the context for Y?" when the answer is already in the vault. This wastes Terry's time and breaks flow.

## Symptoms

- Terry responds with "it's in the vault"
- Answer was in a note Claude could have searched
- Unnecessary back-and-forth

## Root Cause

Defaulting to asking rather than searching. The vault is the shared memory—Claude should use it.

## Solution

Before asking about a person, company, or context:

1. **Search the vault first**:
   ```
   Grep: pattern="PersonName" path="/Users/terry/code/vivesca-terry/chromatin"
   ```

2. **Check Active Pipeline** for job-related context

3. **Check linked notes** from any matching results

4. **Only ask if genuinely not found**

## Applies To

- "Who is [name]?"
- "What's the context for [company]?"
- "When did we discuss [topic]?"
- Any question about Terry's situation or history

## Prevention

Build the reflex: "Can I find this in the vault?" before "Should I ask Terry?"

The vault exists precisely so Claude can maintain context across sessions. Use it.
