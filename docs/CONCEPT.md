# Concept

A Vippa panel is a slab of hardwood (oak, walnut) or brass with panel
hardware set into its face. It hangs on a wall or stands on a desk and
controls Home Assistant through an ESP32 behind it. It should feel like
a piece of old lab equipment: heavy, deliberate, no screen.

## Component families

Each family becomes catalog entries (catalog/components.json) with
measured or datasheet values.

- Toggle switches: full size (12 mm, 15/32 in bushing) and miniature
  (6 mm, 1/4 in bushing), bat handles. On/off and momentary. In the
  catalog: `toggle_12mm` and `toggle_6mm` (family `toggle`).
- Rotary controls: incremental encoders with push (for dimmers and
  volume) and multi-position rotary switches (scene selectors), with
  machined or bakelite knobs. In the catalog: `encoder_knob` (family
  `encoder`, M7 bushing, knurled aluminium knob) and `rotary_switch`
  (family `rotary`, 1 pole 6 positions, 3/8 in bushing, bakelite
  pointer knob).
- Pushbuttons: momentary, metal, optionally illuminated. In the
  catalog: `pushbutton_16mm` (family `pushbutton`, 16 mm threaded
  body, flat head).

Every catalog value is a placeholder from a typical datasheet
(`measured: false`) until calipers confirm it. The face mounted
families all mount the toggle's way, through a round hole: a threaded
bushing, a nut behind the face and the body behind that, and in front
a second nut, or for a pushbutton its head. So the same checks and the
same punch template cover them all.
- Pilot lamps: bezel indicators, LED inside.
- LED segment displays, for readouts: a knob's value, later a
  temperature. Dark until an event (a knob turns, a button is pressed,
  a toggle flips, later a new value from Home Assistant), then lit for
  `display_time` (5 s by default) and dark again, so the display is off
  whenever the panel sleeps. The module lies in the cavity behind a
  window routed through the face, its LED block reaching through into
  a printed bezel on the face that covers the window's edges and
  corners (ADR-0006). In the catalog: `led_segment_4d` (family
  `display`, 4 digits of 0.36 in on a TM1637 driver), with its bezel in
  `cad/bezels/`. A display is not a control: a knob beside it is, so
  the panel's feedback stays mechanical.

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
6. A panel with a display: drop the router template's step plate into
   its opening and route each window through the face, then chisel the
   window's round corners square to the four punch marks.
7. Fit the hardware, glue each display's bezel over its window, wire it
   all to the ESP32 in the cavity, close the back.

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
- Controls are centered on the face: the bounding box of the components
  sits on the board's center lines, unless the panel says why not. The
  internals (battery holder, ESP32 board) find room in the cavity around
  the controls, and the board grows to fit them, not the other way
  round. scripts/panels.py reports an off center panel as [info].
- Panel configs are JSON (stdlib, validated before rendering, readable
  by the firmware generator later).

## Radio

Zigbee, as a sleepy end device on an ESP32-H2, through the user's
existing Zigbee coordinator (ZHA or Zigbee2MQTT). No wifi, no bridge.

Why: the delay that makes smart switches feel slow is the device
rejoining wifi and Home Assistant after each wake. A Zigbee end device
stays joined to its parent while it sleeps, so a toggle wakes it and the
report goes out at once, the way commercial battery switches work.
Zigbee also acknowledges every frame, which keeps the lever and the
light in agreement.

How it was chosen (2026-10-21):

- ESPHome has official Zigbee end device support on ESP32-C6 and H2;
  its docs call the H2 more reliable. Support is basic: Home Automation
  profile only, and a config change usually means re-pairing.
- ESPHome has no Matter support. Its OpenThread component carries the
  normal ESPHome API over Thread, the same connect handshake as wifi.
  Matter would mean leaving ESPHome.
- ESP-NOW to a plug-in bridge was the fallback: fast and all ESPHome,
  but one more device in the house.
- Risk: ESPHome documents its sleepy option for nRF52 only. Sleep
  current and flip to light latency on the H2 must be measured on a
  dev kit before the hardware is final. Target: under 300 ms.

The antenna works at 2.4 GHz like wifi, through the wood:

- Dry hardwood costs a few dB at panel thicknesses, not enough to
  matter in a house. Wet or green wood costs much more: oil the panel,
  never mount it fresh.
- Metal is what kills the signal. A PCB antenna needs a zone with no
  metal around its end: no battery can, switch body or wire bundle in
  it. The panel check enforces this with the module's antenna_keepout,
  so the board lies with its antenna end toward a cavity wall.
- A metal back cover, a metal wall box or a brass face shields the
  antenna completely. Those need a board with an external antenna
  connector (u.FL) and the antenna placed in wood or out in the open.
