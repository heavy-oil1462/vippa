---
name: panel-config
description: Add or change a Vippa panel (panels/<name>.json), validate it and look at the result. Use when the user wants a new panel, a different layout, board size or cavity, or asks whether a layout works.
---

# Panel config

```bash
python3 scripts/panels.py <name>          # validate one panel, fast
python3 scripts/regen_all.py <name>       # templates and previews into build/panels/<name>/
```

## Format

```json
{
  "description": "what this panel is",
  "board": {"w": 180, "h": 90, "t": 27, "chamfer": 2, "material": "oak"},
  "cavity": {"face_t": 4, "rim": 18, "r": 8},
  "components": [{"id": "left", "type": "toggle_12mm", "x": 45, "y": 45}]
}
```

- Millimetres. x, y are hole centers measured from the reference corner:
  bottom left seen from the front.
- face_t: wood left over the cavity; it must not exceed any component's
  max_panel_t. rim: wood around the cavity. r: cavity corner radius, at
  least the router bit radius.
- type is a key of catalog/components.json. A part that is not there
  is added with the component-catalog skill first, never inlined here.
- id is the component's name; the firmware will use it later, so keep
  it stable and meaningful.

## Procedure

1. Write or edit the JSON, run `panels.py <name>` until it is `[ok]`.
2. Run `regen_all.py <name>`, then look at `front.png` and `back.png` in
   build/panels/<name>/ with the Read tool. State what they should show
   first.
3. If the panel is the hero panel (HERO_PANEL in render_hero.py),
   regenerate media/ with the hero-render skill in the same change.
4. Run verify before committing.

## When it fails

- `face_t ... thicker than the bushing takes`: thin the face (raise
  cavity depth) or pick a part with a longer bushing.
- `cavity depth ... shallower than back nut plus body`: thicker board or
  thinner face.
- `leaves the cavity`: move the part inward or shrink the rim.
- `keepouts need`: spread the parts; keepout_d is in the catalog.
- An assert from cad/lib/panel.scad during regen (bit radius, rail
  width, router base span, bed size) is a tooling limit: change the
  panel, never the assert.
