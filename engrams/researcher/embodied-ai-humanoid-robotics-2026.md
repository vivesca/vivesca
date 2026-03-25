---
name: Embodied AI & Humanoid Robotics State (Mar 2026)
description: Current state of humanoid robot companies, models, AI integration, breakthroughs, timelines, and deployments as of March 2026
type: reference
---

## Key Companies and Models (as of Mar 2026)

- **Figure AI**: Figure 02 deployed at BMW Spartanburg (see reality check below). Figure 03 announced with Helix VLA platform, 48+ DoF, BotQ factory tooled for 12K units/year.
- **Tesla Optimus Gen 3**: Musk confirmed on Q4 2025 earnings call (Jan 28 2026) that deployed units are NOT doing "useful work" — data collection only. Gen 3 production started at Fremont Feb 2026. Claims of "1,000+ working units" contradicted by Musk himself.
- **Boston Dynamics Atlas (electric)**: Unveiled at CES Jan 5 2026. 56 DoF. Deploying to Hyundai's Georgia Metaplant (RMAC). Google DeepMind partnership — Gemini Robotics models running on it. All 2026 units already committed (Hyundai + DeepMind).
- **Agility Robotics Digit**: Most credible commercial deployment. Toyota Canada: 7+ units on RAV4 production line under RaaS agreement. GXO, Mercado Libre also. Handles tote unloading — specific, repetitive.
- **1X NEO**: $20K consumer robot. Open for preorders, first deliveries 2026. Uses teleoperator hybrid model — human in loop for tasks AI can't handle. Only consumer-targeting humanoid actually shipping.
- **Unitree G1**: $13,500. Best value. VLA open-sourced (UnifoLM-VLA-0). CES 2026: H2 at $29,900. G1 now doing real dexterous tasks (pill bottles, pegboard sorting) not just demos.
- **Xpeng Iron**: Mass production started 2026, factory trials in Guangzhou.

## AI + Robotics Integration

**Vision-Language-Action (VLA) models** are the dominant paradigm — unify perception, language reasoning, and motor control in one model.

Key models:
- **Physical Intelligence π0**: Open-sourced Feb 2026. Trained on 7 robot platforms, 68 tasks. π0.5 generalizes to new homes. π0.6 (with Weave Robotics): 50% reduction in human interventions for laundry folding. March 2026: Multi-Scale Embodied Memory (MEM) added — handles tasks >10 minutes.
- **Gemini Robotics**: Google DeepMind. Launched March 2026. Two models: Gemini Robotics (VLA, direct robot control) and Gemini Robotics-ER (embodied reasoning/spatial understanding). Runs on ALOHA, Bi-arm Franka, Apptronik Apollo, and Atlas. Gemini Robotics 1.5 added chain-of-thought reasoning before action.
- **Figure Helix**: Figure's in-house VLA platform. Proprietary.
- **Unitree UnifoLM-VLA-0**: Open-sourced, general manipulation.

## Data Flywheel / Field Experience

The formal concept ("Robot-Powered Data Flywheels", arxiv:2511.19647) is well-established theoretically. Key instantiations: AutoRT, AgiBot World, DexFlyWheel, Scanford. Single robot generates terabytes/hour of multimodal data. Fleet learning allows instant skill replication across units once learned.

**Reality**: Most robots still in "kindergarten" — simulators (NVIDIA Isaac Sim) + teleoperation, not truly accumulating diverse field experience. The data-from-deployment flywheel is nascent. Physical Intelligence's π0.6 Weave deployment is the clearest example of real-world data improving a deployed model.

## Key Breakthroughs

- VLA models achieving meaningful zero-shot generalization (π0.5 in new homes, Gemini Robotics on new robot types)
- Multi-Scale Embodied Memory (MEM) enabling tasks >10 min (March 2026)
- Dexterous hands: 25-50 actuators per arm (Tesla Gen 3), MATRIX-3 27-DoF hand
- NVIDIA Jetson Thor (late 2025): 2070 FP4 TFLOPS enabling real-time reasoning within humanoid power budget
- Locomotion: Unitree H1 sprinting/jumping/balance after heavy pushes — genuinely dynamic

## Realistic Timelines (cross-referenced: Bain, Goldman Sachs, Morgan Stanley)

- **Now-3 years**: Semi-structured industrial tasks in controlled environments (tote picking, parts feeding, palletizing). Hundreds to ~13K units shipped in 2025, ~15-30K in 2026.
- **3-5 years**: Service environments (hotel cleaning, hospital logistics) with battery hot-swaps. 250K+ units/year by 2030 (Goldman Sachs base case).
- **5-10 years**: Consumer applications at meaningful scale.
- **10+ years**: Open-ended real-world autonomy.

**Biggest bottleneck per Bain**: Battery life (2hrs vs 8hr shift requirement) — could take up to 10 years. Fine motor/tactile dexterity also lagging.

## Reality Checks

- **Figure/BMW claim**: BMW confirmed only ONE robot doing a SINGLE task (part pick-and-place for welding). Figure CEO's "fleet running end-to-end operations" language was significantly overstated. The partnership is real; the scale is not.
- **Tesla Optimus**: Musk himself confirmed no "useful work" on Q4 2025 earnings call — current units are data collection infrastructure, not labor replacement.
- **Goldman Sachs**: $38B TAM by 2035, 250K shipments/year by 2030 (almost all industrial).
- **Morgan Stanley**: $5T by 2050, slow until mid-2030s.

## Source Reliability Notes

- fortune.com WebFetch works for detailed fact-checking
- bain.com/insights WebFetch works well, returns clean summaries
- figure.ai/news WebFetch works for press releases
- arxiv.org HTML pages work
- deepmind.google/blog pages work
- humanoidsdaily.com reasonable secondary source
