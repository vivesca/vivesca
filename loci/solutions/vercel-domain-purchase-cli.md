# Vercel Domain Purchase via CLI

## Pricing

Check price via API (no auth needed for availability, auth needed for price):
```bash
VERCEL_TOKEN=$(cat "/Users/terry/Library/Application Support/com.vercel.cli/auth.json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('token',''))")
curl -s "https://api.vercel.com/v1/registrar/domains/<domain>/price" -H "Authorization: Bearer $VERCEL_TOKEN"
# Returns: {"years":1,"purchasePrice":22,"renewalPrice":60,"transferPrice":60}
```

## Buying via CLI

`vercel domains buy <domain>` is interactive — prompts for buy confirmation, auto-renew, and full contact info. Piped input (`echo y | vercel...`) fails because the CLI detects non-TTY.

**Solution: use `expect`**

```bash
cat > /tmp/buy-domain.exp << 'EOF'
#!/usr/bin/expect -f
set timeout 60
spawn vercel domains buy lacuna.sh
expect "Buy now"      ; send "y\r"
expect "Auto renew"   ; send "n\r"
expect "First name"   ; send "Terry\r"
expect "Last name"    ; send "Li\r"
expect "Email"        ; send "terry.li.hm@gmail.com\r"
expect "Phone"        ; send "+85261872354\r"
expect "Address"      ; send "Flat G, 9/F, Tower 1, Grand Promenade\r"
expect "City"         ; send "Sai Wan Ho\r"
expect "State"        ; send "HK\r"
expect "Postal"       ; send "N/A\r"
expect "Country"      ; send "HK\r"
expect "Company"      ; send "\r"
expect eof
EOF
expect /tmp/buy-domain.exp
```

**Gotchas:**
- `expect` is case-sensitive — prompts use "Country" (capital C), not "country"
- CLI may show "unexpected error" even on successful purchase — verify with `vercel domains ls`
- Contact info is sourced from Vercel billing: `curl -s "https://api.vercel.com/v2/teams/$TEAM" -H "Authorization: Bearer $VERCEL_TOKEN"` → `.billing.address`
- HK has no postal code — use `N/A`
- Apex domain CNAME → use ALIAS record type (Vercel rejects CNAME for `@`):
  ```bash
  curl -s -X POST "https://api.vercel.com/v2/domains/<domain>/records?teamId=$TEAM" \
    -H "Authorization: Bearer $VERCEL_TOKEN" -H "Content-Type: application/json" \
    -d '{"type":"ALIAS","name":"","value":"<railway-cname>.up.railway.app","ttl":60}'
  ```

## Token location

`/Users/terry/Library/Application Support/com.vercel.cli/auth.json` → `.token`

## .sh TLD pricing (2026)

| Registrar | First year | Renewal |
|-----------|-----------|---------|
| Vercel | $22 | $60/yr |
| Porkbun | $31.20 | $46.65/yr |
| Cloudflare | not supported | — |
