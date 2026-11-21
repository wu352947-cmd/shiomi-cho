"""Deterministic topography, shoreline, terraced hillside, and stone retaining walls
for Shiomi-cho (汐見町).

All other modules query `get_height(x, y)` so buildings, roads, stairs, poles,
and trees sit accurately on the terrain with zero floating or burial.
"""

import math
import bmesh
from mathutils import Vector
from lib.geo import MeshBuilder, ensure_collection, apply_auto_smooth
from lib.materials import get_mat


def _smoothstep(e0: float, e1: float, x: float) -> float:
    if e1 == e0:
        return 1.0 if x >= e1 else 0.0
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3.0 - 2.0 * t)


def _gauss2(x: float, y: float, cx: float, cy: float, sx: float, sy: float) -> float:
    dx = (x - cx) / sx
    dy = (y - cy) / sy
    return math.exp(-0.5 * (dx * dx + dy * dy))


def _hash_noise(x: float, y: float) -> float:
    """Smooth deterministic pseudo-noise in [-1, 1] using trig harmonics."""
    return (
        0.50 * math.sin(x * 0.047 + y * 0.031)
        + 0.30 * math.cos(x * 0.089 - y * 0.067 + 1.2)
        + 0.20 * math.sin(x * 0.143 + y * 0.119 - 0.7)
    )


def _fine_noise(x: float, y: float) -> float:
    """Higher-frequency, lower-amplitude surface variation for ground blending."""
    return (
        0.45 * math.sin(x * 0.23 + y * 0.19 + 0.4)
        + 0.30 * math.cos(x * 0.41 - y * 0.37 + 2.1)
        + 0.25 * math.sin(x * 0.67 + y * 0.53 - 1.3)
    )


