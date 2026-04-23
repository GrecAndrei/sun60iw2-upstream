#!/usr/bin/env python3
"""
Generate sun60i-a733 CCU driver code from structured data.

Design goals:
- Merge canonical IDs from ccu-main.json with richer extracted shapes from
  ccu-main-extracted.json.
- Emit only framework-supported clock shapes.
- Keep unsupported/vendor-only details visible as TODO comments.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set

# Ensure project root is in path for plugin imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from generators.plugins import DOMAINS

HELPER_PATTERNS = ("-sdm-pat",)
SUPPORTED_TYPES = {
    "nm",
    "nkmp",
    "divider",
    "fixed_factor",
    "gate",
    "gate_with_fixed_rate",
    "gate_with_key",
    "mux",
    "mux_gate",
    "mux_gate_key",
    "mux_divider",
    "mux_divider_gate",
    "mp_mux_gate_no_index",
}

DEFAULT_KEY_LITERALS = {
    "AHB_MASTER_KEY_VALUE": "0x10000FF",
    "MBUS_MASTER_KEY_VALUE": "0x41055800",
    "MBUS_GATE_KEY_VALUE": "0x40302",
    "UPD_KEY_VALUE": "0x8000000",
}


def c_name(name: str) -> str:
    return name.replace("-", "_")


def reg_hex(value) -> str:
    return f"0x{int(value, 0) if isinstance(value, str) else int(value):03x}"


def is_helper(name: str) -> bool:
    return any(marker in name for marker in HELPER_PATTERNS)


def load_json(path: Path) -> Dict:
    with path.open() as f:
        return json.load(f)


def parse_binding_ids(path: Path) -> Set[str]:
    if not path.exists():
        return set()
    text = path.read_text()
    return {
        m.group(1)
        for m in re.finditer(r"^#define\s+CLK_([A-Z0-9_]+)\s+\d+", text, re.M)
    }


def norm_id_token(name: str) -> str:
    token = re.sub(r"[^A-Za-z0-9]+", "_", name.upper())
    return re.sub(r"_+", "_", token).strip("_")


def id_candidates(name: str) -> List[str]:
    base = norm_id_token(name)
    cands: List[str] = []

    def add(value: str):
        if value and value not in cands:
            cands.append(value)

    add(base)
    add(f"BUS_{base}")
    add(f"{base}_GATE")

    if base.endswith("_BUS"):
        root = base[:-4]
        add(root)
        add(f"BUS_{root}")

    if base.endswith("_GATE"):
        root = base[:-5]
        add(root)
        add(f"BUS_{root}")

    if base.startswith("BUS_"):
        root = base[4:]
        add(root)
        add(f"{root}_GATE")

    return cands


def flag_expr(value) -> str:
    if not value:
        return "0"
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " | ".join(value) if value else "0"
    return str(value)


def infer_clock_id(name: str, binding_ids: Set[str]) -> str | None:
    for cand in id_candidates(name):
        if cand in binding_ids:
            return cand
    return None


def merge_data(primary: Dict, extracted: Dict, binding_ids: Set[str]) -> Dict:
    primary_clocks = primary.get("clocks", [])
    extracted_clocks = extracted.get("clocks", [])

    primary_by_name = {
        item.get("name"): item for item in primary_clocks if item.get("name")
    }

    merged: List[Dict] = []
    seen = set()

    for item in extracted_clocks:
        name = item.get("name")
        if not name:
            continue
        out = dict(item)
        canon = primary_by_name.get(name)
        if canon:
            if "id" in canon:
                out["id"] = canon["id"]
                out["_id_source"] = "canonical"
            if "flags" in canon and "flags" not in out:
                out["flags"] = canon["flags"]
        elif out.get("type") != "parent_array":
            inferred = infer_clock_id(name, binding_ids)
            if inferred:
                out["id"] = inferred
                out["_id_source"] = "inferred"
        merged.append(out)
        seen.add(name)

    for item in primary_clocks:
        name = item.get("name")
        if not name or name in seen:
            continue
        extra = dict(item)
        if "id" in extra:
            extra["_id_source"] = "canonical"
        merged.append(extra)

    return {
        **primary,
        "clocks": merged,
        "resets": primary.get("resets", []),
    }


def build_metrics(data: Dict, generated: Generator | None = None) -> Dict:
    clocks = data.get("clocks", [])
    extracted = [c for c in clocks if c.get("type") != "parent_array"]
    parent_arrays = [c for c in clocks if c.get("type") == "parent_array"]
    supported = [
        c
        for c in extracted
        if c.get("type") in SUPPORTED_TYPES and not is_helper(c.get("name", ""))
    ]
    ids = [c for c in extracted if c.get("id")]
    canonical_ids = [c for c in extracted if c.get("_id_source") == "canonical"]
    inferred_ids = [c for c in extracted if c.get("_id_source") == "inferred"]

    metrics = {
        "total_clocks": len(clocks),
        "extractable_clocks": len(extracted),
        "parent_arrays": len(parent_arrays),
        "supported_clocks": len(supported),
        "id_mapped_clocks": len(ids),
        "id_mapped_canonical": len(canonical_ids),
        "id_mapped_inferred": len(inferred_ids),
        "support_coverage": round((len(supported) / len(extracted)) * 100, 2)
        if extracted
        else 0.0,
        "id_coverage": round((len(ids) / len(extracted)) * 100, 2)
        if extracted
        else 0.0,
    }

    if generated is not None:
        emitted_common = set(generated.emitted_common)
        emitted_hw = set(generated.emitted_hw)
        metrics.update(
            {
                "emitted_common": len(emitted_common),
                "emitted_hw": len(emitted_hw),
                "unsupported_entries": len(set(generated.unsupported)),
                "emit_common_coverage": round(
                    (len(emitted_common) / len(supported)) * 100, 2
                )
                if supported
                else 0.0,
                "emit_hw_coverage": round((len(emitted_hw) / len(supported)) * 100, 2)
                if supported
                else 0.0,
                "key_gate_native_emitted": len(set(generated.key_gate_emitted)),
                "key_gate_fallbacks": max(
                    0,
                    sum(1 for c in generated.clocks if c.get("type") == "gate_with_key")
                    - len(set(generated.key_gate_emitted)),
                ),
            }
        )

    return metrics


class Generator:
    def __init__(self, data: Dict, domain: Dict):
        self.data = data
        self.domain = domain
        self.all_clocks = data.get("clocks", [])
        self.resets = data.get("resets", []) if domain.get("has_resets", True) else []

        self.parent_arrays = {
            c["name"]: c.get("parents", [])
            for c in self.all_clocks
            if c.get("type") == "parent_array"
        }

        self.clocks = [
            c
            for c in self.all_clocks
            if c.get("type") != "parent_array"
            and c.get("name")
            and not is_helper(c["name"])
        ]
        self.by_name = {c["name"]: c for c in self.clocks}

        self.unsupported: List[str] = []
        self.emitted_common: List[str] = []
        self.emitted_hw: List[str] = []
        self.key_gate_emitted: List[str] = []
        self.defined_names: set[str] = set()

    def hw_ref(self, parent_name: str) -> str:
        if parent_name not in self.defined_names:
            return ""
        node = self.by_name.get(parent_name)
        if not node:
            return ""
        t = node.get("type")
        if t == "fixed_factor":
            return f"&{c_name(parent_name)}_clk.hw"
        if t == "gate_with_key":
            return f"&{c_name(parent_name)}_clk.gate.common.hw"
        if t == "gate_with_fixed_rate":
            return f"&{c_name(parent_name)}_clk.gate.common.hw"
        return f"&{c_name(parent_name)}_clk.common.hw"

    def parent_data_entries(self, parents: List[str]) -> List[str]:
        entries = []
        for parent in parents:
            ref = self.hw_ref(parent)
            if ref:
                entries.append(f"\t{{ .hw = {ref} }},")
            else:
                entries.append(f'\t{{ .fw_name = "{parent}" }},')
        return entries

    def emit_header(self) -> str:
        d = self.domain
        compat = d["compat"]
        mod = d["module_name"]
        binding = d["binding_header"]
        has_resets = d.get("has_resets", True)
        has_key_gates = d.get("has_key_gates", True)
        has_fixed_rate_gates = any(
            c.get("type") == "gate_with_fixed_rate" for c in self.clocks
        )

        reset_include = f"#include <dt-bindings/reset/{binding}>" if has_resets else ""

        key_gate_struct = (
            """struct sun60i_key_gate {
	struct ccu_gate gate;
	u32 key_value;
};

