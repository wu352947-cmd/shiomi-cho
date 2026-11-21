"""Headless Eevee self-critique renderer for Shiomi-cho (汐見町).

Loads `blender/shiomi_town.blend`, configures summer 15:30 anime-inspired
sun + blue sky lighting + preview sea plane, enables AO vertex color preview,
and renders 6 review shots into `shots/blender/`.

Usage:
    /home/box/.local/bin/blender -b --factory-startup --python blender/render_check.py
"""

import math
import os
import sys
import time
import bpy
import bmesh
from mathutils import Vector

BLENDER_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BLENDER_DIR)
if BLENDER_DIR not in sys.path:
    sys.path.insert(0, BLENDER_DIR)

from lib.materials import toggle_ao_preview, hex_to_linear_rgba


def _add_preview_sea() -> bpy.types.Object:
    """Add a render-only shimmering blue sea plane at z = 0 (never exported to town.glb)."""
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=8, y_segments=8, size=1400.0)
    mesh = bpy.data.meshes.new("_preview_sea")
    bm.to_mesh(mesh)
    bm.free()

    mat = bpy.data.materials.new("_preview_sea_mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = hex_to_linear_rgba("#3D8BC9")
    bsdf.inputs["Roughness"].default_value = 0.14
    bsdf.inputs["Metallic"].default_value = 0.05
    mesh.materials.append(mat)

    obj = bpy.data.objects.new("_preview_sea", mesh)
    obj.location = (0.0, -420.0, -0.02)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _setup_lighting_and_world(scene: bpy.types.Scene) -> None:
    # Summer afternoon ~15:30: elevation 35 deg, azimuth from South-West (lighting from front-left)
    sun_data = bpy.data.lights.new("SunKey", type="SUN")
    sun_data.energy = 4.6
    sun_data.color = (1.0, 0.94, 0.82)  # warm #FFF1D6
    sun_data.angle = math.radians(1.6)
    sun_obj = bpy.data.objects.new("SunKey", sun_data)
    scene.collection.objects.link(sun_obj)
    # Direction FROM (-1, -1, +tan35) TOWARD town: aim sun vector
    sun_dir = Vector((0.68, 0.56, -0.58)).normalized()
    sun_obj.rotation_euler = sun_dir.to_track_quat("-Z", "Y").to_euler()

    # Cool blue-violet sky fill bounce so shadows are never black
    fill_data = bpy.data.lights.new("SkyFill", type="SUN")
    fill_data.energy = 0.85
    fill_data.color = (0.55, 0.72, 1.0)
    fill_data.use_shadow = False
    fill_obj = bpy.data.objects.new("SkyFill", fill_data)
    scene.collection.objects.link(fill_obj)
    fill_dir = Vector((-0.55, -0.45, -0.70)).normalized()
    fill_obj.rotation_euler = fill_dir.to_track_quat("-Z", "Y").to_euler()

    # Clear bright summer blue sky gradient world
    world = bpy.data.worlds.new("PreviewSkyWorld")
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = hex_to_linear_rgba("#BFE0FA")
    ramp.color_ramp.elements[1].position = 0.45
    ramp.color_ramp.elements[1].color = hex_to_linear_rgba("#4A94E2")
    bg.inputs["Strength"].default_value = 1.15
    nt.links.new(tex_coord.outputs["Generated"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    scene.world = world


def _aim_camera(cam_obj: bpy.types.Object, pos, target, lens: float = 35.0) -> None:
    cam_obj.location = Vector(pos)
    direction = (Vector(target) - Vector(pos)).normalized()
    cam_obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    cam_obj.data.lens = lens
    cam_obj.data.clip_start = 0.2
    cam_obj.data.clip_end = 3000.0


def render_all_shots(res_x: int = 1024, res_y: int = 640) -> list[str]:
    blend_path = os.path.join(BLENDER_DIR, "shiomi_town.blend")
    out_dir = os.path.join(PROJECT_DIR, "shots", "blender")
    os.makedirs(out_dir, exist_ok=True)

    bpy.ops.wm.open_mainfile(filepath=blend_path)
    scene = bpy.context.scene

    # Enable AO vertex color preview in Blender materials for accurate visual inspection
    toggle_ao_preview(True, attr_name="AO")
    _add_preview_sea()
    _setup_lighting_and_world(scene)

    scene.render.engine = "BLENDER_EEVEE"
    if hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = 16
    scene.render.resolution_x = res_x
    scene.render.resolution_y = res_y
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"

    # AgX / Filmic color management
    try:
        scene.view_settings.view_transform = "AgX"
        scene.view_settings.look = "AgX - Punchy"
    except Exception:
        scene.view_settings.view_transform = "Filmic"
    scene.view_settings.exposure = -0.15

    cam_data = bpy.data.cameras.new("ReviewCam")
    cam_obj = bpy.data.objects.new("ReviewCam", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    shots = [
        # 1. Wide overview from South-West over the sea (shows town, shrine, both breakwaters & red lighthouse)
        ("01_overview_sw.png", (-150.0, -195.0, 96.0), (8.0, 26.0, 14.0), 28.0),
        # 2. Harbor close-up: quay, piers, fishing boats, east breakwater & full 14m red lighthouse
        ("02_harbor_closeup.png", (-34.0, -158.0, 29.0), (24.0, -52.0, 5.5), 25.0),
        # 3. Street-level view along coastal shopping street (noren, awnings, wires, vending machines)
        ("03_shopping_street.png", (-20.0, 2.5, 3.2), (16.0, 8.8, 3.4), 30.0),
        # 4. Close-up of 2-3 hillside houses (unobstructed view of flush windows, roofs, trim, AC, balcony)
        ("04_houses_closeup.png", (-42.0, 39.2, 16.5), (-42.0, 54.0, 17.0), 35.0),
        # 5. Hilltop Shiomi Shrine (torii, stairs, honden, lanterns, camphor & sakura)
        ("05_shrine.png", (-14.0, 120.0, 56.5), (-31.0, 148.0, 54.5), 32.0),
        # 6. Level crossing gate/signal, railway tracks, Shiomi Station & coastal tram
        ("06_level_crossing.png", (-31.5, 13.8, 5.0), (10.0, 13.4, 4.0), 30.0),
    ]

    saved = []
    for fname, pos, target, lens in shots:
        t0 = time.time()
        _aim_camera(cam_obj, pos, target, lens)
        fpath = os.path.join(out_dir, fname)
        scene.render.filepath = fpath
        bpy.ops.render.render(write_still=True)
        print(f"[render_check] Rendered {fname} in {time.time() - t0:.1f}s")
        saved.append(fpath)
    return saved


if __name__ == "__main__":
    render_all_shots()
