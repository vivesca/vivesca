#!/usr/bin/env bash
# Score task 7: Real codebase navigation
DIR="$1"
score=0; max=6

if [ -f "$DIR/analysis.json" ]; then
  score=$((score + 1))  # file exists
  if python3 -c "import json; json.load(open('$DIR/analysis.json'))" 2>/dev/null; then
    score=$((score + 1))  # valid JSON
  fi
  # Check specific facts from the ribosome script
  python3 -c "
import json
d = json.load(open('$DIR/analysis.json'))
h = d.get('harnesses', [])
if 'claude' in h and 'goose' in h and 'droid' in h: print('HARNESSES_OK')
b = d.get('backends', [])
if 'zhipu' in b: print('BACKENDS_OK')
if d.get('default_harness') == 'claude': print('DEFAULT_H_OK')
if 'bigmodel.cn' in d.get('zhipu_anthropic_url', '') or 'anthropic' in d.get('zhipu_anthropic_url', ''): print('URL_OK')
" 2>/dev/null | while read line; do
    case "$line" in
      HARNESSES_OK|BACKENDS_OK|DEFAULT_H_OK|URL_OK) score=$((score + 1)) ;;
    esac
    echo "$score" > /tmp/task7_score_$$
  done
  if [ -f /tmp/task7_score_$$ ]; then
    extra=$(cat /tmp/task7_score_$$)
    score=$((score + extra))
    rm -f /tmp/task7_score_$$
  fi
fi

echo "$score/$max"
