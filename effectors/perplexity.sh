#!/usr/bin/env bash
# Perplexity API CLI — lightweight replacement for MCP server
# Usage: perplexity.sh <mode> "query"
#   Modes: search | ask | research | reason
#   Models: sonar (search), sonar-pro (ask), sonar-deep-research (research), sonar-reasoning-pro (reason)
#
# Cost per query (approx):
#   search:   ~$0.006  (sonar, low depth)
#   ask:      ~$0.010  (sonar-pro)
#   research: ~$0.400  (sonar-deep-research) ← EXPENSIVE
#   reason:   ~$0.010  (sonar-reasoning-pro)

set -euo pipefail

# Handle --help / -h before requiring API key
usage() {
  sed -n '2,11p' "$0"
  exit 0
}

MODE="${1:-}"
case "$MODE" in
  -h|--help) usage ;;
  "")        echo "Usage: perplexity.sh <search|ask|research|reason> \"query\"" >&2; exit 1 ;;
esac
QUERY="${2:?Missing query}"

case "$MODE" in
  search)   MODEL="sonar" ;;
  ask)      MODEL="sonar-pro" ;;
  research) MODEL="sonar-deep-research" ;;
  reason)   MODEL="sonar-reasoning-pro" ;;
  *)        echo "Unknown mode: $MODE (use search|ask|research|reason)" >&2; exit 1 ;;
esac

# Load API key (deferred so --help works without it)
source ~/.secrets 2>/dev/null || true
: "${PERPLEXITY_API_KEY:?Set PERPLEXITY_API_KEY in ~/.secrets}"

# Escape query for JSON
QUERY_JSON=$(python3 -c "import json,sys; print(json.dumps(sys.argv[1]))" "$QUERY")

RESPONSE=$(curl -sS https://api.perplexity.ai/chat/completions \
  -H "Authorization: Bearer $PERPLEXITY_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"$MODEL\",
    \"messages\": [{\"role\": \"user\", \"content\": $QUERY_JSON}]
  }")

# Extract content, fall back to raw response on error
CONTENT=$(python3 -c "
import json, sys
try:
    d = json.loads(sys.argv[1])
    if 'choices' in d:
        print(d['choices'][0]['message']['content'])
    elif 'error' in d:
        print(f\"ERROR: {d['error'].get('message', d['error'])}\", file=sys.stderr)
        sys.exit(1)
    else:
        print(json.dumps(d, indent=2))
except Exception as e:
    print(f'Parse error: {e}', file=sys.stderr)
    print(sys.argv[1])
" "$RESPONSE")

echo "$CONTENT"
