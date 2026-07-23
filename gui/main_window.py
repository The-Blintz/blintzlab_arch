"""
Arcris Installer GUI — PySide6 wizard with dark theme, real-time logs,
async installation via QThread, and full step-by-step configuration.
"""

import sys
import os
import subprocess
import threading
from pathlib import Path
from typing import cast

from PySide6.QtCore import (
    QThread,
    Signal,
    Qt,
    QSize,
    QTimer,
)
from PySide6.QtGui import (
    QFont,
    QPalette,
    QColor,
    QIcon,
    QPixmap,
    QTextCursor,
)
from PySide6.QtWidgets import (
    QApplication,
    QWizard,
    QWizardPage,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QLineEdit,
    QTextEdit,
    QCheckBox,
    QGroupBox,
    QFormLayout,
    QSpinBox,
    QRadioButton,
    QButtonGroup,
    QProgressBar,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QSpacerItem,
    QSizePolicy,
    QFrame,
    QSlider,
    QWidget,
)

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.installer import ArcrisInstaller
from src.swap_manager import detect_total_ram_mb, calculate_swap_config


DARK_STYLESHEET = """
QWidget {
    background-color: #1a1a2e;
    color: #e0e0ff;
    font-family: "Inter", "Segoe UI", "Noto Sans", sans-serif;
    font-size: 13px;
}
QWizard {
    background-color: #161b33;
}
QWizardPage {
    background-color: #161b33;
}
QLabel {
    color: #e0e0ff;
    background: transparent;
}
QLabel#heading {
    font-size: 22px;
    font-weight: bold;
    color: #ffffff;
    padding: 16px 0 8px 0;
}
QLabel#subheading {
    font-size: 13px;
    color: #8888bb;
    padding: 0 0 16px 0;
}
QLabel#status {
    font-size: 12px;
    color: #8888bb;
    padding: 4px 0;
}
QLineEdit, QSpinBox, QComboBox {
    background-color: #0f1935;
    border: 1px solid #2a2a5a;
    border-radius: 8px;
    padding: 8px 12px;
    color: #ffffff;
    font-size: 13px;
    selection-background-color: #5050cc;
}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1px solid #5050cc;
}
QLineEdit:disabled, QSpinBox:disabled, QComboBox:disabled {
    background-color: #12122a;
    color: #555588;
}
QComboBox::drop-down {
    border: none;
    width: 28px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #8888bb;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #0f1935;
    border: 1px solid #2a2a5a;
    border-radius: 6px;
    selection-background-color: #5050cc;
    color: #ffffff;
    outline: none;
}
QCheckBox {
    spacing: 10px;
    background: transparent;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #3a3a6a;
    border-radius: 4px;
    background-color: #0f1935;
}
QCheckBox::indicator:checked {
    background-color: #5050cc;
    border-color: #5050cc;
}
QRadioButton {
    spacing: 8px;
    background: transparent;
}
QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #3a3a6a;
    border-radius: 10px;
    background-color: #0f1935;
}
QRadioButton::indicator:checked {
    background-color: #5050cc;
    border-color: #5050cc;
}
QPushButton {
    background-color: #3a3aee;
    border: none;
    border-radius: 10px;
    padding: 10px 24px;
    color: #ffffff;
    font-size: 14px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #5050ee;
}
QPushButton:pressed {
    background-color: #2a2acc;
}
QPushButton:disabled {
    background-color: #2a2a5a;
    color: #555588;
}
QPushButton#secondary {
    background-color: transparent;
    border: 1px solid #3a3a6a;
    color: #8888bb;
}
QPushButton#secondary:hover {
    border-color: #5050cc;
    color: #e0e0ff;
}
QTextEdit, QPlainTextEdit {
    background-color: #0a0a1a;
    border: 1px solid #2a2a5a;
    border-radius: 8px;
    padding: 10px;
    color: #00e676;
    font-family: "Fira Code", "JetBrains Mono", monospace;
    font-size: 12px;
    selection-background-color: #5050cc;
}
QGroupBox {
    background-color: #12122e;
    border: 1px solid #2a2a5a;
    border-radius: 10px;
    margin-top: 14px;
    padding: 14px 10px 10px 10px;
    font-weight: bold;
    color: #c0c0ee;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 10px;
    color: #9090cc;
}
QProgressBar {
    background-color: #0a0a1a;
    border: none;
    border-radius: 8px;
    text-align: center;
    color: #ffffff;
    font-size: 12px;
    height: 16px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #3a3aee, stop:1 #6060ff);
    border-radius: 8px;
}
QSlider::groove:horizontal {
    background: #0f1935;
    border-radius: 4px;
    height: 8px;
}
QSlider::handle:horizontal {
    background: #5050cc;
    border-radius: 8px;
    width: 18px;
    height: 18px;
    margin: -5px 0;
}
QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #3a3aee, stop:1 #6060ff);
    border-radius: 4px;
}
QListWidget {
    background-color: #0f1935;
    border: 1px solid #2a2a5a;
    border-radius: 8px;
    padding: 4px;
    outline: none;
}
QListWidget::item {
    padding: 8px 12px;
    border-radius: 6px;
}
QListWidget::item:selected {
    background-color: #5050cc;
}
QListWidget::item:hover {
    background-color: #1a1a4a;
}
QFrame#separator {
    background-color: #2a2a5a;
    max-height: 1px;
    min-height: 1px;
}
QFrame#card {
    background-color: #12122e;
    border: 1px solid #2a2a5a;
    border-radius: 12px;
    padding: 16px;
}
QSpinBox {
    min-width: 80px;
}
"""


