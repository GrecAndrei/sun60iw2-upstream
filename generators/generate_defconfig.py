#!/usr/bin/env python3
"""
Kernel defconfig generator for Orange Pi 4 Pro.

Generates a board-specific defconfig from a structured specification.
Avoids manual .config editing.

Usage:
    python3 generators/generate_defconfig.py > configs/sun60iw2_defconfig
"""

import sys
from pathlib import Path

# Structured specification of kernel config options
DEFCONFIG_SPEC = {
    "_metadata": {
        "board": "Orange Pi 4 Pro",
        "soc": "Allwinner A733 (sun60iw2)",
        "purpose": "Initial bringup - UART, SD, network",
    },
    "architecture": {
        "CONFIG_ARCH_SUNXI": "y",
        "CONFIG_ARCH_SUN60IW2": "y",  # Will add when we create the Kconfig entry
        "CONFIG_64BIT": "y",
        "CONFIG_ARM64": "y",
        "CONFIG_ARM64_4K_PAGES": "y",
        "CONFIG_ARM64_VA_BITS_39": "y",
    },
    "cpu": {
        "CONFIG_SMP": "y",
        "CONFIG_NR_CPUS": "8",
        "CONFIG_ARM_PSCI": "y",
        "CONFIG_CPU_FREQ": "y",
        "CONFIG_CPU_FREQ_DEFAULT_GOV_SCHEDUTIL": "y",
        "CONFIG_CPU_FREQ_GOV_PERFORMANCE": "y",
        "CONFIG_CPU_FREQ_GOV_POWERSAVE": "y",
        "CONFIG_CPU_FREQ_GOV_USERSPACE": "y",
        "CONFIG_CPU_FREQ_GOV_ONDEMAND": "y",
        "CONFIG_CPU_FREQ_GOV_CONSERVATIVE": "y",
        "CONFIG_CPU_FREQ_GOV_SCHEDUTIL": "y",
        "CONFIG_ARM_SUN50I_CPUFREQ_NVMEM": "y",
    },
    "serial": {
        "CONFIG_SERIAL_8250": "y",
        "CONFIG_SERIAL_8250_CONSOLE": "y",
        "CONFIG_SERIAL_8250_NR_UARTS": "8",
        "CONFIG_SERIAL_8250_RUNTIME_UARTS": "8",
        "CONFIG_SERIAL_8250_DW": "y",
        "CONFIG_SERIAL_OF_PLATFORM": "y",
    },
    "clocks": {
        "CONFIG_COMMON_CLK": "y",
        "CONFIG_CLK_SUNXI": "y",
        "CONFIG_CLK_SUNXI_CLOCKS": "y",
        "CONFIG_CLK_SUNXI_PRCM": "y",
        "CONFIG_SUNXI_CCU": "y",
        "CONFIG_SUN50I_A64_CCU": "y",
        "CONFIG_SUN50I_H6_CCU": "y",
        "CONFIG_SUN50I_H616_CCU": "y",
        "CONFIG_SUN55I_A523_CCU": "y",
        "CONFIG_SUN60I_A733_CCU": "y",  # Our new driver
    },
    "pinctrl": {
        "CONFIG_PINCTRL": "y",
        "CONFIG_PINCTRL_SUNXI": "y",
        "CONFIG_PINCTRL_SUN50I_A64": "y",
        "CONFIG_PINCTRL_SUN50I_H6": "y",
        "CONFIG_PINCTRL_SUN50I_H616": "y",
        "CONFIG_PINCTRL_SUN55I_A523": "y",
        "CONFIG_PINCTRL_SUN60I_A733": "y",  # Our new driver
    },
    "mmc": {
        "CONFIG_MMC": "y",
        "CONFIG_MMC_SUNXI": "y",
    },
    "network": {
        "CONFIG_NET": "y",
        "CONFIG_ETHERNET": "y",
        "CONFIG_NET_VENDOR_STMICRO": "y",
        "CONFIG_STMMAC_ETH": "y",
        "CONFIG_STMMAC_PLATFORM": "y",
        "CONFIG_DWMAC_SUNXI": "y",
        "CONFIG_DWMAC_SUN55I": "y",
        "CONFIG_MDIO_DEVICE": "y",
        "CONFIG_PHYLIB": "y",
    },
    "usb": {
        "CONFIG_USB": "y",
        "CONFIG_USB_SUPPORT": "y",
        "CONFIG_USB_COMMON": "y",
        "CONFIG_USB_EHCI_HCD": "y",
        "CONFIG_USB_EHCI_ROOT_HUB_TT": "y",
        "CONFIG_USB_OHCI_HCD": "y",
        "CONFIG_USB_DWC3": "y",
        "CONFIG_USB_DWC3_HOST": "y",
    },
    "filesystems": {
        "CONFIG_EXT4_FS": "y",
        "CONFIG_VFAT_FS": "y",
        "CONFIG_TMPFS": "y",
        "CONFIG_DEVTMPFS": "y",
        "CONFIG_DEVTMPFS_MOUNT": "y",
    },
    "debug": {
        "CONFIG_DEBUG_KERNEL": "y",
        "CONFIG_DEBUG_LL": "y",
        "CONFIG_EARLY_PRINTK": "y",
        "CONFIG_PRINTK_TIME": "y",
        "CONFIG_DYNAMIC_DEBUG": "y",
    },
}


