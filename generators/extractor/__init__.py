#!/usr/bin/env python3
"""
Sunxi Semantic Extraction Engine (SSEE)

A modular, self-improving code extraction tool for Allwinner BSP sources.
Understands C code semantically rather than just pattern matching.

Architecture:
- Core parser: Tokenizes and builds AST-like blocks from vendor C
- Semantic Map: Knowledge base of what patterns mean
- Plugin Registry: Modular extractors per subsystem
- Validation: Cross-checks extracted data against known constraints
- Learning: Tracks failed extractions for pattern improvement

Usage:
    from generators.extractor import Engine
    engine = Engine()
    engine.load_semantic_map('generators/extractor/data/semantic_map.json')

    # Extract clocks
    result = engine.extract('clocks', source_file='vendor/ccu-sun60iw2.c')

    # Extract with validation
    result = engine.extract('clocks', validate=True)
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class ExtractionResult:
    """Result from a single extraction run."""

    subsystem: str
    items: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    raw_blocks: List[str] = field(default_factory=list)

    def merge(self, other: "ExtractionResult"):
        """Merge another result into this one."""
        self.items.extend(other.items)
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.raw_blocks.extend(other.raw_blocks)
        self.confidence = (self.confidence + other.confidence) / 2


class SemanticMap:
    """
    Persistent knowledge base of what C patterns mean in sunxi drivers.

    This is the BRAIN of the extraction engine. It lives on disk,
    learns from every extraction run, and grows smarter over time.

    Sections:
    - macros: Signatures for each SUNXI_* macro
    - types: Mapping from C types to semantic types
    - validation_rules: Constraints extracted data must satisfy
    - relationships: Clock/pin parent-child hierarchies
    - learned_patterns: Patterns discovered from failed extractions
    - vendor_history: Which vendor files were processed and when
    """

    DEFAULT_PATH = Path(__file__).parent / "data" / "semantic_map.json"

    def __init__(self, map_path: Optional[Path] = None):
        self._path = map_path or self.DEFAULT_PATH
        self.macros: Dict[str, Dict] = {}
        self.types: Dict[str, str] = {}
        self.validation_rules: List[Dict] = []
        self.relationships: Dict[str, List[str]] = {}
        self.learned_patterns: List[Dict] = []
        self.vendor_history: Dict[str, Dict] = {}

        if self._path.exists():
            self.load(self._path)
        else:
            self._init_defaults()
            self.save(self._path)

    def _init_defaults(self):
        """Initialize with default sunxi knowledge."""
        self.macros = {
            "SUNXI_CCU_M": {
                "type": "divider",
                "args": [
                    "var_name",
                    "clock_name",
                    "parent",
                    "reg",
                    "shift",
                    "width",
                    "flags",
                ],
                "creates": "ccu_div",
            },
            "SUNXI_CCU_GATE": {
                "type": "gate",
                "args": ["var_name", "clock_name", "parent", "reg", "bit", "flags"],
                "creates": "ccu_gate",
            },
            "CLK_FIXED_FACTOR": {
                "type": "fixed_factor",
                "args": ["var_name", "clock_name", "parent", "mult", "div", "flags"],
                "creates": "clk_fixed_factor",
            },
            "ccu_nm": {
                "type": "pll",
                "args": [],
                "creates": "ccu_nm",
                "fields": [
                    ".enable",
                    ".lock",
                    ".n",
                    ".m",
                    ".common.reg",
                    ".common.hw.init",
                ],
            },
            "ccu_nkmp": {
                "type": "pll",
                "args": [],
                "creates": "ccu_nkmp",
                "fields": [
                    ".enable",
                    ".lock",
                    ".n",
                    ".k",
                    ".m",
                    ".p",
                    ".common.reg",
                ],
            },
        }

        self.types = {
            "ccu_nm": "pll",
            "ccu_nkmp": "pll",
            "ccu_div": "divider",
            "ccu_gate": "gate",
            "clk_fixed_factor": "fixed_factor",
            "SUNXI_CCU_M": "divider",
            "SUNXI_CCU_GATE": "gate",
            "CLK_FIXED_FACTOR": "fixed_factor",
        }

        self.validation_rules = [
            {"rule": "all_clocks_have_name", "check": "name in item"},
            {
                "rule": "gates_have_parent",
                "check": "type == 'gate' implies 'parent' in item",
            },
            {"rule": "plls_have_reg", "check": "type == 'pll' implies 'reg' in item"},
            {"rule": "names_unique", "check": "all names are unique"},
        ]

    def load(self, path: Path):
        """Load semantic map from JSON on disk."""
        with open(path) as f:
            data = json.load(f)
        self.macros = data.get("macros", {})
        self.types = data.get("types", {})
        self.validation_rules = data.get("validation_rules", [])
        self.relationships = data.get("relationships", {})
        self.learned_patterns = data.get("learned_patterns", [])
        self.vendor_history = data.get("vendor_history", {})

    def save(self, path: Optional[Path] = None):
        """Save semantic map to JSON on disk."""
        save_path = path or self._path
        data = {
            "macros": self.macros,
            "types": self.types,
            "validation_rules": self.validation_rules,
            "relationships": self.relationships,
            "learned_patterns": self.learned_patterns,
            "vendor_history": self.vendor_history,
        }
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w") as f:
            json.dump(data, f, indent=2)

    def record_vendor_run(self, filepath: Path, stats: Dict):
        """Record that we processed a vendor file."""
        import hashlib

        content = filepath.read_bytes()
        checksum = hashlib.sha256(content).hexdigest()[:16]
        self.vendor_history[str(filepath)] = {
            "checksum": checksum,
            "last_run": str(__import__("time").time()),
            "stats": stats,
        }
        self.save()

    def add_learned_pattern(self, raw_block: str, expected: Dict, context: str = ""):
        """Add a pattern learned from manual correction."""
        import hashlib

        block_hash = hashlib.sha256(raw_block.encode()).hexdigest()[:16]
        self.learned_patterns.append(
            {
                "hash": block_hash,
                "context": context,
                "raw_preview": raw_block[:200],
                "expected": expected,
            }
        )
        self.save()

    def has_seen_vendor(self, filepath: Path) -> bool:
        """Check if we've already processed this vendor file."""
        return str(filepath) in self.vendor_history

    def resolve_type(self, pattern: str) -> Optional[str]:
        """Resolve a C pattern to its semantic type."""
        return self.types.get(pattern)

    def get_macro_signature(self, macro_name: str) -> Optional[Dict]:
        """Get the argument signature for a macro."""
        return self.macros.get(macro_name)


