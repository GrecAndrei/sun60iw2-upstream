"""Tests for DTS extraction plugin."""

import tempfile
import unittest
from pathlib import Path

from generators.extractor import Engine


class TestDtsExtractor(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.map_path = Path(self._tmp.name) / "semantic_map.json"
        self.engine = Engine(map_path=self.map_path)

    def tearDown(self):
        self._tmp.cleanup()

    def test_extract_dts_node(self):
        source = Path(self._tmp.name) / "sample.dtsi"
        source.write_text(
            """
soc {
    uart0: serial@2500000 {
        compatible = "snps,dw-apb-uart";
        clocks = <&ccu CLK_UART0>;
        resets = <&ccu RST_BUS_UART0>;
        status = "disabled";
    };
};
"""
        )
        result = self.engine.extract("dts", source_file=source, validate=True)
        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.items[0]["label"], "uart0")
        self.assertEqual(result.items[0]["node"], "serial@2500000")
        self.assertEqual(result.items[0]["compatible"], "snps,dw-apb-uart")
        self.assertEqual(result.items[0]["status"], "disabled")
        self.assertEqual(result.errors, [])

    def test_extract_overlay_node(self):
        source = Path(self._tmp.name) / "board.dts"
        source.write_text(
            """
&uart0 {
    status = "okay";
};
"""
        )
        result = self.engine.extract("dts", source_file=source, validate=True)
        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.items[0]["node"], "&uart0")
        self.assertEqual(result.items[0]["status"], "okay")


if __name__ == "__main__":
    unittest.main()
