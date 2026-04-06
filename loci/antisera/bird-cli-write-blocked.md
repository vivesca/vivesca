---
title: bird CLI — writes blocked by X anti-automation
date: 2026-03-26
tags: [bird, twitter, x, cli]
titer-hits: 2
titer-last-seen: 2026-04-06
---

# bird CLI: reads work, writes return error 226

`bird whoami`, `bird read`, `bird search` etc all work fine.
`bird tweet` fails with HTTP 226 "looks like it might be automated" + fallback 403.

This is X's write-endpoint anti-automation, NOT an auth cookie issue. Chrome cookies are valid (reads succeed). The write endpoint specifically blocks.

Workaround: paste tweet text manually in browser. No CLI fix known as of Mar 2026.
