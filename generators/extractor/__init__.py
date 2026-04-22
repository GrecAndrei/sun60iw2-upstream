#!/usr/bin/env python3
"""
Sunxi Semantic Extraction Engine (SSEE) v2

Major upgrades:
- Symbol Table: Resolves C variable names to semantic entities
- Cross-Reference Validator: Ensures all parent references exist
- Conflict Detector: Finds register/bit collisions
- Relationship Builder: Auto-discovers clock hierarchies
- Export System: JSON, YAML, CSV, Markdown
- Batch Processor: Process entire vendor trees

Usage:
    from generators.extractor import Engine
    engine = Engine()
    result = engine.extract('clocks', source_file=Path('vendor/ccu.c'))

    # Build symbol table for parent resolution
    symtab = engine.build_symbol_table(result.items)
    resolved = engine.resolve_parents(result.items, symtab)

    # Validate cross-references
    engine.validate_crossrefs(resolved)

    # Detect hardware conflicts
    conflicts = engine.detect_conflicts(resolved)

    # Build clock tree
    tree = engine.build_clock_tree(resolved)

    # Export
    engine.export(resolved, format='json', path='out.json')
    engine.export(resolved, format='markdown', path='out.md')
"""

import json
import re
import csv
import time
import hashlib
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict

# Canonical external/root clock sources that are valid parents even when
# they do not appear as extracted in-file items.
DEFAULT_ROOT_SOURCES = ("osc24M", "dcxo", "hosc", "losc", "ext-osc32k")
PATTERN_PREVIEW_LENGTH = 200
LEARNED_PATTERN_MIN_SIMILARITY = 0.92


@dataclass
class ExtractionResult:
    """Result from a single extraction run."""

    subsystem: str
    items: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    raw_blocks: List[str] = field(default_factory=list)
    symbol_table: Dict[str, str] = field(default_factory=dict)
    relationships: Dict[str, List[str]] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    cached: bool = False

    def merge(self, other: "ExtractionResult"):
        self.items.extend(other.items)
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.raw_blocks.extend(other.raw_blocks)
        self.confidence = (self.confidence + other.confidence) / 2
        self.metrics.update(other.metrics)
        self.cached = self.cached or other.cached


