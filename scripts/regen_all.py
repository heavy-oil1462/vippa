#!/usr/bin/env python3
"""Regenerate all derived artifacts for Vippa in one command.

Run after any change to cad/, catalog/ or panels/ (see the regen-outputs
skill). Never hand-compose openscad command lines for this.

Pipeline:
  1. scripts/check_params.py     shared dimensions are never shadowed
  2. scripts/check_style.py      docs and comments follow the writing rules
  3. scripts/panels.py           catalog and every panel config are valid
  4. every model under cad/      -> build/<category>/<name>.stl
     catalog modules with a "model" (printed holders) must match their
     catalog size: the STL bounding box is compared with "size"
  5. every panels/<name>.json    -> build/panels/<name>/
       <name>.scad               wrapper to open in OpenSCAD
       punch_template.stl        front template, print orientation
       router_template.stl       back template, print orientation
       front.png, back.png       quick reference renders of the panel
       <name>.yaml               ESPHome config (scripts/firmware.py),
                                 validated with esphome config

A model is any .scad under cad/ except cad/lib/ (helpers) and
design_params.scad (data). Everything must render warning-free with
manifold status NoError; a failed assert in cad/lib/panel.scad (router
bit against cavity corner, template against bed size) is a FAIL.

The photoreal README images in media/ come from scripts/render_hero.py,
not from here: Cycles takes minutes and is not byte deterministic.

Prototyping phase: build/ is gitignored while the models are iterated
by eye in OpenSCAD. When designs settle the STLs (and DXFs for the CNC)
become committed build products and --check gains a byte comparison
against them, the way skua does it.

Usage:
    scripts/regen_all.py [name ...]    # no args = everything; a name is a
                                       # model or a panel
    scripts/regen_all.py --check       # read-only gate (the verify skill and
                                       # CI): render everything to a temp dir,
                                       # touch nothing in the tree
"""

import re
import subprocess
import sys
import tempfile
from pathlib import Path

import firmware
import panels
from render_scad import render

ROOT = Path(__file__).resolve().parent.parent
CAD = ROOT / "cad"
BUILD = ROOT / "build"
NON_MODELS = {"design_params"}
GATES = ["check_params.py", "check_style.py", "panels.py"]
# (output name, wrapper part, extra openscad args)
PANEL_OUTPUTS = [
    ("punch_template.stl", "punch", []),
    ("router_template.stl", "router", []),
    ("front.png", "panel", ["--imgsize=1000,700", "--camera=0,0,0,50,0,20,0",
                            "--viewall", "--autocenter", "--colorscheme=Tomorrow"]),
    ("back.png", "panel", ["--imgsize=1000,700", "--camera=0,0,0,130,0,20,0",
                           "--viewall", "--autocenter", "--colorscheme=Tomorrow"]),
]


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
    print(f"[{'ok' if ok else 'FAIL'}] {shown.relative_to(ROOT)}", flush=True)
    for w in warnings:
        print(f"        {w}")
    if not geom_ok:
        print(f"        geometry status: {geom.group(1)}, model is not cleanly manifold")
    if proc.returncode != 0 and not warnings:
        print("        " + "\n        ".join(proc.stderr.strip().splitlines()[-5:]))
    return ok


VERTEX = re.compile(rb"vertex\s+(\S+)\s+(\S+)\s+(\S+)")
SIZE_TOLERANCE = 0.05  # mm


def bbox_size(stl: Path):
    p = [tuple(map(float, m)) for m in VERTEX.findall(stl.read_bytes())]
    return [max(v[i] for v in p) - min(v[i] for v in p) for i in range(3)]


def check_model_sizes(catalog, stl_of) -> bool:
    """Printed catalog modules: the model's envelope is the catalog size."""
    ok = True
    for name, entry in sorted(catalog.items()):
        if "model" not in entry:
            continue
        stl = stl_of(ROOT / entry["model"])
        if not stl.exists():
            print(f"[FAIL] catalog {name}: model {entry['model']} has no STL")
            ok = False
            continue
        got = bbox_size(stl)
        good = all(abs(g - s) <= SIZE_TOLERANCE for g, s in zip(got, entry["size"]))
        ok &= good
        print(f"[{'ok' if good else 'FAIL'}] catalog {name}: model envelope"
              f" {[round(g, 2) for g in got]}, catalog size {entry['size']}")
    return ok


def main(argv):
    check = "--check" in argv
    only = {a for a in argv[1:] if not a.startswith("--")}

    ok = True
    for gate in GATES:
        ok &= subprocess.run([sys.executable, str(ROOT / "scripts" / gate)]).returncode == 0
    if not ok:
        return 1  # a bad panel config would only add render noise

    with tempfile.TemporaryDirectory() as td:
        def target(real: Path) -> Path:
            return Path(td) / real.relative_to(ROOT) if check else real

        for scad in models():
            if only and scad.stem not in only:
                continue
            stl = BUILD / scad.relative_to(CAD).with_suffix(".stl")
            ok &= run_one(scad, target(stl), stl)

        catalog, _ = panels.load_catalog()
        if not only:
            ok &= check_model_sizes(catalog, lambda scad: target(
                BUILD / scad.relative_to(CAD).with_suffix(".stl")))
        for name in panels.panel_names():
            if only and name not in only:
                continue
            real = BUILD / "panels" / name
            panel = panels.load_panel(name)
            scad = panels.wrapper(name, panel, catalog, target(real / f"{name}.scad"))
            for out, part, extra in PANEL_OUTPUTS:
                ok &= run_one(scad, target(real / out), real / out,
                              ["-D", f'part="{part}"', *extra])
            yaml = firmware.config(name, panel, catalog, target(real / f"{name}.yaml"))
            ok &= firmware.validate(yaml, real / f"{name}.yaml")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
