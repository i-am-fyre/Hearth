#!/bin/bash
set -e

if [ -d /run/systemd/system ]; then
    systemctl stop hearth
    systemctl disable hearth
fi

echo "Hearth pre-remove complete."
