# Vippa

Rugged Home Assistant controls made from a solid piece of hardwood or
brass, with real retro toggle switches, rotary knobs, pilot lamps and
analog meters set into it. An ESP32 running ESPHome sits behind the
panel. Open hardware and firmware.

The wood is cut by hand: printed drill guides sit on the board and steer
the drill and Forstner bits, so no CNC is needed. The same geometry can
also go to a CNC router as a DXF.

Status: repository scaffold. The hardware design starts next; the
firmware follows after it. See `docs/CONCEPT.md` and `TODO.md`.

## Layout

| Path | What |
| --- | --- |
| `cad/design_params.scad` | values every model shares |
| `cad/calibration/` | gauges for measured fits |
| `cad/lib/` | shared OpenSCAD helpers |
| `docs/` | concept and design notes |
| `scripts/` | the build pipeline, standard library Python |

## Calibration first

Print `cad/calibration/drill_guide_gauge.scad` with the bit you will
drill with, try the bit in each bore and set `drill_clearance` in
`cad/design_params.scad` to the tightest bore it turns in freely without
wobble.

## Working on the design

Everything is driven from one script:

```bash
python3 scripts/regen_all.py           # gates, then every STL
python3 scripts/regen_all.py --check   # read-only gate, what CI runs
```

It fetches OpenSCAD through nix. Without nix, point `OPENSCAD` at your own
binary. The scripts are standard library Python.

## License

MIT, see `LICENSE`.
