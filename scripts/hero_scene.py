"""Blender side of the README renders. Not run directly:
scripts/render_hero.py invokes it inside headless Blender as

    blender -b --python hero_scene.py -- <mesh_dir> <out_png> <w> <h>
        <samples> <azimuth> <elevation> <distance>

One PLY per material lands in mesh_dir (render_hero.py's MATERIALS maps
the color tags to the names); PBR() below owns what each material looks
like. Studio setup: dark backdrop, warm key, cool fill and a strong rim
so the chrome reads as metal and the wood grain catches the light. The
board's PLY is named after its wood (panels.WOODS), one of WOODS here.
"""

import math
import pathlib
import sys

import bpy
from mathutils import Vector

mesh_dir, out_png, width, height, samples, azim, elev, dist = sys.argv[-8:]


def principled(name, **inputs):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    for key, val in inputs.items():
        bsdf.inputs[key.replace("_", " ").title()].default_value = val
    return mat


# Oiled hardwood colors (linear RGB): earlywood, the ring body toward the
# latewood, and the thin latewood line.
WOODS = {
    "oak": ((0.36, 0.215, 0.10, 1), (0.31, 0.18, 0.08, 1), (0.21, 0.115, 0.05, 1)),
    "walnut": ((0.105, 0.058, 0.032, 1), (0.085, 0.046, 0.025, 1), (0.04, 0.021, 0.012, 1)),
}


def wood(name):
    """Oiled hardwood: growth rings around the board's long (x) axis, the
    way a flat sawn board is cut from the log. The ring center sits well
    outside the board so the face shows long bands in every orientation
    the shots use. Low frequency noise warps the rings so their spacing
    wanders, and a sawtooth profile gives each ring a thin dark latewood
    line. WOODS sets the colors."""
    early, body, latewood = WOODS[name]
    mat = principled(name, roughness=0.42)
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes["Principled BSDF"]
    coord = nodes.new("ShaderNodeTexCoord")
    place = nodes.new("ShaderNodeMapping")
    place.inputs["Location"].default_value = (0.0, 0.11, -0.09)  # log center, m
    warp = nodes.new("ShaderNodeTexNoise")
    warp.inputs["Scale"].default_value = 4.0
    warp.inputs["Detail"].default_value = 2.0
    warp_amount = nodes.new("ShaderNodeVectorMath")
    warp_amount.operation = "SCALE"
    warp_amount.inputs["Scale"].default_value = 0.014
    centered = nodes.new("ShaderNodeVectorMath")
    centered.operation = "SUBTRACT"
    centered.inputs[1].default_value = (0.007, 0.007, 0.007)
    warped = nodes.new("ShaderNodeVectorMath")
    warped.operation = "ADD"
    wave = nodes.new("ShaderNodeTexWave")
    wave.wave_type = "RINGS"
    wave.rings_direction = "X"
    wave.wave_profile = "SAW"
    wave.inputs["Scale"].default_value = 90.0
    wave.inputs["Distortion"].default_value = 0.6
    wave.inputs["Detail"].default_value = 2.0
    ramp = nodes.new("ShaderNodeValToRGB")
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.0, early
    els[1].position, els[1].color = 0.86, body
    late = els.new(0.95)
    late.color = latewood
    tone = nodes.new("ShaderNodeTexNoise")
    tone.inputs["Scale"].default_value = 3.0
    shade = nodes.new("ShaderNodeMix")
    shade.data_type = "RGBA"
    shade.blend_type = "MULTIPLY"
    shade.inputs["Factor"].default_value = 0.25
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.012
    links.new(coord.outputs["Object"], place.inputs["Vector"])
    links.new(place.outputs["Vector"], warp.inputs["Vector"])
    links.new(warp.outputs["Color"], warp_amount.inputs[0])
    links.new(warp_amount.outputs["Vector"], centered.inputs[0])
    links.new(place.outputs["Vector"], warped.inputs[0])
    links.new(centered.outputs["Vector"], warped.inputs[1])
    links.new(warped.outputs["Vector"], wave.inputs["Vector"])
    links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], shade.inputs["A"])
    links.new(tone.outputs["Color"], shade.inputs["B"])
    links.new(shade.outputs["Result"], bsdf.inputs["Base Color"])
    links.new(wave.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def PBR(name):
    if name in WOODS:
        return wood(name)
    if name == "chrome":
        return principled(name, base_color=(0.80, 0.80, 0.82, 1),
                          metallic=1.0, roughness=0.12)
    if name == "black":
        return principled(name, base_color=(0.02, 0.02, 0.02, 1), roughness=0.45)
    if name == "printed":
        return principled(name, base_color=(0.80, 0.77, 0.70, 1), roughness=0.6)
    if name == "pcb":
        return principled(name, base_color=(0.03, 0.18, 0.08, 1), roughness=0.35)
    if name == "aluminium":  # machined knob: brushed, softer than chrome
        return principled(name, base_color=(0.70, 0.70, 0.72, 1),
                          metallic=1.0, roughness=0.32)
    if name == "bakelite":  # knob: near black, a warm brown in the highlights
        return principled(name, base_color=(0.018, 0.010, 0.007, 1), roughness=0.22)
    if name == "led":  # a lit segment: red, glowing
        return principled(name, base_color=(0.9, 0.05, 0.02, 1), roughness=0.3,
                          emission_color=(1.0, 0.06, 0.02, 1), emission_strength=6.0)
    if name == "cell":
        return principled(name, base_color=(0.05, 0.10, 0.40, 1), roughness=0.25)
    raise ValueError(f"no PBR definition for material {name!r}")


bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = int(samples)
scene.cycles.use_denoising = True
scene.render.resolution_x = int(width)
scene.render.resolution_y = int(height)

lo = Vector((1e9,) * 3)
hi = Vector((-1e9,) * 3)
for ply in sorted(pathlib.Path(mesh_dir).glob("*.ply")):
    bpy.ops.wm.ply_import(filepath=str(ply))
    obj = bpy.context.selected_objects[0]
    bpy.context.view_layer.objects.active = obj
    obj.scale = (0.001,) * 3  # mm -> m
    bpy.ops.object.transform_apply(scale=True)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(28))
    obj.data.materials.append(PBR(ply.stem))
    for v in obj.data.vertices:
        co = obj.matrix_world @ v.co
        lo = Vector(map(min, lo, co))
        hi = Vector(map(max, hi, co))

