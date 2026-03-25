# Password Reset Flow via CLI (browser + gog + 1Password)

Reusable chain for resetting forgotten passwords without leaving the terminal.

## Flow

1. Navigate to login page: `agent-browser --cdp 9222 eval "window.location.href = '...'"`
2. Click "Forgot Password": `agent-browser --cdp 9222 click @ref`
3. Fill email: `agent-browser --cdp 9222 fill @ref "email"`
4. Check Gmail for reset link: `gog gmail search "password reset from:noreply" --max 3`
5. Read the email: `gog gmail read <message-id>`
6. Open reset link in browser: `agent-browser --cdp 9222 eval "window.location.href = '...'"`
7. Set new password, submit
8. Update 1Password:
   ```bash
   export OP_BIOMETRIC_UNLOCK_ENABLED=0
   export OP_MASTER_PASSWORD=$(python3 -c "
   for line in open('/Users/terry/.secrets'):
       if line.startswith('OP_MASTER_PASSWORD='):
           print(line.strip().split('=',1)[1])
           break
   ")
   export OP_SESSION_personal=$(echo "$OP_MASTER_PASSWORD" | op signin --raw --account personal)
   op item edit "Site Name" password="newpassword"
   ```

## Prerequisites

- Chrome CDP running on port 9222
- `gog` CLI installed (`/opt/homebrew/bin/gog`)
- 1Password CLI with `OP_MASTER_PASSWORD` and `OP_SECRET_KEY` in `~/.secrets`
- `OP_BIOMETRIC_UNLOCK_ENABLED=0` (Touch ID doesn't work over SSH/Jump Desktop)
