#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../common.sh"

select_environment() {
    local choice
    if command -v whiptail &>/dev/null; then
        choice=$(whiptail --title "Blintzlab - Selección de Entorno" \
            --menu "Elige tu entorno de escritorio o gestor de ventanas:" 20 60 4 \
            "1" "KDE Plasma (Estándar)" \
            "2" "Hyprland Vanilla (Base)" \
            "3" "Blintzlab Premium (Hyprland)" \
            "4" "Omitir / Solo Consola" \
            3>&1 1>&2 2>&3)
    elif command -v dialog &>/dev/null; then
        choice=$(dialog --title "Blintzlab - Selección de Entorno" \
            --menu "Elige tu entorno de escritorio o gestor de ventanas:" 20 60 4 \
            "1" "KDE Plasma (Estándar)" \
            "2" "Hyprland Vanilla (Base)" \
            "3" "Blintzlab Premium (Hyprland)" \
            "4" "Omitir / Solo Consola" \
            3>&1 1>&2 2>&3)
    else
        echo "Selecciona una opción:"
        echo "1) KDE Plasma"
        echo "2) Hyprland Vanilla"
        echo "3) Blintzlab Premium (Hyprland)"
        echo "4) Omitir / Solo Consola"
        read -r choice </dev/tty
    fi

    case "$choice" in
        1)
            info "Instalando KDE Plasma..."
            install_kde_plasma
            ;;
        2)
            info "Instalando Hyprland Vanilla..."
            install_hyprland_vanilla
            ;;
        3)
            info "Instalando Blintzlab Premium..."
            install_blintzlab_premium
            ;;
        4)
            info "Omitiendo instalación de entorno gráfico."
            ;;
        *)
            warn "Opción inválida. Se omite instalación."
            ;;
    esac
}

install_kde_plasma() {
    run_cmd "pacman -S --noconfirm plasma-meta kde-applications-meta"
    success "KDE Plasma instalado."
}

install_hyprland_vanilla() {
    run_cmd "pacman -S --noconfirm hyprland waybar rofi-wayland kitty swaybg"
    success "Hyprland Vanilla instalado."
}

install_blintzlab_premium() {
    source "$SCRIPT_DIR/blintzlab_theme.sh"
    install_blintzlab_premium_packages
    deploy_blintzlab_dotfiles
    success "Blintzlab Premium instalado."
}
