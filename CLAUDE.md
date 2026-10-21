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
- Everything is configurable. A panel is a list of components with
  positions; the model files expose their knobs at the top in OpenSCAD
  Customizer sections (`/* [Section] */`, one comment line above each
  knob). A hard-coded number inside a module that a user could
  reasonably want to change is a finding.
- One component catalog. Each panel part (cutout diameter, anti-rotation
  key, bushing length, body depth, back clearance) is declared once and
  every panel, drill guide and DXF reads it from there. Values come from
  datasheets or calipers, with the source written next to them, never
  guessed.
- Wood is cut by hand with printed drill guides. A guide sits on the
  workpiece, registers on its edges and steers the drill and Forstner
  bits, so a panel needs no CNC. The same geometry also exports a DXF
  for a PrintNC style router; the guides stay the primary path.
- Guide bore fits are MEASURED with calibration gauges in
  cad/calibration/, never tuned by eye. They are printer, profile and
  filament specific.
- Firmware comes later and is built on esphome-skills
  (github.com/heavy-oil1462/esphome-skills), the same way as fika and
  frodas. Hardware first.

## Layout

- `cad/design_params.scad`: single source of truth for every value two
  models share. Models `include` it; `check_params.py` fails the build if
  any file re-declares one of its names.
- `cad/<category>/`: one .scad per printable model. Each model defines a
  module of the same name with every knob as an argument defaulting to
  the file's Customizer value, then calls it once, so other files can
  `use` it and pass overrides. Categories so far: `calibration/`
  (gauges). Planned: `panels/` (faceplates), `guides/` (drill guides).
- `cad/lib/`: shared helpers, not printable (the component catalog will
  live here).
- `docs/CONCEPT.md`: the concept, the component families and the open
  questions. Settle a question there before modeling against it.
- `scripts/`: Python tools, stdlib only.

## Tools and workflow

Everything runs headless through nix (`nix build` / `nix shell` only,
never download binaries). OpenSCAD comes from the nixpkgs pin in
`render_scad.py`. No-nix escape hatch: set `OPENSCAD=/path/to/openscad`.

- `python3 scripts/regen_all.py`: the single entry point. Gates, then
  every model to `stl/<category>/<name>.stl`. `--check` is the read-only
  gate (the verify skill and CI).
- `python3 scripts/check_params.py`: no file may shadow a design_params
  name.
- `python3 scripts/check_style.py`: writing rules (no em dashes, emoji or
  bold) across every tracked text file.
- `python3 scripts/render_scad.py <file.scad> <out.png|stl|dxf> [args]`:
  one-off headless renders (see the openscad-review skill).

Skills in `.claude/skills/`: verify (commit gate), regen-outputs
(rebuild), openscad-review (render and look). Anything done twice becomes
a skill or a script; extend regen_all.py rather than adding a sibling
pipeline.

## Prototyping phase

- `stl/` is gitignored, not committed. verify gates on the param check,
  the style check and every model rendering warning-free and manifold.
- When a model is accepted, follow skua: commit STLs and DXFs as build
  products, add a byte comparison to `--check`.

Conventions:
- Review CAD by rendering and looking at the PNG, never from source alone.
- Keep top-level `name = value;` parameters on one line so the tooling
  and the Customizer can parse them.
- OpenSCAD iterates a reversed range (`[1 : 0]`) backwards with a
  warning instead of skipping it. Loops must survive a count of one.

## Notes

- The sandbox PAT has no workflow scope, so it cannot push changes to
  `.github/workflows/`. Commit those on their own local branch
  (`ci-workflow`) and leave the push to the user.
