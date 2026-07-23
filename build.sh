#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
ISO_OUTPUT="$ROOT_DIR/out/arcris.iso"
WORK_DIR="$ROOT_DIR/.work"

echo "=== Arcris ISO Builder ==="
echo "Root dir: $ROOT_DIR"

mkdir -p "$ROOT_DIR/out" "$WORK_DIR"

echo "[1/5] Copying project files to work directory..."
rsync -av --exclude='.work' --exclude='out' --exclude='.git' "$ROOT_DIR/" "$WORK_DIR/arcris/"

echo "[2/5] Preparing ISO skeleton..."
mkdir -p "$WORK_DIR/iso/airootfs/opt/arcris"

cp -r "$WORK_DIR/arcris/src" "$WORK_DIR/iso/airootfs/opt/arcris/"
cp -r "$WORK_DIR/arcris/gui" "$WORK_DIR/iso/airootfs/opt/arcris/"
cp -r "$WORK_DIR/arcris/configs" "$WORK_DIR/iso/airootfs/opt/arcris/"
cp -r "$WORK_DIR/arcris/scripts" "$WORK_DIR/iso/airootfs/opt/arcris/"
cp -r "$WORK_DIR/arcris/profiles" "$WORK_DIR/iso/airootfs/opt/arcris/"
cp -r "$WORK_DIR/arcris/assets" "$WORK_DIR/iso/airootfs/opt/arcris/"

cp "$WORK_DIR/arcris/main.py" "$WORK_DIR/iso/airootfs/opt/arcris/"

cat > "$WORK_DIR/iso/airootfs/opt/arcris/run.sh" << 'RUNSH'
#!/usr/bin/env bash
cd /opt/arcris
python3 /opt/arcris/main.py "$@"
RUNSH
chmod +x "$WORK_DIR/iso/airootfs/opt/arcris/run.sh"

echo "[3/5] Creating pacman.conf for ISO..."
mkdir -p "$WORK_DIR/iso/airootfs/etc"
cat > "$WORK_DIR/iso/pacman.conf" << 'PACMANCONF'
[options]
SigLevel = Optional TrustAll
Server = https://geo.mirror.pkgbuild.com/$repo/os/$arch

[core]
Include = /etc/pacman.d/mirrorlist

[extra]
Include = /etc/pacman.d/mirrorlist
PACMANCONF

echo "[4/5] Installing dependencies into airootfs..."
mkdir -p "$WORK_DIR/iso/airootfs/root/.config"

cat > "$WORK_DIR/iso/packages.x86_64" << 'PKGS'
# Core system
base
linux
linux-firmware
sudo
networkmanager
network-manager-applet
openssh
bash-completion
man-db
man-pages
vim
nano
git
base-devel

# Installer dependencies
arch-install-scripts
python
python-pyside6
archinstall

# Filesystem tools
btrfs-progs
dosfstools
e2fsprogs
xfsprogs
util-linux
parted

# Memory optimization
zram-generator

# Display server
xorg-server
xorg-xinit
xorg-xrandr
xorg-xset

# Audio
pipewire
pipewire-pulse
pipewire-alsa
wireplumber

# Bluetooth
bluez
bluez-utils

# Fonts
noto-fonts
noto-fonts-cjk
noto-fonts-emoji
ttf-fira-code
ttf-fira-sans
inter-font

# Network
iwd
wpa_supplicant
dhcpcd
PKGS

pacstrap -c "$WORK_DIR/iso/airootfs" $(cat "$WORK_DIR/iso/packages.x86_64")

echo "[5/5] Configuring ISO live environment..."

# Enable NetworkManager in live ISO
mkdir -p "$WORK_DIR/iso/airootfs/etc/systemd/system/multi-user.target.wants"
ln -sf /usr/lib/systemd/system/NetworkManager.service \
    "$WORK_DIR/iso/airootfs/etc/systemd/system/multi-user.target.wants/NetworkManager.service" 2>/dev/null || true

# Enable SSH for remote access during install
ln -sf /usr/lib/systemd/system/sshd.service \
    "$WORK_DIR/iso/airootfs/etc/systemd/system/multi-user.target.wants/sshd.service" 2>/dev/null || true

# Create auto-login for root on TTY1
mkdir -p "$WORK_DIR/iso/airootfs/etc/systemd/system/getty@tty1.service.d"
cat > "$WORK_DIR/iso/airootfs/etc/systemd/system/getty@tty1.service.d/autologin.conf" << 'AUTOLOGIN'
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin root --noclear %I $TERM
AUTOLOGIN

# Create .xinitrc to auto-start installer
cat > "$WORK_DIR/iso/airootfs/root/.xinitrc" << 'XINITRC'
#!/bin/bash
exec startplasma-x11
XINITRC
chmod +x "$WORK_DIR/iso/airootfs/root/.xinitrc"

# Create xprofile to launch installer on login
cat > "$WORK_DIR/iso/airootfs/root/.xprofile" << 'XPROFILE'
#!/bin/bash
if [ -z "$ARCRIS_STARTED" ]; then
    export ARCRIS_STARTED=1
    sleep 2
    python3 /opt/arcris/main.py &
fi
XPROFILE
chmod +x "$WORK_DIR/iso/airootfs/root/.xprofile"

echo "Building ISO with mkarchiso..."
mkarchiso -v -w "$WORK_DIR" -o "$ROOT_DIR/out" "$WORK_DIR/iso"

echo ""
echo "=== Build complete ==="
echo "ISO: $ISO_OUTPUT"
echo "Size: $(du -h "$ISO_OUTPUT" | cut -f1)"