static inline struct sun60i_key_gate *hw_to_sun60i_key_gate(struct clk_hw *hw)
{
	struct ccu_gate *cg = hw_to_ccu_gate(hw);

	return container_of(cg, struct sun60i_key_gate, gate);
}

static int sun60i_key_gate_enable(struct clk_hw *hw)
{
	struct sun60i_key_gate *kg = hw_to_sun60i_key_gate(hw);
	struct ccu_common *common = &kg->gate.common;
	unsigned long flags;
	u32 reg;

	spin_lock_irqsave(common->lock, flags);
	reg = readl(common->base + common->reg);
	reg |= kg->key_value;
	reg |= kg->gate.enable;
	if (common->features & CCU_FEATURE_UPDATE_BIT)
		reg |= CCU_SUNXI_UPDATE_BIT;
	writel(reg, common->base + common->reg);
	spin_unlock_irqrestore(common->lock, flags);

	return 0;
}

static void sun60i_key_gate_disable(struct clk_hw *hw)
{
	struct sun60i_key_gate *kg = hw_to_sun60i_key_gate(hw);
	struct ccu_common *common = &kg->gate.common;
	unsigned long flags;
	u32 reg;

	spin_lock_irqsave(common->lock, flags);
	reg = readl(common->base + common->reg);
	reg |= kg->key_value;
	reg &= ~kg->gate.enable;
	if (common->features & CCU_FEATURE_UPDATE_BIT)
		reg |= CCU_SUNXI_UPDATE_BIT;
	writel(reg, common->base + common->reg);
	spin_unlock_irqrestore(common->lock, flags);
}

