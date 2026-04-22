#!/usr/bin/env python3
"""Pinmux validation plugin for sun60iw2-upstream pinctrl generator.

Validates pinctrl JSON data and compares generated drivers against
mainline sunxi patterns.
"""

import json
import re
from pathlib import Path
from typing import Any


def _parse_c_array(text: str, array_name: str) -> list[int] | None:
    """Extract a C array of integers by variable name."""
    pattern = re.compile(
        rf"static\s+const\s+(?:u8|unsigned\s+int)\s+{re.escape(array_name)}\s*\[\s*\w*\s*\]\s*=[\s\S]*?\{{(.*?)}};",
        re.DOTALL,
    )
    m = pattern.search(text)
    if not m:
        return None
    body = m.group(1)
    # Strip C comments
    body = re.sub(r"/\*.*?\*/", "", body, flags=re.DOTALL)
    body = re.sub(r"//.*", "", body)
    vals = []
    for token in body.replace("\n", " ").split(","):
        token = token.strip()
        if token:
            try:
                vals.append(int(token, 0))
            except ValueError:
                pass
    return vals


def _parse_c_array_mode(text: str) -> dict[str, Any] | None:
    """Parse a C-array mode pinctrl driver (sun60i_a733_pins[] style)."""
    data: dict[str, Any] = {}

    # Count SUNXI_PIN entries per bank
    bank_counts: dict[str, int] = {}
    bank_irq_map: dict[int, int] = {}  # physical bank index -> irq bank index
    bank_irq_mux: dict[int, int] = {}  # physical bank index -> irq mux value

    # Pattern: SUNXI_PIN(SUNXI_PINCTRL_PIN(X, N),
    pin_pattern = re.compile(
        r"SUNXI_PIN\(SUNXI_PINCTRL_PIN\(([A-Z]),\s*(\d+)\)", re.MULTILINE
    )
    for match in pin_pattern.finditer(text):
        bank = match.group(1)
        pin_num = int(match.group(2))
        bank_counts[bank] = max(bank_counts.get(bank, 0), pin_num + 1)

    # Pattern: SUNXI_FUNCTION_IRQ_BANK(mux, irq_bank, pin)
    irq_pattern = re.compile(
        r"SUNXI_FUNCTION_IRQ_BANK\(0x([0-9a-fA-F]+),\s*(\d+),\s*(\d+)\)", re.MULTILINE
    )
    for match in irq_pattern.finditer(text):
        mux = int(match.group(1), 16)
        irq_bank = int(match.group(2))
        pin_num = int(match.group(3))
        # Find which physical bank this pin belongs to
        for bank_letter, count in bank_counts.items():
            if pin_num < count:
                phys_idx = ord(bank_letter) - ord("A")
                bank_irq_map[phys_idx] = irq_bank
                bank_irq_mux[phys_idx] = mux
                break

    if not bank_counts:
        return None

    # Build 11-bank array
    max_bank_idx = max(ord(b) - ord("A") for b in bank_counts)
    banks = [0] * 11
    for bank_letter, count in bank_counts.items():
        idx = ord(bank_letter) - ord("A")
        banks[idx] = count

    data["banks"] = {f"P{chr(65 + i)}": v for i, v in enumerate(banks)}

    # Build irq_bank_map from observed irq_bank -> phys_bank mappings
    if bank_irq_map:
        # Invert: irq_bank -> phys_bank, then sort by irq_bank
        irq_to_phys = {irq: phys for phys, irq in bank_irq_map.items()}
        max_irq_bank = max(irq_to_phys.keys())
        irq_map = []
        for irq_b in range(max_irq_bank + 1):
            if irq_b in irq_to_phys:
                irq_map.append(irq_to_phys[irq_b])
        data["irq_bank_map"] = irq_map

        # Build irq_bank_muxes for all 11 banks
        muxes = [0] * 11
        for phys_idx, mux in bank_irq_mux.items():
            muxes[phys_idx] = mux
        data["irq_bank_muxes"] = muxes

    # Extract flags
    if "SUNXI_PINCTRL_NEW_REG_LAYOUT" in text:
        data.setdefault("flags", []).append("new_reg_layout")
    if "SUNXI_PINCTRL_ELEVEN_BANKS" in text:
        data.setdefault("flags", []).append("eleven_banks")

    return data


