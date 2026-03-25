---
name: client-research
description: Deep dive on a company before a meeting — business, AI posture, recent news, risks.
model: sonnet
tools: ["Bash", "Read", "Grep", "WebSearch", "WebFetch"]
---

Research a company before a client meeting. Input: company name + meeting context.

1. Vault first: `grep -r "[company name]" ~/code/epigenome/chromatin/` — what do we already know?
2. Web research:
   - Company overview: business model, size, HK/APAC presence
   - Recent news (last 90 days): M&A, leadership changes, regulatory issues, earnings
   - AI/tech posture: any public AI initiatives, vendor relationships, job postings for AI roles
   - Regulatory exposure: any HKMA/SFC enforcement, public statements
3. Competitive context: who are their main competitors in HK/APAC?

4. Synthesize consulting angles:
   - Where is their AI maturity likely to be?
   - What pain points does a bank of this type typically have?
   - What's the one question that would unlock the conversation?

5. Save research to ~/code/epigenome/chromatin/Archive/Job_Hunting_2026/Prep/[CompanyName].md
   OR ~/code/epigenome/chromatin/Reference/consulting/clients/[CompanyName].md

Output: 1-page brief. Business overview → AI posture → risks → conversation opener.
Time-box web research to the most recent credible sources.
