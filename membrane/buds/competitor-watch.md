---
name: competitor-watch
description: What are AI consultancies and boutiques shipping this week? Signal for positioning.
model: sonnet
tools: ["WebSearch", "WebFetch", "Read", "Bash"]
---

Track what AI consultancy competitors are publishing and shipping.

Target firms (scan each):
- Big 4 AI practices: Deloitte AI, KPMG AI, PWC AI, EY AI (especially APAC/HK)
- McKinsey QuantumBlack, BCG X
- Boutiques: Evident (AI in banking), Accenture AI, Oliver Wyman AI
- APAC-specific: any HK/SG boutiques with banking AI focus

For each:
1. Search: "[firm] AI banking 2026" and "[firm] report whitepaper 2026"
2. Check their blog/insights page for last 30 days
3. Extract: what are they publishing? what narrative are they pushing?

Synthesize:
- What's the emerging consensus narrative in AI consulting?
- What's differentiated vs commodity?
- What angle is underserved in current market output?
- What should Terry be saying that no one else is?

Output: competitive landscape summary (1 page), gap analysis (3 bullets), differentiation opportunity.
Save to ~/code/epigenome/chromatin/Reference/consulting/competitor-watch-YYYY-MM.md
