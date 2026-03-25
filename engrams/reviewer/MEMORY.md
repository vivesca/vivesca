# Reviewer Agent Memory

## Readwise Synthesis Documents (Terry's vault)

**Pattern:** Terry generates synthesis notes from Readwise batches covering 40-60 articles.
Good ones have: editorial voice, named sources, concrete metrics, a "Key Non-Obvious Findings" section.
Weak spots to check:
- Unattributed "production experience" sections that present first-person practitioner views as generic consensus
- `mailto:reader-forwarded-email/...` source URLs — these are dead ends, flag them
- Widely-cited but unconfirmed metrics presented as settled (e.g. GPT-4 training cost ~$100M)
- Insight duplication across sections (same stat repeated 2-3x without adding meaning)
- Conclusions in the Key Findings section that go further than the cited evidence supports

**Format check:** Frontmatter uses `date`, `tags`, `sources`. Tags should be lowercase. `sources: readwise-batch` is Terry's convention for synthesised batches.

## Rust CLI Patterns (Terry's tools: fingo, stips, etc.)

**Keychain account name:** Terry's CLIs use `security find-generic-password -s <service> -w`. Hardcoding a personal username (`"terry"`) as `KEYCHAIN_ACCOUNT` is a recurring risk — check this constant before any crates.io publish. Should be a generic string like `"api-key"` or the service name itself.

**Placeholder model names in constants:** Check `DEFAULT_*` model constants and `Cargo.toml` description for internal codenames (e.g. `nano-banana-pro-preview`) before publish. These surface in `--help` output and package metadata.

**`mask_api_key` short-key overlap:** Pattern in both fingo and stips — `chars[..first_len]` and `chars[..last_len]` overlap on keys shorter than `first_len + last_len`. Always guard with `.max(first_len)` on the suffix start.

**Dual camelCase/snake_case serde fields:** When Gemini API returns inconsistent casing, prefer `#[serde(rename = "inlineData", alias = "inline_data")]` on a single field over two separate fields with an `.or()` fallback. Both work; single field is cleaner.

**ureq v3 agent-per-call:** Constructing a new `ureq::Agent` inside a per-call function is harmless for CLI single-shot use but misleading if batching is later added. Flag for batching paths.

**`is_image_capable` heuristics tied to placeholder names:** Model filter keyword lists that contain placeholder names (`"banana"`) will silently break when model names are corrected. Review these alongside any model constant changes.

## Chrome Cookie Decryption (porta, photoferry pattern)

**DB version read:** Chrome's `meta.version` is stored as TEXT. Always use `row.get::<_, String>(0)` then `.parse::<i64>()` — never `get::<_, i64>()` directly or it silently returns 0. With version=0, the SHA256 prefix strip is skipped, producing binary garbage in every cookie value.

**SHA256 prefix (DB v24+):** Strip `&decrypted[32..]` when `db_version >= 24 && decrypted.len() > 32`. This is unconditional — no hash verification needed.

**Firefox expiry vs Chrome expiry:** Firefox `expiry` is Unix seconds — pass through directly. Chrome `expires_utc` is Windows FILETIME microseconds — convert with `/ 1_000_000 - 11_644_473_600`.

**SQL injection in domain filter:** Both `chrome.rs` and `firefox.rs` in porta use `format!()` to build SQL `LIKE` queries. A domain filter with `'` or `%` in it can corrupt or inject. Low risk for personal tools but flag it.

**Inline cookie JSON in Python scripts:** Embedding `cookies_json` directly in a Python `r'''...'''` string in inject.rs breaks if any cookie value contains `'''`. Safe alternative: write JSON to a separate temp file and load it from Python.

**`is_auth_cookie` keyword list for Google domains:** Names like `SAPISID`, `APISID`, `1PSID` don't match common keywords (`session`, `auth`, `token`, `login`, `credential`). `"sid"` catches `SID`/`HSID` but not `SAPISID`. Result: watch mode injects every cycle for Google domains (functional but wasteful).

## General Patterns

**Unverified cost/spec numbers in AI industry docs:** Training cost comparisons (GPT-4, Claude, Gemini) almost never have primary source confirmation. Flag any comparison that presents both figures as hard facts without attribution.

**Self-reported company goals:** Treat startup/lab positioning ("our goal is safety through design") as marketing unless accompanied by published research or independent verification. Don't let it read as factual in a synthesis doc.

**`mailto:` links in Sources sections:** Not navigable. Flag to replace with actual URLs or mark as `[forwarded email, no URL]`.
