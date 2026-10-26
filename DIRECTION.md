# Direction

Set by the owner, heavy-oil1462. The supervisor reads this at the start
of every session. Change it through a pull request, or ask on the board
issue.

## Goal

Vippa makes rugged, classy Home Assistant controls: a slab of hardwood
or brass with real panel hardware (toggles, knobs, pushbuttons, pilot
lamps, moving-coil meters) set into it, an ESP32-H2 on two AA cells
behind the face, talking Zigbee. Anyone with hand tools and a 3D printer
should be able to describe a panel in JSON, print two templates and
build it. Hardware first; firmware generated from the same panel file
follows. The concept and its decisions are in docs/CONCEPT.md.

## Guiding principles

- Real panel hardware only. No touchscreens, and no control whose only
  feedback is a LED or a screen. A small non-touch display beside the
  controls is fine as an output: LED segments, lit only for a while
  after an event so the panel stays on AA cells (owner, #19).
- A panel is its JSON file. Nothing about a panel is typed into a
  .scad; everything a panel needs is derived from `panels/<name>.json`
  and the catalog.
- Every part dimension is declared once, in `catalog/components.json`,
  with `source` and `measured`. Placeholders only with
  `measured: false`; never mark a guessed value measured.
- Hand tools only. Positions are measured from the two reference edges
  (bottom, left seen from the front); nothing may need a CNC.
- Fits and tools are measured, never tuned by eye. They live in
  `cad/design_params.scad` and nowhere else (check_params.py).
- Controls are centered on the face: the row or group of components
  sits on the board's center lines unless the panel says why not. The
  internals find room around the controls, not the other way round.
- The two AA cells lie end to end, in series, in a printed inline
  holder; never side by side or stacked.
- One pipeline: `scripts/regen_all.py` owns every derived file. Extend
  it rather than adding a sibling script; anything done twice becomes a
  script or a skill.
- Python is standard library only. OpenSCAD and Blender come from the
  nix pin, never downloaded binaries.
- Settle an open question in docs/CONCEPT.md before modeling against
  it.
- Nothing metal in a radio module's antenna keepout. The panel check
  enforces it; do not weaken it to make a layout pass.

## Architecture

Sources (edited by hand) on the left, derived products on the right.

```
catalog/components.json --+
panels/<name>.json -------+--> scripts/panels.py --+--> scripts/regen_all.py
cad/design_params.scad ---+    (validate, checks,  |    (gates, renders via
cad/holders/*.scad -------+     pins, wrapper)     |     render_scad.py,
cad/bezels/*.scad --------+                        |     esphome config)
cad/lib/panel.scad -------+                        |          |
firmware/packages/*.yaml -----> scripts/firmware.py+          v
                                  build/ (STLs, previews, wrappers,
                                  ESPHome configs; ignored)
scripts/render_hero.py + hero_scene.py (Blender) --> media/*.png (committed)
```

- `panels/` and `catalog/` are data. Only Python reads JSON;
  `panels.py` validates every panel against the catalog and the layout
  rules, assigns pins (ADR-0004, 0005, 0007), then writes a wrapper
  .scad that passes values into `cad/lib/panel.scad`. Every layout rule
  has a failing case in `scripts/check_panel_rules.py`.
- `cad/lib/panel.scad` holds all panel geometry: board, punch and
  router templates (with the step plate for display windows, ADR-0006),
  stand-ins and render scenes. It includes design_params.scad and uses
  holders and bezels; it never reads JSON or holds a panel's numbers.
- `cad/holders/` (printed internals) and `cad/bezels/` (printed parts
  on the face): a catalog part points at one with `model`, and
  regen_all checks the STL envelope against the catalog.
- `cad/calibration/` gauges stand alone on design_params.scad.
- `firmware/packages/` are hand-written ESPHome packages: the H2 base,
  the radio (`zigbee.yaml`, ADR-0003) and one per component family.
  `scripts/firmware.py` includes them with substitutions per panel
  (ADR-0002). Firmware reads the panel and catalog only; nothing on the
  CAD side reads the firmware.

Individual decisions and their reasons go into ADRs in docs/adr.

## Priorities, in order

1. Examples beyond toggles: knobs (encoders, rotary switches),
   pushbuttons, then LED segment displays, each as a family in the
   catalog and an example panel with a README picture (owner on the
   board, 2026-10-26; #18, #20). The first example panels are done
   (#17).
2. Firmware started: an ESPHome config generated from every panel for a
   Zigbee sleepy end device on the ESP32-H2, validated in the gate
   (owner, 2026-10-26; #12). Home Assistant as the target, ESPHome and
   Zigbee first are ADR-0001 to 0003.
3. The first panel (`three_toggles`) buildable for real: measured
   toggles in the catalog, measured tools in design_params, and the
   templates printed and tested on scrap.
4. Settle the ESP32-H2 board and regulator after measuring sleep
   current and flip to light latency on a dev kit (target under 300 ms),
   before the hardware is final.
5. Finish the panel as an object: board tray, back cover and rebate,
   toggle anti-rotation, wall and desk mounting.
6. More component families: encoders, rotary switches, pushbuttons,
   pilot lamps, meters.
7. Bill of materials generated from the panel and catalog.

## Not now

- Moving-coil meters: they need power the whole time they show a
  value (owner, #19). Readouts are LED segment displays instead.

- Wifi, Thread or Matter on the panel; Zigbee is the first radio
  (ADR-0003).
- Committed STLs and byte comparison in `--check`, until the design is
  accepted.
- Boards larger than the print bed, and brass faces, until their open
  questions are settled.

## How to work

- `python3 scripts/regen_all.py --check` passes before every pull
  request (the verify skill).
- Review CAD by rendering and looking at the PNG (openscad-review
  skill), never from source alone.
- `media/*.png` is regenerated in the same change as any CAD or panel
  change it shows (hero-render skill).
- Use the repository skills for their tasks: panel-config,
  component-catalog, regen-outputs.
- Keep `name = value;` parameters on one line; loops must survive a
  count of one.
- Writing style per check_style.py: no em dashes, emoji or bold.
- TODO.md and docs/CONCEPT.md change in the same pull request as the
  work that ticks or settles them.

## Ask the owner first

- Marking any catalog value or tool parameter as measured: only the
  owner has the parts and calipers.
- Choosing or buying hardware (the ESP32-H2 board, regulator, contacts).
- Answering an open question in docs/CONCEPT.md.
- Changes to `.github/workflows/`.
