#!/usr/bin/env python3
"""
generate_dma.py – Generate DMA driver patch data for sun6i-dma.c

Reads generators/data/dma.json and emits the C struct / OF match entry
that needs to be added to drivers/dma/sun6i-dma.c.

Usage:
    python3 generators/generate_dma.py > generators/output/dma_patch.c
"""

import json
import sys
from pathlib import Path

DATA_PATH = Path(__file__).with_name("data") / "dma.json"


def emit_burst_lengths(lengths: list) -> str:
    parts = [f"BIT({v})" for v in lengths]
    return " | ".join(parts)


def emit_addr_widths(widths: list) -> str:
    mapping = {
        1: "DMA_SLAVE_BUSWIDTH_1_BYTE",
        2: "DMA_SLAVE_BUSWIDTH_2_BYTES",
        4: "DMA_SLAVE_BUSWIDTH_4_BYTES",
        8: "DMA_SLAVE_BUSWIDTH_8_BYTES",
    }
    parts = [f"BIT({mapping[w]})" for w in widths]
    return " | ".join(parts)


def generate_driver_patch(data: dict) -> str:
    cfg = data["driver_config"]
    soc = data["soc"]
    compatible = data["compatible"]

    lines = [
        f"/*\n * {soc.upper()} binding uses the number of dma channels from the\n * device tree node.\n */",
        f"static struct sun6i_dma_config {soc.replace('-', '_')}_dma_cfg = {{",
        f"\t.clock_autogate_enable = {cfg['clock_autogate_enable']},",
        f"\t.set_burst_length = {cfg['set_burst_length']},",
        f"\t.set_drq = {cfg['set_drq']},",
        f"\t.set_mode = {cfg['set_mode']},",
        f"\t.src_burst_lengths = {emit_burst_lengths(cfg['src_burst_lengths'])},",
        f"\t.dst_burst_lengths = {emit_burst_lengths(cfg['dst_burst_lengths'])},",
        f"\t.src_addr_widths   = {emit_addr_widths(cfg['src_addr_widths'])},",
        f"\t.dst_addr_widths   = {emit_addr_widths(cfg['dst_addr_widths'])},",
    ]
    if cfg.get("has_high_addr"):
        lines.append("\t.has_high_addr = true,")
    if cfg.get("has_mbus_clk"):
        lines.append("\t.has_mbus_clk = true,")
    lines.append("};")
    lines.append("")
    lines.append("/* Add to sun6i_dma_match[]:")
    lines.append(
        f'\t{{ .compatible = "{compatible}", .data = &{soc.replace("-", "_")}_dma_cfg }},'
    )
    lines.append("*/")
    return "\n".join(lines)


def generate_dt_snippet(data: dict) -> str:
    dt = data["dt"]
    compatible = data["compatible"]
    fallback = data.get("fallback", "")
    compat_line = f'\t\t\tcompatible = "{compatible}"'
    if fallback:
        compat_line += f',\n\t\t\t\t     "{fallback}"'
    compat_line += ";"

    clocks = ", ".join(f"<{c}>" for c in dt["clocks"])
    clock_names = '", "'.join(dt["clock_names"])
    reset = f"<{dt['reset']}>"

    lines = [
        "\t\tdma: dma-controller@4601000 {",
        compat_line,
        f"\t\t\treg = <{dt['reg']} {dt['size']}>;",
        f"\t\t\tinterrupts = {dt['interrupts']};",
        f"\t\t\tclocks = {clocks};",
        f'\t\t\tclock-names = "{clock_names}";',
        f"\t\t\tdma-channels = <{dt['dma_channels']}>;",
        f"\t\t\tdma-requests = <{dt['dma_requests']}>;",
        f"\t\t\tresets = {reset};",
        "\t\t\t#dma-cells = <1>;",
        "\t\t};",
    ]
    return "\n".join(lines)


def main():
    if not DATA_PATH.exists():
        print(f"Error: {DATA_PATH} not found", file=sys.stderr)
        sys.exit(1)

    with open(DATA_PATH, "r") as f:
        data = json.load(f)

    print("/* === Generated driver patch for sun6i-dma.c === */")
    print()
    print(generate_driver_patch(data))
    print()
    print("/* === Generated DT snippet for sun60i-a733.dtsi === */")
    print()
    print(generate_dt_snippet(data))
    print()

    # Also emit UART dmas references
    uart = data["devices"]["uart"]
    print("/* === UART dma references === */")
    for port, req in zip(uart["ports"], uart["request_lines"]):
        print(
            f'&uart{port} {{\n\tdmas = <&dma {req}>, <&dma {req}>;\n\tdma-names = "tx", "rx";\n}};'
        )
    print()


if __name__ == "__main__":
    main()
