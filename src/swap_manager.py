"""
Swap Manager — ZRAM + disk swap hybrid configuration with dynamic sizing
and kernel parameter optimization for performance.

Strategy:
  ZRAM (primary, high priority): 50% RAM for <=8GB, 100% RAM for <=4GB, zstd algo
  Disk SWAP (secondary, low priority): fallback for hibernation / extreme load
"""

import os
import re
import shutil
from pathlib import Path
from typing import NamedTuple


class SwapConfig(NamedTuple):
    zram_size_mb: int
    disk_swap_mb: int
    zram_algorithm: str = "zstd"
    swappiness: int = 180
    vfs_cache_pressure: int = 50
    watermark_boost_factor: int = 0
    dirty_bytes: int = 15 * 1024 * 1024  # 15 MB
    dirty_background_bytes: int = 5 * 1024 * 1024  # 5 MB
    zram_priority: int = 100
    disk_swap_priority: int = -1


def detect_total_ram_mb() -> int:
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    kb = int(re.findall(r'\d+', line)[0])
                    return kb // 1024
    except Exception:
        pass

    try:
        import psutil
        return psutil.virtual_memory().total // (1024 * 1024)
    except ImportError:
        pass

    return 2048


def calculate_swap_config(total_ram_mb: int, disk_swap_percent: float = 0.25) -> SwapConfig:
    if total_ram_mb <= 4 * 1024:
        zram_size = total_ram_mb
    elif total_ram_mb <= 8 * 1024:
        zram_size = total_ram_mb // 2
    else:
        zram_size = min(total_ram_mb // 2, 8 * 1024)

    disk_swap = int(total_ram_mb * disk_swap_percent)

    return SwapConfig(
        zram_size_mb=zram_size,
        disk_swap_mb=disk_swap,
        zram_algorithm="zstd",
        swappiness=180,
        vfs_cache_pressure=50,
        watermark_boost_factor=0,
        dirty_bytes=15 * 1024 * 1024,
        dirty_background_bytes=5 * 1024 * 1024,
        zram_priority=100,
        disk_swap_priority=-1,
    )


def write_zram_generator_config(target: Path, config: SwapConfig) -> None:
    zram_dir = target / "etc/systemd"
    zram_dir.mkdir(parents=True, exist_ok=True)

    conf_path = zram_dir / "zram-generator.conf"

    # zram-generator uses min(ram / N, LIMIT) format
    # For 50% of RAM capped at configured max
    conf_path.write_text(
        "[zram0]\n"
        f"zram-size = min(ram / 2, {config.zram_size_mb})\n"
        f"compression-algorithm = {config.zram_algorithm}\n"
        f"max-zram-size = {config.zram_size_mb}\n"
    )


def write_sysctl_optimizations(target: Path, config: SwapConfig) -> None:
    sysctl_dir = target / "etc/sysctl.d"
    sysctl_dir.mkdir(parents=True, exist_ok=True)

    conf = sysctl_dir / "99-arcris-memory-optimization.conf"
    conf.write_text(
        f"# Arcris memory optimization\n"
        f"# Aggressive ZRAM usage with low disk swap\n"
        f"vm.swappiness = {config.swappiness}\n"
        f"vm.vfs_cache_pressure = {config.vfs_cache_pressure}\n"
        f"vm.watermark_boost_factor = {config.watermark_boost_factor}\n"
        f"vm.dirty_bytes = {config.dirty_bytes}\n"
        f"vm.dirty_background_bytes = {config.dirty_background_bytes}\n"
        f"vm.page-cluster = 0\n"
        f"vm.compact_memory = 1\n"
    )


def create_disk_swap_script(target: Path, swap_size_mb: int, swap_file: str = "/swapfile") -> str:
    script_dir = target / "opt/arcris/scripts"
    script_dir.mkdir(parents=True, exist_ok=True)

    script_path = script_dir / "create-swap.sh"
    content = f"""#!/usr/bin/env bash
set -euo pipefail

SWAPFILE="{swap_file}"
SWAPSIZE_MB={swap_size_mb}

echo "[arcris] Creating swap file: $SWAPFILE ($SWAPSIZE_MB MB)"

# Only create if it doesn't already exist or is wrong size
if [ -f "$SWAPFILE" ]; then
    CURRENT_SIZE=$(stat -c%s "$SWAPFILE" 2>/dev/null || echo 0)
    EXPECTED_SIZE=$((SWAPSIZE_MB * 1024 * 1024))
    if [ "$CURRENT_SIZE" -eq "$EXPECTED_SIZE" ]; then
        echo "[arcris] Swap file already exists with correct size"
        if ! swapon --show | grep -q "$SWAPFILE"; then
            swapon "$SWAPFILE"
        fi
        exit 0
    fi
fi

truncate -s 0 "$SWAPFILE" 2>/dev/null || true
fallocate -l "${{SWAPSIZE_MB}}M" "$SWAPFILE" 2>/dev/null || \\
    dd if=/dev/zero of="$SWAPFILE" bs=1M count="$SWAPSIZE_MB" status=progress

chmod 0600 "$SWAPFILE"
mkswap "$SWAPFILE"

if ! grep -q "$SWAPFILE" /etc/fstab; then
    echo "$SWAPFILE none swap defaults,pri=-1 0 0" >> /etc/fstab
fi

swapon "$SWAPFILE"

echo "[arcris] Disk swap activated."
"""
    script_path.write_text(content)
    script_path.chmod(0o755)

    return str(script_path.relative_to(target))


def configure_hybrid_swap(target: Path, total_ram_mb: int | None = None) -> SwapConfig:
    if total_ram_mb is None:
        total_ram_mb = detect_total_ram_mb()

    config = calculate_swap_config(total_ram_mb)

    write_sysctl_optimizations(target, config)
    write_zram_generator_config(target, config)

    swap_script_rel = create_disk_swap_script(target, config.disk_swap_mb)

    return config


def setup_swap_in_archinstall(
    installation,
    total_ram_mb: int | None = None,
) -> None:
    from archinstall.lib.models.application import ZramAlgorithm

    installation.setup_swap(algo=ZramAlgorithm.ZSTD)

    if total_ram_mb is None:
        total_ram_mb = detect_total_ram_mb()

    config = calculate_swap_config(total_ram_mb)

    write_sysctl_optimizations(installation.target, config)

    swap_mb = config.disk_swap_mb
    enable_resume = total_ram_mb >= 4096
    size_str = f"{swap_mb}M"

    installation.add_swapfile(size=size_str, enable_resume=enable_resume, file="/swapfile")

    info_msg = (
        f"[arcris] Hybrid swap configured:\n"
        f"   ZRAM: {config.zram_size_mb} MB (zstd, pri={config.zram_priority})\n"
        f"   Disk swap: {config.disk_swap_mb} MB (pri={config.disk_swap_priority})\n"
        f"   Swappiness: {config.swappiness}\n"
    )
    from archinstall.lib.log import info
    info(info_msg)
