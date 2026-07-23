#!/usr/bin/env bash
set -euo pipefail

# Arcris First Boot Theme Application
# Applies KDE Plasma macOS-style theme, Kvantum, Latte Dock, SDDM, fonts

echo "[arcris] Applying Arcris macOS-inspired theme..."

USER_HOME="${HOME:-/root}"
USER_NAME="${SUDO_USER:-$USER}"

if [ "$USER_NAME" = "root" ]; then
    USER_HOME="/root"
else
    USER_HOME="/home/$USER_NAME"
fi

# Apply Kvantum theme
KVANTUM_DIR="$USER_HOME/.config/Kvantum"
mkdir -p "$KVANTUM_DIR"
if [ -f /etc/xdg/kvantum/kvantum.kvconfig ]; then
    cp /etc/xdg/kvantum/kvantum.kvconfig "$KVANTUM_DIR/"
fi
if [ -d /etc/xdg/kvantum/ArcrisKvantum ]; then
    cp -r /etc/xdg/kvantum/ArcrisKvantum "$KVANTUM_DIR/"
fi

# Apply Plasma look-and-feel
if [ -d /usr/share/plasma/look-and-feel/org.arcris.macglass ]; then
    lookandfeeltool -a org.arcris.macglass 2>/dev/null || true
fi

# Apply Papirus icon theme
lookandfeeltool -a org.arcris.macglass 2>/dev/null || true
plasma-apply-icon-theme Papirus 2>/dev/null || true

# Apply color scheme
plasma-apply-colorscheme ArcrisDark 2>/dev/null || true

# Start Latte Dock if installed
if command -v latte-dock &>/dev/null; then
    latte-dock --replace &>/dev/null &
    disown
    echo "[arcris] Latte Dock started"
fi

# Enable SDDM theme
SDDM_CONF="/etc/sddm.conf.d/arcris-theme.conf"
if [ -f "$SDDM_CONF" ]; then
    echo "[arcris] SDDM theme configured at $SDDM_CONF"
fi

echo "[arcris] Theme applied. Please log out and back in for full effect."
