---
name: Hosting Platforms Research (Railway, Render, Fly.io, Modal, Cloud Run)
description: Current state of small app hosting platforms as of early 2026 — pricing, reliability, persistent storage, cold starts. Focused on FastAPI/Python, ~$0-20/month budget.
type: reference
---

## Railway (railway.app) — March 2026

### Pricing (confirmed via railway.com/pricing)
- No permanent free tier. 30-day trial with $5 credits only.
- Hobby: $5/month base, includes $5 usage credits (effectively free compute for light usage)
- Pro: $20/month base, includes $20 usage credits
- Usage-based on top: Memory $0.00000386/GB-sec, CPU $0.00000772/vCPU-sec, Volumes $0.00000006/GB-sec, Egress $0.05/GB
- Small FastAPI app: ~$2-5/month actual spend

### Major Product Direction Change (2025-2026)
- **Railway Metal:** In 2024 Railway abandoned Google Cloud entirely and built own bare-metal data centers. All regions on Railway Metal by end Q1 2025.
- **$100M Series B** raised Jan 22, 2026, led by TQ Ventures (also FPV Ventures, Redpoint, Unusual). Plan: expand data center footprint globally, build AI-native cloud tools.
- Railway Metal pricing benefit: egress reduced 50% (from $0.10 to $0.05/GB), disk reduced from $0.25 to $0.15/GB for customers who migrate 80% workloads.
- Positioning: "AI-native cloud to challenge AWS."

### Reliability Incidents 2025
- **September 22, 2025:** PgBouncer upgrade caused API backend outage — dashboard, CLI, GitHub deploys all down.
- **October 28, 2025:** Postgres index creation on 1B-row table caused exclusive lock — all queries queued.
- **November 25, 2025:** Task queue failure — deployments paused across Free/Trial/Hobby tiers. Pro continued with delays.
- **December 16, 2025:** Next.js CVE-2025-55182 supply chain exploit — cryptominer deployed to compromised workloads. ~4h15m outage, <10% workloads affected, <1% private network affected. Europe West primarily.
- **45 incidents in 90 days** (per statusgator) — 10 major, 35 minor.
- Community thread "Railway is becoming unusable" (Dec 16, 2025): users threatening churn, Railway employees acknowledged issues as "100% unacceptable."

## Render

### Pricing
- Free tier: 512MB RAM, 0.1 CPU, no persistent disk, 750 hrs/month. Spins down after 15 min inactivity.
- Cold start on free tier: 30 sec–3 min (varies; user reports vary widely)
- Starter paid web service: $7/month
- Persistent disk: available on paid services only ($0.30/GB/month approximation from Postgres pricing — persistent disk exact rate not confirmed via official page)
- Zero-downtime deploys NOT available when a persistent disk is attached (Render stops old instance before starting new one)

### Notes
- Most predictable pricing of the group; fixed monthly not usage-based
- Free tier useless for persistent volume use case

## Fly.io

### Pricing (confirmed via saaspricepulse.com, 2026)
- Free tier eliminated for new customers in 2024 (replaced by 2-hour trial OR 7-day limit, whichever comes first)
- Legacy customers retain old allowances (3 shared VMs, 160GB transfer)
- Pay-as-you-go minimum ~$5/month
- Persistent volumes: billable storage; volumes survive app restarts
- Good fit for FastAPI + colocated Postgres; persistent volumes are a first-class feature

## Modal

### Pricing
- $30/month free credits for individuals (as of May 2025)
- GPU/CPU-second billing; pay only for actual invocations
- VolumeFS: persistent storage primitive, survives invocations, cross-region
- Sub-3s cold starts via memory snapshotting (even with large Python deps)
- Not a traditional "always-on" server — function-as-a-service model
- Poor fit for ChromaDB persistent vector store (no native persistent volume for arbitrary local files in the same way a VM has)

## Google Cloud Run

### Pricing + Persistence
- Generous free tier: 2M requests/month, 360K vCPU-sec, 180K GiB-sec — small FastAPI app likely free
- Cold start: ~1-2s Python. Setting min_instances=1 eliminates cold starts entirely at ~$5-8/month extra
- Persistent storage: Cloud Run itself is stateless — attach Cloud Storage (GCS) bucket as volume mount (GA 2024), or use Cloud SQL/Firestore for structured data
- GCS volume mount does NOT work well for ChromaDB (needs local filesystem POSIX semantics for SQLite). Better path: Cloud Filestore (NFS) or a dedicated Postgres with pgvector

## Coolify

- Self-hosted PaaS (open source). Runs on your own VPS.
- Not comparable to managed platforms — you own the infra. Best for: cheap VPS (Hetzner €3-5/month) + full control.
- No cold starts, persistent disk by default (it's your VM's disk).

## Recommendation Matrix (FastAPI + ChromaDB, $0-20/month, demo/prototype)

| Platform | Persistent Disk | Cold Start | True Monthly Cost | Notes |
|---|---|---|---|---|
| Railway Hobby | Yes, up to 5GB | ~500ms | ~$5-10 | Most incidents in 2025; use with awareness |
| Render Starter | Yes (paid only) | 30s-3min free; fast on paid | $7+ | Simpler ops; disk blocks zero-downtime deploy |
| Fly.io PAYG | Yes (volumes) | Configurable | ~$5-10 | Best persistence semantics; more ops complexity |
| GCR + GCS | Not native POSIX | 1-2s (or $0 w/ min=1) | ~$0-8 | GCS mount won't satisfy ChromaDB SQLite needs |
| Modal | VolumeFS only | <3s | $0 (credits) | Function model; poor fit for always-on ChromaDB |
| Coolify | Yes (VPS disk) | None | VPS cost ~$5 | Ops overhead; best value if you'll maintain infra |

**Best fit for demo FastAPI + ChromaDB, $0-20/month:** Railway Hobby or Fly.io (both support true persistent volumes with POSIX semantics that ChromaDB requires). Railway is simpler to onboard; Fly.io has better volume reliability but steeper CLI learning curve. Given Railway's 2025 reliability track record, Fly.io is the more conservative choice. If budget is truly $0, GCR free tier + SQLite on /tmp (ephemeral, acceptable for demos) is viable but ChromaDB state won't persist across cold starts.

## Source Access Patterns
- railway.com/pricing — WebFetch works, returns clean pricing table
- blog.railway.com/p/incident-* — WebFetch works, full incident reports
- station.railway.com — WebFetch works, community complaints
- render.com/docs/disks — WebFetch returns sparse content, use WebSearch for pricing
- saaspricepulse.com/tools/flyio — WebFetch works, good pricing history
- venturebeat.com — returns 429 on busy periods, skip
- medium.com — 403 on WebFetch, use WebSearch snippets
