---
name: migration
description: Coordinated multi-component migration — rename, restructure, update paths, verify integrity. Workers execute in parallel on isolated domains, verifier checks nothing broke.
product: migrated codebase/system with zero broken references and a migration log
trigger: rename or restructure affecting 3+ components that cannot be done safely by one sequential agent
---

## Lead (opus)
Plans the migration before any file is touched.
Produces the dependency map: what depends on what, which can move in parallel, which must be sequential.
Reviews verifier report and signs off.

## Workers (sonnet, parallel where safe)
- **domain-worker-N**: each worker owns one isolated domain (e.g., one service, one config namespace, one directory subtree) — renames, moves, updates internal references within that domain only
- **cross-reference-worker**: after domain workers complete, hunts cross-domain references and updates them (imports, symlinks, config values pointing across domains)
- **verifier**: runs tests, checks for broken imports, dangling references, missing files — produces a pass/fail report with specific failures

## Protocol
1. Lead reads the migration brief — what is moving, why, what must not break
2. Lead produces the dependency map: identifies parallel-safe domains, flags sequential dependencies
3. Domain workers run in parallel on their isolated domains — no worker touches another's domain
4. Cross-reference-worker runs after domain workers complete
5. Verifier runs full check: tests, import resolution, grep for old paths still in use
6. If verifier finds failures: lead triages, dispatches targeted fix worker, re-verifies
7. Lead produces migration log: what moved, what changed, any manual follow-ups required
8. Colony dissolves

## Cost gate
~$3-6 depending on scope. Justified when: moving 3+ components, cross-component references exist, or rollback would be expensive. Single-component rename = single bud with sed. Don't form a colony for a two-file rename.

## Dissolution rule
Dissolves only after verifier passes clean. A migration that is "mostly done" is not done. Colony stays active until verifier signs off.
