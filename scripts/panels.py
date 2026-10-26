#!/usr/bin/env python3
"""Panel configs: load, validate, and turn into OpenSCAD wrappers.

A panel is panels/<name>.json: the board, the back cavity, the
components mounted through the front face, and the internals (ESP32
board, battery) that sit in the cavity. Dimensions come from
catalog/components.json, never from the panel file. This module checks
both files and writes the wrapper .scad that cad/lib/panel.scad renders.

Layout rules checked here (tooling rules, such as router bit against
cavity corner, are asserts in cad/lib/panel.scad):

  - the board material, if given, is one of WOODS
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
  - a component's optional "pin" is a usable ESP32-H2 GPIO (PINS), used
    once, or for a family with several pins (FAMILY_PINS, an encoder)
    an object of them by role; pins not given take the next free one in
    PIN_ORDER, and a panel that runs out of pins fails
  - a rotary switch's pin is an ADC pin (ADC_PINS): it reads a resistor
    ladder
  - a display (an LED segment module behind a window routed through the
    face, ADR-0006) is placed like a component: its bezel lies inside
    the cavity outline, clear of every other component's keepout and of
    other bezels; its LED block reaches through the face and stays
    inside the bezel (face_t from digits height less bezel height to
    digits height); its body behind the face fits the cavity depth and
    keeps INTERNAL_CLEARANCE from the cavity wall and from every other
    body, back nut and internal module, and counts as metal for the
    antenna keepout
  - a display shows a knob on the panel ("shows", an encoder or rotary
    switch id, the first one by default): ESPHome's Zigbee on the H2
    cannot receive a value yet (docs/CONCEPT.md, Open questions)

Catalog entries with "measured": false are reported as [info]: their
values are placeholders until someone puts calipers on the real part.
So is a panel whose components are not centered on the face: the
bounding box center of their positions more than CENTER_TOLERANCE off
the board center. Controls are centered unless the panel says why not,
so this is not a failure, only kept visible. Any pin that cannot
wake the H2 from deep sleep (outside WAKE_PINS) is [info] too.

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
# Every family that mounts through the face does it the toggle's way: a
# round hole, a threaded bushing (a pushbutton's threaded body) clamped by
# a nut behind the face, and the body behind that nut. In front sits a
# second nut (toggle, encoder, rotary) or the pushbutton's head.
MOUNT_FIELDS = {
    "hole_d": float, "bushing_d": float, "bushing_len": float,
    "max_panel_t": float, "nut_af": float, "nut_t": float,
    "body": list, "keepout_d": float,
}
# Mounted family -> the two fields its stand-in shows in front of the
# face, in record order: the lever, the knob or the pushbutton's head.
FRONT_FIELDS = {
    "toggle": ["lever_d", "lever_len"],
    "encoder": ["knob_d", "knob_h"],
    "rotary": ["knob_d", "knob_h"],
    "pushbutton": ["cap_d", "cap_h"],
}
# family -> fields it needs beyond COMMON_FIELDS. The FRONT_FIELDS
# families mount through the face; "module" (boards, batteries) sits in
# the cavity. A rotary switch also has its number of positions.
FAMILY_FIELDS = {
    **{f: {**MOUNT_FIELDS, **dict.fromkeys(front, float)} for f, front in FRONT_FIELDS.items()},
    "module": {"size": list, "finish": str},
}
FAMILY_FIELDS["rotary"]["positions"] = int
# A display sits in the cavity and shows through a window routed through
# the face (ADR-0006): digits [w, h, height] is the LED block, height
# above the module's board; window [w, h] the opening in the face; body
# [w, l, depth] the board and its plug behind the face underside; bezel
# [w, h, t] the printed frame on the face around the block. Optional
# model, as for a module, is the bezel's .scad; its envelope is bezel.
FAMILY_FIELDS["display"] = {"digits": list, "window": list, "body": list, "bezel": list}
DISPLAYS = {"display"}
# A bezel overlaps the window edge by at least this all round, to hide
# the chiselled corners (mm).
BEZEL_LAP = 2.0
# Families a display may show (firmware/packages/display.yaml).
SHOWN_FAMILIES = {"encoder", "rotary"}
# Optional module field: model, the repo path of the printable .scad the
# module is (a printed holder); regen_all.py checks its STL bounding box
# against size. Optional module fields: antenna_end ("+x" or "-x", the end of size[0]
# the antenna sits at, before rot) and antenna_keepout (mm past it).
ANTENNA_ENDS = {"+x", "-x"}
MOUNTED = set(FRONT_FIELDS)
FACE = MOUNTED | {"display"}  # families placed under "components"
# Keep-in-sync sweep: FINISHES here and the finish stand-ins in
# cad/lib/panel.scad (internal_stand_in).
FINISHES = {"pcb", "aa_holder"}
# Keep-in-sync sweep: the c_* and i_* index functions in cad/lib/panel.scad.
# The record is the id, family, x, y, these fields, the family's two
# FRONT_FIELDS and the body.
COMPONENT_RECORD = ["hole_d", "bushing_d", "bushing_len", "nut_af", "nut_t"]
# Keep-in-sync sweep: the d_* index functions in cad/lib/panel.scad. A
# display's record is its id, x, y and these fields, flattened.
DISPLAY_RECORD = ["window", "digits", "body", "bezel"]
# Board materials the renders know. Keep-in-sync sweep: PBR() in
# scripts/hero_scene.py. Brass waits for its open question (CONCEPT.md).
WOODS = {"oak", "walnut"}
INTERNAL_CLEARANCE = 2.0  # mm around internals, for wires and fingers
CENTER_TOLERANCE = 1.0  # mm the components' center may sit off the board center
PARTS = ["panel", "punch", "router", "router_step", "hero", "build"]
# ESP32-H2 GPIOs a component may use: 0 to 27 without the SPI flash pins
# (6, 7, 15 to 21), the strapping pins (2, 3, 8, 9, 25) and USB (26, 27),
# per the ESP32-H2 datasheet and ESPHome's esp32 pin checks.
PINS = {0, 1, 4, 5, 10, 11, 12, 13, 14, 22, 23, 24}
# The pins ESPHome can wake the H2 from deep sleep with (LP GPIO 7 to 14).
WAKE_PINS = {10, 11, 12, 13, 14}
# The ADC1 pins among PINS (ADC1 is GPIO1 to 5 on the H2). None can wake.
ADC_PINS = {1, 4, 5}
# Components without a "pin" take the next free one in this order, wake
# capable pins first, then the rest. 13 and 14 double as the 32 kHz
# crystal pins and 23, 24 as UART0, so they come last in their groups.
# Changing the order moves the wiring of every panel that relies on it.
PIN_ORDER = [10, 11, 12, 13, 14, 4, 5, 0, 1, 22, 23, 24]
# Family -> the pins a component of it takes, named, in the order they are
# assigned, so the one that should wake the panel comes first. "pin" is a
# family's only pin; an encoder takes its push and its two phases
# (ADR-0005). In the panel, "pin" is a number for a one pin family and an
# object of role: GPIO for the others, missing roles assigned.
FAMILY_PINS = {"encoder": ["push", "a", "b"], "display": ["clk", "dio"]}
# Families that read their pin as an analog voltage: a rotary switch is a
# resistor ladder on one ADC pin (firmware/packages/rotary.yaml).
ADC_FAMILIES = {"rotary"}
# Families that only drive their pins, a display's CLK and DIO: they take
# the pins that can neither wake nor read a voltage first, so the wake and
# ADC pins stay free for controls (ADR-0007).
OUTPUT_FAMILIES = {"display"}
OUTPUT_ORDER = ([p for p in PIN_ORDER if p not in WAKE_PINS | ADC_PINS]
                + [p for p in PIN_ORDER if p in ADC_PINS]
                + [p for p in PIN_ORDER if p in WAKE_PINS])


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
            ok = (is_num(v) if kind is float else
                  isinstance(v, int) and not isinstance(v, bool) and v >= 2 if kind is int else
                  isinstance(v, kind))
            if not ok:
                errors.append(f"catalog {name}: '{field}' missing or not {kind.__name__}")
        for field in ("body", "size"):
            if field in FAMILY_FIELDS[family] and not is_triple(entry.get(field)):
                errors.append(f"catalog {name}: {field} must be [w, l, depth]")
        if family in DISPLAYS:
            errors += display_catalog_errors(name, entry)
        if family == "module" and entry.get("finish") not in FINISHES:
            errors.append(f"catalog {name}: finish must be one of {sorted(FINISHES)}")
        if family == "module" and "antenna_end" in entry and not (
                entry["antenna_end"] in ANTENNA_ENDS and is_num(entry.get("antenna_keepout"))):
            errors.append(f"catalog {name}: antenna_end must be one of {sorted(ANTENNA_ENDS)}"
                          " with a numeric antenna_keepout")
        if not str(entry.get("source", "")).strip():
            errors.append(f"catalog {name}: source is empty, say where the values come from")
    return catalog, errors


def display_catalog_errors(name, entry):
    """Problems with a display entry beyond its field types."""
    digits, window, bezel = entry.get("digits"), entry.get("window"), entry.get("bezel")
    if not (is_triple(digits) and is_triple(bezel) and isinstance(window, list)
            and len(window) == 2 and all(map(is_num, window))):
        return [f"catalog {name}: digits and bezel must be [w, h, height], window [w, h]"]
    errors = []
    if not all(window[i] > digits[i] for i in (0, 1)):
        errors.append(f"catalog {name}: window {window} must be wider and taller than the"
                      f" digits {digits[:2]}, which pass through it")
    if not all(bezel[i] >= window[i] + 2 * BEZEL_LAP for i in (0, 1)):
        errors.append(f"catalog {name}: bezel {bezel[:2]} must cover the window {window}"
                      f" by {BEZEL_LAP:g} mm all round")
    return errors


def panel_names():
    return sorted(p.stem for p in PANELS.glob("*.json"))


def load_panel(name):
    return json.loads((PANELS / f"{name}.json").read_text())


def board_material(panel):
    return panel["board"].get("material", "oak")


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


def family_of(comp, catalog):
    return catalog.get(comp.get("type"), {}).get("family")


def display_source(comp, comps, catalog):
    """The id of the knob a display shows: its "shows", else the panel's
    first encoder or rotary switch; None if there is no such knob."""
    knobs = [k.get("id") for k in comps if family_of(k, catalog) in SHOWN_FAMILIES]
    shown = comp.get("shows", knobs[0] if knobs else None)
    return shown if shown in knobs else None


def has_display(panel, catalog):
    return any(family_of(c, catalog) in DISPLAYS for c in panel.get("components", []))


def pin_roles(comp, catalog):
    """The named pins a component takes (FAMILY_PINS), ["pin"] by default."""
    return FAMILY_PINS.get(family_of(comp, catalog), ["pin"])


def pin_label(cid, role):
    return str(cid) if role == "pin" else f"{cid} {role}"


def assign_pins(panel, catalog):
    """{component id: {role: GPIO}} with the automatic order filled in, and
    a list of problems. Explicit pins win; the rest take PIN_ORDER in
    component order, then role order, skipping pins already used. A
    family in ADC_FAMILIES takes only ADC_PINS, one in OUTPUT_FAMILIES
    takes them in OUTPUT_ORDER."""
    comps = panel.get("components", [])
    pins, errors = {}, []
    used = {}
    wanted = []  # (id, role, adc, output) still without a pin
    for c in comps:
        cid, roles = c.get("id"), pin_roles(c, catalog)
        family = catalog.get(c.get("type"), {}).get("family")
        adc, output = family in ADC_FAMILIES, family in OUTPUT_FAMILIES
        given = c.get("pin", {} if len(roles) > 1 else None)
        if len(roles) == 1:
            given = {} if given is None else {"pin": given}
        elif not (isinstance(given, dict) and set(given) <= set(roles)):
            errors.append(f"{cid}: pin must be an object with some of {roles}, GPIO each")
            given = {}
        pins[cid] = {}
        for role in roles:
            if role not in given:
                wanted.append((cid, role, adc, output))
                continue
            pin, label = given[role], pin_label(cid, role)
            if not (isinstance(pin, int) and not isinstance(pin, bool)) or pin not in PINS:
                errors.append(f"{label}: pin {pin!r} is not a usable ESP32-H2 GPIO,"
                              f" use one of {sorted(PINS)}")
            elif adc and pin not in ADC_PINS:
                errors.append(f"{label}: pin {pin} is not an ADC pin, a rotary switch"
                              f" reads its resistor ladder on one of {sorted(ADC_PINS)}")
            elif pin in used:
                errors.append(f"{label}: pin {pin} is already used by {used[pin]}")
            else:
                used[pin] = label
                pins[cid][role] = pin
    free = [p for p in PIN_ORDER if p not in used]
    for cid, role, adc, output in wanted:
        fit = ([p for p in free if p in ADC_PINS] if adc else
               [p for p in OUTPUT_ORDER if p in free] if output else free)
        if not fit:
            errors.append(f"{pin_label(cid, role)}: no free ESP32-H2"
                          f" {'ADC ' if adc else ''}pin left")
            continue
        pins[cid][role] = fit[0]
        free.remove(fit[0])
    return pins, errors


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
    if board_material(panel) not in WOODS:
        errors.append(f"board material {board_material(panel)!r} is not one of {sorted(WOODS)}")
    depth = t - face_t
    x0, y0, x1, y1 = rim, rim, w - rim, h - rim
    ids = [c.get("id") for c in comps + internals]
    for dup in {i for i in ids if ids.count(i) > 1}:
        errors.append(f"duplicate id {dup!r}")
    errors += assign_pins(panel, catalog)[1]

    behind = []  # (id, rect) of everything behind the face
    placed = []
    displays = []
    for c in comps:
        cid, kind = c.get("id"), c.get("type")
        if kind not in catalog or catalog[kind]["family"] not in FACE:
            errors.append(f"{cid}: {kind!r} is not a face mounted part in catalog/components.json")
            continue
        if not (is_num(c.get("x")) and is_num(c.get("y"))):
            errors.append(f"{cid}: x and y must be numbers")
            continue
        if catalog[kind]["family"] in DISPLAYS:
            displays.append(c)
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
    bezels = []  # (id, rect)
    for c in displays:
        cid, e, x, y = c["id"], catalog[c["type"]], c["x"], c["y"]
        dh, bt = e["digits"][2], e["bezel"][2]
        if not dh - bt <= face_t <= dh:
            errors.append(f"{cid}: face_t {face_t} must lie from {dh - bt:g} to {dh:g}, so the"
                          f" digits ({dh:g} tall) reach through the face and stay inside"
                          f" the {bt:g} mm bezel")
        bw, bh = e["bezel"][0] / 2, e["bezel"][1] / 2
        bezel = (x - bw, y - bh, x + bw, y + bh)
        if not all(in_rounded_rect(px, py, x0, y0, x1, y1, r)
                   for px in (bezel[0], bezel[2]) for py in (bezel[1], bezel[3])):
            errors.append(f"{cid}: window at ({x}, {y}) leaves no room for its bezel"
                          " inside the cavity")
        for oid, ox, oy, okeep in placed:
            gap = rect_gap(bezel, (ox, oy, ox, oy))
            if gap < okeep / 2:
                errors.append(f"{cid}: bezel {gap:.1f} mm from {oid}, its keepout needs"
                              f" {okeep / 2:.1f}")
        for oid, orect in bezels:
            if rect_gap(bezel, orect) < 0:
                errors.append(f"{cid}: bezel overlaps the bezel of {oid}")
        bezels.append((cid, bezel))
        if depth < e["body"][2]:
            errors.append(f"{cid}: cavity depth {depth} is shallower than the display"
                          f" body ({e['body'][2]})")
        w2, l2 = e["body"][0] / 2, e["body"][1] / 2
        rect = (x - w2, y - l2, x + w2, y + l2)
        corners = [(px, py) for px in (rect[0] - clear, rect[2] + clear)
                   for py in (rect[1] - clear, rect[3] + clear)]
        if not all(in_rounded_rect(px, py, x0, y0, x1, y1, r) for px, py in corners):
            errors.append(f"{cid}: display body at ({x}, {y}) is not {clear:g} mm clear"
                          " of the cavity wall")
        for oid, orect in behind:
            gap = rect_gap(rect, orect)
            if gap < clear:
                errors.append(f"{cid}: display body {gap:.1f} mm from {oid}, needs {clear:g}")
        behind.append((cid, rect))
        if display_source(c, comps, catalog) is None:
            knobs = [k.get("id") for k in comps if family_of(k, catalog) in SHOWN_FAMILIES]
            errors.append(f"{cid}: shows {c.get('shows')!r}, but a display shows one of the"
                          f" panel's knobs {knobs} (encoder or rotary switch); ESPHome's"
                          " Zigbee on the H2 cannot receive a value to show yet")

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
    records, displays = [], []
    for c in panel["components"]:
        e = catalog[c["type"]]
        if e["family"] in DISPLAYS:
            displays.append([c["id"], c["x"], c["y"]] + [v for f in DISPLAY_RECORD for v in e[f]])
            continue
        records.append([c["id"], e["family"], c["x"], c["y"]]
                       + [e[f] for f in COMPONENT_RECORD + FRONT_FIELDS[e["family"]]]
                       + e["body"])
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
        "displays = [",
        *[f"    {scad_value(r)}," for r in displays],
        "];",
        "",
        "panel(part, panel_name, board, cavity, components, internals, displays);",
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
        if not problems:
            outputs = {c["id"] for c in panel["components"]
                       if family_of(c, catalog) in OUTPUT_FAMILIES}
            for cid, roles in assign_pins(panel, catalog)[0].items():
                for role, pin in roles.items():
                    if pin not in WAKE_PINS and cid not in outputs:
                        print(f"[info]  {name}: {pin_label(cid, role)} on GPIO{pin} cannot wake"
                              f" the ESP32-H2 from deep sleep (wake pins {sorted(WAKE_PINS)})")
        used = panel.get("components", []) + panel.get("internals", [])
        for kind in sorted({c.get("type") for c in used}):
            if kind in catalog and not catalog[kind]["measured"]:
                print(f"[info]  {kind}: catalog values are not measured yet ({catalog[kind]['source'][:60]}...)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
