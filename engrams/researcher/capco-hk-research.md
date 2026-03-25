# Capco HK Research — Feb 2026

## Key People (Hong Kong office)

| Name | Title | Specialism |
|------|-------|------------|
| James Arnett | Managing Partner, APAC & Middle East | Strategy, wealth management, client relationships |
| John McBain | Partner | Banking, capital markets, M&A, transformation (30+ yrs) |
| Rezwan Shafique | Partner | Wealth management, capital markets |
| Edwin Hui | Executive Director & APAC Data Lead | Data strategy, governance, architecture; ex-Accenture Applied Intelligence HK lead |
| Bertie Haskins | Executive Director & Head of Data, APAC & ME | Data commercialisation, CDO advisory; podcast: Waters Wavelength Ep. 314 (Apr 2025) |
| Dr. Shelley Zhou | APAC ESG Lead | Carbon, climate, ESG; adjunct prof at HKUST |
| Darren Pigg | Partner & APAC Insurance Lead | Insurance |
| Erik Cheung | Managing Principal, APAC Insurance Operations Lead | Insurance operations; AI Association of HK member |

**Note:** No dedicated AI/data MD visible in HK — Edwin Hui + Bertie Haskins cover data across APAC from HK.

## Capco HK Recent Activity

- **HKMA GenAI sandbox:** Capco cited HKMA Dec 2024 inaugural cohort and Oct 2025 second cohort in public articles; no confirmed Capco direct participation in either cohort (client work likely but not publicised).
- **HK Fintech Week:** Capco maintains booth presence (most recent confirmed: 2024 edition). Not a headline speaker in search results for 2024 or 2025.
- **GenAI Journal Edition 60 (2024/2025):** Hosted by HKDCA (HK Data Centre Association) — signal of HK-facing distribution.
- **Wealth management survey (Jan 2025):** James Arnett + Endowus CEO Q&A — survey of 500 HK HNW respondents. Capco's most visible recent HK-facing output.
- **APAC Banking & Payments Trends 2025 (Feb 2025):** References HKMA AI guidelines (Aug 2024) and sandbox (Dec 2024).

## AI/Data Propositions

### GenAI Governance
- Five foundational elements framework (published Nov 2024): Legal/Compliance, Risk/Control, Monitoring, Operating Model, Privacy/Security
- References NIST AI RMF (not HKMA or SR 11-7 explicitly)
- AI Governance Framework: Roles/responsibilities, practices, tools, regulation, responsible AI principles (published Sep 2024)
- **Capco does NOT publicly market Model Risk Management (MRM) using regulatory terminology like SR 11-7** — governance framing is governance/ethics-led rather than quant model risk

### Document Processing (strong signal)
- **Aptus.AI partnership (May 2024):** Regulatory change detection + legal document → machine-readable transformation. Targets banks/insurers. Originally Italy, now global.
- **Center of Regulatory Intelligence (CRI) Data Feed:** In-house NLP/BERT system processing ~193,000 regulatory releases/year; trains on 300K+ records; monthly retraining. RPA + API integration. (Gen AI Regulatory Impact Analysis, Mar 2024)
- **BA Genie:** Internal GenAI tool consuming project documentation + audio/video to generate requirements specs.
- Both the Aptus.AI partnership and CRI feed are live, productised offerings — not thought leadership only.

### Intelligent Automation (adjacent to AIOps)
- Capco has an IA practice focused on regulatory compliance and process automation in FS
- Published piece on operational AI failures in Asia (Edwin Hui, 2022): cites infra constraints, Asian NLP challenges, platform maturity gaps as barriers
- **No explicit "AIOps" branding found** — Capco does not use the term "AIOps" in their public marketing. The operational AI work is framed as "intelligent automation" or "agentic AI."

### Agentic AI (2025 priority)
- Key focus area for 2025: autonomous decision-making, KYC, credit decisions, payments/cash management
- "Confidence-driven Agentic AI" = threshold-based action gating in regulated environments
- Partnership with OpenAI (Beta Services Partner Program) — priority API access

