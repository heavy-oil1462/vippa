# 0004 Pins and wake on the ESP32-H2

## Status

Proposed

## Context

Each component needs a GPIO. Panels written before pins existed, and
most panels after, should not have to name them. On the ESP32-H2 some
GPIOs are taken by the SPI flash (6, 7, 15 to 21), USB (26, 27) or
strapping (2, 3, 8, 9, 25), and only 10 to 14 of the rest can wake the
chip from deep sleep. ESPHome 2026.5 arms deep sleep wake on the H2
only through ext1, with one level for every pin, so it cannot arm each
toggle for the opposite of its current level (docs/CONCEPT.md, Power).

## Decision

- A component may set `"pin"`; scripts/panels.py rejects a pin outside
  the usable set or used twice. Components without one take the next
  free pin in `PIN_ORDER`, the wake capable pins 10 to 14 first, in
  component order. A toggle on a pin that cannot wake is reported as
  [info].
- Until ESPHome arms a wake level per pin on the H2, the generated
  firmware wakes on a timer only (`poll_period`) and reports every
  toggle on each wake. It does not use ext1: with one level for all
  pins, a toggle left at that level would wake the panel again at once
  and drain the cells.

## Consequences

- Panels without pins keep working, and their wiring follows from the
  component order. Changing `PIN_ORDER` rewires those panels, so it
  only grows at the end.
- At most five toggles per panel can wake the H2.
- A flip reaches Home Assistant at the next timer wake, not at once:
  the flip to light latency target (under 300 ms) is not met until
  ESPHome gains per pin wake levels on the H2, or the owner settles the
  open question in docs/CONCEPT.md another way.
