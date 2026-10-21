---
name: hero-render
description: Re-render the photoreal README images (media/hero.png, back.png, build.png) from the CAD via headless Blender Cycles. Use after any change that alters what the hero panel or its templates look like, when asked for a beauty or hero render, or when tuning the scene in scripts/hero_scene.py.
---

# Render the README images

```bash
python3 scripts/render_hero.py                          # every shot -> media/
python3 scripts/render_hero.py hero --draft --out "$SCRATCH"   # iterate on one
```

How it works: panels.py writes the wrapper for HERO_PANEL, OpenSCAD
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
- Keep-in-sync sweep for materials: the color tags at the top of
  cad/lib/panel.scad, MATERIALS in render_hero.py and PBR() in
  hero_scene.py.

## When it fails

- `untagged geometry: color #XXXXXX`: geometry without one of the color
  tags reached the scene. Tag it in panel.scad, or add the material to
  all three places in the sweep.
- Blender exits with no output: LD_LIBRARY_PATH leaked in; run through
  the script, which strips it.
- 3MF export failure prints the OpenSCAD log; see openscad-review.

## Notes

- Oak grain is procedural: growth rings around the board's long (x)
  axis, the log center set off the board in object space. A grain that
  only shows on the end grain means the rings run along the wrong axis.
- The backdrop is placed behind the subject as seen from the camera; a
  fixed backdrop put the back shot's camera behind the wall (all black).
- Lights are placed relative to the camera azimuth and scaled with the
  subject size, so a new shot or a bigger panel needs no relighting.
