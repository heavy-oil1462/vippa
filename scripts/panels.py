#!/usr/bin/env python3
"""Panel configs: load, validate, and turn into OpenSCAD wrappers.

A panel is panels/<name>.json: the board, the back cavity, the
components mounted through the front face, and the internals (ESP32
board, battery) that sit in the cavity. Dimensions come from
catalog/components.json, never from the panel file. This module checks
both files and writes the wrapper .scad that cad/lib/panel.scad renders.

Layout rules checked here (tooling rules, such as router bit against
cavity corner, are asserts in cad/lib/panel.scad):

  - every type exists in the catalog with the right kind, ids are unique
  - the face is thin enough for every bushing (face_t <= max_panel_t)
  - the cavity is deep enough for every back nut and body, and for
    every internal module
  - every body, back nut and internal module sits inside the cavity,
    internals INTERNAL_CLEARANCE clear of the cavity wall
  - internals stay INTERNAL_CLEARANCE clear of each other and of every
    component's body and back nut, so wires and fingers fit
  - components are at least their keepout radii apart on the face
  - a module with an antenna keeps antenna_keepout mm past its antenna
    end free of metal (every component's body and nut, every other
    module), since metal there detunes the antenna; wood does not count

Catalog entries with "measured": false are reported as [info]: their
values are placeholders until someone puts calipers on the real part.
So is a panel whose components are not centered on the face: the
bounding box center of their positions more than CENTER_TOLERANCE off
the board center. Controls are centered unless the panel says why not,
so this is not a failure, only kept visible.

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

COMMON_FIELDS = {"description": str, "family": str, "measured": bool, "source": str}
# family -> fields it needs beyond COMMON_FIELDS. "toggle" mounts through
# the face; "module" (boards, batteries) sits in the cavity.
FAMILY_FIELDS = {
    "toggle": {
        "hole_d": float, "bushing_d": float, "bushing_len": float,
        "max_panel_t": float, "nut_af": float, "nut_t": float,
        "lever_d": float, "lever_len": float, "body": list, "keepout_d": float,
    },
    "module": {"size": list, "finish": str},
}
# Optional module field: model, the repo path of the printable .scad the
# module is (a printed holder); regen_all.py checks its STL bounding box
# against size. Optional module fields: antenna_end ("+x" or "-x", the end of size[0]
# the antenna sits at, before rot) and antenna_keepout (mm past it).
ANTENNA_ENDS = {"+x", "-x"}
MOUNTED = {"toggle"}
# Keep-in-sync sweep: FINISHES here and the finish stand-ins in
# cad/lib/panel.scad (internal_stand_in).
FINISHES = {"pcb", "aa_holder"}
# Keep-in-sync sweep: the c_* and i_* index functions in cad/lib/panel.scad.
COMPONENT_RECORD = ["hole_d", "bushing_d", "bushing_len", "nut_af", "nut_t",
                    "lever_d", "lever_len"]
INTERNAL_CLEARANCE = 2.0  # mm around internals, for wires and fingers
CENTER_TOLERANCE = 1.0  # mm the components' center may sit off the board center
PARTS = ["panel", "punch", "router", "hero", "build"]


def is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def is_triple(v):
    return isinstance(v, list) and len(v) == 3 and all(map(is_num, v))


def load_catalog():
    """The catalog and a list of problems with it."""
    catalog = json.loads(CATALOG.read_text())
    errors = []
    for name, entry in catalog.items():
        family = entry.get("family")
        if family not in FAMILY_FIELDS:
            errors.append(f"catalog {name}: family must be one of {sorted(FAMILY_FIELDS)}")
            continue
        for field, kind in {**COMMON_FIELDS, **FAMILY_FIELDS[family]}.items():
            v = entry.get(field)
            ok = is_num(v) if kind is float else isinstance(v, kind)
            if not ok:
                errors.append(f"catalog {name}: '{field}' missing or not {kind.__name__}")
        for field in ("body", "size"):
            if field in FAMILY_FIELDS[family] and not is_triple(entry.get(field)):
                errors.append(f"catalog {name}: {field} must be [w, l, depth]")
        if family == "module" and entry.get("finish") not in FINISHES:
            errors.append(f"catalog {name}: finish must be one of {sorted(FINISHES)}")
        if family == "module" and "antenna_end" in entry and not (
                entry["antenna_end"] in ANTENNA_ENDS and is_num(entry.get("antenna_keepout"))):
            errors.append(f"catalog {name}: antenna_end must be one of {sorted(ANTENNA_ENDS)}"
                          " with a numeric antenna_keepout")
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


def rect_gap(a, b):
    """Clear distance between two axis aligned rects (x0, y0, x1, y1);
    negative when they overlap."""
    dx = max(b[0] - a[2], a[0] - b[2])
    dy = max(b[1] - a[3], a[1] - b[3])
    if dx < 0 and dy < 0:
        return max(dx, dy)
    return math.hypot(max(dx, 0), max(dy, 0))


def internal_footprint(item, entry):
    """(x0, y0, x1, y1) of an internal module, rot 90 turns it on the face."""
    w, l, _ = entry["size"]
    if item.get("rot", 0) == 90:
        w, l = l, w
    x, y = item["x"], item["y"]
    return (x - w / 2, y - l / 2, x + w / 2, y + l / 2)


def antenna_zone(item, entry, rect):
    """(x0, y0, x1, y1) that must stay free of metal, or None."""
    if "antenna_end" not in entry:
        return None
    k, sign = entry["antenna_keepout"], 1 if entry["antenna_end"] == "+x" else -1
    x0, y0, x1, y1 = rect
    if item.get("rot", 0) == 90:  # +x turns into +y
        return (x0, y1, x1, y1 + k) if sign > 0 else (x0, y0 - k, x1, y0)
    return (x1, y0, x1 + k, y1) if sign > 0 else (x0 - k, y0, x0, y1)


def back_footprint(comp, entry):
    """(x0, y0, x1, y1) behind the face: the body and the back nut."""
    nut = entry["nut_af"] / math.cos(math.radians(30)) / 2
    half_w = max(entry["body"][0] / 2, nut)
    half_l = max(entry["body"][1] / 2, nut)
    return (comp["x"] - half_w, comp["y"] - half_l, comp["x"] + half_w, comp["y"] + half_l)


def validate(panel, catalog):
    """Problems with one panel, as a list of strings."""
    errors = []
    try:
        b, cav, comps = panel["board"], panel["cavity"], panel["components"]
        w, h, t = b["w"], b["h"], b["t"]
        face_t, rim, r = cav["face_t"], cav["rim"], cav["r"]
    except (KeyError, TypeError) as e:
        return [f"missing key {e}"]
    internals = panel.get("internals", [])
    if not all(map(is_num, [w, h, t, face_t, rim, r, b.get("chamfer", 0)])):
        return ["board and cavity values must be numbers"]
    if not comps:
        return ["no components"]
    depth = t - face_t
    x0, y0, x1, y1 = rim, rim, w - rim, h - rim
    ids = [c.get("id") for c in comps + internals]
    for dup in {i for i in ids if ids.count(i) > 1}:
        errors.append(f"duplicate id {dup!r}")

    behind = []  # (id, rect) of everything behind the face
    placed = []
    for c in comps:
        cid, kind = c.get("id"), c.get("type")
        if kind not in catalog or catalog[kind]["family"] not in MOUNTED:
            errors.append(f"{cid}: {kind!r} is not a face mounted part in catalog/components.json")
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
        behind.append((cid, back_footprint(c, e)))

    clear = INTERNAL_CLEARANCE
    antennas = []  # (id, zone)
    for item in internals:
        iid, kind = item.get("id"), item.get("type")
        if kind not in catalog or catalog[kind]["family"] != "module":
            errors.append(f"{iid}: {kind!r} is not a module in catalog/components.json")
            continue
        if not (is_num(item.get("x")) and is_num(item.get("y"))) or item.get("rot", 0) not in (0, 90):
            errors.append(f"{iid}: x and y must be numbers, rot 0 or 90")
            continue
        e = catalog[kind]
        if depth < e["size"][2]:
            errors.append(f"{iid}: cavity depth {depth} is shallower than the module ({e['size'][2]})")
        fx0, fy0, fx1, fy1 = rect = internal_footprint(item, e)
        corners = [(px, py) for px in (fx0 - clear, fx1 + clear) for py in (fy0 - clear, fy1 + clear)]
        if not all(in_rounded_rect(px, py, x0, y0, x1, y1, r) for px, py in corners):
            errors.append(f"{iid}: at ({item['x']}, {item['y']}) it is not {clear:g} mm clear"
                          " of the cavity wall")
        for oid, orect in behind:
            gap = rect_gap(rect, orect)
            if gap < clear:
                errors.append(f"{iid}: {gap:.1f} mm from {oid}, needs {clear:g}")
        behind.append((iid, rect))
        zone = antenna_zone(item, e, rect)
        if zone:
            antennas.append((iid, zone))
    for aid, zone in antennas:
        for oid, orect in behind:
            if oid != aid and rect_gap(zone, orect) < 0:
                errors.append(f"{aid}: {oid} is metal inside the antenna keepout")
    return errors


def center_offset(panel):
    """(dx, dy) from the board center to the bounding box center of the
    component positions, or None when there is nothing to measure."""
    try:
        w, h = panel["board"]["w"], panel["board"]["h"]
        xs = [c["x"] for c in panel["components"]]
        ys = [c["y"] for c in panel["components"]]
    except (KeyError, TypeError):
        return None
    if not xs or not all(map(is_num, xs + ys + [w, h])):
        return None
    return ((min(xs) + max(xs)) / 2 - w / 2, (min(ys) + max(ys)) / 2 - h / 2)


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
    internals = []
    for item in panel.get("internals", []):
        e = catalog[item["type"]]
        fx0, fy0, fx1, fy1 = internal_footprint(item, e)
        internals.append([item["id"], e["finish"], item["x"], item["y"],
                          fx1 - fx0, fy1 - fy0, e["size"][2]])
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
        "internals = [",
        *[f"    {scad_value(r)}," for r in internals],
        "];",
        "",
        "panel(part, panel_name, board, cavity, components, internals);",
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
        off = center_offset(panel)
        if off and max(map(abs, off)) > CENTER_TOLERANCE:
            print(f"[info]  {name}: components center {off[0]:+g}, {off[1]:+g} mm (x, y)"
                  " off the board center")
        used = panel.get("components", []) + panel.get("internals", [])
        for kind in sorted({c.get("type") for c in used}):
            if kind in catalog and not catalog[kind]["measured"]:
                print(f"[info]  {kind}: catalog values are not measured yet ({catalog[kind]['source'][:60]}...)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
