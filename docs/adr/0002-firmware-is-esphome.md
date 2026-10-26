# ADR-0002: Firmware is ESPHome, built with esphome-skills

Status: Accepted

Decided by the owner, 2026-10-26.

## Context

The owner's other ESPHome projects (fika, frodas, PrintTrek) share
esphome-skills (github.com/heavy-oil1462/esphome-skills): firmware
composed from packages and substitutions, a validation gate, skill docs,
a QEMU simulator and an MQTT protocol contract. Vippa's firmware is
generated from the panel JSON, so it needs a firmware framework whose
configuration a script can write.

## Decision

The firmware is ESPHome, built the esphome-skills way: hand written
packages in `firmware/packages/` plus substitutions, and a validation
gate. No custom C++ beyond what ESPHome itself needs. Where ESPHome
cannot do something yet, the gap is recorded in docs/CONCEPT.md, not
worked around.

## Consequences

- `scripts/firmware.py` writes one config per panel that only includes
  packages with substitutions; the packages hold all ESPHome YAML.
- The gate is `esphome config` on every generated config, run by
  `scripts/regen_all.py` (and so by `--check` and CI). ESPHome comes
  from the same nixpkgs pin as OpenSCAD, no pip install.
- Adopted from esphome-skills: packages plus substitutions, the
  `esphome config` check, and the firmware skill as a thin wrapper over
  its canonical firmware doc.
- Left out: the esphome_skills Python package and its gate framework.
  Vippa's Python is standard library only and regen_all.py is its one
  pipeline, so the check lives there instead.
- Left out: the QEMU simulator. It runs classic ESP32 (Xtensa) firmware
  under Espressif QEMU with an emulated ethernet card standing in for
  wifi. The ESP32-H2 is a RISC-V chip whose 802.15.4 radio QEMU does not
  emulate, so a Zigbee H2 panel cannot run in it.
- Left out: the MQTT protocol contract and mock device. A Zigbee panel
  speaks ZCL to the user's coordinator (ADR-0001, ADR-0003), not MQTT,
  so there is no topic contract to test.
- Behaviour that ESPHome lacks on the H2 waits for ESPHome, or for a new
  ADR that supersedes this one.
