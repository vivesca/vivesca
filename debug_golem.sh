#!/bin/bash
source ~/.zshenv.local

# Test what env vars go into the command
_KEY="$ZHIPU_API_KEY"
_URL="https://open.bigmodel.cn/api/anthropic"
_OPUS="GLM-5.1"; _SONNET="GLM-5.1"; _HAIKU="GLM-4.5-air"
_api_key="$_KEY"
_auth_token=""

echo "Testing with empty auth token..."
echo "ANTHROPIC_AUTH_TOKEN is set: $(set | grep -q ANTHROPIC_AUTH_TOKEN && echo yes || echo no)"
echo "ANTHROPIC_AUTH_TOKEN value: '${ANTHROPIC_AUTH_TOKEN:-unset}'"

# Let's test with my fix manually
env_args=()
env_args+=(CLAUDECODE=)
env_args+=(ANTHROPIC_API_KEY="$_api_key")
[[ -n "$_auth_token" ]] && env_args+=(ANTHROPIC_AUTH_TOKEN="$_auth_token")
env_args+=(ANTHROPIC_BASE_URL="$_URL")
env_args+=(ANTHROPIC_DEFAULT_OPUS_MODEL="$_OPUS")
env_args+=(ANTHROPIC_DEFAULT_SONNET_MODEL="$_SONNET")
env_args+=(ANTHROPIC_DEFAULT_HAIKU_MODEL="$_HAIKU")
env_args+=(API_TIMEOUT_MS=3000000)
env_args+=(CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1)

echo
echo "Env vars being passed:"
for arg in "${env_args[@]}"; do
  echo "  $arg"
done

echo
echo "ANTHROPIC_AUTH_TOKEN will NOT be set because it's empty. Running command..."
echo "="

timeout 30 env "${env_args[@]}" claude --print --dangerously-skip-permissions --max-turns 1 --bare -p "What is 2 + 2? Answer with just the number." 2>&1
