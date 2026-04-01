#!/bin/bash
FAILURES=()
for f in effectors/*; do
  # Skip directories, archives, .pyc, .conf, and .sh that are meant to be sourced?
  if [ -d "$f" ] || [[ "$f" == *.pyc ]] || [[ "$f" == *.conf ]] || [[ "$f" == effectors/.archive/* ]] || [[ "$f" == effectors/__pycache__/* ]]; then
    continue
  fi
  # Check if it's executable
  if [ -x "$f" ]; then
    echo "Testing $f --help..."
    timeout 5 ./"$f" --help >/dev/null 2>&1
    exit_code=$?
    if [ $exit_code -ne 0 ] && [ $exit_code -ne 124 ]; then
      echo "✗ $f failed with exit code $exit_code"
      FAILURES+=("$f")
    else
      echo "✓ $f passed"
    fi
  fi
done
echo -e "\n=== Failed effectors ==="
for f in "${FAILURES[@]}"; do
  echo "$f"
done
exit ${#FAILURES[@]}