center = (lo + hi) / 2
size = max(hi - lo)

# dark bench top and a backdrop well behind the subject
bpy.ops.mesh.primitive_plane_add(size=size * 40, location=(center.x, center.y, lo.z))
bpy.context.object.data.materials.append(
    principled("bench", base_color=(0.035, 0.033, 0.03, 1), roughness=0.35))
# the backdrop stands behind the subject as seen from the camera
a = math.radians(float(azim))
behind = Vector((-math.sin(a), math.cos(a), 0)) * size * 2.5
bpy.ops.mesh.primitive_plane_add(size=size * 40, location=center + behind - Vector((0, 0, center.z - lo.z)),
                                 rotation=(math.pi / 2, 0, a))
bpy.context.object.data.materials.append(
    principled("backdrop", base_color=(0.03, 0.032, 0.035, 1), roughness=0.7))


def area_light(offset, energy, scale, color):
    loc = center + Vector(offset) * size
    bpy.ops.object.light_add(type="AREA", location=loc)
    light = bpy.context.object
    light.data.energy = energy * size * size
    light.data.size = scale * size
    light.data.color = color
    light.rotation_euler = (center - loc).to_track_quat("-Z", "Y").to_euler()


# lights travel with the camera so every shot is lit from the front
rot = lambda x, y, z: (x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a), z)  # noqa: E731
area_light(rot(-2.2, -2.6, 3.0), 900, 2.5, (1.0, 0.95, 0.88))   # warm key
area_light(rot(3.0, -1.5, 1.6), 220, 3.5, (0.85, 0.90, 1.0))     # cool fill
area_light(rot(0.8, 3.2, 3.4), 1500, 1.6, (1.0, 0.98, 0.95))     # rim
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Punchy"
scene.view_settings.exposure = -0.6
world = bpy.data.worlds.new("world")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.02, 0.022, 0.025, 1)
bg.inputs["Strength"].default_value = 1.0

e = math.radians(float(elev))
direction = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
bpy.ops.object.camera_add(location=center + direction * size * float(dist))
cam = bpy.context.object
cam.data.lens = 85
cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.camera = cam

scene.render.filepath = out_png
bpy.ops.render.render(write_still=True)
print("rendered:", out_png)
