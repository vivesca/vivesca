---
problem: Exa API returns 403 from Python urllib
solution: Add User-Agent header — Cloudflare blocks Python-urllib default UA
tags: [exa, search, http, urllib, cloudflare, 403]
titer-hits: 126
titer-last-seen: 2026-05-01
---

Exa API (`api.exa.ai/search`) returns HTTP 403 error code 1010 when called from Python `urllib.request` with default User-Agent. curl works fine.

Fix: add `"User-Agent": "rheotaxis/1.0"` (or any non-default string) to request headers.
