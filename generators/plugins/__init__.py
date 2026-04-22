"""Domain plugins for the CCU generator.

Each domain exports a `DOMAIN` dict that configures the generator for a
specific clock controller (main, R-domain, RTC, CPUPLL).
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _binding(domain: str) -> Path:
    return ROOT / "include" / "dt-bindings" / "clock" / f"sun60i-a733-{domain}.h"


MAIN = {
    "name": "main",
    "data_file": ROOT / "data" / "ccu-main.json",
    "extracted_file": ROOT / "data" / "ccu-main-extracted.json",
    "compat": "allwinner,sun60i-a733-ccu",
    "module_name": "sun60i-a733-ccu",
    "binding_header": "sun60i-a733-ccu.h",
    "binding_path": _binding("ccu"),
    "has_plls": True,
    "has_key_gates": True,
    "has_resets": True,
    "cross_domain_parents": False,
    "key_literals": {
        "AHB_MASTER_KEY_VALUE": "0x10000FF",
        "MBUS_MASTER_KEY_VALUE": "0x41055800",
        "MBUS_GATE_KEY_VALUE": "0x40302",
        "UPD_KEY_VALUE": "0x8000000",
    },
    "output_file": ROOT.parent / "drivers" / "clk" / "sunxi-ng" / "ccu-sun60i-a733.c",
}

R = {
    "name": "r",
    "data_file": ROOT / "data" / "ccu-r-extracted.json",
    "extracted_file": None,
    "compat": "allwinner,sun60i-a733-r-ccu",
    "module_name": "sun60i-a733-r-ccu",
    "binding_header": "sun60i-a733-r-ccu.h",
    "binding_path": _binding("r-ccu"),
    "has_plls": False,
    "has_key_gates": False,
    "has_resets": False,
    "cross_domain_parents": True,
    "key_literals": {},
    "output_file": ROOT.parent / "drivers" / "clk" / "sunxi-ng" / "ccu-sun60i-a733-r.c",
}

RTC = {
    "name": "rtc",
    "data_file": ROOT / "data" / "ccu-rtc-extracted.json",
    "extracted_file": None,
    "compat": "allwinner,sun60i-a733-rtc-ccu",
    "module_name": "sun60i-a733-rtc-ccu",
    "binding_header": "sun60i-a733-rtc.h",
    "binding_path": _binding("rtc"),
    "has_plls": False,
    "has_key_gates": True,
    "has_resets": False,
    "cross_domain_parents": False,
    "key_literals": {
        "KEY_FIELD_MAGIC_NUM_RTC": "0x16AA0000",
    },
    "output_file": ROOT.parent
    / "drivers"
    / "clk"
    / "sunxi-ng"
    / "ccu-sun60i-a733-rtc.c",
}

CPUPLL = {
    "name": "cpupll",
    "data_file": ROOT / "data" / "ccu-cpupll-extracted.json",
    "extracted_file": None,
    "compat": "allwinner,sun60i-a733-cpupll-ccu",
    "module_name": "sun60i-a733-cpupll-ccu",
    "binding_header": "sun60i-a733-cpupll-ccu.h",
    "binding_path": _binding("cpupll-ccu"),
    "has_plls": True,
    "has_key_gates": False,
    "has_resets": False,
    "cross_domain_parents": True,
    "key_literals": {},
    "output_file": ROOT.parent
    / "drivers"
    / "clk"
    / "sunxi-ng"
    / "ccu-sun60i-a733-cpupll.c",
}

DOMAINS = {
    "main": MAIN,
    "r": R,
    "rtc": RTC,
    "cpupll": CPUPLL,
}
