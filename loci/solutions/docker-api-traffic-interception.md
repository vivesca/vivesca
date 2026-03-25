---
title: Docker Container API Traffic Interception
category: integration-issues
tags: [docker, reverse-engineering, debugging, proxy]
date_created: 2026-02-24
---

# Docker Container API Traffic Interception

## Problem

Need to inspect HTTPS API calls from a Docker container to an external service, without modifying the container image or installing certs.

## Pattern

Override the container's upstream URL env var to point at a local HTTP reverse proxy. The proxy logs everything and forwards to the real HTTPS endpoint. No MITM certs needed — the container sends HTTP to your proxy, your proxy sends HTTPS upstream.

```
Container (HTTP) → localhost proxy (logs) → real upstream (HTTPS)
```

## Steps

### 1. Write a logging reverse proxy

Minimal Python script (~100 lines). Key features:
- Logs method, path, auth headers (masked), request body, response status/body
- Forwards all headers except `Host` and `Transfer-Encoding`
- Pretty-prints JSON, truncates long responses
- Handles errors gracefully (502 on upstream failure)

Example: `~/code/wewe-rss-study/intercept-proxy.py`

### 2. Start proxy on host

```bash
python3 intercept-proxy.py > /tmp/proxy.log 2>&1 &
```

### 3. Restart container with URL override

```bash
docker run -d \
  -e PLATFORM_URL=http://host.docker.internal:9999 \
  --add-host=host.docker.internal:host-gateway \
  ...
```

Key: `--add-host=host.docker.internal:host-gateway` lets the container reach the host's localhost.

### 4. Trigger the API calls and read logs

```bash
cat /tmp/proxy.log
```

### 5. Restore when done

Remove `PLATFORM_URL` override and `--add-host` to return to normal.

## Gotchas

- **`host.docker.internal` requires `--add-host` on Linux.** macOS Docker Desktop provides it natively, but explicit is safer.
- **Content-Encoding stripping:** If the proxy strips `content-encoding: gzip` but doesn't decompress, clients get garbled data. Either pass through unchanged or decompress+re-encode.
- **The app may make API calls from both server AND client (browser).** Browser-side calls (e.g., tRPC from a React dashboard) bypass the proxy entirely — they go direct from the user's browser. Only server-side calls route through the env var.
- **Long-poll endpoints** (e.g., login result polling with 120s timeout) need matching timeouts in the proxy.
- **App-level validation happens BEFORE upstream calls.** If the app checks local DB first (e.g., "no valid accounts"), the proxy sees nothing. Fix the local state first.

## When to Use

- Reverse-engineering third-party Docker images that call external APIs
- Debugging auth failures, rate limits, or unexpected responses
- Capturing real API traffic patterns without modifying source code
- Any container with a configurable upstream URL env var

## Discovered During

WeChat Reading API reverse engineering (Feb 2026). wewe-rss container calls `weread.111965.xyz` proxy via `PLATFORM_URL` env var. Intercepted login flow and article fetch endpoints. See `~/docs/solutions/wechat-rss-api-technical-reference.md`.
