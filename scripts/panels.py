#!/usr/bin/env python3
"""Panel configs: load, validate, and turn into OpenSCAD wrappers.

A panel is panels/<name>.json: the board, the back cavity and a list of
components placed on the front face. Component dimensions come from
catalog/components.json, never from the panel file. This module checks
both files and writes the wrapper .scad that cad/lib/panel.scad renders.

Layout rules checked here (tooling rules, such as router bit against
cavity corner, are asserts in cad/lib/panel.scad):

  - every component type exists in the catalog, ids are unique
  - the face is thin enough for every bushing (face_t <= max_panel_t)
  - the cavity is deep enough for the back nut and body
  - every body and back nut sits inside the cavity
  - neighbours are at least their keepout radii apart

Catalog entries with "measured": false are reported as [info]: their
values are placeholders until someone puts calipers on the real part.

Usage:
    scripts/panels.py              # validate every panel, the gate
    scripts/panels.py <name> ...   # validate these panels only
"""

import json
import math
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "catalog" / "components.json"
PANELS = ROOT / "panels"
LIB = ROOT / "cad" / "lib" / "panel.scad"
PARAMS = ROOT / "cad" / "design_params.scad"

CATALOG_FIELDS = {
    "description": str, "family": str, "hole_d": float, "bushing_d": float,
    "bushing_len": float, "max_panel_t": float, "nut_af": float,
    "nut_t": float, "lever_d": float, "lever_len": float, "body": list,
    "keepout_d": float, "measured": bool, "source": str,
}
FAMILIES = {"toggle"}
# Keep-in-sync sweep: the c_* index functions in cad/lib/panel.scad.
COMPONENT_RECORD = ["hole_d", "bushing_d", "bushing_len", "nut_af", "nut_t",
                    "lever_d", "lever_len"]
PARTS = ["panel", "punch", "router", "hero", "build"]


def is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def load_catalog():
    """The catalog and a list of problems with it."""
    catalog = json.loads(CATALOG.read_text())
    errors = []
    for name, entry in catalog.items():
        for field, kind in CATALOG_FIELDS.items():
            v = entry.get(field)
            ok = is_num(v) if kind is float else isinstance(v, kind)
            if not ok:
                errors.append(f"catalog {name}: '{field}' missing or not {kind.__name__}")
        if entry.get("family") not in FAMILIES:
            errors.append(f"catalog {name}: family must be one of {sorted(FAMILIES)}")
        body = entry.get("body")
        if not (isinstance(body, list) and len(body) == 3 and all(map(is_num, body))):
            errors.append(f"catalog {name}: body must be [w, l, depth]")
        if not str(entry.get("source", "")).strip():
            errors.append(f"catalog {name}: source is empty, say where the values come from")
    return catalog, errors


def panel_names():
    return sorted(p.stem for p in PANELS.glob("*.json"))


def load_panel(name):
    return json.loads((PANELS / f"{name}.json").read_text())


def in_rounded_rect(px, py, x0, y0, x1, y1, r):
    """Is point (px, py) inside the rectangle with corner radius r."""
    if not (x0 <= px <= x1 and y0 <= py <= y1):
        return False
    cx = min(max(px, x0 + r), x1 - r)
    cy = min(max(py, y0 + r), y1 - r)
    return math.hypot(px - cx, py - cy) <= r + 1e-9


