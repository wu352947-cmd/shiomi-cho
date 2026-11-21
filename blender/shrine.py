"""Hilltop Shiomi Shrine (汐見神社) at (-30, 145):
two Myojin vermilion torii gates, haiden/honden sanctuary with katsuogi & chigi,
chozuya water pavilion, ema rack, 6 glowing stone lanterns, and approach plaza.
"""

import math
from mathutils import Vector, Matrix, Euler
from lib.geo import MeshBuilder
from lib.roofs import add_irimoya_roof, add_kirizuma_roof
from terrain import get_height, SHRINE_CENTER, SHRINE_Z


def _add_torii(mb: MeshBuilder, pos: tuple[float, float, float], rot_z: float, scale: float = 1.0) -> None:
    """Build a solid Myojin-style curved vermilion torii gate."""
    origin = Vector(pos)
    rm = Matrix.Rotation(rot_z, 4, "Z")

    def xform(lx, ly, lz):
        return origin + (rm @ Vector((lx * scale, ly * scale, lz * scale)))

    col_h = 4.65 * scale
    col_half_w = 1.95 * scale
    # Pillars (slightly canted inward) + black stone base shoes (nemaki)
    for sgn in (-1.0, 1.0):
        bx = sgn * col_half_w
        mb.cylinder(xform(sgn * 1.95, 0.0, 0.35), 0.30 * scale, 0.90 * scale, "stone_dark", segs=10)
        mb.cylinder(xform(sgn * 1.95, 0.0, 0.85), 0.25 * scale, 0.32 * scale, "crossing_black", segs=10)
        p0 = xform(sgn * 1.95, 0.0, 0.80)
        p1 = xform(sgn * 1.78, 0.0, 4.65)
        mb.tube([p0, p1], radius=0.20 * scale, mat="torii_red", segs=10)
        # Daiwa collar ring near top
        mb.cylinder(xform(sgn * 1.80, 0.0, 4.42), 0.24 * scale, 0.16 * scale, "crossing_black", segs=10)

    # Lower penetrating tie beam (nuki) + wedges + central tablet (gakuzuka)
    mb.box(xform(0.0, 0.0, 3.62), (5.25 * scale, 0.24 * scale, 0.30 * scale), "torii_red", bevel=0.02, rot_euler=(0.0, 0.0, rot_z))
    mb.box(xform(0.0, 0.0, 4.10), (0.55 * scale, 0.28 * scale, 0.68 * scale), "crossing_black", bevel=0.02, rot_euler=(0.0, 0.0, rot_z))
    mb.box(xform(0.0, -0.14, 4.10), (0.42 * scale, 0.05 * scale, 0.56 * scale), "sign_yellow", bevel=0.01, rot_euler=(0.0, 0.0, rot_z))

    # Gracefully curved upper lintel (kasagi + shimaki) with upturned tips
    n_pts = 11
    kasagi_pts = []
    cap_pts = []
    for i in range(n_pts):
        u = -1.0 + 2.0 * (i / (n_pts - 1))  # -1..+1
        lx = u * 3.15
        curve_z = 0.26 * (u * u * u * u) + 0.08 * (u * u)
        kasagi_pts.append(xform(lx, 0.0, 4.68 + curve_z))
        cap_pts.append(xform(lx, 0.0, 4.86 + curve_z))
    mb.tube(kasagi_pts, radius=0.22 * scale, mat="torii_red", segs=6)
    mb.tube(cap_pts, radius=0.18 * scale, mat="crossing_black", segs=6)


def _add_stone_lantern(mb: MeshBuilder, lamp_mb: MeshBuilder, pos: tuple[float, float, float], scale: float = 1.0) -> None:
    """Traditional carved Japanese stone tōrō lantern with warm glowing firebox."""
    x, y, z = pos
    mb.box((x, y, z + 0.14 * scale), (0.82 * scale, 0.82 * scale, 0.34 * scale), "stone_dark", bevel=0.03)
    mb.cylinder((x, y, z + 0.72 * scale), 0.17 * scale, 0.90 * scale, "stone", segs=8)
    mb.box((x, y, z + 1.24 * scale), (0.62 * scale, 0.62 * scale, 0.18 * scale), "stone", bevel=0.02)
    # 4 firebox corner posts + glowing paper lantern core
    for sx in (-0.20, 0.20):
        for sy in (-0.20, 0.20):
            mb.box((x + sx * scale, y + sy * scale, z + 1.54 * scale), (0.08 * scale, 0.08 * scale, 0.44 * scale), "stone")
    lamp_mb.box((x, y, z + 1.54 * scale), (0.30 * scale, 0.30 * scale, 0.36 * scale), "lamp_glow")
    # Flared stone roof cap (kasa) + lotus finial (hoju)
    mb.cylinder((x, y, z + 1.92 * scale), 0.56 * scale, 0.34 * scale, "stone", segs=6, radius_top=0.16 * scale)
    mb.icosphere((x, y, z + 2.18 * scale), 0.12 * scale, "stone_dark", subdivisions=1)


