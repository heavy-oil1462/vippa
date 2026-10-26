---
name: regen-outputs
description: Regenerate all derived artifacts for Vippa in one command (gates, then every model and every panel's templates and previews into build/). Use after any change under cad/, catalog/ or panels/, or when the user wants fresh STLs to print. Never hand-run individual openscad commands for this.
---

# Regenerate derived outputs

```bash
python3 scripts/regen_all.py                       # everything
python3 scripts/regen_all.py three_toggles         # just these models or panels
```

Pipeline:
1. `scripts/check_params.py`: no file may shadow a design_params.scad name
2. `scripts/check_style.py`: writing rules across tracked text files
3. `scripts/panels.py`: catalog and every panel config are valid, and
   `scripts/check_panel_rules.py`: each display check fails its case
4. every model in cad/ (lib excluded) -> `build/<category>/<name>.stl`
5. every panels/<name>.json -> `build/panels/<name>/`: the wrapper
   `<name>.scad`, `punch_template.stl`, `router_template.stl`,
   `router_step.stl` (a panel with a display only, ADR-0006),
   `front.png`, `back.png`, `<name>.yaml`, the ESPHome config,
   validated with `esphome config` (the firmware skill), and `bom.md`,
   the bill of materials (`scripts/bom.py`: buy, print, wood, tools,
   wiring, not measured), whose Wiring pins must equal the config's

## Rules

- A new model is picked up automatically: put it under
  `cad/<category>/`, a new panel in `panels/`. A new non-model .scad
  (helper) goes in `cad/lib/`.
  A new artifact type (DXF for the CNC, an assembly PNG, multi-part
  files) gets added to `regen_all.py`, never a side script, and this
  skill documents it in the same change.
- Every line must be `[ok]`. A FAIL is a modeling error; see the verify
  skill's failure section.
- Prototyping phase: build/ is gitignored. The README images in media/
  are not made here; see the hero-render skill.

## When it fails

- Same failures as verify, since it runs the same gates; see that skill.
- `bom.md (wiring matches <name>.yaml)` FAIL: the bill of materials
  and the ESPHome config disagree on a pin. Both take their pins from
  `panels.assign_pins`; fix whichever stopped doing so.
- A model filter matches nothing and the run exits clean: the filter is
  the file's bare name (`punch_guide_gauge`, `three_toggles`), not a path.
