# Vippa

Rugged, classy Home Assistant controls: a solid piece of hardwood (or
brass) with real panel hardware set into it. Toggle switches, rotary
knobs, pushbuttons, pilot lamps and analog moving-coil meters, wired to
an ESP32 running ESPHome. Open hardware and firmware.

The name is Swedish for to tip or flip, as in vippströmbrytare, a toggle
switch.

## Core design ideas (do not design against these)

- Real hardware, no touchscreens. Every control is a bought panel part
  with a threaded bushing or a bezel, the kind found on test gear and
  old radios. Feedback is mechanical (a detent, a lever position, a
  needle), never only a LED or a screen.
- A panel is a JSON file in `panels/`: board size and thickness, the
  back cavity, the components placed on the front face and the
  internals (ESP32 board, battery) lying in the cavity. Battery
  powered: two AA cells, deep sleep, wake on a toggle (docs/CONCEPT.md,
  Power). The
  user's own panels live there too. Everything a panel needs is
  derived from that file; nothing about a panel is typed into a .scad.
  The same file will drive the firmware later.
- One component catalog, `catalog/components.json`. Each panel part
  (hole, bushing, nut, body, keepout) is declared once there, with
  `source` saying where the values come from and `measured` saying
  whether calipers have confirmed them. Placeholder values are allowed
  only with `measured: false`, which the pipeline reports on every run.
  Never guess a value and mark it measured.
- Hand tools only, no CNC needed. Two printed templates per panel, both
  registering on fences along the two reference edges (bottom and left
  seen from the front), so every position is measured from those edges:
  - punch template on the front face: a plain bore per hole, just big
    enough to guide the center punch; holes are then drilled from the
    punch marks
  - router template on the back face: the guide bushing (copy ring)
    runs inside it to route the cavity that thins the face for the
    bushings and holds the electronics
- Fits and tools are MEASURED, never tuned by eye: `punch_clearance`
  with the punch guide gauge, `punch_d`, `copy_ring_od` and `bit_d` on
  the user's own tools. They live in `cad/design_params.scad`.
- Radio is Zigbee: an ESP32-H2 as a sleepy end device on the user's
  coordinator, for instant response on battery. No wifi on the panel
  (docs/CONCEPT.md, Radio). 2.4 GHz goes through the wood but not
  through metal: nothing metal in a module's antenna keepout, no metal
  back or face without an external antenna.
- Firmware is ESPHome, generated from the panel JSON and built on
  esphome-skills (github.com/heavy-oil1462/esphome-skills) the way fika
  and frodas are: packages plus substitutions, no custom C++ (ADR-0002).
  It only reads the panel and catalog; nothing on the CAD side reads
  the firmware. Hardware first.

## Layout

- `panels/<name>.json`: one panel. Validated by `scripts/panels.py`,
  including the optional `"pin"` per component (ESP32-H2 GPIO; missing
  pins follow `PIN_ORDER`).
- `catalog/components.json`: panel hardware dimensions.
- `cad/design_params.scad`: tools, printer and fits shared by every
  panel. `check_params.py` fails the build if any file re-declares one
  of its names.
- `cad/lib/panel.scad`: the board, both templates, the stand-in parts
  and the render scenes, all driven by one panel. Its parts:
  `panel`, `punch`, `router` (templates in print orientation), `hero`
  and `build` (render scenes).
- `cad/calibration/`: gauges for measured fits.
- `cad/holders/`: printed parts that sit in the cavity (the AA battery
  holder). A catalog module with a `model` field points at one, and
  regen_all.py fails if the STL's bounding box differs from the catalog
  size.
- `firmware/packages/`: hand written ESPHome packages: `h2_base.yaml`
  (chip, deep sleep, `poll_period`), `zigbee.yaml` (the radio) and one
  per component family (`toggle.yaml`). `scripts/firmware.py` includes
  them with substitutions into `build/panels/<name>/<name>.yaml`.
- `docs/adr/`: architecture decision records, index in its README.
- `scripts/`: Python tools, stdlib only. `hero_scene.py` runs inside
  Blender.
- `media/`: the README renders, committed build products of
  render_hero.py.
- `docs/CONCEPT.md`: the concept, decisions and the open questions.
  Settle a question there before modeling against it.

## Tools and workflow

Everything runs headless through nix (`nix build` only, never download
binaries). OpenSCAD, Blender and ESPHome come from the nixpkgs pin in
`render_scad.py`. No-nix escape hatches: `OPENSCAD=`, `BLENDER=` and
`ESPHOME=`.

- `python3 scripts/regen_all.py`: the single entry point. Gates, then
  every model and every panel into `build/`, the ESPHome config
  included and checked with `esphome config`. `--check` is the
  read-only gate (the verify skill and CI).
- `python3 scripts/panels.py [name]`: validate panel configs and the
  catalog.
- `python3 scripts/firmware.py [--check] [name]`: write (and validate)
  the ESPHome configs only.
- `python3 scripts/render_hero.py [shot] [--draft]`: photoreal README
  images into `media/` (Cycles, minutes; not part of verify).
- `python3 scripts/render_scad.py <file.scad> <out.png|stl|dxf> [args]`:
  one-off headless renders (see the openscad-review skill).

Skills in `.claude/skills/`: verify (commit gate), regen-outputs
(rebuild), openscad-review (render and look), panel-config (add or
change a panel), component-catalog (add or measure a part),
hero-render (README images), firmware (generate and validate the
ESPHome config). Anything done twice becomes a skill or a
script; extend regen_all.py rather than adding a sibling pipeline.

## Prototyping phase

- `build/` is gitignored, not committed. verify gates on the param,
  style and panel checks and every model and panel output rendering
  warning-free and manifold.
- `media/*.png` is committed: regenerate it in the same change as any
  CAD or panel change it shows.
- When a design is accepted, follow skua: commit STLs as build products
  and add a byte comparison to `--check`.

Conventions:
- Review CAD by rendering and looking at the PNG, never from source alone.
- Keep top-level `name = value;` parameters on one line so the tooling
  and the Customizer can parse them.
- OpenSCAD iterates a reversed range (`[1 : 0]`) backwards with a
  warning instead of skipping it. Loops must survive a count of one.

## Notes

- CI lives on main: `.github/workflows/verify.yml` runs
  `regen_all.py --check` on every pull request and push to main, with
  OpenSCAD and Mesa from the same nix pin. It adds no checks of its
  own; a new check goes into regen_all.py. The sandbox PAT has workflow
  scope, but workflow changes still need the owner's approval first
  (DIRECTION.md).
- Hamstra configures builds with wrapper .scad files, not JSON. Vippa
  uses JSON because Python validates it before anything renders and the
  firmware will read it too; the wrapper is generated instead.
