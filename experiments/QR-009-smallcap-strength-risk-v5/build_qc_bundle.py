#!/usr/bin/env python3
"""Concatenate the QR-009 QC project into one paste-able file (same minify
pipeline as QR-008). industry_map.py is shared from the QR-008 directory.

    python3 experiments/QR-009-smallcap-strength-risk-v5/build_qc_bundle.py
"""

import ast
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent.parent
SOURCES = [
    ROOT / "quant_research" / "core.py",
    ROOT / "quant_research" / "scoring_v5.py",
    HERE.parent / "QR-008-strength-risk-v5" / "industry_map.py",
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


# Bundle-only pruning of functions QR-009 never calls (sources untouched).
DROP_FUNCS = {"numeric_field", "equal_weight_return", "resolved_codes"}


def _minify(source):
    tree = ast.parse(source)
    tree.body = [n for n in tree.body
                 if not (isinstance(n, ast.FunctionDef) and n.name in DROP_FUNCS)]
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                body.pop(0)
                if not body:
                    body.append(ast.Pass())
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            node.returns = None
            args = node.args
            for arg in args.args + args.posonlyargs + args.kwonlyargs:
                arg.annotation = None
            if args.vararg:
                args.vararg.annotation = None
            if args.kwarg:
                args.kwarg.annotation = None
    lines = []
    for line in ast.unparse(tree).splitlines():
        stripped = line.lstrip(" ")
        depth = (len(line) - len(stripped)) // 4
        lines.append(" " * depth + stripped)
    return "\n".join(lines)


def main():
    commit = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    parts = [
        f"# GENERATED QR-009 bundle (quant-research@{commit}); edit only SMOKE:\n"
        "# True = smoke to 2011-06-30, False = frozen full run.\n",
        "from AlgorithmImports import *\n",
    ]
    for src in SOURCES:
        body = "".join(
            line for line in src.read_text().splitlines(keepends=True)
            if not line.startswith(DROP_PREFIXES)
        )
        parts.append(_minify(body) + "\n")
    OUT.write_text("".join(parts))
    size = OUT.stat().st_size
    print(f"wrote {OUT} ({size} chars) from {commit}"
          + ("" if size <= 32000 else "  !! OVER the 32000-char QC cap"))


if __name__ == "__main__":
    main()
