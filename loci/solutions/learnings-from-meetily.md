# Learnings from Meetily (~10K stars)

**Source:** https://github.com/Zackriya-Solutions/meeting-minutes
**Date:** 2026-02-23

## Growth / Positioning

1. **"Privacy-first" is a powerful wedge.** Meeting tools are a trust-sensitive category. Positioning as the local alternative to Otter/Fireflies gets you stars and press coverage even at v0.2. The privacy claim doesn't need to be perfect — it just needs to be *more private than the cloud incumbents*.

2. **Open-source community edition + PRO upsell is the 2025-26 playbook.** Core stays MIT, enterprise/compliance features (GDPR, PDF export, custom templates) go PRO. Stars drive awareness, PRO drives revenue. The community edition IS the marketing.

3. **Trending badges compound.** They display Trendshift badge prominently — social proof begets more social proof. Same pattern as "Featured on HN" badges.

## Technical Patterns

4. **Tauri 2 + Rust backend is a credible desktop stack.** 45MB binary vs Electron's 150MB+. Metal/CoreML auto-enabled per platform via Cargo feature flags — clean cross-platform GPU pattern without runtime detection.

5. **Dual transcription engine (Whisper + Parakeet).** Parakeet (ONNX-based) positioned as 4x faster. Having two engines lets them claim speed improvements without abandoning the well-known Whisper brand. Good product strategy.

6. **Audio pipeline depth matters.** VAD (Silero), noise suppression (RNNoise), loudness normalisation (EBU R128), device monitoring, incremental saving — this is what separates a real tool from a Whisper wrapper. The audio engineering is the moat, not the LLM integration.

7. **LLM provider abstraction as a feature.** Separate modules for Ollama, Anthropic, Groq, OpenRouter, OpenAI — each in its own Rust module. Users pick their backend. Low engineering cost, high perceived flexibility.

## Anti-Patterns to Avoid

8. **"Privacy-first" + opt-out telemetry is a credibility gap.** PostHog defaults to ON, hardcoded API key in source, "are you sure?" friction when disabling. Anyone reading the source (and they will — it's open source) will notice. If you claim privacy, make analytics opt-in or don't have them.

9. **Hardcoded API keys in source.** `phc_cohhHPgfQfnNWl33THRRpCftuRtWx2k5svtKrkpFb04` sitting in `commands.rs`. Even for PostHog (where the key is semi-public by design), it looks sloppy in a privacy-focused project.

10. **Heavy git dependency pinning.** `silero_rs` pinned to a specific rev, `cpal` patched via git, `ffmpeg-sidecar` on branch main, `cidre` pinned to rev. Each is a build fragility point. Fine for a startup shipping fast, risky for long-term maintenance.