## Responsible AI / Model Risk
- Capco's public positioning is governance/ethics-led (NIST, GDPR, privacy-by-design)
- Bertie Haskins article explicitly references Singapore AI MRM guidelines and HKMA GenAI technical framework as regional standards to meet
- No SR 11-7, no MRM lifecycle framing in public content
- **Key gap Terry can fill:** Capco's governance content is governance-layer only; no published content on quantitative model validation, model monitoring, or MRM lifecycle for ML/GenAI models

## Three Target Topic Overlaps

| Topic | Capco Signal | Strength |
|-------|-------------|----------|
| AIOps | None under that name; "intelligent automation" is the framing | Weak explicit, moderate adjacent |
| Responsible AI / Model Risk | GenAI governance framework, NIST alignment, regional regulatory tracking | Strong governance angle; weak MRM/quant angle |
| GenAI Document Processing | Aptus.AI partnership + CRI Data Feed (both live products) | Strong |

## HKMA GenAI Sandbox — Participant + Peer Mapping (Feb 2026)

Full research note at: `/Users/terry/code/epigenome/chromatin/HKMA GenAI Sandbox Research.md`

### Cohort 1 (Dec 2024, 10 banks)
HSBC, BOCHK, Standard Chartered, CNCBI, CCB Asia, Citibank HK, Dah Sing Bank, Hang Seng Bank, Livi Bank, Societe Generale

### Cohort 2 (Oct 2025 selection, trials early 2026, 20 banks)
Adds: Ant Bank, BoCom HK, BEA, Chiyu Banking, CMB Wing Lung, Fubon Bank HK, ICBC Asia, Industrial Bank, Nanyang Commercial, PAO Bank, Public Bank HK, Shanghai Commercial Bank.
Continuing: HSBC, BOCHK, CCB Asia, Livi Bank, Dah Sing Bank (and StanChart per SCMP).

### Key Named Peers (AI/data leads at sandbox banks)
| Person | Title | Bank | LinkedIn search |
|--------|-------|------|----------------|
| Bojan Obradovic | Chief Digital Officer | HSBC HK | bojanobradovic |
| Kazimierz Kelles-Krauz | MD, Head of Digital Channels and AI, WPB | HSBC HK | — |
| Alex Chen (陳維凌) | Head of Data and Analytics | HSBC HK | alex-wei-ling-chen |
| Martin Qiao | Head of Data Science Solutions, WPB | HSBC HK | martinqiao |
| Edward Wu | Head of Data Science & Governance | BEA | Spoke CDOTrends HK 2025 |
| Yusuf Demiral | Head of Data, Analytics and AI, Wealth | StanChart HK | Joined Jul 2025 |

### Source reliability for HKMA sandbox research
- hkma.gov.hk press releases: authoritative but annex PDFs are binary-encoded and unreadable by WebFetch
- cncbinternational.com/_document/: direct bank press release PDFs — also binary, unreadable
- SCMP, finews.asia, Caproasia: reliable for participant lists and quotes
- thedigitalbanker.com: good for named AI/data exec profiles and awards
- cdotrends.com/event/: speaker profiles = most reliable source for HK-level AI/data named leads
- about.hsbc.com.hk: HSBC HK press releases fetch cleanly

### Methodology notes
- Bank AI lead discovery: "CDOTrends Hong Kong Summit" speaker profiles + fintech news quotes + sandbox press releases (best 3-source combo)
- HKMA PDFs: text PDFs work via WebFetch; binary/compressed PDFs return gibberish — do not retry
- Virtual bank AI leads: almost none are publicly named; CTO is the closest reachable peer

## Sources
- capco.com/intelligence (articles)
- capco.com/about-us/newsroom-and-media (press releases)
- consultancy.asia: Edwin Hui/Rezwan Shafique hire announcement
- waterstechnology.com: Bertie Haskins podcast (Apr 2025)
- theorg.com/org/capco: Erik Cheung org chart
- hkdca.com: Journal 60 PDF distribution (HK signal)
