"""
Clock extraction plugin for the semantic extraction engine.

Understands Allwinner CCU driver patterns and extracts structured
data about PLLs, dividers, gates, and fixed-factor clocks.
"""

import re
from typing import Dict, Optional
from generators.extractor import ExtractorPlugin


class ClockExtractor(ExtractorPlugin):
    """Extract clock definitions from vendor CCU drivers."""

    def __init__(self, semantic_map):
        super().__init__(semantic_map)
        self.macro_patterns = {
            r"static\s+struct\s+ccu_nm\s+": "pll_nm",
            r"static\s+struct\s+ccu_nkmp\s+": "pll_nkmp",
            r"static\s+struct\s+ccu_div\s+": "struct_divider",
            r"static\s+struct\s+ccu_gate\s+": "struct_gate",
            r"static\s+struct\s+ccu_mux\s+": "struct_mux",
            r"SUNXI_CCU_M_WITH_MUX_GATE_KEY\s*\(": "mux_divider_gate_key",
            r"SUNXI_CCU_M_WITH_MUX_GATE\s*\(": "mux_divider_gate",
            r"SUNXI_CCU_M_WITH_MUX\s*\(": "mux_divider",
            r"SUNXI_CCU_MUX_WITH_GATE_KEY\s*\(": "mux_gate_key",
            r"SUNXI_CCU_MUX_WITH_GATE\s*\(": "mux_gate",
            r"SUNXI_CCU_MP_WITH_MUX_GATE_NO_INDEX\s*\(": "mp_mux_gate_no_index",
            r"SUNXI_CCU_GATE_WITH_KEY\s*\(": "gate_with_key",
            r"SUNXI_CCU_GATE_WITH_FIXED_RATE\s*\(": "gate_with_fixed_rate",
            r"SUNXI_CCU_MUX\s*\(": "mux",
            r"static\s+SUNXI_CCU_M\s*\(": "divider",
            r"static\s+SUNXI_CCU_GATE\s*\(": "gate",
            r"static\s+CLK_FIXED_FACTOR\s*\(": "fixed_factor",
        }

    def can_extract(self, block: Dict) -> bool:
        """Check if block contains a clock definition."""
        if block.get("type") not in ("struct", "macro"):
            return False

        content = block.get("content", "")
        for pattern in self.macro_patterns:
            if re.search(pattern, content):
                return True
        return False

    def extract(self, block: Dict) -> Optional[Dict]:
        """Extract clock data from a block."""
        content = block.get("content", "")
        block_type = block.get("type")

        if block_type == "struct":
            return self._extract_struct_clock(content)
        elif block_type == "macro":
            return self._extract_macro_clock(content)
        elif block_type == "parent_array":
            return None

        return None

    def _extract_struct_clock(self, content: str) -> Optional[Dict]:
        """Extract a PLL defined as a struct (ccu_nm, ccu_nkmp)."""
        # Detect type
        if "struct ccu_nm" in content:
            clk_type = "nm"
        elif "struct ccu_nkmp" in content:
            clk_type = "nkmp"
        elif "struct ccu_div" in content:
            return self._extract_struct_div_clock(content)
        elif "struct ccu_gate" in content:
            return self._extract_struct_gate_clock(content)
        else:
            return None

        # Extract variable name
        var_match = re.search(r"struct\s+\w+\s+(\w+)\s*=", content)
        if not var_match:
            return None

        name = var_match.group(1).replace("_clk", "").replace("_", "-")

        # Extract register
        reg_match = re.search(r"\.reg\s*=\s*(0x[0-9a-fA-F]+)", content)
        reg = reg_match.group(1) if reg_match else "0x000"

        # Extract parent from CLK_HW_INIT
        parent_match = re.search(r'CLK_HW_INIT\s*\(\s*"[^"]+",\s*"([^"]+)"', content)
        parent = parent_match.group(1) if parent_match else "osc24M"

        return {
            "name": name,
            "type": clk_type,
            "reg": reg,
            "parent": parent,
        }

    def _extract_struct_gate_clock(self, content: str) -> Optional[Dict]:
        """Extract a gate clock defined as struct ccu_gate."""
        clk_name_match = re.search(
            r'CLK_HW_INIT\s*\(\s*"([^"]+)"\s*,\s*"([^"]+)"', content
        )
        reg_match = re.search(r"\.reg\s*=\s*(0x[0-9a-fA-F]+)", content)
        bit_match = re.search(r"\.enable\s*=\s*BIT\((\d+)\)", content)
        key_match = re.search(r"\.key_value\s*=\s*([A-Z_0-9]+)", content)
        key_reg_match = re.search(r"\.key_reg\s*=\s*(0x[0-9a-fA-F]+)", content)
        features_match = re.search(r"\.features\s*=\s*([A-Z_0-9_|\s]+)", content)

        if not clk_name_match:
            return None

        item = {
            "name": clk_name_match.group(1),
            "type": "gate",
            "parent": clk_name_match.group(2),
        }
        if reg_match:
            item["reg"] = reg_match.group(1)
        if bit_match:
            item["bit"] = int(bit_match.group(1))
        if key_match:
            item["key_value"] = key_match.group(1)
        if key_reg_match:
            item["key_reg"] = key_reg_match.group(1)
        if features_match:
            feats = [f.strip() for f in features_match.group(1).split("|")]
            item["features"] = feats

        return item

    def _extract_struct_div_clock(self, content: str) -> Optional[Dict]:
        """Extract a divider/mux clock defined as struct ccu_div."""
        name_match = re.search(r"static\s+struct\s+ccu_div\s+(\w+)\s*=", content)
        clk_name_match = re.search(
            r'CLK_HW_INIT_PARENTS\s*\(\s*"([^"]+)"\s*,\s*(\w+_parents)',
            content,
        )
        reg_match = re.search(r"\.reg\s*=\s*(0x[0-9a-fA-F]+)", content)
        if not (name_match and clk_name_match and reg_match):
            return None

        item = {
            "name": clk_name_match.group(1),
            "type": "mux_divider",
            "parents_array": clk_name_match.group(2),
            "reg": reg_match.group(1),
        }

        mux_match = re.search(
            r"\.mux\s*=\s*_SUNXI_CCU_MUX\((\d+)\s*,\s*(\d+)\)", content
        )
        if mux_match:
            item["mux_shift"] = int(mux_match.group(1))
            item["mux_width"] = int(mux_match.group(2))

        div_match = re.search(
            r"\.div\s*=\s*_SUNXI_CCU_DIV(?:_FLAGS|_TABLE)?\((\d+)\s*,\s*(\d+)",
            content,
        )
        if div_match:
            item["div_shift"] = int(div_match.group(1))
            item["div_width"] = int(div_match.group(2))

        key_match = re.search(r"\.key_value\s*=\s*([A-Z_0-9]+)", content)
        if key_match:
            item["key_value"] = key_match.group(1)

        return item

    def _strip_comments(self, text: str) -> str:
        """Remove C-style comments from text."""
        # Remove /* ... */ comments
        text = re.sub(r"/\*.*?\*/", " ", text, flags=re.DOTALL)
        # Remove // comments
        text = re.sub(r"//.*", " ", text)
        return text

    def _extract_macro_clock(self, content: str) -> Optional[Dict]:
        """Extract a clock defined via macro."""
        content_no_comments = self._strip_comments(content)
        flat = " ".join(content_no_comments.split())

        # IMPORTANT: Try most specific patterns FIRST to avoid partial matches.
        # SUNXI_CCU_M_WITH_MUX_GATE_KEY must come before GATE, which must come before MUX.

        # SUNXI_CCU_M_WITH_MUX_GATE_KEY - mux + divider + gate with key
        match = re.match(
            r'.*?SUNXI_CCU_M_WITH_MUX_GATE_KEY\s*\(\s*\w+\s*,\s*"([^"]+)"\s*,\s*(\w+_parents)\s*,\s*(0x[0-9a-fA-F]+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(?:BIT\s*\()?([\d]+)\s*\)?\s*,\s*(\d+)\s*,\s*([A-Z_0-9]+)\s*\)',
            flat,
        )
        if match:
            return {
                "name": match.group(1),
                "type": "mux_divider_gate_key",
                "parents_array": match.group(2),
                "reg": match.group(3),
                "mux_shift": int(match.group(4)),
                "mux_width": int(match.group(5)),
                "div_shift": int(match.group(6)),
                "div_width": int(match.group(7)),
                "gate_bit": int(match.group(8)),
            }

        # SUNXI_CCU_MUX_WITH_GATE_KEY - mux + gate with key register
        match = re.match(
            r'.*?SUNXI_CCU_MUX_WITH_GATE_KEY\s*\(\s*\w+\s*,\s*"([^"]+)"\s*,\s*(\w+_parents)\s*,\s*(0x[0-9a-fA-F]+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([A-Z_0-9]+)\s*,\s*(?:BIT\s*\()?([\d]+)\)?\s*,\s*([A-Z_0-9]+)\s*\)',
            flat,
        )
        if match:
            return {
                "name": match.group(1),
                "type": "mux_gate_key",
                "parents_array": match.group(2),
                "reg": match.group(3),
                "mux_shift": int(match.group(4)),
                "mux_width": int(match.group(5)),
                "key_value": match.group(6),
                "gate_bit": int(match.group(7)),
            }

        # SUNXI_CCU_GATE_WITH_FIXED_RATE - gate with fixed output rate
        match = re.match(
            r'.*?SUNXI_CCU_GATE_WITH_FIXED_RATE\s*\(\s*\w+\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*(0x[0-9a-fA-F]+)\s*,\s*(\d+)\s*,\s*BIT\s*\(?([\d]+)\)?\s*\)',
            flat,
        )
        if match:
            return {
                "name": match.group(1),
                "type": "gate_with_fixed_rate",
                "parent": match.group(2),
                "reg": match.group(3),
                "rate": int(match.group(4)),
                "bit": int(match.group(5)),
            }

        # SUNXI_CCU_GATE_WITH_KEY - gate with key register
        match = re.match(
            r'.*?SUNXI_CCU_GATE_WITH_KEY\s*\(\s*\w+\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*(0x[0-9a-fA-F]+)\s*,\s*([A-Z_0-9]+)\s*,\s*BIT\s*\(?([\d]+)\)?\s*,\s*([A-Z_0-9]+)\s*\)',
            flat,
        )
        if match:
            return {
                "name": match.group(1),
                "type": "gate_with_key",
                "parent": match.group(2),
                "reg": match.group(3),
                "key_value": match.group(4),
                "bit": int(match.group(5)),
            }

        # SUNXI_CCU_MUX_WITH_GATE - mux + gate
        match = re.match(
            r'.*?SUNXI_CCU_MUX_WITH_GATE\s*\(\s*\w+\s*,\s*"([^"]+)"\s*,\s*(\w+_parents)\s*,\s*(0x[0-9a-fA-F]+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(?:BIT\s*\()?([\d]+)\)?\s*,\s*([A-Z_0-9]+)\s*\)',
            flat,
        )
        if match:
            return {
                "name": match.group(1),
                "type": "mux_gate",
                "parents_array": match.group(2),
                "reg": match.group(3),
                "mux_shift": int(match.group(4)),
                "mux_width": int(match.group(5)),
                "gate_bit": int(match.group(6)),
            }

        # SUNXI_CCU_MP_WITH_MUX_GATE_NO_INDEX - mux + M/N divider + gate
        match = re.match(
            r'.*?SUNXI_CCU_MP_WITH_MUX_GATE_NO_INDEX\s*\(\s*\w+\s*,\s*"([^"]+)"\s*,\s*(\w+_parents)\s*,\s*(0x[0-9a-fA-F]+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(?:BIT\s*\()?([\d]+)\)?\s*,\s*([A-Z_0-9\s|]+)\s*\)',
            flat,
        )
        if match:
            return {
                "name": match.group(1),
                "type": "mp_mux_gate_no_index",
                "parents_array": match.group(2),
                "reg": match.group(3),
                "m_shift": int(match.group(4)),
                "m_width": int(match.group(5)),
                "n_shift": int(match.group(6)),
                "n_width": int(match.group(7)),
                "mux_shift": int(match.group(8)),
                "mux_width": int(match.group(9)),
                "gate_bit": int(match.group(10)),
            }

        # SUNXI_CCU_MUX - mux only
        match = re.match(
            r'.*?SUNXI_CCU_MUX\s*\(\s*\w+\s*,\s*"([^"]+)"\s*,\s*(\w+_parents)\s*,\s*(0x[0-9a-fA-F]+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([A-Z_0-9\s|]+)\s*\)',
            flat,
        )
        if match:
            return {
                "name": match.group(1),
                "type": "mux",
                "parents_array": match.group(2),
                "reg": match.group(3),
                "mux_shift": int(match.group(4)),
                "mux_width": int(match.group(5)),
                "flags": match.group(6).strip(),
            }

        # static struct ccu_div - divider with mux and optional table
        if "struct ccu_div" in content:
            name_match = re.search(r"static\s+struct\s+ccu_div\s+(\w+)\s*=", content)
            clk_name_match = re.search(
                r'CLK_HW_INIT_PARENTS\s*\(\s*"([^"]+)"\s*,\s*(\w+_parents)', content
            )
            reg_match = re.search(r"\.reg\s*=\s*(0x[0-9a-fA-F]+)", content)
            if name_match and clk_name_match and reg_match:
                item = {
                    "name": clk_name_match.group(1),
                    "type": "div_mux",
                    "parents_array": clk_name_match.group(2),
                    "reg": reg_match.group(1),
                }
                mux_match = re.search(
                    r"\.mux\s*=\s*_SUNXI_CCU_MUX\((\d+)\s*,\s*(\d+)\)", content
                )
                if mux_match:
                    item["mux_shift"] = int(mux_match.group(1))
                    item["mux_width"] = int(mux_match.group(2))
                div_match = re.search(
                    r"\.div\s*=\s*_SUNXI_CCU_DIV(?:_FLAGS|_TABLE)?\((\d+)\s*,\s*(\d+)",
                    content,
                )
                if div_match:
                    item["div_shift"] = int(div_match.group(1))
                    item["div_width"] = int(div_match.group(2))
                return item

        # static struct ccu_gate - simple gate with a struct wrapper
        if "struct ccu_gate" in content:
            clk_name_match = re.search(
                r'CLK_HW_INIT\s*\(\s*"([^"]+)"\s*,\s*"([^"]+)"', content
            )
            reg_match = re.search(r"\.reg\s*=\s*(0x[0-9a-fA-F]+)", content)
            bit_match = re.search(r"\.enable\s*=\s*BIT\((\d+)\)|BIT\((\d+)\)", content)
            if clk_name_match and reg_match:
                bit = None
                if bit_match:
                    bit = int(bit_match.group(1) or bit_match.group(2))
                return {
                    "name": clk_name_match.group(1),
                    "type": "gate",
                    "parent": clk_name_match.group(2),
                    "reg": reg_match.group(1),
                    **({"bit": bit} if bit is not None else {}),
                }

        # SUNXI_CCU_M_WITH_MUX_GATE - mux + divider + gate
        match = re.match(
            r'.*?SUNXI_CCU_M_WITH_MUX_GATE\s*\(\s*\w+\s*,\s*"([^"]+)"\s*,\s*(\w+_parents)\s*,\s*(0x[0-9a-fA-F]+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(?:BIT\s*\()?([\d]+)\s*\)?\s*,\s*([A-Z_0-9\s|]+)\s*\)',
            flat,
        )
        if match:
            return {
                "name": match.group(1),
                "type": "mux_divider_gate",
                "parents_array": match.group(2),
                "reg": match.group(3),
                "mux_shift": int(match.group(4)),
                "mux_width": int(match.group(5)),
                "div_shift": int(match.group(6)),
                "div_width": int(match.group(7)),
                "gate_bit": int(match.group(8)),
            }

        # SUNXI_CCU_M_WITH_MUX - divider with parent mux
        match = re.match(
            r'.*?SUNXI_CCU_M_WITH_MUX\s*\(\s*\w+\s*,\s*"([^"]+)"\s*,\s*(\w+_parents)\s*,\s*(0x[0-9a-fA-F]+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([A-Z_0-9\s|]+)\s*\)',
            flat,
        )
        if match:
            return {
                "name": match.group(1),
                "type": "mux_divider",
                "parents_array": match.group(2),
                "reg": match.group(3),
                "mux_shift": int(match.group(4)),
                "mux_width": int(match.group(5)),
                "div_shift": int(match.group(6)),
                "div_width": int(match.group(7)),
            }

        # SUNXI_CCU_M - divider (flags can be numeric or macro)
        match = re.match(
            r'.*?SUNXI_CCU_M\s*\(\s*\w+\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*(0x[0-9a-fA-F]+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([A-Z_0-9\s|]+)\s*\)',
            flat,
        )
        if match:
            return {
                "name": match.group(1),
                "type": "divider",
                "parent": match.group(2),
                "reg": match.group(3),
                "shift": int(match.group(4)),
                "width": int(match.group(5)),
            }

        # SUNXI_CCU_GATE (flags can be numeric or macro)
        match = re.match(
            r'.*?SUNXI_CCU_GATE\s*\(\s*\w+\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*(0x[0-9a-fA-F]+)\s*,\s*(?:BIT\s*\()?([\d]+)\s*\)?\s*,\s*([A-Z_0-9\s|]+)\s*\)',
            flat,
        )
        if match:
            return {
                "name": match.group(1),
                "type": "gate",
                "parent": match.group(2),
                "reg": match.group(3),
                "bit": int(match.group(4)),
            }

        # SUNXI_CCU_GATE_WITH_KEY can also appear in a compact 6-arg form.
        match = re.match(
            r'.*?SUNXI_CCU_GATE_WITH_KEY\s*\(\s*\w+\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*(0x[0-9a-fA-F]+)\s*,\s*([A-Z_0-9]+)\s*,\s*(?:BIT\s*\()?([\d]+)\s*\)?\s*,\s*([A-Z_0-9]+)\s*\)',
            flat,
        )
        if match:
            return {
                "name": match.group(1),
                "type": "gate_with_key",
                "parent": match.group(2),
                "reg": match.group(3),
                "key_value": match.group(4),
                "bit": int(match.group(5)),
            }

        # CLK_FIXED_FACTOR (flags can be numeric or macro)
        match = re.match(
            r'.*?CLK_FIXED_FACTOR\s*\(\s*\w+\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([A-Z_0-9]+)\s*\)',
            flat,
        )
        if match:
            return {
                "name": match.group(1),
                "type": "fixed_factor",
                "parent": match.group(2),
                "mult": int(match.group(3)),
                "div": int(match.group(4)),
            }

        return None

    def validate(self, items: list) -> list:
        """Validate extracted clock items."""
        errors = []
        names = set()

        for item in items:
            name = item.get("name", "")

            if not name:
                errors.append(f"Clock item missing name: {item}")
                continue

            if name in names:
                errors.append(f"Duplicate clock name: {name}")
            names.add(name)

            clk_type = item.get("type", "")
            if clk_type == "gate" and "parent" not in item:
                errors.append(f"Gate clock '{name}' missing parent")
            elif clk_type in ("nm", "nkmp") and "reg" not in item:
                errors.append(f"PLL '{name}' missing register offset")

        return errors
