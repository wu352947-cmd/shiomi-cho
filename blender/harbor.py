"""Harbor quay, piers, east & west curved breakwaters with tetrapods,
14m red lighthouse, white west beacon, 8 fishing boats, rowboats, and buoys.
"""

import math
import random
import bpy
from mathutils import Vector, Euler
from lib.geo import MeshBuilder
from terrain import QUAY_Y, QUAY_Z


def _quad_bezier(p0, p1, p2, t: float) -> tuple[float, float]:
    u = 1.0 - t
    x = u * u * p0[0] + 2.0 * u * t * p1[0] + t * t * p2[0]
    y = u * u * p0[1] + 2.0 * u * t * p1[1] + t * t * p2[1]
    return x, y


def _create_tetrapod_mesh(name: str = "tetrapod_proto") -> bpy.types.Mesh:
    """Build a single 4-legged coastal concrete tetrapod mesh for GPU instancing."""
    mb = MeshBuilder(name)
    # 4 legs along regular tetrahedron unit directions
    dirs = [
        Vector((0.0, 0.0, 1.0)),
        Vector((0.9428, 0.0, -0.3333)),
        Vector((-0.4714, 0.8165, -0.3333)),
        Vector((-0.4714, -0.8165, -0.3333)),
    ]
    mb.icosphere((0.0, 0.0, 0.0), 0.62, "concrete", subdivisions=1)
    for d in dirs:
        d = d.normalized()
        q = Vector((0.0, 0.0, 1.0)).rotation_difference(d)
        center = d * 0.78
        mb.cylinder(center, 0.42, 1.35, "concrete", segs=7, radius_top=0.28, rot_euler=q.to_euler("XYZ"))
    obj = mb.to_object(name, collection=None)
    mesh = obj.data
    bpy.data.objects.remove(obj)
    return mesh


def _build_quay_and_piers(mb: MeshBuilder, col) -> list:
    objs = []
    # Main concrete quay wall along y = QUAY_Y (-5) from x = -60..90
    mb.box((15.0, QUAY_Y + 3.4, (QUAY_Z - 5.2) * 0.5), (152.0, 6.8, QUAY_Z + 5.2), "concrete", bevel=0.05, subdiv_cuts=2)
    # Stone coping lip along waterfront edge
    mb.box((15.0, QUAY_Y + 0.25, QUAY_Z + 0.04), (152.0, 0.55, 0.14), "stone", bevel=0.02)
    # End return walls at east & west harbor flanks
    mb.box((-61.5, -2.5, (QUAY_Z - 4.8) * 0.5), (3.2, 9.5, QUAY_Z + 4.8), "concrete", bevel=0.04)
    mb.box((92.5, -2.5, (QUAY_Z - 4.8) * 0.5), (4.5, 9.5, QUAY_Z + 4.8), "concrete", bevel=0.04)

    # Mooring bollards & dark rubber fenders along quay front (every 6m)
    for x in range(-56, 90, 6):
        mb.cylinder((x, QUAY_Y + 0.48, QUAY_Z + 0.22), 0.16, 0.42, "metal_dark", segs=8)
        mb.cylinder((x, QUAY_Y + 0.48, QUAY_Z + 0.44), 0.22, 0.08, "metal_dark", segs=8)
        mb.box((x + 3.0, QUAY_Y - 0.12, QUAY_Z - 0.55), (0.35, 0.24, 1.05), "crossing_black", bevel=0.03)

    # Two water-access stair recesses built outward slightly on quay wall
    for sx in (-44.0, 32.0):
        for step in range(6):
            sz = QUAY_Z - 0.18 * (step + 1)
            mb.box((sx + step * 0.45, QUAY_Y - 0.48, sz - 0.45), (0.48, 0.92, 0.95), "stone", bevel=0.015)

    # 3 Piers extending south into the harbor basin
    lamp_mb = MeshBuilder("lamp_piers")
    pier_specs = [
        (-28.0, 24.0, 3.6, "wood_weathered"),
        (12.0, 29.0, 4.2, "concrete"),
        (46.0, 22.0, 3.4, "wood_weathered"),
    ]
    for px, length, width, deck_mat in pier_specs:
        y_mid = QUAY_Y - length * 0.5
        # Main deck slab
        mb.box((px, y_mid, QUAY_Z - 0.12), (width, length, 0.28), deck_mat, bevel=0.03, subdiv_cuts=1)
        # Side wooden/concrete stringer beams
        for sx in (-width * 0.5 + 0.12, width * 0.5 - 0.12):
            mb.box((px + sx, y_mid, QUAY_Z + 0.06), (0.18, length, 0.14), "wood_dark", bevel=0.01)
        # Support pilings every 4.2m down to basin seabed
        n_bents = max(3, int(length / 4.2))
        for i in range(1, n_bents + 1):
            py = QUAY_Y - i * (length / n_bents) + 0.6
            for sx in (-width * 0.40, width * 0.40):
                mb.cylinder((px + sx, py, -2.0), 0.18, 6.2, "pole_wood", segs=8)
                mb.cylinder((px + sx, py, QUAY_Z + 0.36), 0.14, 0.45, "metal_dark", segs=8)
        # Pier end bollard & warm post lamp
        tip_y = QUAY_Y - length + 0.7
        mb.cylinder((px, tip_y, QUAY_Z + 1.45), 0.07, 2.8, "metal_dark", segs=8)
        lamp_mb.icosphere((px, tip_y, QUAY_Z + 2.95), 0.20, "lamp_glow", subdivisions=1)

    objs.append(lamp_mb.to_object("lamp_piers", collection=col))
    return objs


