# ADR-0004: Pins on the ESP32-H2

Status: Accepted

Decided by the supervisor, in review of #15.

## Context

Each component needs a GPIO. Panels written before pins existed, and
most panels after, should not have to name them. On the ESP32-H2 some
GPIOs are taken by the SPI flash (6, 7, 15 to 21), USB (26, 27) or
strapping (2, 3, 8, 9, 25), and only 10 to 14 of the rest can wake the
chip from deep sleep, which a toggle needs to wake the panel
(docs/CONCEPT.md, Power).

## Decision

- A component may set `"pin"`; scripts/panels.py rejects a pin outside
  the usable set (`PINS`) or used twice.
- Components without one take the next free pin in `PIN_ORDER`, in
  component order, the wake capable pins 10 to 14 first.
- A toggle on a pin that cannot wake is reported as [info], not a
  failure.

## Consequences

- Panels without pins keep working, and their wiring follows from the
  component order.
- Changing the order of `PIN_ORDER` rewires every panel that relies on
  it, so it only grows at the end.
- At most five toggles per panel can wake the H2.
