# Concept

A Vippa panel is a slab of hardwood (oak, walnut) or brass with panel
hardware set into its face. It hangs on a wall or stands on a desk and
controls Home Assistant through an ESP32 behind it. It should feel like
a piece of old lab equipment: heavy, deliberate, no screen.

## Component families

Each family becomes an entry in the component catalog (cad/lib/) with
measured or datasheet values. Nothing here is a chosen part yet.

- Toggle switches: full size (12 mm, 15/32 in bushing) and miniature
  (6 mm, 1/4 in bushing), bat handles. On/off and momentary.
- Rotary controls: incremental encoders with push (for dimmers and
  volume) and multi-position rotary switches (scene selectors), with
  machined or bakelite knobs.
- Pushbuttons: momentary, metal, optionally illuminated.
- Pilot lamps: bezel indicators, LED inside.
- Analog meters: moving-coil panel meters driven by ESP32 PWM, with
  printed custom scales (temperature, power, anything HA knows).

## How a panel is made

1. Pick a board and the components, lay them out in a panel file.
2. Print the drill guide for that layout. It registers on two board
   edges (or clamps over the board) and holds a bore for each hole.
3. Drill the through holes for the bushings and Forstner the back
   pockets from behind, so a thick board leaves a thin face that the
   bushing reaches through.
4. Fit the hardware, wire it to the ESP32 board mounted in the back
   cavity, close the back.

## Open questions

Settle these here before modeling against them.

- Board thickness range to support, and the face thickness each
  bushing length needs.
- How a guide registers: edge fences, corner stops, or dowel pins in
  holes that a back pocket later removes.
- Guide bores: plain printed bores, or pressed in steel drill bushings
  for repeat use.
- Back of the panel: routed cavity with a cover plate, or a separate
  box behind a thinner face.
- Mounting: wall (keyhole, French cleat) and desk (angled base).
- Power: USB C, 5 V wall supply, or PoE (ESP32 Ethernet board).
- Brass panels: same guides, or a separate path (laser, water jet).