class SemanticMap:
    """Persistent knowledge base stored on disk."""

    DEFAULT_PATH = Path(__file__).parent / "data" / "semantic_map.json"

    def __init__(self, map_path: Optional[Path] = None):
        self._path = map_path or self.DEFAULT_PATH
        self.macros: Dict[str, Dict] = {}
        self.types: Dict[str, str] = {}
        self.validation_rules: List[Dict] = []
        self.relationships: Dict[str, List[str]] = {}
        self.learned_patterns: List[Dict] = []
        self.vendor_history: Dict[str, Dict] = {}
        self.root_sources: Set[str] = set()

        if self._path.exists():
            self.load(self._path)
        else:
            self._init_defaults()
            self.save(self._path)

    def _init_defaults(self):
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
                "fields": [".enable", ".lock", ".n", ".k", ".m", ".p", ".common.reg"],
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
        self.root_sources = set(DEFAULT_ROOT_SOURCES)

    def load(self, path: Path):
        with open(path) as f:
            data = json.load(f)
        self.macros = data.get("macros", {})
        self.types = data.get("types", {})
        self.validation_rules = data.get("validation_rules", [])
        self.relationships = data.get("relationships", {})
        self.learned_patterns = data.get("learned_patterns", [])
        self.vendor_history = data.get("vendor_history", {})
        self.root_sources = set(data.get("root_sources", list(DEFAULT_ROOT_SOURCES)))

    def save(self, path: Optional[Path] = None):
        save_path = path or self._path
        data = {
            "macros": self.macros,
            "types": self.types,
            "validation_rules": self.validation_rules,
            "relationships": self.relationships,
            "learned_patterns": self.learned_patterns,
            "vendor_history": self.vendor_history,
            "root_sources": sorted(self.root_sources),
        }
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w") as f:
            json.dump(data, f, indent=2)

    def record_vendor_run(self, filepath: Path, stats: Dict):
        checksum = self._file_checksum(filepath)
        previous = self.vendor_history.get(str(filepath), {})
        run_count = int(previous.get("run_count", 0)) + 1
        now_iso = datetime.now(timezone.utc).isoformat()
        now_epoch = str(time.time())
        self.vendor_history[str(filepath)] = {
            "checksum": checksum,
            "last_run": now_epoch,
            "last_run_iso": now_iso,
            "run_count": run_count,
            "stats": stats,
        }
        self.save()

    def add_learned_pattern(self, raw_block: str, expected: Dict, context: str = ""):
        normalized = self._normalize_for_learning(raw_block)
        block_hash = hashlib.sha256(raw_block.encode()).hexdigest()[:16]
        normalized_hash = hashlib.sha256(normalized.encode()).hexdigest()[:16]
        self.learned_patterns.append(
            {
                "hash": block_hash,
                "normalized_hash": normalized_hash,
                "context": context,
                "raw_preview": raw_block[:PATTERN_PREVIEW_LENGTH],
                "normalized_preview": normalized[:PATTERN_PREVIEW_LENGTH],
                "expected": expected,
            }
        )
        self.save()

    def has_seen_vendor(self, filepath: Path) -> bool:
        return str(filepath) in self.vendor_history

    def _file_checksum(self, filepath: Path) -> str:
        content = filepath.read_bytes()
        return hashlib.sha256(content).hexdigest()[:16]

    def is_vendor_unchanged(self, filepath: Path) -> bool:
        info = self.vendor_history.get(str(filepath))
        if not info:
            return False
        return info.get("checksum") == self._file_checksum(filepath)

    @staticmethod
    def _normalize_for_learning(raw_block: str) -> str:
        compact = " ".join(raw_block.split())
        compact = re.sub(r"\b0x[0-9a-fA-F]+\b", "0xN", compact)
        compact = re.sub(r"\b\d+\b", "N", compact)
        compact = re.sub(r'"[^"]*"', '"STR"', compact)
        return compact

    def resolve_type(self, pattern: str) -> Optional[str]:
        return self.types.get(pattern)

    def get_macro_signature(self, macro_name: str) -> Optional[Dict]:
        return self.macros.get(macro_name)


class CBlockParser:
    """Parses C source into semantic blocks."""

    def __init__(self):
        self.blocks: List[Dict] = []

    def parse_file(self, filepath: Path) -> List[Dict]:
        with open(filepath) as f:
            content = f.read()
        return self.parse(content)

    def parse(self, content: str) -> List[Dict]:
        blocks = []
        lines = content.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i].strip()
            if not line or line.startswith("//"):
                i += 1
                continue

            if line.startswith("/*"):
                comment, i = self._extract_multiline_comment(lines, i)
                blocks.append({"type": "comment", "content": comment, "raw": comment})
                continue

            if line.startswith("#"):
                preproc_block, i = self._extract_preprocessor(lines, i)
                blocks.append(preproc_block)
                continue

            if "struct " in line and "{" in line:
                struct_block, i = self._extract_struct(lines, i)
                blocks.append(struct_block)
                continue

            if line.startswith("static "):
                macro_block, i = self._extract_macro_invocation(lines, i)
                if macro_block:
                    blocks.append(macro_block)
                continue

            i += 1

        self.blocks = blocks
        return blocks

    def _extract_multiline_comment(self, lines, start_idx):
        block = []
        i = start_idx
        while i < len(lines):
            block.append(lines[i])
            if "*/" in lines[i]:
                break
            i += 1
        return "\n".join(block), i + 1

    def _extract_struct(self, lines, start_idx):
        block_lines = []
        brace_count = 0
        i = start_idx
        var_name = None
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
            if paren_depth == 0 and ");" in line:
                break
            i += 1

        content = "\n".join(block_lines)
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

    def _extract_preprocessor(self, lines, start_idx):
        block_lines = []
        i = start_idx
        while i < len(lines):
            line = lines[i]
            block_lines.append(line)
            if not line.rstrip().endswith("\\"):
                break
            i += 1
        content = "\n".join(block_lines)
        return {"type": "preprocessor", "content": content, "raw": content}, i + 1


