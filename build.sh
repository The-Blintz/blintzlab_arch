#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
ISO_OUTPUT="$ROOT_DIR/out/arcris.iso"
WORK_DIR="$ROOT_DIR/.work"

echo "=== Arcris ISO Builder ==="
echo "Root dir: $ROOT_DIR"

mkdir -p "$ROOT_DIR/out" "$WORK_DIR"

echo "[1/4] Copying project files to work directory..."
rsync -av --exclude='.work' --exclude='out' --exclude='.git' "$ROOT_DIR/" "$WORK_DIR/arcris/"

echo "[2/4] Preparing ISO skeleton..."
mkdir -p "$WORK_DIR/iso/airootfs/opt/arcris"

cp -r "$WORK_DIR/arcris/src" "$WORK_DIR/iso/airootfs/opt/arcris/"
cp -r "$WORK_DIR/arcris/gui" "$WORK_DIR/iso/airootfs/opt/arcris/"
cp -r "$WORK_DIR/arcris/configs" "$WORK_DIR/iso/airootfs/opt/arcris/"
cp -r "$WORK_DIR/arcris/scripts" "$WORK_DIR/iso/airootfs/opt/arcris/"
cp -r "$WORK_DIR/arcris/profiles" "$WORK_DIR/iso/airootfs/opt/arcris/"
cp -r "$WORK_DIR/arcris/assets" "$WORK_DIR/iso/airootfs/opt/arcris/"

cp "$WORK_DIR/arcris/src/main.py" "$WORK_DIR/iso/airootfs/opt/arcris/"

cat > "$WORK_DIR/iso/airootfs/opt/arcris/run.sh" << 'RUNSH'
#!/usr/bin/env bash
cd /opt/arcris
python3 /opt/arcris/main.py "$@"
RUNSH
chmod +x "$WORK_DIR/iso/airootfs/opt/arcris/run.sh"

echo "[3/4] Installing dependencies into airootfs..."
mkdir -p "$WORK_DIR/iso/airootfs/root/.config"

cat > "$WORK_DIR/iso/packages.x86_64" << 'PKGS'
arch-install-scripts
python
python-pyside6
archinstall
btrfs-progs
dosfstools
lsblk
util-linux
zram-generator
PKGS

pacstrap -c "$WORK_DIR/iso/airootfs" $(cat "$WORK_DIR/iso/packages.x86_64")

echo "[4/4] Building ISO..."
mkarchiso -v -w "$WORK_DIR" -o "$ROOT_DIR/out" "$WORK_DIR/iso"

echo "Done: $ISO_OUTPUT"
