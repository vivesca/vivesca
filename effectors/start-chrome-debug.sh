#!/usr/bin/env bash
# Start Chrome with remote debugging enabled
# This allows Playwright/OpenClaw to connect without extension clicks

set -euo pipefail

DEBUG_PORT=9222

usage() {
    cat <<'EOF'
Usage: start-chrome-debug.sh [OPTIONS]

Start Chrome with remote debugging enabled.

Options:
  -h, --help     Show this help message
  -p, --port     Debugging port (default: 9222)

EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            usage
            exit 0
            ;;
        -p|--port)
            DEBUG_PORT="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

# Detect Chrome binary and user-data-dir based on platform
case "$(uname -s)" in
    Darwin)
        CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        USER_DATA_DIR="$HOME/Library/Application Support/Google/Chrome"
        ;;
    Linux)
        for candidate in google-chrome-stable google-chrome chromium-browser chromium; do
            if command -v "$candidate" &>/dev/null; then
                CHROME="$(command -v "$candidate")"
                break
            fi
        done
        USER_DATA_DIR="$HOME/.config/google-chrome"
        ;;
    *)
        echo "Unsupported platform: $(uname -s)" >&2
        exit 1
        ;;
esac

if [[ -z "${CHROME:-}" ]]; then
    echo "Error: Chrome/Chromium not found on PATH" >&2
    exit 1
fi

if [[ ! -x "$CHROME" ]]; then
    echo "Error: Chrome binary not executable: $CHROME" >&2
    exit 1
fi

# Check if Chrome is already running with debugging
if curl -s "http://localhost:$DEBUG_PORT/json/version" >/dev/null 2>&1; then
    echo "Chrome already running with debugging on port $DEBUG_PORT"
    exit 0
fi

# Start Chrome with remote debugging
"$CHROME" \
    --remote-debugging-port="$DEBUG_PORT" \
    --user-data-dir="$USER_DATA_DIR" \
    &

CHROME_PID=$!
sleep 1

# Verify the background process didn't immediately die
if ! kill -0 "$CHROME_PID" 2>/dev/null; then
    echo "Error: Chrome failed to start (pid $CHROME_PID exited immediately)" >&2
    exit 1
fi

echo "Chrome started with remote debugging on port $DEBUG_PORT (pid $CHROME_PID)"
echo "Connect via: http://localhost:$DEBUG_PORT"