def _seg_dist(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
    dx, dy = bx - ax, by - ay
    l2 = dx * dx + dy * dy
    if l2 < 1e-6:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / l2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


_PATH_POLYLINES = [
    [(-25.0, 6.8), (-25.0, 23.0), (-24.0, 34.0), (-6.0, 40.0), (22.0, 44.0), (42.0, 56.0),
     (28.0, 74.0), (2.0, 82.0), (-28.0, 88.0), (-48.0, 100.0), (-42.0, 118.0), (-28.0, 128.0)],
    [(32.0, 20.0), (50.0, 32.0), (54.0, 48.0), (42.0, 56.0)],
    [(-25.0, 22.0), (-52.0, 26.0), (-64.0, 46.0), (-56.0, 70.0), (-28.0, 88.0)],
    [(4.0, 18.0), (0.0, 36.0), (-6.0, 56.0), (-12.0, 78.0), (-18.0, 102.0), (-26.0, 132.5)],
]


def _dist_to_paths(x: float, y: float) -> float:
    best = 999.0
    for poly in _PATH_POLYLINES:
        for i in range(len(poly) - 1):
            d = _seg_dist(x, y, poly[i][0], poly[i][1], poly[i + 1][0], poly[i + 1][1])
            if d < best:
                best = d
    return best


# Key geographic constants shared across modules
QUAY_Y = -5.0
QUAY_Z = 1.2
ROAD_Y = 4.0
ROAD_Z = 1.5
RAIL_Y = 13.0
RAIL_Z = 2.5
SHRINE_CENTER = (-30.0, 145.0)
SHRINE_Z = 51.5


def raw_hill_height(x: float, y: float) -> float:
    """Base un-terraced natural elevation before road/harbor/shrine flattening."""
    # Northward rise starting past y = 16
    north_rise = _smoothstep(14.0, 155.0, y)

    # Amphitheater of hills: main shrine summit (-30, 150) z~55, east & west shoulders
    h_shrine = 53.0 * _gauss2(x, y, -30.0, 152.0, 72.0, 72.0)
    h_east = 38.0 * _gauss2(x, y, 68.0, 138.0, 68.0, 62.0)
    h_far_east = 44.0 * _gauss2(x, y, 145.0, 175.0, 75.0, 85.0)
    h_west = 40.0 * _gauss2(x, y, -125.0, 145.0, 75.0, 75.0)
    h_back = 42.0 * _smoothstep(135.0, 245.0, y)

    hill = max(h_shrine, h_east, h_far_east, h_west, h_back * 0.85)
    # Blend gentle continuous hillside base so slopes are smooth everywhere
    hill = hill * 0.78 + (north_rise * 30.0) * 0.22 + 1.8 * _hash_noise(x, y) * north_rise

    # East rocky headland cliff (x = 96..180, y = -45..35) — smooth scenic bluff
    headland_mask = (
        _smoothstep(94.0, 128.0, x)
        * _smoothstep(-54.0, -14.0, y)
        * (1.0 - _smoothstep(22.0, 72.0, y))
    )
    headland = (16.5 + 2.4 * _hash_noise(x * 1.1, y * 1.1)) * headland_mask

    # West rocky point beyond sandy beach (x < -125)
    west_point = 13.0 * _smoothstep(-115.0, -158.0, x) * _smoothstep(-35.0, 15.0, y)

    # Sea floor dropping south of shoreline
    sea_drop = -10.5 * _smoothstep(2.0, -95.0, y)
    # Keep harbor basin moderately deep
    in_harbor = (
        _smoothstep(-68.0, -55.0, x)
        * (1.0 - _smoothstep(85.0, 98.0, x))
        * _smoothstep(-2.0, -10.0, y)
    )
    sea_z = sea_drop * (1.0 - 0.35 * in_harbor)

    # Combine land and sea across coastal transition
    land_mask = _smoothstep(-14.0, 18.0, y)
    z = sea_z * (1.0 - land_mask) + max(2.2, hill) * land_mask
    z = max(z, headland - 2.0) if headland_mask > 0.05 else z
    z += west_point
    return z


def get_height(x: float, y: float) -> float:
    """Final sculpted terrain height including harbor bench, road, railway,
    west beach, east cliff path, and hilltop shrine plateau.
    """
    z = raw_hill_height(x, y)

    # 1. West sandy beach (x in [-132, -64], y in [-30, 8])
    beach_x = _smoothstep(-135.0, -118.0, x) * (1.0 - _smoothstep(-74.0, -60.0, x))
    beach_y = _smoothstep(-34.0, -18.0, y) * (1.0 - _smoothstep(2.0, 12.0, y))
    beach_m = beach_x * beach_y
    if beach_m > 0.0:
        # Smooth sand slope: z=0 near y=-11, z=1.6 near y=3, z=-2.8 near y=-26
        beach_z = -0.1 + 0.145 * (y + 10.5) + 0.18 * math.sin(x * 0.12)
        z = z * (1.0 - beach_m) + beach_z * beach_m

    # 2. Harbor basin dredged seabed (x in [-62, 92], y < -5.5)
    harbor_x = _smoothstep(-66.0, -58.0, x) * (1.0 - _smoothstep(88.0, 96.0, x))
    harbor_y = _smoothstep(-4.8, -8.0, y) * (1.0 - _smoothstep(-96.0, -112.0, y))
    harbor_m = harbor_x * harbor_y
    if harbor_m > 0.0:
        basin_z = -3.8 - 2.8 * _smoothstep(-8.0, -90.0, y)
        z = z * (1.0 - harbor_m) + basin_z * harbor_m

    # 3. Harbor quay apron (x in [-62, 94], y in [-5.0, 1.5]) -> flat z = QUAY_Z
    quay_x = _smoothstep(-66.0, -59.0, x) * (1.0 - _smoothstep(91.0, 97.0, x))
    quay_y = _smoothstep(-6.2, -4.6, y) * (1.0 - _smoothstep(1.0, 2.5, y))
    quay_m = quay_x * quay_y
    if quay_m > 0.0:
        z = z * (1.0 - quay_m) + QUAY_Z * quay_m

    # 4. Coastal road bench along y = ROAD_Y (4.0), z = ROAD_Z (1.5)
    road_x = _smoothstep(-140.0, -118.0, x) * (1.0 - _smoothstep(105.0, 128.0, x))
    road_y = _smoothstep(0.6, 2.0, y) * (1.0 - _smoothstep(6.8, 9.6, y))
    road_m = road_x * road_y
    if road_m > 0.0:
        # Gentle coastal road rise at far east onto headland
        rz = ROAD_Z + 1.8 * _smoothstep(88.0, 118.0, x)
        z = z * (1.0 - road_m) + rz * road_m

    # 5. Shopping strip shelf between road and railway (y in [6.5, 11.2], x in [-68, 86])
    shop_x = _smoothstep(-74.0, -64.0, x) * (1.0 - _smoothstep(82.0, 92.0, x))
    shop_y = _smoothstep(6.2, 7.2, y) * (1.0 - _smoothstep(10.8, 12.0, y))
    shop_m = shop_x * shop_y
    if shop_m > 0.0:
        z = z * (1.0 - shop_m) + 1.65 * shop_m

    # 6. Single-track railway bench along y = RAIL_Y (13.0), z = RAIL_Z (2.5)
    rail_y = _smoothstep(10.6, 11.8, y) * (1.0 - _smoothstep(15.6, 17.6, y))
    rail_x = _smoothstep(-185.0, -155.0, x) * (1.0 - _smoothstep(155.0, 185.0, x))
    rail_m = rail_x * rail_y
    if rail_m > 0.0:
        z = z * (1.0 - rail_m) + RAIL_Z * rail_m

    # 7. Subtle town terracing on central hillside (y in [18, 128], x in [-95, 95])
    town_x = _smoothstep(-105.0, -82.0, x) * (1.0 - _smoothstep(82.0, 105.0, x))
    town_y = _smoothstep(17.0, 24.0, y) * (1.0 - _smoothstep(122.0, 136.0, y))
    town_m = town_x * town_y
    if town_m > 0.0 and z > 4.5:
        step_h = 5.5
        s = z / step_h
        sf = math.floor(s)
        frac = s - sf
        # Smooth terrace stair profile (flat middle, steeper riser)
        terraced = (sf + _smoothstep(0.18, 0.82, frac)) * step_h
        z = z * (1.0 - 0.42 * town_m) + terraced * (0.42 * town_m)

    # 8. Shrine hilltop flat plateau at (-30, 145)
    sx, sy = SHRINE_CENTER
    dist_shrine = math.hypot(x - sx, (y - sy) * 1.1)
    shrine_m = 1.0 - _smoothstep(14.5, 25.0, dist_shrine)
    if shrine_m > 0.0:
        z = z * (1.0 - shrine_m) + SHRINE_Z * shrine_m

    # 9. Gentle ramp easing right north of level crossing (x ~ -25, y in [14, 28])
    xc_m = (1.0 - _smoothstep(2.5, 8.5, abs(x + 25.0))) * _smoothstep(13.5, 16.0, y) * (1.0 - _smoothstep(24.0, 32.0, y))
    if xc_m > 0.0:
        ramp_z = RAIL_Z + 0.24 * max(0.0, y - 14.0)
        z = z * (1.0 - xc_m * 0.78) + ramp_z * (xc_m * 0.78)

    # 10. Lighthouse approach path shelf along east cliff (from (95, 4) to (96, -5))
    path_m = _smoothstep(88.0, 93.0, x) * (1.0 - _smoothstep(99.0, 105.0, x)) * _smoothstep(-8.0, -4.0, y) * (1.0 - _smoothstep(5.0, 9.0, y))
    if path_m > 0.0:
        z = z * (1.0 - path_m) + 1.55 * path_m

    return z


def _terrain_mat_index(x: float, y: float, z: float, nz: float, mat_map: dict[str, int]) -> int:
    # Underwater & beach
    if z < -0.25:
        if -140.0 <= x <= -58.0 and y > -45.0:
            return mat_map["sand"]
        return mat_map["stone_dark"]
    if -135.0 <= x <= -62.0 and -26.0 <= y <= 4.5 and z < 2.1:
        return mat_map["sand"]
    # Harbor apron concrete / stone
    if -64.0 <= x <= 94.0 and -6.0 <= y <= 2.0 and z < 1.8:
        return mat_map["concrete"]
    # East headland cliffs & steep rock faces (leave grassy crest on flat top)
    if (x > 96.0 and y < 32.0 and z > 1.8 and (nz < 0.90 or z < 11.5)) or nz < 0.72:
        return mat_map["cliff_rock"]
    if x < -122.0 and y < 25.0 and nz < 0.85:
        return mat_map["cliff_rock"]
    # Shrine plaza stone/dirt
    if math.hypot(x - SHRINE_CENTER[0], y - SHRINE_CENTER[1]) < 15.5:
        return mat_map["dirt_path"]

    # High-frequency subtle surface noise so no huge blocky patches appear
    fn = _fine_noise(x, y)
    hn = _hash_noise(x * 1.4, y * 1.4)

    # Inside dense town hillside: gravel/earth/stone mid-tones around lanes, terraces & yards
    if -80.0 <= x <= 78.0 and 15.0 <= y <= 122.0:
        d_path = _dist_to_paths(x, y)
        if d_path < 4.4 + 0.9 * fn:
            return mat_map["stone"] if (d_path < 2.1 and fn > 0.05) else mat_map["dirt_path"]
        # Terrace yard gravel/earth strips along densely built town belts
        if -72.0 <= x <= 68.0 and 18.0 <= y <= 106.0:
            terrace_mix = 0.55 * fn + 0.45 * hn
            if terrace_mix > 0.22:
                return mat_map["dirt_path"]
            if terrace_mix < -0.42:
                return mat_map["stone"]

    # Forested upper hill & outer flanks: smooth single-tone grass_dark only deep inside tree groves
    # (gentle organic feathered boundary hidden under dense forest canopy)
    forest_edge = 132.0 + 9.0 * hn + 4.5 * fn
    side_edge = 92.0 + 10.0 * hn + 4.5 * fn
    if y > forest_edge or abs(x) > side_edge or (x > 98.0 and y < 36.0 and z >= 11.5):
        return mat_map["grass_dark"]
    return mat_map["grass"]


def _warped_axis(v_min: float, v_max: float, focus_lo: float, focus_hi: float, n: int) -> list[float]:
    """Slightly denser grid spacing inside the town core without adding huge triangles."""
    pts = []
    # Piecewise density weighting integrated numerically
    weights = []
    steps = n * 4
    acc = 0.0
    for k in range(steps + 1):
        u = v_min + (v_max - v_min) * (k / steps)
        in_f = _smoothstep(focus_lo - 18.0, focus_lo, u) * (1.0 - _smoothstep(focus_hi, focus_hi + 18.0, u))
        w = 1.0 + 0.85 * in_f
        if k > 0:
            acc += w
        weights.append((u, acc))
    total = acc
    j = 0
    for i in range(n + 1):
        target = total * (i / n)
        while j < steps - 1 and weights[j + 1][1] < target:
            j += 1
        u0, w0 = weights[j]
        u1, w1 = weights[j + 1]
        frac = 0.0 if w1 <= w0 else (target - w0) / (w1 - w0)
        pts.append(u0 + (u1 - u0) * frac)
    pts[0], pts[-1] = v_min, v_max
    return pts


def build_terrain_mesh(col) -> list:
    """Create the subdivided terrain mesh + hillside stone retaining walls."""
    x_min, x_max, nx = -200.0, 200.0, 152
    y_min, y_max, ny = -120.0, 250.0, 140
    xs = _warped_axis(x_min, x_max, -85.0, 85.0, nx)
    ys = _warped_axis(y_min, y_max, 10.0, 138.0, ny)

    bm = bmesh.new()
    mat_names = ["grass", "grass_dark", "dirt_path", "sand", "cliff_rock", "concrete", "stone_dark", "stone"]
    mat_map = {m: i for i, m in enumerate(mat_names)}

    grid = []
    for iy in range(ny + 1):
        y = ys[iy]
        row = []
        for ix in range(nx + 1):
            x = xs[ix]
            z = get_height(x, y)
            row.append(bm.verts.new((x, y, z)))
        grid.append(row)

    # Create solid surface quads
    for iy in range(ny):
        for ix in range(nx):
            v00 = grid[iy][ix]
            v10 = grid[iy][ix + 1]
            v11 = grid[iy + 1][ix + 1]
            v01 = grid[iy + 1][ix]
            f = bm.faces.new((v00, v10, v11, v01))
            f.normal_update()
            cx = 0.25 * (v00.co.x + v10.co.x + v11.co.x + v01.co.x)
            cy = 0.25 * (v00.co.y + v10.co.y + v11.co.y + v01.co.y)
            cz = 0.25 * (v00.co.z + v10.co.z + v11.co.z + v01.co.z)
            f.material_index = _terrain_mat_index(cx, cy, cz, f.normal.z, mat_map)

    # Close underside skirt so terrain is a watertight solid block (z_bottom = -14.0)
    z_bot = -14.0
    b_verts = [
        bm.verts.new((x_min, y_min, z_bot)),
        bm.verts.new((x_max, y_min, z_bot)),
        bm.verts.new((x_max, y_max, z_bot)),
        bm.verts.new((x_min, y_max, z_bot)),
    ]
    mi_rock = mat_map["stone_dark"]
    # Perimeter skirts
    for ix in range(nx):
        for edge_row, b0, b1, flip in (
            (grid[0], b_verts[0], b_verts[1], False),
            (grid[ny], b_verts[3], b_verts[2], True),
        ):
            va, vb = edge_row[ix], edge_row[ix + 1]
            # Extrude straight down cleanly with simple triangles to corner skirt verts
            pass
    # Build clean perimeter walls with matching bottom ring
    bot_south = [bm.verts.new((grid[0][ix].co.x, y_min, z_bot)) for ix in range(nx + 1)]
    bot_north = [bm.verts.new((grid[ny][ix].co.x, y_max, z_bot)) for ix in range(nx + 1)]
    bot_west = [bm.verts.new((x_min, grid[iy][0].co.y, z_bot)) for iy in range(ny + 1)]
    bot_east = [bm.verts.new((x_max, grid[iy][nx].co.y, z_bot)) for iy in range(ny + 1)]
    for ix in range(nx):
        f1 = bm.faces.new((bot_south[ix], bot_south[ix + 1], grid[0][ix + 1], grid[0][ix]))
        f2 = bm.faces.new((grid[ny][ix], grid[ny][ix + 1], bot_north[ix + 1], bot_north[ix]))
        f1.material_index = f2.material_index = mi_rock
    for iy in range(ny):
        f3 = bm.faces.new((bot_west[iy + 1], bot_west[iy], grid[iy][0], grid[iy + 1][0]))
        f4 = bm.faces.new((grid[iy][nx], grid[iy + 1][nx], bot_east[iy + 1], bot_east[iy]))
        f3.material_index = f4.material_index = mi_rock
    # Remove unused corner verts & cap bottom with single quad? Use the boundary loop directly
    for bv in b_verts:
        bm.verts.remove(bv)
    bot_loop = bot_south[:-1] + bot_east[:-1] + list(reversed(bot_north[1:])) + list(reversed(bot_west[1:]))
    fb = bm.faces.new(list(reversed(bot_loop)))
    fb.material_index = mi_rock

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("terrain_main")
    bm.to_mesh(mesh)
    bm.free()
    for mn in mat_names:
        mesh.materials.append(get_mat(mn))
    apply_auto_smooth(mesh, 38.0)

    obj = bpy.data.objects.new("terrain_main", mesh)
    col.objects.link(obj)
    objs = [obj]

    # Build hillside stone retaining walls (ishigaki) along major terrace contours
    objs.append(_build_retaining_walls(col))
    return objs


def _build_retaining_walls(col):
    """Build segmented Japanese stone retaining walls (ishigaki) along hillside contours."""
    mb = MeshBuilder("terrain_retaining_walls")

    # Contour bands across the town slope + railway embankment (dense stepped Onomichi terraces)
    wall_runs = [
        # Railway stone retaining wall (south side of tracks, broken at crossing x=-25 and station x=10)
        (-85.0, -31.0, 11.4, 1.8, 0.55),
        (-19.0, 1.5, 11.4, 1.8, 0.55),
        (21.5, 86.0, 11.4, 1.8, 0.55),
        # Tier 1 lower terrace retaining wall north of railway
        (-80.0, -30.0, 16.8, 2.2, 0.65),
        (-20.0, 0.5, 16.8, 2.2, 0.65),
        (16.0, 82.0, 16.8, 2.2, 0.65),
        # Tier 1.5 terrace walls (y ~ 28.5)
        (-78.0, -29.0, 28.5, 2.3, 0.65),
        (-20.0, -2.0, 28.5, 2.3, 0.65),
        (8.0, 74.0, 28.5, 2.3, 0.65),
        # Tier 2 walls (y ~ 39.5)
        (-74.0, -29.0, 39.5, 2.5, 0.68),
        (-19.0, -5.5, 39.5, 2.4, 0.68),
        (5.5, 68.0, 39.5, 2.5, 0.68),
        # Tier 2.5 walls (y ~ 51.0)
        (-70.0, -10.0, 51.0, 2.6, 0.70),
        (1.0, 66.0, 51.0, 2.6, 0.70),
        # Tier 3 walls (y ~ 63.0)
        (-68.0, -14.0, 63.0, 2.7, 0.72),
        (-1.0, 64.0, 63.0, 2.7, 0.72),
        # Tier 3.5 walls (y ~ 75.5)
        (-64.0, -18.0, 75.5, 2.7, 0.72),
        (-4.0, 58.0, 75.5, 2.7, 0.72),
        # Tier 4 walls (y ~ 89.0)
        (-60.0, -22.0, 89.0, 2.8, 0.75),
        (-8.0, 52.0, 89.0, 2.8, 0.75),
        # Upper terrace walls below shrine (y ~ 104, 116)
        (-56.0, -24.0, 104.0, 2.8, 0.75),
        (-11.0, 44.0, 104.0, 2.8, 0.75),
        (-52.0, -28.0, 116.0, 2.6, 0.72),
        (-14.0, 32.0, 116.0, 2.6, 0.72),
    ]

    for x0, x1, y_base, h_wall, thick in wall_runs:
        n_segs = max(4, int((x1 - x0) / 7.5))
        for i in range(n_segs):
            xa = x0 + (x1 - x0) * (i / n_segs)
            xb = x0 + (x1 - x0) * ((i + 1) / n_segs)
            xm = 0.5 * (xa + xb)
            # Gentle organic contour curve for upper walls
            dy = 0.0 if y_base < 20.0 else 2.2 * math.sin(xm * 0.045 + y_base * 0.1)
            ym = y_base + dy
            zg = get_height(xm, ym)
            seg_len = (xb - xa) + 0.18
            # Main stone wall body embedded deeply into slope (never overhangs)
            mat_w = "stone" if (i % 3 != 0) else "stone_dark"
            full_h = h_wall + 1.8
            top_z = zg + h_wall * 0.68
            mb.box((xm, ym, top_z - full_h * 0.5), (seg_len, thick, full_h), mat_w, bevel=0.04, subdiv_cuts=1)
            # Concrete coping cap on top of retaining wall
            mb.box((xm, ym, top_z + 0.06), (seg_len + 0.04, thick + 0.12, 0.14), "concrete", bevel=0.02)

    # Shrine plateau semicircular stone retaining wall on south face
    sx, sy = SHRINE_CENTER
    r_shrine = 15.8
    for i in range(18):
        a = math.radians(-165.0 + i * (150.0 / 17.0))
        # Leave opening at approach stairs (around south-east / south, a ~ -85..-65 deg)
        if -88.0 < math.degrees(a) < -64.0:
            continue
        px = sx + r_shrine * math.cos(a)
        py = sy + r_shrine * math.sin(a)
        ang = a + math.pi * 0.5
        mb.box((px, py, SHRINE_Z - 1.6), (2.9, 0.9, 3.6), "stone", bevel=0.04, rot_euler=(0.0, 0.0, ang))
        mb.box((px, py, SHRINE_Z + 0.25), (3.0, 1.05, 0.18), "concrete", bevel=0.02, rot_euler=(0.0, 0.0, ang))

    return mb.to_object("terrain_retaining_walls", collection=col)


import bpy  # noqa: E402
