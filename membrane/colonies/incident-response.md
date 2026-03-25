---
name: incident-response
description: Coordinated response to a system break — triage, research, fix, verify in parallel.
product: fixed system + incident report
trigger: something broke and needs coordinated fast response
---

## Lead (opus)
Triage — assess severity, coordinate workers, decide fix strategy.
Produces incident report after resolution.

## Workers (sonnet, parallel)
- **diagnostician**: read logs, trace the error, identify root cause
- **fixer**: implement the fix once root cause is identified
- **verifier**: run tests, verify the fix doesn't break other things

## Protocol
1. Lead assesses severity: is this blocking? Data loss risk?
2. Diagnostician traces root cause (reads logs, git blame, error patterns)
3. Lead reviews diagnosis, approves fix strategy
4. Fixer implements (sequential with diagnostician, parallel with verifier prep)
5. Verifier runs full test suite
6. Lead produces incident report: what broke, why, fix, prevention
7. Colony dissolves

## Cost gate
~$2-4 per incident. Only for breaks that affect multiple components.
Single-file bugs = single bud. Don't form a colony for a typo.