static int sun60i_key_gate_is_enabled(struct clk_hw *hw)
{
	struct sun60i_key_gate *kg = hw_to_sun60i_key_gate(hw);

	return ccu_gate_helper_is_enabled(&kg->gate.common, kg->gate.enable);
}

static unsigned long sun60i_key_gate_recalc_rate(struct clk_hw *hw,
						 unsigned long parent_rate)
{
	return parent_rate;
}

static int sun60i_key_gate_determine_rate(struct clk_hw *hw,
					  struct clk_rate_request *req)
{
	if (clk_hw_get_flags(hw) & CLK_SET_RATE_PARENT)
		req->best_parent_rate = clk_hw_round_rate(clk_hw_get_parent(hw), req->rate);

	req->rate = req->best_parent_rate;
	return 0;
}

static int sun60i_key_gate_set_rate(struct clk_hw *hw, unsigned long rate,
				    unsigned long parent_rate)
{
	return 0;
}

static const struct clk_ops sun60i_key_gate_ops = {
	.disable	= sun60i_key_gate_disable,
	.enable		= sun60i_key_gate_enable,
	.is_enabled	= sun60i_key_gate_is_enabled,
	.determine_rate	= sun60i_key_gate_determine_rate,
	.set_rate	= sun60i_key_gate_set_rate,
	.recalc_rate	= sun60i_key_gate_recalc_rate,
};

"""
            if has_key_gates
            else ""
        )

        fixed_rate_gate_struct = (
            """struct sun60i_fixed_rate_gate {
	struct ccu_gate gate;
	unsigned long fixed_rate;
};

static inline struct sun60i_fixed_rate_gate *hw_to_sun60i_fixed_rate_gate(struct clk_hw *hw)
{
	struct ccu_gate *cg = hw_to_ccu_gate(hw);

	return container_of(cg, struct sun60i_fixed_rate_gate, gate);
}

static int sun60i_fixed_rate_gate_enable(struct clk_hw *hw)
{
	struct sun60i_fixed_rate_gate *fg = hw_to_sun60i_fixed_rate_gate(hw);

	return ccu_gate_helper_enable(&fg->gate.common, fg->gate.enable);
}

