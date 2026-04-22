#!/usr/bin/env python3
"""
Pinmux extraction plugin for Allwinner sun60iw2 vendor pinctrl driver.

Parses vendor BSP pinctrl-sun60iw2.c and extracts pinmux function tables
into structured JSON compatible with generate_pinmux.py.

Usage:
    from generators.plugins.pinmux_extractor import extract_pinmux, VENDOR_NAME_MAP
    data = extract_pinmux("/path/to/pinctrl-sun60iw2.c")
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Vendor -> mainline name mappings
VENDOR_NAME_MAP = {
    "twi": "i2c",
    "sdc": "mmc",
    "spif": "spi",
    "ndfc": "nand",
    "dpss": "lcd0",
    "sd": "mmc",  # sd0 -> mmc0, sd2 -> mmc2
}

# Functions to skip (vendor-internal / not upstreamable)
SKIP_FUNCTIONS = {"gpio_in", "gpio_out", "io_disabled", "test"}

# Regex patterns
RE_PIN_START = re.compile(r"SUNXI_PIN\(SUNXI_PINCTRL_PIN\(([A-Z]),\s*(\d+)\)")
RE_FUNCTION = re.compile(r'SUNXI_FUNCTION\(0x([0-9a-fA-F]+),\s*"([^"]+)"\)')
RE_IRQ_BANK = re.compile(
    r"SUNXI_FUNCTION_IRQ_BANK\(0x([0-9a-fA-F]+),\s*(\d+),\s*(\d+)\)"
)
RE_COMMENT = re.compile(r"/\*\s*(.*?)\s*\*/")


def _apply_name_map(name: str) -> str:
    """Translate vendor function names to mainline equivalents."""
    # Skip commented-out vendor names (e.g. //owa)
    if name.startswith("//"):
        return ""

    # Direct prefix replacement: twi0 -> i2c0, sdc2 -> mmc2, etc.
    for vendor, mainline in sorted(VENDOR_NAME_MAP.items(), key=lambda x: -len(x[0])):
        if name.startswith(vendor):
            # Check if next char is a digit (to avoid matching 'twi' inside 'twilight')
            remainder = name[len(vendor) :]
            if remainder == "" or remainder[0].isdigit():
                return mainline + remainder
    return name


def _parse_pin_block(block: str) -> Optional[Dict]:
    """Parse a single SUNXI_PIN(...) block into structured data."""
    lines = block.strip().split("\n")
    if not lines:
        return None

    # First line must contain SUNXI_PIN(SUNXI_PINCTRL_PIN(X, N),
    m = RE_PIN_START.search(lines[0])
    if not m:
        return None

    bank = "P" + m.group(1)
    pin_num = int(m.group(2))

    functions = []
    irq_bank = None
    irq_mux = None
    seen_mux = set()
    issues = []

    for line in lines[1:]:
        line = line.strip()
        if not line or line == "),":
            continue

        # Extract inline comment for signal name
        signal = ""
        cm = RE_COMMENT.search(line)
        if cm:
            signal = cm.group(1).strip()
            # Remove leading/trailing comment markers if nested
            signal = signal.lstrip("/").strip()

        # Check for IRQ function
        irq_m = RE_IRQ_BANK.search(line)
        if irq_m:
            irq_mux = int(irq_m.group(1), 16)
            irq_bank = int(irq_m.group(2))
            continue

        # Check for regular function
        fm = RE_FUNCTION.search(line)
        if fm:
            mux = int(fm.group(1), 16)
            raw_name = fm.group(2)

            if raw_name in SKIP_FUNCTIONS:
                continue

            # Skip commented-out duplicates like //owa
            if raw_name.startswith("//"):
                continue

            # Detect duplicate mux values on same pin
            if mux in seen_mux:
                # Check if it's truly a different function name
                existing = [f for f in functions if f["mux"] == mux]
                if existing and existing[0]["name"] != raw_name:
                    issues.append(
                        f"Duplicate mux 0x{mux:x} on {bank}{pin_num}: "
                        f"'{existing[0]['name']}' vs '{raw_name}'"
                    )
                continue
            seen_mux.add(mux)

            mapped_name = _apply_name_map(raw_name)
            if not mapped_name:
                continue

            func_entry = {
                "mux": mux,
                "name": mapped_name,
            }
            if signal and signal != mapped_name:
                func_entry["signal"] = signal

            functions.append(func_entry)

    result = {
        "bank": bank,
        "pin": pin_num,
        "functions": functions,
    }
    if irq_bank is not None:
        result["irq_bank"] = irq_bank
        result["irq_mux"] = irq_mux

    return result, issues


def extract_pinmux(vendor_file: Path) -> Dict:
    """
    Parse the vendor pinctrl driver and extract all pinmux tables.

    Returns a dict with:
        - soc: "sun60i-a733"
        - banks: dict of bank -> max_pin_number+1
        - irq: {bank_mux, bank_map}
        - name_map: vendor->mainline mappings used
        - pins: list of per-pin function descriptions
        - issues: list of extraction warnings
    """
    vendor_file = Path(vendor_file)
    if not vendor_file.exists():
        raise FileNotFoundError(f"Vendor file not found: {vendor_file}")

    content = vendor_file.read_text()

    # ------------------------------------------------------------------
    # Locate the non-FPGA pin array (the #else branch after FPGA defines)
    # ------------------------------------------------------------------
    # The vendor file has:
    #   #if IS_ENABLED(CONFIG_AW_FPGA_S4) || IS_ENABLED(CONFIG_AW_FPGA_V7)
    #       ... FPGA pins ...
    #   #else
    #       ... real SoC pins ...
    #   #endif
    # We want the real SoC pins (the #else section).
    # ------------------------------------------------------------------
    array_start = content.find("static const struct sunxi_desc_pin sun60iw2_pins[] = {")
    if array_start == -1:
        raise ValueError("Could not find sun60iw2_pins array")

    # Find the #else inside the array (first #else after array start)
    else_pos = content.find("#else", array_start)
    endif_pos = content.find("#endif", else_pos)

    if else_pos == -1 or endif_pos == -1:
        raise ValueError("Could not locate #else / #endif in pin array")

    soc_section = content[else_pos:endif_pos]

    # ------------------------------------------------------------------
    # Split the section into individual SUNXI_PIN(...) blocks
    # ------------------------------------------------------------------
    blocks = []
    i = 0
    while True:
        pin_start = soc_section.find("SUNXI_PIN(SUNXI_PINCTRL_PIN(", i)
        if pin_start == -1:
            break

        # Find the matching closing ')),' or just ')' that ends SUNXI_PIN
        # The block ends at the line that has '),'
        block_end = soc_section.find("SUNXI_PIN(", pin_start + 1)
        if block_end == -1:
            block_end = len(soc_section)

        block = soc_section[pin_start:block_end]
        blocks.append(block)
        i = block_end

    # ------------------------------------------------------------------
    # Parse each block
    # ------------------------------------------------------------------
    pins = []
    all_issues = []
    banks_max = {}

    for block in blocks:
        parsed = _parse_pin_block(block)
        if parsed is None:
            continue
        pin_data, issues = parsed
        pins.append(pin_data)
        all_issues.extend(issues)

        bank = pin_data["bank"]
        pin_num = pin_data["pin"]
        banks_max[bank] = max(banks_max.get(bank, 0), pin_num + 1)

    # Sort pins by bank then pin number
    BANK_ORDER = {chr(ord("A") + i): i for i in range(26)}
    pins.sort(key=lambda p: (BANK_ORDER[p["bank"][-1]], p["pin"]))

    # ------------------------------------------------------------------
    # Build bank sizes (include banks that have 0 pins if they're in range)
    # Based on vendor: banks B-K are present, A is not used.
    # ------------------------------------------------------------------
    all_banks = ["PA", "PB", "PC", "PD", "PE", "PF", "PG", "PH", "PI", "PJ", "PK"]
    banks = {}
    for b in all_banks:
        banks[b] = banks_max.get(b, 0)

    # ------------------------------------------------------------------
    # Extract IRQ bank map and mux values from the first pin of each bank
    # ------------------------------------------------------------------
    irq_bank_map = []
    irq_bank_muxes = []
    bank_irq_seen = set()

    for p in pins:
        bank = p["bank"]
        if bank in bank_irq_seen:
            continue
        if "irq_bank" in p:
            bank_irq_seen.add(bank)
            bidx = BANK_ORDER[bank[-1]]
            # Ensure arrays are long enough
            while len(irq_bank_map) <= bidx:
                irq_bank_map.append(0)
                irq_bank_muxes.append(0)
            irq_bank_map[bidx] = p["irq_bank"]
            irq_bank_muxes[bidx] = p.get("irq_mux", 0)

    # Pad arrays to 11 entries (PA-PK)
    while len(irq_bank_muxes) < 11:
        irq_bank_muxes.append(0)
    while len(irq_bank_map) < 11:
        irq_bank_map.append(0)

    return {
        "soc": "sun60i-a733",
        "banks": banks,
        "irq": {
            "bank_mux": irq_bank_muxes,
            "bank_map": irq_bank_map,
        },
        "name_map": dict(VENDOR_NAME_MAP),
        "pins": pins,
        "issues": all_issues,
    }


def validate_pinmux(data: Dict) -> List[str]:
    """
    Validate extracted pinmux data and return a list of error strings.

    Checks:
      - All pins have required fields
      - No duplicate (bank, pin) entries
      - Function mux values are within 0x0-0xf
      - Bank sizes are consistent with pin numbers
      - IRQ bank assignments are contiguous where expected
    """
    errors = []

    if "pins" not in data:
        errors.append("Missing 'pins' array")
        return errors

    banks = data.get("banks", {})
    seen_pins = set()
    BANK_ORDER = {chr(ord("A") + i): i for i in range(26)}

    for p in data["pins"]:
        bank = p.get("bank", "")
        pin = p.get("pin", -1)

        if not bank or pin < 0:
            errors.append(f"Invalid pin entry: {p}")
            continue

        key = (bank, pin)
        if key in seen_pins:
            errors.append(f"Duplicate pin entry: {bank}{pin}")
        seen_pins.add(key)

        max_pins = banks.get(bank, 0)
        if max_pins > 0 and pin >= max_pins:
            errors.append(f"Pin {bank}{pin} exceeds bank size ({max_pins})")

        funcs = p.get("functions", [])
        for func in funcs:
            mux = func.get("mux", -1)
            name = func.get("name", "")
            if not name:
                errors.append(f"Empty function name on {bank}{pin}")
            if not (0 <= mux <= 15):
                errors.append(f"Invalid mux 0x{mux:x} on {bank}{pin} for '{name}'")

    # Check that banks with pins have consistent IRQ assignments
    irq = data.get("irq", {})
    bank_mux = irq.get("bank_mux", [])
    bank_map = irq.get("bank_map", [])

    if len(bank_mux) < 11:
        errors.append(f"irq.bank_mux too short: {len(bank_mux)} (expected 11)")
    if len(bank_map) < 11:
        errors.append(f"irq.bank_map too short: {len(bank_map)} (expected 11)")

    return errors


def main():
    """CLI entry point: extract and save pinmux JSON."""
    import sys

    # Default vendor file location
    vendor_default = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "linux-orangepi"
        / "bsp"
        / "drivers"
        / "pinctrl"
        / "pinctrl-sun60iw2.c"
    )

    vendor_file = Path(sys.argv[1]) if len(sys.argv) > 1 else vendor_default
    output_file = Path(__file__).resolve().parent.parent / "data" / "pinmux-full.json"

    print(f"Extracting pinmux from: {vendor_file}")
    data = extract_pinmux(vendor_file)

    errors = validate_pinmux(data)
    if errors:
        print(f"Validation errors: {len(errors)}")
        for e in errors:
            print(f"  - {e}")

    if data.get("issues"):
        print(f"Extraction issues: {len(data['issues'])}")
        for issue in data["issues"]:
            print(f"  - {issue}")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Saved {len(data['pins'])} pins to {output_file}")
    print(f"Banks: {data['banks']}")
    print(f"Functions extracted: {sum(len(p['functions']) for p in data['pins'])}")


if __name__ == "__main__":
    main()
