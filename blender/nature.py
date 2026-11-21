"""Hand-crafted anime-style nature for Shiomi-cho:
- Dense overlapping forest GROVES blanketing the upper hill, shrine backdrop & east/west flanks
- Multi-lobe (3-6) lumpy clustered broadleaf trees, sakura, coastal black pines & sacred camphor
- Hedges along terrace walls, bamboo clumps, terraced vegetable plots, hydrangea & boulders
- Foliage stored in `anim_tree_zone0..4` & `anim_tree_shrubs` for web wind sway
"""

import math
import random
from mathutils import Vector
from lib.geo import MeshBuilder
from terrain import get_height, ROAD_Y, RAIL_Y, SHRINE_CENTER, SHRINE_Z
from houses import HOUSE_FOOTPRINTS


def _zone_id(x: float, y: float) -> int:
    if y < 18.0:
        return 0
    if y < 58.0:
        return 1 if x < 0.0 else 2
    if y < 112.0:
        return 3
    return 4


def _add_lumpy_puff(
    mb: MeshBuilder, center, radius: float, mat: str, scale=(1.0, 1.0, 0.80), seed_off: float = 0.0, subdiv: int = 2
) -> None:
    """Create a sculpted lumpy anime foliage puff (not a smooth sphere)."""
    verts = mb.icosphere(center, radius, mat, subdivisions=subdiv, scale=scale)
    c = Vector(center)
    for v in verts:
        d = v.co - c
        ang_n = (
            0.16 * math.sin(d.x * 2.5 + seed_off) * math.cos(d.y * 2.2 - seed_off)
            + 0.11 * math.cos(d.z * 2.9 + d.x * 1.8 + seed_off * 1.7)
        )
        v.co = c + d * (1.0 + ang_n)


def _add_broadleaf_tree(
    trunk_mb: MeshBuilder, canopy_mb: MeshBuilder, x: float, y: float, z: float,
    scale: float, mats: tuple[str, str, str], rng: random.Random, subdiv: int = 2,
) -> None:
    """Multi-lobe clustered tree (trunk + boughs + 4-6 wide overlapping lumpy canopy puffs)."""
    h_tr = rng.uniform(2.4, 3.6) * scale
    r_base = 0.30 * scale
    lean_x, lean_y = rng.uniform(-0.4, 0.4) * scale, rng.uniform(-0.4, 0.4) * scale
    p0 = Vector((x, y, z - 0.75))
    p1 = Vector((x + lean_x * 0.45, y + lean_y * 0.45, z + h_tr * 0.55))
    p2 = Vector((x + lean_x, y + lean_y, z + h_tr))
    trunk_mb.tube([p0, p1, p2], radius=r_base, mat="bark", segs=6)

    top = p2
    mat_dark, mat_mid, mat_light = mats
    n_lobes = rng.randint(4, 6)
    for k in range(n_lobes):
        a = (2.0 * math.pi * k / max(1, n_lobes - 1)) + rng.uniform(-0.45, 0.45)
        is_crown = (k == n_lobes - 1)
        dist = rng.uniform(0.0, 0.35) * scale if is_crown else rng.uniform(1.15, 2.05) * scale
        dz = rng.uniform(1.25, 1.85) * scale if is_crown else rng.uniform(0.15, 1.05) * scale
        cx, cy, cz = top.x + math.cos(a) * dist, top.y + math.sin(a) * dist, top.z + dz
        rad = rng.uniform(1.55, 2.25) * scale * (1.12 if is_crown else 0.96)
        m = mat_light if (is_crown or dz > 0.82 * scale) else (mat_dark if dz < 0.40 * scale else mat_mid)
        _add_lumpy_puff(canopy_mb, (cx, cy, cz), rad, m, scale=(1.18, 1.12, 0.78), seed_off=rng.uniform(0, 25), subdiv=subdiv)
        if k < 2 and subdiv >= 2:
            trunk_mb.tube([p1.lerp(p2, 0.72), Vector((cx, cy, cz - rad * 0.35))], radius=r_base * 0.45, mat="bark", segs=5)


