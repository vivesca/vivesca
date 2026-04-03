---
name: salus
description: "Manulife health insurance claims checker CLI. Use when checking claim status, reimbursement amounts, or claim history. Commands: salus claims, salus claims --all."
---

# salus — Manulife Claims Checker

Binary: `~/bin/salus` (symlink to `~/code/target/debug/salus`)
Source: `~/code/salus/`

## Commands

```bash
salus claims        # Show last 10 claims (page 1)
salus claims --all  # Paginate through all claims
```

## How it works

Shells out to `agent-browser` to automate the Manulife portal. Full login flow including OTP via Gmail. Uses persistent profile (`AGENT_BROWSER_PROFILE`) — if session is still alive, login is skipped.

Credentials fetched from 1Password: `op item get "Manulife" --vault Personal --fields username/password`
Falls back to stdin prompt if 1Password unavailable.

## Portal Details (confirmed Mar 2026)

- **Login URL:** `https://individuallogin.manulife.com.hk/thf/auth/signIn?lang=en_US`
- **Username:** `TERRYLIHM` (not email address)
- **Claims URL:** `https://individuallogin.manulife.com.hk/tfm/eclaim/myClaim?lang=en_US`
- **Claims nav path:** Login → Claims & Services → View my claims → Claim Records tab

## Known Gotchas

**Angular buttons need real mouse events.** `agent-browser click @ref` and synthetic `.click()` don't fire Angular handlers. Must dispatch `mousedown + mouseup + click` sequence. Used for: Send OTP button, Continue button. Confirmed working pattern:
```js
['mousedown','mouseup','click'].forEach(e => btn.dispatchEvent(new MouseEvent(e, {bubbles:true, cancelable:true, view:window})))
```

**OTP email — `gog gmail show` only returns first message in thread.** All OTP emails thread together. Use `gog gmail thread get <id>` to read all messages and get the latest OTP. The OTP is the bold 6-digit number in the body; `Ref: XXXXXX` at the end is NOT the OTP.

**OTP expires in 5 minutes.** Read email and submit immediately after `Send OTP`. If expired, the page shows "Incorrect OTP entered" with a Resend option.

**`myservices.manulife.com.hk` is NXDOMAIN.** Retired. All access via `individuallogin.manulife.com.hk`.

**Session persistence.** Login skipped if current URL is not `individuallogin`. Run `porta inject --browser chrome --domain manulife.com.hk` to restore session from Chrome if stale.

**Claims `--all` pagination.** Uses `ul li` text matching for page numbers. May need updating if Manulife changes pagination markup.

## Output

Fixed-width table, ANSI-bold on PAID column:
```
DATE         CLAIM#        MEMBER              BENEFIT                        CCY   CLAIMED    PAID    STATUS
02 Mar 2026  260612089E    LI HO MING TERRY    Physiotherapy Treatment        HKD   1,450.00   800.00  Processed
```

## Benefit Cap Notes

- **Physiotherapy:** $800/claim cap (confirmed Mar 2026 — $1,450 claimed, $800 paid)
- **Body check ("Routine Physical Examination"):** ~$840/year annual cap — separate from Plan C $2,800 limit
- **Specialist:** $800/claim cap
- Full details: `~/docs/solutions/operational/manulife-simpleclaim-gotchas.md`