def heading(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("heading")
    return lbl


def subheading(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("subheading")
    return lbl


def separator() -> QFrame:
    f = QFrame()
    f.setObjectName("separator")
    f.setFrameShape(QFrame.Shape.HLine)
    return f


class RefreshThread(QThread):
    finished = Signal(object)

    def __init__(self, fn, *args):
        super().__init__()
        self.fn = fn
        self.args = args

    def run(self):
        result = self.fn(*self.args)
        self.finished.emit(result)


class InstallWorker(QThread):
    progress = Signal(int, int, str)
    log = Signal(str)
    finished = Signal(bool, str)
    error = Signal(str)

    def __init__(self, installer: ArcrisInstaller):
        super().__init__()
        self.installer = installer

    def run(self):
        try:
            def cb(step, total, label):
                self.progress.emit(step, total, label)
                self.log.emit(f"[{step}/{total}] {label}")

            self.log.emit("Starting installation...")
            success = self.installer.run_installation(progress_callback=cb)
            if success:
                self.finished.emit(True, "Installation completed successfully!")
            else:
                self.finished.emit(False, "Installation failed. Check logs.")
        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit(False, f"Error: {e}")


class WelcomePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("")
        self.setSubTitle("")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(12)

        layout.addStretch()

        title = QLabel("Arcris")
        title.setObjectName("heading")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 48px; font-weight: 300; color: #ffffff; letter-spacing: 8px;")
        layout.addWidget(title)

        subtitle = QLabel("Arch Linux — Elevated")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 18px; color: #8888bb; letter-spacing: 4px;")
        layout.addWidget(subtitle)

        layout.addSpacing(20)

        desc = QLabel(
            "A modern, graphical Arch Linux installer with:\n"
            "• Hybrid ZRAM + Disk Swap optimization\n"
            "• KDE Plasma with macOS-inspired theme\n"
            "• Automatic memory tuning for any system"
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("font-size: 13px; color: #6666aa; line-height: 1.6;")
        layout.addWidget(desc)

        layout.addStretch()

        hint = QLabel("Click Next to begin configuration")
        hint.setObjectName("status")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

        ram_mb = detect_total_ram_mb()
        swap = calculate_swap_config(ram_mb)
        info = QLabel(
            f"Detected RAM: {ram_mb} MB\n"
            f"Suggested ZRAM: {swap.zram_size_mb} MB | Disk swap: {swap.disk_swap_mb} MB"
        )
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setObjectName("status")
        layout.addWidget(info)


class DiskPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Storage")
        self.setSubTitle("Select the target disk and partition layout")
        self.devices: list[dict] = []
        self._loaded = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 16, 32, 16)
        layout.setSpacing(12)

        layout.addWidget(heading("Disk Selection"))

        self.device_combo = QComboBox()
        self.device_combo.setPlaceholderText("Scanning devices...")
        layout.addWidget(self.device_combo)

        self.refresh_btn = QPushButton("Refresh Devices")
        self.refresh_btn.setObjectName("secondary")
        self.refresh_btn.clicked.connect(self.load_devices)
        layout.addWidget(self.refresh_btn)

        layout.addWidget(separator())

        layout.addWidget(heading("Partition Layout"))

        form = QFormLayout()
        form.setSpacing(10)

        self.use_efi = QCheckBox("UEFI (recommended)")
        self.use_efi.setChecked(True)
        form.addRow("Boot mode:", self.use_efi)

        self.wipe_check = QCheckBox("Wipe entire disk (erases all data)")
        self.wipe_check.setChecked(True)
        form.addRow("", self.wipe_check)

        self.boot_size = QSpinBox()
        self.boot_size.setRange(256, 4096)
        self.boot_size.setValue(1024)
        self.boot_size.setSuffix(" MB")
        form.addRow("Boot size:", self.boot_size)

        self.root_size = QSpinBox()
        self.root_size.setRange(10, 500)
        self.root_size.setValue(40)
        self.root_size.setSuffix(" GB")
        form.addRow("Root size:", self.root_size)

        self.home_rest = QCheckBox("Use remaining space for /home")
        self.home_rest.setChecked(True)
        form.addRow("", self.home_rest)

        self.fs_combo = QComboBox()
        self.fs_combo.addItems(["ext4", "btrfs", "xfs"])
        self.fs_combo.setCurrentText("ext4")
        form.addRow("Filesystem:", self.fs_combo)

        layout.addLayout(form)
        layout.addStretch()

    def initializePage(self):
        if not self._loaded:
            QTimer.singleShot(100, self.load_devices)
            self._loaded = True

    def load_devices(self):
        self.device_combo.clear()
        self.device_combo.setEnabled(False)
        self.refresh_btn.setEnabled(False)

        def _fetch():
            inst = ArcrisInstaller()
            return inst.detect_devices()

        def _done(devs):
            self.devices = devs
            self.device_combo.clear()
            if not devs:
                self.device_combo.addItem("No devices found", "")
                self.device_combo.setPlaceholderText("No devices found")
            else:
                for d in devs:
                    label = f"{d['path']}  —  {d['model']}  ({d['size_gb']} GB)"
                    self.device_combo.addItem(label, d['path'])
                self.device_combo.setPlaceholderText("Select a disk...")
            self.device_combo.setEnabled(True)
            self.refresh_btn.setEnabled(True)

        self.t = RefreshThread(_fetch)
        self.t.finished.connect(_done)
        self.t.start()

    def get_selected_device(self) -> str | None:
        data = self.device_combo.currentData()
        return data if data else None

    def validatePage(self):
        if not self.devices:
            QMessageBox.warning(self, "Warning", "No disks detected. Refresh or check connections.")
            return False
        if not self.get_selected_device():
            QMessageBox.warning(self, "Warning", "Please select a disk.")
            return False
        return True


class SwapPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Memory Optimization")
        self.setSubTitle("Hybrid ZRAM + Disk Swap configuration")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 16, 32, 16)
        layout.setSpacing(12)

        layout.addWidget(heading("Swap Configuration"))

        ram_mb = detect_total_ram_mb()
        default_config = calculate_swap_config(ram_mb)

        info_card = QFrame()
        info_card.setObjectName("card")
        card_layout = QVBoxLayout(info_card)
        card_layout.setSpacing(4)
        ram_label = QLabel(f"Detected RAM: <b>{ram_mb} MB</b> ({ram_mb // 1024} GB)")
        ram_label.setStyleSheet("font-size: 14px;")
        card_layout.addWidget(ram_label)
        suggested = QLabel(
            f"Suggested: ZRAM <b>{default_config.zram_size_mb} MB</b>  "
            f"|  Disk swap <b>{default_config.disk_swap_mb} MB</b>"
        )
        card_layout.addWidget(suggested)
        layout.addWidget(info_card)

        layout.addWidget(separator())

        self.enable_zram = QCheckBox("Enable ZRAM (primary swap — compressed in RAM)")
        self.enable_zram.setChecked(True)
        layout.addWidget(self.enable_zram)

        zram_form = QFormLayout()
        self.zram_algo = QComboBox()
        self.zram_algo.addItems(["zstd", "lz4", "lzo", "lzo-rle", "lz4hc"])
        self.zram_algo.setCurrentText("zstd")
        zram_form.addRow("ZRAM algorithm:", self.zram_algo)

        self.zram_percent = QSlider(Qt.Orientation.Horizontal)
        self.zram_percent.setRange(25, 150)
        self.zram_percent.setValue(50 if ram_mb > 4096 else 100)
        self.zram_label = QLabel(f"{self.zram_percent.value()}% of RAM")
        self.zram_percent.valueChanged.connect(
            lambda v: self.zram_label.setText(f"{v}% of RAM ({ram_mb * v // 100} MB)")
        )
        zram_form.addRow("ZRAM size:", self.zram_percent)
        zram_form.addRow("", self.zram_label)
        layout.addLayout(zram_form)

        layout.addWidget(separator())

        self.enable_disk_swap = QCheckBox("Enable disk swap file (secondary — for hibernation/extreme load)")
        self.enable_disk_swap.setChecked(True)
        layout.addWidget(self.enable_disk_swap)

        swap_form = QFormLayout()
        self.swap_percent = QSlider(Qt.Orientation.Horizontal)
        self.swap_percent.setRange(5, 100)
        self.swap_percent.setValue(25)
        self.swap_pct_label = QLabel(f"{self.swap_percent.value()}% of RAM ({ram_mb * 25 // 100} MB)")
        self.swap_percent.valueChanged.connect(
            lambda v: self.swap_pct_label.setText(
                f"{v}% of RAM ({ram_mb * v // 100} MB)"
            )
        )
        swap_form.addRow("Disk swap size:", self.swap_percent)
        swap_form.addRow("", self.swap_pct_label)
        layout.addLayout(swap_form)

        layout.addWidget(separator())

        adv_card = QFrame()
        adv_card.setObjectName("card")
        adv_layout = QVBoxLayout(adv_card)
        adv_layout.addWidget(QLabel("Kernel tuning parameters (will be applied):"))
        sysctl_info = QLabel(
            "vm.swappiness = 180\n"
            "vm.vfs_cache_pressure = 50\n"
            "vm.watermark_boost_factor = 0\n"
            "vm.dirty_bytes = 15 MB\n"
            "vm.page-cluster = 0"
        )
        sysctl_info.setStyleSheet("color: #8888bb; font-family: monospace; font-size: 12px;")
        adv_layout.addWidget(sysctl_info)
        adv_card.setVisible(True)
        layout.addWidget(adv_card)

        layout.addStretch()


class EncryptionPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Encryption")
        self.setSubTitle("Optional LUKS disk encryption")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 16, 32, 16)
        layout.setSpacing(12)

        layout.addWidget(heading("Disk Encryption"))

        self.enable_enc = QCheckBox("Enable LUKS encryption for root partition")
        layout.addWidget(self.enable_enc)

        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.setPlaceholderText("Encryption passphrase")
        self.pass_input.setEnabled(False)
        layout.addWidget(self.pass_input)

        self.pass_confirm = QLineEdit()
        self.pass_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_confirm.setPlaceholderText("Confirm passphrase")
        self.pass_confirm.setEnabled(False)
        layout.addWidget(self.pass_confirm)

        self.enable_enc.toggled.connect(self.pass_input.setEnabled)
        self.enable_enc.toggled.connect(self.pass_confirm.setEnabled)

        warn = QLabel("WARNING: Encryption will be applied to root (and optionally home) partitions.")
        warn.setObjectName("status")
        warn.setWordWrap(True)
        layout.addWidget(warn)

        layout.addStretch()

    def validatePage(self):
        if self.enable_enc.isChecked():
            if not self.pass_input.text():
                QMessageBox.warning(self, "Warning", "Please enter an encryption passphrase.")
                return False
            if self.pass_input.text() != self.pass_confirm.text():
                QMessageBox.warning(self, "Warning", "Passphrases do not match.")
                return False
            if len(self.pass_input.text()) < 6:
                QMessageBox.warning(self, "Warning", "Passphrase must be at least 6 characters.")
                return False
        return True


class UserPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Users")
        self.setSubTitle("Create your user account")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 16, 32, 16)
        layout.setSpacing(12)

        layout.addWidget(heading("User Accounts"))

        form = QFormLayout()
        form.setSpacing(10)

        self.hostname_input = QLineEdit("arcris")
        form.addRow("Hostname:", self.hostname_input)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("e.g. johndoe")
        form.addRow("Username:", self.username_input)

        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.setPlaceholderText("User password")
        form.addRow("Password:", self.pass_input)

        self.pass_confirm = QLineEdit()
        self.pass_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_confirm.setPlaceholderText("Confirm password")
        form.addRow("Confirm:", self.pass_confirm)

        self.sudo_check = QCheckBox("Grant sudo access")
        self.sudo_check.setChecked(True)
        form.addRow("", self.sudo_check)

        layout.addLayout(form)

        layout.addWidget(separator())

        layout.addWidget(heading("Root Password (optional)"))

        self.root_pass = QLineEdit()
        self.root_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.root_pass.setPlaceholderText("Root password (leave empty for no root login)")
        layout.addWidget(self.root_pass)

        self.root_pass_confirm = QLineEdit()
        self.root_pass_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.root_pass_confirm.setPlaceholderText("Confirm root password")
        layout.addWidget(self.root_pass_confirm)

        layout.addStretch()

    def validatePage(self):
        if not self.username_input.text().strip():
            QMessageBox.warning(self, "Warning", "Please enter a username.")
            return False
        if not self.pass_input.text():
            QMessageBox.warning(self, "Warning", "Please enter a user password.")
            return False
        if self.pass_input.text() != self.pass_confirm.text():
            QMessageBox.warning(self, "Warning", "User passwords do not match.")
            return False
        if self.root_pass.text() and self.root_pass.text() != self.root_pass_confirm.text():
            QMessageBox.warning(self, "Warning", "Root passwords do not match.")
            return False
        return True


class ProfilePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Desktop Environment")
        self.setSubTitle("Select your desktop and additional packages")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 16, 32, 16)
        layout.setSpacing(12)

        layout.addWidget(heading("Desktop Profile"))

        self.profile_combo = QComboBox()
        self.profile_combo.addItems([
            "kde",
            "gnome",
            "xfce",
            "cinnamon",
            "minimal",
        ])
        self.profile_combo.setCurrentText("kde")
        layout.addWidget(self.profile_combo)

        layout.addWidget(separator())

        layout.addWidget(heading("Bootloader"))

        self.bootloader_combo = QComboBox()
        self.bootloader_combo.addItems(["systemd-boot", "grub", "limine", "none"])
        self.bootloader_combo.setCurrentText("systemd-boot")
        layout.addWidget(self.bootloader_combo)

        layout.addWidget(separator())

        layout.addWidget(heading("Timezone"))

        self.timezone_combo = QComboBox()
        tz_list = [
            "America/Argentina/Buenos_Aires",
            "America/Mexico_City",
            "America/Lima",
            "America/Santiago",
            "America/Bogota",
            "America/Sao_Paulo",
            "America/New_York",
            "America/Chicago",
            "America/Denver",
            "America/Los_Angeles",
            "America/Anchorage",
            "Pacific/Honolulu",
            "Europe/Madrid",
            "Europe/London",
            "Europe/Paris",
            "Europe/Berlin",
            "Europe/Moscow",
            "Asia/Tokyo",
            "Asia/Shanghai",
            "Asia/Kolkata",
            "Asia/Dubai",
            "Asia/Singapore",
            "Australia/Sydney",
            "Africa/Cairo",
            "Africa/Johannesburg",
            "UTC",
        ]
        tz_list.sort()
        self.timezone_combo.addItems(tz_list)
        self.timezone_combo.setCurrentText("America/Argentina/Buenos_Aires")
        layout.addWidget(self.timezone_combo)

        layout.addWidget(separator())

        layout.addWidget(heading("Additional Packages"))

        self.packages_edit = QLineEdit()
        self.packages_edit.setPlaceholderText("e.g. neovim git docker htop")
        layout.addWidget(self.packages_edit)

        layout.addStretch()


class SummaryPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Summary")
        self.setSubTitle("Review your configuration before installation")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 16, 32, 16)
        layout.setSpacing(12)

        layout.addWidget(heading("Installation Summary"))

        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setStyleSheet(
            "QTextEdit {"
            "  background-color: #0a0a1a;"
            "  border: 1px solid #2a2a5a;"
            "  border-radius: 8px;"
            "  padding: 12px;"
            "  color: #e0e0ff;"
            "  font-size: 13px;"
            "  font-family: 'Fira Code', monospace;"
            "}"
        )
        layout.addWidget(self.summary_text)

        warn = QLabel("WARNING: All data on the selected disk will be erased!")
        warn.setStyleSheet("color: #ff6666; font-weight: bold; font-size: 14px; padding: 8px;")
        warn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(warn)

        layout.addStretch()

    def initializePage(self):
        wizard = cast(InstallerWizard, self.wizard())
        lines = []

        disk_page = wizard.page(1)
        if isinstance(disk_page, DiskPage):
            dev = disk_page.get_selected_device()
            lines.append(f"Disk:     {dev or 'Not selected'}")
            lines.append(f"Boot:     {disk_page.boot_size.value()} MB")
            lines.append(f"Root:     {disk_page.root_size.value()} GB")
            lines.append(f"Home:     {'Remaining space' if disk_page.home_rest.isChecked() else 'No /home partition'}")
            lines.append(f"FS:       {disk_page.fs_combo.currentText()}")
            lines.append(f"Wipe:     {'Yes' if disk_page.wipe_check.isChecked() else 'No'}")

        swap_page = wizard.page(2)
        if isinstance(swap_page, SwapPage):
            lines.append("")
            lines.append("--- Memory ---")
            lines.append(f"ZRAM:     {'Enabled' if swap_page.enable_zram.isChecked() else 'Disabled'}")
            if swap_page.enable_zram.isChecked():
                ram = detect_total_ram_mb()
                pct = swap_page.zram_percent.value()
                lines.append(f"  Size:   {pct}% = {ram * pct // 100} MB")
                lines.append(f"  Algo:   {swap_page.zram_algo.currentText()}")
            lines.append(f"Disk SWAP: {'Enabled' if swap_page.enable_disk_swap.isChecked() else 'Disabled'}")

        enc_page = wizard.page(3)
        if isinstance(enc_page, EncryptionPage):
            lines.append("")
            lines.append("--- Encryption ---")
            lines.append(f"LUKS:     {'Enabled' if enc_page.enable_enc.isChecked() else 'Disabled'}")

        user_page = wizard.page(4)
        if isinstance(user_page, UserPage):
            lines.append("")
            lines.append("--- Users ---")
            lines.append(f"Hostname: {user_page.hostname_input.text()}")
            lines.append(f"User:     {user_page.username_input.text()}")
            lines.append(f"Sudo:     {'Yes' if user_page.sudo_check.isChecked() else 'No'}")

        prof_page = wizard.page(5)
        if isinstance(prof_page, ProfilePage):
            lines.append("")
            lines.append("--- Software ---")
            lines.append(f"Profile:  {prof_page.profile_combo.currentText()}")
            lines.append(f"Bootloader: {prof_page.bootloader_combo.currentText()}")
            lines.append(f"Timezone: {prof_page.timezone_combo.currentText()}")
            pkgs = prof_page.packages_edit.text().strip()
            if pkgs:
                lines.append(f"Packages: {pkgs}")

        self.summary_text.setText("\n".join(lines))


class InstallPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Installing")
        self.setSubTitle("Arcris is installing Arch Linux to your disk")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 16, 32, 16)
        layout.setSpacing(12)

        layout.addWidget(heading("Installation Progress"))

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 12)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Initializing...")
        self.status_label.setObjectName("status")
        layout.addWidget(self.status_label)

        layout.addWidget(separator())

        log_header = QLabel("Installation Log")
        log_header.setStyleSheet("font-weight: bold; font-size: 13px; color: #9090cc;")
        layout.addWidget(log_header)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        self.worker = None
        self._finished = False

    def initializePage(self):
        self._finished = False
        self.progress_bar.setValue(0)
        self.status_label.setText("Preparing installer...")
        self.log_output.clear()
        self.wizard().button(QWizard.WizardButton.BackButton).setEnabled(False)
        self.wizard().button(QWizard.WizardButton.NextButton).setEnabled(False)
        QTimer.singleShot(500, self._start_install)

    def _start_install(self):
        wizard = cast(InstallerWizard, self.wizard())
        try:
            installer = self._build_installer(wizard)
        except Exception as e:
            self._on_log(f"FATAL: Failed to configure installer: {e}")
            self.status_label.setText(f"Error: {e}")
            self.status_label.setStyleSheet("color: #ff5252; font-weight: bold;")
            self._finished = True
            self.wizard().button(QWizard.WizardButton.NextButton).setEnabled(True)
            return

        self.worker = InstallWorker(installer)
        self.worker.progress.connect(self._on_progress)
        self.worker.log.connect(self._on_log)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _build_installer(self, wizard: "InstallerWizard") -> ArcrisInstaller:
        installer = ArcrisInstaller()

        disk_p = cast(DiskPage, wizard.page(1))
        swap_p = cast(SwapPage, wizard.page(2))
        enc_p = cast(EncryptionPage, wizard.page(3))
        user_p = cast(UserPage, wizard.page(4))
        prof_p = cast(ProfilePage, wizard.page(5))

        device_path = disk_p.get_selected_device()
        if not device_path:
            raise ValueError("No disk selected")
        if not installer.set_device(device_path):
            raise ValueError(f"Could not access device: {device_path}")

        fs_text = disk_p.fs_combo.currentText()
        installer.use_btrfs = (fs_text == "btrfs")
        if fs_text == "xfs":
            from archinstall.lib.models.device import FilesystemType
            installer.fs_type = FilesystemType("xfs")

        installer.configure_disk_layout(
            boot_mb=disk_p.boot_size.value(),
            root_gb=disk_p.root_size.value(),
            home_uses_rest=disk_p.home_rest.isChecked(),
            wipe=disk_p.wipe_check.isChecked(),
        )

        if enc_p.enable_enc.isChecked():
            installer.encryption_password = enc_p.pass_input.text()

        installer.swap_enabled = swap_p.enable_zram.isChecked()
        installer.use_disk_swap = swap_p.enable_disk_swap.isChecked()

        ram_mb = detect_total_ram_mb()
        installer.swap_zram_algo = swap_p.zram_algo.currentText()
        installer.swap_size_mb = int(ram_mb * swap_p.zram_percent.value() / 100)

        username = user_p.username_input.text().strip()
        password = user_p.pass_input.text()
        if username and password:
            installer.add_user(
                username,
                password,
                sudo=user_p.sudo_check.isChecked(),
            )
        installer.hostname = user_p.hostname_input.text().strip() or "arcris"

        if user_p.root_pass.text():
            from archinstall.lib.models.users import Password
            installer.root_password = Password(plaintext=user_p.root_pass.text())

        installer.desktop_profile = prof_p.profile_combo.currentText()

        from archinstall.lib.models.bootloader import Bootloader
        bl_text = prof_p.bootloader_combo.currentText()
        if bl_text == "grub":
            installer.bootloader = Bootloader.GRUB
        elif bl_text == "limine":
            installer.bootloader = Bootloader.LIMINE
        elif bl_text == "none":
            installer.bootloader = Bootloader.NO_BOOTLOADER
        else:
            installer.bootloader = Bootloader.SYSTEMD

        installer.timezone = prof_p.timezone_combo.currentText()

        pkgs = prof_p.packages_edit.text().strip()
        if pkgs:
            installer.packages = [p for p in pkgs.split() if p]

        return installer

    def _on_progress(self, step: int, total: int, label: str):
        self.progress_bar.setValue(step)
        self.progress_bar.setMaximum(total)
        self.status_label.setText(f"[{step}/{total}] {label}")

    def _on_log(self, msg: str):
        self.log_output.append(msg)
        cursor = self.log_output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_output.setTextCursor(cursor)

    def _on_finished(self, success: bool, message: str):
        self._finished = True
        self._on_log("")
        if success:
            self._on_log("✓ " + message)
            self.status_label.setStyleSheet("color: #00e676; font-weight: bold;")
        else:
            self._on_log("✗ " + message)
            self.status_label.setStyleSheet("color: #ff5252; font-weight: bold;")
        self.status_label.setText(message)
        self.wizard().button(QWizard.WizardButton.NextButton).setEnabled(True)

    def _on_error(self, msg: str):
        self._on_log(f"ERROR: {msg}")

    def isComplete(self):
        return self._finished

    def validatePage(self):
        return self._finished

    def cleanupPage(self):
        pass


class FinishPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Complete")
        self.setSubTitle("Arcris has been installed")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(12)

        layout.addStretch()

        title = QLabel("Installation Complete!")
        title.setObjectName("heading")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 32px; color: #00e676; font-weight: bold;")
        layout.addWidget(title)

        subtitle = QLabel("Arcris is ready. Remove the installation media and reboot.")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 15px; color: #8888bb;")
        layout.addWidget(subtitle)

        layout.addSpacing(20)

        info_card = QFrame()
        info_card.setObjectName("card")
        card_layout = QVBoxLayout(info_card)
        for line in [
            "✓ Arch Linux base installed",
            "✓ Hybrid ZRAM + Disk Swap configured",
            "✓ KDE Plasma with macOS-style theme applied",
            "✓ Kernel memory optimizations set",
            "✓ User accounts created",
        ]:
            lbl = QLabel(line)
            lbl.setStyleSheet("color: #b0b0e0; font-size: 13px; padding: 2px 0;")
            card_layout.addWidget(lbl)
        layout.addWidget(info_card)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        self.reboot_btn = QPushButton("Reboot Now")
        self.reboot_btn.clicked.connect(self._reboot)
        btn_layout.addWidget(self.reboot_btn)

        self.shutdown_btn = QPushButton("Shutdown")
        self.shutdown_btn.setObjectName("secondary")
        self.shutdown_btn.clicked.connect(self._shutdown)
        btn_layout.addWidget(self.shutdown_btn)

        layout.addLayout(btn_layout)
        layout.addStretch()

    def _reboot(self):
        os.system("reboot")

    def _shutdown(self):
        os.system("poweroff")


