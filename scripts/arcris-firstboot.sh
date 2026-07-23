#!/usr/bin/env bash
set -euo pipefail

# Arcris First Boot Service Runner
# Called by systemd service arcris-firstboot.service

SCRIPT_DIR="/opt/arcris/scripts"

echo "[arcris] First boot setup starting..."

# Run post-install optimizations
if [ -f "$SCRIPT_DIR/post_optimize.sh" ]; then
    echo "[arcris] Running post-install optimizations..."
    bash "$SCRIPT_DIR/post_optimize.sh"
fi

# Apply theme
if [ -f "$SCRIPT_DIR/post_theme.sh" ]; then
    echo "[arcris] Applying theme..."
    bash "$SCRIPT_DIR/post_theme.sh"
fi

# Create swap if configured
if [ -f "$SCRIPT_DIR/create-swap.sh" ]; then
    echo "[arcris] Creating disk swap..."
    bash "$SCRIPT_DIR/create-swap.sh"
fi

# Disable first-boot service so it only runs once
systemctl disable arcris-firstboot.service 2>/dev/null || true

# Remove the service file after successful run
rm -f /etc/systemd/system/arcris-firstboot.service
rm -f /etc/systemd/system/graphical-session.target.wants/arcris-firstboot.service
systemctl daemon-reload 2>/dev/null || true

echo "[arcris] First boot setup complete."
