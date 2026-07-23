"""
Post-install configuration engine — applies the visual theme (Hyperland-inspired
macOS style with blur, rounded corners, global menu, Plank/Latte dock),
SDDM theming, Kvantum engine, and system-level polish after base install.

Runs inside the chrooted target after all packages are installed.
"""

import shutil
from pathlib import Path


class PostInstallConfigurator:
    def __init__(self, target: Path, username: str = ""):
        self.target = target
        self.username = username
        self.home = target / "home" / username if username else target / "root"

    def run_all(self) -> None:
        self.install_theme_packages()
        self.configure_sddm()
        self.configure_kvantum()
        self.configure_latte_dock()
        self.configure_plasma_theme()
        self.configure_global_menu()
        self.configure_fonts_and_icons()
        self.configure_shortcuts()
        self.write_first_boot_service()
        self.enable_services()

    def install_theme_packages(self) -> None:
        packages = [
            "sddm",
            "kvantum",
            "kvantum-theme-materia",
            "papirus-icon-theme",
            "latte-dock",
            "plasma5-applets-window-buttons",
            "plasma5-applets-window-title",
            "plasma5-applets-window-appmenu",
            "lightly-qt",
            "noto-fonts",
            "noto-fonts-cjk",
            "noto-fonts-emoji",
            "ttf-fira-code",
            "ttf-fira-sans",
            "inter-font",
        ]
        script = self._command_script(packages, "pacman -S --noconfirm --needed")
        self._run_script(script)

    def enable_services(self) -> None:
        services = [
            "sddm.service",
            "NetworkManager.service",
            "bluetooth.service",
            "pipewire.service",
            "pipewire-pulse.service",
            "wireplumber.service",
            "fstrim.timer",
        ]
        for svc in services:
            script = f"#!/usr/bin/env bash\nset -euo pipefail\nsystemctl enable {svc}"
            self._run_script(script)

    def configure_sddm(self) -> None:
        sddm_conf_dir = self.target / "etc/sddm.conf.d"
        sddm_conf_dir.mkdir(parents=True, exist_ok=True)

        conf = sddm_conf_dir / "arcris-theme.conf"
        conf.write_text(
            "[Theme]\n"
            "Current=sddm-theme-arcris\n"
            "CursorTheme=Breeze_Snow\n"
            "Font=Inter,10,-1,5,50,0,0,0,0,0\n"
            "\n"
            "[Users]\n"
            "RememberLastUser=true\n"
            "ReuseSession=true\n"
            "\n"
            "[General]\n"
            "HaltCommand=/usr/bin/systemctl poweroff\n"
            "RebootCommand=/usr/bin/systemctl reboot\n"
        )

        theme_dir = self.target / "usr/share/sddm/themes/sddm-theme-arcris"
        theme_dir.mkdir(parents=True, exist_ok=True)

        metadata = theme_dir / "metadata.desktop"
        metadata.write_text(
            "[SddmGreeterTheme]\n"
            "Name=Arcris\n"
            "Description=Arcris macOS-inspired SDDM theme\n"
            "Author=Arcris Project\n"
            "Version=1.0\n"
            "Type=sddm-theme\n"
        )

        main_qml = theme_dir / "Main.qml"
        main_qml.write_text(self._sddm_qml_content())

    def _sddm_qml_content(self) -> str:
        return """import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Window 2.15
import SddmComponents 2.0

Rectangle {
    id: root
    width: Screen.width
    height: Screen.height
    color: "#1a1a2e"

    property alias loginColor: "#ffffff"
    property string background: "/usr/share/sddm/themes/sddm-theme-arcris/background.jpg"

    Image {
        id: bg
        anchors.fill: parent
        source: root.background
        fillMode: Image.PreserveAspectCrop
        opacity: 0.6
    }

    Rectangle {
        id: loginPanel
        width: 400
        height: 360
        anchors.centerIn: parent
        color: Qt.rgba(0.1, 0.1, 0.15, 0.85)
        radius: 18
        border.color: Qt.rgba(0.4, 0.4, 0.6, 0.35)

        Rectangle {
            id: header
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            height: 46
            color: Qt.rgba(0.08, 0.08, 0.12, 0.9)
            radius: 18

            Rectangle {
                anchors.bottom: header.bottom
                anchors.left: header.left
                anchors.right: header.right
                height: 18
                color: header.color
            }

            Label {
                anchors.centerIn: parent
                text: "Arcris"
                font.pixelSize: 20
                font.weight: Font.Bold
                color: "#e0e0ff"
            }
        }

        Column {
            id: form
            anchors.top: header.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.margins: 28
            spacing: 18

            Label {
                anchors.horizontalCenter: parent.horizontalCenter
                text: textConstants.welcomeText.arg(sddm.hostName)
                font.pixelSize: 12
                color: "#8080a0"
            }

            ComboBox {
                id: session
                anchors.left: parent.left
                anchors.right: parent.right
                model: sessionModel
                currentIndex: sessionModel.lastIndex
                font.pixelSize: 14
                Accessible.name: textConstants.session
            }

            TextBox {
                id: username
                anchors.left: parent.left
                anchors.right: parent.right
                text: userModel.lastUser
                font.pixelSize: 15
                placeholderText: textConstants.userName
                color: "#e0e0ff"
                borderColor: Qt.rgba(0.5, 0.5, 0.8, 0.4)
                focusColor: "#6060ff"
                hoverColor: Qt.rgba(0.4, 0.4, 0.7, 0.3)
                textColor: "#ffffff"
            }

            PasswordBox {
                id: password
                anchors.left: parent.left
                anchors.right: parent.right
                font.pixelSize: 15
                placeholderText: textConstants.password
                color: "#e0e0ff"
                borderColor: Qt.rgba(0.5, 0.5, 0.8, 0.4)
                focusColor: "#6060ff"
                hoverColor: Qt.rgba(0.4, 0.4, 0.7, 0.3)
                textColor: "#ffffff"
                ToolTip.visible: false
                Keys.onReturnPressed: loginButton.clicked()
            }

            Button {
                id: loginButton
                anchors.left: parent.left
                anchors.right: parent.right
                height: 42
                text: textConstants.login
                font.pixelSize: 16
                font.weight: Font.Bold

                onClicked: sddm.login(username.text, password.text, session.currentIndex)
                Keys.onReturnPressed: sddm.login(username.text, password.text, session.currentIndex)

                background: Rectangle {
                    color: parent.down ? "#4040cc" : (parent.hovered ? "#5050ee" : "#3a3aee")
                    radius: 12
                }
            }

            Button {
                id: shutdownButton
                anchors.left: parent.left
                anchors.right: parent.right
                height: 32
                text: textConstants.shutdown
                font.pixelSize: 13

                onClicked: sddm.powerOff()

                background: Rectangle {
                    color: parent.down ? "#444444" : (parent.hovered ? "#555555" : "transparent")
                    radius: 8
                    border.color: Qt.rgba(0.6, 0.6, 0.6, 0.25)
                }
            }
        }
    }
}
"""

    def configure_kvantum(self) -> None:
        kv_config_dir = self.target / "etc/xdg/kvantum"
        kv_config_dir.mkdir(parents=True, exist_ok=True)

        config_file = kv_config_dir / "kvantum.kvconfig"
        theme_dir = kv_config_dir / "ArcrisKvantum"
        theme_dir.mkdir(parents=True, exist_ok=True)

        config_file.write_text("[General]\ntheme=ArcrisKvantum\n")

        svg_content = self._kvantum_theme_svg()
        theme_svg = theme_dir / "ArcrisKvantum.svg"
        theme_svg.write_text(svg_content)

        theme_kvconfig = theme_dir / "ArcrisKvantum.kvconfig"
        theme_kvconfig.write_text(self._kvantum_config())

    def _kvantum_config(self) -> str:
        return """[General]
author=Arcris
comment=macOS inspired glass/blur theme
opaque=Arcvariant
[%General]
radius_frames=8
radius_menus=8
radius_tooltips=4
radius_popups=10
radius_docks=12
radius_progressbars=4
radius_sliders=4

# Blur & Transparency
bg_blur_enabled=true
bg_blur_radius=12
bg_blur_noise=0.02
bg_opacity_translucent=0.78
bg_opacity_overlay=0.45

# Colors
base_color=#1a1a2e
highlight_color=#5050cc
window_color=#16213e
button_color=#1f3460
tooltip_base_color=#0f3460

# Shadows
shadow_enabled=true
shadow_thickness=20
shadow_opacity=55

# Frame
frame_border=0.6
menu_shadow=true

# Scrollbar
scrollbar_width=8

# Progress
progressbar_thickness=6

# Animation
animate_states=true
"""

    def _kvantum_theme_svg(self) -> str:
        return """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="0" height="0">
  <defs>
    <linearGradient id="windowGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#1e2244"/>
      <stop offset="100%" stop-color="#161b33"/>
    </linearGradient>
    <linearGradient id="highlightGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#5050cc"/>
      <stop offset="100%" stop-color="#3838aa"/>
    </linearGradient>
  </defs>
</svg>
"""

    def configure_latte_dock(self) -> None:
        latte_conf_dir = self.target / "usr/share/latte/arcris-layout"
        latte_conf_dir.mkdir(parents=True, exist_ok=True)

        layout = latte_conf_dir / "dock.layout.latte"

        layout.write_text(
            "[Layout]\n"
            "name=Arcris Dock\n"
            "version=2\n"
            "\n"
            "[Dock]\n"
            "alignment=center\n"
            "visibility=windowsGoBelow\n"
            "background=translucent\n"
            "blur_background=true\n"
            "blur_radius=14\n"
            "background_opacity=0.58\n"
            "icon_size=44\n"
            "margin=8\n"
            "padding=12\n"
            "radius=16\n"
            "animation_parabolic_factor=0.2\n"
            "show_tooltips=true\n"
            "can_dock_applets=true\n"
        )

        autostart_dir = self.home / ".config/autostart"
        autostart_dir.mkdir(parents=True, exist_ok=True)

        desktop_entry = autostart_dir / "latte-dock.desktop"
        desktop_entry.write_text(
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Latte Dock\n"
            "Exec=latte-dock\n"
            "X-GNOME-Autostart-enabled=true\n"
            "X-KDE-autostart-after=panel\n"
        )

    def configure_plasma_theme(self) -> None:
        theme_dir = self.target / "usr/share/plasma/look-and-feel/org.arcris.macglass"
        theme_dir.mkdir(parents=True, exist_ok=True)

        metadata = theme_dir / "metadata.desktop"
        metadata.write_text(
            "[Desktop Entry]\n"
            "Name=Arcris MacGlass\n"
            "Comment=Elevated macOS-style with glass blur\n"
            "\n"
            "[Splash]\n"
            "Theme=org.arcris.macglass\n"
            "Engine=splash\n"
        )

        defaults = theme_dir / "defaults"
        defaults.write_text(
            "[Desktop]\n"
            "ColorScheme=ArcrisDark\n"
            "widgetStyle=kvantum\n"
            "\n"
            "[Icons]\n"
            "Theme=Papirus\n"
            "\n"
            "[Wallpaper]\n"
            "Image=/usr/share/wallpapers/arcris/default.jpg\n"
            "\n"
            "[Plasma]\n"
            "ToolBoxButton=true\n"
            "ToolBoxButtonX=0\n"
            "ToolBoxButtonY=0\n"
        )

    def configure_global_menu(self) -> None:
        plasma_layout_dir = self.home / ".config/plasma-org.kde.plasma.desktop-appletsrc"
        plasma_layout_dir.parent.mkdir(parents=True, exist_ok=True)

        plasma_layout_dir.write_text(
            "[PlasmaPanels][1]\n"
            "location=1\n"
            "plugin=org.kde.plasma.desktop\n"
            "\n"
            "[Containments][1]\n"
            "formfactor=2\n"
            "location=1\n"
            "plugin=org.kde.plasma.desktopcontainment\n"
            "\n"
            "[Containments][1][Applets][2]\n"
            "plugin=org.kde.plasma.windowtitle\n"
            "\n"
            "[Containments][1][Applets][3]\n"
            "plugin=org.kde.plasma.windowappmenu\n"
            "\n"
            "[Containments][1][Applets][4]\n"
            "plugin=org.kde.plasma.windowbuttons\n"
            "\n"
            "[Containments][1][General]\n"
            "showToolbox=true\n"
        )

    def configure_fonts_and_icons(self) -> None:
        fonts_dir = self.home / ".config/fontconfig"
        fonts_dir.mkdir(parents=True, exist_ok=True)

        fonts_conf = fonts_dir / "fonts.conf"
        fonts_conf.write_text(
            '<?xml version="1.0"?>\n'
            '<!DOCTYPE fontconfig SYSTEM "fonts.dtd">\n'
            "<fontconfig>\n"
            "  <alias>\n"
            "    <family>sans-serif</family>\n"
            "    <prefer><family>Inter</family></prefer>\n"
            "  </alias>\n"
            "  <alias>\n"
            "    <family>monospace</family>\n"
            "    <prefer><family>Fira Code</family></prefer>\n"
            "  </alias>\n"
            "</fontconfig>\n"
        )

        icons_conf_dir = self.home / ".config"
        icons_conf_dir.mkdir(parents=True, exist_ok=True)
        kde_globals = icons_conf_dir / "kdeglobals"
        kde_globals.write_text(
            "[Icons]\nTheme=Papirus\n"
        )

    def configure_shortcuts(self) -> None:
        shortcut_dir = self.home / ".config"
        shortcut_dir.mkdir(parents=True, exist_ok=True)

        kglobalshortcutsrc = shortcut_dir / "kglobalshortcutsrc"
        kglobalshortcutsrc.write_text(
            "[kwin]\n"
            "Window Maximize=Meta+Up,none,Maximize Window\n"
            "Window Minimize=Meta+Down,none,Minimize Window\n"
            "Window Tile Left=Meta+Left,none,Quick Tile Window to the Left\n"
            "Window Tile Right=Meta+Right,none,Quick Tile Window to the Right\n"
            "Window Close=Meta+Q,none,Close Window\n"
            "\n"
            "[plasmashell]\n"
            "activate widget 28=Meta+Space,none,Activate Application Launcher\n"
        )

    def write_first_boot_service(self) -> None:
        service_dir = self.target / "etc/systemd/system"
        service_dir.mkdir(parents=True, exist_ok=True)

        service_path = service_dir / "arcris-firstboot.service"
        service_path.write_text(
            "[Unit]\n"
            "Description=Arcris First Boot Theme Setup\n"
            "After=network.target graphical-session.target\n"
            "Wants=graphical-session.target\n"
            "\n"
            "[Service]\n"
            "Type=oneshot\n"
            "ExecStart=/opt/arcris/scripts/arcris-firstboot.sh\n"
            "User=%s\n"
            "Environment=DISPLAY=:0\n"
            "RemainAfterExit=yes\n"
            "\n"
            "[Install]\n"
            "WantedBy=graphical-session.target\n"
            % (self.username or "root")
        )

        target_wants = self.target / "etc/systemd/system/graphical-session.target.wants"
        target_wants.mkdir(parents=True, exist_ok=True)
        link = target_wants / "arcris-firstboot.service"
        link.unlink(missing_ok=True)
        link.symlink_to(str(service_path))

    def _command_script(self, packages: list[str], base_cmd: str) -> str:
        pkgs = " ".join(packages)
        return f"#!/usr/bin/env bash\nset -euo pipefail\n{base_cmd} {pkgs}"

    def _run_script(self, content: str) -> None:
        script_path = self.target / "tmp/_arcris_post_install.sh"
        script_path.parent.mkdir(parents=True, exist_ok=True)
        script_path.write_text(content)
        script_path.chmod(0o755)


def configure_post_install(target: Path, username: str = "") -> None:
    configurator = PostInstallConfigurator(target, username)
    configurator.run_all()
