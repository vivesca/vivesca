# No Public Gists Guardrail
# =========================
# Prevents accidental creation of public GitHub gists.
#
# Why: Gists are often used for quick code transfer between agent and user.
#      Public gists are indexed by search engines and expose content permanently.
#      Failed Jan 26 & 27 when agent used `-p` flag by mistake.
#
# Install: Add to ~/.zshrc or source this file
#
# Usage:
#   gist file.txt              → creates secret gist (allowed)
#   gist -p file.txt           → blocked
#   gh gist create file.txt    → creates secret gist (allowed)
#   gh gist create -p file.txt → blocked
#
# Override: Edit ~/.zshrc or call `command gh gist create -p` directly

# Block public gists entirely
gist() {
  if [[ "$*" == *"-p"* ]] || [[ "$*" == *"--public"* ]]; then
    echo "❌ Public gists disabled. Edit ~/.zshrc to override."
    return 1
  fi
  gh gist create "$@"
}

# Wrap gh to catch direct `gh gist create -p` calls
gh() {
  if [[ "$1" == "gist" && "$2" == "create" ]]; then
    shift 2
    gist "$@"
  else
    command gh "$@"
  fi
}
