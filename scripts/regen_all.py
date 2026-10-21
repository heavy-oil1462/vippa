#!/usr/bin/env python3
"""Regenerate all derived artifacts for Vippa in one command.

Run after any change to cad/ (see the regen-outputs skill). Never
hand-compose openscad command lines for this.

Pipeline:
  1. scripts/check_params.py     shared dimensions are never shadowed
  2. scripts/check_style.py      docs and comments follow the writing rules
  3. every model under cad/      -> stl/<category>/<name>.stl

A model is any .scad under cad/ except cad/lib/ (helpers) and
design_params.scad (data). Each model must render warning-free with
manifold status NoError.

Prototyping phase: stl/ is gitignored while the models are iterated by
eye in OpenSCAD. When designs settle the STLs (and DXFs for the CNC)
become committed build products and --check gains a byte comparison
against them, the way skua does it.

Usage:
    scripts/regen_all.py [model ...]   # no args = everything
    scripts/regen_all.py --check       # read-only gate (the verify skill and
                                       # CI): render everything to a temp dir,
                                       # touch nothing in the tree
"""

import re
import subprocess
import sys
import tempfile
from pathlib import Path

from render_scad import render

ROOT = Path(__file__).resolve().parent.parent
CAD = ROOT / "cad"
NON_MODELS = {"design_params"}
GATES = ["check_params.py", "check_style.py"]


def models():
    for p in sorted(CAD.rglob("*.scad")):
        rel = p.relative_to(CAD)
        if rel.parts[0] != "lib" and p.stem not in NON_MODELS:
            yield p


def run_one(scad: Path, out: Path, shown: Path, extra=None) -> bool:
    """Render scad -> out and report. shown is the path to print (the
    real target when out is a temp file in check mode)."""
    out.parent.mkdir(parents=True, exist_ok=True)
    proc = render(str(scad), str(out), extra)
    warnings = sorted({l.strip() for l in proc.stderr.splitlines()
                       if "WARNING" in l or "ERROR" in l})
    # Manifold backend reports geometry health as "Status: NoError"
    geom = re.search(r"Status:\s+(\w+)", proc.stderr)
    geom_ok = geom is None or geom.group(1) == "NoError"
    ok = proc.returncode == 0 and not warnings and geom_ok
    print(f"[{'ok' if ok else 'FAIL'}] {scad.relative_to(ROOT)} -> {shown.relative_to(ROOT)}",
          flush=True)
    for w in warnings:
        print(f"        {w}")
    if not geom_ok:
        print(f"        geometry status: {geom.group(1)}, model is not cleanly manifold")
    if proc.returncode != 0 and not warnings:
        print("        " + "\n        ".join(proc.stderr.strip().splitlines()[-5:]))
    return ok


def main(argv):
    check = "--check" in argv
    only = {a for a in argv[1:] if not a.startswith("--")}

    ok = True
    for gate in GATES:
        ok &= subprocess.run([sys.executable, str(ROOT / "scripts" / gate)]).returncode == 0

    with tempfile.TemporaryDirectory() as td:
        for scad in models():
            if only and scad.stem not in only:
                continue
            stl = ROOT / "stl" / scad.relative_to(CAD).with_suffix(".stl")
            out = Path(td) / stl.relative_to(ROOT) if check else stl
            ok &= run_one(scad, out, stl)

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
