"""Scene finalization, zone-based static joining (<400 draw calls),
glTF 2.0 binary (.glb) export, and town.stats.json generation.
"""

import json
import os
import struct
import bpy
from lib.geo import apply_auto_smooth

KEEP_SEPARATE_PREFIXES = ("anim_", "lamp_", "sign_", "lighthouse_lamp")


def _is_kept_separate(obj: bpy.types.Object) -> bool:
    return obj.name.startswith(KEEP_SEPARATE_PREFIXES)


def _smooth_angle_for(name: str) -> float:
    if name.startswith("anim_tree_"):
        return 78.0
    if name.startswith(("bg_", "static_background")):
        return 65.0
    if name == "terrain_main":
        return 42.0
    return 30.0


def _ensure_sign_uvs(obj: bpy.types.Object) -> None:
    """Assign clean [0,1]x[0,1] planar UVs to `sign_*` meshes so canvas textures
    render upright and un-mirrored from front (-Y) and back (+Y) views.
    """
    mesh = obj.data
    if mesh is None or len(mesh.vertices) == 0:
        return
    uv_layer = mesh.uv_layers.get("UVMap") or mesh.uv_layers.new(name="UVMap")
    xs = [v.co.x for v in mesh.vertices]
    zs = [v.co.z for v in mesh.vertices]
    min_x, max_x = min(xs), max(xs)
    min_z, max_z = min(zs), max(zs)
    span_x = max(1e-4, max_x - min_x)
    span_z = max(1e-4, max_z - min_z)
    for poly in mesh.polygons:
        flip_u = poly.normal.y > 0.0
        for loop_idx in poly.loop_indices:
            vco = mesh.vertices[mesh.loops[loop_idx].vertex_index].co
            u = (vco.x - min_x) / span_x
            if flip_u:
                u = 1.0 - u
            v = (vco.z - min_z) / span_z
            uv_layer.data[loop_idx].uv = (u, v)


def _apply_transforms_safe(objs: list[bpy.types.Object]) -> None:
    """Bake world transforms on static meshes before zone-joining, while
    preserving local object pivots on `anim_*` and `sign_*` objects for web animation/UVs.
    """
    for obj in objs:
        if obj.type != "MESH" or obj.data is None:
            continue
        if obj.name.startswith("sign_"):
            _ensure_sign_uvs(obj)
            continue
        if obj.name.startswith(("anim_", "lamp_", "lighthouse_lamp")):
            # Keep clean local pivot & rotation for bobbing/swaying in Three.js
            apply_auto_smooth(obj.data, _smooth_angle_for(obj.name))
            continue
        if obj.data.users > 1:
            continue
        mw = obj.matrix_world.copy()
        if mw != mw.Identity(4):
            obj.data.transform(mw)
            obj.matrix_world = mw.Identity(4)
            apply_auto_smooth(obj.data, _smooth_angle_for(obj.name))


def _join_objects(objs: list[bpy.types.Object], target_name: str, col) -> bpy.types.Object | None:
    valid = [o for o in objs if o.type == "MESH" and o.data is not None and len(o.data.polygons) > 0]
    if not valid:
        return None
    if len(valid) == 1:
        valid[0].name = target_name
        return valid[0]

    # Ensure unique mesh data before joining so no shared instanced datablock is mutated
    for o in valid:
        if o.data.users > 1:
            o.data = o.data.copy()

    bpy.ops.object.select_all(action="DESELECT")
    for o in valid:
        o.select_set(True)
    bpy.context.view_layer.objects.active = valid[0]
    bpy.ops.object.join()
    joined = bpy.context.view_layer.objects.active
    joined.name = target_name
    joined.data.name = target_name
    apply_auto_smooth(joined.data, _smooth_angle_for(target_name))
    # Ensure linked to target collection
    if col is not None and joined.name not in col.objects:
        col.objects.link(joined)
    return joined


