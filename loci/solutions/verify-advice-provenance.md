# Verify Advice Provenance Before Adopting

## Pattern
Community "best practices" get presented as authoritative without citing primary sources. AI assistants (including Claude) amplify this by confidently synthesizing community advice as if it were official guidance.

## Case Study: Context Compaction (Feb 2026)
1. Asked whether compacting at 50% was a good idea
2. Claude confidently said "compact at turn 3-4" based on own reasoning
3. When asked to verify online, Claude found community blogs recommending "compact at 70%" and presented this as consensus
4. When asked **who** recommends 70% — it was community guides (claudefa.st, DeepWiki/FlorianBruniaux), not Anthropic
5. Official Anthropic docs: no specific percentage. Just "trust auto-compact, `/clear` between tasks"
6. Meanwhile, we had `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=50` in settings.json — actively overriding Anthropic's default based on unverified advice

## The Error Chain
- Plausible reasoning ("context degrades as it fills") → community blog formalises a number (70%) → AI assistant cites it as best practice → user configures system accordingly → suboptimal behaviour for months

## Rule
**Before adopting a tool/config recommendation, ask: "Is this from the vendor or from a blog?"**
- Vendor docs = adopt with confidence
- Community guide = treat as one person's opinion, check vendor docs first
- AI-generated advice = verify the source chain, not just the claim

## Applies To
- Any tool configuration (not just Claude Code)
- Framework "best practices" that cite no source
- AI assistant recommendations that sound authoritative but cite community blogs