def parse_c_driver(text: str) -> dict[str, Any]:
    """Parse a generated/mainline pinctrl C driver into structured data."""
    data: dict[str, Any] = {}

    # --- Try C-array mode first ---
    bank_counts: dict[str, int] = {}
    bank_irq_map: dict[int, int] = {}  # phys_idx -> irq_bank
    bank_irq_mux: dict[int, int] = {}  # phys_idx -> mux

    current_bank = None

    for line in text.split("\n"):
        # Track current bank from SUNXI_PIN
        m = re.search(r"SUNXI_PIN\(SUNXI_PINCTRL_PIN\(([A-Z]),\s*(\d+)\)", line)
        if m:
            current_bank = m.group(1)
            pin_num = int(m.group(2))
            bank_counts[current_bank] = max(
                bank_counts.get(current_bank, 0), pin_num + 1
            )

        # Extract IRQ info (belongs to current bank)
        m = re.search(
            r"SUNXI_FUNCTION_IRQ_BANK\(0x([0-9a-fA-F]+),\s*(\d+),\s*(\d+)\)", line
        )
        if m and current_bank:
            mux = int(m.group(1), 16)
            irq_bank = int(m.group(2))
            phys_idx = ord(current_bank) - ord("A")
            bank_irq_map[phys_idx] = irq_bank
            bank_irq_mux[phys_idx] = mux

    if bank_counts:
        # Build 11-bank size array
        banks = [0] * 11
        for bank_letter, count in bank_counts.items():
            idx = ord(bank_letter) - ord("A")
            banks[idx] = count
        data["banks"] = {f"P{chr(65 + i)}": v for i, v in enumerate(banks)}

        # Build irq_bank_map: for each irq_bank, what phys_bank maps to it?
        if bank_irq_map:
            # Build reverse mapping
            irq_to_phys: dict[int, list[int]] = {}
            for phys, irq in bank_irq_map.items():
                irq_to_phys.setdefault(irq, []).append(phys)

            # The irq_map is indexed by irq_bank, value is phys_bank
            # Include ALL irq banks from 0 to max, with None for unused
            max_irq = max(bank_irq_map.values())
            irq_map = []
            for irq_b in range(max_irq + 1):
                if irq_b in irq_to_phys:
                    irq_map.append(min(irq_to_phys[irq_b]))
                else:
                    irq_map.append(0)  # Default to PA for unused irq banks
            data["irq_bank_map"] = irq_map

            # Build irq_bank_muxes: index = phys_bank, value = mux
            muxes = [0] * 11
            for phys_idx, mux in bank_irq_mux.items():
                muxes[phys_idx] = mux
            data["irq_bank_muxes"] = muxes

        data["_mode"] = "c_array"

        # Extract flags
        if "SUNXI_PINCTRL_NEW_REG_LAYOUT" in text:
            data.setdefault("flags", []).append("new_reg_layout")
        if "SUNXI_PINCTRL_ELEVEN_BANKS" in text:
            data.setdefault("flags", []).append("eleven_banks")

        return data

    # --- Fall back to DT mode (arrays like a733_nr_bank_pins) ---
    for prefix in ("a733", "a523"):
        banks = _parse_c_array(text, f"{prefix}_nr_bank_pins")
        if banks is not None:
            break
    else:
        banks = None

    if banks is not None:
        data["banks"] = {f"P{chr(65 + i)}": v for i, v in enumerate(banks)}

    for prefix in ("a733", "a523"):
        irq_map = _parse_c_array(text, f"{prefix}_irq_bank_map")
        if irq_map is not None:
            break
    else:
        irq_map = None

    if irq_map is not None:
        data["irq_bank_map"] = irq_map

    for prefix in ("a733", "a523"):
        irq_muxes = _parse_c_array(text, f"{prefix}_irq_bank_muxes")
        if irq_muxes is not None:
            break
    else:
        irq_muxes = None

    if irq_muxes is not None:
        data["irq_bank_muxes"] = irq_muxes

    data["_mode"] = "dt"

    # Extract flags
    if "SUNXI_PINCTRL_NEW_REG_LAYOUT" in text:
        data.setdefault("flags", []).append("new_reg_layout")
    if "SUNXI_PINCTRL_ELEVEN_BANKS" in text:
        data.setdefault("flags", []).append("eleven_banks")

    return data


