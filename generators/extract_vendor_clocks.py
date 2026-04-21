#!/usr/bin/env python3
"""
Extract clock definitions from vendor BSP CCU driver.

Parses Allwinner's vendor CCU driver and extracts clock/register
information into our JSON format for code generation.

Usage:
    python3 generators/extract_vendor_clocks.py \\
        --input /path/to/vendor/bsp/drivers/clk/sunxi-ng/ccu-sun60iw2.c \\
        --output generators/data/ccu-main.json
"""

import re
import json
import argparse
from pathlib import Path


class VendorClockExtractor:
    """Extract clock definitions from vendor CCU C code."""

    def __init__(self):
        self.clocks = []
        self.resets = []
        self.current_reg = None

    def extract_define_reg(self, line):
        """Extract register offset from #define like: #define SUN60IW2_PLL_DDR_CTRL_REG   0x0020"""
        match = re.match(r"#define\s+\w+_REG\s+(0x[0-9a-fA-F]+)", line)
        if match:
            return int(match.group(1), 0)
        return None

    def extract_ccu_nm(self, lines, start_idx):
        """Extract a ccu_nm (PLL) definition."""
        # Look for pattern: static struct ccu_nm name = { ... };
        block = ""
        brace_count = 0
        i = start_idx

        while i < len(lines):
            line = lines[i]
            block += line + "\n"
            brace_count += line.count("{") - line.count("}")

            if brace_count == 0 and "{" in block:
                break
            i += 1

        # Extract name
        name_match = re.search(r"struct ccu_nm\s+(\w+)\s*=", block)
        if not name_match:
            return None, i

        clk_name = name_match.group(1).replace("_clk", "").replace("_", "-")

        # Extract reg
        reg_match = re.search(r"\.reg\s*=\s*(0x[0-9a-fA-F]+)", block)
        reg = int(reg_match.group(1), 0) if reg_match else 0

        # Extract parent
        parent_match = re.search(r'CLK_HW_INIT\("[^"]+",\s*"([^"]+)"', block)
        parent = parent_match.group(1) if parent_match else "osc24M"

        return {
            "name": clk_name,
            "type": "nm",
            "reg": f"0x{reg:03x}",
            "parent": parent,
        }, i

    def extract_sunxi_ccu_m(self, line):
        """Extract a SUNXI_CCU_M (divider) definition."""
        # Pattern: static SUNXI_CCU_M(name, "name", "parent", reg, shift, width, flags);
        match = re.match(
            r'static SUNXI_CCU_M\((\w+),\s*"([^"]+)",\s*"([^"]+)",\s*(0x[0-9a-fA-F]+),\s*(\d+),\s*(\d+),\s*(\d+)\)',
            line,
        )
        if match:
            return {
                "name": match.group(2),
                "type": "divider",
                "parent": match.group(3),
                "reg": match.group(4),
                "shift": int(match.group(5)),
                "width": int(match.group(6)),
            }
        return None

    def extract_clk_fixed_factor(self, line):
        """Extract a CLK_FIXED_FACTOR definition."""
        # Pattern: static CLK_FIXED_FACTOR(name, "name", "parent", mult, div, flags);
        match = re.match(
            r'static CLK_FIXED_FACTOR\((\w+),\s*"([^"]+)",\s*"([^"]+)",\s*(\d+),\s*(\d+),\s*(\d+)\)',
            line,
        )
        if match:
            return {
                "name": match.group(2),
                "type": "fixed_factor",
                "parent": match.group(3),
                "mult": int(match.group(4)),
                "div": int(match.group(5)),
            }
        return None

    def extract_gate(self, line):
        """Extract a gate clock definition."""
        # Look for SUNXI_CCU_GATE macros
        match = re.match(
            r'static SUNXI_CCU_GATE\((\w+),\s*"([^"]+)",\s*"([^"]+)",\s*(0x[0-9a-fA-F]+),\s*(\d+),\s*(\d+)\)',
            line,
        )
        if match:
            return {
                "name": match.group(2),
                "type": "gate",
                "parent": match.group(3),
                "reg": match.group(4),
                "bit": int(match.group(5)),
            }
        return None

    def parse_file(self, filepath):
        """Parse vendor CCU driver file."""
        with open(filepath) as f:
            lines = f.readlines()

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Extract register defines
            reg = self.extract_define_reg(line)
            if reg:
                self.current_reg = reg

            # Extract PLL (ccu_nm)
            if "struct ccu_nm" in line and "static" in line:
                clk, i = self.extract_ccu_nm(lines, i)
                if clk:
                    self.clocks.append(clk)
                continue

            # Extract divider (SUNXI_CCU_M)
            if "SUNXI_CCU_M(" in line and "struct ccu_nm" not in line:
                clk = self.extract_sunxi_ccu_m(line)
                if clk:
                    self.clocks.append(clk)

            # Extract fixed factor
            if "CLK_FIXED_FACTOR(" in line:
                clk = self.extract_clk_fixed_factor(line)
                if clk:
                    self.clocks.append(clk)

            # Extract gate
            if "SUNXI_CCU_GATE(" in line:
                clk = self.extract_gate(line)
                if clk:
                    self.clocks.append(clk)

            i += 1

    def assign_ids(self):
        """Assign clock IDs based on dt-bindings header."""
        # Read the dt-bindings header to get IDs
        dt_bindings_path = (
            Path(__file__).parent.parent
            / "include"
            / "dt-bindings"
            / "clock"
            / "sun60i-a733-ccu.h"
        )

        if not dt_bindings_path.exists():
            print(f"Warning: {dt_bindings_path} not found, skipping ID assignment")
            return

        ids = {}
        with open(dt_bindings_path) as f:
            for line in f:
                match = re.match(r"#define CLK_(\w+)\s+(\d+)", line)
                if match:
                    name = match.group(1).lower().replace("_", "-")
                    ids[name] = match.group(1)

        # Assign IDs to clocks
        for clk in self.clocks:
            clk_name_normalized = clk["name"].lower().replace("_", "-")
            if clk_name_normalized in ids:
                clk["id"] = ids[clk_name_normalized]

    def to_json(self):
        """Export as JSON."""
        return {
            "_comment": "Auto-extracted from vendor BSP. Review and verify before use.",
            "clocks": self.clocks,
            "resets": self.resets,
        }


def main():
    parser = argparse.ArgumentParser(
        description="Extract clocks from vendor CCU driver"
    )
    parser.add_argument("--input", "-i", required=True, help="Vendor CCU driver C file")
    parser.add_argument(
        "--output", "-o", default="generators/data/ccu-main.json", help="Output JSON"
    )
    args = parser.parse_args()

    extractor = VendorClockExtractor()
    extractor.parse_file(args.input)
    extractor.assign_ids()

    output_path = Path(args.output)
    with open(output_path, "w") as f:
        json.dump(extractor.to_json(), f, indent=2)

    print(f"Extracted {len(extractor.clocks)} clocks")
    print(f"Output: {output_path}")

    # Print summary by type
    types = {}
    for clk in extractor.clocks:
        t = clk.get("type", "unknown")
        types[t] = types.get(t, 0) + 1

    print("\nBy type:")
    for t, count in sorted(types.items()):
        print(f"  {t}: {count}")


if __name__ == "__main__":
    main()
