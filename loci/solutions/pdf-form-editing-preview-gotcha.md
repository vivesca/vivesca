# Preview PDF Form Editing — Silent Field Corruption

## Problem

When editing fillable PDF forms in macOS Preview, changing one field can silently corrupt adjacent fields. Observed: editing phone number changed DOB to today's date, changed "LI" to "Li", and reverted "LI, HO MING TERRY" block letters to mixed case.

## Why It Happens

Preview's form field handling is fragile — clicking into adjacent fields while editing can overwrite or reset them, especially with date-formatted fields.

## Fix

Always do a **full re-review of all fields** after any edit pass — not just the field you changed. Treat each Preview save as a potential corruption event.

For critical forms (legal, onboarding), have a second pair of eyes review before sending.