static void sun60i_fixed_rate_gate_disable(struct clk_hw *hw)
{
	struct sun60i_fixed_rate_gate *fg = hw_to_sun60i_fixed_rate_gate(hw);

	ccu_gate_helper_disable(&fg->gate.common, fg->gate.enable);
}

static int sun60i_fixed_rate_gate_is_enabled(struct clk_hw *hw)
{
	struct sun60i_fixed_rate_gate *fg = hw_to_sun60i_fixed_rate_gate(hw);

	return ccu_gate_helper_is_enabled(&fg->gate.common, fg->gate.enable);
}

static unsigned long sun60i_fixed_rate_gate_recalc_rate(struct clk_hw *hw,
							unsigned long parent_rate)
{
	struct sun60i_fixed_rate_gate *fg = hw_to_sun60i_fixed_rate_gate(hw);

	return fg->fixed_rate;
}

static int sun60i_fixed_rate_gate_determine_rate(struct clk_hw *hw,
						 struct clk_rate_request *req)
{
	struct sun60i_fixed_rate_gate *fg = hw_to_sun60i_fixed_rate_gate(hw);

	req->rate = fg->fixed_rate;
	return 0;
}

static int sun60i_fixed_rate_gate_set_rate(struct clk_hw *hw, unsigned long rate,
					   unsigned long parent_rate)
{
	return 0;
}

static const struct clk_ops sun60i_fixed_rate_gate_ops = {
	.disable	= sun60i_fixed_rate_gate_disable,
	.enable		= sun60i_fixed_rate_gate_enable,
	.is_enabled	= sun60i_fixed_rate_gate_is_enabled,
	.determine_rate	= sun60i_fixed_rate_gate_determine_rate,
	.set_rate	= sun60i_fixed_rate_gate_set_rate,
	.recalc_rate	= sun60i_fixed_rate_gate_recalc_rate,
};

"""
            if has_fixed_rate_gates
            else ""
        )

        return f"""// SPDX-License-Identifier: GPL-2.0
/*
 * Copyright (C) 2026 Alexander Grec
 *
 * GENERATED FILE - DO NOT EDIT MANUALLY
 * Generated by: generators/generate_ccu.py --domain {d["name"]}
 * Source data:  {d.get("data_file", "unknown")}
 */

#include <linux/clk-provider.h>
#include <linux/io.h>
#include <linux/module.h>
#include <linux/platform_device.h>

#include <dt-bindings/clock/{binding}>
{reset_include}

#include "../clk.h"

#include "ccu_common.h"
#include "ccu_reset.h"

#include "ccu_div.h"
#include "ccu_gate.h"
#include "ccu_mp.h"
#include "ccu_nm.h"
#include "ccu_nkmp.h"
#include "ccu_mux.h"

static const struct clk_parent_data osc24M[] = {{
	{{ .fw_name = "hosc" }},
}};

{key_gate_struct}{fixed_rate_gate_struct}"""

    def emit_pll(self, c: Dict) -> str:
        name = c_name(c["name"])
        reg = reg_hex(c["reg"])
        parent = c.get("parent", "dcxo")

        self.emitted_common.append(c["name"])
        self.emitted_hw.append(c["name"])
        self.defined_names.add(c["name"])

        if c.get("type") == "nkmp":
            return f"""static struct ccu_nkmp {name}_clk = {{
	.enable		= BIT(27),
	.lock		= BIT(28),
	.n		= _SUNXI_CCU_MULT_MIN(8, 8, 11),
	.m		= _SUNXI_CCU_DIV(1, 1),
	.p		= _SUNXI_CCU_DIV(0, 1),
	.common		= {{
		.reg		= {reg},
		.hw.init	= CLK_HW_INIT("{c["name"]}", "{parent}", &ccu_nkmp_ops,
					      CLK_SET_RATE_GATE),
	}},
}};

"""

        return f"""static struct ccu_nm {name}_clk = {{
	.enable		= BIT(27),
	.lock		= BIT(28),
	.n		= _SUNXI_CCU_MULT_MIN(8, 8, 11),
	.m		= _SUNXI_CCU_DIV(1, 1),
	.common		= {{
		.reg		= {reg},
		.hw.init	= CLK_HW_INIT("{c["name"]}", "{parent}", &ccu_nm_ops,
					      CLK_SET_RATE_GATE),
	}},
}};

