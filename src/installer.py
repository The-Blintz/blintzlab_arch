"""
Core installer — wraps archinstall library with Arcris-specific extensions:
- Hybrid ZRAM + disk swap
- Desktop profile installation
- Post-install optimization scripts
"""

import time
from pathlib import Path

from archinstall.lib.disk.device_handler import device_handler
from archinstall.lib.disk.filesystem import FilesystemHandler
from archinstall.lib.installer import Installer
from archinstall.lib.models.application import ZramAlgorithm
from archinstall.lib.models.bootloader import Bootloader
from archinstall.lib.models.device import (
    DeviceModification,
    DiskEncryption,
    DiskLayoutConfiguration,
    DiskLayoutType,
    EncryptionType,
    FilesystemType,
    ModificationStatus,
    PartitionFlag,
    PartitionModification,
    PartitionType,
    Size,
    Unit,
)
from archinstall.lib.models.locale import LocaleConfiguration
from archinstall.lib.models.profile import ProfileConfiguration
from archinstall.lib.models.users import Password, User
from archinstall.lib.profile.profiles_handler import profile_handler

from src.swap_manager import configure_hybrid_swap

MOUNTPOINT = Path("/mnt")


class ArcrisInstaller:
    def __init__(self):
        self.mountpoint = MOUNTPOINT
        self.device = None
        self.device_mod = None
        self.disk_config = None
        self.hostname = "arcris"
        self.locale_config = LocaleConfiguration.default()
        self.timezone = "UTC"
        self.kernels = ["linux"]
        self.users: list[User] = []
        self.root_password: Password | None = None
        self.bootloader = Bootloader.SYSTEMD
        self.encryption_password: str | None = None
        self.desktop_profile = "kde"
        self.fs_type = FilesystemType("ext4")
        self.swap_size_mb = 0
        self.swap_enabled = True
        self.swap_zram_algo = ZramAlgorithm.ZSTD
        self.packages: list[str] = []
        self.services: list[str] = []
        self.use_disk_swap = True
        self.use_btrfs = False

    def detect_devices(self) -> list[dict]:
        result = []
        for info in device_handler.list_devices():
            result.append({
                "path": str(info.path),
                "model": info.model,
                "size_gb": info.size_gb,
                "sector_size": info.sector_size,
                "fs_type": info.fs_type,
            })
        return result

    def set_device(self, device_path: str) -> bool:
        dev = device_handler.get_device(Path(device_path))
        if dev is None:
            return False
        self.device = dev
        return True

    def configure_disk_layout(
        self,
        boot_mb: int = 1024,
        root_gb: int = 30,
        swap_mb: int = 0,
        home_uses_rest: bool = True,
        use_efi: bool = True,
        wipe: bool = True,
    ) -> None:
        if self.device is None:
            raise ValueError("No device selected")

        fs_type = FilesystemType("btrfs") if self.use_btrfs else self.fs_type
        sector_size = self.device.device_info.sector_size

        device_mod = DeviceModification(self.device, wipe=wipe)

        boot_partition = PartitionModification(
            status=ModificationStatus.CREATE,
            type=PartitionType.PRIMARY,
            start=Size(1, Unit.MiB, sector_size),
            length=Size(boot_mb, Unit.MiB, sector_size),
            mountpoint=Path("/boot"),
            fs_type=FilesystemType.FAT32,
            flags=[PartitionFlag.BOOT],
        )
        device_mod.add_partition(boot_partition)

        next_start = Size(boot_mb + 1, Unit.MiB, sector_size)

        if swap_mb > 0:
            swap_partition = PartitionModification(
                status=ModificationStatus.CREATE,
                type=PartitionType.PRIMARY,
                start=next_start,
                length=Size(swap_mb, Unit.MiB, sector_size),
                mountpoint=None,
                fs_type=FilesystemType("swap"),
            )
            device_mod.add_partition(swap_partition)
            next_start = Size(
                boot_mb + 1 + swap_mb,
                Unit.MiB,
                sector_size,
            )

        root_partition = PartitionModification(
            status=ModificationStatus.CREATE,
            type=PartitionType.PRIMARY,
            start=next_start,
            length=Size(root_gb, Unit.GiB, sector_size),
            mountpoint=None,
            fs_type=fs_type,
        )
        device_mod.add_partition(root_partition)

        if home_uses_rest:
            start_home = root_partition.length
            length_home = self.device.device_info.total_size - start_home
            home_partition = PartitionModification(
                status=ModificationStatus.CREATE,
                type=PartitionType.PRIMARY,
                start=start_home,
                length=length_home,
                mountpoint=Path("/home"),
                fs_type=fs_type,
            )
            device_mod.add_partition(home_partition)

        self.device_mod = device_mod

        disk_config = DiskLayoutConfiguration(
            config_type=DiskLayoutType.Default,
            device_modifications=[device_mod],
        )

        if self.encryption_password:
            disk_config.disk_encryption = DiskEncryption(
                encryption_password=Password(plaintext=self.encryption_password),
                encryption_type=EncryptionType.LUKS,
                partitions=[root_partition] + (
                    [home_partition] if home_uses_rest else []
                ),
            )

        self.disk_config = disk_config
        self._root_part = root_partition

    def run_filesystem_operations(self) -> bool:
        if self.disk_config is None:
            return False

        fs_handler = FilesystemHandler(self.disk_config)
        try:
            fs_handler.perform_filesystem_operations()
            return True
        except Exception:
            return False

    def run_installation(self, progress_callback=None) -> bool:
        if self.disk_config is None:
            raise ValueError("Disk config not set. Call configure_disk_layout() first.")

        total_steps = 12
        current_step = [0]

        def progress_step(label: str):
            current_step[0] += 1
            if progress_callback:
                progress_callback(current_step[0], total_steps, label)

        progress_step("Mounting filesystems")

        with Installer(
            self.mountpoint,
            self.disk_config,
            kernels=self.kernels,
        ) as installation:
            progress_step("Ordered mount")

            installation.mount_ordered_layout()
            installation.sanity_check()

            if self.disk_config.disk_encryption and self.disk_config.disk_encryption.encryption_type != EncryptionType.NO_ENCRYPTION:
                installation.generate_key_files()

            progress_step("Base installation (pacstrap)")

            installation.minimal_installation(
                hostname=self.hostname,
                locale_config=self.locale_config,
            )

            progress_step("Configuring mirrors")

            progress_step("Configuring hybrid swap")

            if self.swap_enabled:
                from src.swap_manager import setup_swap_in_archinstall
                ram_mb = detect_total_ram_mb()
                setup_swap_in_archinstall(installation, total_ram_mb=ram_mb)

            progress_step("Installing bootloader")

            installation.add_bootloader(self.bootloader)

            progress_step("Creating users")

            if self.users:
                installation.create_users(self.users)

            if self.root_password:
                root_user = User("root", self.root_password, False)
                installation.set_user_password(root_user)

            progress_step("Installing desktop profile")

            if self.desktop_profile:
                self._install_desktop_profile(installation)

            progress_step("Additional packages")

            if self.packages:
                installation.add_additional_packages(self.packages)

            progress_step("Timezone")

            installation.set_timezone(self.timezone)
            installation.activate_time_synchronization()

            progress_step("Enabling services")

            if self.services:
                installation.enable_service(self.services)

            progress_step("Generating fstab")

            installation.genfstab()

            progress_step("Post-install optimizations")

            self._apply_post_install_scripts(installation)

            progress_step("Done")

            return True

    def _install_desktop_profile(self, installation) -> None:
        profile_map = {
            "kde": "archinstall.default_profiles.desktop.KdeProfile",
            "gnome": "archinstall.default_profiles.desktop.GnomeProfile",
            "xfce": "archinstall.default_profiles.desktop.XFCEProfile",
            "cinnamon": "archinstall.default_profiles.desktop.CinnamonProfile",
        }

        if self.desktop_profile in profile_map:
            profile = profile_handler.get_profile_by_name(self.desktop_profile)
            if profile is None:
                from archinstall.default_profiles.desktop import (
                    KdeProfile,
                )
                profile = KdeProfile()
        else:
            from archinstall.default_profiles.minimal import MinimalProfile
            profile = MinimalProfile()

        profile_config = ProfileConfiguration(profile)
        profile_handler.install_profile_config(installation, profile_config)

        if self.users:
            profile.post_install(installation)
            profile.provision(installation, self.users)

    def _apply_post_install_scripts(self, installation) -> None:
        scripts_dir = Path(__file__).parent.parent / "scripts"
        for script_path in sorted(scripts_dir.glob("*.sh")):
            if script_path.name.startswith("post_"):
                dest = installation.target / "opt/arcris/scripts" / script_path.name
                dest.parent.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy(script_path, dest)
                dest.chmod(0o755)

    def add_user(self, name: str, password_plaintext: str, sudo: bool = True) -> None:
        self.users.append(User(name, Password(plaintext=password_plaintext), sudo))