class SymbolTable:
    """
    Maps C variable names to semantic clock names.

    Vendor code uses variable names as parents:
        static struct ccu_nm pll_peri0_clk = { ... name: "pll-peri0" ... };
        static SUNXI_CCU_GATE(uart0_clk, "uart0", pll_peri0_clk, ...);
                                              ^^^^^^^^^^^^^^
    The symbol table resolves pll_peri0_clk -> "pll-peri0"
    """

    def __init__(self):
        self.symbols: Dict[str, str] = {}  # var_name -> clock_name
        self.by_name: Dict[str, Dict] = {}  # clock_name -> item

    def index(self, items: List[Dict]):
        """Build index from extracted items."""
        for item in items:
            name = item.get("name", "")
            if not name:
                continue
            self.by_name[name] = item
            # Also index by normalized variable name
            var_name = name.replace("-", "_") + "_clk"
            self.symbols[var_name] = name
            # And without _clk suffix
            self.symbols[name.replace("-", "_")] = name

    def resolve(self, parent_ref: str) -> Optional[str]:
        """Resolve a parent reference to a clock name."""
        parent_ref = self._normalize_parent_ref(parent_ref)
        if not parent_ref:
            return None
        # Already a quoted string name
        if parent_ref.startswith('"') and parent_ref.endswith('"'):
            return parent_ref.strip('"')
        # Variable name
        return self.symbols.get(parent_ref)

    @staticmethod
    def _normalize_parent_ref(parent_ref: str) -> str:
        ref = parent_ref.strip()
        if not ref:
            return ""
        if ref.startswith("&"):
            ref = ref[1:]
        if ref.startswith("*"):
            ref = ref[1:]
        if "." in ref:
            ref = ref.split(".", 1)[0]
        if "[" in ref:
            ref = ref.split("[", 1)[0]
        fn_match = re.match(r"\w+\s*\(\s*&?([\w\[\]\.]+)", ref)
        if fn_match:
            ref = fn_match.group(1).split(".", 1)[0].split("[", 1)[0]
        return ref.strip()

    def get_item(self, name: str) -> Optional[Dict]:
        return self.by_name.get(name)


class CrossReferenceValidator:
    """Validates that all parent/child references exist."""

    def validate(
        self, items: List[Dict], symtab: SymbolTable, root_sources: Optional[Set[str]] = None
    ) -> List[str]:
        errors = []
        all_names = {item.get("name", "") for item in items}
        known_roots = root_sources or set(DEFAULT_ROOT_SOURCES)

        for item in items:
            parent = item.get("parent", "")
            if not parent:
                continue

            # Resolve through symbol table
            resolved = symtab.resolve(parent)
            if resolved and resolved in all_names:
                continue
            if parent in all_names:
                continue

            # Check if it's a known root source
            if parent in known_roots:
                continue

            errors.append(
                f"Clock '{item.get('name')}' references unknown parent: '{parent}'"
            )

        return errors


class ConflictDetector:
    """Detects register offset and bit collisions."""

    def detect(self, items: List[Dict]) -> List[str]:
        conflicts = []

        # Group gates by register
        gates_by_reg: Dict[str, List[Tuple[str, int]]] = defaultdict(list)
        for item in items:
            if item.get("type") == "gate":
                reg = str(item.get("reg", ""))
                bit = item.get("bit")
                if reg and bit is not None:
                    gates_by_reg[reg].append((item.get("name", ""), bit))

        # Check for bit collisions
        for reg, gates in gates_by_reg.items():
            bits_used: Dict[int, List[str]] = defaultdict(list)
            for name, bit in gates:
                bits_used[bit].append(name)

            for bit, names in bits_used.items():
                if len(names) > 1:
                    conflicts.append(
                        f"BIT CONFLICT at reg={reg}, bit={bit}: {', '.join(names)}"
                    )

        # Check for overlapping PLL registers
        pll_regs: Dict[str, str] = {}
        for item in items:
            if item.get("type") in ("nm", "nkmp", "pll"):
                reg = str(item.get("reg", ""))
                if reg in pll_regs:
                    conflicts.append(
                        f"PLL REGISTER OVERLAP at {reg}: "
                        f"'{pll_regs[reg]}' and '{item.get('name')}'"
                    )
                pll_regs[reg] = item.get("name", "")

        return conflicts


