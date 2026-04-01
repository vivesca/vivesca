---
problem: Tavily API auth header format
solution: Uses Authorization Bearer, not x-api-key
tags: [tavily, search, http, auth, api-key]
titer-hits: 4
titer-last-seen: 2026-04-01
---

Tavily API (`api.tavily.com/search`) uses `"Authorization": f"Bearer {key}"` header, not `"x-api-key"` like Exa/Serper.
