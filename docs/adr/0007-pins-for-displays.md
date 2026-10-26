# ADR-0007: Pins for displays: after the wake and ADC pins

Status: Proposed

Proposed for #20.

## Context

A TM1637 display takes two pins, CLK and DIO, which the firmware only
drives; neither has to wake the panel or read a voltage. ADR-0004 and
ADR-0005 assign pins without one in component order from `PIN_ORDER`,
wake pins (10 to 14) first, so a display listed before the controls
would take two of the five wake pins, and one listed after an encoder
two of the last ones, leaving fewer for toggles and buttons. The three
ADC pins are as scarce for rotary switches.

## Decision

- A display takes two named pins, `clk` and `dio` (`FAMILY_PINS`), and
  is in `OUTPUT_FAMILIES` in scripts/panels.py: its pins left out of
  the panel are assigned in `OUTPUT_ORDER`, the pins that can neither
  wake nor read a voltage first (0, 22, 23, 24), then the ADC pins,
  then the wake pins, each group in `PIN_ORDER` order.
- A pin a display is given in the panel follows ADR-0004 unchanged.
- An output pin outside the wake pins is not reported as [info]; it
  never needs to wake the panel.

## Consequences

- A display never costs a wake pin while another pin is free, wherever
  it sits in the component list.
- Panels without a display wire exactly as before.
- On a panel with a display, GPIO 0 and 22 are no longer free for the
  controls that come after it in the automatic order; the controls
  take the wake pins first anyway.
- A later output family (pilot lamps) joins `OUTPUT_FAMILIES` the same
  way.
