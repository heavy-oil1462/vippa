# Architecture decision records

One file per decision, `NNNN-title.md`: a four digit number, the next
free one, and a short title in lowercase words joined by hyphens. Each
file has these sections:

- Status: Proposed, Accepted, or Superseded by ADR-NNNN. The
  supervisor accepts or rejects a Proposed ADR in review. One that
  touches DIRECTION.md's guiding principles or its Ask the owner first
  list waits for the owner.
- Context: what forces the decision, what was known at the time.
- Decision: what was decided, in a few plain sentences.
- Consequences: what follows from it, good and bad, and what it rules
  out.

An Accepted ADR is not edited. A change that departs from one adds a
new ADR that supersedes it, and only the old one's Status changes.
Add every new ADR to the index below in the same change.

| Number | Title | Status |
| --- | --- | --- |
| [0001](0001-home-assistant-is-the-target.md) | Home Assistant is the target | Accepted |
| [0002](0002-firmware-is-esphome.md) | Firmware is ESPHome, built with esphome-skills | Accepted |
| [0003](0003-zigbee-is-the-first-radio.md) | Zigbee is the first radio | Accepted |
| [0004](0004-pins-on-the-h2.md) | Pins on the ESP32-H2 | Accepted |
| [0005](0005-pins-for-knobs.md) | Pins for knobs: named pins and a resistor ladder | Accepted |
