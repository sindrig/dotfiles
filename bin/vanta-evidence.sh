#!/usr/bin/env bash
set -euxo pipefail

echo "Screenlock enabled"
ps -ef | grep sway[l]ock

echo "Hard disk encrypted"
lsblk --fs

echo "Available updates"
checkupdates || echo "No updates available"
systemctl status --user checkupdates-notify.timer
