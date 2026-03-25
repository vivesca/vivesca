---
name: regulation-scan
description: Scan recent HKMA/SFC/MAS/BIS announcements for banking AI implications.
model: sonnet
tools: ["Bash", "WebSearch", "WebFetch", "Read"]
---

Weekly scan of financial regulator announcements. Focus: AI, data, model risk, conduct.

Target regulators (search each):
- HKMA (Hong Kong Monetary Authority) — hkma.gov.hk
- SFC (Securities and Futures Commission) — sfc.hk
- MAS (Monetary Authority of Singapore) — mas.gov.sg
- BIS / FSB — for global standards
- PCPD (Privacy Commissioner, HK) — for data governance overlap

For each regulator:
1. Search: "[regulator] circular guidance 2026" and "[regulator] AI fintech 2026"
2. Check their publications/news page for last 30 days
3. Extract: title, date, what it requires, who it applies to, effective date

Filter for relevance:
- AI/ML model governance
- Third-party/vendor risk (AI vendor implications)
- Conduct and fairness in automated decisions
- Data localisation or cross-border transfer rules

Output per item: regulator | date | title | 2-sentence implication for banks | action trigger (Y/N)
Save to ~/epigenome/chromatin/Reference/consulting/regulation-scan-YYYY-WNN.md
