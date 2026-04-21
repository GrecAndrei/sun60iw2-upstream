"""
Reset extraction plugin for the semantic extraction engine.

Extracts reset line definitions from vendor CCU drivers.
"""

import re
from typing import Dict, Optional
from generators.extractor import ExtractorPlugin


class ResetExtractor(ExtractorPlugin):
    """Extract reset definitions from vendor CCU drivers."""

    def __init__(self, semantic_map):
        super().__init__(semantic_map)

    def can_extract(self, block: Dict) -> bool:
        """Check if block contains reset definitions."""
        content = block.get("content", "")
        return "ccu_reset_map" in content or "RST_BUS_" in content

    def extract(self, block: Dict) -> Optional[Dict]:
        """Extract reset data from a block."""
        content = block.get("content", "")

        # Look for reset map entries like: [RST_BUS_UART0] = { 0x000, 0 },
        match = re.search(
            r"\[(RST_BUS_\w+)\]\s*=\s*\{\s*(0x[0-9a-fA-F]+)\s*,\s*(\d+)\s*\}", content
        )
        if match:
            return {
                "id": match.group(1),
                "reg": match.group(2),
                "bit": int(match.group(3)),
            }

        return None

    def validate(self, items: list) -> list:
        """Validate extracted reset items."""
        errors = []
        ids = set()

        for item in items:
            rid = item.get("id", "")
            if not rid.startswith("RST_BUS_"):
                errors.append(f"Reset ID doesn't follow naming convention: {rid}")
            if rid in ids:
                errors.append(f"Duplicate reset ID: {rid}")
            ids.add(rid)

        return errors