class InstallerWizard(QWizard):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arcris Installer")
        self.setFixedSize(800, 640)
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setOption(QWizard.WizardOption.NoBackButtonOnLastPage, True)
        self.setOption(QWizard.WizardOption.HaveFinishButtonOnEarlyPages, False)
        self.setOption(QWizard.WizardOption.HaveCustomButton1, False)

        self.setStyleSheet(DARK_STYLESHEET)

        self.setPage(0, WelcomePage())
        self.setPage(1, DiskPage())
        self.setPage(2, SwapPage())
        self.setPage(3, EncryptionPage())
        self.setPage(4, UserPage())
        self.setPage(5, ProfilePage())
        self.setPage(6, SummaryPage())
        self.setPage(7, InstallPage())
        self.setPage(8, FinishPage())

        self.setStartId(0)

        self.currentIdChanged.connect(self._on_page_changed)

    def _on_page_changed(self, page_id: int):
        if page_id == 7:
            self.button(QWizard.WizardButton.BackButton).setEnabled(False)
            self.button(QWizard.WizardButton.NextButton).setText("Installing...")
        elif page_id == 8:
            self.button(QWizard.WizardButton.BackButton).setEnabled(False)
            self.button(QWizard.WizardButton.NextButton).setText("Finish")
            self.button(QWizard.WizardButton.CancelButton).setEnabled(False)
        else:
            self.button(QWizard.WizardButton.NextButton).setText("Next >")


def run_gui():
    app = QApplication(sys.argv)
    app.setApplicationName("Arcris Installer")
    app.setStyle("Fusion")

    wizard = InstallerWizard()
    wizard.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_gui()
