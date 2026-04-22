#!/usr/bin/env python3
"""CCU pipeline health and ROI report.

Compares:
- canonical-only model (ccu-main.json)
- merged model (canonical + extracted)

Outputs machine-readable JSON so progress can be tracked over time.
"""

from __future__ import annotations

import json
from pathlib import Path

from generate_ccu import (
    Generator,
    build_metrics,
    load_json,
    merge_data,
    parse_binding_ids,
)


def run_metrics(data: dict) -> dict:
    gen = Generator(data)
    gen.render()
    return build_metrics(data, gen)


def main() -> int:
    base = Path(__file__).parent / "data"
    canonical = load_json(base / "ccu-main.json")
    extracted = load_json(base / "ccu-main-extracted.json")
    binding_path = (
        Path(__file__).resolve().parent.parent
        / "include"
        / "dt-bindings"
        / "clock"
        / "sun60i-a733-ccu.h"
    )
    binding_ids = parse_binding_ids(binding_path)
    merged = merge_data(canonical, extracted, binding_ids)

    canonical_metrics = run_metrics(canonical)
    merged_metrics = run_metrics(merged)

    delta = {
        "extractable_clocks_gain": merged_metrics["extractable_clocks"]
        - canonical_metrics["extractable_clocks"],
        "supported_clocks_gain": merged_metrics["supported_clocks"]
        - canonical_metrics["supported_clocks"],
        "emitted_common_gain": merged_metrics["emitted_common"]
        - canonical_metrics["emitted_common"],
        "emitted_hw_gain": merged_metrics["emitted_hw"]
        - canonical_metrics["emitted_hw"],
        "support_coverage_gain": round(
            merged_metrics["support_coverage"] - canonical_metrics["support_coverage"],
            2,
        ),
        "id_coverage_gain": round(
            merged_metrics["id_coverage"] - canonical_metrics["id_coverage"],
            2,
        ),
    }

    report = {
        "canonical": canonical_metrics,
        "merged": merged_metrics,
        "delta": delta,
    }

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
