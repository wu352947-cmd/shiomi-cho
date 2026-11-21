"""Master deterministic Blender 5.2 generator for Shiomi-cho (汐見町).

Usage:
    /home/box/.local/bin/blender -b --factory-startup --python blender/build.py
"""

import os
import sys
import time
import bpy

BLENDER_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BLENDER_DIR)
if BLENDER_DIR not in sys.path:
    sys.path.insert(0, BLENDER_DIR)

from lib.materials import create_all_materials, toggle_ao_preview
from lib.geo import ensure_collection
from terrain import build_terrain_mesh
from roads_rail import build_roads_and_rail
from harbor import build_harbor
from houses import build_houses
from shrine import build_shrine
from nature import build_nature
from props import build_props
from background import build_background
from bake_ao import bake_scene_ao
from export import optimize_scene_for_export, export_town_glb

SEED = 4207


def clear_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if bpy.context.scene.world is None:
        bpy.context.scene.world = bpy.data.worlds.new("ShiomiWorld")


def build_all(
    ao_samples: int = 16,
    save_blend: bool = True,
    use_meshopt: bool = False,
) -> dict:
    t0 = time.time()
    print("=== Shiomi-cho (汐見町) Build Start ===")
    clear_scene()
    create_all_materials()

    c_terrain = ensure_collection("01_Terrain")
    c_roads = ensure_collection("02_RoadsRail")
    c_harbor = ensure_collection("03_Harbor")
    c_houses = ensure_collection("04_Houses")
    c_shrine = ensure_collection("05_Shrine")
    c_nature = ensure_collection("06_Nature")
    c_props = ensure_collection("07_Props")
    c_bg = ensure_collection("08_Background")

    print("[1/8] Building terrain & stone retaining walls...")
    build_terrain_mesh(c_terrain)
    print("[2/8] Building coastal road, lanes, stairway, railway, station & tram...")
    build_roads_and_rail(c_roads)
    print("[3/8] Building harbor quay, piers, breakwaters, tetrapods, lighthouse & boats...")
    build_harbor(c_harbor, seed=SEED)
    print("[4/8] Building dense town houses, shops, apartments, warehouses & landmarks...")
    build_houses(c_houses, seed=SEED)
    print("[5/8] Building hilltop Shiomi Shrine...")
    build_shrine(c_shrine)
    print("[6/8] Building trees, sakura, coastal pines, hydrangea & boulders...")
    build_nature(c_nature, seed=SEED)
    print("[7/8] Building utility poles, wires, vending machines, bikes, lamps & cats...")
    build_props(c_props, seed=SEED)
    print("[8/8] Building layered distant mountains & sea islands...")
    build_background(c_bg)

    print("[Opt] Applying transforms & joining static geometry by spatial zone...")
    optimize_scene_for_export(join_tetrapods=True)

    print("[AO] Baking Cycles CPU Ambient Occlusion to vertex attribute 'AO'...")
    bake_scene_ao(samples=ao_samples, attr_name="AO")

    # Keep materials pure ART_BIBLE base colors for glTF export
    toggle_ao_preview(False)

    if save_blend:
        blend_path = os.path.join(BLENDER_DIR, "shiomi_town.blend")
        bpy.ops.wm.save_as_mainfile(filepath=blend_path)
        print(f"[Save] Saved Blender scene to {blend_path}")

    glb_path = os.path.join(PROJECT_DIR, "public", "models", "town.glb")
    stats_path = os.path.join(PROJECT_DIR, "public", "models", "town.stats.json")
    elapsed = time.time() - t0
    stats = export_town_glb(
        glb_path=glb_path,
        stats_path=stats_path,
        build_seconds=elapsed,
        ao_method=f"cycles_cpu_vertex_ao_{ao_samples}spp",
        use_meshopt=use_meshopt,
    )
    print("=== Build Complete ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    return stats


if __name__ == "__main__":
    build_all(ao_samples=16, save_blend=True, use_meshopt=True)
