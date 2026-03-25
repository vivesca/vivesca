---
name: little-monster-playhouse
description: Check opening hours and walk-in availability for Little Monster Playhouse in Chai Wan. Use when user asks about "Little Monster", "小怪獸遊戲室", or "Chai Wan playhouse".
---

# Little Monster Playhouse Schedule

Check opening hours and walk-in availability for Little Monster Playhouse in Chai Wan.

## Trigger

Use when:
- User asks about "Little Monster playhouse hours"
- User says "Is Little Monster open today", "小怪獸遊戲室"
- User asks about "Chai Wan playhouse schedule"

## Inputs

- **date** (optional): Date to check, defaults to today

## Key Information

- **Location:** 柴灣寧富街3號誠興大廈10樓全層 (10/F, Shing Hing Commercial Building, 3 Ning Fu Street, Chai Wan)
- **Access:** 1 min walk from MTR Chai Wan Station via flyover
- **Price:** $148/hour (1 adult + 1 child) — often have "Buy 1 Hour Get 1 Free" promotions
- **Walk-ins:** Accepted ("預約/ Walk-in 均可")
- **Contact:** Littlemonsterplayhouse@gmail.com

## Workflow

1. **Navigate to Instagram** schedule post:
   - Profile: https://www.instagram.com/littlemonster_playhouse/
   - They post monthly "散場時間表" around end of each month
   - Current schedule post: https://www.instagram.com/p/DS9YM5pkpuU/

2. **Read the schedule**:
   - **Green cells:** Open for walk-in with times shown
   - **Yellow "Deep Cleaning":** Closed
   - **"Fully Booked":** No walk-in available

3. **Zoom in on specific date** user is asking about

4. **Report hours** with contact info for confirmation

## Error Handling

- **If Instagram shows login popup**: Click X to dismiss
- **If "Profile isn't available"**: Try specific post URL instead
- **If image compressed (1 vs 6 unclear)**: Ask user to verify from original
- **If schedule not found**: Provide contact info for direct inquiry

## Output

- Opening hours for requested date
- Contact info for confirmation
- Note about common patterns

## Common Patterns

- **Weekdays (Tue/Wed/Fri):** Usually 1:00 - 6:00 pm
- **Saturdays:** Varies (10am-1pm, 10am-2pm, 10am-3pm, or 10am-6pm)
- **Sundays:** Usually 10:00 am - 1:00 pm (or Fully Booked)
- **Mon/Thu:** Often Deep Cleaning days

**Note:** Always verify with actual schedule as hours change monthly.
