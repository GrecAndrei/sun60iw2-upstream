#!/usr/bin/env python3
"""
Prototype pinmux function table generator for Allwinner sunxi SoCs.

Reads structured JSON pinmux data and emits:
    --mode=c      Explicit C arrays (SUNXI_PIN style)
    --mode=dt     Device-Tree pinctrl nodes
    --mode=report Markdown table for review

Usage:
    python3 generators/generate_pinmux.py --mode=c   generators/data/pinmux-example.json
    python3 generators/generate_pinmux.py --mode=dt  generators/data/pinmux-example.json
    python3 generators/generate_pinmux.py --mode=report generators/data/pinmux-example.json
"""

import argparse
import json
import sys
from pathlib import Path
from collections import defaultdict


# Bank letter → index (A=0, B=1, ...)
BANK_ORDER = {chr(ord("A") + i): i for i in range(26)}


def load_json(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def normalize(data: dict) -> dict:
    """Apply name_map, sort pins, validate basic structure."""
    name_map = data.get("name_map", {})
    banks = data["banks"]
    pins = data.get("pins", [])

    # Validate and map names
    for p in pins:
        for func in p.get("functions", []):
            raw_name = func["name"]
            # Apply prefix replacements (e.g. twi0 -> i2c0, sdc2 -> mmc2)
            for vendor, mainline in name_map.items():
                if raw_name.startswith(vendor):
                    func["name"] = mainline + raw_name[len(vendor) :]
                    break

    # Sort by bank index then pin number
    pins.sort(key=lambda p: (BANK_ORDER[p["bank"][-1]], p["pin"]))
    data["pins"] = pins
    return data


def bank_index(bank_str: str) -> int:
    return BANK_ORDER[bank_str[-1]]


def emit_c(data: dict) -> str:
    """Generate explicit SUNXI_PIN C array (sun50i-h616 style)."""
    soc = data["soc"].replace("-", "_")
    pins = data["pins"]
    banks = data["banks"]
    irq = data["irq"]
    irq_muxes = irq["bank_mux"]

    # Build a fast lookup: (bank, pin) -> functions list
    pin_funcs = {}
    for p in pins:
        pin_funcs[(p["bank"], p["pin"])] = p.get("functions", [])

    # Pre-compute sequential IRQ bank indices (only for banks with irq_mux > 0)
    irq_bank_index = {}
    seq = 0
    for bank_name in banks:
        bidx = bank_index(bank_name)
        if bidx < len(irq_muxes) and irq_muxes[bidx] > 0:
            irq_bank_index[bank_name] = seq
            seq += 1

    lines = []
    lines.append(f"static const struct sunxi_desc_pin {soc}_pins[] = {{")

    prev_bank_idx = -1
    for bank_name, num_pins in banks.items():
        bidx = bank_index(bank_name)
        if num_pins == 0:
            continue
        if prev_bank_idx != -1 and bidx != prev_bank_idx + 1:
            lines.append("\t/* Hole */")
        prev_bank_idx = bidx

        lines.append(f"\t/* bank {bank_name} */")

        irq_mux = irq_muxes[bidx] if bidx < len(irq_muxes) else 0
        irq_bank = irq_bank_index.get(bank_name)

        for pin_num in range(num_pins):
            key = (bank_name, pin_num)
            funcs = pin_funcs.get(key, [])

            lines.append(f"\tSUNXI_PIN(SUNXI_PINCTRL_PIN({bank_name[-1]}, {pin_num}),")
            lines.append('\t\t  SUNXI_FUNCTION(0x0, "gpio_in"),')
            lines.append('\t\t  SUNXI_FUNCTION(0x1, "gpio_out"),')

            for func in funcs:
                mux = func["mux"]
                name = func["name"]
                signal = func.get("signal", "")
                comment = f"\t\t/* {signal} */" if signal else ""
                lines.append(f'\t\t  SUNXI_FUNCTION(0x{mux:x}, "{name}"),{comment}')

            if irq_mux and irq_bank is not None:
                lines.append(
                    f"\t\t  SUNXI_FUNCTION_IRQ_BANK(0x{irq_mux:x}, {irq_bank}, {pin_num})),"
                    f"\t/* {bank_name}_EINT{pin_num} */"
                )
            else:
                lines.append("\t\t),")

    lines.append("};")
    return "\n".join(lines)


def emit_dt(data: dict) -> str:
    """Generate Device-Tree pinctrl nodes for sunxi_pinctrl_dt_table_init()."""
    pins = data["pins"]

    # Group by (function_name, mux_value)
    groups = defaultdict(list)
    for p in pins:
        for func in p.get("functions", []):
            key = (func["name"], func["mux"])
            groups[key].append(p)

    lines = []
    lines.append("/* Auto-generated pinmux DT nodes */")
    lines.append("")

    for (func_name, mux), pin_list in sorted(groups.items()):
        # Sort pins by bank then number
        pin_list.sort(key=lambda p: (bank_index(p["bank"]), p["pin"]))
        pin_names = [f'"{p["bank"]}{p["pin"]}"' for p in pin_list]
        node_name = f"{func_name}_pins: {func_name.replace('_', '-')}-pins"
        lines.append(f"\t{node_name} {{")
        lines.append(f"\t\tpins = {', '.join(pin_names)};")
        lines.append(f'\t\tfunction = "{func_name}";')
        lines.append(f"\t\tallwinner,pinmux = <{mux}>;")
        lines.append("\t};")
        lines.append("")

    return "\n".join(lines)


def emit_report(data: dict) -> str:
    """Generate a markdown table of pin vs function mux values."""
    pins = data["pins"]

    # Collect all unique function names
    func_names = set()
    for p in pins:
        for func in p.get("functions", []):
            func_names.add(func["name"])
    func_names = sorted(func_names)

    header = ["Pin", "gpio_in", "gpio_out"] + func_names
    rows = []
    rows.append("| " + " | ".join(header) + " |")
    rows.append("|" + "|".join(["---"] * len(header)) + "|")

    for p in pins:
        pin_id = f"{p['bank']}{p['pin']}"
        func_map = {f["name"]: f"0x{f['mux']:x}" for f in p.get("functions", [])}
        cells = [pin_id, "0x0", "0x1"] + [func_map.get(fn, "—") for fn in func_names]
        rows.append("| " + " | ".join(cells) + " |")

    return "\n".join(rows)


MODES = {
    "c": emit_c,
    "dt": emit_dt,
    "report": emit_report,
}


def main():
    parser = argparse.ArgumentParser(description="Generate pinmux tables from JSON")
    parser.add_argument("json", type=Path, help="Input JSON file")
    parser.add_argument("--mode", choices=MODES.keys(), default="c", help="Output mode")
    args = parser.parse_args()

    if not args.json.exists():
        print(f"Error: {args.json} not found", file=sys.stderr)
        sys.exit(1)

    data = load_json(args.json)
    data = normalize(data)
    print(MODES[args.mode](data))


if __name__ == "__main__":
    main()
