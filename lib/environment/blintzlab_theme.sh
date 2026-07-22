#!/usr/bin/env bash
set -euo pipefail

# Asegurar ejecución con Bash
if [ -z "${BASH_VERSION:-}" ]; then
    exec bash "$0" "$@"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
source "$SCRIPT_DIR/../common.sh"

PREMIUM_PACKAGES=(
    hyprland
    waybar
    rofi-wayland
    kitty
    swaybg
    python-pywal
    ttf-nerd-fonts-symbols
    ttf-nerd-fonts-fira-code
)

install_blintzlab_premium_packages() {
    info "Instalando paquetes premium..."
    local pkg
    for pkg in "${PREMIUM_PACKAGES[@]}"; do
        run_cmd "pacman -S --noconfirm $pkg"
    done
    success "Paquetes premium instalados."
}

deploy_blintzlab_dotfiles() {
    info "Desplegando dotfiles de Blintzlab..."
    local user_home
    if [[ -z "${NEW_USER:-}" ]]; then
        warn "NEW_USER no definido. Usando /root como fallback."
        user_home="/root"
    else
        user_home="/home/$NEW_USER"
    fi

    local dotfiles_src="$SCRIPT_DIR/../../dotfiles/hypr"
    if [[ ! -d "$dotfiles_src" ]]; then
        error "No se encontraron dotfiles en $dotfiles_src"
        return 1
    fi

    mkdir -p "$user_home/.config/hypr"
    mkdir -p "$user_home/.config/waybar"
    mkdir -p "$user_home/.config/rofi"
    mkdir -p "$user_home/.config/kitty"

    run_cmd "cp -r $dotfiles_src/hypr/* $user_home/.config/hypr/"
    run_cmd "cp -r $dotfiles_src/waybar/* $user_home/.config/waybar/"
    run_cmd "cp -r $dotfiles_src/rofi/* $user_home/.config/rofi/"
    run_cmd "cp -r $dotfiles_src/kitty/* $user_home/.config/kitty/"

    if [[ -n "${NEW_USER:-}" ]]; then
        run_cmd "chown -R $NEW_USER:$NEW_USER $user_home/.config"
    fi

    success "Dotfiles desplegados."
}
