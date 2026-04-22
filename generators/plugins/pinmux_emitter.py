#!/usr/bin/env python3
"""
Pinmux emitter plugin for the sun60i-a733 pinctrl generator.

Integrates with generators/generate_pinctrl.py to emit mainline-style
pinmux tables from structured JSON data.

Exports:
    emit_pinmux_c(data) -> str
    emit_pinmux_dt(data) -> str
    validate_emission(data) -> list
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA = ROOT / "data" / "pinmux-full.json"
FALLBACK_DATA = ROOT / "data" / "pinmux-example.json"

BANK_ORDER = {chr(ord("A") + i): i for i in range(26)}


def _bank_index(bank_str: str) -> int:
    return BANK_ORDER[bank_str[-1]]


def load_pinmux_data() -> dict:
    """Load pinmux JSON, falling back to example data if full is absent."""
    for path in (DEFAULT_DATA, FALLBACK_DATA):
        if path.exists():
            with open(path) as f:
                return json.load(f)
    raise FileNotFoundError(f"Neither {DEFAULT_DATA} nor {FALLBACK_DATA} found")


def normalize(data: dict) -> dict:
    """Apply name_map, sort pins, validate basic structure."""
    name_map = data.get("name_map", {})
    banks = data.get("banks", {})
    pins = data.get("pins", [])

    for p in pins:
        for func in p.get("functions", []):
            raw_name = func["name"]
            for vendor, mainline in name_map.items():
                if raw_name.startswith(vendor):
                    func["name"] = mainline + raw_name[len(vendor) :]
                    break

    pins.sort(key=lambda p: (_bank_index(p["bank"]), p["pin"]))
    data["pins"] = pins
    return data


def _build_physical_to_irq_bank(irq_bank_map: list) -> dict:
    """Map physical bank index -> IRQ bank index from irq_bank_map."""
    mapping = {}
    for irq_idx, phys_idx in enumerate(irq_bank_map):
        mapping[phys_idx] = irq_idx
    return mapping


def emit_pinmux_c(data: dict) -> str:
    """
    Emit explicit SUNXI_PIN C array in mainline sunxi style
    (e.g. pinctrl-sun50i-h616.c).
    """
    soc = data.get("soc", "sun60i-a733").replace("-", "_")
    banks = data.get("banks", {})
    pins = data.get("pins", [])
    irq = data.get("irq", {})
    irq_bank_map = irq.get("bank_map", [])
    irq_muxes = irq.get("bank_mux", [])

    # Fast lookup: (bank, pin) -> functions list
    pin_funcs = {}
    for p in pins:
        pin_funcs[(p["bank"], p["pin"])] = p.get("functions", [])

    phys_to_irq = _build_physical_to_irq_bank(irq_bank_map)

    lines = []
    lines.append(f"static const struct sunxi_desc_pin {soc}_pins[] = {{")

    prev_bank_idx = -1
    for bank_name, num_pins in banks.items():
        bidx = _bank_index(bank_name)
        if num_pins == 0:
            continue
        if prev_bank_idx != -1 and bidx != prev_bank_idx + 1:
            lines.append("\t/* Hole */")
        prev_bank_idx = bidx

        lines.append(f"\t/* Bank {bank_name} */")

        irq_mux = irq_muxes[bidx] if bidx < len(irq_muxes) else 0
        irq_bank = phys_to_irq.get(bidx)

        for pin_num in range(num_pins):
            key = (bank_name, pin_num)
            funcs = pin_funcs.get(key, [])
            # Sort functions by mux value for deterministic output
            funcs = sorted(funcs, key=lambda f: f["mux"])

            bank_letter = bank_name[-1]

            entries = []
            entries.append('\t\t  SUNXI_FUNCTION(0x0, "gpio_in")')
            entries.append('\t\t  SUNXI_FUNCTION(0x1, "gpio_out")')

            for func in funcs:
                mux = func["mux"]
                name = func["name"]
                signal = func.get("signal", "")
                comment = f"\t\t/* {signal} */" if signal else ""
                entries.append(f'\t\t  SUNXI_FUNCTION(0x{mux:x}, "{name}"){comment}')

            if irq_mux and irq_bank is not None:
                entries.append(
                    f"\t\t  SUNXI_FUNCTION_IRQ_BANK(0x{irq_mux:x}, {irq_bank}, {pin_num}))"
                    f"\t/* {bank_name}_EINT{pin_num} */"
                )

            lines.append(f"\tSUNXI_PIN(SUNXI_PINCTRL_PIN({bank_letter}, {pin_num}),")
            for i, entry in enumerate(entries):
                if i < len(entries) - 1:
                    lines.append(f"{entry},")
                else:
                    # IRQ entry closes SUNXI_PIN itself, so add outer-array comma
                    if irq_mux and irq_bank is not None:
                        lines.append(f"{entry},")
                    else:
                        lines.append(entry)
            if not (irq_mux and irq_bank is not None):
                lines.append("\t\t),")

    lines.append("};")
    return "\n".join(lines)


def emit_pinmux_dt(data: dict) -> str:
    """
    Emit Device-Tree pinctrl nodes compatible with
    sunxi_pinctrl_dt_table_init().
    """
    pins = data.get("pins", [])

    # Group by (function_name, mux_value)
    groups = defaultdict(list)
    for p in pins:
        for func in p.get("functions", []):
            key = (func["name"], func["mux"])
            groups[key].append(p)

    lines = []
    lines.append("/* Auto-generated pinmux DT nodes */")
    lines.append("")

    # Track how many times each function appears so labels stay unique
    func_counts = defaultdict(int)
    for func_name, _ in groups.keys():
        func_counts[func_name] += 1

    func_seen = defaultdict(int)
    for (func_name, mux), pin_list in sorted(groups.items()):
        pin_list.sort(key=lambda p: (_bank_index(p["bank"]), p["pin"]))
        pin_names = [f'"{p["bank"]}{p["pin"]}"' for p in pin_list]

        if func_counts[func_name] > 1:
            func_seen[func_name] += 1
            suffix = f"_mux{mux}"
            node_name = (
                f"{func_name}{suffix}_pins: {func_name.replace('_', '-')}{suffix}-pins"
            )
        else:
            node_name = f"{func_name}_pins: {func_name.replace('_', '-')}-pins"

        lines.append(f"\t{node_name} {{")
        lines.append(f"\t\tpins = {', '.join(pin_names)};")
        lines.append(f'\t\tfunction = "{func_name}";')
        lines.append(f"\t\tallwinner,pinmux = <{mux}>;")
        lines.append("\t};")
        lines.append("")

    return "\n".join(lines)


def validate_emission(data: dict) -> list:
    """
    Validate pinmux data and return a list of error strings.
    An empty list means the data is clean.
    """
    errors = []
    banks = data.get("banks", {})
    pins = data.get("pins", [])
    irq = data.get("irq", {})
    irq_muxes = irq.get("bank_mux", [])

    # Check required top-level keys
    for key in ("soc", "banks", "irq", "pins"):
        if key not in data:
            errors.append(f"Missing required top-level key: '{key}'")

    if not banks:
        errors.append("No banks defined")
        return errors

    # Build a set of valid (bank, pin) combinations
    seen_pins = set()
    for p in pins:
        bank = p.get("bank", "")
        pin_num = p.get("pin", -1)

        if bank not in banks:
            errors.append(f"Pin references unknown bank: {bank}")
            continue

        max_pins = banks[bank]
        if not (0 <= pin_num < max_pins):
            errors.append(
                f"Pin {bank}{pin_num} out of range (bank has {max_pins} pins)"
            )

        key = (bank, pin_num)
        if key in seen_pins:
            errors.append(f"Duplicate pin definition: {bank}{pin_num}")
        seen_pins.add(key)

        # Check for duplicate mux values on the same pin
        muxes = []
        for func in p.get("functions", []):
            mux = func.get("mux")
            if mux in muxes:
                errors.append(f"Duplicate mux value 0x{mux:x} on pin {bank}{pin_num}")
            muxes.append(mux)

            if not isinstance(mux, int) or not (0 <= mux <= 0xF):
                errors.append(
                    f"Invalid mux value {mux} on pin {bank}{pin_num} (must be 0-0xF)"
                )

    # Validate IRQ data consistency
    if irq_muxes:
        if len(irq_muxes) != len(banks):
            errors.append(
                f"irq.bank_mux length ({len(irq_muxes)}) does not match "
                f"number of banks ({len(banks)})"
            )

    return errors


# --- Integration helpers for generate_pinctrl.py ---


def emit_pinmux_section(data: dict, mode: str = "dt") -> str:
    """
    Convenience wrapper used by generate_pinctrl.py.
    mode: "c" | "dt" | "report"
    """
    data = normalize(data)
    errors = validate_emission(data)
    if errors:
        raise ValueError("Pinmux validation failed:\n" + "\n".join(errors))

    if mode == "c":
        return emit_pinmux_c(data)
    elif mode == "dt":
        return emit_pinmux_dt(data)
    else:
        raise ValueError(f"Unknown pinmux mode: {mode}")


def get_pinmux_data() -> dict:
    """Load and normalize pinmux data for the current SoC."""
    data = load_pinmux_data()
    return normalize(data)


if __name__ == "__main__":
    # Allow standalone testing during development
    import argparse

    parser = argparse.ArgumentParser(description="Pinmux emitter plugin")
    parser.add_argument("--mode", choices=["c", "dt"], default="c")
    args = parser.parse_args()

    data = get_pinmux_data()
    errors = validate_emission(data)
    if errors:
        print("Validation errors:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)

    if args.mode == "c":
        print(emit_pinmux_c(data))
    else:
        print(emit_pinmux_dt(data))