def validate_pinctrl_structure(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Validate pinctrl data structure and return list of errors.

    Each error is a dict with keys: name, message, severity.
    """
    errors: list[dict[str, Any]] = []

    banks = data.get("banks", {})
    irq_map = data.get("irq_bank_map", data.get("irq", {}).get("bank_map", []))
    irq_muxes = data.get("irq_bank_muxes", data.get("irq", {}).get("bank_mux", []))
    pins = data.get("pins", [])
    flags = data.get("flags", [])

    expected_banks = [f"P{chr(65 + i)}" for i in range(11)]
    actual_banks = list(banks.keys())

    # 1. Bank assignments are sequential (PA..PK)
    if actual_banks != expected_banks:
        errors.append(
            {
                "name": "bank_sequence",
                "message": f"Banks not sequential PA..PK: got {actual_banks}",
                "severity": "error",
            }
        )

    # 2. Bank sizes are non-negative
    for bank, size in banks.items():
        if size < 0:
            errors.append(
                {
                    "name": "negative_bank_size",
                    "message": f"Bank {bank} has negative size {size}",
                    "severity": "error",
                }
            )

    # 3. IRQ bank map consistency
    # Count banks that have IRQ mux support (mux value > 0)
    if irq_muxes and len(irq_muxes) == 11:
        irq_banks = [expected_banks[i] for i in range(11) if irq_muxes[i] > 0]
    else:
        # Fallback: use non-empty banks if muxes unavailable
        irq_banks = [k for k in expected_banks if banks.get(k, 0) > 0]

    if irq_map:
        # irq_bank_map is indexed by irq_bank, so it may include unused banks
        if len(irq_map) < len(irq_banks):
            errors.append(
                {
                    "name": "irq_map_length",
                    "message": (
                        f"irq_bank_map length ({len(irq_map)}) < "
                        f"IRQ-enabled banks ({len(irq_banks)})"
                    ),
                    "severity": "error",
                }
            )
        # Values should be sequential starting from 0 (mainline pattern)
        expected_map = list(range(len(irq_map)))
        if list(irq_map) != expected_map:
            errors.append(
                {
                    "name": "irq_map_non_sequential",
                    "message": (
                        f"irq_bank_map values {list(irq_map)} are not "
                        f"sequential starting from 0"
                    ),
                    "severity": "warning",
                }
            )

    # 4. IRQ muxes length
    if irq_muxes:
        if len(irq_muxes) != 11:
            errors.append(
                {
                    "name": "irq_muxes_length",
                    "message": (
                        f"irq_bank_muxes length ({len(irq_muxes)}) != 11 "
                        f"(SUNXI_PINCTRL_MAX_BANKS)"
                    ),
                    "severity": "error",
                }
            )
        # First entry should be 0 (PA has no IRQ mux)
        if irq_muxes[0] != 0:
            errors.append(
                {
                    "name": "irq_mux_pa_nonzero",
                    "message": (
                        f"irq_bank_muxes[0] (PA) is {irq_muxes[0]}, expected 0"
                    ),
                    "severity": "error",
                }
            )

    # 5. Pin-level validation (if detailed pinmux data present)
    if pins:
        pin_ids = set()
        for pin in pins:
            bank = pin.get("bank", "")
            pin_num = pin.get("pin", -1)
            pin_id = (bank, pin_num)

            if pin_id in pin_ids:
                errors.append(
                    {
                        "name": "duplicate_pin",
                        "message": f"Duplicate pin definition: {bank}{pin_num}",
                        "severity": "error",
                    }
                )
            pin_ids.add(pin_id)

            if bank not in banks:
                errors.append(
                    {
                        "name": "unknown_bank",
                        "message": (
                            f"Pin {bank}{pin_num} references unknown bank {bank}"
                        ),
                        "severity": "error",
                    }
                )
                continue

            max_pin = banks[bank]
            if max_pin > 0 and pin_num >= max_pin:
                errors.append(
                    {
                        "name": "pin_out_of_range",
                        "message": (f"Pin {bank}{pin_num} exceeds bank size {max_pin}"),
                        "severity": "error",
                    }
                )

            functions = pin.get("functions", [])
            func_names = {f.get("name", "") for f in functions}

            # Every pin should have at least gpio_in/gpio_out
            has_gpio = "gpio_in" in func_names or "gpio_out" in func_names
            if not has_gpio:
                errors.append(
                    {
                        "name": "missing_gpio",
                        "message": (f"Pin {bank}{pin_num} missing gpio_in/gpio_out"),
                        "severity": "warning",
                    }
                )

            # Function mux values are unique per pin
            mux_vals = [f.get("mux") for f in functions if "mux" in f]
            if len(mux_vals) != len(set(mux_vals)):
                dups = [m for m in mux_vals if mux_vals.count(m) > 1]
                errors.append(
                    {
                        "name": "mux_collision",
                        "message": (
                            f"Pin {bank}{pin_num} has duplicate mux values: {dups}"
                        ),
                        "severity": "error",
                    }
                )

        # Check for missing pins or holes
        for bank, size in banks.items():
            if size == 0:
                continue
            present = {p["pin"] for p in pins if p.get("bank") == bank}
            expected = set(range(size))
            missing = expected - present
            if missing:
                errors.append(
                    {
                        "name": "missing_pins",
                        "message": (f"Bank {bank} missing pins: {sorted(missing)}"),
                        "severity": "error",
                    }
                )

    # 6. Flags sanity
    if "eleven_banks" not in flags and len(banks) != 11:
        errors.append(
            {
                "name": "missing_eleven_banks_flag",
                "message": (f"11 banks present but 'eleven_banks' flag missing"),
                "severity": "warning",
            }
        )

    return errors


def compare_to_mainline(
    generated: dict[str, Any], template: dict[str, Any]
) -> list[dict[str, Any]]:
    """Compare generated pinctrl data against mainline template.

    Returns list of deviation dicts with keys: name, message, severity.
    """
    deviations: list[dict[str, Any]] = []

    # Detect C-array mode vs DT mode
    gen_c_array = generated.get("_mode") == "c_array"
    tmpl_dt = template.get("_mode") == "dt"

    # Skip bank-by-bank comparison when modes differ (C-array vs DT)
    if gen_c_array and tmpl_dt:
        # Only compare flags
        gen_flags = set(generated.get("flags", []))
        tmpl_flags = set(template.get("flags", []))
        missing_flags = tmpl_flags - gen_flags
        if missing_flags:
            deviations.append(
                {
                    "name": "missing_flags",
                    "message": (
                        f"Generated missing mainline flags: {sorted(missing_flags)}"
                    ),
                    "severity": "warning",
                }
            )
        return deviations

    gen_banks = generated.get("banks", {})
    tmpl_banks = template.get("banks", {})

    all_banks = set(gen_banks) | set(tmpl_banks)
    for bank in sorted(all_banks):
        g = gen_banks.get(bank)
        t = tmpl_banks.get(bank)
        if g is None and t is not None:
            deviations.append(
                {
                    "name": f"bank_missing_{bank}",
                    "message": (
                        f"Generated missing bank {bank} (template has size {t})"
                    ),
                    "severity": "error",
                }
            )
        elif t is None and g is not None:
            deviations.append(
                {
                    "name": f"bank_extra_{bank}",
                    "message": (
                        f"Generated has extra bank {bank} (size {g}) not in template"
                    ),
                    "severity": "warning",
                }
            )
        elif g != t:
            deviations.append(
                {
                    "name": f"bank_size_mismatch_{bank}",
                    "message": (
                        f"Bank {bank} size mismatch: generated={g}, template={t}"
                    ),
                    "severity": "warning",
                }
            )

    # IRQ bank map
    gen_map = generated.get("irq_bank_map", [])
    tmpl_map = template.get("irq_bank_map", [])
    if gen_map != tmpl_map:
        deviations.append(
            {
                "name": "irq_bank_map_mismatch",
                "message": (
                    f"IRQ bank map mismatch: generated={gen_map}, template={tmpl_map}"
                ),
                "severity": "error",
            }
        )

    # IRQ muxes
    gen_muxes = generated.get("irq_bank_muxes", [])
    tmpl_muxes = template.get("irq_bank_muxes", [])
    if gen_muxes != tmpl_muxes:
        deviations.append(
            {
                "name": "irq_bank_muxes_mismatch",
                "message": (
                    f"IRQ bank muxes mismatch: generated={gen_muxes}, "
                    f"template={tmpl_muxes}"
                ),
                "severity": "error",
            }
        )

    # Flags
    gen_flags = set(generated.get("flags", []))
    tmpl_flags = set(template.get("flags", []))
    missing_flags = tmpl_flags - gen_flags
    if missing_flags:
        deviations.append(
            {
                "name": "missing_flags",
                "message": (
                    f"Generated missing mainline flags: {sorted(missing_flags)}"
                ),
                "severity": "warning",
            }
        )

    return deviations


def generate_report(data: dict[str, Any]) -> str:
    """Generate a human-readable validation report for the given data."""
    lines = []
    lines.append("=" * 60)
    lines.append("Pinctrl Validation Report")
    lines.append("=" * 60)

    struct_errors = validate_pinctrl_structure(data)
    lines.append(f"\nStructural Checks: {'PASS' if not struct_errors else 'FAIL'}")
    lines.append("-" * 40)
    if struct_errors:
        for err in struct_errors:
            lines.append(
                f"  [{err['severity'].upper()}] {err['name']}: {err['message']}"
            )
    else:
        lines.append("  No structural errors found.")

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


def validate_all(
    json_path: Path,
    generated_path: Path,
    template_path: Path,
) -> dict[str, Any]:
    """Run full validation pipeline and return structured results."""
    data = json.loads(json_path.read_text())
    generated = parse_c_driver(generated_path.read_text())
    template = parse_c_driver(template_path.read_text())

    struct_errors = validate_pinctrl_structure(data)
    mainline_devs = compare_to_mainline(generated, template)

    report = generate_report(data)
    if mainline_devs:
        report += "\nMainline Comparison Deviations:\n"
        report += "-" * 40 + "\n"
        for d in mainline_devs:
            report += f"  [{d['severity'].upper()}] {d['name']}: {d['message']}\n"

    return {
        "structural_errors": struct_errors,
        "mainline_deviations": mainline_devs,
        "report": report,
        "pass": not any(e["severity"] == "error" for e in struct_errors)
        and not any(d["severity"] == "error" for d in mainline_devs),
    }
