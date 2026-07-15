#!/usr/bin/env python3
"""Concatenate the QR-008 QC project (core, scoring_v5, industry_map, main)
into one paste-able file for single-script QC workflows.

    python3 experiments/QR-008-strength-risk-v5/build_qc_bundle.py

Writes qc_bundle_main.py next to this script. Regenerate after ANY source
change; never edit the bundle by hand (except flipping SMOKE before pasting).
"""

import subprocess
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent.parent
SOURCES = [
    ROOT / "quant_research" / "core.py",
    ROOT / "quant_research" / "scoring_v5.py",
    HERE / "industry_map.py",
    HERE / "main.py",
]
OUT = HERE / "qc_bundle_main.py"

DROP_PREFIXES = (
    "from __future__ import",
    "from AlgorithmImports import",
    "from core import",
    "from industry_map import",
    "from scoring_v5 import",
)


def main():
    commit = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    parts = [
        "# GENERATED single-file bundle for QR-008 -- do not edit by hand.\n"
        f"# Built by build_qc_bundle.py from quant-research@{commit}.\n"
        "# Sources: quant_research/core.py, quant_research/scoring_v5.py,\n"
        "#          experiments/QR-008-strength-risk-v5/{industry_map,main}.py\n"
        "# Before pasting: set SMOKE = True for the P-B smoke run through\n"
        "# 2011-06-30; SMOKE = False only for the frozen full-period run.\n",
        "from __future__ import annotations\n",
        "from AlgorithmImports import *\n",
    ]
    for src in SOURCES:
        body = "".join(
            line for line in src.read_text().splitlines(keepends=True)
            if not line.startswith(DROP_PREFIXES)
        )
        parts.append(f"\n\n# ===== {src.relative_to(ROOT)} =====\n{body}")
    OUT.write_text("".join(parts))
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes) from {commit}")


if __name__ == "__main__":
    main()
