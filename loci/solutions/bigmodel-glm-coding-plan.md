# bigmodel.cn GLM Coding Plan

## What It Is

GLM Coding Plan is a **subscription for interactive coding tools** (Claude Code, OpenCode, Cursor, Cline, etc.) — NOT an API plan. Bigmodel.cn's docs explicitly state:

> "单独调用 API 是独立计费的，不可享用 Coding 套餐的额度"
> ("Standalone API calls are billed separately and cannot use the Coding plan quota.")

## Terry's Plan

- **Plan:** GLM Coding Max — Annual
- **Valid until:** 2027-01-28
- **Cost:** ¥1920/year
- **Quota:** 1600 prompts / 5-hour window, 8000 prompts / week
- **GLM-5 quota cost:** 2× (off-peak) or 3× (peak 14:00–18:00 HKT) vs GLM-4.7

## Plans Available

| Plan | Price | Quota (5h/week) |
|------|-------|-----------------|
| Lite | ¥132/quarter | 80 / 400 prompts |
| Pro  | ¥402/quarter | 400 / 2000 prompts |
| Max  | ¥1266/quarter | 1600 / 8000 prompts |

## Supported Tools

Claude Code, OpenCode, Cursor, Cline, Roo Code, Kilo Code, Crush, Goose, OpenClaw, etc.

## Billing Separation

- **OpenCode** → uses Coding Plan quota (configured via `zhipuai-coding-plan/glm-5`)
- **Consilium API calls** → separate pay-as-you-go via `api.z.ai` (¥4-6/M input, ¥18-22/M output for GLM-5)
- **Cannot** route consilium through OpenCode subprocess to use plan quota — too slow, fragile, and violates terms

## Key Pages

- Plan details: `https://bigmodel.cn/glm-coding`
- My plan: `https://bigmodel.cn/usercenter/glm-coding/my-plan`
- Pricing: `https://bigmodel.cn/pricing`
- Docs: `https://docs.bigmodel.cn/cn/coding-plan/overview`

## Browsing Notes

- Portal uses CAPTCHA — must login manually in Chrome first, then `porta inject --domain bigmodel.cn`
- Cookie injection was successful — navigation worked via agent-browser after injection
