# Concept

A Vippa panel is a slab of hardwood (oak, walnut) or brass with panel
hardware set into its face. It hangs on a wall or stands on a desk and
controls Home Assistant through an ESP32 behind it. It should feel like
a piece of old lab equipment: heavy, deliberate, no screen.

## Component families

Each family becomes catalog entries (catalog/components.json) with
measured or datasheet values.

- Toggle switches: full size (12 mm, 15/32 in bushing) and miniature
  (6 mm, 1/4 in bushing), bat handles. On/off and momentary. The first
  family in the catalog.
- Rotary controls: incremental encoders with push (for dimmers and
  volume) and multi-position rotary switches (scene selectors), with
  machined or bakelite knobs.
- Pushbuttons: momentary, metal, optionally illuminated.
- Pilot lamps: bezel indicators, LED inside.
- Analog meters: moving-coil panel meters driven by ESP32 PWM, with
  printed custom scales (temperature, power, anything HA knows).

## How a panel is made

1. Describe the panel in `panels/<name>.json`: board, cavity and the
   components with their positions from the reference corner.
2. `python3 scripts/regen_all.py` checks it and writes both templates.
3. Mark the reference edges on the board (bottom and left seen from the
   front). Seat the punch template on the front face, fences hard
   against both edges, and punch every hole center.
4. Drill each hole from its punch mark; the template is engraved with
   the drill size next to each bore.
5. Turn the board over its long edge. Seat the router template on the
   back, fences on the same two edges, and route the cavity with the
   guide bushing against the template. The template is engraved with
   the bushing, bit and depth it was made for.
6. Fit the hardware, wire it to the ESP32 in the cavity, close the back.

## Decisions

- Board thickness, cavity rim, corner radius and face thickness are per
  panel, in the panel JSON.
- Templates register on edge fences along two reference edges. A
  diamond relief groove runs along each fence root so an eased arris or
  dust cannot lift the template.
- Front template bores guide the center punch only, sized from the
  measured punch nose. Drilling is freehand from the mark.
- The cavity is routed by hand with a guide bushing against a printed
  template, not drilled or CNC cut. The template extends router_margin
  past the board on every side so the router base stays supported.
- Panel configs are JSON (stdlib, validated before rendering, readable
  by the firmware generator later).

## Open questions

- Back of the panel: a cover plate in a rebate, or a screwed panel.
  Needs a second, shallower router template step.
- Anti-rotation for toggles: a second small hole for the lock washer tab,
  or rely on the nut torque.
- Mounting: wall (keyhole, French cleat) and desk (angled base).
- Power: USB C, 5 V wall supply, or PoE (ESP32 Ethernet board).
- Boards larger than the print bed: split templates or a two-step
  registration.
- Brass panels: same templates, or a separate path.