- Wall mounting puts the wall behind the antenna; plaster and wood are
  fine, a metal stud or a mirror behind it is not.

## Power

Battery powered, two AA cells end to end in a printed inline holder
screwed to the cavity floor, never side by side or stacked. In line the
cells are in series by touching nose to tail, so the holder needs bought
contacts only at its two ends: a spring for the negative end and a flat
plate for the positive. The long, narrow holder fits the band of cavity
beside a centered row of controls. The ESP32-H2 sleeps as a Zigbee sleepy end device, polling its
parent now and then, and wakes at once when a toggle moves.

Budget for two alkaline AA (about 2500 mAh, of which perhaps 2000 mAh
is usable through a regulator). Unlike wifi, a flip costs almost
nothing (a short radio burst), so the average sleep current, poll
wakes included, sets the battery life:

| Average sleep current | Per day | Two AA last |
| --- | --- | --- |
| 20 uA | 0.5 mAh | years, limited by the cells' shelf life |
| 100 uA | 2.4 mAh | about 2 years |
| 500 uA | 12 mAh | about 5 months |

The ESP32-H2 figure is not known yet for ESPHome; measuring it is the
first firmware task. Things that decide it:

- The board. A typical dev board with a USB serial chip, a common LDO
  and a power LED draws several mA asleep, which empties the cells in
  weeks. It has to be a board made for deep sleep, or a bare module.
- The regulator. Two AA give 3.2 V fresh and about 2 V flat; the ESP32
  wants 3.0 to 3.6 V. A buck boost with a quiescent current under a
  microamp uses the whole cell. Lithium AA (1.5 to 1.8 V flat curve)
  give more capacity and work in the cold. NiMH (2.4 V for two) needs
  the boost too.
- The poll period: how often the sleeping device asks its parent for
  messages. Longer polls save power; a switch only sends, so it can
  poll rarely.
- Switch wiring. A closed toggle on a pull up resistor draws current
  for as long as it is on: about 70 uA through the ESP32's internal
  pull up, more than the whole sleep budget. Use ON-ON (SPDT) toggles
  wired between 3.3 V and ground, which hold the pin at a level with no
  current, or very high value external pull ups.
- Waking on a change. A toggle left on holds its pin high, so the wake
  must be armed per pin for the opposite of its current level before
  each sleep. The chip variant decides how easy that is; settle it with
  the firmware.

A display draws nothing while it is dark and the panel sleeps, and 10
to 80 mA while it is lit, depending on how many segments are on and
its intensity. Its budget is the lit current times the time it stays
lit per event, times the events per day. With `display_time` 5 s:

| Lit current | Per event | 20 events a day | 100 events a day |
| --- | --- | --- | --- |
| 10 mA | 0.014 mAh | 0.28 mAh | 1.4 mAh |
| 30 mA | 0.042 mAh | 0.83 mAh | 4.2 mAh |
| 80 mA | 0.11 mAh | 2.2 mAh | 11 mAh |

At 30 mA and 20 events a day the display costs more than a 20 uA sleep
(0.5 mAh a day): the two AA last about 4 years instead of being
limited by shelf life. At 80 mA and 100 events, about 6 months. The
firmware sets a middle intensity (4 of 7). Each event also keeps the
H2 awake for `display_time`, mostly inside the `awake_time` the wake
takes anyway. The module's standby current, dark but powered, is not
known yet (Open questions).

The holder's screws go into the 4 mm face from behind. panel.scad
asserts that holder_screw_len minus holder_flange_t stops face_skin
short of the front; with the defaults a 2.2 x 4.5 screw reaches 2.5 mm
into the oak. Drill the pilot holes with a depth stop.

## Firmware

ESPHome (ADR-0002), generated from the panel JSON by scripts/firmware.py
into build/panels/<name>/<name>.yaml and checked with `esphome config`
by regen_all.py. The config only includes the packages in
firmware/packages/: h2_base.yaml (the chip and deep sleep), zigbee.yaml
(the radio, ADR-0003) and one package per component family.

- Each toggle is a Zigbee binary input named after its component id,
  reported on every change (`report: force`), internal pull resistors
  off for the ON-ON wiring above.
- A pushbutton is a binary input too, normally open to ground on the
  internal pull up: no current until it is pressed.
- An encoder is an analog input, a level from 0 to 100 percent in 20
  detents, kept in flash across deep sleep, and its push a binary input
  `<id>_push`. Its phases sit on pull ups to ground, so it must be a
  part whose contacts are both open at every detent.
- A rotary switch is an analog input, its position from 1, read as a
  resistor ladder on one ADC pin (ADR-0005), about 1 uA.
