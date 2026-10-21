---
name: regen-outputs
description: Regenerate all derived artifacts for Vippa in one command (gates, then every model STL). Use after any change under cad/, or when the user wants fresh STLs to print. Never hand-run individual openscad commands for this.
---

# Regenerate derived outputs

```bash
python3 scripts/regen_all.py                       # everything
python3 scripts/regen_all.py drill_guide_gauge     # just these models
```

Pipeline:
1. `scripts/check_params.py`: no file may shadow a design_params.scad name
2. `scripts/check_style.py`: writing rules across tracked text files
3. every model in cad/ (lib excluded) -> `stl/<category>/<name>.stl`

## Rules

- A new model is picked up automatically: put it under
  `cad/<category>/`. A new non-model .scad (helper) goes in `cad/lib/`.
  A new artifact type (DXF for the CNC, an assembly PNG, multi-part
  files) gets added to `regen_all.py`, never a side script, and this
  skill documents it in the same change.
- Every line must be `[ok]`. A FAIL is a modeling error; see the verify
  skill's failure section.
- Prototyping phase: the STLs are gitignored.

## When it fails

- Same failures as verify, since it runs the same gates; see that skill.
- A model filter matches nothing and the run exits clean: the filter is
  the file's bare name (`drill_guide_gauge`), not a path.
