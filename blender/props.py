"""Japanese seaside town props for Shiomi-cho:
utility poles + transformers + sagging catenary wires, vending machines,
bicycles, red postboxes, retro street lamps, benches, convex road mirrors,
street planters, harbor crates, and sleeping/sitting cats on stone walls.
"""

import math
import random
from mathutils import Vector, Matrix
from lib.geo import MeshBuilder
from terrain import get_height, ROAD_Y, QUAY_Y, QUAY_Z


def _add_utility_pole(mb: MeshBuilder, x: float, y: float, z: float, yaw: float, has_transformer: bool) -> list[Vector]:
    """Build a detailed Japanese utility pole and return 3 wire attachment points."""
    h = 9.2
    mb.cylinder((x, y, z + 0.55), 0.22, 1.5, "concrete", segs=8)
    mb.cylinder((x, y, z + h * 0.5), 0.16, h, "pole_wood", segs=8, radius_top=0.11)
    rm = Matrix.Rotation(yaw, 4, "Z")

    # Two horizontal crossarms with ceramic insulators
    pts = []
    for arm_z, arm_w in ((h - 0.55, 1.75), (h - 1.35, 1.45)):
        mb.box((x, y, z + arm_z), (0.10, arm_w, 0.10), "metal_grey", bevel=0.01, rot_euler=(0.0, 0.0, yaw))
        # Diagonal brace struts
        for sgn in (-1.0, 1.0):
            p_a = Vector((x, y, z + arm_z - 0.48))
            p_b = Vector((x, y, z + arm_z)) + (rm @ Vector((0.0, sgn * arm_w * 0.36, 0.0)))
            mb.tube([p_a, p_b], 0.022, "metal_grey", 4)
        for sgn in (-0.44, 0.0, 0.44):
            ip = Vector((x, y, z + arm_z + 0.11)) + (rm @ Vector((0.0, sgn * arm_w, 0.0)))
            mb.cylinder(ip, 0.045, 0.14, "trim_white", segs=6)
            if arm_z > h - 0.8:
                pts.append(ip + Vector((0.0, 0.0, 0.06)))
    # Lower telecom cable bracket attachment
    tp = Vector((x, y, z + h - 2.35)) + (rm @ Vector((0.18, 0.0, 0.0)))
    mb.box(tp, (0.28, 0.14, 0.10), "metal_dark")
    pts.append(tp)

    # Pole-mounted cylindrical transformer drum
    if has_transformer:
        tr_p = Vector((x, y, z + h - 2.85)) + (rm @ Vector((-0.34, 0.0, 0.0)))
        mb.cylinder(tr_p, 0.28, 0.78, "metal_grey", segs=10)
        mb.cylinder(tr_p + Vector((0, 0, 0.42)), 0.31, 0.08, "metal_dark", segs=10)
    return pts


def _add_pole_line(mb: MeshBuilder, coords: list[tuple[float, float]], base_z_fn) -> None:
    """Place a chain of utility poles with 4 sagging catenary power & telecom wires."""
    pole_anchors: list[list[Vector]] = []
    for i, (px, py) in enumerate(coords):
        if i < len(coords) - 1:
            nx, ny = coords[i + 1]
            yaw = math.atan2(ny - py, nx - px)
        else:
            px0, py0 = coords[i - 1]
            yaw = math.atan2(py - py0, px - px0)
        pz = base_z_fn(px, py)
        pole_anchors.append(_add_utility_pole(mb, px, py, pz, yaw, has_transformer=(i % 2 == 1)))

    for i in range(len(pole_anchors) - 1):
        a0, a1 = pole_anchors[i], pole_anchors[i + 1]
        span = (a1[0] - a0[0]).length
        sag_hi = min(1.05, span * 0.036)
        sag_lo = min(1.35, span * 0.046)
        for k in range(3):
            mb.catenary(a0[k], a1[k], sag=sag_hi, radius=0.022, mat="wire_black", steps=8, segs=4)
        mb.catenary(a0[3], a1[3], sag=sag_lo, radius=0.028, mat="wire_black", steps=8, segs=4)


