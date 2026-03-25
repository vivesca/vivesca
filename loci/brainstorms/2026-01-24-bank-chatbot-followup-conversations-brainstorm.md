---
date: 2026-01-24
topic: bank-chatbot-followup-conversations
---

# Bank FAQ Chatbot Follow-up Conversations

## What We're Building

Enable the bank FAQ chatbot to handle follow-up conversations by maintaining session context, allowing customers to ask related questions without restating previous information. Currently, the chatbot only supports single Q&A interactions.

## Why This Approach

We chose **Session Memory with Context Window** over more complex alternatives because:
- It provides immediate user benefit with minimal complexity
- Follows established chatbot patterns that users expect
- Can be implemented quickly and iterated upon
- Addresses the core limitation (single Q&A only) directly

## Key Decisions

- **Session-based memory**: Store last 5-10 Q&A pairs during active user session
- **Context window**: Use recent conversation as context for generating responses
- **Session timeout**: Clear memory after reasonable inactivity period (e.g., 30 minutes)
- **No persistent storage**: Keep implementation simple and privacy-focused

## Open Questions

- What is the optimal context window size (5, 10, or more Q&A pairs)?
- How should we handle session timeout and memory clearing?
- Should we prioritize certain types of banking information in context?
- How will we measure user satisfaction improvements?

## Next Steps

→ `/workflows:plan` for implementation details including:
- Session management architecture
- Context storage mechanism
- Integration with existing chatbot responses
- Testing strategy for multi-turn conversations