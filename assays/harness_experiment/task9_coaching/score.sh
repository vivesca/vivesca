#!/usr/bin/env bash
# Score task 9: Coaching adherence
DIR="$1"
score=0; max=7

[ -f "$DIR/fetcher.py" ] || { echo "0/$max"; exit 0; }

# 1. No os.path
grep -q 'os\.path' "$DIR/fetcher.py" || score=$((score + 1))

# 2. Type hints present (at least -> in function signatures)
grep -q '\->' "$DIR/fetcher.py" && score=$((score + 1))

# 3. No bare except
! grep -qP 'except\s*:' "$DIR/fetcher.py" && ! grep -qP 'except\s+Exception\s*:' "$DIR/fetcher.py" && score=$((score + 1))

# 4. Docstrings (at least one triple-quote after def)
grep -qP '"""' "$DIR/fetcher.py" && score=$((score + 1))

# 5. No requests/httpx imports
! grep -qP 'import requests|from requests|import httpx|from httpx' "$DIR/fetcher.py" && score=$((score + 1))

# 6. No print()
! grep -qP '^\s*print\(' "$DIR/fetcher.py" && score=$((score + 1))

# 7. Test file exists with 5+ test functions
if [ -f "$DIR/test_fetcher.py" ]; then
  count=$(grep -c 'def test_' "$DIR/test_fetcher.py" || echo 0)
  [ "$count" -ge 5 ] && score=$((score + 1))
fi

echo "$score/$max"
