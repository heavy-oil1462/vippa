# TODO

## Phase 1: foundation (this PR)

- [x] Repo conventions: shared params, param guard, style guard
- [x] Pipeline: regen_all with the read-only `--check` gate
- [x] Skills: verify, regen-outputs, openscad-review
- [x] CI running the verify gate (on the `ci-workflow` branch until a
      token with workflow scope pushes it)
- [x] First calibration gauge: drill guide bore fit

## Phase 2: hardware

- [ ] Settle the open questions in docs/CONCEPT.md
- [ ] Component catalog in cad/lib/ with sourced dimensions
- [ ] Parametric panel model driven by a component list
- [ ] Drill guide generated from the same panel layout
- [ ] DXF export of the panel for a CNC router
- [ ] Back cavity, cover and mounting
- [ ] Assembly render as the README image
- [ ] Bill of materials

## Phase 3: firmware

- [ ] Adopt esphome-skills (validation gate, simulator)
- [ ] ESPHome packages per component family
- [ ] Analog meter driver with calibration
- [ ] Home Assistant integration examples