class CBlockParser:
    """
    Parses C source into semantic blocks.

    Handles:
    - Multi-line struct definitions
    - Multi-line macro invocations
    - Block comments
    - Preprocessor directives
    """

    def __init__(self):
        self.blocks: List[Dict] = []

    def parse_file(self, filepath: Path) -> List[Dict]:
        """Parse a C file into blocks."""
        with open(filepath) as f:
            content = f.read()
        return self.parse(content)

    def parse(self, content: str) -> List[Dict]:
        """Parse C content into structured blocks."""
        blocks = []
        lines = content.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines and single-line comments
            if not line or line.startswith("//"):
                i += 1
                continue

            # Multi-line comment
            if line.startswith("/*"):
                comment_block, i = self._extract_multiline_comment(lines, i)
                blocks.append({"type": "comment", "content": comment_block})
                continue

            # Preprocessor directive
            if line.startswith("#"):
                blocks.append({"type": "preprocessor", "content": line})
                i += 1
                continue

            # Struct definition
            if "struct " in line and "{" in line:
                struct_block, i = self._extract_struct(lines, i)
                blocks.append(struct_block)
                continue

            # Static variable with macro
            if line.startswith("static "):
                macro_block, i = self._extract_macro_invocation(lines, i)
                if macro_block:
                    blocks.append(macro_block)
                continue

            i += 1

        self.blocks = blocks
        return blocks

    def _extract_multiline_comment(self, lines, start_idx):
        """Extract a /* ... */ comment block."""
        block = []
        i = start_idx
        while i < len(lines):
            block.append(lines[i])
            if "*/" in lines[i]:
                break
            i += 1
        return "\n".join(block), i + 1

    def _extract_struct(self, lines, start_idx):
        """Extract a struct definition block."""
        block_lines = []
        brace_count = 0
        i = start_idx
        var_name = None

        # Get variable name from first line
        first_line = lines[i]
        var_match = re.search(r"(\w+)\s*=", first_line)
        if var_match:
            var_name = var_match.group(1)

        while i < len(lines):
            line = lines[i]
            block_lines.append(line)
            brace_count += line.count("{") - line.count("}")

            if brace_count == 0 and "{" in "".join(block_lines):
                break
            i += 1

        # Check for semicolon termination
        while i < len(lines) and ";" not in lines[i]:
            block_lines.append(lines[i])
            i += 1

        if i < len(lines):
            block_lines.append(lines[i])

        content = "\n".join(block_lines)

        return {
            "type": "struct",
            "var_name": var_name,
            "content": content,
            "raw": content,
        }, i + 1

    def _extract_macro_invocation(self, lines, start_idx):
        """Extract a multi-line macro invocation."""
        block_lines = []
        i = start_idx
        paren_depth = 0

        while i < len(lines):
            line = lines[i]
            block_lines.append(line)

            for char in line:
                if char == "(":
                    paren_depth += 1
                elif char == ")":
                    paren_depth -= 1

            # Check if macro ends with );
            if paren_depth == 0 and ");" in line:
                break
            i += 1

        content = "\n".join(block_lines)

        # Detect macro name
        macro_match = re.search(r"static\s+\w+\s*\(\s*(\w+)", content)
        if not macro_match:
            macro_match = re.search(r"static\s+(\w+)\s*\(", content)

        macro_name = macro_match.group(1) if macro_match else "unknown"

        return {
            "type": "macro",
            "macro_name": macro_name,
            "content": content,
            "raw": content,
        }, i + 1


