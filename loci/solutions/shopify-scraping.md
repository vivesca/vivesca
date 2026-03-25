# Shopify Store Scraping

Any Shopify store exposes a public JSON API — no auth, no API key needed.

## Endpoints

- **All products:** `https://{store}/products.json?limit=250&page={n}`
- **Collection products:** `https://{store}/collections/{handle}/products.json?limit=250&page={n}`
- **Collections list:** `https://{store}/collections.json`
- **Single product:** `https://{store}/products/{handle}.json`

## Key details

- Max 250 products per page (Shopify limit). Paginate until empty response.
- Rate limit: ~2 req/s (Shopify default). 500ms sleep between pages is safe.
- Product data includes: id, title, handle (model number), body_html, vendor, product_type, tags, variants (with SKU, price, availability, images), images (with CDN URLs, dimensions).
- Frame specs and other structured data often live in **tags** rather than body_html.
- Images are on Shopify CDN (`cdn.shopify.com`), direct download, no hotlink protection.
- `robots.txt` is Shopify boilerplate — blocks checkout/cart/admin, not product endpoints.

## Gender/category filtering

Tags are free-form. Common patterns: `MEN`, `WOMEN`, `UNISEX`, `KIDS`. Many older products have no gender tags — "exclude explicitly women-only + kids" is more complete than "include explicitly men's."

## Identifying Shopify stores

- Check page source for `cdn.shopify.com` or `Shopify.theme`
- Check `robots.txt` — Shopify stores have a distinctive comment block about checkout bots
- `/products.json` returning valid JSON confirms it

## Example: Zoff HK

- Store: `hk.zoff.com` (not `zoff.com.hk`)
- 278 products across 2 pages
- Frame specs in tags as `51□19-145` (lens□bridge-temple)
- Color variants in option1, SKU pattern: `MODEL_COLORCODE`
- CLI: `~/code/zoff-scraper/`, installed at `~/bin/zoff`
