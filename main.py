#!/usr/bin/env python3
"""
Arcris Installer — graphical Arch Linux installer with hybrid swap,
KDE Plasma macOS-inspired theme, and post-install optimization.

Entry point: requires root, checks dependencies, launches GUI wizard.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def check_root() -> None:
    if os.geteuid() != 0:
        print("ERROR: Arcris installer must be run as root.")
        print("  Run: sudo python3 main.py")
        sys.exit(1)


def check_dependencies() -> None:
    required = ["archinstall"]
    missing = []
    for mod in required:
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
    if missing:
        print(f"ERROR: Missing dependencies: {', '.join(missing)}")
        print("  Install with: pacman -S archinstall python-pyside6")
        sys.exit(1)


def check_live_environment() -> None:
    if not Path("/run/archiso").exists():
        print("WARNING: /run/archiso not found. You may not be on the Arch ISO.")
        print("  Proceeding anyway...")


def main() -> None:
    check_root()
    check_dependencies()
    check_live_environment()

    try:
        from PySide6.QtWidgets import QApplication
        from gui.main_window import InstallerWizard
    except ImportError:
        print("ERROR: PySide6 not found. Install with: pacman -S python-pyside6")
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setApplicationName("Arcris Installer")

    wizard = InstallerWizard()
    wizard.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