- Home Assistant turns the numbers into brightness, volume or a scene
  with an automation; nothing on the panel knows the lights.
- A display (display.yaml, a TM1637 driver) shows a knob's value,
  right aligned: an encoder's level or a rotary switch's position,
  `"shows"` in the panel or the first knob. A turn of an encoder, a
  flip or a press lights it for `display_time`; each event restarts
  the time and holds off deep sleep until it is dark again. A rotary
  switch does not light it: its first reading at every wake would.
  Its CLK and DIO pins come after the wake and ADC pins (ADR-0007).
- Pins come from the panel's `"pin"` or a fixed order in
  scripts/panels.py, wake capable pins first (ADR-0004). An encoder
  takes three, its push first (ADR-0005).
- The panel deep sleeps, wakes every `poll_period`, rejoins its parent,
  reports and sleeps again after `awake_time`.

## Open questions

- Firmware gaps in ESPHome 2026.5.1 on the ESP32-H2 (the nixpkgs pin),
  not worked around with custom C++ (ADR-0002):
  - No sleepy end device: ESPHome's `sleepy` option is nRF52 only. The
    H2 deep sleeps and rejoins its parent after every wake instead of
    staying joined and polling. The cost in wake time and current has
    to be measured on the dev kit.
  - No wake level per pin: deep sleep on the H2 wakes through ext1 with
    one level for every pin, and ESPHome's single `wakeup_pin` with
    INVERT_WAKEUP is not implemented on the H2. So the firmware cannot
    arm each toggle for the opposite of its level, and wakes on the
    timer only, an interim default in h2_base.yaml and not a decision:
    a flip waits up to `poll_period`. ext1 is left out because with
    one level for all pins, a toggle left at that level would wake the
    panel again at once and drain the cells. Options:
    wait for ESPHome, or add per pin ext1 levels to ESPHome upstream
    (ESP-IDF supports them on the H2).
  - No trigger for an acknowledged report: the panel sleeps after
    `awake_time` instead of as soon as the parent acknowledges.
  - Only five H2 GPIOs can wake it (10 to 14), so at most five
    toggles per panel can wake the panel once per pin wake works. An
    encoder takes three of them.
  - Knobs reach Home Assistant only as Zigbee analog inputs: ESPHome on
    the ESP32 exposes binary sensors and sensors, not switches, numbers,
    the level control cluster or a multistate input. So an encoder
    cannot be bound to a light as a dimmer, and a scene number needs an
    automation in Home Assistant to mean anything.
  - An encoder counts only while the panel is awake. A turn while it
    sleeps does not wake it (its phases would need per pin wake levels
    too, see above) and the detents turned before the next wake are
    lost. Pushing the knob first, once a push can wake the panel, is
    the interim way to use it.
  - A rotary switch on the ADC cannot wake the panel at all (the ADC
    pins are not wake pins): a new position is reported at the next
    wake. On living_room an apply pushbutton beside the selector wakes
    the panel and carries the position with it.
  - A Home Assistant value cannot reach a display yet: ESPHome's Zigbee
    on the ESP32 has no number, switch or other cluster the
    coordinator writes to (those are nRF52 only), so the H2 cannot
    receive a temperature or any other value to show. A display shows
    a knob on its own panel until it can, and a new value from Home
    Assistant is no event yet.
  - A display lights on events while the panel is awake only: a turn
    or a press while it sleeps does not wake it, as above.
- Displays: the module's standby current with every segment dark is
  not measured. If it matters against the sleep budget, the module's
  supply needs switching off in deep sleep (a load switch on a pin),
  which is hardware to choose. Also how the module is held: the bezel
  grips its LED block and the board rests against the face behind the
  window; a screw or a spot of glue may be needed in practice.
- Analog meters, not now: a moving-coil meter shows a value only while
  current flows through it, so it draws power the whole time it reads,
  which a panel on two AA cells cannot afford. LED segment displays,
  lit for a while after an event, are the readout for now (the owner,
  on #19, 2026-10-26).
- Charging: none for alkaline cells, or a board with a charger for
  rechargeable cells.
- Back of the panel: a cover plate in a rebate, or a screwed panel.
  Needs a second, shallower router template step.
- Anti-rotation for toggles and knobs: a second small hole for the lock
  washer or body tab, or rely on the nut torque. A knob is turned
  against the nut every time it is used, so it matters more there.
- Mounting: wall (keyhole, French cleat) and desk (angled base).
- The ESP32 board: generic placeholder for now. Holding it in the
  cavity: printed tray screwed like the battery holder.
- Boards larger than the print bed: split templates or a two-step
  registration.
- Brass panels: same templates, or a separate path.
