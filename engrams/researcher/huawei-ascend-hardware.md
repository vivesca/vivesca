# Huawei Ascend AI Chip Research — Feb 2026

## Reliable Sources for This Domain
- nexgen-compute.com/blog/huawei-ascend-910c-vs-nvidia-h100-ai-chip-comparison: best specs table (cross-referenced against marketing claims)
- aiproem.substack.com: best CANN ecosystem depth analysis, power efficiency numbers
- tomshardware.com: most reliable ongoing coverage (verified training failure, roadmap, DeepSeek data)
- digitimes.com: yield rate data (early, behind paywall but search results surface key numbers)
- technode.com: supply chain data (HBM bottleneck, shipment targets)
- scmp.com: Zhipu/GLM-5 deployment confirmation
- trendforce.com: roadmap announcements (950 series, HBM specs)
- semianalysis.com: deepest supply chain analysis (behind paywall; SemiAnalysis excerpts surface via fibermall.com/blog/)

## Key Verified Facts (Feb 2026)

### Ascend 910C Specs
- FP16: ~800 TFLOPS (marketing) / ~60% H100 effective (DeepSeek measured)
- BF16: ~781 TFLOPS
- INT8: ~1,600 TOPS
- Memory: 128 GB HBM3
- Memory bandwidth: 3.2 TB/s (slightly below H100's 3.35 TB/s, below H20's 4.0 TB/s)
- TDP: ~310 W
- Process: SMIC N+2 (7nm DUV, NOT EUV)
- Architecture: Da Vinci, dual 910B chiplet package
- Interconnect: HCCS 392 GB/s (8-chip) — matches NVIDIA A800 NVLink, lags H100 NVLink (900 GB/s) badly
- Transistors: 53 billion

### Comparisons
- vs H100: ~81% raw FP16, ~60% effective inference, far behind on training, 2.3x less efficient per watt
- vs H20: much higher raw FP16 (800 vs 148 TFLOPS), but H20 has higher memory bandwidth and better CUDA software
- CloudMatrix 384: 300 PFLOPS BF16 (1.7x GB200 NVL72), but 4x more power — rack-level brute force, not chip parity

### Confirmed Deployments
- **Zhipu AI (GLM-5, 744B MoE):** Fully trained on 100,000 Ascend 910B chips with MindSpore. Released Feb 11, 2026. CONFIRMED.
- **DeepSeek:** Inference on 910C confirmed. Training (R2) failed multiple times on Ascend; reverted to NVIDIA for training. CONFIRMED failure.
- **Baidu/ByteDance/China Mobile:** Testing confirmed; scale unclear. ByteDance $5.6B procurement announced — not confirmed deployed.
- H20 export ban (April 15, 2025) forced Chinese labs to pivot regardless of preference.

### CANN vs CUDA
- CANN developer base ~1/10th of CUDA's (CUDA: 2M+ developers, 438K monthly downloads)
- PyTorch translation layer exists but maturity gap is real — debugging, profiling, operator coverage all inferior
- Huawei open-sourced CANN, MindSpore, Pangu in 2025 — improving domestic adoption
- DeepSeek-V3 officially supports CANN as first-class target (alongside Cambricon, Hygon)
- Inference: functional with engineering effort. Training: high-risk, requires deep Ascend expertise.

### MoE Model Support
- Inference of 671B+ MoE models (DeepSeek-V3, GLM-5): works on 910C via MindIE framework
- 128GB HBM per chip is an advantage over H100 (80GB) for fitting large model shards
- HCCS interconnect bottlenecks expert-parallel communication in large MoE at scale
- Training: Zhipu succeeded (GLM-5, 910B chips, heroic engineering). DeepSeek failed (R2, abandoned).

### Production/Supply
- Yield: started ~20-30% (late 2024) → ~40% (Feb 2025, first profitable). Target: 60%.
- 2025 shipment plan: ~653K × 910C + ~152K × 910B = ~805K total Ascend units
- HBM supply (not yield) is now primary bottleneck for further scaling
- Constraint: SMIC uses DUV (not EUV) — structural disadvantage vs TSMC at 4nm

### Roadmap (announced, not verified)
- **910D** (Q2 2026): Four-die design, targeting H100+ single-chip performance
- **950PR** (Q1 2026): 128GB in-house HBM (HiBL 1.0), 1.6 TB/s bandwidth, prefill/recommendation
- **950DT** (Q4 2026): 144GB HBM, 4 TB/s memory bandwidth, 2 TB/s interconnect — critical improvement
- **960** (Q4 2027): 2x 950 on compute, memory, interconnect
- Ascend 920: NOT a real model — no 920 in official roadmap; confusion from early reports

## Misinformation Patterns
- "910C outperforms H100" — true only at system (rack) level with 4x power; false at chip level
- "Ascend is nearly CUDA-equivalent now" — CANN has improved but developer ecosystem gap is 5-10x; training stability unsolved
- "China has solved semiconductor independence" — GLM-5 on Ascend is milestone but exception, not norm; DeepSeek R2 failure is equally real
- Spec sheets: 800 TFLOPS FP16 is a marketing claim. Actual measured inference is ~60% of H100 (DeepSeek data). Always flag the discrepancy.
- Huawei official site NEVER published an Ascend 910C datasheet — all specs are from teardowns, leaks, or secondary analysis.

## Methodology That Worked
- Tom's Hardware consistently had the best verified reporting on both positive (DeepSeek inference) and negative (R2 training failure) data points
- aiproem.substack.com had the cleanest CANN vs CUDA ecosystem comparison with concrete numbers
- WebFetch on Tom's Hardware and nexgen-compute returned empty body (JS-heavy) — rely on WebSearch result summaries for those sites
- Search for "problems/failures/disappointed" surfaces the DeepSeek R2 training failure story, which most positive coverage omits
