"""
DT-binding constants extraction plugin for SSEE.

Extracts CLK_*, RST_*, and PD_* identifiers from dt-binding headers.
"""

import re
from typing import Dict, Optional

from generators.extractor import ExtractorPlugin


class DtBindingsExtractor(ExtractorPlugin):
    """Extract dt-binding #define constants from headers."""

    DEFINE_PATTERN = re.compile(r"#define\s+((?:CLK|RST|PD)_[A-Z0-9_]+)\s+\(?(\d+)")

    def can_extract(self, block: Dict) -> bool:
        if block.get("type") != "preprocessor":
            return False
        return self.DEFINE_PATTERN.search(block.get("content", "")) is not None

    def extract(self, block: Dict) -> Optional[Dict]:
        content = block.get("content", "")
        match = self.DEFINE_PATTERN.search(content)
        if not match:
            return None

        symbol = match.group(1)
        value = int(match.group(2))
        if symbol.startswith("CLK_"):
            domain = "clock"
        elif symbol.startswith("RST_"):
            domain = "reset"
        elif symbol.startswith("PD_"):
            domain = "power"
        else:
            domain = "unknown"

        return {"symbol": symbol, "value": value, "domain": domain}

    def validate(self, items: list) -> list:
        errors = []
        seen = {}
        for item in items:
            key = (item.get("domain"), item.get("value"))
            if key in seen:
                errors.append(
                    f"Duplicate {item.get('domain')} value {item.get('value')}: "
                    f"{seen[key]} and {item.get('symbol')}"
                )
            else:
                seen[key] = item.get("symbol")
        return errors