def _build_quay_clutter(mb: MeshBuilder, rng: random.Random) -> None:
    """Populate harbor quay & piers with stacked crates, fishing nets, oil drums,
    a small yellow harbor jib crane, west davit hoist, and mooring ropes to boats.
    """
    z0 = QUAY_Z

    # 1. Small Yellow Harbor Jib Crane near Fish Market Hall (x=52.5, y=-3.7)
    cx, cy = 52.5, QUAY_Y + 1.3
    mb.box((cx, cy, z0 + 0.45), (1.9, 1.9, 0.90), "concrete", bevel=0.03)
    mb.cylinder((cx, cy, z0 + 1.45), 0.52, 1.15, "metal_dark", segs=10)
    mb.box((cx + 0.15, cy + 0.20, z0 + 2.55), (1.55, 1.75, 1.45), "sign_yellow", bevel=0.03)
    mb.window_unit((cx + 0.15, cy - 0.68, z0 + 2.68), 0.95, 0.72, "-Y", "metal_dark", "window_glass", None, mullions=(0, 0))
    # Angled crane boom reaching south-west over harbor water + tie-back stay + hook cable
    b_base = Vector((cx, cy - 0.55, z0 + 2.65))
    b_tip = Vector((cx - 1.8, cy - 5.4, z0 + 6.95))
    b_top = Vector((cx + 0.1, cy + 0.45, z0 + 4.35))
    mb.tube([b_base, b_tip], 0.16, "sign_yellow", 6)
    mb.tube([b_top, b_tip], 0.045, "metal_dark", 5)
    mb.tube([b_tip, Vector((b_tip.x, b_tip.y, z0 + 2.4))], 0.03, "metal_dark", 5)
    mb.box((b_tip.x, b_tip.y, z0 + 2.25), (0.34, 0.24, 0.36), "crossing_black", bevel=0.02)

    # Secondary compact blue davit hoist near west quay sheds (-33.5, -3.7)
    dx, dy = -33.5, QUAY_Y + 1.25
    mb.cylinder((dx, dy, z0 + 1.4), 0.16, 2.8, "boat_blue", segs=8)
    mb.tube([Vector((dx, dy, z0 + 2.65)), Vector((dx + 0.4, dy - 2.4, z0 + 3.85))], 0.11, "boat_blue", 6)
    mb.tube([Vector((dx + 0.4, dy - 2.4, z0 + 3.85)), Vector((dx + 0.4, dy - 2.4, z0 + 1.4))], 0.025, "metal_dark", 4)

    # 2. Stacked colorful fishing crates along quay & pier aprons (low-poly boxes)
    crate_clusters = [
        (-54.5, -3.5), (-43.5, -3.4), (-32.0, -3.2), (-23.0, -3.5), (-11.0, -3.3),
        (-2.0, -3.6), (7.5, -3.4), (17.5, -3.5), (27.5, -3.4), (39.5, -3.3),
        (48.5, -3.5), (56.5, -3.6), (72.5, -3.5), (84.0, -3.4),
        (-28.0, -10.0), (12.0, -12.0), (46.0, -11.0),
    ]
    crate_mats = ["vending_blue", "sign_yellow", "wood_light", "vending_white", "boat_red"]
    for idx_c, (qx, qy) in enumerate(crate_clusters):
        # Wooden shipping pallet + 3–6 stacked crates
        mb.box((qx, qy, z0 + 0.07), (1.75, 1.15, 0.14), "wood_weathered")
        n_cols = 2
        for c in range(n_cols):
            h_stack = 2 + ((idx_c + c) % 2)
            cm = crate_mats[(idx_c + c * 2) % len(crate_mats)]
            for lv in range(h_stack):
                yaw = rng.uniform(-0.14, 0.14)
                mb.box((qx - 0.42 + c * 0.84, qy + rng.uniform(-0.08, 0.08), z0 + 0.34 + lv * 0.40), (0.74, 0.54, 0.38), cm, bevel=0.012, rot_euler=(0, 0, yaw))

    # 3. Oil drum clusters (200L fuel drums near warehouses & pier entrances)
    drum_groups = [(-44.5, -1.6), (-25.5, -2.2), (15.5, -2.0), (30.5, -2.2), (50.0, -1.8), (74.5, -2.2)]
    drum_mats = ["boat_blue", "boat_red", "metal_dark", "sign_yellow"]
    for gi, (ox, oy) in enumerate(drum_groups):
        for k, (ddx, ddy) in enumerate(((0.0, 0.0), (0.64, 0.10), (0.30, -0.58), (-0.56, -0.45))):
            if k == 3 and gi % 2 == 0:
                continue
            dm = drum_mats[(gi + k) % len(drum_mats)]
            mb.cylinder((ox + ddx, oy + ddy, z0 + 0.46), 0.28, 0.90, dm, segs=8)
            mb.cylinder((ox + ddx, oy + ddy, z0 + 0.92), 0.29, 0.04, "metal_grey", segs=8)

    # 4. Bunched / draped fishing nets with colorful cork buoys along quay & piers
    net_spots = [(-41.0, -4.1), (-16.5, -4.0), (4.5, -4.1), (21.5, -4.0), (43.0, -4.1), (60.5, -4.2), (12.8, -19.5)]
    for ni, (nx, ny) in enumerate(net_spots):
        nmat = ("noren_indigo", "leaf_dark", "wood_weathered")[ni % 3]
        mb.icosphere((nx, ny, z0 + 0.32), 0.72, nmat, subdivisions=1, scale=(1.55, 1.05, 0.56))
        mb.icosphere((nx + 0.55, ny - 0.18, z0 + 0.26), 0.54, nmat, subdivisions=1, scale=(1.3, 0.95, 0.52))
        for fl in range(3):
            mb.icosphere((nx - 0.4 + fl * 0.45, ny - 0.35 + (fl % 2) * 0.30, z0 + 0.48), 0.13, "torii_red" if fl % 2 == 0 else "sign_yellow", subdivisions=1)

    # 5. Mooring ropes (catenary hemp lines from quay/pier bollards to moored boats)
    rope_pairs = [
        (Vector((-26.2, -10.5, z0 + 0.38)), Vector((-22.8, -11.5, 0.85))),
        (Vector((-26.2, -19.0, z0 + 0.38)), Vector((-22.2, -18.5, 0.85))),
        (Vector((-29.8, -17.0, z0 + 0.38)), Vector((-33.2, -17.8, 0.85))),
        (Vector((9.9, -12.0, z0 + 0.38)), Vector((6.5, -12.2, 0.85))),
        (Vector((9.9, -20.5, z0 + 0.38)), Vector((6.0, -20.8, 0.85))),
        (Vector((14.1, -20.5, z0 + 0.38)), Vector((17.5, -20.8, 0.85))),
        (Vector((44.3, -13.5, z0 + 0.38)), Vector((40.5, -13.8, 0.85))),
        (Vector((47.7, -11.0, z0 + 0.38)), Vector((51.2, -11.2, 0.85))),
        (Vector((-52.0, QUAY_Y + 0.48, z0 + 0.32)), Vector((-52.0, -11.5, 0.38))),
    ]
    for p_a, p_b in rope_pairs:
        mb.catenary(p_a, p_b, sag=0.22, radius=0.032, mat="sand", steps=5, segs=4)
    # Coiled rope rings resting beside select bollards
    for rx in (-36.0, -12.0, 24.0, 58.0):
        c_pts = [Vector((rx + 0.32 * math.cos(2 * math.pi * k / 10), QUAY_Y + 0.85 + 0.32 * math.sin(2 * math.pi * k / 10), z0 + 0.05)) for k in range(11)]
        mb.tube(c_pts, 0.042, "sand", 4)


