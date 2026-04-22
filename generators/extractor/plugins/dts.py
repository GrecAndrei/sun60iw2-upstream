"""
Device Tree extraction plugin for SSEE.

Extracts node-level metadata from DTS/DTSI blocks to support bringup audits.
"""

import re
from typing import Dict, Optional

from generators.extractor import ExtractorPlugin


class DtsExtractor(ExtractorPlugin):
    """Extract DTS node metadata."""

    NODE_HEADER = re.compile(r"^\s*(?:(\w+)\s*:\s*)?([A-Za-z0-9,_-]+)(?:@([0-9a-fA-Fx]+))?\s*\{")
    OVERLAY_HEADER = re.compile(r"^\s*&(\w+)\s*\{")

    def can_extract(self, block: Dict) -> bool:
        return block.get("type") == "dts_node"

    def extract(self, block: Dict) -> Optional[Dict]:
        content = block.get("content", "")
        lines = content.splitlines()
        if not lines:
            return None

        header = lines[0]
        overlay_match = self.OVERLAY_HEADER.match(header)
        if overlay_match:
            target = overlay_match.group(1)
            status_match = re.search(r'status\s*=\s*"([^"]+)"', content)
            return {
                "node": f"&{target}",
                "label": target,
                "name": target,
                "unit_addr": "",
                "compatible": "",
                "status": status_match.group(1) if status_match else "",
                "clocks_refs": 0,
                "resets_refs": 0,
                "overlay": True,
            }

        match = self.NODE_HEADER.match(header)
        if not match:
            return None

        label = match.group(1)
        node_name = match.group(2)
        unit_addr = match.group(3)

        compatible_match = re.search(r'compatible\s*=\s*"([^"]+)"', content)
        status_match = re.search(r'status\s*=\s*"([^"]+)"', content)
        clocks_count = len(re.findall(r"&\w+", re.search(r"clocks\s*=\s*([^;]+);", content, re.S).group(1))) if re.search(r"clocks\s*=\s*([^;]+);", content, re.S) else 0
        resets_count = len(re.findall(r"&\w+", re.search(r"resets\s*=\s*([^;]+);", content, re.S).group(1))) if re.search(r"resets\s*=\s*([^;]+);", content, re.S) else 0

        return {
            "node": f"{node_name}@{unit_addr}" if unit_addr else node_name,
            "label": label or "",
            "name": node_name,
            "unit_addr": unit_addr or "",
            "compatible": compatible_match.group(1) if compatible_match else "",
            "status": status_match.group(1) if status_match else "",
            "clocks_refs": clocks_count,
            "resets_refs": resets_count,
        }

    def validate(self, items: list) -> list:
        errors = []
        seen = set()
        for item in items:
            node = item.get("node", "")
            if node in seen:
                errors.append(f"Duplicate DTS node: {node}")
            seen.add(node)
        return errors
