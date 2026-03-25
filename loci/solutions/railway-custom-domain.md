# Railway Custom Domain Setup

## What Railway actually needs

1. **ALIAS (or CNAME) record** — target is the Railway-assigned subdomain shown in "Show DNS records" in the Railway dashboard (e.g. `35htonnv.up.railway.app`). This is NOT the same as the service URL (`lacuna-production-8dbb.up.railway.app`).
2. **TXT verification record** — `_railway-verify` with value from the dashboard. Without this, Railway won't provision the SSL cert even if DNS resolves correctly.

## Vercel DNS commands

```bash
vercel dns ls lacuna.sh                                        # inspect current records
vercel dns add lacuna.sh @ ALIAS 35htonnv.up.railway.app      # apex ALIAS
vercel dns add lacuna.sh _railway-verify TXT "railway-verify=<hash>"  # verification
echo "y" | vercel dns rm <record-id>                          # remove a record
```

## Diagnosing issues

- `x-railway-fallback: true` in curl response = Railway edge can't route to your service. Check ALIAS target is correct per dashboard.
- SSL still wildcard (`*.up.railway.app`) after 30+ min = TXT verification record missing.
- `railway domain lacuna.sh` returns "Domain is not available" = domain already added (not an error).
- DNS target to use: always read from Railway dashboard → domain → "Show DNS records". Never guess from service URL.

## Timeline

After adding both records: SSL typically provisions within 5–15 minutes.