def _build_breakwaters_and_lighthouses(mb: MeshBuilder, col, rng: random.Random) -> list:
    objs = []
    tetra_mesh = _create_tetrapod_mesh("tetrapod_proto")

    def make_breakwater(p0, p1, p2, n_segs, width, deck_z, para_side, tetrapod_side, name_prefix):
        for i in range(n_segs):
            t0, t1 = i / n_segs, (i + 1) / n_segs
            ax, ay = _quad_bezier(p0, p1, p2, t0)
            bx, by = _quad_bezier(p0, p1, p2, t1)
            xm, ym = 0.5 * (ax + bx), 0.5 * (ay + by)
            seg_len = math.hypot(bx - ax, by - ay) + 0.55
            yaw = math.atan2(by - ay, bx - ax)
            nx_v, ny_v = -math.sin(yaw), math.cos(yaw)
            # Base rubble armor mound + concrete caisson block
            mb.box((xm, ym, -2.5), (seg_len, width + 3.2, 5.4), "stone_dark", bevel=0.12, rot_euler=(0, 0, yaw))
            mb.box((xm, ym, (deck_z - 4.5) * 0.5), (seg_len, width, deck_z + 4.5), "concrete", bevel=0.06, rot_euler=(0, 0, yaw))
            # Outer sea-side wave splash parapet wall
            px = xm + nx_v * para_side * (width * 0.5 - 0.45)
            py = ym + ny_v * para_side * (width * 0.5 - 0.45)
            mb.box((px, py, deck_z + 0.65), (seg_len, 0.85, 1.35), "concrete", bevel=0.04, rot_euler=(0, 0, yaw))
            # Instanced tetrapods clustered along the seaward slope
            if i >= 1 and i <= n_segs - 1:
                for k in range(2 if width > 4.0 else 1):
                    tx = xm + nx_v * tetrapod_side * (width * 0.5 + 1.85 + k * 1.55 + rng.uniform(-0.3, 0.3))
                    ty = ym + ny_v * tetrapod_side * (width * 0.5 + 1.85 + k * 1.55 + rng.uniform(-0.3, 0.3))
                    tz = 0.85 - k * 0.40 + rng.uniform(-0.15, 0.25)
                    tobj = bpy.data.objects.new(f"{name_prefix}_tetra_{i}_{k}", tetra_mesh)
                    tobj.location = (tx, ty, tz)
                    tobj.rotation_euler = Euler((rng.uniform(0, 6.28), rng.uniform(0, 6.28), rng.uniform(0, 6.28)))
                    sc = rng.uniform(0.95, 1.25)
                    tobj.scale = (sc, sc, sc)
                    col.objects.link(tobj)
                    objs.append(tobj)

    # East curved breakwater from (95, -5) curving to (60, -95): outer ocean side = +1.0
    make_breakwater((95.0, -5.0), (104.0, -64.0), (60.0, -95.0), 18, 5.2, 2.0, 1.0, 1.0, "east_bw")
    # West short breakwater from (-70, -10) curving to (-45, -70): outer ocean side = -1.0
    make_breakwater((-70.0, -10.0), (-74.0, -48.0), (-45.0, -70.0), 12, 4.0, 1.8, -1.0, -1.0, "west_bw")

    # 14m Red Lighthouse at tip of east breakwater (~(58, -98))
    lx, ly, lz = 58.0, -98.0, 2.0
    mb.cylinder((lx, ly, lz - 2.6), 4.6, 5.6, "concrete", segs=12)          # circular foundation pier
    mb.cylinder((lx, ly, lz + 0.8), 3.3, 1.6, "stone", segs=10)             # plinth base
    # Tapered red lighthouse shaft with classic crisp white mid band
    mb.cylinder((lx, ly, lz + 4.0), 2.55, 5.0, "lighthouse_red", segs=14, radius_top=2.10)
    mb.cylinder((lx, ly, lz + 7.5), 2.10, 2.2, "lighthouse_white", segs=14, radius_top=1.92)
    mb.cylinder((lx, ly, lz + 10.1), 1.92, 3.0, "lighthouse_red", segs=14, radius_top=1.72)
    # Flush entrance door & vertical stacked windows on shaft
    mb.door_unit((lx, ly + 2.40, lz + 1.60), 1.0, 2.0, "+Y", "metal_dark", "door_wood", None)
    for wz in (lz + 5.0, lz + 7.6, lz + 9.8):
        mb.window_unit((lx - 2.05, ly, wz), 0.62, 0.85, "-X", "trim_white", "window_glass", None, mullions=(0, 0))
    # Observation gallery deck & railings
    gz = lz + 11.75
    mb.cylinder((lx, ly, gz), 2.55, 0.35, "lighthouse_white", segs=16)
    for k in range(16):
        a = 2.0 * math.pi * k / 16
        rx, ry = lx + 2.38 * math.cos(a), ly + 2.38 * math.sin(a)
        mb.cylinder((rx, ry, gz + 0.62), 0.04, 1.05, "metal_dark", segs=5)
    ring_pts = [Vector((lx + 2.38 * math.cos(2 * math.pi * k / 20), ly + 2.38 * math.sin(2 * math.pi * k / 20), gz + 1.12)) for k in range(21)]
    mb.tube(ring_pts, radius=0.045, mat="metal_dark", segs=5)
    # Lantern room mullions + red dome roof + lightning finial (total ~14.2m above deck)
    mb.cylinder((lx, ly, gz + 2.25), 1.48, 0.35, "lighthouse_red", segs=14)
    mb.cylinder((lx, ly, gz + 2.85), 1.42, 0.90, "lighthouse_red", segs=14, radius_top=0.22)
    mb.cylinder((lx, ly, gz + 3.65), 0.06, 0.90, "metal_dark", segs=6)
    # Separate glowing lighthouse_lamp object per ART_BIBLE naming
    lh_lamp = MeshBuilder("lighthouse_lamp")
    lh_lamp.cylinder((lx, ly, gz + 1.15), 1.18, 1.85, "lamp_glow", segs=14)
    objs.append(lh_lamp.to_object("lighthouse_lamp", collection=col))

    # Small 7m White Beacon Tower on west breakwater tip (-44, -71)
    wx, wy, wz = -44.0, -71.0, 1.8
    mb.cylinder((wx, wy, wz - 2.2), 3.1, 4.8, "concrete", segs=10)
    mb.cylinder((wx, wy, wz + 2.6), 1.45, 5.2, "lighthouse_white", segs=12, radius_top=1.05)
    mb.cylinder((wx, wy, wz + 5.35), 1.42, 0.25, "lighthouse_white", segs=12)
    mb.cylinder((wx, wy, wz + 6.45), 0.92, 0.65, "lighthouse_white", segs=12, radius_top=0.18)
    wb_lamp = MeshBuilder("lamp_west_beacon")
    wb_lamp.cylinder((wx, wy, wz + 5.85), 0.68, 0.85, "lamp_glow", segs=10)
    objs.append(wb_lamp.to_object("lamp_west_beacon", collection=col))
    return objs


