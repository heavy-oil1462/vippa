# 0005 Pins for knobs: named pins and a resistor ladder

## Status

Proposed

## Context

ADR-0004 gives each component one GPIO. The families added for #18 do
not all fit that: an incremental encoder with push needs three inputs
(the two phases and the push switch), and a rotary switch has one
contact per position, six on the first one in the catalog. The
ESP32-H2 has twelve usable GPIOs (`PINS` in scripts/panels.py), only
five of which can wake it (10 to 14). One input per position would
spend most of a panel's pins on one knob, and a common on a pull up
draws about 70 uA through whichever position is closed, more than the
whole sleep budget (docs/CONCEPT.md, Power). ESPHome's Zigbee on the
ESP32 exposes binary sensors (binary input) and sensors (analog input)
only, so a knob reaches Home Assistant as a number either way.

## Decision

- A family may take several pins, named: `FAMILY_PINS` in
  scripts/panels.py. An encoder takes `push`, `a` and `b`, in that
  order, so its push gets a wake pin first. In a panel, `"pin"` stays a
  number for a one pin family and is an object of role to GPIO for the
  others; roles left out are assigned from `PIN_ORDER` as in ADR-0004.
- A rotary switch is read as a resistor ladder on one ADC pin
  (`ADC_FAMILIES`, `ADC_PINS`): positions + 1 equal high value resistors
  from 3.3 V to ground, the taps to the positions, the common to the
  pin. The firmware package (firmware/packages/rotary.yaml) turns the
  voltage into the position number, an analog input. panels.py rejects
  a rotary switch on a pin that is not an ADC pin, and assigns it the
  first free ADC pin in `PIN_ORDER`.
- The firmware passes a family's only pin as var `pin` and the others
  as `pin_<role>`.

## Consequences

- An encoder counts three pins against the five wake pins; a panel
  with two encoders has no wake pin left for a third control.
- Any number of positions costs one pin, and with 470 k resistors the
  ladder draws about 1 uA, always.
- The ADC pins (1, 4, 5 among `PINS`) cannot wake the H2, so a turn of
  a rotary switch is reported at the next wake. A pushbutton or toggle
  beside it that wakes the panel brings the position along.
- The ladder's accuracy rests on the 3.3 V rail; rounding to the
  nearest position leaves half a step of margin.
- A panel that gives an encoder's pins names them; a panel written for
  ADR-0004 alone is unchanged.
