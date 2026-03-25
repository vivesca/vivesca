---
name: ingestion
description: Suggest lunch from meal plan + log what was eaten. "lunch", "what to eat", "log lunch"
user_invocable: false
---

# ingestion -- meal suggestion + logging

Two modes: **suggest** (default) and **log**.

## Suggest

1. Read `~/epigenome/chromatin/Health/Weekly Meal Plan - Taikoo Place.md` -- the rotation and order log are both in this file.
2. Run `date '+%A'` to get today's day of week.
3. Check the last 3 entries in the order log section.
4. Suggest based on:
   - Today's rotation slot (day -> restaurant + dish)
   - If same restaurant appears 2+ times in last 3 entries, suggest the alternate from rotation
   - Gym vs rest day (check readiness from Tonus if available -- gym days favour protein + omega-3)
5. Present: restaurant, dish, one line. Don't over-explain.

## Log

After Terry eats (or when he says "log lunch"):

1. Ask what he had if not already mentioned in conversation.
2. Append to the `## Order log` section of the meal plan file:
   ```
   - YYYY-MM-DD (Day): Restaurant, dish. Lunch/Snack.
   ```
3. Confirm with one line.

## Principles

- One suggestion, not a menu. If the rotation says X and history supports it, just say X.
- Don't ask "want me to check?" -- checking is the point.
- Keep the order log chronological, newest last.