def generate_defconfig(spec):
    """Generate defconfig text from specification."""
    lines = []

    lines.append("# Automatically generated defconfig")
    lines.append(f"# Board: {spec['_metadata']['board']}")
    lines.append(f"# SoC: {spec['_metadata']['soc']}")
    lines.append(f"# Purpose: {spec['_metadata']['purpose']}")
    lines.append("")

    for category, options in spec.items():
        if category.startswith("_"):
            continue

        lines.append(f"# {category.upper()}")
        for key, value in sorted(options.items()):
            lines.append(f"{key}={value}")
        lines.append("")

    return "\n".join(lines)


def generate_minimal_defconfig():
    """Generate absolute minimal defconfig for UART bringup only."""

    minimal = """# Minimal defconfig for Orange Pi 4 Pro UART bringup
# This is the smallest config that can boot to a shell prompt

CONFIG_ARCH_SUNXI=y
CONFIG_ARCH_SUN60IW2=y
CONFIG_64BIT=y
CONFIG_ARM64=y

# CPU
CONFIG_SMP=y
CONFIG_NR_CPUS=8
CONFIG_ARM_PSCI=y

# Serial - CRITICAL for bringup
CONFIG_SERIAL_8250=y
CONFIG_SERIAL_8250_CONSOLE=y
CONFIG_SERIAL_8250_DW=y
CONFIG_SERIAL_OF_PLATFORM=y

# Clocks
CONFIG_COMMON_CLK=y
CONFIG_SUNXI_CCU=y
CONFIG_SUN60I_A733_CCU=y

# Pinctrl
CONFIG_PINCTRL=y
CONFIG_PINCTRL_SUNXI=y
CONFIG_PINCTRL_SUN60I_A733=y

# Timer
CONFIG_TIMER_OF=y

# Basic kernel features
CONFIG_BLOCK=y
CONFIG_BLK_DEV=y
CONFIG_BLK_DEV_INITRD=y
CONFIG_RD_GZIP=y

# Filesystems for initrd
CONFIG_PROC_FS=y
CONFIG_SYSFS=y
CONFIG_TMPFS=y
CONFIG_DEVTMPFS=y
CONFIG_DEVTMPFS_MOUNT=y

# Debug
CONFIG_PRINTK=y
CONFIG_EARLY_PRINTK=y
CONFIG_DEBUG_LL=y
CONFIG_PRINTK_TIME=y
"""
    return minimal


if __name__ == "__main__":
    out_dir = Path(__file__).parent.parent / "configs"
    out_dir.mkdir(exist_ok=True)

    # Generate full defconfig
    with open(out_dir / "sun60iw2_defconfig", "w") as f:
        f.write(generate_defconfig(DEFCONFIG_SPEC))

    # Generate minimal defconfig
    with open(out_dir / "sun60iw2_minimal_defconfig", "w") as f:
        f.write(generate_minimal_defconfig())

    print(f"Defconfigs written to {out_dir}/")
    print(f"  {out_dir}/sun60iw2_defconfig          - Full featured")
    print(f"  {out_dir}/sun60iw2_minimal_defconfig  - UART bringup only")