class RelationshipBuilder:
    """Builds clock tree relationships from parent references."""

    def build(self, items: List[Dict], symtab: SymbolTable) -> Dict[str, List[str]]:
        tree: Dict[str, List[str]] = defaultdict(list)

        for item in items:
            name = item.get("name", "")
            parent = item.get("parent", "")
            if not parent:
                continue

            resolved = symtab.resolve(parent)
            if resolved:
                tree[resolved].append(name)
            else:
                tree[parent].append(name)

        return dict(tree)


class ExportSystem:
    """Exports extracted data to multiple formats."""

    def export(self, items: List[Dict], fmt: str, path: Path):
        """Export items to the specified format."""
        if fmt == "json":
            self._export_json(items, path)
        elif fmt == "yaml":
            self._export_yaml(items, path)
        elif fmt == "csv":
            self._export_csv(items, path)
        elif fmt == "markdown":
            self._export_markdown(items, path)
        else:
            raise ValueError(f"Unknown export format: {fmt}")

    def _export_json(self, items: List[Dict], path: Path):
        with open(path, "w") as f:
            json.dump({"clocks": items}, f, indent=2)

    def _export_yaml(self, items: List[Dict], path: Path):
        lines = ["clocks:"]
        for item in items:
            lines.append(f"  - name: {item.get('name', '')}")
            for key, val in item.items():
                if key != "name":
                    lines.append(f"    {key}: {val}")
        path.write_text("\n".join(lines))

    def _export_csv(self, items: List[Dict], path: Path):
        if not items:
            return
        keys = list(items[0].keys())
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(items)

    def _export_markdown(self, items: List[Dict], path: Path):
        lines = [
            "# Extracted Clocks\n",
            "| Name | Type | Reg | Parent |",
            "|------|------|-----|--------|",
        ]
        for item in items:
            lines.append(
                f"| {item.get('name', '')} | {item.get('type', '')} | "
                f"{item.get('reg', '')} | {item.get('parent', '')} |"
            )
        path.write_text("\n".join(lines))


class BatchProcessor:
    """Process multiple vendor files at once."""

    def __init__(self, engine: "Engine"):
        self.engine = engine

    def process_directory(
        self, directory: Path, subsystem: str, skip_unchanged: bool = True
    ) -> Dict[str, ExtractionResult]:
        """Process all matching source files in a directory."""
        results = {}
        patterns = ["*.h"] if subsystem == "registers" else ["*.c"]
        if subsystem == "registers":
            patterns.append("*.c")
        source_files: List[Path] = []
        for pattern in patterns:
            source_files.extend(directory.rglob(pattern))
        source_files = sorted(set(source_files))
        for source_file in source_files:
            print(f"Processing {source_file}...")
            result = self.engine.extract(
                subsystem, source_file=source_file, skip_unchanged=skip_unchanged
            )
            results[str(source_file)] = result
        return results

    def process_file_list(
        self, files: List[Path], subsystem: str, skip_unchanged: bool = True
    ) -> Dict[str, ExtractionResult]:
        results = {}
        for source_file in files:
            result = self.engine.extract(
                subsystem, source_file=source_file, skip_unchanged=skip_unchanged
            )
            results[str(source_file)] = result
        return results


class PluginRegistry:
    """Registry of extraction plugins."""

    def __init__(self):
        self.plugins: Dict[str, "ExtractorPlugin"] = {}

    def register(self, name: str, plugin: "ExtractorPlugin"):
        self.plugins[name] = plugin

    def get(self, name: str) -> Optional["ExtractorPlugin"]:
        return self.plugins.get(name)

    def list_plugins(self) -> List[str]:
        return list(self.plugins.keys())