"""

    def emit_parent_arrays(self) -> str:
        out = []
        for arr, parents in sorted(self.parent_arrays.items()):
            out.append(f"static const struct clk_parent_data {arr}[] = {{")
            out.extend(self.parent_data_entries(parents))
            out.append("};\n")
        return "\n".join(out)

    def emit_divider(self, c: Dict) -> str:
        name = c_name(c["name"])
        self.emitted_common.append(c["name"])
        self.emitted_hw.append(c["name"])
        self.defined_names.add(c["name"])
        return (
            f'static SUNXI_CCU_M({name}_clk, "{c["name"]}", "{c["parent"]}",'
            f" {reg_hex(c['reg'])}, {c.get('shift', 0)}, {c.get('width', 0)}, 0);\n\n"
        )

    def emit_gate(self, c: Dict) -> str:
        name = c_name(c["name"])
        self.emitted_common.append(c["name"])
        self.emitted_hw.append(c["name"])
        self.defined_names.add(c["name"])
        return (
            f'static SUNXI_CCU_GATE({name}_clk, "{c["name"]}", "{c["parent"]}",'
            f" {reg_hex(c['reg'])}, BIT({c['bit']}), 0);\n\n"
        )

    def emit_gate_with_key(self, c: Dict) -> str:
        name = c_name(c["name"])
        self.emitted_common.append(c["name"])
        self.emitted_hw.append(c["name"])
        self.key_gate_emitted.append(c["name"])
        self.defined_names.add(c["name"])

        key_token = c.get("key_value", "0")
        key_literals = {**DEFAULT_KEY_LITERALS, **self.domain.get("key_literals", {})}
        key_literal = key_literals.get(key_token, key_token)
        flags = flag_expr(c.get("flags"))

        return f"""static struct sun60i_key_gate {name}_clk = {{
	.gate		= {{
		.enable	= BIT({c["bit"]}),
		.common	= {{
			.reg		= {reg_hex(c["reg"])},
			.hw.init	= CLK_HW_INIT("{c["name"]}", "{c["parent"]}",
					      &sun60i_key_gate_ops,
					      {flags}),
		}},
	}},
	.key_value	= {key_literal},
}};

"""

    def emit_gate_with_fixed_rate(self, c: Dict) -> str:
        name = c_name(c["name"])
        self.emitted_common.append(c["name"])
        self.emitted_hw.append(c["name"])
        self.defined_names.add(c["name"])

        return f"""static struct sun60i_fixed_rate_gate {name}_clk = {{
	.gate		= {{
		.enable	= BIT({c["bit"]}),
		.common	= {{
			.reg		= {reg_hex(c["reg"])},
			.hw.init	= CLK_HW_INIT("{c["name"]}", "{c["parent"]}",
					      &sun60i_fixed_rate_gate_ops,
					      0),
		}},
	}},
	.fixed_rate	= {c["rate"]},
}};

