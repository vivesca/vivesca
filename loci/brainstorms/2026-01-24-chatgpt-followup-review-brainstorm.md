---
date: 2026-01-24
topic: chatgpt-followup-review
---

# Review: ChatGPT-Style Follow-Up Conversations for Bank FAQ Chatbot

## What We're Building

Enable the bank FAQ chatbot to maintain conversation context across multiple Q&A turns, allowing users to ask follow-up questions like "tell me more about option 2" without restating previous context.

**Goal**: Demo to call center head showing natural conversation flow.

## Review of Existing AI-Generated Plans

Three plans were created by another AI. Here's the assessment:

### Plan 1: Full Implementation (11 hours)
**File**: `feat-session-memory-followup-conversations-plan.md`

**Scope**:
- Session management with sliding window (5-10 exchanges)
- Hash deduplication for Q&A pairs
- TTL cleanup and session timeout
- Context relevance filtering
- PII redaction in conversation history
- Comprehensive logging and monitoring

**Assessment**: ❌ **Over-engineered**

**Problems**:
- Solving problems that don't exist yet (deduplication, relevance filtering)
- No validation that users actually want this feature
- 11 hours is excessive for a demo feature
- Premature optimization without evidence of need

### Plan 2: Simple Demo (2-3 hours)
**File**: `feat-simple-session-memory-demo-plan.md`

**Scope**:
- Basic in-memory session storage
- Last 2-3 Q&A pairs in context
- Simple list append/trim logic
- No encryption, compliance, or complex security

**Assessment**: ✅ **Exactly right for demo**

**Strengths**:
- Minimal implementation matches demo requirements
- Quick to build and test (2-3 hours)
- Enables natural conversation demonstration
- Can validate the idea before investing more

### Plan 3: Banking Compliance (6 weeks)
**File**: `feat-secure-session-memory-banking-compliance-plan.md`

**Scope**:
- Client-side encryption with HSM key management
- HKMA and PDPO compliance frameworks
- Penetration testing and security audits
- Encrypted session storage with consent flows
- Audit logging and anomaly detection

**Assessment**: ❌ **Premature for demo**

**Problems**:
- 6 weeks of work for a call center demo
- Banking compliance unnecessary for internal demo
- Should only consider if feature proves valuable in pilot
- Classic example of premature optimization

## Why This Approach (Simple Demo)

**Reasoning**:

1. **Demo requirements are minimal** — need to show natural conversation flow, not production security
2. **Validate before investing** — 2-3 hours proves the concept, then decide if it's worth more
3. **YAGNI principle** — don't build compliance infrastructure until you have real users
4. **Risk mitigation** — if demo fails or feature isn't valued, only lost 2-3 hours instead of weeks

**When to revisit complexity**:
- ✅ After demo succeeds and call center head wants pilot
- ✅ After pilot shows users actually use follow-ups
- ✅ After measuring impact on user satisfaction
- ✅ Only then add security/compliance for production

## Key Decisions

**Decision 1: Use simple in-memory storage (not database)**
- **Rationale**: Demo doesn't need persistence across server restarts
- **Trade-off**: Loses context if server restarts, but that's acceptable for demo

**Decision 2: Store last 2-3 exchanges only (not 5-10)**
- **Rationale**: Shorter context is easier to manage and sufficient for demo scenarios
- **Trade-off**: Longer conversations lose older context, but demo conversations are short

**Decision 3: No encryption or compliance features**
- **Rationale**: Internal demo with fake/sanitized data doesn't need production security
- **Trade-off**: Can't use with real customer data, but that's not the goal

**Decision 4: Client-side context injection only (no server storage optimization)**
- **Rationale**: Simple string concatenation is fast enough for demo
- **Trade-off**: Not optimized for production scale, but demo scale is 1-2 concurrent users

## Implementation Summary

**Core changes** (from simple demo plan):

```python
# 1. Extend session to include history
session = {
    "lang": lang,
    "history": [],  # NEW: Simple list of Q&A pairs
}

# 2. Add Q&A to history after each response
def add_to_history(session_id, question, answer):
    if session_id in sessions:
        sessions[session_id]["history"].append({
            "q": question,
            "a": answer,
            "ts": datetime.utcnow().strftime("%H:%M")
        })
        # Keep last 3 exchanges only
        if len(sessions[session_id]["history"]) > 3:
            sessions[session_id]["history"] = sessions[session_id]["history"][-3:]

# 3. Build context string for response generation
def get_context_string(history):
    if not history:
        return ""
    recent = history[-2:]  # Last 2 exchanges
    return "\n\n".join([f"Q: {h['q']}\nA: {h['a']}" for h in recent])

# 4. Use context in response generation
def generate_response(query, session_id):
    session = get_session(session_id)
    context = get_context_string(session.get("history", []))
    full_query = (context + "\n\nCurrent question: " + query) if context else query
    # Rest of FAQ retrieval unchanged
    return existing_faq_retrieval(full_query)
```

**Total implementation**: ~20 lines of actual code changes

## Open Questions

None — requirements are clear for demo scope.

**Future questions** (only if demo succeeds):
- Should production version use database or in-memory?
- What security/compliance features are actually required?
- How long should sessions persist?
- Should we track conversation analytics?

## Next Steps

→ **Proceed directly to implementation** using the simple demo plan (`feat-simple-session-memory-demo-plan.md`)

**Estimated time**: 2-3 hours total

**Success criteria**:
- ✅ Can demonstrate: "What are mortgage rates?" → "Tell me more about option 2"
- ✅ Context maintained for 3-5 exchanges during demo
- ✅ No crashes during 30-minute presentation
- ✅ Simple session reset available for new demo scenarios

**After demo**:
1. Get feedback from call center head
2. If positive, consider small pilot with real users
3. Only then evaluate security/compliance needs

---

## Meta-Lessons: AI Over-Engineering Pattern

This review revealed a common AI failure mode:

**The progression**:
1. Start with reasonable feature request
2. Over-engineer to 11 hours of complexity
3. Self-correct to 2-3 hour simple version ✅
4. Then over-correct to 6 weeks of unnecessary compliance ❌

**Why this happens**:
- AI tries to anticipate all edge cases without user feedback
- Lacks real-world judgment about diminishing returns
- Doesn't distinguish between demo and production requirements

**How to prevent**:
- Always start with simplest implementation that proves the idea
- Add complexity only when evidence shows it's needed
- Question any plan that grows beyond 2x initial estimate
- Ask "what's the minimum to validate this idea?"
