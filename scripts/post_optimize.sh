#!/usr/bin/env bash
set -euo pipefail

# Arcris Post-Install Optimization Script
# Applies sysctl tuning, enables zram, creates disk swap if configured

echo "[arcris] Applying kernel memory optimizations..."

SYSCTL_FILE="/etc/sysctl.d/99-arcris-memory-optimization.conf"
if [ -f "$SYSCTL_FILE" ]; then
    sysctl -p "$SYSCTL_FILE"
    echo "[arcris] Memory sysctl applied: $SYSCTL_FILE"
else
    echo "[arcris] WARNING: $SYSCTL_FILE not found"
fi

echo "[arcris] Enabling zram-generator..."
systemctl enable systemd-zram-setup@zram0.service 2>/dev/null || true
systemctl start systemd-zram-setup@zram0.service 2>/dev/null || true

echo "[arcris] Enabling periodic TRIM for SSDs..."
systemctl enable fstrim.timer 2>/dev/null || true
systemctl start fstrim.timer 2>/dev/null || true

# Create disk swap if the script exists
if [ -f /opt/arcris/scripts/create-swap.sh ]; then
    bash /opt/arcris/scripts/create-swap.sh
fi

echo "[arcris] Post-install optimization complete."
