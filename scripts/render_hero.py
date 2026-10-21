#!/usr/bin/env python3
"""Render the photoreal README images in media/ from the CAD.

    python3 scripts/render_hero.py                  # every shot, full quality
    python3 scripts/render_hero.py hero --draft     # one shot, small and fast
    python3 scripts/render_hero.py --draft --out DIR

Pipeline: scripts/panels.py writes the wrapper for HERO_PANEL, OpenSCAD
exports the shot's part as a colored 3MF (the color() tags in
cad/lib/panel.scad are the material tags), this script splits the mesh
into one PLY per material, and headless Blender (Cycles, CPU) renders
the studio scene in scripts/hero_scene.py.

The results go to media/, not build/: they are committed as the README
images. Cycles output is not byte deterministic across machines, so they
can never sit under a byte drift gate; they are still build products.
Regenerate them in the same change that alters what they show, never
edit them by hand.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict
from pathlib import Path

import panels
from render_scad import nix_path, render

ROOT = Path(__file__).resolve().parent.parent
SCENE = ROOT / "scripts" / "hero_scene.py"
HERO_PANEL = "three_toggles"

# 3MF displaycolor (the color() tags in cad/lib/panel.scad) -> material
# name. hero_scene.py owns the PBR definition for each name. Keep-in-sync
# sweep: the tags in panel.scad, this table and PBR() in hero_scene.py.
MATERIALS = {
    "C8A165": "oak",
    "C0C0C0": "chrome",
    "222222": "black",
    "E8E4DA": "printed",
}

# shot -> (panel part, camera azimuth deg, elevation deg, distance factor)
# Azimuth 0 looks along +y, so the hero part (front toward -y) faces it.
SHOTS = {
    "hero": ("hero", -32, 14, 4.2),
    "back": ("hero", 145, 22, 4.4),
    "build": ("build", -18, 42, 2.6),
}

M3MF = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}


def export_3mf(scad: Path, part: str, out: Path) -> None:
    proc = render(str(scad), str(out), ["-D", f'part="{part}"'])
    if proc.returncode != 0 or "WARNING" in proc.stderr:
        sys.exit(f"[FAIL] 3MF export of {part}:\n{proc.stderr[-2000:]}")


def split_by_material(threemf: Path, mesh_dir: Path) -> None:
    """One ascii PLY per material color; die on untagged geometry."""
    root = ET.fromstring(zipfile.ZipFile(threemf).read("3D/3dmodel.model"))
    colors = [b.get("displaycolor").lstrip("#")[:6].upper()
              for b in root.findall(".//m:basematerials/m:base", M3MF)]
    groups = defaultdict(list)  # material name -> [(vertices, triangles)]
    for obj in root.findall(".//m:object", M3MF):
        verts = [(float(v.get("x")), float(v.get("y")), float(v.get("z")))
                 for v in obj.findall(".//m:vertices/m:vertex", M3MF)]
        by_color = defaultdict(list)
        for t in obj.findall(".//m:triangles/m:triangle", M3MF):
            p1 = t.get("p1", obj.get("pindex"))
            if p1 is None:
                sys.exit("[FAIL] untagged geometry: a triangle has no color,"
                         " every part needs a color() material tag")
            by_color[int(p1)].append((int(t.get("v1")), int(t.get("v2")), int(t.get("v3"))))
        for idx, tris in by_color.items():
            name = MATERIALS.get(colors[idx])
            if name is None:
                sys.exit(f"[FAIL] untagged geometry: color #{colors[idx]} has no"
                         " entry in MATERIALS")
            groups[name].append((verts, tris))

    for name, meshes in sorted(groups.items()):
        vlines, flines, base = [], [], 0
        for verts, tris in meshes:
            used = sorted({i for tri in tris for i in tri})
            remap = {i: base + n for n, i in enumerate(used)}
            vlines += ["%.4f %.4f %.4f" % verts[i] for i in used]
            flines += [f"3 {remap[a]} {remap[b]} {remap[c]}" for a, b, c in tris]
            base += len(used)
        (mesh_dir / f"{name}.ply").write_text(
            "ply\nformat ascii 1.0\n"
            f"element vertex {len(vlines)}\n"
            "property float x\nproperty float y\nproperty float z\n"
            f"element face {len(flines)}\n"
            "property list uchar int vertex_indices\nend_header\n"
            + "\n".join(vlines + flines) + "\n")
        print(f"ok: {name}.ply ({len(flines)} triangles)")


def blender_bin() -> str:
    """$BLENDER, then blender on PATH, then the pinned nix one."""
    return (os.environ.get("BLENDER") or shutil.which("blender")
            or nix_path("blender") + "/bin/blender")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("shots", nargs="*", choices=[[], *SHOTS], default=[])
    ap.add_argument("--out", type=Path, default=ROOT / "media")
    ap.add_argument("--draft", action="store_true",
                    help="640x480, few samples, for scene iteration")
    args = ap.parse_args()
    width, height, samples = (640, 480, 24) if args.draft else (1920, 1280, 160)

    args.out.mkdir(parents=True, exist_ok=True)
    catalog, errors = panels.load_catalog()
    if errors:
        sys.exit("[FAIL] catalog: " + "; ".join(errors))
    for shot in args.shots or SHOTS:
        part, azim, elev, dist = SHOTS[shot]
        out = args.out / f"{shot}.png"
        with tempfile.TemporaryDirectory() as tmp:
            mesh_dir = Path(tmp)
            scad = panels.wrapper(HERO_PANEL, panels.load_panel(HERO_PANEL), catalog,
                                  mesh_dir / f"{HERO_PANEL}.scad")
            export_3mf(scad, part, mesh_dir / "scene.3mf")
            split_by_material(mesh_dir / "scene.3mf", mesh_dir)
            # the sandbox's LD_LIBRARY_PATH segfaults nix blender: drop it
            env = {k: v for k, v in os.environ.items() if k != "LD_LIBRARY_PATH"}
            proc = subprocess.run(
                [blender_bin(), "-b", "-noaudio", "--factory-startup",
                 "--python", str(SCENE), "--", str(mesh_dir), str(out),
                 str(width), str(height), str(samples), str(azim), str(elev), str(dist)],
                env=env, capture_output=True, text=True)
            tail = "\n".join((proc.stdout + proc.stderr).splitlines()[-12:])
            if proc.returncode != 0 or not out.exists():
                sys.exit(f"[FAIL] blender render of {shot}:\n{tail}")
        shown = out.relative_to(ROOT) if out.is_relative_to(ROOT) else out
        print(f"ok: {shown} ({width}x{height})", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
