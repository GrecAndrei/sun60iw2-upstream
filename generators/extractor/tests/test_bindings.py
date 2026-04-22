"""Tests for dt-bindings extraction plugin."""

import tempfile
import unittest
from pathlib import Path

from generators.extractor import Engine


class TestDtBindingsExtractor(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.map_path = Path(self._tmp.name) / "semantic_map.json"
        self.engine = Engine(map_path=self.map_path)

    def tearDown(self):
        self._tmp.cleanup()

    def test_extract_clock_binding(self):
        blocks = [
            {
                "type": "preprocessor",
                "content": "#define CLK_UART0 154",
                "raw": "#define CLK_UART0 154",
            }
        ]
        result = self.engine.extract("bindings", blocks=blocks, validate=True)
        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.items[0]["domain"], "clock")
        self.assertEqual(result.items[0]["value"], 154)

    def test_validate_duplicate_values(self):
        blocks = [
            {
                "type": "preprocessor",
                "content": "#define RST_BUS_UART0 41",
                "raw": "#define RST_BUS_UART0 41",
            },
            {
                "type": "preprocessor",
                "content": "#define RST_BUS_UART1 41",
                "raw": "#define RST_BUS_UART1 41",
            },
        ]
        result = self.engine.extract("bindings", blocks=blocks, validate=True)
        self.assertEqual(len(result.items), 2)
        self.assertTrue(any("Duplicate reset value 41" in err for err in result.errors))


if __name__ == "__main__":
    unittest.main()