"""

    def emit_fixed_factor(self, c: Dict) -> str:
        name = c_name(c["name"])
        self.emitted_hw.append(c["name"])
        self.defined_names.add(c["name"])
        return (
            f'static CLK_FIXED_FACTOR({name}_clk, "{c["name"]}", "{c["parent"]}",'
            f" {c['div']}, {c['mult']}, 0);\n\n"
        )

    def emit_mux(self, c: Dict) -> str:
        name = c_name(c["name"])
        self.emitted_common.append(c["name"])
        self.emitted_hw.append(c["name"])
        self.defined_names.add(c["name"])
        flags = flag_expr(c.get("flags"))
        return (
            f'static SUNXI_CCU_MUX_DATA({name}_clk, "{c["name"]}", {c["parents_array"]},'
            f" {reg_hex(c['reg'])}, {c['mux_shift']}, {c['mux_width']}, {flags});\n\n"
        )

    def emit_mux_gate(self, c: Dict) -> str:
        name = c_name(c["name"])
        self.emitted_common.append(c["name"])
        self.emitted_hw.append(c["name"])
        self.defined_names.add(c["name"])
        flags = flag_expr(c.get("flags"))
        return (
            f'static SUNXI_CCU_MUX_DATA_WITH_GATE({name}_clk, "{c["name"]}", {c["parents_array"]},'
            f" {reg_hex(c['reg'])}, {c['mux_shift']}, {c['mux_width']}, BIT({c['gate_bit']}), {flags});\n\n"
        )

    def emit_mux_gate_key(self, c: Dict) -> str:
        name = c_name(c["name"])
        self.emitted_common.append(c["name"])
        self.emitted_hw.append(c["name"])
        self.defined_names.add(c["name"])
        flags = flag_expr(c.get("flags"))
        return f"""static struct ccu_mux {name}_clk = {{
	.enable	= BIT({c["gate_bit"]}),
	.mux	= _SUNXI_CCU_MUX({c["mux_shift"]}, {c["mux_width"]}),
	.common	= {{
		.reg		= {reg_hex(c["reg"])},
		.features	= CCU_FEATURE_KEY_FIELD,
		.hw.init	= CLK_HW_INIT_PARENTS_DATA("{c["name"]}",
							   {c["parents_array"]},
							   &ccu_mux_ops,
							   {flags}),
	}},
}};

"""

    def emit_mp_mux_gate(self, c: Dict) -> str:
        name = c_name(c["name"])
        self.emitted_common.append(c["name"])
        self.emitted_hw.append(c["name"])
        self.defined_names.add(c["name"])
        return (
            f'static SUNXI_CCU_MP_DATA_WITH_MUX_GATE_FEAT({name}_clk, "{c["name"]}", {c["parents_array"]},'
            f" {reg_hex(c['reg'])}, {c['m_shift']}, {c['m_width']}, {c['n_shift']}, {c['n_width']},"
            f" {c['mux_shift']}, {c['mux_width']}, BIT({c['gate_bit']}), 0, CCU_FEATURE_DUAL_DIV);\n\n"
        )

    def emit_mux_divider(self, c: Dict, with_gate: bool = False) -> str:
        name = c_name(c["name"])
        self.emitted_common.append(c["name"])
        self.emitted_hw.append(c["name"])
        self.defined_names.add(c["name"])
        flags = flag_expr(c.get("flags"))
        if with_gate:
            return (
                f'static SUNXI_CCU_M_DATA_WITH_MUX_GATE({name}_clk, "{c["name"]}", {c["parents_array"]},'
                f" {reg_hex(c['reg'])}, {c['div_shift']}, {c['div_width']}, {c['mux_shift']}, {c['mux_width']},"
                f" BIT({c['gate_bit']}), {flags});\n\n"
            )
        return (
            f'static SUNXI_CCU_M_DATA_WITH_MUX({name}_clk, "{c["name"]}", {c["parents_array"]},'
            f" {reg_hex(c['reg'])}, {c['div_shift']}, {c['div_width']}, {c['mux_shift']}, {c['mux_width']}, {flags});\n\n"
        )

    def emit_clock(self, c: Dict) -> str:
        t = c.get("type")
        if t == "divider":
            return self.emit_divider(c)
        if t == "gate":
            return self.emit_gate(c)
        if t == "gate_with_fixed_rate":
            return self.emit_gate_with_fixed_rate(c)
        if t == "gate_with_key":
            return self.emit_gate_with_key(c)
        if t == "fixed_factor":
            return self.emit_fixed_factor(c)
        if t == "mux":
            return self.emit_mux(c)
        if t == "mux_gate":
            return self.emit_mux_gate(c)
        if t == "mux_gate_key":
            return self.emit_mux_gate_key(c)
        if t == "mux_divider":
            return self.emit_mux_divider(c, with_gate=False)
        if t == "mux_divider_gate":
            return self.emit_mux_divider(c, with_gate=True)
        if t == "mp_mux_gate_no_index":
            return self.emit_mp_mux_gate(c)

        self.unsupported.append(f"{t}: {c.get('name')}")
        return f"/* Unsupported clock type '{t}' for '{c.get('name')}' */\n\n"

    def emit_ccu_clks(self) -> str:
        suffix = (
            self.domain["module_name"].replace("sun60i-a733-", "").replace("-", "_")
        )
        var_name = f"sun60i_a733_{suffix}_clks"
        lines = []
        for c in self.clocks:
            if c["name"] in self.emitted_common:
                if c.get("type") in {"gate_with_key", "gate_with_fixed_rate"}:
                    lines.append(f"\t&{c_name(c['name'])}_clk.gate.common,")
                else:
                    lines.append(f"\t&{c_name(c['name'])}_clk.common,")
        body = "\n".join(lines)
        return f"static struct ccu_common *{var_name}[] = {{\n{body}\n}};\n\n"

    def emit_hw_clks(self) -> str:
        suffix = (
            self.domain["module_name"].replace("sun60i-a733-", "").replace("-", "_")
        )
        var_name = f"sun60i_a733_{suffix}_hw_clks"
        lines = []
        for c in self.clocks:
            clk_id = c.get("id")
            if not clk_id or c["name"] not in self.emitted_hw:
                continue
            if c.get("type") == "fixed_factor":
                lines.append(f"\t[CLK_{clk_id}]\t= &{c_name(c['name'])}_clk.hw,")
            elif c.get("type") in {"gate_with_key", "gate_with_fixed_rate"}:
                lines.append(
                    f"\t[CLK_{clk_id}]\t= &{c_name(c['name'])}_clk.gate.common.hw,"
                )
            else:
                lines.append(f"\t[CLK_{clk_id}]\t= &{c_name(c['name'])}_clk.common.hw,")
        body = "\n".join(lines)
        domain_name = self.domain["name"].upper()
        num_macro = (
            f"CLK_{domain_name}_NUMBER" if domain_name != "MAIN" else "CLK_NUMBER"
        )
        return f"""static struct clk_hw_onecell_data {var_name} = {{
	.num	= {num_macro},
	.hws	= {{
{body}
	}},
}};

