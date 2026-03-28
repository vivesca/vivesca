#!/bin/bash
set -euo pipefail
DISK=$(df / --output=pcent | tail -1 | tr -d " %")
MEM=$(free -m | awk "/Mem:/{printf \"%d/%dMB\", \$3, \$2}")
FAILED=$(systemctl --user --failed --no-legend 2>/dev/null | wc -l)
if [ "$DISK" -gt 85 ] || [ "$FAILED" -gt 0 ]; then
    ~/scripts/tg-notify.sh "pharos health: disk=${DISK}% mem=${MEM} failed_units=${FAILED}"
fi