def _make_fishing_boat(
    name: str,
    location: tuple[float, float, float],
    rot_z: float,
    length: float,
    beam: float,
    stripe_mat: str,
    col,
    flag_idx: int,
) -> list:
    """Create a sculpted Japanese coastal fishing boat (`anim_boat_*`) and flag (`anim_flag_*`)."""
    mb = MeshBuilder(name)
    hl = length * 0.5
    hb = beam * 0.5

    # Tapered curved 2D hull profile (bow at +X, stern at -X)
    def hull_poly(scale_xy: float, bow_ext: float = 0.0):
        return [
            (-hl * scale_xy, -hb * 0.78 * scale_xy),
            (hl * 0.35 * scale_xy, -hb * scale_xy),
            (hl * 0.78 * scale_xy, -hb * 0.55 * scale_xy),
            ((hl + bow_ext) * scale_xy, 0.0),
            (hl * 0.78 * scale_xy, hb * 0.55 * scale_xy),
            (hl * 0.35 * scale_xy, hb * scale_xy),
            (-hl * scale_xy, hb * 0.78 * scale_xy),
        ]

    # Lower waterline hull (red/blue), mid white freeboard, and raised deck lip
    mb.prism(hull_poly(0.90), -0.68, 0.16, stripe_mat)
    mb.prism(hull_poly(1.00, bow_ext=0.35), 0.14, 0.82, "boat_white")
    # Raised prow gunwale & wooden working deck
    mb.prism(hull_poly(0.88), 0.76, 0.92, "wood_light")
    mb.box((hl * 0.55, 0.0, 0.96), (length * 0.28, beam * 0.58, 0.24), "boat_white", bevel=0.04)

    # Wheelhouse cabin (set aft-of-center like authentic Japanese fishing trawlers)
    cx = -hl * 0.12
    cw = length * 0.27
    cd = beam * 0.62
    ch = 1.65
    mb.box((cx, 0.0, 0.92 + ch * 0.5), (cw, cd, ch), "boat_white", bevel=0.05)
    mb.box((cx + 0.08, 0.0, 0.92 + ch + 0.08), (cw + 0.45, cd + 0.25, 0.14), stripe_mat, bevel=0.02)
    # Recessed windshield & side windows on wheelhouse
    mb.window_unit((cx + cw * 0.5, 0.0, 0.92 + ch * 0.62), cd * 0.76, 0.62, "+X", "metal_dark", "window_glass", None, mullions=(1, 0))
    for face, wy in (("-Y", -cd * 0.5), ("+Y", cd * 0.5)):
        mb.window_unit((cx, wy, 0.92 + ch * 0.62), cw * 0.65, 0.58, face, "metal_dark", "window_glass", None, mullions=(0, 0))

    # Mast, cross spar, exhaust funnel & stern fish crates
    mx = cx + cw * 0.22
    mz_top = 0.92 + ch + 2.65
    mb.cylinder((mx, 0.0, 0.92 + ch + 1.35), 0.055, 2.75, "metal_grey", segs=8)
    mb.box((mx, 0.0, mz_top - 0.55), (0.08, 1.35, 0.08), "metal_grey")
    mb.cylinder((cx - cw * 0.32, cd * 0.25, 0.92 + ch + 0.55), 0.10, 1.0, "metal_dark", segs=8)
    # Rubber fenders along hull sides + deck coolers
    for fx in (-hl * 0.5, 0.0, hl * 0.35):
        for sy in (-hb - 0.04, hb + 0.04):
            mb.cylinder((fx, sy, 0.42), 0.11, 0.42, "crossing_black", segs=8)
    mb.box((-hl * 0.62, -hb * 0.25, 1.18), (0.95, 0.65, 0.52), "vending_blue", bevel=0.02)
    mb.box((-hl * 0.62, hb * 0.26, 1.16), (0.85, 0.60, 0.48), "sign_yellow", bevel=0.02)

    boat_obj = mb.to_object(name, collection=col, location=location, rot_z=rot_z)

    # Separate animated colorful fishing flag (Tairyo-bata) near mast top
    fmb = MeshBuilder(f"anim_flag_boat_{flag_idx:02d}")
    rm = Euler((0.0, 0.0, rot_z)).to_matrix()
    flag_local = Vector((mx - 0.52, 0.0, mz_top - 0.35))
    flag_world = Vector(location) + (rm @ flag_local)
    fmat = ("boat_red", "sign_yellow", "boat_blue", "torii_red")[flag_idx % 4]
    fmb.box((0.0, 0.0, 0.0), (0.95, 0.04, 0.58), fmat, bevel=0.008, subdiv_cuts=2)
    flag_obj = fmb.to_object(f"anim_flag_boat_{flag_idx:02d}", collection=col, location=flag_world, rot_z=rot_z)
    return [boat_obj, flag_obj]


