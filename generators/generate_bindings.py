#!/usr/bin/env python3
"""
Device Tree binding documentation generator.

Generates YAML binding files required for upstream submission.
Each driver needs a binding document in Documentation/devicetree/bindings/.

Usage:
    python3 generators/generate_bindings.py
    # Outputs to generators/output/bindings/
"""

import sys
from pathlib import Path

BINDINGS = {
    "ccu": {
        "compatible": "allwinner,sun60i-a733-ccu",
        "title": "Allwinner A733 Clock Controller Unit (CCU)",
        "description": "The Allwinner A733 CCU provides clocks and resets for all on-chip peripherals.",
        "properties": {
            "compatible": {"const": "allwinner,sun60i-a733-ccu"},
            "reg": {"maxItems": 1, "description": "CCU register region"},
            "clocks": {
                "items": [
                    {"description": "High frequency oscillator (24 MHz)"},
                    {"description": "Low frequency oscillator (32.768 kHz)"},
                ]
            },
            "clock-names": {"items": ["hosc", "losc"]},
            "#clock-cells": {
                "const": 1,
                "description": "One cell indicating the clock index",
            },
            "#reset-cells": {
                "const": 1,
                "description": "One cell indicating the reset index",
            },
        },
        "required": [
            "compatible",
            "reg",
            "clocks",
            "clock-names",
            "#clock-cells",
            "#reset-cells",
        ],
        "examples": [
            """ccu: clock-controller@2002000 {
    compatible = "allwinner,sun60i-a733-ccu";
    reg = <0x02002000 0x2000>;
    clocks = <&osc24M>, <&rtc_ccu CLK_OSC32K>;
    clock-names = "hosc", "losc";
    #clock-cells = <1>;
    #reset-cells = <1>;
};"""
        ],
    },
    "pinctrl": {
        "compatible": "allwinner,sun60i-a733-pinctrl",
        "title": "Allwinner A733 Pin Controller",
        "description": "The Allwinner A733 pin controller manages GPIO and pin multiplexing for PA-PK banks.",
        "properties": {
            "compatible": {"const": "allwinner,sun60i-a733-pinctrl"},
            "reg": {"maxItems": 1},
            "interrupts": {
                "minItems": 1,
                "maxItems": 10,
                "description": "One interrupt per GPIO bank",
            },
            "clocks": {
                "items": [
                    {"description": "APB clock"},
                    {"description": "High frequency oscillator"},
                    {"description": "Low frequency oscillator"},
                ]
            },
            "clock-names": {"items": ["apb", "hosc", "losc"]},
            "gpio-controller": True,
            "#gpio-cells": {"const": 3, "description": "Bank, pin, flags"},
            "interrupt-controller": True,
            "#interrupt-cells": {"const": 3},
        },
        "required": [
            "compatible",
            "reg",
            "interrupts",
            "clocks",
            "clock-names",
            "gpio-controller",
            "#gpio-cells",
            "interrupt-controller",
            "#interrupt-cells",
        ],
        "examples": [
            """pio: pinctrl@2000000 {
    compatible = "allwinner,sun60i-a733-pinctrl";
    reg = <0x2000000 0x600>;
    interrupts = <GIC_SPI 69 IRQ_TYPE_LEVEL_HIGH>,
                 <GIC_SPI 71 IRQ_TYPE_LEVEL_HIGH>;
    clocks = <&ccu CLK_APB1>, <&osc24M>, <&rtc_ccu CLK_OSC32K>;
    clock-names = "apb", "hosc", "losc";
    gpio-controller;
    #gpio-cells = <3>;
    interrupt-controller;
    #interrupt-cells = <3>;
};"""
        ],
    },
    "r-pinctrl": {
        "compatible": "allwinner,sun60i-a733-r-pinctrl",
        "title": "Allwinner A733 R-Domain Pin Controller",
        "description": "The R-domain pin controller manages GPIO for the always-on PL-PM banks.",
        "properties": {
            "compatible": {"const": "allwinner,sun60i-a733-r-pinctrl"},
            "reg": {"maxItems": 1},
            "interrupts": {"maxItems": 2},
            "clocks": {
                "items": [
                    {"description": "APB clock"},
                    {"description": "High frequency oscillator"},
                    {"description": "Low frequency oscillator"},
                ]
            },
            "clock-names": {"items": ["apb", "hosc", "losc"]},
            "gpio-controller": True,
            "#gpio-cells": {"const": 3},
            "interrupt-controller": True,
            "#interrupt-cells": {"const": 3},
        },
        "required": [
            "compatible",
            "reg",
            "interrupts",
            "clocks",
            "clock-names",
            "gpio-controller",
            "#gpio-cells",
            "interrupt-controller",
            "#interrupt-cells",
        ],
        "examples": [
            """r_pio: pinctrl@7025000 {
    compatible = "allwinner,sun60i-a733-r-pinctrl";
    reg = <0x7025000 0x410>;
    interrupts = <GIC_SPI 198 IRQ_TYPE_LEVEL_HIGH>,
                 <GIC_SPI 200 IRQ_TYPE_LEVEL_HIGH>;
    clocks = <&r_ccu CLK_R_APBS0>, <&osc24M>, <&rtc_ccu CLK_OSC32K>;
    clock-names = "apb", "hosc", "losc";
    gpio-controller;
    #gpio-cells = <3>;
    interrupt-controller;
    #interrupt-cells = <3>;
};"""
        ],
    },
    "board": {
        "compatible": "xunlong,orangepi-4-pro",
        "title": "Orange Pi 4 Pro",
        "description": "The Orange Pi 4 Pro is a single-board computer based on the Allwinner A733 SoC.",
        "properties": {
            "compatible": {
                "items": [
                    {"const": "xunlong,orangepi-4-pro"},
                    {"const": "allwinner,sun60i-a733"},
                ]
            },
            "model": {"const": "Orange Pi 4 Pro"},
        },
        "required": ["compatible"],
        "examples": [
            """/ {
    model = "Orange Pi 4 Pro";
    compatible = "xunlong,orangepi-4-pro", "allwinner,sun60i-a733";
};"""
        ],
    },
}


