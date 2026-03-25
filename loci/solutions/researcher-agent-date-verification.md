# Researcher Agent Date Verification Gotcha

## Problem

Delegated researcher agents confidently misattribute events from Year N-1 to Year N when anniversary coverage appears in search results.

**Example:** Searching "AI developments January 2026" returned DeepSeek R1 anniversary articles. The researcher treated these as January 2026 events, not realising R1 launched January 2025. The article text said "on the one-year anniversary" — the researcher even quoted this phrase but still classified it as a 2026 event.

## Why It Happens

- Search results for "X January 2026" include retrospectives and anniversary pieces published in January 2026
- Researchers prioritise source date (when the article was published) over event date (when the thing happened)
- Confirmation bias: the researcher is looking for January 2026 events, so anything from a January 2026 article gets classified as one

## Mitigation

When delegating historical research:
1. Explicitly instruct: "Verify the EVENT date, not the PUBLICATION date. Anniversary coverage is not a new event."
2. For any event claimed in the target month, ask: "Did this actually happen this year, or is this retrospective coverage?"
3. Cross-check major events against known timelines before including them

## Related Pattern

Regulatory modules get conflated when mentioned in the same priority document. HKMA's 2026 priorities mention both OR-2 (operational resilience) and AI governance — a researcher bundled them together as "AI regulation" when OR-2 has nothing to do with AI. Always check whether a cited regulation is actually about the claimed topic.
