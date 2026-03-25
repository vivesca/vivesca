# Agent-Reach Cherry-Pick Notes

**Repo:** https://github.com/Panniantong/Agent-Reach (~7.5k stars, Mar 2026)
**Decision:** Don't adopt wholesale. Cherry-pick patterns. Revisit quarterly.
**Last reviewed:** 2026-03-13

## Worth Stealing

### 1. XHS via xiaohongshu-mcp (replaces broken MediaCrawler in qianli)

Current `qianli xhs` uses MediaCrawler (QR auth, fragile subprocess). Agent-Reach uses:
- **xiaohongshu-mcp** (https://github.com/xpzouying/xiaohongshu-mcp, 9k+ stars)
- Docker container: `docker run -d --name xiaohongshu-mcp -p 18060:18060 xpzouying/xiaohongshu-mcp`
  - ARM64 (Apple Silicon): add `--platform linux/amd64`
- Access via mcporter: `mcporter config add xiaohongshu http://localhost:18060/mcp`
- Commands:
  ```bash
  mcporter call 'xiaohongshu.search_feeds(keyword: "query")'
  mcporter call 'xiaohongshu.get_feed_detail(feed_id: "xxx", xsec_token: "yyy")'
  mcporter call 'xiaohongshu.get_feed_detail(feed_id: "xxx", xsec_token: "yyy", load_all_comments: true)'
  mcporter call 'xiaohongshu.publish_content(title: "标题", content: "正文", images: ["/path/img.jpg"], tags: ["tag"])'
  ```
- Still needs cookie auth (Cookie-Editor export) but no QR scan dance.
- **Action:** Rebuild qianli XHS backend on this. Priority: HIGH.

### 2. Weibo via mcp-server-weibo (new capability)

- https://github.com/Panniantong/mcp-server-weibo (their own fork)
- Install: `pip install git+https://github.com/Panniantong/mcp-server-weibo.git`
- Register: `mcporter config add weibo --command 'mcp-server-weibo'`
- Capabilities: 热搜, search content/users/topics, user timeline, comments
- No auth for public content.
- **Action:** Add to qianli as `qianli weibo "query"`. Priority: LOW (no current use case).

### 3. V2EX public API patterns (trivial curl)

No auth needed. Useful curl one-liners:
```bash
# Hot topics
curl -s "https://www.v2ex.com/api/topics/hot.json" -H "User-Agent: agent-reach/1.0"
# Node topics
curl -s "https://www.v2ex.com/api/topics/show.json?node_name=python&page=1"
# Topic + replies
curl -s "https://www.v2ex.com/api/topics/show.json?id=TOPIC_ID"
curl -s "https://www.v2ex.com/api/replies/show.json?topic_id=TOPIC_ID&page=1"
# No search API — use Exa with site:v2ex.com
```
- **Action:** Add to qianli as `qianli v2ex "query"` (via exauro site:). Priority: LOW.

### 4. `agent-reach doctor` pattern

Health-check across all channels in one command. Nice pattern for our own tool fleet.
Could build a `/doctor` skill that checks: exauro, auceps, qianli backends, deltos, fasti, etc.
- **Action:** Consider building. Priority: LOW.

### 5. Xiaoyuzhou podcast transcription (Groq Whisper)

`~/.agent-reach/tools/xiaoyuzhou/transcribe.sh` — downloads audio, runs through Groq's free Whisper API.
- **Action:** Niche. Skip unless a podcast research need arises.

## Not Worth Stealing

- **Twitter/X (xreach)** — we have auceps + grok, more integrated
- **YouTube (yt-dlp)** — we have video-digest
- **Web reading (Jina Reader)** — we have defuddle + agent-browser
- **Web search (Exa via mcporter)** — we have exauro + noesis
- **LinkedIn (linkedin-mcp)** — we have nodus + nexum
- **WeChat articles** — we have wechat-article skill
- **GitHub (gh CLI)** — already installed
- **RSS (feedparser)** — trivial, already available
- **Their SKILL.md** — would conflict with our routing

## Known Issue: qianli XHS broken

MediaCrawler backend is fragile (QR auth expires, subprocess timeout). Replacing with
xiaohongshu-mcp (Docker + mcporter) is the fix. See item #1 above.

## Revisit Schedule

Check repo quarterly for new channels or improved upstream tool choices.
Next review: 2026-06-13.
