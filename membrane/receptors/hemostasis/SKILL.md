---
name: hemostasis
description: Emergency stabilization — stop the bleeding, not fix it. "stop the bleeding"
user_invocable: true
model: sonnet
---

# Hemostasis — Clot First, Heal Later

Hemostasis is the body's emergency bleeding response. It doesn't heal the wound — it stops the loss long enough for healing to begin. Platelets aggregate, clot forms, bleeding stops. Repair comes later.

This skill is not debugging. It is not root cause analysis. It is not fixing. It is: stop the organism from losing more than it already has.

## When to Use

- A process is running and consuming resources (CPU, tokens, money, time) with no useful output
- A pipeline is cascading failures downstream
- Data is being corrupted or lost
- A service is down and taking dependent services with it
- You don't know what's wrong yet but you know it's getting worse

## The Hemostasis Protocol

### Phase 1 — Tourniquet (< 2 minutes)

Stop the active bleeding immediately. Don't investigate yet.

Candidates:
```bash
# Kill the runaway process
pkill -f process-name

# Disable the failing LaunchAgent
launchctl unload ~/Library/LaunchAgents/failing.plist

# Pause the scheduled job
launchctl unload -w ~/Library/LaunchAgents/job.plist

# Revert the last change
git revert HEAD --no-edit

# Disable the failing endpoint
# (comment out, feature flag, nginx 503)
```

Pick the fastest clot, not the best fix.

### Phase 2 — Stabilize (< 10 minutes)

Assess what's still bleeding after the tourniquet:
- What downstream systems depended on the stopped process?
- Is any data still being lost or corrupted?
- Is the organism in a state that will cause further harm if left?

Apply secondary clots as needed.

### Phase 3 — Handoff note

Before leaving hemostasis mode, write three lines:
1. What was stopped and why
2. What is currently broken as a result (known gaps)
3. What the next person (or future session) needs to do to resume

Do not skip this. Hemostasis without a handoff note causes secondary hemorrhage when someone unknowingly restarts the stopped process.

## What Hemostasis Is Not

- Not root cause analysis (that's palpation or auscultation)
- Not cleanup (that's debridement)
- Not a fix (fix comes after)

## Anti-patterns

- **Diagnosing while bleeding:** spending 20 minutes understanding the problem while the damage compounds. Stop first, understand second.
- **Overtightening the tourniquet:** shutting down more than necessary. Match clot to wound. Don't kill the organism to save it.
- **No handoff note:** hemostasis without documentation leaves the wound reopenable.
