#!/usr/bin/env bash
# Score task 6: MCP tool usage
# Checks: file exists, valid JSON, version looks real, source is a URL
DIR="$1"
score=0; max=4

if [ -f "$DIR/answer.json" ]; then
  score=$((score + 1))  # file exists
  if python3 -c "import json; json.load(open('$DIR/answer.json'))" 2>/dev/null; then
    score=$((score + 1))  # valid JSON
  fi
  if python3 -c "import json; d=json.load(open('$DIR/answer.json')); assert d.get('version','').count('.') >= 1" 2>/dev/null; then
    score=$((score + 1))  # version looks like semver
  fi
  if python3 -c "import json; d=json.load(open('$DIR/answer.json')); assert d.get('source','').startswith('http')" 2>/dev/null; then
    score=$((score + 1))  # source is a URL
  fi
fi

echo "$score/$max"
