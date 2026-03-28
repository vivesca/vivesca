#!/bin/bash
# Start Chrome with remote debugging enabled
# This allows Playwright/OpenClaw to connect without extension clicks

CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
DEBUG_PORT=9222

# Check if Chrome is already running with debugging
if curl -s "http://localhost:$DEBUG_PORT/json/version" > /dev/null 2>&1; then
    echo "Chrome already running with debugging on port $DEBUG_PORT"
    exit 0
fi

# Start Chrome with remote debugging
"$CHROME" \
    --remote-debugging-port=$DEBUG_PORT \
    --user-data-dir="$HOME/Library/Application Support/Google/Chrome" \
    &

echo "Chrome started with remote debugging on port $DEBUG_PORT"
echo "Connect via: http://localhost:$DEBUG_PORT"
