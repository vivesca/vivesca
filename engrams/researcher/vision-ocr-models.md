# Vision OCR Models Research (Feb 2026)

## Use Case: Clean Printed Book Text from Screenshots

### Key Conclusion
For clear typeset text at 1280x720, **Gemini 2.0 Flash** is the best cost/accuracy ratio among API models. **GOT-OCR 2.0** or **DeepSeek-OCR** are best for high-volume self-hosted. Specialized OCR models beat general VLMs on messy docs but are overkill for clean book text.

### Reliable Sources for this Topic
- reducto.ai/blog/lvm-ocr-accuracy-mistral-gemini: independent head-to-head Mistral vs Gemini with real benchmarks
- arxiv.org/html/2501.00321v2: OCRBench v2 paper — comprehensive leaderboard across 8 OCR tasks
- e2enetworks.com/blog/complete-guide-open-source-ocr-models-2025: self-hosted throughput/cost table (H100 data)
- artificialanalysis.ai/models/deepseek-ocr: DeepSeek-OCR speed and pricing data
- platform.claude.com/docs/en/build-with-claude/vision: authoritative Claude image token formula
- ai.google.dev/gemini-api/docs/pricing: Gemini image pricing (canonical)
- getomni.ai/blog/ocr-benchmark: JS-heavy, Framer site — WebFetch returns no data; use WebSearch instead

### Image Token Costs (verified, Feb 2026)
- **Claude formula:** tokens = (width * height) / 750. 1280x720 = ~1,229 tokens. Images auto-scaled if >1568px on any edge.
- **Gemini formula:** images tiled into 258-token chunks. 1280x720 stays within one tile band. Priced at text input rate.
- **Gemini 2.0 Flash:** $0.10/M input tokens. 1280x720 = ~1,229 tokens = ~$0.000123/image
- **Gemini 2.0 Flash-Lite:** $0.075/M input tokens. Same image = ~$0.000092/image
- **Claude 3.5 Haiku:** $0.80/M input tokens. Same image = ~$0.00098/image (8x more than Flash)
- **Claude 3.5 Sonnet:** $3.00/M input tokens. Same image = ~$0.0037/image (30x more than Flash-Lite)

### Benchmark Data (OCRBench v2, 2501.00321)
- Claude 3.5 Sonnet: 62.2% English text recognition
- GPT-4o: 61.2%
- Gemini Pro: 61.2%
- Ovis2-8B (open source): 73.2% — leads the leaderboard
- Qwen2.5-VL-7B: 68.8%
- Note: OCRBench v2 includes all 8 OCR subtasks (localization + recognition + reasoning). Pure printed-text recognition scores are higher (98-99% reported for top models on clean docs).

### Reducto Head-to-Head (independent benchmark, real-world docs)
- Gemini 2.0 Flash: 80.1% on RD-FormsBench (complex mixed docs with handwriting, tables)
- Mistral OCR: 45.3% on the same — despite Mistral self-reporting 94.89%
- Key insight: vendor benchmarks are on curated datasets; real-world accuracy diverges significantly.

### Self-Hosted OCR Throughput (E2E Networks H100 benchmark)
| Model | Pages/sec | OlmOCR Score | Cost per 1M pages |
|---|---|---|---|
| LightOn OCR | 5.55 | 76.1 | $141 |
| DeepSeek-OCR | 4.65 | 75.7 | $168 |
| PaddleOCR-VL | 2.20 | 80.0 | $355 |
| OlmOCR-2 | 1.78 | 82.4 | $439 |
| Chandra | 1.29 | 83.1 | $605 |

### Model Notes
- **Gemini 2.0 Flash:** Best API option for clean text. Fast, cheap, accurate on clean docs. Thinking variants (2.5) are WORSE at OCR — confirmed by community reports.
- **Gemini 2.0 Flash-Lite:** Slightly cheaper, similar quality for simple text. Worth testing first.
- **Claude 3.5 Haiku:** Good quality but 8x pricier than Flash per image. Better for tasks needing reasoning + extraction combined.
- **GPT-4o-mini:** Not benchmarked directly; inference: similar quality to Haiku, similar pricing. Less proven for document OCR.
- **Mistral OCR:** Self-reported 94.89% but collapsed to 45.3% on independent test. Not reliable.
- **GOT-OCR 2.0:** 580M params, specialized for documents. Low WER on printed text. Self-hostable (MIT). Best for book-page extraction at scale.
- **DeepSeek-OCR:** Oct 2025, 3.3B params, 307 tokens/sec, MIT license. $0.03/$0.10 via API. Fastest in class. Good for high-volume.
- **Surya:** 88% layout accuracy, .4s/image on A10. Higher error rates vs GOT-OCR.
- **Tesseract 5:** CPU-first, no GPU needed, 98-99% on clean printed text. Still solid baseline for simple Latin scripts. No API cost.
- **PaddleOCR-VL:** 92.86 on OmniDocBench — top for complex documents. Apache 2.0.

### Methodology Gotchas
- getomni.ai OCR benchmark is the most cited but JS-rendered (Framer) — cannot WebFetch; use Google cache or community summaries
- OCRBench v2 combines 8 subtasks; for pure text recognition, filter to just text recognition sub-scores
- "98-99% accuracy" claims for printed text often reference Tesseract/specialized pipelines, not raw VLMs
- Self-hosted cost assumes H100 GPU; scale accordingly for A100 or local GPU
