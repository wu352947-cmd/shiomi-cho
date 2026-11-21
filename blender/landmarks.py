"""Distinctive Shiomi-cho town landmarks and dense residential yard details:
- Enlarged Harbor Fish Market Hall (汐見魚市場) with clerestory red tin roof
- Coastal Elementary School / Clock Building (汐見小学校) with prominent clock gable
- Elevated Coastal Water Tower on braced steel legs
- 100% hillside residential garden walls, side fences, stepping stones, planters & yard laundry
"""

import math
import random
from mathutils import Vector, Euler
from lib.geo import MeshBuilder
from lib.roofs import add_kirizuma_roof
from terrain import get_height


def _world_pt(origin: Vector, rot_z: float, local: tuple[float, float, float]) -> Vector:
    return origin + (Euler((0.0, 0.0, rot_z)).to_matrix() @ Vector(local))


def build_fish_market(spec: dict, col, rng: random.Random) -> list:
    """Enlarged harbor Fish Market Hall with clerestory roof monitor & wide loading canopy."""
    w, d = spec["w"], spec["d"]
    h = 5.4
    pos, rot_z = Vector(spec["pos"]), spec["rot_z"]
    mb = MeshBuilder(spec["name"])
    objs = []

    # Concrete plinth + raised wide loading dock along quay front
    mb.box((0.0, 0.0, -1.2), (w + 0.4, d + 0.4, 3.4), "concrete", bevel=0.03)
    mb.box((0.0, -d * 0.5 - 1.05, 0.30), (w + 0.6, 2.05, 0.62), "concrete", bevel=0.03)
    # Main timber/plaster hall body + weathered wood wainscoting + pilaster columns
    mb.box((0.0, 0.0, 0.52 + h * 0.5), (w, d, h), "wall_cream", bevel=0.03, subdiv_cuts=1)
    mb.box((0.0, 0.0, 1.55), (w + 0.08, d + 0.08, 2.05), "wood_weathered", bevel=0.02)
    for px in (-w * 0.48, -w * 0.16, w * 0.16, w * 0.48):
        mb.box((px, -d * 0.5 - 0.04, 0.52 + h * 0.5), (0.24, 0.22, h), "wood_dark", bevel=0.015)

    # Three wide sliding cargo bays + high clerestory windows
    for dx in (-w * 0.30, 0.0, w * 0.30):
        mb.door_unit((dx, -d * 0.5, 0.60), 3.15, 2.95, "-Y", "metal_dark", "wood_dark", None, sliding=True)
        mb.window_unit((dx, -d * 0.5, 4.72), 2.80, 0.82, "-Y", "metal_dark", "window_glass", None, mullions=(3, 0))
        mb.window_unit((dx, d * 0.5, 4.72), 2.80, 0.82, "+Y", "metal_dark", "window_glass", None, mullions=(3, 0))

    # Projecting steel-framed corrugated loading canopy over dock
    mb.box((0.0, -d * 0.5 - 1.15, 3.92), (w + 0.8, 2.35, 0.14), "roof_tin_red", bevel=0.02, rot_euler=(0.18, 0.0, 0.0))
    for px in (-w * 0.45, -w * 0.15, w * 0.15, w * 0.45):
        mb.cylinder((px, -d * 0.5 - 1.95, 2.15), 0.08, 3.45, "metal_dark", segs=8)

    # Prominent red corrugated tin roof + raised ridge clerestory monitor
    z_pk = add_kirizuma_roof(
        mb, 0.0, 0.0, 0.52 + h, w, d, 21.0, "roof_tin_red", "wood_weathered", "metal_dark", 0.82, 0.90, tile_ribs=True
    )
    mon_w, mon_d = w * 0.66, d * 0.28
    mb.box((0.0, 0.0, z_pk + 0.36), (mon_w, mon_d, 0.86), "wall_cream", bevel=0.02)
    for mx in (-mon_w * 0.28, 0.0, mon_w * 0.28):
        mb.window_unit((mx, -mon_d * 0.5, z_pk + 0.42), 2.2, 0.48, "-Y", "metal_dark", "window_glass", None, mullions=(2, 0))
    add_kirizuma_roof(
        mb, 0.0, 0.0, z_pk + 0.78, mon_w, mon_d, 18.0, "roof_tin_red", "wood_weathered", "metal_dark", 0.38, 0.42, tile_ribs=False
    )

    # Stacked blue/yellow fish boxes along loading dock
    for cx, cy, layers, mat in (
        (-w * 0.42, -d * 0.5 - 1.1, 3, "vending_blue"),
        (-w * 0.34, -d * 0.5 - 1.2, 2, "sign_yellow"),
        (w * 0.38, -d * 0.5 - 1.1, 3, "vending_blue"),
        (w * 0.44, -d * 0.5 - 1.0, 2, "wood_light"),
    ):
        for k in range(layers):
            mb.box((cx, cy, 0.82 + k * 0.43), (0.78, 0.54, 0.40), mat, bevel=0.015)

    # Prominent fish market sign board
    smb = MeshBuilder(f"sign_{spec['idx']:02d}")
    smb.box((0.0, 0.0, 0.0), (5.0, 0.12, 0.95), "sign_yellow", bevel=0.02)
    sobj = smb.to_object(f"sign_{spec['idx']:02d}", collection=col, location=_world_pt(pos, rot_z, (0.0, -d * 0.5 - 1.85, 4.45)), rot_z=rot_z)
    sobj["text"] = spec.get("shop_text", "汐見魚市場")
    objs.append(sobj)

    objs.insert(0, mb.to_object(spec["name"], collection=col, location=pos, rot_z=rot_z))
    return objs