class ExtractorPlugin:
    """Base class for extraction plugins."""

    def __init__(self, semantic_map: SemanticMap):
        self.semantic_map = semantic_map
        self.confidence_threshold = 0.8

    def can_extract(self, block: Dict) -> bool:
        raise NotImplementedError

    def extract(self, block: Dict) -> Optional[Dict]:
        raise NotImplementedError

    def validate(self, items: List[Dict]) -> List[str]:
        return []


class Engine:
    """Main extraction engine with full analysis pipeline."""

    def __init__(
        self,
        semantic_map: Optional[SemanticMap] = None,
        map_path: Optional[Path] = None,
    ):
        self.semantic_map = semantic_map or SemanticMap(map_path=map_path)
        self.parser = CBlockParser()
        self.registry = PluginRegistry()
        self.symbol_table = SymbolTable()
        self.xref_validator = CrossReferenceValidator()
        self.conflict_detector = ConflictDetector()
        self.relationship_builder = RelationshipBuilder()
        self.exporter = ExportSystem()
        self.batch = BatchProcessor(self)
        self._load_plugins()

    def _load_plugins(self):
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
        skip_unchanged: bool = False,
    ) -> ExtractionResult:
        plugin = self.registry.get(subsystem)
        if not plugin:
            return ExtractionResult(
                subsystem=subsystem,
                errors=[f"No plugin registered for subsystem: {subsystem}"],
            )

        if blocks is None:
            if source_file is None:
                return ExtractionResult(
                    subsystem=subsystem,
                    errors=["Either source_file or blocks must be provided"],
                )
            if skip_unchanged and self.semantic_map.is_vendor_unchanged(source_file):
                stats = (
                    self.semantic_map.vendor_history.get(str(source_file), {}).get("stats", {})
                )
                return ExtractionResult(
                    subsystem=subsystem,
                    confidence=float(stats.get("confidence", 1.0)),
                    metrics={
                        "skipped_unchanged": True,
                        "cached_from_history": True,
                        "previous_items": int(stats.get("items", 0)),
                    },
                    warnings=[f"Skipped unchanged file: {source_file}"],
                    cached=True,
                )
            blocks = self.parser.parse_file(source_file)

        result = ExtractionResult(subsystem=subsystem)
        extracted_count = 0
        failed_count = 0
        learned_count = 0

        for block in blocks:
            if plugin.can_extract(block):
                item = plugin.extract(block)
                if not item:
                    item = self._apply_learned_pattern(
                        subsystem=subsystem, raw_block=block.get("raw", "")
                    )
                    if item:
                        learned_count += 1
                if item:
                    result.items.append(item)
                    extracted_count += 1
                else:
                    failed_count += 1
                    result.raw_blocks.append(block.get("raw", ""))

        total = extracted_count + failed_count
        if total > 0:
            result.confidence = extracted_count / total
        result.metrics.update(
            {
                "total_candidate_blocks": total,
                "extracted_blocks": extracted_count,
                "failed_blocks": failed_count,
                "learned_pattern_hits": learned_count,
            }
        )

        # Post-extraction analysis
        self.symbol_table.index(result.items)
        result.symbol_table = dict(self.symbol_table.symbols)

        # Resolve parents
        result.items = self.resolve_parents(result.items)

        # Build relationships
        result.relationships = self.relationship_builder.build(
            result.items, self.symbol_table
        )

        # Validation
        if validate:
            result.errors.extend(plugin.validate(result.items))
            result.errors.extend(self._semantic_validate(subsystem, result.items))
            result.errors.extend(
                self.xref_validator.validate(
                    result.items, self.symbol_table, self.semantic_map.root_sources
                )
            )

            conflicts = self.conflict_detector.detect(result.items)
            if conflicts:
                result.warnings.extend(conflicts)

        # Record history
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

    def _apply_learned_pattern(self, subsystem: str, raw_block: str) -> Optional[Dict]:
        if not raw_block:
            return None
        block_hash = hashlib.sha256(raw_block.encode()).hexdigest()[:16]
        normalized = self.semantic_map._normalize_for_learning(raw_block)
        normalized_hash = hashlib.sha256(normalized.encode()).hexdigest()[:16]
        best: Optional[Dict[str, Any]] = None
        best_score = 0.0
        normalized_prefix = normalized[:24]

        for pattern in self.semantic_map.learned_patterns:
            if pattern.get("context") and pattern.get("context") != subsystem:
                continue
            if pattern.get("hash") == block_hash:
                return dict(pattern.get("expected", {}))
            if pattern.get("normalized_hash") == normalized_hash:
                return dict(pattern.get("expected", {}))
            preview = pattern.get("normalized_preview", "")
            if not preview:
                continue
            if (
                normalized_prefix
                and preview
                and not preview.startswith(normalized_prefix[:8])
                and normalized_prefix[:8] not in preview
            ):
                continue
            score = SequenceMatcher(
                None, normalized[:PATTERN_PREVIEW_LENGTH], preview
            ).ratio()
            if score > best_score:
                best_score = score
                best = pattern

        if best and best_score >= LEARNED_PATTERN_MIN_SIMILARITY:
            return dict(best.get("expected", {}))
        return None

    def resolve_parents(self, items: List[Dict]) -> List[Dict]:
        """Resolve variable-name parents to actual clock names."""
        for item in items:
            parent = item.get("parent", "")
            if parent and not parent.startswith('"'):
                resolved = self.symbol_table.resolve(parent)
                if resolved:
                    item["parent"] = resolved
        return items

    def build_clock_tree(self, items: List[Dict]) -> Dict[str, List[str]]:
        """Build full clock hierarchy."""
        return self.relationship_builder.build(items, self.symbol_table)

    def validate_crossrefs(self, items: List[Dict]) -> List[str]:
        """Validate all cross-references."""
        return self.xref_validator.validate(
            items, self.symbol_table, self.semantic_map.root_sources
        )

    def detect_conflicts(self, items: List[Dict]) -> List[str]:
        """Detect register/bit conflicts."""
        return self.conflict_detector.detect(items)

    def export(self, items: List[Dict], fmt: str, path: Path):
        """Export to specified format."""
        self.exporter.export(items, fmt, path)

    def _semantic_validate(self, subsystem: str, items: List[Dict]) -> List[str]:
        errors = []
        names = [item.get("name", "") for item in items]
        seen = set()
        for name in names:
            if name in seen:
                errors.append(f"Duplicate {subsystem} name: {name}")
            seen.add(name)

        if subsystem == "clocks":
            for item in items:
                if item.get("type") == "gate" and "parent" not in item:
                    errors.append(f"Gate clock '{item.get('name')}' missing parent")

        return errors

    def learn(self, subsystem: str, raw_block: str, expected: Dict):
        self.semantic_map.add_learned_pattern(raw_block, expected, subsystem)

    def report(self, result: ExtractionResult) -> str:
        lines = [
            f"Extraction Report: {result.subsystem}",
            "=" * 40,
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
        if result.relationships:
            lines.append(
                f"Relationships discovered: {len(result.relationships)} parents"
            )
        if result.raw_blocks:
            lines.append(f"Unparsed blocks: {len(result.raw_blocks)}")
        if result.cached:
            lines.append("Used cached history for unchanged file.")
        if result.metrics:
            lines.append(
                "Metrics: "
                + ", ".join(f"{k}={v}" for k, v in sorted(result.metrics.items()))
            )
        return "\n".join(lines)

    def save_semantic_map(self, path: Path):
        self.semantic_map.save(path)


if __name__ == "__main__":
    print("Sunxi Semantic Extraction Engine v2")
    print("New features:")
    print("  - Symbol table with parent resolution")
    print("  - Cross-reference validation")
    print("  - Register/bit conflict detection")
    print("  - Clock tree relationship builder")
    print("  - Multi-format export (json, yaml, csv, markdown)")
    print("  - Batch processor for entire vendor trees")