def build_harbor(col, seed: int = 4207) -> list:
    rng = random.Random(seed + 101)
    mb = MeshBuilder("harbor_static")
    objs = []
    objs.extend(_build_quay_and_piers(mb, col))
    _build_quay_clutter(mb, rng)
    objs.extend(_build_breakwaters_and_lighthouses(mb, col, rng))
    objs.append(mb.to_object("harbor_static", collection=col))

    # 8 varied Japanese fishing boats moored along piers & harbor basin
    boat_specs = [
        (-22.5, -15.0, math.radians(-85), 9.4, 2.7, "boat_blue"),
        (-33.5, -21.0, math.radians(-92), 8.0, 2.4, "boat_red"),
        (6.2, -16.5, math.radians(-88), 10.6, 3.0, "boat_blue"),
        (17.8, -24.5, math.radians(-95), 8.8, 2.6, "boat_red"),
        (40.2, -17.5, math.radians(-84), 9.8, 2.8, "boat_blue"),
        (51.5, -14.0, math.radians(-98), 7.6, 2.3, "boat_red"),
        (-6.0, -42.0, math.radians(24), 11.2, 3.1, "boat_blue"),
        (28.0, -56.0, math.radians(-148), 8.6, 2.5, "boat_red"),
    ]
    for i, (bx, by, rot, length, beam, smat) in enumerate(boat_specs, start=1):
        objs.extend(_make_fishing_boat(f"anim_boat_{i:02d}", (bx, by, 0.0), rot, length, beam, smat, col, i))

    # 3 small wooden rowboats near west quay & beach
    for i, (rx, ry, rot) in enumerate(((-52.0, -13.0, 0.3), (-57.0, -19.0, -0.4), (-82.0, -14.0, 1.1)), start=1):
        rmb = MeshBuilder(f"anim_boat_row_{i:02d}")
        pts = [(-1.7, -0.45), (0.5, -0.62), (1.85, 0.0), (0.5, 0.62), (-1.7, 0.45)]
        rmb.prism(pts, -0.22, 0.36, "wood_light")
        rmb.box((0.0, 0.0, 0.24), (0.35, 1.05, 0.06), "wood_dark")
        rmb.box((-0.9, 0.0, 0.24), (0.32, 0.88, 0.06), "wood_dark")
        objs.append(rmb.to_object(f"anim_boat_row_{i:02d}", collection=col, location=(rx, ry, 0.05), rot_z=rot))

    # 6 floating harbor buoys
    for i, (ux, uy, umat) in enumerate((
        (-16.0, -58.0, "boat_red"), (12.0, -72.0, "boat_white"), (42.0, -76.0, "boat_red"),
        (-36.0, -52.0, "sign_yellow"), (68.0, -45.0, "boat_white"), (24.0, -34.0, "boat_red"),
    ), start=1):
        bmb = MeshBuilder(f"anim_boat_buoy_{i:02d}")
        bmb.cylinder((0.0, 0.0, 0.15), 0.48, 0.95, umat, segs=10)
        bmb.cylinder((0.0, 0.0, 0.72), 0.12, 0.55, "metal_dark", segs=6)
        bmb.icosphere((0.0, 0.0, 1.04), 0.14, "sign_yellow", subdivisions=1)
        objs.append(bmb.to_object(f"anim_boat_buoy_{i:02d}", collection=col, location=(ux, uy, 0.0)))

    return objs