def build_school_clock_hall(spec: dict, col, rng: random.Random) -> list:
    """2F retro Japanese coastal schoolhouse with central gable portico & big clock."""
    w, d = spec["w"], spec["d"]
    h = 6.4  # tall 2-storey wooden schoolhouse
    pos, rot_z = Vector(spec["pos"]), spec["rot_z"]
    mb = MeshBuilder(spec["name"])
    objs = []

    # Deep terraced stone plinth + main cream wooden school block
    mb.box((0.0, 0.0, -1.6), (w + 0.5, d + 0.5, 4.2), "stone", bevel=0.04)
    mb.box((0.0, 0.0, 0.52), (w + 0.6, d + 0.6, 0.16), "concrete", bevel=0.02)
    mb.box((0.0, 0.0, 0.55 + h * 0.5), (w, d, h), "wall_white", bevel=0.03, subdiv_cuts=1)
    mb.box((0.0, 0.0, 1.45), (w + 0.08, d + 0.08, 1.80), "wood_light", bevel=0.02)
    mb.box((0.0, 0.0, 3.72), (w + 0.16, d + 0.16, 0.18), "wood_dark", bevel=0.015)

    # Rhythm of tall bright classroom windows on both floors
    for wx in (-w * 0.38, -w * 0.22, w * 0.22, w * 0.38):
        for wz in (2.05, 5.15):
            mb.window_unit((wx, -d * 0.5, wz), 1.85, 1.65, "-Y", "wood_dark", "window_glass", "trim_white", mullions=(2, 1))
            mb.window_unit((wx, d * 0.5, wz), 1.85, 1.65, "+Y", "wood_dark", "window_glass", "trim_white", mullions=(2, 1))
    for face, sx in (("-X", -w * 0.5), ("+X", w * 0.5)):
        for wz in (2.05, 5.15):
            mb.window_unit((sx, 0.0, wz), 2.2, 1.55, face, "wood_dark", "window_glass", "trim_white", mullions=(2, 1))

    # Main roof (terracotta or navy blue — very legible in overview)
    roof_mat = spec.get("roof", "roof_terracotta")
    z_pk = add_kirizuma_roof(mb, 0.0, 0.0, 0.55 + h, w, d, 26.0, roof_mat, "wall_white", "wood_dark", 0.78, 0.85, tile_ribs=True)

    # Central protruding clock gable portico + entrance steps
    pw, pd = 4.6, 2.2
    mb.box((0.0, -d * 0.5 - pd * 0.45, 0.55 + (h + 0.8) * 0.5), (pw, pd, h + 0.8), "wall_cream", bevel=0.03)
    mb.door_unit((0.0, -d * 0.5 - pd * 0.95, 0.58), 2.2, 2.35, "-Y", "wood_dark", "door_wood", "window_glass", sliding=True)
    for s in range(3):
        mb.box((0.0, -d * 0.5 - pd - 0.35 - s * 0.40, 0.42 - s * 0.16), (3.2, 0.44, 0.28), "stone", bevel=0.015)
    add_kirizuma_roof(
        mb, 0.0, -d * 0.5 - pd * 0.35, 0.55 + h + 0.75, pw, pd + 0.9, 32.0, roof_mat, "wall_cream", "wood_dark",
        0.55, 0.55, ridge_along_x=False, tile_ribs=False,
    )

    # Prominent Round School Clock Face on front gable (reads clearly even from overview!)
    cy = -d * 0.5 - pd * 0.96
    cz = 0.55 + h + 0.65
    mb.cylinder((0.0, cy - 0.06, cz), 0.92, 0.16, "metal_dark", segs=16, rot_euler=(math.pi * 0.5, 0.0, 0.0))
    mb.cylinder((0.0, cy - 0.11, cz), 0.78, 0.10, "trim_white", segs=16, rot_euler=(math.pi * 0.5, 0.0, 0.0))
    # Clock hands set to ~15:30 (summer afternoon!)
    mb.box((0.24, cy - 0.17, cz), (0.50, 0.04, 0.09), "crossing_black")
    mb.box((0.0, cy - 0.17, cz - 0.30), (0.08, 0.04, 0.62), "crossing_black")
    # Small roof cupola bell tower behind clock gable
    mb.box((0.0, 0.0, z_pk + 0.45), (1.8, 1.8, 1.15), "trim_white", bevel=0.02)
    mb.cylinder((0.0, 0.0, z_pk + 1.55), 1.45, 1.15, roof_mat, segs=4, radius_top=0.10, rot_euler=(0.0, 0.0, math.pi * 0.25))

    # School sign + flagpole
    smb = MeshBuilder(f"sign_{spec['idx']:02d}")
    smb.box((0.0, 0.0, 0.0), (2.8, 0.10, 0.65), "wall_cream", bevel=0.015)
    sobj = smb.to_object(f"sign_{spec['idx']:02d}", collection=col, location=_world_pt(pos, rot_z, (0.0, cy - 0.08, 3.65)), rot_z=rot_z)
    sobj["text"] = spec.get("shop_text", "汐見小学校")
    objs.append(sobj)

    mb.cylinder((w * 0.46, -d * 0.5 - 1.8, 4.6), 0.06, 9.2, "trim_white", segs=8)
    fmb = MeshBuilder(f"anim_flag_school_{spec['idx']:02d}")
    fmb.box((0.55, 0.0, -0.32), (1.15, 0.04, 0.72), "boat_blue", bevel=0.008, subdiv_cuts=2)
    objs.append(fmb.to_object(f"anim_flag_school_{spec['idx']:02d}", collection=col, location=_world_pt(pos, rot_z, (w * 0.46, -d * 0.5 - 1.8, 8.95)), rot_z=rot_z))

    objs.insert(0, mb.to_object(spec["name"], collection=col, location=pos, rot_z=rot_z))
    return objs


