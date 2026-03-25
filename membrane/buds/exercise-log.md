---
name: exercise-log
description: Review and log gym sessions from daily notes. Track volume, gaps, progression.
model: sonnet
tools: ["Bash", "Read", "Grep", "Glob"]
---

Review and log gym sessions from the week's notes.

1. Read recent daily notes: ~/epigenome/chromatin/Daily/ (last 14 days)
2. Search for gym mentions: grep for "gym", "PURE", "upper body", "bike", "zone 2", "recumbent"
3. Extract per session:
   - Date
   - Type: upper body strength / zone 2 cardio / mixed
   - Duration if mentioned
   - Key exercises or weights if noted
   - Readiness/energy level if mentioned

4. Compare against target cadence:
   - Upper body: 3x per week
   - Zone 2 bike: alongside gym or separate
   - Rest days: check Oura readiness vs actual rest

5. Flag:
   - Gaps > 3 days in upper body training
   - Sessions where readiness was < 70 but trained hard anyway
   - Weeks with < 2 sessions

6. Volume trend: is training load increasing, stable, or declining?

Output: table of sessions + gap analysis + one observation on progression.
Save log to ~/epigenome/chromatin/Health/gym-log-YYYY-WNN.md if session data found.