"""

    def emit_resets(self) -> str:
        if not self.resets:
            return ""
        lines = []
        for r in self.resets:
            lines.append(
                f"\t[RST_{r['id']}]\t= {{ {reg_hex(r['reg'])}, BIT({r['bit']}) }},"
            )
        body = "\n".join(lines)
        return f"static struct ccu_reset_map sun60i_a733_ccu_resets[] = {{\n{body}\n}};\n\n"

    def emit_desc(self) -> str:
        d = self.domain
        suffix = d["module_name"].replace("sun60i-a733-", "").replace("-", "_")
        desc_name = f"sun60i_a733_{suffix}_desc"
        resets_ptr = f"sun60i_a733_{suffix}_resets" if self.resets else "NULL"
        resets_num = f"ARRAY_SIZE(sun60i_a733_{suffix}_resets)" if self.resets else "0"
        clks_name = f"sun60i_a733_{suffix}_clks"
        hw_clks_name = f"sun60i_a733_{suffix}_hw_clks"
        return f"""static const struct sunxi_ccu_desc {desc_name} = {{
	.ccu_clks	= {clks_name},
	.num_ccu_clks	= ARRAY_SIZE({clks_name}),

	.hw_clks	= &{hw_clks_name},

	.resets		= {resets_ptr},
	.num_resets	= {resets_num},
}};

"""

    def emit_probe(self) -> str:
        d = self.domain
        compat = d["compat"]
        mod = d["module_name"]
        suffix = mod.replace("sun60i-a733-", "").replace("-", "_")
        desc_name = f"sun60i_a733_{suffix}_desc"
        probe_name = f"sun60i_a733_{suffix}_probe"
        ids_name = f"sun60i_a733_{suffix}_ids"
        drv_name = f"sun60i_a733_{suffix}_driver"
        return f"""static int {probe_name}(struct platform_device *pdev)
{{
	void __iomem *reg;
	int ret;

	reg = devm_platform_ioremap_resource(pdev, 0);
	if (IS_ERR(reg))
		return PTR_ERR(reg);

	ret = devm_sunxi_ccu_probe(&pdev->dev, reg, &{desc_name});
	if (ret)
		return ret;

	return 0;
}}