def _add_coastal_pine(trunk_mb: MeshBuilder, canopy_mb: MeshBuilder, x: float, y: float, z: float, scale: float, rng: random.Random) -> None:
    """Crooked Japanese black pine (kuromatsu) with tiered cloud-like needle pads."""
    h = rng.uniform(4.2, 6.2) * scale
    ang = rng.uniform(0.0, 6.28)
    dx, dy = math.cos(ang), math.sin(ang)
    pts = [
        Vector((x, y, z - 0.65)),
        Vector((x + dx * 0.6 * scale, y + dy * 0.6 * scale, z + h * 0.35)),
        Vector((x + dx * 1.4 * scale, y + dy * 1.4 * scale, z + h * 0.70)),
        Vector((x + dx * 0.9 * scale, y + dy * 0.9 * scale, z + h)),
    ]
    trunk_mb.tube(pts, radius=0.25 * scale, mat="bark", segs=6)
    for i, (t_frac, pad_r, off_a) in enumerate(((0.56, 1.75, 0.0), (0.74, 1.90, 2.1), (0.88, 1.65, 4.2), (1.0, 1.85, 1.0))):
        bp = pts[1].lerp(pts[3], min(1.0, t_frac))
        bx = bp.x + math.cos(ang + off_a) * 1.25 * scale * (0.2 if i == 3 else 1.0)
        by = bp.y + math.sin(ang + off_a) * 1.25 * scale * (0.2 if i == 3 else 1.0)
        bz = bp.z + 0.35 * scale
        trunk_mb.tube([bp, Vector((bx, by, bz - 0.15))], radius=0.11 * scale, mat="bark", segs=5)
        m = "leaf_dark" if i < 3 else "leaf_green"
        _add_lumpy_puff(canopy_mb, (bx, by, bz), pad_r * scale, m, scale=(1.32, 1.20, 0.44), seed_off=rng.uniform(0, 20), subdiv=2)


def _add_sacred_camphor(trunk_mb: MeshBuilder, canopy_mb: MeshBuilder, rng: random.Random) -> None:
    """Monumental ancient camphor tree (kusunoki) guarding Shiomi Shrine."""
    cx, cy, cz = SHRINE_CENTER[0] - 10.2, SHRINE_CENTER[1] + 2.8, SHRINE_Z
    trunk_mb.cylinder((cx, cy, cz + 2.1), 1.35, 5.2, "bark", segs=12, radius_top=0.95)
    for k in range(6):
        a = k * math.pi / 3.0
        trunk_mb.tube(
            [Vector((cx + math.cos(a) * 1.85, cy + math.sin(a) * 1.85, cz - 0.4)), Vector((cx + math.cos(a) * 0.85, cy + math.sin(a) * 0.85, cz + 1.5))],
            radius=0.42, mat="bark", segs=6,
        )
    rope_pts = [Vector((cx + 1.18 * math.cos(2 * math.pi * k / 14), cy + 1.18 * math.sin(2 * math.pi * k / 14), cz + 2.1)) for k in range(15)]
    trunk_mb.tube(rope_pts, radius=0.12, mat="sand", segs=6)
    lobes = [
        (0.0, 0.0, 8.6, 3.4, "leaf_light"), (-2.8, -1.6, 6.6, 2.8, "leaf_green"), (2.9, -1.4, 6.8, 2.7, "leaf_light"),
        (-2.4, 2.6, 6.9, 2.9, "leaf_green"), (2.6, 2.4, 7.1, 2.7, "leaf_dark"), (0.0, -3.2, 6.1, 2.5, "leaf_dark"),
        (0.2, 3.4, 6.4, 2.6, "leaf_green"), (-3.6, 0.6, 5.8, 2.3, "leaf_dark"), (3.7, 0.4, 5.9, 2.3, "leaf_green"),
        (-1.4, -0.8, 7.8, 2.6, "leaf_light"), (1.6, 1.0, 8.0, 2.5, "leaf_light"),
    ]
    for dx, dy, dz, rad, m in lobes:
        trunk_mb.tube([Vector((cx, cy, cz + 4.0)), Vector((cx + dx * 0.72, cy + dy * 0.72, cz + dz - 0.9))], 0.30, "bark", 6)
        _add_lumpy_puff(canopy_mb, (cx + dx, cy + dy, cz + dz), rad, m, scale=(1.15, 1.10, 0.78), seed_off=rng.uniform(0, 30), subdiv=2)


