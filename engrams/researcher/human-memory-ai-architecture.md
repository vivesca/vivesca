# Human Memory Research for AI Architecture (Mar 2026)

## Reliable Sources
- Nature Neuroscience 2023 (CLS generalization): https://www.nature.com/articles/s41593-023-01382-9
- Nature Human Behaviour 2023 (generative model of consolidation): https://www.nature.com/articles/s41562-023-01799-z; PMC: https://pmc.ncbi.nlm.nih.gov/articles/PMC10963272/
- Frontiers Behavioral Neurosci 2025 (top-down vs emotional salience): https://www.frontiersin.org/journals/behavioral-neuroscience/articles/10.3389/fnbeh.2025.1643449/full
- Nature Communications (awake replay): https://www.nature.com/articles/s41467-023-43939-z
- eLife (replay as context-driven reactivation): https://elifesciences.org/reviewed-preprints/99931v1
- Trends in Neurosciences 2025 (engram competition, forgetting): https://www.cell.com/trends/neurosciences/fulltext/S0166-2236(25)00153-5
- PMC (intentional forgetting needs remembering, 2024): https://psycnet.apa.org/record/2024-42584-001
- Frontiers Psychology 2024 (context-dependent memory real world): https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2024.1489039/full
- Memory & Cognition 2024 (encoding variability): https://link.springer.com/article/10.3758/s13421-024-01603-x; PMC: https://pmc.ncbi.nlm.nih.gov/articles/PMC12053356/
- PMC 2025 (evolving engrams, dynamic cueing): https://pmc.ncbi.nlm.nih.gov/articles/PMC12056888/
- PMC 2025 (anticipating reminders harms unaided PM): https://pmc.ncbi.nlm.nih.gov/articles/PMC12262018/
- PMC 2025 (reminders eliminate age-related PM decline): https://pmc.ncbi.nlm.nih.gov/articles/PMC11781985/
- Frontiers Psychology 2024 (cost avoidance drives reminder use): https://pmc.ncbi.nlm.nih.gov/articles/PMC12305806/
- ArXiv Dec 2025 (Memory in Age of AI Agents survey): https://arxiv.org/abs/2512.13564
- ArXiv 2025 (Memory-Augmented Transformers systematic review): https://arxiv.org/html/2508.10824v1
- ScienceDirect 2025 (awake replay, off the clock): https://www.sciencedirect.com/science/article/pii/S0166223625000372

## Key Methodology Notes
- PMC (pubmed central) WebFetch works well for paywalled papers
- Nature.com often 303-redirects; use PMC versions or search result summaries
- Cell.com (Trends Neurosciences) also 303s; use ScienceDirect mirror or search summaries
- ArXiv abstracts fetchable; full papers usually accessible
- Frontiers (frontiersin.org) WebFetch works reliably on full articles
- Best search terms: "engram competition forgetting 2025", "CLS generalization neocortex 2024", "context-dependent memory real world 2024"

## Key Findings Summary (for future cross-reference)

### CLS Theory 2023-2024 Updates
- Consolidation is NOT indiscriminate: only memories that aid **generalization** get promoted to neocortex
- Prediction error drives what gets encoded: high-error (novel) elements stay hippocampus-dependent; schema-consistent elements consolidate rapidly
- Memory becomes progressively schema-distorted over time (gist-based, trades specificity for prediction efficiency)
- 2023 Nature Neurosci: unregulated consolidation causes overfitting — brain regulates to optimize generalization

### Sleep Consolidation Priorities
- Top-down instruction outweighs emotional salience (Frontiers 2025)
- Replay is tagged during waking before sleep: cumulative awake replay events predict what gets sleep-consolidated
- Brief waking rest equivalent to sleep for declarative/procedural memory
- Salient experiences (novel, reward-tagged, high prediction error) get preferential sleep replay
- Without sleep within 24h of learning, any saliency-based consolidation advantage is permanently lost

### Active Forgetting
- Forgetting = engram competition, not erasure: memories persist in latent state; one engram suppresses another
- Intentional forgetting requires intentional remembering first (paradox: must activate to suppress)
- Distinct neural ensembles: Fos-tagged = retrieval, Npas4-tagged = forgetting (2025, dentate gyrus)
- Adaptive function: suppresses obsolete memories when environmental conditions change

### Prospective Memory
- Implementation intentions ("If situation X, then action Y") outperform plain to-do lists by d=0.45-0.51 (meta-analyses)
- Anticipating reminders reduces encoding effort — and causes larger failures when reminders are unavailable
- Offloading to environment (calendar, reminder apps) circumvents capacity limits and is net-positive IF reliable
- "Great Expectations" finding: expecting a reminder changes strategy selection, not just effort level

### Context-Dependent Memory
- Real-world 2024: effect strongest at low-frequency locations (distinctive contexts); weak at habitual locations
- Encoding variability (studying across multiple contexts) benefits recognition when future retrieval context is uncertain
- Dynamic cueing (2025): memories change rapidly toward abstraction; effective cues shift from perceptual to semantic
- Implication: notes should be re-tagged over time as memory consolidates from specific to abstract

### AI Agent Memory Architecture (Dec 2025 survey)
- Three dominant realizations: token-level, parametric, latent memory
- Three function classes: factual, experiential, working (better than long/short-term framing)
- Fast-binding (hippocampal analog) = episodic store; slow-learning (neocortical) = parametric/semantic
- Trend: hierarchical 3-tier (short → mid → long) + Zettelkasten-style dynamic linking
