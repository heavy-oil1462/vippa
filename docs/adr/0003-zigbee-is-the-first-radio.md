# ADR-0003: Zigbee is the first radio

Status: Accepted

Decided by the owner, 2026-10-26.

## Context

docs/CONCEPT.md, Radio: a battery panel has to report a flip at once.
Wifi rejoins the network after each wake, which is the delay that makes
battery switches feel slow. A Zigbee end device stays joined to its
parent, and ESPHome supports Zigbee end devices on the ESP32-H2.

## Decision

Zigbee is the first radio: the panel is a sleepy end device on an
ESP32-H2, on the user's existing coordinator. Other radios may follow,
each as its own ADR.

## Consequences

- The radio lives in its own package, `firmware/packages/zigbee.yaml`.
  The component packages (toggle.yaml and later families) declare
  entities without knowing the radio, so another radio replaces one
  package.
- The panel JSON does not name the radio; nothing in it is Zigbee
  specific.
- No wifi on the panel (DIRECTION.md, Not now).
- ESPHome 2026.5 offers the sleepy end device option on nRF52 only. On
  the H2 the panel deep sleeps and rejoins its parent on each wake until
  ESPHome supports it (docs/CONCEPT.md, Open questions).
