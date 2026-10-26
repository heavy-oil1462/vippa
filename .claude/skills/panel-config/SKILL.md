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

## Examples

panels/ holds ready-made examples, each with a README picture in
media/panels/: three_toggles (the first panel, three full size toggles
in a row), bedside (one toggle, walnut, the ESP32 board beside it),
hallway (two toggles in a row), scenes (six miniature toggles in two
rows of three, a 22 mm board, the ESP32 board turned 90 beside them),
dimmer (one encoder knob, walnut, a 22 mm board) and living_room (a row
of a rotary switch, two pushbuttons and an encoder knob, the battery
below the row and the ESP32 board above it) and thermostat (an LED
segment display above an encoder knob, walnut) and garage (two
toggles with a pilot lamp above each and a pushbutton between them).
Start a new panel from the closest one.

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
- material: the board wood, one of WOODS in panels.py (oak, walnut);
  the renders use it. Default oak.
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
  free pin in PIN_ORDER (wake capable 10 to 14 first). An encoder
  (encoder_knob) takes three pins; its pin is an object with some of
  push, a and b, e.g. `"pin": {"push": 10}`, the rest assigned. A
  rotary switch (rotary_switch) takes one ADC pin, 1, 4 or 5, and can
  never wake the panel (ADR-0005). panels.py prints
  `[info] ... cannot wake` for any pin outside 10 to 14. See the
  firmware skill.
- A display (led_segment_4d) goes under components with x, y the
  center of its window, centered with the controls. Its bezel must lie
  inside the cavity outline and clear every other component's keepout,
  its body behind the face 2 mm clear of the cavity wall and everything
  else behind the face, and the face between digits height less bezel
  t and digits height (3.2 to 7.2 mm). It shows a knob, `"shows":
  "<id>"` of an encoder or rotary switch, else the first one; a panel
  with a display needs one. Its pin is an object with some of clk and
  dio; left out, they come after the wake and ADC pins (ADR-0007).
- A pilot lamp (pilot_lamp_12mm) goes under components like a
  pushbutton and goes through the same checks. `"follows": "<id>"`
  names the toggle, encoder (its push) or pushbutton it lights after;
  a lamp needs one. `"color"` is one of its catalog colors (red, amber,
  green), the first by default. Its pin comes after the wake and ADC
  pins (ADR-0007). It is metal for the antenna keepout.
- Knobs need room: keepout_d of a knob is the knob plus fingers, so
  knobs sit further apart than toggles, and a pushbutton between two
  knobs saves width.

## Procedure

1. Write or edit the JSON, run `panels.py <name>` until it is `[ok]`.
2. Run `regen_all.py <name>`, then look at `front.png` and `back.png` in
   build/panels/<name>/ with the Read tool. State what they should show
   first.
3. Render its picture with `render_hero.py --panels --panel <name>`
   (hero-render skill) into media/panels/<name>.png, and give it a line
   in the README's Example panels section. If the panel is the hero
   panel (HERO_PANEL in render_hero.py), regenerate the media/ shots
   too, in the same change.
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
- `pin ... is not an ADC pin`: a rotary switch reads a resistor
  ladder; give it 1, 4 or 5, or leave pin out.
- `pin must be an object`: an encoder's pin names its roles,
  `{"push": .., "a": .., "b": ..}`, a display's `{"clk": .., "dio": ..}`.
- `leaves no room for its bezel inside the cavity`, `display body ...
  not 2 mm clear`: move the display inward or grow the board.
- `bezel ... its keepout needs`: move the display away from the knob.
- `face_t ... must lie from`: the display's digits would not reach
  through the face or would stand out of the bezel; change face_t.
- `a display shows one of the panel's knobs`: give the panel an encoder
  or rotary switch, or fix `"shows"`.
- `a lamp follows one of the panel's toggles, encoders or
  pushbuttons`: set `"follows"` to the id of one of them.
- `color ... is not one of`: pick a color from the catalog entry.
- `holder screws reach ... mm into a ... mm face`: the face is too thin
  for holder_screw_len; use shorter screws or a thicker face.
- An assert from cad/lib/panel.scad during regen (bit radius, rail
  width, router base span, bed size) is a tooling limit: change the
  panel, never the assert.
