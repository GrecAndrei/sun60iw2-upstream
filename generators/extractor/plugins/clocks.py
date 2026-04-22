"""
Clock extraction plugin for the semantic extraction engine.

Understands Allwinner CCU driver patterns and extracts structured
data about PLLs, dividers, gates, and fixed-factor clocks.
"""

import re
import ast
from typing import Dict, Optional
from generators.extractor import ExtractorPlugin


class ClockExtractor(ExtractorPlugin):
    """Extract clock definitions from vendor CCU drivers."""

    def __init__(self, semantic_map):
        super().__init__(semantic_map)
        self.macro_patterns = {
            r"static\s+struct\s+ccu_nm\s+": "pll_nm",
            r"static\s+struct\s+ccu_nkmp\s+": "pll_nkmp",
            r"static\s+SUNXI_CCU_M\s*\(": "divider",
            r"static\s+SUNXI_CCU_GATE\s*\(": "gate",
            r"static\s+SUNXI_CCU_GATE_HWS\s*\(": "gate",
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

        return None

    def _extract_struct_clock(self, content: str) -> Optional[Dict]:
        """Extract a PLL defined as a struct (ccu_nm, ccu_nkmp)."""
        # Detect type
        if "struct ccu_nm" in content:
            clk_type = "nm"
        elif "struct ccu_nkmp" in content:
            clk_type = "nkmp"
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

    def _extract_macro_clock(self, content: str) -> Optional[Dict]:
        """Extract a clock defined via macro."""
        # Flatten content
        flat = " ".join(content.split())

        # SUNXI_CCU_M - divider
        match = re.match(
            r'.*?SUNXI_CCU_M\s*\(\s*\w+\s*,\s*"([^"]+)"\s*,\s*("[^"]+"|\w+)\s*,\s*(0x[0-9a-fA-F]+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([\w\|\s]+)\s*\)',
            flat,
        )
        if match:
            parent = match.group(2).strip('"')
            return {
                "name": match.group(1),
                "type": "divider",
                "parent": parent,
                "reg": match.group(3),
                "shift": int(match.group(4)),
                "width": int(match.group(5)),
            }

        # SUNXI_CCU_GATE / SUNXI_CCU_GATE_HWS
        match = re.match(
            r'.*?SUNXI_CCU_GATE(?:_HWS)?\s*\(\s*\w+\s*,\s*"([^"]+)"\s*,\s*("[^"]+"|\w+)\s*,\s*(0x[0-9a-fA-F]+)\s*,\s*([^,]+)\s*,\s*([\w\|\s]+)\s*\)',
            flat,
        )
        if match:
            parent = match.group(2).strip('"')
            bit_raw = match.group(4).strip()
            bit = self._parse_bit(bit_raw)
            return {
                "name": match.group(1),
                "type": "gate",
                "parent": parent,
                "reg": match.group(3),
                **({"bit": bit} if bit is not None else {"bit_expr": bit_raw}),
            }

        # CLK_FIXED_FACTOR
        match = re.match(
            r'.*?CLK_FIXED_FACTOR\s*\(\s*\w+\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)',
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

    def _parse_bit(self, value: str) -> Optional[int]:
        value = value.strip()
        if value.isdigit():
            return int(value)
        bit_match = re.match(r"BIT\s*\((.+)\)", value)
        if bit_match:
            return self._safe_eval_int(bit_match.group(1))
        return self._safe_eval_int(value)

    def _safe_eval_int(self, expression: str) -> Optional[int]:
        expression = expression.strip()
        if not expression:
            return None
        try:
            node = ast.parse(expression, mode="eval")
        except SyntaxError:
            return None
        if not self._is_safe_int_ast(node):
            return None
        try:
            return int(self._eval_safe_int_node(node.body))
        except Exception:
            return None

    def _is_safe_int_ast(self, node: ast.AST) -> bool:
        allowed = (
            ast.Expression,
            ast.BinOp,
            ast.UnaryOp,
            ast.Add,
            ast.Sub,
            ast.Mult,
            ast.Div,
            ast.FloorDiv,
            ast.Mod,
            ast.LShift,
            ast.RShift,
            ast.BitAnd,
            ast.BitOr,
            ast.BitXor,
            ast.USub,
            ast.UAdd,
            ast.Constant,
        )
        return all(isinstance(n, allowed) for n in ast.walk(node))

    def _eval_safe_int_node(self, node: ast.AST) -> int:
        if isinstance(node, ast.Constant):
            if not isinstance(node.value, int):
                raise ValueError("Unsupported constant type")
            return int(node.value)
        if isinstance(node, ast.UnaryOp):
            operand = self._eval_safe_int_node(node.operand)
            if isinstance(node.op, ast.USub):
                return -operand
            if isinstance(node.op, ast.UAdd):
                return operand
            raise ValueError("Unsupported unary operator")
        if isinstance(node, ast.BinOp):
            left = self._eval_safe_int_node(node.left)
            right = self._eval_safe_int_node(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, (ast.Div, ast.FloorDiv)):
                if right == 0:
                    raise ValueError("Division by zero")
                return left // right
            if isinstance(node.op, ast.Mod):
                if right == 0:
                    raise ValueError("Modulo by zero")
                return left % right
            if isinstance(node.op, ast.LShift):
                return left << right
            if isinstance(node.op, ast.RShift):
                return left >> right
            if isinstance(node.op, ast.BitAnd):
                return left & right
            if isinstance(node.op, ast.BitOr):
                return left | right
            if isinstance(node.op, ast.BitXor):
                return left ^ right
            raise ValueError("Unsupported binary operator")
        raise ValueError("Unsupported AST node")

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
