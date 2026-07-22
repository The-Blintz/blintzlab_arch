#!/usr/bin/env bash
set -euo pipefail

# Lanzador de Blintzlab Installer
# Extrae el repositorio comprimido y ejecuta el instalador con acceso a la terminal.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Suponemos que el repositorio comprimido se encuentra en el mismo directorio
ARCHIVE="${SCRIPT_DIR}/blintzlab-repo.tar.gz"
if [[ ! -f "$ARCHIVE" ]]; then
    echo "Error: No se encontró el archivo comprimido $ARCHIVE" >&2
    exit 1
fi

# Extraer en un directorio temporal
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

tar -xzf "$ARCHIVE" -C "$TMPDIR"

# Ejecutar el instalador con entrada desde la terminal
cd "$TMPDIR"
exec ./blintzlab-install </dev/tty
