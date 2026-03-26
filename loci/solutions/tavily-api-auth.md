---
problem: Tavily API auth header format
solution: Uses Authorization Bearer, not x-api-key
---

Tavily API (`api.tavily.com/search`) uses `"Authorization": f"Bearer {key}"` header, not `"x-api-key"` like Exa/Serper.
