# Pharos Migration Options — Cost Analysis
_Generated 2026-03-20. Pharos = Ubuntu 24.04 on EC2 t3.small (ap-southeast-1). Runs: Obsidian sync daemon, vault-git-backup, OpenCode, Tailscale, systemd user timers. 2 GB RAM, swap essential._

## Comparison Table

| Option | Cost/month | Specs | HK Latency | Pros | Cons | Migration effort |
|--------|-----------|-------|-----------|------|------|-----------------|
| **Current: AWS t3.small** | ~$26 USD | 2 vCPU, 2 GB RAM, ap-southeast-1 | ~10 ms (SG→HK) | Known working, same region | Expensive for workload | — |
| **Hetzner CX23** (Singapore) | ~$3.80 USD (EUR 3.49) | 2 vCPU, 4 GB RAM, 40 GB NVMe | ~30–50 ms est. (SG→HK) | More RAM than t3.small, 20 TB traffic, cheap | No HK DC; SG latency slightly higher than AWS SG | Low — same region, Ubuntu, systemd |
| **Hetzner CX33** (Singapore) | ~$6.00 USD (EUR 5.49) | 4 vCPU, 8 GB RAM, 80 GB NVMe | ~30–50 ms est. | Headroom for growth, best price/perf | Overkill for current load | Low |
| **Oracle Cloud Free Tier** | $0 | 4 OCPU ARM, 24 GB RAM, 200 GB block | Tokyo/Seoul DC (no SG/HK) | Free forever, generous specs | ARM (minor compat risk); provisioning unreliable; no SG/HK DC; Oracle account risk | Medium — ARM arch, new account |
| **Mac Mini at parents' home** | ~HKD 4–13/mo (~$0.50–1.70 USD) elec. only | M4: idle 3–7 W; full load ~60 W | ~5 ms (same city) | Near-zero ongoing cost, lowest latency, full control | Dynamic IP (needs DDNS), home ISP reliability, NAT/port-forward setup, hardware failure = manual fix, parents must not unplug | High — DDNS, port-forward, VPN/Tailscale, UPS recommendation |
| **Fly.io** (sin region) | ~$2–5 USD | Shared CPU, 256 MB–1 GB RAM | ~30–50 ms (SG) | Simple deploys, close region | Per-service model awkward for Pharos's multi-daemon setup; RAM constrained | High — rearchitect as Fly apps |
| **Render** | ~$7 USD | 1 vCPU, 1 GB RAM | Virginia/Oregon/Frankfurt | Free tier too limited; paid reasonable | No Singapore; latency ~150–250 ms to HK; worse than AWS for this use case | High + latency regression |

## Notes

**CX22 is discontinued** as of Feb 2026. CX23 is the replacement — same specs (2 vCPU, 4 GB RAM) but cheaper at EUR 3.49 vs old EUR 3.79.

**Hetzner Singapore latency to HK:** No published benchmark. Singapore→Tokyo is ~70 ms; Singapore→HK is typically 30–50 ms on good routes. AWS ap-southeast-1 (SG) to HK is ~10–15 ms due to AWS's private backbone. Hetzner will be slightly higher but acceptable for background daemons (Obsidian sync, git backup).

**Mac Mini power estimate:** M4 at 7 W average (light server load) = ~HKD 6/mo (~$0.80 USD). Even at 15 W = HKD 13/mo ($1.70 USD). Electricity cost is negligible; the real costs are setup complexity and reliability.

**Oracle free tier caveat:** ARM Ampere A1 instances. Most Pharos tooling (bun, opencode, cargo binaries) has ARM Linux builds, but the provisioning lottery and Oracle's history of reclaiming "idle" free instances make it unsuitable for a critical sync daemon without a paid fallback.

## Recommendation

**Hetzner CX23 (Singapore)** — saves ~$22/month vs AWS, more RAM (4 GB vs 2 GB), same region, minimal migration effort. Ubuntu 24.04 → Ubuntu 24.04, same systemd setup, Tailscale re-joins cleanly. Migration: provision, rsync home dir, re-enable linger, update Tailscale, update `~/.ssh/config` with new IP.

**Mac Mini** is compelling if reliability is acceptable — near-zero cost, lowest latency. Block on: parents' home having stable internet + UPS, and willingness to set up Tailscale exit/subnet routing. Worth revisiting if Hetzner SG latency proves annoying in practice.
