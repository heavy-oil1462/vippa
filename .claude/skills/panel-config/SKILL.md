---
name: panel-config
description: Add or change a Vippa panel (panels/<name>.json), validate it and look at the result. Use when the user wants a new panel, a different layout, board size or cavity, or asks whether a layout works.
---

# Panel config

```bash
python3 scripts/panels.py <name>          # validate one panel, fast
python3 scripts/regen_all.py <name>       # templates and previews into build/panels/<name>/
```

## Format

```json
{
  "description": "what this panel is",
  "board": {"w": 190, "h": 107, "t": 27, "chamfer": 2, "material": "oak"},
  "cavity": {"face_t": 4, "rim": 15, "r": 8},
  "components": [
    {"id": "left", "type": "toggle_12mm", "x": 45, "y": 53.5},
    {"id": "middle", "type": "toggle_12mm", "x": 95, "y": 53.5},
    {"id": "right", "type": "toggle_12mm", "x": 145, "y": 53.5}
  ],
  "internals": [
    {"id": "battery", "type": "battery_2aa_holder", "x": 95, "y": 30},
    {"id": "esp", "type": "esp32_devboard", "x": 135, "y": 77, "rot": 0}
  ]
}
```

## Layout: start centered

A new panel starts from a centered row: put the components first, with
the bounding box of their x, y on the board center (w/2, h/2). Then
place the internals in the bands of cavity around the row, the inline
battery holder on one side and the ESP32 board on the other, and size
the board as small as the checks allow. Grow the board to make room;
never move the row off center for the internals. panels.py prints
`[info] <name>: components center ... off the board center` when the
row is more than 1 mm off; a panel that breaks the rule on purpose says
why in its description.

- Millimetres. x, y are hole centers measured from the reference corner:
  bottom left seen from the front.
- face_t: wood left over the cavity; it must not exceed any component's
  max_panel_t. rim: wood around the cavity. r: cavity corner radius, at
  least the router bit radius.
- type is a key of catalog/components.json. A part that is not there
  is added with the component-catalog skill first, never inlined here.
- internals are catalog modules (ESP32 board, battery) lying in the
  cavity, x, y their center seen from the front, rot 0 or 90. They must
  keep 2 mm (INTERNAL_CLEARANCE in panels.py) from the cavity wall,
  from each other and from every switch body and back nut.
- A module with an antenna needs antenna_keepout mm past its antenna end
  free of metal (switch bodies, battery). Put the antenna end toward a
  cavity wall; wood in the keepout is fine.
- id is the component's name and its Home Assistant entity name in the
  generated firmware, so keep it stable and meaningful.
- pin (optional) is the component's ESP32-H2 GPIO, one of PINS in
  panels.py, each used once. Without it the component takes the next
  free pin in PIN_ORDER (wake capable 10 to 14 first). panels.py prints
  `[info] ... cannot wake` for a toggle outside 10 to 14. See the
  firmware skill.

## Procedure

1. Write or edit the JSON, run `panels.py <name>` until it is `[ok]`.
2. Run `regen_all.py <name>`, then look at `front.png` and `back.png` in
   build/panels/<name>/ with the Read tool. State what they should show
   first.
3. If the panel is the hero panel (HERO_PANEL in render_hero.py),
   regenerate media/ with the hero-render skill in the same change.
4. Run verify before committing.

## When it fails

- `face_t ... thicker than the bushing takes`: thin the face (raise
  cavity depth) or pick a part with a longer bushing.
- `cavity depth ... shallower than back nut plus body`: thicker board or
  thinner face.
- `leaves the cavity` or `not ... clear of the cavity wall`: move the
  part inward, shrink the rim or grow the board.
- `... mm from ..., needs 2`: two things behind the face are too close.
- `... is metal inside the antenna keepout`: turn the board so its
  antenna end faces a wall with nothing metal in between.
- `keepouts need`: spread the parts; keepout_d is in the catalog.
- `holder screws reach ... mm into a ... mm face`: the face is too thin
  for holder_screw_len; use shorter screws or a thicker face.
- An assert from cad/lib/panel.scad during regen (bit radius, rail
  width, router base span, bed size) is a tooling limit: change the
  panel, never the assert.
