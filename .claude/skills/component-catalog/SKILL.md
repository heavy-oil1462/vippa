---
name: component-catalog
description: Add a panel part to catalog/components.json or replace its placeholder values with measured ones. Use when a panel needs a part the catalog lacks, when the user has measured a part, or when the pipeline reports a part as not measured.
---

# Component catalog

```bash
python3 scripts/panels.py                 # validates the catalog, then every panel
```

Two families. `toggle` mounts through the face; `module` (ESP32
board, battery) lies in the cavity and is placed under `internals` in a
panel.

## Toggle fields (all required)

| Field | Meaning | How to get it |
| --- | --- | --- |
| family | stand-in shape and firmware kind; only `toggle` so far | |
| hole_d | drill size for the face hole | bushing_d plus a little, check on scrap |
| bushing_d | thread outer diameter | calipers |
| bushing_len | thread length from the body | calipers |
| max_panel_t | thickest face both nuts still grip | test fit on stepped scrap |
| nut_af, nut_t | front and back nut, across flats and thickness | calipers |
| lever_d, lever_len | lever tip diameter, length above the bushing | calipers |
| body | [w, l, depth] behind the back nut, terminals included | calipers |
| keepout_d | face clearance for fingers and the nut wrench | judgement, say so in source |
| measured | true only once every value above came off the real part | |
| source | part number and where each value came from | |

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
- A new family needs a stand-in module and a case in finished_panel()
  in cad/lib/panel.scad, and FAMILY_FIELDS in scripts/panels.py. A new
  module finish needs a branch in internal_stand_in() and FINISHES in
  panels.py. Keep-in-sync
  sweep for record fields: COMPONENT_RECORD in panels.py and the c_*
  functions in panel.scad.
- After a change, run regen-outputs and look at the panels using the
  part; regenerate media/ if the hero panel uses it.

## When it fails

- `'field' missing or not ...`: the entry lacks a field or has the wrong
  type; numbers must be numbers, body a list of three.
- `source is empty`: write where the values came from.
