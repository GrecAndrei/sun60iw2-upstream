"""Unit tests for SSEE engine improvements."""

import tempfile
import unittest
from pathlib import Path

from generators.extractor import CBlockParser, Engine


class TestSSEEEngine(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self._tmp.name)
        self.map_path = self.tmp_path / "semantic_map.json"
        self.engine = Engine(map_path=self.map_path)

    def tearDown(self):
        self._tmp.cleanup()

    def test_learned_pattern_fallback_extracts_item(self):
        raw = "static SUNXI_CCU_GATE(uart0_clk);"
        expected = {
            "name": "uart0",
            "type": "gate",
            "parent": "apb1",
            "reg": "0x000",
            "bit": 0,
        }
        self.engine.learn("clocks", raw, expected)

        result = self.engine.extract(
            "clocks", blocks=[{"type": "macro", "content": raw, "raw": raw}]
        )
        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.items[0]["name"], "uart0")
        self.assertEqual(result.metrics.get("learned_pattern_hits"), 1)

    def test_preprocessor_multiline_is_single_block(self):
        content = "#define CLK_NAME(x) \\\n\t((x) + 1)\nstatic SUNXI_CCU_GATE(foo, \"f\", p, 0x0, 1, 0);"
        blocks = CBlockParser().parse(content)
        preproc = [b for b in blocks if b.get("type") == "preprocessor"]
        self.assertEqual(len(preproc), 1)
        self.assertIn("\\", preproc[0]["content"])
        self.assertIn("((x) + 1)", preproc[0]["content"])

    def test_skip_unchanged_uses_cache(self):
        source = self.tmp_path / "ccu-test.c"
        source.write_text(
            'static SUNXI_CCU_GATE(uart0_clk, "uart0", "apb1", 0x000, 1, 0);\n'
        )

        first = self.engine.extract("clocks", source_file=source, skip_unchanged=True)
        self.assertFalse(first.cached)
        self.assertEqual(len(first.items), 1)

        second = self.engine.extract("clocks", source_file=source, skip_unchanged=True)
        self.assertTrue(second.cached)
        self.assertTrue(second.metrics.get("skipped_unchanged"))

    def test_parent_normalization_resolves_complex_ref(self):
        items = [
            {"name": "pll-peri0", "type": "nm", "reg": "0x20"},
            {
                "name": "uart0",
                "type": "gate",
                "reg": "0x100",
                "bit": 1,
                "parent": "clk_hw_get_parent(&pll_peri0_clk.common.hw)",
            },
        ]
        self.engine.symbol_table.index(items)
        resolved = self.engine.resolve_parents(items)
        uart0 = next(item for item in resolved if item.get("name") == "uart0")
        self.assertEqual(uart0.get("parent"), "pll-peri0")


if __name__ == "__main__":
    unittest.main()
