#!/usr/bin/env python3
"""Shared-dimension guard for the Vippa CAD files.

cad/design_params.scad is the single source of truth for every dimension
two models must agree on. This script enforces it:

  FAIL  any .scad under cad/ re-declares a name that design_params.scad
        defines, with any value. Models must consume the shared value,
        never shadow it, so mismatches cannot exist.
  info  any other parameter assigned differing numeric literals in more
        than one file (normal for Customizer knobs like count, worth a
        look otherwise).

Exit 1 on FAIL, 0 otherwise.

Usage:
    scripts/check_params.py
"""

import re
import sys
from collections import defaultdict
from pathlib import Path

CAD = Path(__file__).resolve().parent.parent / "cad"
DESIGN_PARAMS = CAD / "design_params.scad"

# one `name = value;` per line; module argument lists never match because
# they do not end the line with a semicolon
ASSIGN = re.compile(r"(?m)^\s*(\w+)\s*=\s*([^;\n]+?)\s*;")


def scad_files():
    return [p for p in sorted(CAD.rglob("*.scad")) if p != DESIGN_PARAMS]


def main():
    shared = {m.group(1) for m in ASSIGN.finditer(DESIGN_PARAMS.read_text())}
    if not shared:
        print(f"[FAIL] no parameters found in {DESIGN_PARAMS}")
        return 1

    failures = 0
    numeric = defaultdict(dict)  # name -> {file: value}, non-shared literals
    for path in scad_files():
        rel = str(path.relative_to(CAD.parent))
        for m in ASSIGN.finditer(path.read_text()):
            name, raw = m.groups()
            if name in shared:
                print(f"[FAIL] {rel}: '{name} = {raw};' shadows design_params.scad,"
                      " delete it and use the shared value")
                failures += 1
                continue
            try:
                numeric[name].setdefault(rel, float(raw))
            except ValueError:
                pass  # derived expression, not a literal

    for name in sorted(numeric):
        per_file = numeric[name]
        if len(per_file) > 1 and len(set(per_file.values())) > 1:
            print(f"[info] {name} differs between files (fine if unrelated,"
                  " move to design_params.scad if not):")
            for rel, val in sorted(per_file.items()):
                print(f"        {val:<8g} {rel}")

    if failures:
        print(f"\n{failures} shadowed parameter(s). The shared value in"
              " cad/design_params.scad is the only place these may be set.")
        return 1
    print(f"ok: {len(shared)} shared parameters, no shadowing")
    return 0


if __name__ == "__main__":
    sys.exit(main())