def _add_bamboo_clump(trunk_mb: MeshBuilder, canopy_mb: MeshBuilder, x: float, y: float, rng: random.Random) -> None:
    """Cluster of slender Japanese moso bamboo culms with airy feathery foliage crowns."""
    n_stalks = rng.randint(7, 10)
    for k in range(n_stalks):
        ang = rng.uniform(0.0, 6.28)
        r = rng.uniform(0.2, 1.4)
        bx, by = x + math.cos(ang) * r, y + math.sin(ang) * r
        bz = get_height(bx, by)
        bh = rng.uniform(6.2, 9.4)
        lean_x, lean_y = math.cos(ang) * rng.uniform(0.5, 1.4), math.sin(ang) * rng.uniform(0.5, 1.4)
        pts = [Vector((bx, by, bz - 0.3)), Vector((bx + lean_x * 0.35, by + lean_y * 0.35, bz + bh * 0.55)), Vector((bx + lean_x, by + lean_y, bz + bh))]
        trunk_mb.tube(pts, radius=0.065, mat="leaf_green" if k % 2 == 0 else "leaf_light", segs=5)
        if k % 2 == 0:
            _add_lumpy_puff(canopy_mb, pts[-1] + Vector((0, 0, 0.35)), rng.uniform(1.1, 1.6), "leaf_light" if k % 4 == 0 else "leaf_green", scale=(1.35, 1.25, 0.52), seed_off=k * 3.1, subdiv=1)


def _add_veg_plot(trunk_mb: MeshBuilder, shrub_mb: MeshBuilder, x: float, y: float, rot: float, rng: random.Random) -> None:
    """Small terraced Japanese backyard vegetable plot with raised soil beds & leafy rows."""
    z = get_height(x, y)
    # Low timber retaining border + dark tilled earth mound
    trunk_mb.box((x, y, z - 0.08), (4.2, 2.8, 0.65), "wood_dark", bevel=0.02, rot_euler=(0, 0, rot))
    trunk_mb.box((x, y, z + 0.14), (3.8, 2.4, 0.32), "bark", bevel=0.02, rot_euler=(0, 0, rot))
    ca, sa = math.cos(rot), math.sin(rot)
    for row in (-0.68, 0.0, 0.68):
        for col_i in range(-2, 3):
            lx, ly = col_i * 0.68, row
            wx, wy = x + lx * ca - ly * sa, y + lx * sa + ly * ca
            wz = get_height(wx, wy) + 0.34
            m = "leaf_light" if (col_i + int(row * 2)) % 2 == 0 else "leaf_green"
            shrub_mb.icosphere((wx, wy, wz), 0.24, m, subdivisions=1, scale=(1.1, 1.0, 0.72))
    # 2 crossed bamboo bean-trellis poles on back edge
    for sx in (-1.1, 1.1):
        wx, wy = x + sx * ca - 0.85 * sa, y + sx * sa + 0.85 * ca
        wz = get_height(wx, wy)
        trunk_mb.cylinder((wx, wy, wz + 0.95), 0.035, 1.75, "wood_light", segs=5)


