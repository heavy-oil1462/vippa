---
name: hero-render
description: Re-render the photoreal README images (media/hero.png, back.png, build.png, and media/panels/<name>.png per example panel) from the CAD via headless Blender Cycles. Use after any change that alters what a panel or its templates look like, when asked for a beauty or hero render, or when tuning the scene in scripts/hero_scene.py.
---

# Render the README images

```bash
python3 scripts/render_hero.py                          # every shot -> media/
python3 scripts/render_hero.py hero --draft --out "$SCRATCH"   # iterate on one
python3 scripts/render_hero.py --panels                 # hero shot of every panel -> media/panels/
python3 scripts/render_hero.py --panels --panel bedside # just these (repeat --panel)
python3 scripts/render_hero.py back --panel scenes --draft --out "$SCRATCH"
```

The plain shots show HERO_PANEL (three_toggles) as media/<shot>.png.
`--panel NAME` picks another panel and then needs `--out`, so it never
overwrites the README shots. `--panels` renders PANEL_SHOT of each
panel as media/panels/<name>.png, the pictures in the README's Example
panels section. A panel in `PANEL_EXTRA_SHOTS` gets those shots too,
as media/panels/<name>_<shot>.png (the thermostat's back).

How it works: panels.py writes the wrapper for the panel, OpenSCAD
exports the shot's part (`hero` or `build` in cad/lib/panel.scad) as a
colored 3MF, render_hero.py splits it into one PLY per color tag, and
Blender renders scripts/hero_scene.py with Cycles on CPU. Drafts take
about 15 seconds a shot, full quality about 7 minutes a shot
(21 minutes for all three in the sandbox): run it in the background.

## Rules

- media/*.png are build products of this command: regenerate them in
  the same change that alters what they show, never edit them. They are
  not byte deterministic, so verify does not compare them.
- Judge scene changes by looking at a --draft render, never by reading
  hero_scene.py. Render full quality only once the draft is right.
- Shots (part, camera azimuth, elevation, distance) live in SHOTS in
  render_hero.py. A new shot goes there and into the README.
- A new or changed panel in panels/ gets its media/panels/<name>.png
  (re)rendered in the same change, and a line in the README's Example
  panels section.
- Keep-in-sync sweep for materials: the color tags at the top of
  cad/lib/panel.scad, MATERIALS in render_hero.py and PBR() in
  hero_scene.py. The board's tag is "wood" and renders as the panel's
  board material: a new wood goes into WOODS in panels.py and WOODS in
  hero_scene.py.

## When it fails

- `untagged geometry: color #XXXXXX`: geometry without one of the color
  tags reached the scene. Tag it in panel.scad, or add the material to
  all three places in the sweep.
- Blender exits with no output: LD_LIBRARY_PATH leaked in; run through
  the script, which strips it.
- 3MF export failure prints the OpenSCAD log; see openscad-review.

## Notes

- Wood grain (oak, walnut) is procedural: growth rings around the board's long (x)
  axis, the log center set off the board in object space. A grain that
  only shows on the end grain means the rings run along the wrong axis.
- The backdrop is placed behind the subject as seen from the camera; a
  fixed backdrop put the back shot's camera behind the wall (all black).
- Lights are placed relative to the camera azimuth and scaled with the
  subject size, so a new shot or a bigger panel needs no relighting.
