# WeChat RSS Reference

> **Migrated to Wechat2RSS (Feb 26, 2026).** Old WeWe RSS container retired. See `~/docs/solutions/wechat-rss-api-technical-reference.md` for full API surface and alternatives.

## Wechat2RSS (Active)
- **Service:** `localhost:8001` (Docker container `wechat2rss`)
- **Docker compose:** `~/services/wechat2rss/docker-compose.yml`
- **License email:** terrylihm@gmail.com
- **Activation code:** `1fbce197-bfb1-44d1-bba7-5a8c46df8ccb`
- **Expiry:** 2027-02-24 20:55:00 (¥150/year)
- **API token:** `werss2026` (passed as `?k=werss2026` on all API calls)
- **Add account:** `curl -s "http://localhost:8001/addurl?url=<article_url>&k=werss2026"`
- **List subs:** `curl -s "http://localhost:8001/list?k=werss2026"`
- **Feed URL format:** `http://localhost:8001/feed/<biz_id>.xml`
- **Web UI:** `http://localhost:8001` (QR scan login here)
- **13 feeds active** (10 original + 3 migrated from xlab.app; extra 结构词AI deleted Feb 26)
- **Lustro sources.yaml updated** — all feeds point to `localhost:8001`

### Deployment Gotchas (Feb 2026)
- **`RSS_HOST` must NOT include `http://`** — the app prepends it. Use `localhost:8001` not `http://localhost:8001`.
- **Internal listen port is 8080, not 80.** Docker mapping must be `8001:8080`.
- **License is machine-bound via SQLite DB.** Deleting `res.db` loses the binding → "激活码已被绑定到其他机器" error on fresh DB. Keep the DB file.
- **License check has two phases:** local (from DB) then online. First boot with empty DB shows `Expire: 0001-01-01` locally, then validates online. If the online check fails (429 rate limit from rapid restarts), the server won't start.
- **No "listening" log message.** After license validation, the HTTP server starts silently.
- **No delete API, but web UI has delete buttons.** Feed management (pause/update/delete) via `localhost:8001` → 订阅管理. Re-add by BID: fill 公众号ID field + click 订阅.
- **Web UI login via agent-browser:** `agent-browser fill "input" "werss2026"` then `agent-browser click "button"`. Must use `fill` (Playwright native), not `eval` with `input.value =` — Vue's `v-model` ignores programmatic DOM changes.
- **风控 (risk control) on first login is common.** Proper fix: open WeChat Reading app → 书架 → 文章收藏 → click any 公众号名称 (not article) → enter article list. This proves organic usage to Tencent. 刷新风控 button works but is "not recommended" per docs. Risk control may also auto-clear after hours/days. Ref: https://wechat2rss.xlab.app/deploy/guide#手动解除风控
- **`addurl` resolves the *publisher* of the article, not accounts mentioned in it.** An interview *about* 李继刚 returns the interviewer's account. Always use articles written *by* the target account.

### Health Check
- **Script:** `~/scripts/crons/wewe-rss-health.py` (every 6h via LaunchAgent)
- **Monitors:** `localhost:8001/list` endpoint for feed count and paused status
- **Alerts:** Telegram on state changes (healthy → failing, failing → healthy)

### General Gotchas
- **Most WeChat公众号 aren't externally indexed.** Web search won't find `/s/` URLs for niche accounts. Must get article links from WeChat app directly.
- **No auto-renewal possible.** QR scan requires physical WeChat on phone.
- **Session lifetime unclear** — monitor via health check. WeWe RSS sessions lasted ~2 days; wechat2rss may differ.

## WeWe RSS (Retired Feb 26, 2026)
- Was on `localhost:4000`, data at `~/services/wewe-rss/data/` (SQLite DB with 484 cached articles)
- Container stopped and removed. Docker compose still at `~/services/wewe-rss/docker-compose.yml` for reference.
- Upstream archived Jan 2026. Relied on `weread.111965.xyz` proxy that was killed by Tencent rate limits.
