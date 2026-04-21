"""
Register extraction plugin for the semantic extraction engine.

Extracts register offsets and memory addresses from vendor headers.
"""

import re
from typing import Dict, Optional
from generators.extractor import ExtractorPlugin


class RegisterExtractor(ExtractorPlugin):
    """Extract register definitions from vendor headers."""

    def __init__(self, semantic_map):
        super().__init__(semantic_map)

    def can_extract(self, block: Dict) -> bool:
        """Check if block is a register #define."""
        if block.get("type") != "preprocessor":
            return False
        content = block.get("content", "")
        return re.match(r"#define\s+\w+_REG\s+0x", content) is not None

    def extract(self, block: Dict) -> Optional[Dict]:
        """Extract register data from a block."""
        content = block.get("content", "")

        match = re.match(r"#define\s+(\w+)_REG\s+(0x[0-9a-fA-F]+)", content)
        if match:
            return {
                "name": match.group(1),
                "offset": match.group(2),
                "type": "register",
            }

        # Also catch base address defines
        match = re.match(r"#define\s+(\w+_BASE)\s+(0x[0-9a-fA-F]+)", content)
        if match:
            return {
                "name": match.group(1),
                "address": match.group(2),
                "type": "base_address",
            }

        return None

    def validate(self, items: list) -> list:
        """Validate extracted register items."""
        errors = []
        offsets = set()

        for item in items:
            if item.get("type") == "register":
                offset = item.get("offset", "")
                if offset in offsets:
                    errors.append(
                        f"Duplicate register offset: {item.get('name')} = {offset}"
                    )
                offsets.add(offset)

        return errors
