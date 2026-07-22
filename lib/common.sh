#!/usr/bin/env bash
set -euo pipefail

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funciones de mensaje
info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

success() {
    echo -e "${GREEN}[OK]${NC} $*"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

# Función para ejecutar comandos con log
run_cmd() {
    local cmd="$*"
    info "Ejecutando: $cmd"
    if ! eval "$cmd" >> /tmp/blintzlab-install.log 2>&1; then
        error "Falló el comando: $cmd"
        return 1
    fi
    success "Comando completado: $cmd"
}