def optimize_scene_for_export(join_tetrapods: bool = True) -> None:
    """Apply transforms and join static buildings/props by spatial zone to keep draw calls < 400."""
    bpy.context.view_layer.update()
    all_meshes = [o for o in bpy.data.objects if o.type == "MESH"]

    # Optionally bake instanced tetrapods into harbor_static if viewer doesn't load GPU instancing
    if join_tetrapods:
        for o in all_meshes:
            if "_tetra_" in o.name and o.data.users > 1:
                o.data = o.data.copy()

    _apply_transforms_safe(all_meshes)

    # Group static objects by logical/spatial zone
    zones: dict[str, list[bpy.types.Object]] = {
        "static_harbor": [],
        "static_coastal": [],
        "static_town_west": [],
        "static_town_east": [],
        "static_upper_shrine": [],
        "static_background": [],
    }

    for obj in list(bpy.data.objects):
        if obj.type != "MESH" or _is_kept_separate(obj):
            continue
        name = obj.name
        if name.startswith("bg_"):
            zones["static_background"].append(obj)
            continue
        if name in ("terrain_main",):
            # Keep terrain separate for crisp culling & readability
            continue
        if name.startswith(("harbor_", "east_bw_", "west_bw_")):
            zones["static_harbor"].append(obj)
            continue
        if name.startswith("shrine_"):
            zones["static_upper_shrine"].append(obj)
            continue
        # Classify houses, roads, retaining walls, props, trunks by bounding-box center
        bbox = [obj.matrix_world @ v for v in [bpy.types.Object.bound_box]] if False else None
        verts = obj.data.vertices
        if len(verts) == 0:
            continue
        ys = [v.co.y for v in verts]
        xs = [v.co.x for v in verts]
        cy = 0.5 * (min(ys) + max(ys))
        cx = 0.5 * (min(xs) + max(xs))
        if name in ("roads_and_rail", "terrain_retaining_walls", "props_static", "garden_walls", "nature_trunks_rocks"):
            # Keep infrastructure / props cleanly grouped into coastal vs hillside
            if name in ("roads_and_rail", "props_static"):
                zones["static_coastal"].append(obj)
            else:
                zones["static_town_east"].append(obj)
            continue
        if cy < 16.0:
            zones["static_coastal"].append(obj)
        elif cy > 96.0:
            zones["static_upper_shrine"].append(obj)
        elif cx < 0.0:
            zones["static_town_west"].append(obj)
        else:
            zones["static_town_east"].append(obj)

    root_col = bpy.context.scene.collection
    for zname, zobjs in zones.items():
        if zobjs:
            _join_objects(zobjs, zname, root_col)

    # Clean up unused empty meshes/materials
    for m in list(bpy.data.meshes):
        if m.users == 0:
            bpy.data.meshes.remove(m)


def _inspect_glb_stats(glb_path: str) -> dict:
    """Parse GLB JSON header to report exact exported meshes, primitives (draw calls),
    triangles, materials, and file size.
    """
    size_bytes = os.path.getsize(glb_path)
    with open(glb_path, "rb") as f:
        header = f.read(12)
        magic, version, total_len = struct.unpack("<4sII", header)
        chunk_len, chunk_type = struct.unpack("<II", f.read(8))
        json_bytes = f.read(chunk_len)
    gltf = json.loads(json_bytes.decode("utf-8"))

    meshes = gltf.get("meshes", [])
    accessors = gltf.get("accessors", [])
    nodes = gltf.get("nodes", [])
    materials = gltf.get("materials", [])

    # Count mesh instances across scene nodes for accurate draw-call count
    draw_calls = 0
    total_tris = 0
    has_color0 = False
    sign_extras = 0
    for node in nodes:
        if "extras" in node and "text" in node["extras"]:
            sign_extras += 1
        if "mesh" in node:
            mesh = meshes[node["mesh"]]
            for prim in mesh.get("primitives", []):
                draw_calls += 1
                attrs = prim.get("attributes", {})
                if "COLOR_0" in attrs:
                    has_color0 = True
                if "indices" in prim:
                    total_tris += accessors[prim["indices"]]["count"] // 3
                elif "POSITION" in attrs:
                    total_tris += accessors[attrs["POSITION"]]["count"] // 3

    return {
        "file_size_bytes": size_bytes,
        "file_size_mb": round(size_bytes / (1024 * 1024), 2),
        "triangles": total_tris,
        "objects": len([n for n in nodes if "mesh" in n]),
        "draw_calls": draw_calls,
        "materials": len(materials),
        "has_vertex_ao_color0": has_color0,
        "sign_extras_count": sign_extras,
    }


def export_town_glb(
    glb_path: str,
    stats_path: str,
    build_seconds: float,
    ao_method: str = "cycles_vertex_ao",
    use_meshopt: bool = False,
) -> dict:
    """Export finalized scene to glTF binary (.glb) and write town.stats.json."""
    os.makedirs(os.path.dirname(glb_path), exist_ok=True)
    os.makedirs(os.path.dirname(stats_path), exist_ok=True)

    # Make sure only mesh objects are exported (exclude any helper cameras/lights)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            obj.select_set(True)

    export_kwargs = dict(
        filepath=glb_path,
        export_format="GLB",
        use_selection=True,
        export_yup=True,
        export_apply=True,
        export_normals=True,
        export_materials="EXPORT",
        export_vertex_color="NAME",
        export_vertex_color_name="AO",
        export_all_vertex_colors=False,
        export_extras=True,
        export_gpu_instances=True,
        export_animations=False,
    )
    if use_meshopt:
        export_kwargs["export_meshopt_compression_enable"] = True
        export_kwargs["export_meshopt_extension"] = "EXT_meshopt_compression"

    bpy.ops.export_scene.gltf(**export_kwargs)

    stats = _inspect_glb_stats(glb_path)
    stats["build_seconds"] = round(build_seconds, 2)
    stats["ao_method"] = ao_method
    stats["compression"] = "EXT_meshopt_compression" if use_meshopt else "none"

    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    return stats