def build_shrine(col) -> list:
    sx, sy = SHRINE_CENTER
    sz = SHRINE_Z
    mb = MeshBuilder("shrine_static")
    lamp_mb = MeshBuilder("lamp_shrine_lanterns")
    objs = []

    # 1. Paved stone shrine approach walkway & plaza apron
    mb.cylinder((sx, sy + 1.0, sz - 0.16), 14.2, 0.38, "dirt_path", segs=24)
    # Central stone flagstone path (sandō) from approach to main hall
    for k in range(12):
        py = sy - 11.5 + k * 1.45
        mb.box((sx + (11 - k) * 0.14, py, sz + 0.05), (2.6, 1.28, 0.12), "stone", bevel=0.02)

    # 2. Two iconic vermilion Torii gates
    # Lower gate astride the top segment of the stone stairs
    z_lower = get_height(-22.5, 121.0)
    _add_torii(mb, (-22.5, 121.0, z_lower - 0.15), rot_z=math.radians(16.0), scale=0.95)
    # Grand main torii at entrance of shrine precinct
    _add_torii(mb, (sx + 1.5, sy - 10.8, sz - 0.05), rot_z=math.radians(8.0), scale=1.12)

    # 3. Main Shrine Hall (Haiden + elevated Honden) at (sx - 0.5, sy + 5.0)
    hx, hy, hz = sx - 0.5, sy + 5.2, sz
    w, d = 9.4, 6.4
    # Elevated stone masonry podium + front ceremonial steps
    mb.box((hx, hy, hz + 0.38), (w + 1.6, d + 1.8, 1.15), "stone", bevel=0.04)
    mb.box((hx, hy, hz + 0.98), (w + 1.8, d + 2.0, 0.14), "wood_dark", bevel=0.02)
    for st in range(5):
        mb.box((hx, hy - d * 0.5 - 1.0 - st * 0.36, hz + 0.88 - st * 0.18), (3.2, 0.40, 0.22), "wood_light", bevel=0.015)
    # Vermilion veranda railings wrapping around the podium
    for side in (-1.0, 1.0):
        mb.box((hx + side * (w * 0.5 + 0.72), hy, hz + 1.62), (0.12, d + 1.5, 0.12), "torii_red", bevel=0.01)
        for py in (-d * 0.5 - 0.6, 0.0, d * 0.5 + 0.6):
            mb.box((hx + side * (w * 0.5 + 0.72), hy + py, hz + 1.32), (0.14, 0.14, 0.70), "torii_red")
        # Front rails flanking stairs
        mb.box((hx + side * 3.15, hy - d * 0.5 - 0.82, hz + 1.62), (3.2, 0.12, 0.12), "torii_red", bevel=0.01)

    # Main hall wooden + white plaster sanctuary body
    bh = 3.55
    mb.box((hx, hy, hz + 1.02 + bh * 0.5), (w, d, bh), "wall_white", bevel=0.03, subdiv_cuts=1)
    mb.box((hx, hy, hz + 1.02 + 0.75), (w + 0.08, d + 0.08, 1.45), "wood_dark", bevel=0.02)
    # Vermilion structural columns across front facade
    for px in (-w * 0.48, -w * 0.18, w * 0.18, w * 0.48):
        mb.cylinder((hx + px, hy - d * 0.5 - 0.18, hz + 1.02 + bh * 0.5), 0.16, bh + 0.1, "torii_red", segs=10)
    # Wide central sanctuary doors + flanking lattice shoji screens
    mb.door_unit((hx, hy - d * 0.5, hz + 1.05), 2.5, 2.55, "-Y", "wood_dark", "door_wood", "shoji", sliding=True)
    for fx in (-w * 0.33, w * 0.33):
        mb.window_unit((hx + fx, hy - d * 0.5, hz + 2.65), 1.95, 1.35, "-Y", "wood_dark", "shoji", "torii_red", mullions=(3, 1))
    for face, ox in (("-X", hx - w * 0.5), ("+X", hx + w * 0.5)):
        mb.window_unit((ox, hy, hz + 2.65), 2.2, 1.25, face, "wood_dark", "shoji", "wood_dark", mullions=(3, 1))

    # Offering box (saisen-bako), hanging bell & sacred shimenawa rope
    mb.box((hx, hy - d * 0.5 - 0.65, hz + 1.48), (1.75, 0.72, 0.88), "wood_light", bevel=0.02)
    mb.icosphere((hx, hy - d * 0.5 - 0.48, hz + 3.85), 0.24, "sign_yellow", subdivisions=1)
    mb.catenary((hx - 2.1, hy - d * 0.5 - 0.30, hz + 4.15), (hx + 2.1, hy - d * 0.5 - 0.30, hz + 4.15), sag=0.22, radius=0.09, mat="sand", steps=8, segs=6)

    # Grand curved-feel irimoya sanctuary roof + decorative chigi & katsuogi ridge ornaments
    z_peak = add_irimoya_roof(mb, hx, hy, hz + 1.02 + bh, w + 0.5, d + 0.6, 28.0, "roof_charcoal", "wall_white", "torii_red", overhang=1.05)
    # Katsuogi horizontal billets along ridge + crossed chigi finials
    for kx in (-1.8, -0.9, 0.0, 0.9, 1.8):
        mb.cylinder((hx + kx, hy, z_peak + 0.16), 0.14, 1.05, "sign_yellow", segs=8, rot_euler=(math.pi * 0.5, 0.0, 0.0))
    for sx_c in (-2.55, 2.55):
        for tilt in (-0.52, 0.52):
            mb.box((hx + sx_c, hy, z_peak + 0.45), (0.14, 0.22, 1.55), "sign_yellow", bevel=0.015, rot_euler=(tilt, 0.0, 0.0))
    # Front portico porch roof (kohai) over the steps
    mb.box((hx, hy - d * 0.5 - 1.55, hz + 4.25), (4.4, 2.45, 0.18), "roof_charcoal", bevel=0.02, rot_euler=(0.30, 0.0, 0.0))
    for px in (-1.75, 1.75):
        mb.cylinder((hx + px, hy - d * 0.5 - 2.35, hz + 2.25), 0.15, 3.65, "torii_red", segs=10)

    # 4. Chozuya (water purification pavilion) at west of courtyard
    cx, cy = sx - 7.4, sy - 4.5
    mb.box((cx, cy, sz + 0.55), (1.75, 1.05, 0.92), "stone_dark", bevel=0.04)
    mb.box((cx, cy, sz + 1.00), (1.42, 0.74, 0.08), "window_glass")
    for px in (-1.35, 1.35):
        for py in (-1.05, 1.05):
            mb.cylinder((cx + px, cy + py, sz + 1.38), 0.11, 2.75, "wood_dark", segs=8)
    add_kirizuma_roof(mb, cx, cy, sz + 2.75, 2.8, 2.2, 26.0, "roof_charcoal", "wood_dark", "wood_dark", 0.45, 0.50, tile_ribs=True, gutter_mat=None)

    # 5. Ema wooden prayer-plaque rack on east of courtyard
    ex, ey = sx + 7.6, sy - 2.5
    for dx in (-1.25, 1.25):
        mb.box((ex + dx, ey, sz + 1.25), (0.12, 0.12, 2.45), "wood_dark")
    mb.box((ex, ey, sz + 2.52), (3.1, 0.82, 0.14), "roof_charcoal", bevel=0.02)
    for row_z in (1.25, 1.65, 2.05):
        mb.box((ex, ey, sz + row_z), (2.4, 0.05, 0.05), "wood_dark")
        for k in range(8):
            mb.box((ex - 1.02 + k * 0.29, ey - 0.04, sz + row_z - 0.13), (0.16, 0.03, 0.12), "wood_light")

    # 6. 6 Carved Stone Lanterns (tōrō) flanking entrance & hall
    lantern_coords = [
        (sx - 1.6, sy - 8.2, sz), (sx + 4.4, sy - 8.2, sz),
        (sx - 4.4, sy - 2.4, sz), (sx + 4.0, sy - 2.4, sz),
        (sx - 5.2, sy + 2.6, sz), (sx + 4.6, sy + 2.6, sz),
    ]
    for lp in lantern_coords:
        _add_stone_lantern(mb, lamp_mb, lp, scale=1.0)

    # 7. Pair of animated shrine banner flags (`anim_flag_shrine_*`) + wooden shrine signboard (`sign_shrine`)
    for i, bx in enumerate((sx - 3.2, sx + 5.8), start=1):
        by = sy - 10.6
        mb.cylinder((bx, by, sz + 2.15), 0.055, 4.3, "wood_dark", segs=8)
        mb.box((bx + 0.36, by, sz + 4.15), (0.78, 0.05, 0.05), "wood_dark")
        fmb = MeshBuilder(f"anim_flag_shrine_{i:02d}")
        fmb.box((0.0, 0.0, -1.05), (0.64, 0.035, 2.10), "laundry_white" if i == 1 else "torii_red", bevel=0.008, subdiv_cuts=2)
        objs.append(fmb.to_object(f"anim_flag_shrine_{i:02d}", collection=col, location=(bx + 0.36, by, sz + 4.10)))

    smb = MeshBuilder("sign_shrine")
    smb.box((0.0, 0.0, 0.0), (0.55, 0.10, 2.15), "wood_light", bevel=0.02)
    sobj = smb.to_object("sign_shrine", collection=col, location=(sx + 4.9, sy - 11.4, sz + 1.15), rot_z=math.radians(8.0))
    sobj["text"] = "汐見神社"
    objs.append(sobj)

    objs.insert(0, mb.to_object("shrine_static", collection=col))
    objs.append(lamp_mb.to_object("lamp_shrine_lanterns", collection=col))
    return objs
