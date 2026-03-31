#!/bin/bash
set -euo pipefail

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    echo "Usage: pharos-health.sh"
    echo ""
    echo "Check system health (disk, memory, failed systemd units)."
    echo "Sends a Telegram alert via tg-notify.sh if disk > 85% or any"
    echo "user-level systemd units have failed."
    echo ""
    echo "Exit 0 = healthy, exit 1 = alert sent (unhealthy)."
    exit 0
fi

DISK=$(df / --output=pcent | tail -1 | tr -d " %")
MEM=$(free -m | awk "/Mem:/{printf \"%d/%dMB\", \$3, \$2}")
FAILED=$(systemctl --user --failed --no-legend 2>/dev/null | wc -l) || FAILED=0

ALERT=false
if [ "$DISK" -gt 85 ]; then
    ALERT=true
fi
if [ "$FAILED" -gt 0 ]; then
    ALERT=true
fi

if $ALERT; then
    ~/scripts/tg-notify.sh "pharos health: disk=${DISK}% mem=${MEM} failed_units=${FAILED}"
    exit 1
fi

echo "pharos health: ok disk=${DISK}% mem=${MEM} failed_units=${FAILED}"
exit 0
