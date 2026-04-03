---
name: taobao
description: Reference for accessing Taobao/Tmall product pages and analysing products. Consult when user shares Taobao links.
user_invocable: false
---

# Taobao Product Research

Reference skill for when users share Taobao/Tmall product links (`e.tb.cn`, `item.taobao.com`, `detail.tmall.com`).

## Access Pattern

Taobao/Tmall is a walled garden. Jina Reader, WebFetch, and unauthenticated browsers all fail.

### Login Flow

```bash
# 1. Open the link (redirects to login page)
agent-browser --profile -- open "https://e.tb.cn/SHORT_CODE"

# 2. Screenshot to check state
agent-browser screenshot /tmp/taobao-login.png

# 3. The `click` command often fails on Taobao's login button.
#    Use JS eval instead:
agent-browser eval "document.querySelector('button.fm-submit').click(); 'clicked'"

# 4. Wait for redirect, then verify
sleep 3 && agent-browser screenshot /tmp/taobao-product.png

# 5. Extract product details
agent-browser eval "document.body.innerText.substring(0, 3000)"
```

**Gotchas:**
- `agent-browser click "快速进入"` hangs/fails — always use the JS eval approach
- Login session persists across navigations within the same browser session
- Short links (`e.tb.cn`) resolve to `item.taobao.com` or `detail.tmall.com` after login
- If "快速进入" button isn't available (no saved session), user must scan QR code on phone

### Multiple Products

Once logged in, navigate to each link sequentially:
```bash
agent-browser open "https://e.tb.cn/NEXT_LINK"
agent-browser eval "document.body.innerText.substring(0, 3000)"
```

## Product Analysis Framework

### Key Fields to Extract

| Field | Where to Find | Why It Matters |
|-------|---------------|----------------|
| Price (券后) | Main listing | Real price after coupons; ignore 优惠前 (inflated original) |
| 配料表 | 参数信息 section | Actual ingredients — check order (first = highest proportion) |
| 是否保健食品 | 参数信息 section | "否" = ordinary food, legally cannot claim health benefits |
| 生产许可证编号 | 参数信息 section | SC prefix = legit; verify at [国家企业信用信息](http://www.gsxt.gov.cn/) |
| 生产日期 | 参数信息 section | Check freshness relative to shelf life |
| 净含量 + dosing | SKU options | Calculate daily dose; compare against therapeutic thresholds |
| Reviews (评价标签) | 用户评价 section | Taobao auto-generates tag clouds — look for negative tags |
| Store rating | Store header | 88VIP好评率, 发货速度, 客服满意度 |
| Sales volume | Main listing | "已售 X+" — social proof but not quality signal |

### Red Flags

1. **Coupon theatre:** ¥338→¥98 discounts — original price was never real
2. **Kitchen sink formulas:** 10+ ingredients in a small package = sub-therapeutic doses of everything
3. **Ordinary food making health claims:** "好眠", "助眠" on non-保健食品 products is legally dubious
4. **Invented marketing terms:** "100%静安原浆", "非遗" — verify or flag as [unverified]
5. **Review astroturfing:** Specific, detailed positive reviews appearing in clusters = likely paid
6. **Same store, multiple SKUs:** Often the same product in different packaging at different price points

### Health/TCM Product Specifics

When evaluating TCM-style health products:

1. **Identify the lead ingredient** — what's the active compound? Search for clinical evidence
2. **Check delivery format vs evidence:** Clinical trials typically use decoctions or standardised extracts, not tea bags
3. **Calculate dose per serving:** Total weight / number of ingredients / servings per day. Compare against pharmacopoeia doses
4. **Ingredient economics:** If wholesale cost of lead ingredient > retail price per dose, the product can't contain meaningful amounts
5. **Search Chinese sources for criticism:** `"[product type] 智商税"`, `"[product type] 有用吗"`, `"[ingredient] 含量 不足"`

### CLAUDE.md Product Research Rules Apply

- Never recommend purchase in the same session as research
- Red-team every frontrunner: search "[product] problems/returns/disappointed"
- Personal (body/taste/fit): 15 min shortlist max, then try in person