def _is_clear(x: float, y: float, pad_house: float = 0.8) -> bool:
    if y < -16.0 or y > 232.0 or abs(x) > 180.0:
        return False
    if abs(y - ROAD_Y) < 4.5 and -125.0 < x < 105.0:
        return False
    if abs(y - RAIL_Y) < 3.6:
        return False
    if -64.0 < x < 94.0 and y < 1.8:
        return False
    if math.hypot(x - SHRINE_CENTER[0], y - SHRINE_CENTER[1]) < 15.5:
        return False
    # Keep Camera 05 (-14, 120 looking toward -31, 148) sightline completely unobstructed!
    if -28.0 < x < -6.0 and 112.0 < y < 140.0:
        return False
    if 17.0 < y < 133.0:
        stair_x = 4.0 - 30.0 * ((y - 18.0) / 115.0)
        if abs(x - stair_x) < 4.5:
            return False
    # Keep Camera 04 sightline corridor clear of large tree trunks
    if -45.5 < x < -38.5 and 35.5 < y < 50.0:
        return False
    for hx, hy, hrad in HOUSE_FOOTPRINTS:
        if math.hypot(x - hx, y - hy) < hrad + pad_house:
            return False
    return True


def build_nature(col, seed: int = 4207) -> list:
    rng = random.Random(seed + 505)
    trunk_mb = MeshBuilder("nature_trunks_rocks")
    canopy_mbs = {z: MeshBuilder(f"anim_tree_zone{z}") for z in range(5)}
    shrub_mb = MeshBuilder("anim_tree_shrubs")

    # 1. Sacred Camphor Tree at hilltop shrine
    _add_sacred_camphor(trunk_mb, canopy_mbs[4], rng)

    # 2. Curated Sakura blossom trees around shrine, stairs & scenic terrace pockets
    sakura_spots = [
        (-16.5, 138.0, 1.25), (-43.5, 137.0, 1.20), (-19.0, 154.0, 1.30), (-39.0, 158.0, 1.25),
        (-28.0, 161.0, 1.32), (-15.0, 126.0, 1.10), (-34.0, 125.0, 1.08),
        (-7.5, 104.0, 1.00), (-21.0, 82.0, 1.02), (-3.5, 62.0, 1.00), (7.0, 35.5, 0.96),
        (25.5, 18.2, 0.94), (-32.0, 18.2, 0.96), (44.0, 74.0, 1.08), (-66.0, 86.0, 1.12),
    ]
    for sx, sy, sc in sakura_spots:
        if any(math.hypot(sx - hx, sy - hy) < hrad - 0.5 for hx, hy, hrad in HOUSE_FOOTPRINTS):
            continue
        _add_broadleaf_tree(trunk_mb, canopy_mbs[_zone_id(sx, sy)], sx, sy, get_height(sx, sy), sc, ("sakura_deep", "sakura", "sakura"), rng, subdiv=2)

    # 3. Coastal crooked Japanese black pines on east headland, west rocky point & coast edges
    pine_spots = [
        (104, -12, 1.12), (114, -18, 1.24), (124, -8, 1.16), (108, 6, 1.08),
        (118, 18, 1.20), (132, 12, 1.26), (142, -2, 1.16), (98, 20, 1.04),
        (128, 34, 1.20), (112, 38, 1.10), (-128, -4, 1.12), (-138, 8, 1.22),
        (-122, 16, 1.08), (-106, 18, 1.00), (-88, 10, 0.96), (-76, 10, 0.94),
    ]
    for px, py, sc in pine_spots:
        pz = get_height(px, py)
        if pz > 0.6:
            _add_coastal_pine(trunk_mb, canopy_mbs[_zone_id(px, py)], px, py, pz, sc, rng)

    # 4. DENSE OVERLAPPING FOREST GROVES (not sprinkled lollipops!)
    # Seed grove centers blanketing the entire upper ridge (y=128..232), shrine backdrop & east/west flanks
    grove_centers: list[tuple[float, float, int, float, int]] = []  # (gx, gy, count, scale_base, subdiv)
    # Upper backdrop forest crest behind town & shrine (subdiv=1 keeps tris lean while canopies overlap solidly)
    for gx in range(-162, 168, 20):
        for gy in (134, 156, 180, 204, 226):
            grove_centers.append((gx + rng.uniform(-6, 6), gy + rng.uniform(-5, 5), rng.randint(4, 5), rng.uniform(1.70, 2.30), 1))
    # East & West hillside forest flanks wrapping tightly up to town edges
    for gx in (-148, -124, -100, -82, -68, 66, 82, 102, 124, 148):
        for gy in (34, 56, 78, 102, 122):
            sd = 2 if (abs(gx) < 86 and gy < 110) else 1
            grove_centers.append((gx + rng.uniform(-5, 5), gy + rng.uniform(-5, 5), rng.randint(4, 5), rng.uniform(1.35, 1.85), sd))
    # Intimate mid-slope pocket groves tucked between town blocks
    for gx, gy in ((-64, 114), (42, 112), (58, 88), (-74, 62), (72, 46), (-88, 28)):
        grove_centers.append((gx, gy, 4, 1.22, 2))

    tree_pts: list[tuple[float, float]] = []
    for gx, gy, count, sc_base, subdiv in grove_centers:
        for _ in range(count * 3):
            if count <= 0:
                break
            ang = rng.uniform(0.0, 6.28)
            dist = rng.uniform(0.5, 9.6)
            tx, ty = gx + math.cos(ang) * dist, gy + math.sin(ang) * dist
            if not _is_clear(tx, ty, pad_house=1.0):
                continue
            min_sp = 5.2 if subdiv == 1 else 3.8
            if any(math.hypot(tx - ox, ty - oy) < min_sp for ox, oy in tree_pts):
                continue
            tz = get_height(tx, ty)
            if tz < 1.2:
                continue
            tree_pts.append((tx, ty))
            count -= 1
            sc = sc_base * rng.uniform(0.86, 1.18)
            _add_broadleaf_tree(trunk_mb, canopy_mbs[_zone_id(tx, ty)], tx, ty, tz, sc, ("leaf_dark", "leaf_green", "leaf_light"), rng, subdiv=subdiv)

    # 5. Bamboo clumps near shrine flanks & scenic mid-slope terrace corners
    bamboo_spots = [
        (-52, 134), (-48, 152), (-8, 146), (12, 132), (-68, 96),
        (56, 76), (68, 56), (-74, 48), (44, 118), (-16, 118),
    ]
    for bx, by in bamboo_spots:
        if _is_clear(bx, by, pad_house=0.2):
            _add_bamboo_clump(trunk_mb, canopy_mbs[_zone_id(bx, by)], bx, by, rng)

    # 6. Terraced vegetable plots filling remaining sunny mid-slope pockets
    veg_spots = [
        (-68, 36, 0.1), (62, 34, -0.1), (-62, 74, 0.08), (52, 68, -0.08),
        (42, 96, -0.1), (-56, 106, 0.12), (24, 108, -0.05), (-18, 36, 0.05),
        (60, 56, -0.12), (-30, 118, 0.04),
    ]
    for vx, vy, vrot in veg_spots:
        if _is_clear(vx, vy, pad_house=0.0):
            _add_veg_plot(trunk_mb, shrub_mb, vx, vy, vrot, rng)

    # 7. Dense hedges & abundant hydrangea (ajisai) along terrace walls, stairs & switchbacks
    # Shrine stairs hydrangea + hedge border
    for k in range(36):
        t = k / 35.0
        sy = 19.0 + t * 110.0
        side = -1.0 if (k % 2 == 0) else 1.0
        sx = (4.0 - 30.0 * t) + side * rng.uniform(2.3, 3.2)
        sz = get_height(sx, sy)
        _add_lumpy_puff(shrub_mb, (sx, sy, sz + 0.36), 0.78, "leaf_dark", (1.25, 1.15, 0.72), k * 1.3, subdiv=1)
        hmat = "hydrangea_blue" if (k % 3 != 0) else "hydrangea_pink"
        for b in range(3):
            ba = b * 2.1 + k
            shrub_mb.icosphere((sx + math.cos(ba) * 0.38, sy + math.sin(ba) * 0.38, sz + 0.72), 0.28, hmat, subdivisions=1)

    # Continuous hedgerows & hydrangea along terrace retaining wall tops (and Camera 04 alley edges!)
    hedge_runs = [
        (-74, -32, 17.6), (-18, -1, 17.6), (18, 76, 17.6),
        (-70, -32, 29.2), (10, 68, 29.2), (-68, -30, 40.2), (8, 64, 40.2),
        (-64, -12, 51.8), (4, 62, 51.8), (-60, -16, 63.8), (2, 58, 63.8),
        (-56, -20, 76.2), (-2, 52, 76.2), (-52, -24, 89.8), (-6, 48, 89.8),
    ]
    for x0, x1, y_wall in hedge_runs:
        x = x0 + 1.5
        while x < x1 - 1.5:
            hy = y_wall + (0.0 if y_wall < 20.0 else 2.2 * math.sin(x * 0.045 + y_wall * 0.1))
            if not any(math.hypot(x - hx, hy - hy0) < hrad - 1.0 for hx, hy0, hrad in HOUSE_FOOTPRINTS):
                hz = get_height(x, hy)
                _add_lumpy_puff(shrub_mb, (x, hy, hz + 0.42), rng.uniform(0.75, 1.05), rng.choice(["leaf_dark", "leaf_green"]), (1.45, 0.95, 0.75), x * 0.7, subdiv=1)
                if rng.random() < 0.45:
                    shrub_mb.icosphere((x, hy - 0.25, hz + 0.82), 0.30, rng.choice(["hydrangea_blue", "hydrangea_pink"]), subdivisions=1)
            x += rng.uniform(2.6, 4.4)

    # Extra hydrangea & sunflowers tucked right alongside Camera 04 stairs (-44..-40, 41..49)
    for hx, hy, hmat in ((-44.4, 42.6, "hydrangea_blue"), (-39.6, 43.2, "hydrangea_pink"), (-44.3, 46.8, "hydrangea_pink"), (-39.7, 47.4, "hydrangea_blue")):
        hz = get_height(hx, hy)
        _add_lumpy_puff(shrub_mb, (hx, hy, hz + 0.32), 0.65, "leaf_dark", (1.1, 1.0, 0.75), hx, subdiv=1)
        for b in range(3):
            shrub_mb.icosphere((hx + math.cos(b * 2.1) * 0.32, hy + math.sin(b * 2.1) * 0.32, hz + 0.66), 0.26, hmat, subdivisions=1)

    # 8. Coastal beach & headland cliff boulders
    rock_spots = [
        (-124, -14, 2.4), (-118, -11, 1.6), (-112, -16, 1.4), (-74, -8, 1.9), (-69, -12, 1.5),
        (98, -14, 2.6), (105, -22, 3.0), (112, -28, 2.5), (122, -24, 3.2), (132, -16, 2.8),
    ]
    for rx, ry, rrad in rock_spots:
        _add_lumpy_puff(trunk_mb, (rx, ry, get_height(rx, ry) - rrad * 0.18), rrad, "cliff_rock", (1.25, 1.05, 0.72), rx * 0.7, subdiv=2)

    objs = [trunk_mb.to_object("nature_trunks_rocks", collection=col, auto_smooth_deg=45.0)]
    for z, mb in canopy_mbs.items():
        if len(mb.bm.verts) > 0:
            objs.append(mb.to_object(f"anim_tree_zone{z}", collection=col, auto_smooth_deg=78.0))
        else:
            mb.bm.free()
    objs.append(shrub_mb.to_object("anim_tree_shrubs", collection=col, auto_smooth_deg=78.0))
    return objs
