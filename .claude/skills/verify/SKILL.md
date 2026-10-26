---
name: verify
description: Read-only commit gate for Vippa. Runs the shared-param, writing style and panel config checks and renders every model and panel output to a temp dir, failing on warnings or non-manifold geometry. Use when about to commit, before opening a PR, or when asked whether the repo is consistent.
---

# Verify

```bash
python3 scripts/regen_all.py --check
```

Read-only: nothing in the working tree is touched. Every line must be
`[ok]` or `ok:` and the exit code 0 before committing. CI runs exactly
this.

What it checks, in order:

1. `check_params.py`: no file shadows a design_params.scad name
2. `check_style.py`: no em dashes, emoji or bold in tracked text files
3. `panels.py`: the catalog and every panel config are valid;
   `check_panel_rules.py`: each display check still fails a panel
   broken for it
4. every model under cad/ (lib excluded) and every panel's templates and
   previews render warning-free with manifold status NoError
5. every panel's generated ESPHome config passes `esphome config`
   with no warnings (the firmware skill)

Prototyping phase: there is no byte comparison against committed STLs
yet, because build/ is not committed while the models are iterated by eye.
See CLAUDE.md for the plan once models settle.

## When it fails

- `[FAIL]` on check_params: a model re-declares a shared name. Delete
  the local copy and use the value in cad/design_params.scad. Never
  rename the local copy to dodge the check.
- `[FAIL]` on check_style: rewrite the line. Use a comma, colon or a
  new sentence instead of a dash, plain words instead of bold. Never
  add the file to the skip list.
- `[FAIL] panels/...`: the layout breaks a rule; see the panel-config
  skill. `[info] ... not measured` is not a failure, it reminds that the
  catalog part still has placeholder values.
- `[FAIL] catalog ...: model envelope`: a printed holder changed size.
  Update size in the catalog to the printed envelope (the holder is the
  source), then run panels.py: the layout may no longer fit.
- `[FAIL]` with warnings: read them. An `assert` message means the knobs
  ask for impossible geometry; fix the knob, never the assert.
- `[FAIL] ... (esphome config)`: see the firmware skill.
- `[FAIL]` with a geometry status: the model is not cleanly manifold,
  usually coincident faces in a `difference()`. Extend the cutter by eps
  past both surfaces. See the openscad-review skill.

## Notes

- CI lives on main: `.github/workflows/verify.yml` runs exactly this
  gate on every pull request and push to main, with OpenSCAD and Mesa
  from the same nix pin. It adds no checks of its own; a new check goes
  into regen_all.py. Workflow changes need the owner's approval first
  (DIRECTION.md).
- check_style.py builds its patterns with chr() on purpose: the agent's
  file write tool turns `\u2014` style escapes into the real characters,
  and the gate then flags its own source. Keep those patterns as chr()
  codes.