def build_water_tower(spec: dict, col, rng: random.Random) -> list:
    """Elevated municipal water tower on braced steel frame — crisp hilltop silhouette."""
    pos, rot_z = Vector(spec["pos"]), spec["rot_z"]
    mb = MeshBuilder(spec["name"])

    # Concrete foundation pad
    mb.box((0.0, 0.0, -0.9), (6.0, 6.0, 2.4), "concrete", bevel=0.04)
    # 4 splayed steel legs climbing 6.4m + cross-bracing + central riser pipe
    r_bot, r_top, h_leg = 2.35, 1.75, 6.4
    legs = []
    for k in range(4):
        a = math.radians(45.0 + k * 90.0)
        p0 = Vector((r_bot * math.cos(a), r_bot * math.sin(a), 0.2))
        p1 = Vector((r_top * math.cos(a), r_top * math.sin(a), h_leg))
        legs.append((p0, p1))
        mb.tube([p0, p1], 0.14, "metal_dark", 6)
    for k in range(4):
        a0, a1 = legs[k]
        b0, b1 = legs[(k + 1) % 4]
        am, bm = a0.lerp(a1, 0.52), b0.lerp(b1, 0.52)
        mb.tube([am, bm], 0.075, "metal_grey", 5)
        mb.tube([a0.lerp(a1, 0.12), bm], 0.055, "metal_grey", 4)
        mb.tube([b0.lerp(b1, 0.12), am], 0.055, "metal_grey", 4)
        mb.tube([am, b1], 0.055, "metal_grey", 4)
        mb.tube([bm, a1], 0.055, "metal_grey", 4)
    mb.cylinder((0.0, 0.0, h_leg * 0.5), 0.34, h_leg + 0.4, "metal_grey", segs=10)

    # Catwalk platform + safety railing ring
    mb.cylinder((0.0, 0.0, h_leg), 2.85, 0.22, "metal_dark", segs=14)
    ring_pts = [Vector((2.76 * math.cos(2 * math.pi * i / 14), 2.76 * math.sin(2 * math.pi * i / 14), h_leg + 1.0)) for i in range(15)]
    mb.tube(ring_pts, 0.04, "metal_dark", 5)
    for i in range(14):
        a = 2 * math.pi * i / 14
        mb.cylinder((2.76 * math.cos(a), 2.76 * math.sin(a), h_leg + 0.55), 0.035, 0.95, "metal_dark", segs=5)

    # Cylindrical sky-white water tank with blue marine stripe + conical roof
    mb.cylinder((0.0, 0.0, h_leg + 2.05), 2.15, 3.85, "wall_white", segs=16)
    mb.cylinder((0.0, 0.0, h_leg + 2.05), 2.19, 0.72, "boat_blue", segs=16)
    mb.cylinder((0.0, 0.0, h_leg + 4.65), 2.38, 1.45, "roof_blue", segs=16, radius_top=0.18)
    mb.cylinder((0.0, 0.0, h_leg + 5.75), 0.05, 0.95, "metal_dark", segs=6)

    return [mb.to_object(spec["name"], collection=col, location=pos, rot_z=rot_z)]