def _add_vending_machine(mb: MeshBuilder, lamp_mb: MeshBuilder, pos, rot_z: float, body_mat: str) -> None:
    origin = Vector(pos)
    rm = Matrix.Rotation(rot_z, 4, "Z")

    def box_l(lx, ly, lz, sx, sy, sz, mat, bev=0.015):
        mb.box(origin + (rm @ Vector((lx, ly, lz))), (sx, sy, sz), mat, bevel=bev, rot_euler=(0, 0, rot_z))

    box_l(0.0, 0.0, 0.94, 1.08, 0.72, 1.88, body_mat, 0.025)
    # Recessed illuminated drink display showcase + 3 rows of colorful cans
    box_l(0.0, -0.35, 1.32, 0.88, 0.08, 0.78, "window_glass", 0.008)
    lamp_mb.box(origin + (rm @ Vector((0.0, -0.37, 1.32))), (0.82, 0.03, 0.70), "lamp_glow", rot_euler=(0, 0, rot_z))
    for row, rz in enumerate((1.10, 1.32, 1.54)):
        for c in range(5):
            cm = ("vending_red", "vending_blue", "sign_yellow", "tram_green", "vending_white")[(row + c) % 5]
            box_l(-0.30 + c * 0.15, -0.38, rz, 0.09, 0.05, 0.13, cm, 0.004)
    # Pickup chute & coin panel
    box_l(0.0, -0.35, 0.42, 0.80, 0.08, 0.30, "metal_dark", 0.01)
    # Side plastic bottle recycling bin
    box_l(0.76, 0.02, 0.42, 0.36, 0.42, 0.84, "vending_white", 0.02)
    box_l(0.76, -0.14, 0.70, 0.22, 0.14, 0.18, "vending_blue", 0.01)


def _add_bicycle(mb: MeshBuilder, pos, rot_z: float, frame_mat: str) -> None:
    origin = Vector(pos)
    rm = Matrix.Rotation(rot_z, 4, "Z")

    def pt(lx, ly, lz):
        return origin + (rm @ Vector((lx, ly, lz)))

    # Two wheels (radius 0.33m)
    for wx in (-0.54, 0.54):
        mb.cylinder(pt(wx, 0.0, 0.34), 0.33, 0.06, "crossing_black", segs=12, rot_euler=(math.pi * 0.5, 0.0, rot_z))
        mb.cylinder(pt(wx, 0.0, 0.34), 0.25, 0.07, "metal_grey", segs=12, rot_euler=(math.pi * 0.5, 0.0, rot_z))
    # Classic Japanese mamachari frame tubes, handlebars, saddle & front basket
    mb.tube([pt(-0.54, 0.0, 0.34), pt(-0.08, 0.0, 0.78), pt(0.42, 0.0, 0.82), pt(0.54, 0.0, 0.34)], 0.024, frame_mat, 5)
    mb.tube([pt(-0.54, 0.0, 0.34), pt(-0.02, 0.0, 0.36), pt(0.42, 0.0, 0.82)], 0.022, frame_mat, 5)
    mb.tube([pt(0.42, 0.0, 0.82), pt(0.38, 0.0, 1.02)], 0.022, "metal_grey", 5)
    mb.tube([pt(0.36, -0.26, 1.02), pt(0.38, 0.0, 1.02), pt(0.36, 0.26, 1.02)], 0.020, "metal_grey", 5)
    mb.box(pt(-0.12, 0.0, 0.88), (0.24, 0.16, 0.07), "wood_dark", bevel=0.02, rot_euler=(0, 0, rot_z))
    mb.box(pt(0.56, 0.0, 0.84), (0.26, 0.32, 0.24), "metal_dark", bevel=0.015, rot_euler=(0, 0, rot_z))


