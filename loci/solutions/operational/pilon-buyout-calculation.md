# PILON Buyout Calculation — HK Employment Ordinance

## Key Lesson (Feb 2026)

The calculation method depends on how the **contract** expresses the notice period:

- **"X months' notice"** → PILON = average monthly wages × months (or pro-rata for partial)
- **"X days' notice"** → PILON = average daily wages × days (but EO daily wage excludes rest days from denominator — NOT simply salary × 12 / 365)

**Always check the actual contract clause.** Stella (CNCBI HR) said "21 days × daily average wages" but the contract said "2 months' notice" (Clause 5.1(c)). Different formula, different number.

## EO Average Daily Wage

Per [1823.gov.hk](https://www.1823.gov.hk/en/faq/how-to-calculate-the-notice-period-or-payment-in-lieu-of-notice-upon-termination-of-employment):

Excludes from the denominator: rest days, statutory holidays, annual leave, sick leave, maternity/paternity leave, days employer provided no work. Both the days AND wages for those days are stripped out.

This means the daily rate is HIGHER than `monthly × 12 / 365`.

## Tax Gross-Up

Capco reimbursement of PILON is taxable income. True gross-up formula:

```
gross_payment = net_amount / (1 - marginal_tax_rate)
```

NOT simply `net + (net × rate)`. At 15% standard rate: 74k / 0.85 = ~87k (not 74k + 11k = 85k).

## Message Strategy (from 2 council rounds)

- Split PILON from gross-up — don't bundle into one ambiguous number ("80k including tax")
- Use ceiling numbers for budget approvals — COOs approve budgets, not ranges
- When relaying through an intermediary (recruiter), make numbers copy-pasteable
- If you secretly prefer the fallback (Apr 8), a clean number still serves you — let the company decide
