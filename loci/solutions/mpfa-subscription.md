# MPFA Website Subscription — Agent-Browser Gotcha

**LRN-20260311-001**

## Problem
`agent-browser open "https://www.mpfa.org.hk/en/subscription"` loads the page but the subscription form body renders blank — only header/footer visible.

## Fix
Navigate via the homepage nav link instead:
1. `agent-browser open "https://www.mpfa.org.hk/en/subscription"`
2. Accept the cookie banner: `agent-browser click "text=Accept"`
3. Click the nav Subscription link (ref: `e5` or similar): `agent-browser click "ref=e5"`
4. Form renders at `/en/home/subscription`

The direct URL doesn't trigger the same JS bootstrap that the nav click does.

## Subscription topics (Terry's selection)
- What's New
- eMPF Platform
- Press Releases
- Research & Statistics
- Circulars

Email: terry.li.hm@gmail.com, Language: English

## Blocker
reCAPTCHA on submit — requires manual tick. Everything else can be automated.

## Frequency
Annual (activation link expires in 24h, so re-subscribe if missed).