class PluginRegistry:
    """Registry of extraction plugins."""

    def __init__(self):
        self.plugins: Dict[str, "ExtractorPlugin"] = {}

    def register(self, name: str, plugin: "ExtractorPlugin"):
        """Register a plugin."""
        self.plugins[name] = plugin

    def get(self, name: str) -> Optional["ExtractorPlugin"]:
        """Get a plugin by name."""
        return self.plugins.get(name)

    def list_plugins(self) -> List[str]:
        """List all registered plugins."""
        return list(self.plugins.keys())


class ExtractorPlugin:
    """Base class for extraction plugins."""

    def __init__(self, semantic_map: SemanticMap):
        self.semantic_map = semantic_map
        self.confidence_threshold = 0.8

    def can_extract(self, block: Dict) -> bool:
        """Check if this plugin can extract from the given block."""
        raise NotImplementedError

    def extract(self, block: Dict) -> Optional[Dict]:
        """Extract structured data from a block."""
        raise NotImplementedError

    def validate(self, items: List[Dict]) -> List[str]:
        """Validate extracted items."""
        return []


class Engine:
    """
    Main extraction engine.

    Coordinates parsing, plugin execution, validation, and learning.
    The semantic map is ALWAYS loaded from disk and saved back after runs.
    """

    def __init__(self):
        # Always load from disk so knowledge persists across runs
        self.semantic_map = SemanticMap()
        self.parser = CBlockParser()
        self.registry = PluginRegistry()

        # Load built-in plugins
        self._load_plugins()

    def _load_plugins(self):
        """Load built-in extraction plugins."""
        from generators.extractor.plugins.clocks import ClockExtractor
        from generators.extractor.plugins.resets import ResetExtractor
        from generators.extractor.plugins.registers import RegisterExtractor

        self.registry.register("clocks", ClockExtractor(self.semantic_map))
        self.registry.register("resets", ResetExtractor(self.semantic_map))
        self.registry.register("registers", RegisterExtractor(self.semantic_map))

    def extract(
        self,
        subsystem: str,
        source_file: Optional[Path] = None,
        blocks: Optional[List[Dict]] = None,
        validate: bool = False,
    ) -> ExtractionResult:
        """
        Extract data for a subsystem.

        Args:
            subsystem: Plugin name (clocks, resets, registers, etc.)
            source_file: Path to C source file (optional if blocks provided)
            blocks: Pre-parsed blocks (optional if source_file provided)
            validate: Whether to run validation
        """
        plugin = self.registry.get(subsystem)
        if not plugin:
            return ExtractionResult(
                subsystem=subsystem,
                errors=[f"No plugin registered for subsystem: {subsystem}"],
            )

        # Parse source if needed
        if blocks is None:
            if source_file is None:
                return ExtractionResult(
                    subsystem=subsystem,
                    errors=["Either source_file or blocks must be provided"],
                )
            blocks = self.parser.parse_file(source_file)

        # Extract
        result = ExtractionResult(subsystem=subsystem)
        extracted_count = 0
        failed_count = 0

        for block in blocks:
            if plugin.can_extract(block):
                item = plugin.extract(block)
                if item:
                    result.items.append(item)
                    extracted_count += 1
                else:
                    failed_count += 1
                    result.raw_blocks.append(block.get("raw", ""))

        # Calculate confidence
        total_attempts = extracted_count + failed_count
        if total_attempts > 0:
            result.confidence = extracted_count / total_attempts

        # Validate if requested
        if validate:
            errors = plugin.validate(result.items)
            result.errors.extend(errors)

            # Run semantic map validation rules
            semantic_errors = self._semantic_validate(subsystem, result.items)
            result.errors.extend(semantic_errors)

        # Record this run in the semantic map's persistent history
        if source_file:
            self.semantic_map.record_vendor_run(
                source_file,
                stats={
                    "subsystem": subsystem,
                    "items": len(result.items),
                    "confidence": result.confidence,
                    "errors": len(result.errors),
                    "unparsed": len(result.raw_blocks),
                },
            )

        return result

    def _semantic_validate(self, subsystem: str, items: List[Dict]) -> List[str]:
        """Validate items against semantic map rules."""
        errors = []

        # Check for duplicate names
        names = [item.get("name", "") for item in items]
        seen = set()
        for name in names:
            if name in seen:
                errors.append(f"Duplicate {subsystem} name: {name}")
            seen.add(name)

        # Check gates have parents
        if subsystem == "clocks":
            for item in items:
                if item.get("type") == "gate" and "parent" not in item:
                    errors.append(f"Gate clock '{item.get('name')}' missing parent")

        return errors

    def learn(self, subsystem: str, raw_block: str, expected: Dict):
        """
        Learn from a manual correction and persist to disk.

        When the engine fails to extract something correctly,
        provide the raw block and expected output to improve patterns.
        This is stored permanently in the semantic map JSON.
        """
        self.semantic_map.add_learned_pattern(
            raw_block=raw_block,
            expected=expected,
            context=subsystem,
        )

    def report(self, result: ExtractionResult) -> str:
        """Generate a human-readable extraction report."""
        lines = [
            f"Extraction Report: {result.subsystem}",
            f"=" * 40,
            f"Items extracted: {len(result.items)}",
            f"Confidence: {result.confidence:.2%}",
            f"Errors: {len(result.errors)}",
            f"Warnings: {len(result.warnings)}",
            "",
        ]

        if result.errors:
            lines.append("Errors:")
            for err in result.errors:
                lines.append(f"  - {err}")
            lines.append("")

        if result.warnings:
            lines.append("Warnings:")
            for warn in result.warnings:
                lines.append(f"  - {warn}")
            lines.append("")

        if result.raw_blocks:
            lines.append(f"Unparsed blocks: {len(result.raw_blocks)}")

        return "\n".join(lines)

    def save_semantic_map(self, path: Path):
        """Save the current semantic map."""
        self.semantic_map.save(path)


if __name__ == "__main__":
    # Self-test
    print("Sunxi Semantic Extraction Engine")
    print("=================================")

    engine = Engine()
    print(f"Loaded plugins: {engine.registry.list_plugins()}")
    print(f"Semantic map macros: {list(engine.semantic_map.macros.keys())}")
