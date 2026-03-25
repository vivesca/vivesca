# FAQ Semantic Search System - Brainstorm
**Date:** 2026-01-24  
**Status:** Design Complete  
**Context:** Replace iFLYTEK keyword-based chatbot with semantic retrieval system

---

## What We're Building

A **production FAQ retrieval system** that uses semantic search to match user queries to relevant FAQ answers from the bank's knowledge base. The system will:

- Use **LLM for intent classification only** (query understanding)
- Return **exact FAQ content** (no LLM-generated responses)
- Handle **query variations and domain terminology** (e.g., "SWIFT code" queries)
- Meet **sub-30 second response time** requirement
- Support **easy FAQ updates** by business users

**Problem statement:** Current iFLYTEK chatbot cannot answer "SWIFT code" queries because it uses keyword matching and the FAQ information is buried in a question about "remittance templates". Users asking "What is the SWIFT code?" get no answer, even though the information exists in the knowledge base.

---

## Why This Approach

### Chosen: **Semantic Search with Vector Embeddings**

**Architecture:**
1. Convert all FAQ Q&A pairs to vector embeddings (using embedding model)
2. Store embeddings in vector database (Pinecone, Weaviate, or Chroma)
3. User query → embed query → semantic search → return top match FAQ answer
4. Optional: Use LLM to enhance query understanding before retrieval

**Why this solves the SWIFT code problem:**
- Semantic embeddings capture meaning, not just keywords
- "SWIFT code" query will match "remittance templates" FAQ semantically
- Handles synonyms automatically (SWIFT code = BIC code = bank identifier code)

**Why not keyword-based improvements:**
- Fundamental limitation: cannot handle semantic gaps
- Requires manual synonym dictionaries (high maintenance)
- Still fails on paraphrased or novel query variations

**Why not hybrid search (keywords + semantic):**
- More complexity for marginal accuracy gain
- Can add keyword layer later if needed (YAGNI principle)
- Semantic-only is simpler to build and maintain

**Why not full generative chatbot (RAG):**
- User requirement: no LLM-generated responses
- Direct FAQ retrieval is safer, more predictable
- Avoids hallucination risks in banking context

---

## Key Decisions

### 1. **No LLM Response Generation**
- System returns exact FAQ content from knowledge base
- LLM used only for query understanding/enhancement
- Eliminates hallucination risk, ensures compliance

### 2. **Response Format: Answer Only**
- Return the FAQ answer text directly
- Don't show the matched FAQ question
- Cleaner user experience for conversational interface

### 3. **Semantic-First Approach**
- Start with pure semantic search (vector embeddings)
- Add keyword/hybrid layer later if accuracy issues emerge
- Prioritize simplicity and maintainability

### 4. **Vector Database Selection** (TBD)
- Options: Pinecone (managed), Weaviate (self-hosted), Chroma (lightweight)
- Selection criteria: cost, latency, ease of updates, scalability
- Decision deferred to planning phase

### 5. **Embedding Model Selection** (TBD)
- Options: OpenAI ada-002, Cohere embed-v3, local BGE-large
- Selection criteria: quality, cost, latency, privacy requirements
- Need to evaluate Chinese + English performance for bilingual FAQs

### 6. **Retrieval Strategy**
- Return top-1 match by default (highest confidence)
- If confidence score < threshold, escalate to human or return "no match"
- Threshold tuning required during implementation

### 7. **Embedding Strategy: Q&A Together** ✅
- Concatenate question + answer text into single string before embedding
- One embedding vector per FAQ entry
- **Rationale:**
  - Solves SWIFT code problem: answer contains keywords not in question
  - Simpler architecture: single embedding per FAQ, easier maintenance
  - Modern embedding models handle longer text well (512+ tokens)
  - Answer provides semantic context that improves matching
- **Implementation note:** May need to truncate very long answers (>512 tokens)
- **Alternative considered:** Dual embeddings (Q + A separately) - deferred for now (YAGNI)

---

## Open Questions

### Technical Architecture
1. **Which vector database?** Pinecone (ease) vs Weaviate (control) vs Chroma (cost)?
2. **Which embedding model?** Need bilingual (Chinese + English) support
3. **Confidence threshold?** What score constitutes "no match" requiring escalation?
4. **Query enhancement?** Should we use LLM to rephrase queries before embedding?

### FAQ Structure
5. ~~**How to chunk FAQs?**~~ ✅ **RESOLVED:** One embedding per Q&A pair (question + answer concatenated)
6. **Truncation strategy?** If answer > 512 tokens, truncate or chunk? Test full vs partial answer.
7. **Metadata tagging?** Should we tag FAQs by category/product for filtering?
8. **Multilingual handling?** Separate embeddings for EN/ZH or unified multilingual model?

### Production Requirements
8. **Fallback behavior?** What happens when no FAQ matches the query?
9. **Monitoring metrics?** How to track retrieval quality in production?
10. **Update workflow?** How do business users update FAQ content and trigger re-embedding?

### Integration
11. **Frontend integration?** Does this replace iFLYTEK entirely or sit alongside it?
12. **Escalation logic?** When/how to route to human agents?
13. **Existing systems?** How does this connect to Live Chat interface and EIP systems?

---

## Success Criteria

1. ✅ **Response time:** < 30 seconds (target: < 5 seconds for semantic search)
2. ✅ **Query variation handling:** "SWIFT code" queries successfully match remittance FAQ
3. ✅ **No generation:** Returns exact FAQ content, no LLM-generated text
4. ✅ **Easy updates:** Business users can add/modify FAQs without engineering support
5. ⏳ **Accuracy:** To be measured - need baseline metrics from current system

---

## Out of Scope (For Now)

- **Multi-turn conversations:** System handles single queries only (no context memory)
- **Personalization:** No user-specific responses based on account data
- **External data sources:** Only searches FAQ knowledge base, not live banking data
- **Answer synthesis:** No combining information from multiple FAQs
- **Follow-up suggestions:** No "related questions" or conversation flows

These can be added in future iterations if needed (YAGNI principle).

---

## Next Steps

**Proceed to planning** - Run `/workflows:plan` to design:
1. Vector database and embedding model selection criteria
2. FAQ ingestion and chunking strategy
3. API architecture and integration points
4. Evaluation methodology and metrics
5. Deployment and monitoring approach

**Testing strategy:**
- Start with SWIFT code query as test case
- Expand to other domain-specific terms (FPS, eDDA, early uplift)
- Compare retrieval quality vs current iFLYTEK system

---

## Research Context

- Current system: iFLYTEK (pre-LLM, keyword-based, 2-3 min response time)
- FAQ knowledge base: 300+ entries across 11 banking categories
- Known pain points: domain terminology, multi-step processes, contextual queries
- Team: Nicole (business), Derek (sponsor), Terry (data science lead)
- Strategic context: Part of Customer Service Taskforce initiative

**Reference documents:**
- `faq.md` - Complete FAQ knowledge base (11 categories, 300+ entries)
- Meeting notes from Sep 2025 - Performance and accuracy concerns documented
