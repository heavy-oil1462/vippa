# TODO

## Phase 1: foundation

- [x] Repo conventions: shared params, param guard, style guard
- [x] Pipeline: regen_all with the read-only `--check` gate
- [x] Skills: verify, regen-outputs, openscad-review
- [x] CI running the verify gate (on the `ci-workflow` branch until a
      token with workflow scope pushes it)

## Phase 2: hardware

- [x] Panel configs in JSON, validated against the catalog
- [x] Component catalog with the first toggle (placeholder values)
- [x] Punch template (front) and router template (back) with edge fences
- [x] Punch guide gauge
- [x] Photoreal README renders (Blender Cycles, like pourbot)
- [ ] Measure the real toggles and replace the placeholder catalog values
- [ ] Measure the center punch, copy ring and bit; set design_params
- [ ] Print and test the first panel's templates on scrap
- [ ] Back cover and its rebate
- [ ] Toggle anti-rotation
- [ ] Mounting (wall and desk)
- [ ] More families: encoders, rotary switches, pilot lamps, meters
- [ ] Bill of materials generated from the panel and catalog

## Phase 3: firmware

- [ ] Adopt esphome-skills (validation gate, simulator)
- [ ] ESPHome config generated from the panel JSON
- [ ] Analog meter driver with calibration
- [ ] Home Assistant integration examples
