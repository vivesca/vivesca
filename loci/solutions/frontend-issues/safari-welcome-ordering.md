---
title: Safari welcome ordering breaks when delay array length mismatches
category: frontend-issues
module: public/app.js
symptoms:
  - Safari/iOS shows tour chips before welcome messages
  - Welcome lines render out of order despite gating logic
root_cause:
  - WELCOME_DELAYS array had fewer entries than welcome messages; adding a new welcome line produced NaN timeouts in Safari
fix:
  - Compute delays dynamically from message count and use a default fallback
  - Trigger chips only after final welcome message renders
  - Optional: insert welcome messages above any early chip container as safety net
verification:
  - iOS Safari renders welcome lines in order, chips appear after last line
---

## Summary
Adding a new welcome line without updating the delays array caused `NaN` timeouts in Safari, which reordered the UI. Compute delays from message count instead of hardcoding.
