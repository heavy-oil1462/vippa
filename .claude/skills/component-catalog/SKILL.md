---
name: component-catalog
description: Add a panel part to catalog/components.json or replace its placeholder values with measured ones. Use when a panel needs a part the catalog lacks, when the user has measured a part, or when the pipeline reports a part as not measured.
---

# Component catalog

```bash
python3 scripts/panels.py                 # validates the catalog, then every panel
```

Five families. `toggle`, `encoder`, `rotary` and `pushbutton` mount
through the face (`FRONT_FIELDS` in scripts/panels.py); `module`
(ESP32 board, battery) lies in the cavity and is placed under
`internals` in a panel.

In the catalog: `toggle_12mm`, `toggle_6mm` (toggle), `encoder_knob`
(encoder with push and a knurled aluminium knob), `rotary_switch` (1
pole 6 positions, bakelite pointer knob) and `pushbutton_16mm`
(pushbutton), all placeholders.

## Mount fields (every face mounted family, all required)

Every face mounted family mounts the toggle's way: a round hole, a
threaded bushing (a pushbutton's threaded body), a nut behind the face
and the body behind that nut. In front sits a second nut, or a
pushbutton's head.

| Field | Meaning | How to get it |
| --- | --- | --- |
| family | stand-in shape and firmware package | |
| hole_d | drill size for the face hole | bushing_d plus a little, check on scrap |
| bushing_d | thread outer diameter | calipers |
| bushing_len | thread length from the body (a pushbutton: from the head) | calipers |
| max_panel_t | thickest face the nuts (or head and nut) still grip | test fit on stepped scrap |
| nut_af, nut_t | the nuts, across flats and thickness | calipers |
| body | [w, l, depth] behind the back nut, terminals included | calipers |
| keepout_d | face clearance for fingers, knob and the nut wrench | judgement, say so in source |
| measured | true only once every value above came off the real part | |
| source | part number and where each value came from | |

## Family fields (in front of the face)

| Family | Fields | Meaning |
| --- | --- | --- |
| toggle | lever_d, lever_len | lever tip diameter, length above the bushing |
| encoder | knob_d, knob_h | knob diameter and height |
| rotary | knob_d, knob_h, positions | knob, and the number of switch positions (an integer, at least 2) |
| pushbutton | cap_d, cap_h | head diameter and height above the face |

## Module fields

| Field | Meaning | How to get it |
| --- | --- | --- |
| size | [w, l, depth] envelope, depth measured from the face underside, cables and headers included | calipers |
| finish | stand-in look: `pcb` or `aa_holder` | |
| model | optional: repo path of the printable .scad this module is (a printed holder). regen_all.py fails if its STL bounding box differs from size | |
| antenna_end, antenna_keepout | optional: `+x` or `-x` end of w where the antenna is, and the metal-free distance past it | module datasheet |
| measured, source | as for toggles | |

## Rules

- Never guess a value and set measured to true. A datasheet value is
  fine with the datasheet named in source; mark measured true only for
  calipered parts.
- A new face mounted family needs its two front fields in FRONT_FIELDS
  in scripts/panels.py, a stand-in module and a case in finished_panel()
  in cad/lib/panel.scad, and a firmware package in FAMILY_PACKAGES
  (firmware skill); one that takes several pins goes into FAMILY_PINS
  (ADR-0005). A new module finish needs a branch in internal_stand_in()
  and FINISHES in panels.py. Keep-in-sync sweep for record fields:
  COMPONENT_RECORD and FRONT_FIELDS in panels.py and the c_* functions
  in panel.scad. A new stand-in color goes into the material sweep
  (hero-render skill).
- After a change, run regen-outputs and look at the panels using the
  part; regenerate media/ if the hero panel uses it.

## When it fails

- `'field' missing or not ...`: the entry lacks a field or has the wrong
  type; numbers must be numbers, body a list of three.
- `source is empty`: write where the values came from.
