# URL Shortener Module Spec

Module: `shortener.py`
Class: `URLShortener`

## API

### `shorten(url: str) -> str`
- Takes a full URL, returns a 6-character short code
- Same URL always returns the same code (idempotent)
- Raises `ValueError` if URL is empty or not a valid http/https URL

### `expand(code: str) -> str`
- Takes a short code, returns the original URL
- Raises `KeyError` if code not found

### `list_urls() -> dict[str, str]`
- Returns dict mapping all short codes to original URLs
- Empty dict if nothing stored

### `delete(code: str) -> bool`
- Deletes a short code mapping
- Returns True if deleted, False if code didn't exist
- After deletion, `expand(code)` should raise KeyError

## Constraints
- Short codes are exactly 6 alphanumeric characters
- Thread safety is NOT required
- No persistence — in-memory only
