# Newsletter Dedup: Verify Source Before Unsubscribing

## Pattern

Before unsubscribing an email newsletter that a tool (Lustro, RSS reader) claims to cover:

1. **Verify the tool can actually fetch it.** Check for RSS feed, public web archive, or API.
2. **"No RSS" ≠ "email only."** The content may be publicly archived on the website (Evident Banking Brief: full briefs at `evidentinsights.com/bankingbrief/`).
3. **Check LinkedIn** — many B2B newsletters post full content or direct links on their company page.
4. **Test the alternative channel before unsubscribing.** Fetch one article via the non-email path. If it works, unsubscribe.

## Discovery

Feb 2026. Unsubscribed Evident Banking Brief assuming email-only (no RSS). User challenged — found full briefs publicly archived on website + linked from LinkedIn posts. Re-subscribed, then verified web archive works, then unsubscribed correctly.

## Checklist

- [ ] RSS feed exists? (`<link>` tag in page source, or `/feed`, `/rss`)
- [ ] Public web archive? (check newsletter landing page for "All editions" or similar)
- [ ] LinkedIn company page posts with links?
- [ ] Can Lustro/tool actually scrape it? (test one fetch)
- [ ] Only then: unsubscribe email
