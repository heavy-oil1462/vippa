---
name: firmware
description: Generate and validate the ESPHome firmware config of every Vippa panel (Zigbee end device on an ESP32-H2), or change the firmware packages. Use when a panel's controls or pins change, when editing firmware/packages/, or when asked whether a panel's firmware is valid. Flashing comes later.
---

# Firmware

```bash
python3 scripts/firmware.py --check                 # every panel: write and validate
python3 scripts/firmware.py --check three_toggles   # one panel
python3 scripts/regen_all.py --check                # the full gate, this included
```

Each panel gets `build/panels/<name>/<name>.yaml`, which only includes
the packages in `firmware/packages/` with substitutions:

- `h2_base.yaml`: ESP32-H2, logger, deep sleep. Substitutions
  `poll_period` (timer wake, under the parent's 64 min end device
  timeout) and `awake_time` (how long a wake lasts).
- `zigbee.yaml`: the radio (ADR-0003). Another radio would be another
  package; component packages never mention the radio.
- one package per catalog family, `FAMILY_PACKAGES` in
  `scripts/firmware.py`. `toggle.yaml` takes vars `id`, `name` (the
  component id) and `pin`.

`esphome config` from the nixpkgs pin in `scripts/render_scad.py`
validates each config; `ESPHOME=/path/to/esphome` overrides it. Any
WARNING or ERROR line is a FAIL.

The shared workflow and editing rules are esphome-skills' canonical
firmware doc (github.com/heavy-oil1462/esphome-skills,
skills/firmware.md). Its simulator and MQTT contract do not apply to a
Zigbee H2 panel (ADR-0002).

## Rules

- Nothing about a panel goes into a package. Panel specific values are
  substitutions written by `scripts/firmware.py` from the panel JSON.
- No custom C++ and no lambdas that stand in for a missing ESPHome
  feature (ADR-0002). Record the gap under Open questions in
  docs/CONCEPT.md instead.
- Pins: set `"pin"` in the panel JSON or leave it to `PIN_ORDER` in
  `scripts/panels.py` (ADR-0004). Never reorder `PIN_ORDER`; it rewires
  every panel without pins.
- A new component family needs its package and an entry in
  `FAMILY_PACKAGES` in the same change as its catalog entry, or the
  firmware step fails for any panel that uses it.
- Firmware reads the panel and catalog only; nothing on the CAD side
  may read the generated YAML.

## When it fails

- `[FAIL] ... (esphome config)`: the lines below are ESPHome's. A bad
  pin usually means `panels.py` lets through a GPIO ESPHome rejects;
  fix `PINS` in `scripts/panels.py`, not the generated file.
- `no firmware package for family`: see the new family rule above.
- `pin ... is not a usable ESP32-H2 GPIO` or `already used` from
  panels.py: pick a pin from the list it prints.

## Later

Flashing and pairing on a real ESP32-H2 dev kit is the owner's step
(`esphome run build/panels/<name>/<name>.yaml` over USB), with the sleep
current and flip to light latency measured at the same time (TODO.md).
