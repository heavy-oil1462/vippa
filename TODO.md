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
- [x] Example panels (bedside, hallway, scenes) with README pictures,
      miniature toggle in the catalog (placeholder values)
- [ ] Measure the real miniature toggles
- [ ] Measure on an ESP32-H2 dev kit with ESPHome zigbee: sleep current
      and flip to light latency (target under 300 ms). Do this before the
      hardware is final
- [ ] Choose a low power ESP32-H2 board and its regulator, replace the
      placeholder (docs/CONCEPT.md, Power)
- [ ] Buy AA contacts, measure them, set contact_space in the holder
- [ ] Measure the real sleep and wake current, update the budget
- [ ] Tray for the ESP32 board
- [ ] Back cover and its rebate
- [ ] Toggle and knob anti-rotation
- [ ] Mounting (wall and desk)
- [x] More families: encoders, rotary switches and pushbuttons
      (placeholder values), stand-ins, firmware packages and the example
      panels dimmer and living_room
- [ ] Measure the real encoders, rotary switches, knobs and pushbuttons
- [x] LED segment displays: window routed through the face with a
      step plate in the router template, printed bezel, firmware lit
      after an event, the example panel thermostat (ADR-0006, ADR-0007)
- [ ] Measure the real display module and set its catalog values
- [ ] Measure slip_fit with a test print of the bezel and the step plate
- [ ] Measure the display module's standby current; switch its supply
      off in deep sleep if it matters (docs/CONCEPT.md, Open questions)
- [ ] More families: pilot lamps (need a design decision first); meters
      not now (docs/CONCEPT.md, Open questions)
- [ ] Bill of materials generated from the panel and catalog

## Phase 3: firmware

- [x] Adopt esphome-skills: packages plus substitutions, the esphome
      config gate in regen_all.py, the firmware skill (ADR-0002; the
      simulator and MQTT contract do not apply to a Zigbee H2)
- [x] ESPHome config generated from the panel JSON, Zigbee on the
      ESP32-H2, a pin per component (ADR-0003, ADR-0004)
- [ ] Flash a generated config on an ESP32-H2 dev kit and pair it with
      ZHA or Zigbee2MQTT
- [ ] Wake on a flip: per pin wake levels and a sleepy end device on the
      H2, once ESPHome has them (docs/CONCEPT.md, Open questions)
- [ ] Show a Home Assistant value on a display, once ESPHome's Zigbee
      on the H2 can receive one (docs/CONCEPT.md, Open questions)
- [ ] Home Assistant integration examples