static const struct of_device_id {ids_name}[] = {{
	{{ .compatible = "{compat}" }},
	{{ }}
}};
MODULE_DEVICE_TABLE(of, {ids_name});

static struct platform_driver {drv_name} = {{
	.probe	= {probe_name},
	.driver	= {{
		.name			= "{mod}",
		.suppress_bind_attrs	= true,
		.of_match_table		= {ids_name},
	}},
}};
module_platform_driver({drv_name});

MODULE_IMPORT_NS("SUNXI_CCU");
MODULE_DESCRIPTION("Support for the Allwinner A733 {suffix.upper()} CCU");
MODULE_LICENSE("GPL");
"""

    def render(self) -> str:
        out = [self.emit_header()]

        pll_types = {"nm", "nkmp"}
        parent_array_types = {
            "mux",
            "mux_gate",
            "mux_gate_key",
            "mux_divider",
            "mux_divider_gate",
            "mp_mux_gate_no_index",
        }

        # Phase 1: define PLL roots first.
        for c in self.clocks:
            if c.get("type") in pll_types:
                out.append(self.emit_pll(c))

        # Phase 2: define non-parent-array clocks (fixed factors, gates, dividers)
        # so parent arrays can safely reference them by .hw/.common.hw.
        for c in self.clocks:
            t = c.get("type")
            if t in pll_types or t in parent_array_types:
                continue
            if t not in SUPPORTED_TYPES:
                self.unsupported.append(f"{t}: {c.get('name')}")
                out.append(
                    f"/* Unsupported clock type '{t}' for '{c.get('name')}' */\n\n"
                )
                continue
            out.append(self.emit_clock(c))

        # Phase 3: now emit parent arrays; hw refs are used only for already-defined symbols.
        out.append(self.emit_parent_arrays())

        # Phase 4: emit parent-array consumers.
        for c in self.clocks:
            t = c.get("type")
            if t not in parent_array_types:
                continue
            if t not in SUPPORTED_TYPES:
                self.unsupported.append(f"{t}: {c.get('name')}")
                out.append(
                    f"/* Unsupported clock type '{t}' for '{c.get('name')}' */\n\n"
                )
                continue
            out.append(self.emit_clock(c))

        out.append(self.emit_ccu_clks())
        out.append(self.emit_hw_clks())
        out.append(self.emit_resets())
        out.append(self.emit_desc())
        out.append(self.emit_probe())

        return "".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate or report sun60i-a733 CCU output"
    )
    parser.add_argument(
        "--domain",
        choices=list(DOMAINS.keys()),
        default="main",
        help="CCU domain to generate (default: main)",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Print JSON metrics report to stderr",
    )
    parser.add_argument(
        "--no-output",
        action="store_true",
        help="Do not print generated C output",
    )
    args = parser.parse_args()

    domain = DOMAINS[args.domain]
    data_dir = Path(__file__).parent / "data"
    primary_path = domain.get("data_file") or (data_dir / f"ccu-{args.domain}.json")
    extracted_path = domain.get("extracted_file")
    binding_path = domain.get("binding_path")

    # Fallback for main domain legacy paths
    if args.domain == "main":
        primary_path = data_dir / "ccu-main.json"
        extracted_path = data_dir / "ccu-main-extracted.json"

    if not primary_path.exists():
        print(f"Error: {primary_path} not found", file=sys.stderr)
        return 1

    primary = load_json(primary_path)
    extracted = (
        load_json(extracted_path)
        if extracted_path and extracted_path.exists()
        else {"clocks": []}
    )
    binding_ids = parse_binding_ids(binding_path) if binding_path else set()
    merged = merge_data(primary, extracted, binding_ids)

    gen = Generator(merged, domain)
    rendered = gen.render()

    if not args.no_output:
        print(rendered, end="")

    if args.report:
        metrics = build_metrics(merged, gen)
        print(json.dumps(metrics, indent=2), file=sys.stderr)

    if gen.unsupported:
        print("[generate_ccu] Unsupported clock entries:", file=sys.stderr)
        for item in sorted(set(gen.unsupported)):
            print(f"  - {item}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
