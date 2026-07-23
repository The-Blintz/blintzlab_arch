#!/usr/bin/env bash
set -euo pipefail

# Arcris First Boot Service Runner
# Called by systemd service arcris-firstboot.service

SCRIPT_DIR="/opt/arcris/scripts"

if [ -f "$SCRIPT_DIR/post_optimize.sh" ]; then
    bash "$SCRIPT_DIR/post_optimize.sh"
fi

if [ -f "$SCRIPT_DIR/post_theme.sh" ]; then
    bash "$SCRIPT_DIR/post_theme.sh"
fi

# Disable first-boot service so it only runs once
systemctl disable arcris-firstboot.service 2>/dev/null || true

echo "[arcris] First boot setup complete."