def generate_yaml(binding_name, binding):
    """Generate a YAML binding document."""

    yaml = f"""# SPDX-License-Identifier: (GPL-2.0-only OR BSD-2-Clause)
%YAML 1.2
---
$id: http://devicetree.org/schemas/clock/allwinner,{binding_name.replace("_", "-")}-sun60i-a733.yaml#
$schema: http://devicetree.org/meta-schemas/core.yaml#

title: {binding["title"]}

maintainers:
  - Alexander Grec <alex092lap@duck.com>

description: |
  {binding["description"]}

properties:
  compatible:
"""

    if "const" in binding["properties"]["compatible"]:
        yaml += f"    const: {binding['properties']['compatible']['const']}\n"
    elif "items" in binding["properties"]["compatible"]:
        yaml += "    items:\n"
        for item in binding["properties"]["compatible"]["items"]:
            yaml += f"      - const: {item['const']}\n"

    # Add other properties
    for prop_name, prop_def in binding["properties"].items():
        if prop_name == "compatible":
            continue

        yaml += f"\n  {prop_name}:\n"

        if prop_def is True:
            yaml += "    type: boolean\n"
        elif isinstance(prop_def, dict):
            if "const" in prop_def:
                yaml += f"    const: {prop_def['const']}\n"
            if "maxItems" in prop_def:
                yaml += f"    maxItems: {prop_def['maxItems']}\n"
            if "minItems" in prop_def:
                yaml += f"    minItems: {prop_def['minItems']}\n"
            if "description" in prop_def:
                yaml += f"    description: {prop_def['description']}\n"
            if "items" in prop_def:
                yaml += "    items:\n"
                for item in prop_def["items"]:
                    if isinstance(item, str):
                        yaml += f"      - const: {item}\n"
                    elif isinstance(item, dict):
                        yaml += f"      - description: {item['description']}\n"

    # Required properties
    yaml += "\nrequired:\n"
    for req in binding["required"]:
        yaml += f"  - {req}\n"

    # Examples
    yaml += "\nadditionalProperties: false\n"
    yaml += "\nexamples:\n"
    for i, example in enumerate(binding["examples"]):
        yaml += f"  - |\n"
        for line in example.split("\n"):
            yaml += f"      {line}\n"

    return yaml


if __name__ == "__main__":
    out_dir = Path(__file__).parent / "output" / "bindings"
    out_dir.mkdir(parents=True, exist_ok=True)

    for name, binding in BINDINGS.items():
        yaml = generate_yaml(name, binding)
        filename = f"allwinner,{name}-sun60i-a733.yaml"
        filepath = out_dir / filename
        with open(filepath, "w") as f:
            f.write(yaml)
        print(f"Generated: {filepath}")

    print(f"\nAll bindings written to {out_dir}/")
    print("\nTo validate bindings (requires linux tree):")
    print("  ./scripts/check_dtschema.py <binding_file>")