def build_yard_details(specs: list[dict], col, rng: random.Random) -> list:
    """Build 100% hillside residential walls/fences, stepping stones, planters & batched yard laundry."""
    wall_mb = MeshBuilder("garden_walls")
    laundry_mb = MeshBuilder("anim_flag_laundry_yards")
    laundry_mats = ["laundry_white", "laundry_blue", "laundry_pink", "laundry_white"]
    flower_mats = ["hydrangea_blue", "hydrangea_pink", "flower_red", "flower_yellow", "leaf_light"]

    for sp in specs:
        if sp["kind"] not in ("minka", "stucco", "cottage") or sp["pos"][1] < 18.0:
            continue
        px, py, _ = sp["pos"]
        w, d, rot = sp["w"], sp["d"], sp["rot_z"]
        ca, sa = math.cos(rot), math.sin(rot)

        def to_w(lx: float, ly: float) -> tuple[float, float, float]:
            wx = px + lx * ca - ly * sa
            wy = py + lx * sa + ly * ca
            return wx, wy, get_height(wx, wy)

        # 1. Front garden wall or wooden fence (100% of hillside residences)
        use_wood = rng.random() < 0.38
        wy_off = -(d * 0.5 + 1.45)
        is_cam04_center = (abs(px + 42.0) < 2.5 and abs(py - 52.8) < 2.5)
        if is_cam04_center:
            # Open central stone gateway aligned cleanly with the Camera 04 alley staircase!
            for sgn in (-1.0, 1.0):
                px_w, py_w, pz_w = to_w(sgn * (w * 0.36), wy_off)
                wall_mb.box((px_w, py_w, pz_w + 0.48), (w * 0.24, 0.26, 1.24), "stone", bevel=0.02, rot_euler=(0, 0, rot))
                wall_mb.box((px_w, py_w, pz_w + 1.14), (w * 0.26, 0.32, 0.10), "concrete", rot_euler=(0, 0, rot))
                gx, gy, gz = to_w(sgn * (w * 0.21), wy_off)
                wall_mb.box((gx, gy, gz + 0.60), (0.34, 0.34, 1.42), "stone", bevel=0.02, rot_euler=(0, 0, rot))
                wall_mb.box((gx, gy, gz + 1.35), (0.40, 0.40, 0.09), "concrete", rot_euler=(0, 0, rot))
        else:
            fx, fy, fz = to_w(-w * 0.14, wy_off)
            if use_wood:
                wall_mb.box((fx, fy, fz + 0.25), (w * 0.58, 0.22, 0.85), "stone", rot_euler=(0, 0, rot))
                wall_mb.box((fx, fy, fz + 0.92), (w * 0.56, 0.10, 0.72), "wood_dark", rot_euler=(0, 0, rot))
                wall_mb.box((fx, fy, fz + 1.30), (w * 0.60, 0.18, 0.08), "wood_light", rot_euler=(0, 0, rot))
            else:
                wall_mb.box((fx, fy, fz + 0.46), (w * 0.58, 0.24, 1.25), "stone", rot_euler=(0, 0, rot))
                wall_mb.box((fx, fy, fz + 1.12), (w * 0.60, 0.30, 0.10), "concrete", rot_euler=(0, 0, rot))
            # Gate post on right of entry gap
            gx, gy, gz = to_w(w * 0.35, wy_off)
            wall_mb.box((gx, gy, gz + 0.56), (0.34, 0.34, 1.36), "stone", rot_euler=(0, 0, rot))
            wall_mb.box((gx, gy, gz + 1.28), (0.40, 0.40, 0.09), "concrete", rot_euler=(0, 0, rot))

        # 2. Side boundary fence separating neighbouring plots (left or right side)
        side_sgn = -1.0 if (sp["idx"] % 2 == 0) else 1.0
        sx, sy, sz = to_w(side_sgn * (w * 0.5 + 0.75), -0.35)
        wall_mb.box((sx, sy, sz + 0.42), (0.18, d * 0.78, 1.15), "stone_dark" if not use_wood else "wood_weathered", rot_euler=(0, 0, rot))

        # 3. Stepping stones leading from gate to doorstep
        for st in range(3):
            tx, ty, tz = to_w(0.0 if is_cam04_center else w * 0.14, wy_off + 0.30 + st * 0.42)
            wall_mb.cylinder((tx, ty, tz + 0.04), 0.22, 0.10, "stone", segs=6)

        # 4. Yard planters along garden wall
        for k in range(2):
            bx, by, bz = to_w(-w * 0.32 + k * 0.78, wy_off - 0.34)
            wall_mb.box((bx, by, bz + 0.18), (0.52, 0.34, 0.38), "wood_light" if k == 0 else "roof_terracotta", rot_euler=(0, 0, rot))
            wall_mb.icosphere((bx, by, bz + 0.46), 0.22, rng.choice(flower_mats), subdivisions=1)

        # 5. Yard laundry pole + hanging clothes (on ~50% of plots, batched for 3 draw calls!)
        if rng.random() < 0.52:
            lx0, ly0, lz0 = to_w(-w * 0.34, wy_off + 0.62)
            lx1, ly1, lz1 = to_w(w * 0.08, wy_off + 0.62)
            lz_bar = max(lz0, lz1) + 1.72
            for px_p, py_p, pz_p in ((lx0, ly0, lz0), (lx1, ly1, lz1)):
                wall_mb.cylinder((px_p, py_p, pz_p + 0.90), 0.035, 1.85, "metal_grey", segs=5)
            wall_mb.tube([Vector((lx0, ly0, lz_bar)), Vector((lx1, ly1, lz_bar))], 0.025, "metal_grey", 5)
            for c in range(3):
                t = 0.20 + 0.30 * c
                cx = lx0 + (lx1 - lx0) * t
                cy = ly0 + (ly1 - ly0) * t
                ch = rng.uniform(0.55, 0.75)
                laundry_mb.box((cx, cy, lz_bar - ch * 0.5 - 0.03), (0.36, 0.04, ch), rng.choice(laundry_mats), bevel=0.008, rot_euler=(0, 0, rot))

    out = [wall_mb.to_object("garden_walls", collection=col)]
    if len(laundry_mb.bm.verts) > 0:
        out.append(laundry_mb.to_object("anim_flag_laundry_yards", collection=col))
    else:
        laundry_mb.bm.free()
    return out
