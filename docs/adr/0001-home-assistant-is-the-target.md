# 0001 Home Assistant is the target

## Status

Accepted (the owner, 2026-10-26)

## Context

A Vippa panel is a set of physical controls with nothing to control on
its own. It needs one home automation system to report to, and the
names, entity types and pairing flow follow from that choice.

## Decision

Panels control Home Assistant. Entities, names and pairing follow what
Home Assistant expects through its Zigbee integrations, ZHA or
Zigbee2MQTT.

## Consequences

- Each control becomes a Home Assistant entity named after its
  component id in the panel JSON, so the JSON names what the user sees.
- A panel pairs like any other Zigbee device: the user's coordinator,
  ZHA or Zigbee2MQTT, no bridge or add on of our own.
- Other systems may work through the same Zigbee clusters, but they are
  not designed for or tested.