def _add_cat(mb: MeshBuilder, pos, rot_z: float, coat_mat: str) -> None:
    """Cute stylized low-poly sitting cat perched on a stone wall or bollard."""
    origin = Vector(pos)
    rm = Matrix.Rotation(rot_z, 4, "Z")

    def pt(lx, ly, lz):
        return origin + (rm @ Vector((lx, ly, lz)))

    mb.icosphere(pt(0.0, 0.0, 0.16), 0.14, coat_mat, subdivisions=1, scale=(1.0, 1.25, 1.15))
    mb.icosphere(pt(0.0, -0.10, 0.33), 0.10, coat_mat, subdivisions=1)
    # Pointed little ears
    for sx in (-0.06, 0.06):
        mb.cylinder(pt(sx, -0.10, 0.42), 0.032, 0.08, coat_mat, segs=4, radius_top=0.005)
    # Curled tail
    mb.tube([pt(0.0, 0.14, 0.10), pt(0.10, 0.22, 0.18), pt(0.14, 0.16, 0.30)], 0.024, coat_mat, 5)


def build_props(col, seed: int = 4207) -> list:
    rng = random.Random(seed + 606)
    mb = MeshBuilder("props_static")
    lamp_mb = MeshBuilder("lamp_streetlights")

    # 1. Utility pole lines & sagging catenary power wires along coastal road + hillside switchback
    coastal_poles = [(-82, 6.7), (-62, 6.7), (-42, 6.7), (-22, 6.7), (-2, 6.7), (18, 6.7), (38, 6.7), (58, 6.7), (78, 6.7)]
    _add_pole_line(mb, coastal_poles, lambda x, y: get_height(x, y) - 0.1)

    hill_poles = [
        (-22, 20), (-21, 35), (-3, 41), (20, 45), (39, 57),
        (26, 74), (2, 82), (-25, 88), (-44, 100), (-39, 117),
    ]
    _add_pole_line(mb, hill_poles, lambda x, y: get_height(x, y) - 0.15)

    west_poles = [(-22, 20), (-45, 25), (-61, 44), (-54, 68), (-30, 86)]
    _add_pole_line(mb, west_poles, lambda x, y: get_height(x, y) - 0.15)

    # 2. Japanese Vending Machines along shopping street, station & hillside corners
    vm_spots = [
        (-50.0, 6.9, 0.0, "vending_red"), (-33.5, 6.9, 0.0, "vending_blue"),
        (-12.2, 6.9, 0.0, "vending_white"), (15.2, 7.2, 0.0, "vending_red"),
        (33.0, 6.9, 0.0, "vending_blue"), (50.0, 6.9, 0.0, "vending_red"),
        (-21.0, 22.0, math.radians(-18), "vending_blue"), (18.0, 46.5, math.radians(10), "vending_white"),
    ]
    for vx, vy, vrot, vmat in vm_spots:
        _add_vending_machine(mb, lamp_mb, (vx, vy, get_height(vx, vy)), vrot, vmat)

    # 3. Classic Red Japanese Postboxes (at Shiomi Station & mid-town crossing)
    for px, py in ((4.8, 6.9), (-21.5, 36.5)):
        pz = get_height(px, py)
        mb.cylinder((px, py, pz + 0.42), 0.14, 0.84, "metal_dark", segs=8)
        mb.cylinder((px, py, pz + 1.08), 0.26, 0.68, "vending_red", segs=12)
        mb.icosphere((px, py, pz + 1.42), 0.26, "vending_red", subdivisions=1, scale=(1.0, 1.0, 0.45))
        mb.box((px, py - 0.25, pz + 1.22), (0.24, 0.08, 0.09), "metal_dark")

    # 4. Parked Japanese Bicycles outside shops, station & homes
    bike_spots = [
        (-57, 6.9, 0.4, "vending_red"), (-41, 6.9, -0.3, "vending_blue"), (-18, 6.9, 0.6, "tram_green"),
        (6.4, 7.1, 1.2, "sign_yellow"), (14.0, 7.2, -0.8, "vending_white"), (25.5, 6.9, 0.2, "vending_blue"),
        (41.5, 6.9, -0.5, "vending_red"), (-30.5, 6.9, 0.3, "tram_green"), (22, 46, 0.1, "vending_blue"),
        (58.0, 6.9, -0.4, "sign_yellow"),
    ]
    for bx, by, brot, bmat in bike_spots:
        _add_bicycle(mb, (bx, by, get_height(bx, by)), brot, bmat)

    # 5. Retro Seaside Street Lamps (`lamp_streetlights`) along harbor quay, coastal road, switchbacks & stairs
    lamp_coords = [
        (-52, QUAY_Y + 1.2), (-34, QUAY_Y + 1.2), (-14, QUAY_Y + 1.2), (6, QUAY_Y + 1.2),
        (26, QUAY_Y + 1.2), (44, QUAY_Y + 1.2), (64, QUAY_Y + 1.2),
        (-70, ROAD_Y + 3.0), (-32, ROAD_Y + 3.0), (-4, ROAD_Y + 3.0), (24, ROAD_Y + 3.0), (52, ROAD_Y + 3.0),
        # Mid-slope switchback & side-lane lamps (every ~16-20m along paths)
        (-22.5, 22.0), (-22.0, 34.5), (-6.0, 41.8), (10.0, 44.2), (24.0, 45.8), (40.5, 57.5),
        (29.5, 75.0), (14.0, 80.5), (-4.0, 84.5), (-25.0, 89.5), (-46.0, 101.5), (-40.0, 118.5),
        # East & west side lanes + Camera 04 alley + shrine stairway landings
        (48.0, 33.0), (52.5, 48.0), (-50.0, 27.5), (-62.0, 47.0), (-54.0, 70.0),
        (-40.2, 41.2), (-38.6, 48.4), (1.8, 35.0), (-4.0, 56.0), (-10.0, 78.0), (-16.0, 102.0),
    ]
    for lx, ly in lamp_coords:
        lz = QUAY_Z if ly < 0.0 else get_height(lx, ly)
        mb.cylinder((lx, ly, lz + 0.35), 0.12, 0.72, "metal_dark", segs=8)
        mb.cylinder((lx, ly, lz + 2.35), 0.065, 4.1, "metal_dark", segs=8)
        # Curved goose-neck lamp arm & shade
        mb.tube([Vector((lx, ly, lz + 4.35)), Vector((lx, ly - 0.35, lz + 4.65)), Vector((lx, ly - 0.72, lz + 4.45))], 0.04, "metal_dark", 6)
        mb.cylinder((lx, ly - 0.72, lz + 4.42), 0.24, 0.12, "metal_dark", segs=10, radius_top=0.06)
        lamp_mb.icosphere((lx, ly - 0.72, lz + 4.24), 0.18, "lamp_glow", subdivisions=1)

    # 6. Harbor Promenade Wooden Benches facing the sea + Orange Convex Traffic Mirrors
    for bx in (-42.0, -18.0, 2.0, 22.0, 38.0):
        by = QUAY_Y + 1.8
        mb.box((bx, by, QUAY_Z + 0.44), (1.95, 0.52, 0.09), "wood_light", bevel=0.015)
        mb.box((bx, by + 0.22, QUAY_Z + 0.80), (1.95, 0.08, 0.40), "wood_light", bevel=0.01)
        for dx in (-0.75, 0.75):
            mb.box((bx + dx, by, QUAY_Z + 0.22), (0.09, 0.44, 0.44), "metal_dark")

    for mx, my, mrot in ((-21.8, 6.2, 0.6), (-21.5, 36.2, -0.7), (43.5, 56.5, 2.2), (-49.5, 100.5, 0.8)):
        mz = get_height(mx, my)
        mb.cylinder((mx, my, mz + 1.55), 0.045, 3.1, "crossing_yellow", segs=6)
        mb.cylinder((mx, my - 0.06, mz + 2.95), 0.36, 0.10, "torii_red", segs=12, rot_euler=(math.pi * 0.5, 0.0, mrot))
        mb.cylinder((mx, my - 0.10, mz + 2.95), 0.30, 0.05, "window_glass", segs=12, rot_euler=(math.pi * 0.5, 0.0, mrot))

    # 7. Shopping Street Flower Planter Boxes + Mid-Slope Switchback Potted Plants
    for fx in (-58, -44, -20, -4, 18, 34, 48, 62):
        fz = get_height(fx, 6.85)
        mb.box((fx, 6.85, fz + 0.24), (1.15, 0.46, 0.46), "wood_light", bevel=0.02)
        mb.icosphere((fx - 0.28, 6.85, fz + 0.58), 0.24, "leaf_green", subdivisions=1)
        mb.icosphere((fx + 0.26, 6.85, fz + 0.58), 0.24, "leaf_light", subdivisions=1)
        mb.icosphere((fx, 6.85, fz + 0.66), 0.18, rng.choice(["flower_red", "flower_yellow", "hydrangea_blue"]), subdivisions=1)

    # Charming terracotta potted plants & wooden planters lining mid-slope switchbacks & stair landings
    lane_pots = [
        (-22.8, 25.0), (-22.6, 31.5), (-14.0, 39.2), (4.0, 43.2), (18.0, 45.2), (32.0, 50.5),
        (39.8, 59.0), (33.0, 69.5), (20.0, 78.2), (6.0, 82.8), (-12.0, 86.2), (-26.0, 89.8),
        (-40.0, 96.5), (-45.8, 105.0), (-40.5, 114.0), (44.0, 29.0), (51.8, 41.0), (-44.0, 26.8),
        (-61.5, 42.0), (-58.5, 62.0), (-43.5, 41.4), (-40.5, 42.0), (-43.6, 45.2), (-40.4, 46.2),
        (-43.5, 49.0), (-40.5, 49.2),
    ]
    for px, py in lane_pots:
        pz = get_height(px, py)
        if rng.random() < 0.45:
            mb.box((px, py, pz + 0.22), (0.85, 0.38, 0.42), "wood_light", bevel=0.015)
            mb.icosphere((px - 0.20, py, pz + 0.52), 0.20, "leaf_green", subdivisions=1)
            mb.icosphere((px + 0.20, py, pz + 0.54), 0.18, rng.choice(["flower_red", "flower_yellow", "hydrangea_blue", "hydrangea_pink"]), subdivisions=1)
        else:
            mb.cylinder((px, py, pz + 0.20), 0.16, 0.36, "roof_terracotta", segs=7, radius_top=0.21)
            mb.icosphere((px, py, pz + 0.50), 0.24, rng.choice(["leaf_green", "leaf_light", "hydrangea_blue", "flower_red"]), subdivisions=1)

    # 8. Cute Low-Poly Cats lounging on quay bollards, retaining walls & stairs!
    cat_spots = [
        (-14.0, QUAY_Y + 0.48, QUAY_Z + 0.48, 0.5, "wall_white"),
        (26.0, QUAY_Y + 1.8, QUAY_Z + 0.48, -0.8, "wall_peach"),
        (-10.0, 11.4, get_height(-10.0, 11.4) + 1.32, 0.2, "wood_light"),
        (8.0, 36.0, get_height(8.0, 36.0) + 1.85, -0.4, "metal_dark"),
        (-28.0, 58.0, get_height(-28.0, 58.0) + 2.02, 0.3, "wall_white"),
        (-26.0, 134.5, get_height(-26.0, 134.5) + 0.12, -0.2, "wall_peach"),
    ]
    for cx, cy, cz, crot, cmat in cat_spots:
        _add_cat(mb, (cx, cy, cz), crot, cmat)

    return [mb.to_object("props_static", collection=col), lamp_mb.to_object("lamp_streetlights", collection=col)]
