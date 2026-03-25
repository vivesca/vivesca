# WeChat公众号 RSS — Technical API Reference

> Reverse-engineered API surface for scraping WeChat public account articles.
> Two independent API families: WeChat Reading (`i.weread.qq.com`) and MP Platform (`mp.weixin.qq.com`).
> Built from wewe-rss source analysis + community research. Feb 2026.

---

## Architecture: Two Distinct Approaches

| Approach | Domain | Auth mechanism | Used by |
|----------|--------|---------------|---------|
| **WeChat Reading (WeRead) API** | `i.weread.qq.com` | wr_vid + wr_skey cookies OR vid + accessToken headers | wewe-rss, RSSHub experiments |
| **WeChat MP Platform API** | `mp.weixin.qq.com` | fakeid + token (scraped from operator's own MP account login session) | we-mp-rss, wechat_spider, most direct scrapers |

These are completely separate authentication domains. wewe-rss uses the WeRead approach (exploiting WeChat Reading's subscription-to-public-accounts feature). we-mp-rss uses the MP platform approach (simulating the official account operator's web portal).

---

## API Family 1: WeChat Reading (i.weread.qq.com)

### Auth Flow

1. **QR code login:** User opens WeChat Reading web login at `https://weread.qq.com/web/login` (or `https://r.qq.com#login`).
2. **Session init:** GET `https://weread.qq.com/web/login/session/init` — returns initial cookie skeleton.
3. **QR scan:** User scans with WeChat mobile app.
4. **Cookie population:** First request to `https://weread.qq.com/web/user?userVid=[userId]` triggers full cookie population. The field to watch for is `wr_name` — if empty, the session is not yet ready; the page must reload.
5. **Cookies set (all must be present):** `wr_vid`, `wr_skey`, `wr_name`, `wr_logined`, `wr_avatar`.

**Token identities:**
- `wr_vid` = permanent user identifier (same across sessions)
- `wr_skey` = session key (`accessToken` in header-based auth)
- **Session lifetime:** ~2 days in practice (wewe-rss experience); earlier reports cited 2 hours for `accessToken` directly. The wewe-rss proxy observed `INVALID` status after ~48h consistently.

**Two equivalent auth methods:**
```
# Cookie-based
Cookie: wr_vid=31087522; wr_skey=Vp1IaX46; wr_name=...; wr_logined=1

# Header-based (equivalent)
vid: 31087522
accessToken: Vp1IaX46
```

**No auto-renewal is possible.** The QR scan requires physical WeChat on a mobile device. Cannot be automated via headless browser or API.

---

### Endpoints: User / Auth

#### GET /user/notebooks
- **URL:** `https://i.weread.qq.com/user/notebooks`
- **Auth:** Cookie or vid/accessToken headers
- **Params:** None
- **Returns:** User's reading notebooks list. Also serves as an auth check — returns -2012 on login timeout.
- **Error -2012:** Login timeout (登录超时)

#### GET /shelf/sync
- **URL:** `https://i.weread.qq.com/shelf/sync`
- **Params:** `userVid`, `synckey=0`, `lectureSynckey=0`
- **Returns:** Bookshelf contents including subscribed public accounts

---

### Endpoints: Public Account Articles (Key for RSS)

#### GET /book/articles
- **URL:** `https://i.weread.qq.com/book/articles`
- **Params:**
  - `bookId` — must be in format `MP_WXS_[numeric_id]` (e.g., `MP_WXS_3080584025`)
  - `offset` — pagination offset (e.g., `0`)
  - `count` — articles per page (e.g., `10`)
- **Auth:** Cookie or vid/accessToken headers
- **Returns:** Article list for the given public account

**Critical constraint:** A public account must first be "subscribed" within the WeChat Reading app (via the "Subscribe to Official Accounts" feature). Accounts not yet opened in WeChat Reading via mobile will return empty results. Direct API access without prior mobile initialization fails.

#### GET /store/search
- **URL:** `https://i.weread.qq.com/store/search`
- **Params:** `keyword`, `author`, `authorVids`, `categoryId`, `count=20`, `maxIdx=0`, `type=0`, `v=1`, `outer=1`, `fromBookId`
- **Returns:** Search results; used to find the `MP_WXS_` bookId for a public account by searching its name.

---

### Endpoints: Books (General WeRead)

#### GET /book/info
- **URL:** `https://i.weread.qq.com/book/info`
- **Params:** `bookId`

#### GET /book/chapterInfos
- **URL:** `https://i.weread.qq.com/book/chapterInfos`
- **Params:** `bookIds=[bookId]`, `synckeys=0`

#### GET /book/bookmarklist
- **URL:** `https://i.weread.qq.com/book/bookmarklist`
- **Params:** `bookId`

#### GET /book/bestbookmarks
- **URL:** `https://i.weread.qq.com/book/bestbookmarks`
- **Params:** `bookId`

#### GET /review/list
- **URL:** `https://i.weread.qq.com/review/list`
- **Params:** `bookId`, `listType=11`, `mine=1`, `synckey=0`, `listMode`

#### (Web variant) GET /web/book/...
The web version of WeRead (`weread.qq.com/web/`) uses the same cookie auth but different path prefix:
- `/web/book/info?bookId=...`
- `/web/book/bookmarklist?bookId=...`
- `/web/review/list?bookId=...&listType=11&mine=1&synckey=0`
- `/web/book/chapterInfos` (POST)
- `/web/book/getProgress?bookId=...`
- `/api/user/notebook` (GET)

---

## API Family 2: WeChat MP Platform (mp.weixin.qq.com)

This approach simulates a WeChat public account operator logged into the WeChat MP web admin portal (`mp.weixin.qq.com`). It does NOT require a WeChat Reading account.

### Auth Flow

1. **Login:** Selenium or headless browser logs into `https://mp.weixin.qq.com/` using a WeChat account that operates (owns/manages) a public account, OR uses session cookies from a valid logged-in session.
2. **Token extraction:** The `token` value is embedded in the URL after login (visible in the redirected URL query string).
3. **fakeid discovery:** Obtained by calling the Search API with a public account name — the response contains `fakeid` for each account.
4. **Cookie requirement:** The session cookie from the logged-in MP portal session is required for all requests.

**Key parameters:**
- `token` — changes per login session; embedded in URL. Expires when session expires.
- `fakeid` — permanent unique ID for a public account; stable across sessions.
- `__biz` — another encoding of the account identifier, used in article URLs.
- `uin` — user identifier (URL-encoded).
- `key` — dynamically generated per session for `getmasssendmsg` endpoint; expires quickly.
- `pass_ticket` — session token for `getmasssendmsg`; also expires.
- `appmsg_token` — separate token for `getappmsgext`; obtained from request headers when browsing articles.

---

### Endpoint: Search for Account fakeid

#### GET /cgi-bin/searchbiz
- **URL:** `https://mp.weixin.qq.com/cgi-bin/searchbiz`
- **Method:** GET
- **Params:**
  - `action=search_biz`
  - `token=[session_token]`
  - `lang=zh_CN`
  - `f=json`
  - `ajax=1`
  - `random=[random_float]`
  - `query=[account_name]`
  - `begin=0`
  - `count=5`
- **Auth:** Session cookies + token in URL
- **Returns:** JSON array of accounts; each has `fakeid`, `nickname`, `round_head_img`, `service_type`

---

### Endpoint: Article List (Operator Portal)

#### GET /cgi-bin/appmsg
- **URL:** `https://mp.weixin.qq.com/cgi-bin/appmsg`
- **Method:** GET
- **Params:**
  - `action=list_ex`
  - `token=[session_token]`
  - `lang=zh_CN`
  - `f=json`
  - `ajax=1`
  - `random=[random_float]`
  - `begin=[offset]` — pagination (0, 5, 10, …)
  - `count=5`
  - `fakeid=[account_fakeid]`
  - `type=9`
- **Auth:** Session cookies + token
- **Returns:** JSON with `app_msg_list` array (article title, link, create_time, cover, etc.) and `app_msg_cnt` (total count)

---

### Endpoint: Public Article History (Reader-facing, needs interception)

#### GET /mp/getmasssendmsg
- **URL:** `https://mp.weixin.qq.com/mp/getmasssendmsg`
- **Params:** `__biz`, `uin`, `key`, `pass_ticket`, `frommsgid`, `count`, `f=json`, `devicetype`, `version`, `lang`
- **Note:** `key` and `pass_ticket` are dynamically generated per session and expire quickly. Must be captured via MITM proxy or intercepting WeChat desktop/mobile client traffic.
- **Returns:** JSON with 10 articles per request. Pagination via `frommsgid` (use the msgid of the last item).

#### GET /mp/profile_ext (pagination variant)
- **URL:** `https://mp.weixin.qq.com/mp/profile_ext?action=getmsg`
- **Params:** `__biz`, `offset`, `count`, `uin`, `pass_ticket`, `appmsg_token`
- **Returns:** Next batch of articles

---

### Endpoint: Article Metrics

#### GET /mp/getappmsgext
- **URL:** `https://mp.weixin.qq.com/mp/getappmsgext`
- **Params:** `mid`, `sn`, `idx`, `appmsg_type`, `title`, `ct`, `appmsg_token`, `__biz`
- **Returns:** Extended article data (views, likes, comments). Token captured from article request headers.

---

## The wewe-rss Proxy Layer (weread.111965.xyz)

wewe-rss does NOT call `i.weread.qq.com` directly from client deployments. Instead:

1. The wewe-rss server calls `weread.111965.xyz` (Cloudflare-proxied, mirrors to `weread.965111.xyz` for domestic China DNS).
2. The proxy translates these calls to the actual WeChat Reading API and returns results.
3. The proxy was run by the project maintainer; it did NOT store user data (per project claims).

**Proxy API endpoints (as called by wewe-rss server → weread.111965.xyz):**

| Proxy endpoint | Method | Purpose |
|----------------|--------|---------|
| `GET /api/v2/platform/mps/{mpId}/articles?page={n}` | GET | Fetch article list for a public account |
| `POST /api/v2/platform/wxs2mp` body: `{url}` | POST | Resolve article URL to MP account metadata |
| `GET /api/v2/login/platform` | GET | Create login session (returns `uuid`, `scanUrl`) |
| `GET /api/v2/login/platform/{id}` | GET | Poll login result (returns `vid`, `token`, `username`) |

**Proxy auth headers (wewe-rss → proxy):**
```
xid: [account_id_in_wewe_db]
Authorization: Bearer [weread_account_token]
```

The proxy handles the actual `i.weread.qq.com` calls, cookie management, and session lifecycle on behalf of user deployments. This was the "not completely open source" aspect noted in coverage — the proxy was centrally operated.

---

## Rate Limits and Throttling

### WeChat Reading API (i.weread.qq.com) — Confirmed from wewe-rss issues

| Limit type | Value | Source |
|------------|-------|--------|
| Per-account daily | **50 requests/day** (post-Apr 2025) | Issue #396 |
| Per-IP (24h) | **300 requests/24h** (post-Apr 2025) | Issue #396 |
| Stable safe zone | ~10 accounts × ~2 refreshes/day | Issue #223 |
| Account blocking ("小黑屋") | Triggered by exceeding above | Issue #223 |
| Unblock time | 24 hours | Community reports |

**Earlier limits (pre-Apr 2025):**
- Per-account daily: was 150, briefly raised to 300 → API broke within days, forced rollback to 50
- This pattern suggests Tencent monitors aggregate usage and tightens limits reactively

**Throttle responses:**
- **401 (WeReadError401):** Session/account invalid — wewe-rss marks account as INVALID, removes from pool
- **429 (WeReadError429):** Rate limited — wewe-rss adds account to daily blocklist (keyed to Asia/Shanghai date)
- **400 (WeReadError400):** Parameter error / account processing issue — wewe-rss retries after 10-second delay, up to 3 retries
- **403:** Blocked by Tencent's anti-automation controls
- **404:** Endpoint change / deprecated route (seen in getMpArticles post-archival)
- **500:** Backend error with "账号处理请求参数出错" (account parameter processing error)

**CAPTCHA trigger:** Searching for public accounts in the WeChat Reading app too frequently triggers CAPTCHA challenges, separate from API rate limits.

### WeChat MP Platform API (mp.weixin.qq.com)

- `key` and `pass_ticket` in getmasssendmsg expire within minutes (must be freshly captured).
- `token` for cgi-bin/appmsg expires with the web session (hours to days depending on inactivity).
- `fakeid` is permanent.
- No documented per-day limits, but automated traffic patterns trigger security challenges (CAPTCHA, account locks).
- Random delays between requests are essential (we-mp-rss uses random delay mechanism).

---

## IP and Account Reputation Factors

- **Datacenter IPs** are flagged faster than residential IPs. The weread.111965.xyz proxy (Cloudflare CDN, Canadian IP `172.64.80.1`) was detectable as datacenter-origin.
- **Account age/activity:** Newly registered WeChat accounts or accounts with no organic WeChat Reading activity are flagged faster.
- **Subscription count:** Subscribing to >10 public accounts in WeChat Reading via automated means triggers CAPTCHA in the app.
- **DNS pollution (domestic China):** weread.111965.xyz was DNS-poisoned in parts of China; workaround was `PLATFORM_URL=https://weread.965111.xyz` or manual `/etc/hosts` entry.

---

## What Killed wewe-rss

**Timeline:**

| Date | Event |
|------|-------|
| ~2024 Mar | v2.x launched with "more stable" new interface (via weread.111965.xyz proxy) |
| ~2024 Mar–Apr | v2.3–v2.6 iteration: random account selection, delay controls, history article fetching |
| ~Apr 2025 | Tencent tightened WeChat Reading API limits to 50 req/account/day and 300 req/IP/24h. New interface required (accounts needed re-login). The maintainer had briefly raised limits to 300/account/day — the API broke within 2 days, forcing the more restrictive 50/day rollback. |
| Jan 19, 2026 | Repository archived by maintainer. Read-only. |

**Root cause:** Tencent's April 2025 rate limit changes made the centralized proxy unviable. At 50 requests/account/day and 300/IP/24h, a shared proxy serving many users hits limits almost immediately. The wewe-rss architecture requires the proxy to make WeChat Reading API calls on behalf of all deployments, so the IP-level limit was particularly fatal. Self-hosting with a dedicated account reduces IP contention but still hits 50/account/day which is enough for ~25 feeds refreshed twice daily — borderline for personal use, inadequate for a shared service.

**Secondary cause:** Login token refresh issues introduced in the April 2025 update. The v2 interface change required re-authentication and introduced bugs where phone-side login appeared successful but the web account failed to register.

**Architecture vulnerability:** The proxy-dependent design meant a single Tencent policy change was terminal. Projects that call the MP platform API directly (we-mp-rss) or use direct `i.weread.qq.com` calls without a shared proxy are less vulnerable to IP-level limits.

---

## Alternative: we-mp-rss Architecture (mp.weixin.qq.com)

**Key difference:** Uses the operator's own WeChat MP web portal session rather than a WeChat Reading user account.

- Mechanism: Simulates `mp.weixin.qq.com` web platform requests using `fakeid` + `token` from the operator's own WeChat MP account login.
- Token acquisition: `token` is embedded in the URL after Selenium-driven login. `fakeid` is obtained via the `searchbiz` API.
- Stability advantage: Token is per-session (not per-account-day quota), and there's no shared IP-level throttle like the WeChat Reading approach. Each deployment uses its own operator account.
- Weakness: Requires a WeChat account that manages at least one public account (operator access), or simulating such access. Session cookies expire and Selenium re-login is needed periodically.
- Data scope: Can access the full article history via `cgi-bin/appmsg` without mobile initialization. No `MP_WXS_` bookId dependency.

**Source:** rachelos/we-mp-rss (2.2k stars, last release v1.4.8 Dec 2025, still active as of Feb 2026).

---

## Anti-Detection Patterns (from wewe-rss source code)

From `apps/server/src/trpc/trpc.service.ts` and `apps/server/src/feeds/feeds.service.ts`:

1. **Account pool rotation** — `getAvailableAccount()` randomly picks from enabled, non-blocked accounts
2. **Daily blacklist** — rate-limited accounts quarantined per-day, keyed to `Asia/Shanghai` midnight via dayjs
3. **Sequential feed processing** — one feed at a time, `UPDATE_DELAY_TIME` seconds between each (default 60s)
4. **30s hardcoded cooldown** between feeds (in `feeds.service.ts` finally block)
5. **3× retry with account switch** — each `getMpArticles` retry calls `getAvailableAccount()` again, picking a different random account
6. **Low-frequency cron** — default `35 5,17 * * *` (twice daily at 5:35am/5:35pm CST)
7. **LRU cache** — 5000-entry cache for article HTML content, avoids re-fetching `mp.weixin.qq.com/s/{id}`
8. **Browser-like headers** — Chrome 101 UA, full sec-ch-ua headers, accept-encoding, on the article content fetcher

### What Wechat2RSS (ttttmr) adds (from blog.xlab.app)

9. **Phone/residential IP proxying** — mobile carrier IPs treated as legitimate by Tencent risk control; datacenter IPs get CAPTCHA'd
10. **Intelligent update frequency** — adaptive backoff when risk control triggers, ramp up when clear
11. **Static RSS via Vercel/Cloudflare** — scraper runs on old laptop behind NAT on residential IP; RSS XML served from CDN
12. **Closed source as survival strategy** — fewer users = less Tencent attention on the pattern

---

## Article Content Fetching (Both Approaches)

Article full text is fetched from **public URLs** — no auth needed:
```
GET https://mp.weixin.qq.com/s/{article_id}
```

From `feeds.service.ts`:
- Standard browser headers (Chrome UA, sec-ch-ua, etc.)
- `data-src` → `src` replacement for lazy-loaded images
- `opacity: 0` and `visibility: hidden` CSS removal (anti-scraping countermeasures)
- Cheerio extracts `.rich_media_content` div
- HTML minified via `html-minifier`
- RSS output via `feed` npm package (atom, rss2, json1 formats)

---

## Data Model (from wewe-rss Prisma schema)

```
Account {id, token(2048), name, status(0|1|2), createdAt, updatedAt}
Feed    {id, mpName, mpCover, mpIntro, status, syncTime, updateTime, hasHistory}
Article {id, mpId, title, picUrl, publishTime, createdAt, updatedAt}
```

- `Account.status`: 0=expired (WeReadError401), 1=active, 2=disabled
- `Feed.hasHistory`: 1=more pages available, 0=all fetched
- `Article.id`: the short ID from `mp.weixin.qq.com/s/{id}`

---

## Building Your Own — Decision Tree

```
Want to build?
├── Just need RSS output → Pay ¥150/yr for Wechat2RSS
├── Want FOSS + full control → Deploy we-mp-rss (MP Platform approach)
│   └── Trade-off: token expiry management instead of QR re-auth
└── Want to learn anti-detection engineering
    ├── Step 1: Study this doc + wewe-rss source (zero risk)
    ├── Step 2: Observe live wewe-rss traffic (zero risk)
    ├── Step 3: Use SECONDARY WeChat account only
    ├── Step 4: Residential IP, <10 req/day, aggressive backoff
    └── NEVER use primary WeChat account for scraping
```

---

## Local Source Code Reference

- wewe-rss source: `~/code/wewe-rss-study/` (cloned for study)
- **Key file:** `apps/server/src/trpc/trpc.service.ts` — all proxy API calls, account rotation, error handling
- **Feed generation:** `apps/server/src/feeds/feeds.service.ts` — cron scheduling, HTML cleaning, RSS output
- **tRPC routes:** `apps/server/src/trpc/trpc.router.ts` — CRUD for accounts/feeds/articles
- **Schema:** `apps/server/prisma/schema.prisma` — Account, Feed, Article models
- **Config:** `apps/server/src/configuration.ts` — `PLATFORM_URL` (default `weread.111965.xyz`), delays, auth

---

## Wechat2RSS Local Tool API (ttttmr/wechat2rss)

Reverse-engineered from JS bundle (`/assets/index-*.js`). All endpoints require `?k=<RSS_TOKEN>` (set via `RSS_TOKEN` env var in Docker).

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/list?k=TOKEN` | GET | List all subscribed feeds (returns JSON with id, name, link, paused, check_time) |
| `/add/{wechat_id}?k=TOKEN` | GET | Add a WeChat account by its public account ID (e.g. `almosthuman2014`) |
| `/addurl?k=TOKEN&url=URL` | GET | Add a feed by article URL |
| `/feed/{feed_id}.xml?k=TOKEN` | GET | Get RSS XML for a specific feed |
| `/pause/{feed_id}?k=TOKEN&status=BOOL` | GET | Pause/resume a feed |
| `/opml?k=TOKEN` | GET | Export all feeds as OPML |
| `/login/new` | GET | Start new WeChat QR login session |
| `/login/code` | GET | Get QR code for login |
| `/login/list` | GET | List login sessions |
| `/config` | GET | Get server config |

**Docker env vars:** `RSS_TOKEN`, `RSS_HOST`, `RSS_HTTPS`, `RSS_KEEP_OLD_COUNT`, `RSS_MAX_ITEM_COUNT`.

**Feed IDs are numeric** (e.g. `3073282833` for 机器之心). Obtained from `/list` response.

---

## Sources

1. [wewe-rss GitHub repo (archived Jan 2026)](https://github.com/cooderl/wewe-rss)
2. [Issue #396 — Apr 2025 rate limit changes](https://github.com/cooderl/wewe-rss/issues/396)
3. [Issue #223 — Subscription update failures (comprehensive)](https://github.com/cooderl/wewe-rss/issues/223)
4. [Issue #251 — Failed account addition, WeReadError400](https://github.com/cooderl/wewe-rss/issues/251)
5. [Issue #314 — DNS resolution failure for weread.111965.xyz](https://github.com/cooderl/wewe-rss/issues/314)
6. [RSSHub Issue #311 — Original WeChat RSS discussion](https://github.com/DIYgod/RSSHub/issues/311)
7. [trpc.service.ts — wewe-rss proxy API calls (raw)](https://raw.githubusercontent.com/cooderl/wewe-rss/main/apps/server/src/trpc/trpc.service.ts)
8. [obsidian-weread-plugin weread-api.md](https://github.com/zhaohongxuan/obsidian-weread-plugin/blob/main/docs/weread-api.md)
9. [WeRead QR login flow (zhaohongxuan blog)](https://zhaohongxuan.github.io/2022/05/24/weread-qrcode-login-in-obsidian/)
10. [崔庆才 — New MP article scraping interface](https://cuiqingcai.com/4652.html)
11. [wechat_spider gist — getmasssendmsg details](https://gist.github.com/snowman/97fa792582e727dcf62b1eb6f980c0bd)
12. [we-mp-rss GitHub (rachelos)](https://github.com/rachelos/we-mp-rss)
13. [WeRSS principle analysis (cnblogs)](https://www.cnblogs.com/wintersun/p/19265009)
14. [Sspai wewe-rss overview](https://sspai.com/post/93845)
