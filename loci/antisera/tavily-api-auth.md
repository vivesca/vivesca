---
problem: Tavily API auth header format
solution: Uses Authorization Bearer, not x-api-key
tags: [tavily, search, http, auth, api-key]
titer-hits: 2
titer-last-seen: 2026-03-27
---

Tavily API (`api.tavily.com/search`) uses `"Authorization": f"Bearer {key}"` header, not `"x-api-key"` like Exa/Serper.
