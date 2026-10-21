---
name: openscad-review
description: Render and review Vippa's OpenSCAD models headlessly (via nix, no GUI). Checks warnings, manifold geometry, visual correctness and the project's design rules. Use after any .scad change, or when asked to review or check the CAD.
---

# OpenSCAD review

Review by rendering and looking, never from source alone.

```bash
python3 scripts/render_scad.py cad/<category>/<model>.scad "$SCRATCH/<model>.png" \
    --imgsize=900,700 --camera=0,0,0,55,0,25,0 --viewall --autocenter
```

`--camera=0,0,0,55,0,25,0` is a three-quarter view from above, the
natural view of a flat panel or guide. `--projection=o` with
`--camera=0,0,0,0,0,0,0` gives a true top view for checking hole
positions.

## Procedure

1. Run `python3 scripts/regen_all.py --check` first (the verify skill).
   It gates params, style, warnings and manifold status for every model.
2. Before rendering, state what the image should show (hole count,
   positions, labels). Render each changed model into the scratchpad and
   look at the PNGs with the Read tool. A mismatch is a modeling error to
   investigate, not a rendering quirk.

## Design rules to check

- Every knob a user might change is a Customizer parameter at the top of
  the model file and an argument of the model's module.
- Shared values come from cad/design_params.scad, never a local copy.
- Component dimensions come from the catalog in cad/lib/, never a
  number typed into a panel or guide.
- Prints without support in the modeled orientation: nothing starts
  above the bed with a flat underside, no horizontal round holes without
  a teardrop roof.

## Notes

- The sandbox's `LD_LIBRARY_PATH=/lib` crashes nix binaries; render_scad.py
  overrides it. Do the same if running openscad manually via `nix shell`.
- PNGs use Mesa software GL via `EGL_PLATFORM=surfaceless`, no X needed.
  `libEGL warning: Not allowed to force software rendering` is benign.
- `Fontconfig error: Cannot load default config file` is benign too:
  OpenSCAD falls back to its bundled font and text() still renders. It is
  lowercase, so regen_all does not flag it.
- `nixpkgs#openscad-unstable` on the unstable registry has no hydra cache
  and its source build fails at link after an hour. render_scad.py pins a
  release branch that ships the same snapshot prebuilt. Probe a new pin
  with `--max-jobs 0` before switching.
- Section views need `--render`: the OpenCSG preview mis-draws a
  difference against a huge half-space cube. Size half-space cutters to
  the part, never 1e4.
- A model used as a library is `use`d with a path relative to the using
  file; top-level variables of a `use`d file are not visible to the user
  of it, so pass overrides as module arguments.
