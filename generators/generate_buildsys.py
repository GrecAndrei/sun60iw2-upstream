#!/usr/bin/env python3
"""
Build system generator for sun60i-a733 drivers.

Generates Kconfig entries and Makefile rules for:
- drivers/clk/sunxi-ng/Makefile + Kconfig
- drivers/pinctrl/sunxi/Makefile + Kconfig

Usage:
    python3 generators/generate_buildsys.py
    # Outputs patches to apply to linux tree
"""

import sys
from pathlib import Path

BUILD_DATA = {
    "clk": {
        "driver_name": "sun60i-a733-ccu",
        "config_name": "SUN60I_A733_CCU",
        "source_files": ["ccu-sun60i-a733.o"],
        "dependencies": ["ARCH_SUNXI", "CLK_SUNXI"],
        "description": "Allwinner A733 Clock Controller Unit",
        "default": "y if ARCH_SUNXI",
    },
    "pinctrl": {
        "driver_name": "sun60i-a733-pinctrl",
        "config_name": "PINCTRL_SUN60I_A733",
        "source_files": ["pinctrl-sun60i-a733.o"],
        "dependencies": ["ARCH_SUNXI", "PINCTRL_SUNXI"],
        "description": "Allwinner A733 Pin Controller",
        "default": "y if ARCH_SUNXI",
    },
}


def generate_kconfig_fragment(subsystem, data):
    """Generate Kconfig fragment for a subsystem."""
    deps = " && ".join(f"CONFIG_{d}" for d in data["dependencies"])

    return f'''# {data["description"]}
config {data["config_name"]}
	tristate "{data["description"]}"
	depends on {deps}
	default {data["default"]}
	help
	  Support for the {data["description"]} found on Allwinner A733 SoC.
'''


def generate_makefile_fragment(subsystem, data):
    """Generate Makefile fragment for a subsystem."""
    objs = " ".join(data["source_files"])
    return f"""# {data["description"]}
obj-$(CONFIG_{data["config_name"]}) += {objs}
"""


def generate_full_patch():
    """Generate a complete patch with all build system changes."""

    patch = """# Build System Integration Patches
#
# Apply these to the mainline Linux tree:
#
# --- drivers/clk/sunxi-ng/Kconfig ---
# Add at the end of the file:

"""

    for subsystem, data in BUILD_DATA.items():
        patch += f"""
# --- drivers/{subsystem}/sunxi-ng/Kconfig (for clk) or drivers/{subsystem}/sunxi/Kconfig ---
{generate_kconfig_fragment(subsystem, data)}
# --- drivers/{subsystem}/sunxi-ng/Makefile (for clk) or drivers/{subsystem}/sunxi/Makefile ---
{generate_makefile_fragment(subsystem, data)}
"""

    # Add arch/arm64 dts Makefile fragment
    patch += """
# --- arch/arm64/boot/dts/allwinner/Makefile ---
# Add to existing dtb-$(CONFIG_ARCH_SUNXI) list:

dtb-$(CONFIG_ARCH_SUNXI) += sun60i-a733-orangepi-4-pro.dtb
"""

    return patch


def generate_standalone_kconfig():
    """Generate a standalone Kconfig file for the sun60iw2 family."""

    kconfig = """# sun60iw2 SoC family configuration
# Include this in drivers/soc/sunxi/Kconfig or create arch/arm64/Kconfig.platforms entry

menuconfig ARCH_SUN60IW2
	bool "Allwinner sun60iw2 (A733) SoC Family"
	depends on ARCH_SUNXI
	default n
	help
	  Support for Allwinner sun60iw2 SoC family (A733 and variants).
	  This includes the Orange Pi 4 Pro and other boards based on
	  the A733 SoC.

if ARCH_SUN60IW2

config SUN60I_A733_CCU
	bool "Allwinner A733 Clock Controller"
	default y
	help
	  Support for the Clock Controller Unit (CCU) on Allwinner A733.

config SUN60I_A733_PINCTRL
	bool "Allwinner A733 Pin Controller"
	default y
	help
	  Support for the pin controller on Allwinner A733.

config SUN60I_A733_WATCHDOG
	bool "Allwinner A733 Watchdog"
	default y
	help
	  Support for the watchdog timer on Allwinner A733.

endif # ARCH_SUN60IW2
"""
    return kconfig


if __name__ == "__main__":
    out_dir = Path(__file__).parent / "output"
    out_dir.mkdir(exist_ok=True)

    # Generate patch instructions
    with open(out_dir / "BUILD_PATCH.txt", "w") as f:
        f.write(generate_full_patch())

    # Generate standalone Kconfig
    with open(out_dir / "Kconfig.sun60iw2", "w") as f:
        f.write(generate_standalone_kconfig())

    print(f"Build system patches written to {out_dir}/")
    print("\nFiles generated:")
    print(f"  {out_dir}/BUILD_PATCH.txt     - Patch instructions for Linux tree")
    print(f"  {out_dir}/Kconfig.sun60iw2   - Standalone Kconfig for sun60iw2 family")