def validate(panel, catalog):
    """Problems with one panel, as a list of strings."""
    errors = []
    try:
        b, cav, comps = panel["board"], panel["cavity"], panel["components"]
        w, h, t = b["w"], b["h"], b["t"]
        face_t, rim, r = cav["face_t"], cav["rim"], cav["r"]
    except (KeyError, TypeError) as e:
        return [f"missing key {e}"]
    if not all(map(is_num, [w, h, t, face_t, rim, r, b.get("chamfer", 0)])):
        return ["board and cavity values must be numbers"]
    if not comps:
        return ["no components"]
    depth = t - face_t
    x0, y0, x1, y1 = rim, rim, w - rim, h - rim
    ids = [c.get("id") for c in comps]
    for dup in {i for i in ids if ids.count(i) > 1}:
        errors.append(f"duplicate component id {dup!r}")
    placed = []
    for c in comps:
        cid, kind = c.get("id"), c.get("type")
        if kind not in catalog:
            errors.append(f"{cid}: unknown type {kind!r}, add it to catalog/components.json")
            continue
        if not (is_num(c.get("x")) and is_num(c.get("y"))):
            errors.append(f"{cid}: x and y must be numbers")
            continue
        e, x, y = catalog[kind], c["x"], c["y"]
        if face_t > e["max_panel_t"]:
            errors.append(f"{cid}: face_t {face_t} is thicker than the bushing takes"
                          f" ({kind} max_panel_t {e['max_panel_t']})")
        need = e["nut_t"] + e["body"][2]
        if depth < need:
            errors.append(f"{cid}: cavity depth {depth} is shallower than back nut"
                          f" plus body ({need})")
        bw, bl = e["body"][0] / 2, e["body"][1] / 2
        nut = e["nut_af"] / math.cos(math.radians(30)) / 2
        corners = [(x + sx * bw, y + sy * bl) for sx in (-1, 1) for sy in (-1, 1)]
        corners += [(x + nut * math.cos(math.radians(a)), y + nut * math.sin(math.radians(a)))
                    for a in range(0, 360, 60)]
        if not all(in_rounded_rect(px, py, x0, y0, x1, y1, r) for px, py in corners):
            errors.append(f"{cid}: body or back nut at ({x}, {y}) leaves the cavity")
        for oid, ox, oy, okeep in placed:
            gap = math.hypot(x - ox, y - oy)
            if gap < (e["keepout_d"] + okeep) / 2:
                errors.append(f"{cid}: {gap:.1f} mm from {oid}, keepouts need"
                              f" {(e['keepout_d'] + okeep) / 2:.1f}")
        placed.append((cid, x, y, e["keepout_d"]))
    return errors


def scad_value(v):
    if isinstance(v, str):
        return json.dumps(v)
    if isinstance(v, list):
        return "[" + ", ".join(scad_value(i) for i in v) + "]"
    return f"{v:g}" if isinstance(v, float) else str(v)


def wrapper(name, panel, catalog, out: Path) -> Path:
    """Write the OpenSCAD wrapper for one panel to out (a .scad path)."""
    b, cav = panel["board"], panel["cavity"]
    records = []
    for c in panel["components"]:
        e = catalog[c["type"]]
        records.append([c["id"], e["family"], c["x"], c["y"]]
                       + [e[f] for f in COMPONENT_RECORD] + e["body"])
    rel = lambda p: os.path.relpath(p, out.parent)  # noqa: E731
    lines = [
        f"// GENERATED by scripts/panels.py from panels/{name}.json and the catalog.",
        "// Do not edit: change the JSON and run scripts/regen_all.py.",
        f"use <{rel(LIB)}>",
        f"include <{rel(PARAMS)}>",
        "",
        "/* [Part] */",
        f'part = "panel"; // [{", ".join(PARTS)}]',
        "",
        "/* [Hidden] */",
        f"panel_name = {scad_value(name)};",
        f"board = {scad_value([b['w'], b['h'], b['t'], b.get('chamfer', 0)])};",
        f"cavity = {scad_value([cav['face_t'], cav['rim'], cav['r']])};",
        "components = [",
        *[f"    {scad_value(r)}," for r in records],
        "];",
        "",
        "panel(part, panel_name, board, cavity, components);",
    ]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n")
    return out


def main(argv):
    catalog, errors = load_catalog()
    for e in errors:
        print(f"[FAIL] {e}")
    if errors:
        return 1
    names = argv[1:] or panel_names()
    ok = True
    for name in names:
        panel = load_panel(name)
        problems = validate(panel, catalog)
        ok &= not problems
        print(f"[{'FAIL' if problems else 'ok'}] panels/{name}.json")
        for p in problems:
            print(f"        {p}")
        for kind in sorted({c.get("type") for c in panel.get("components", [])}):
            if kind in catalog and not catalog[kind]["measured"]:
                print(f"[info]  {kind}: catalog values are not measured yet ({catalog[kind]['source'][:60]}...)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
