# TODO

## Phase 1: foundation

- [x] Repo conventions: shared params, param guard, style guard
- [x] Pipeline: regen_all with the read-only `--check` gate
- [x] Skills: verify, regen-outputs, openscad-review
- [x] CI running the verify gate on every pull request and push to
      main (`.github/workflows/verify.yml`)

## Phase 2: hardware

- [x] Panel configs in JSON, validated against the catalog
- [x] Component catalog with the first toggle (placeholder values)
- [x] Punch template (front) and router template (back) with edge fences
- [x] Punch guide gauge
- [x] Photoreal README renders (Blender Cycles, like pourbot)
- [ ] Measure the real toggles and replace the placeholder catalog values
- [ ] Measure the center punch, copy ring and bit; set design_params
- [ ] Print and test the first panel's templates on scrap
- [x] Room in the cavity for the ESP32 board and battery, checked
- [x] Antenna keepout check
- [x] Battery powered on two AA cells, printed inline holder screwed in
      from the cavity under the switch row, screw depth checked against
      the face
- [x] Controls centered on the face, internals around them; panels.py
      reports an off center panel as [info]
- [x] Radio: Zigbee sleepy end device on an ESP32-H2 (docs/CONCEPT.md)
- [ ] Measure on an ESP32-H2 dev kit with ESPHome zigbee: sleep current
      and flip to light latency (target under 300 ms). Do this before the
      hardware is final
- [ ] Choose a low power ESP32-H2 board and its regulator, replace the
      placeholder (docs/CONCEPT.md, Power)
- [ ] Buy AA contacts, measure them, set contact_space in the holder
- [ ] Measure the real sleep and wake current, update the budget
- [ ] Tray for the ESP32 board
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
