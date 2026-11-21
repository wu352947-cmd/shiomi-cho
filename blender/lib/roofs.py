"""Authentic Japanese roof builders (kirizuma, irimoya, corrugated) and
attached building details (AC units, balconies, engawa, gutters).
"""

import math
from mathutils import Matrix, Vector
from lib.geo import MeshBuilder


def _add_sloped_slab(
    mb: MeshBuilder,
    p0: Vector,
    p1: Vector,
    p2: Vector,
    p3: Vector,
    thick: float,
    mat: str,
) -> None:
    """Create a solid closed sloped slab from 4 top corners (CCW) extruded down by thick."""
    mi = mb.mat_idx(mat)
    n = (p1 - p0).cross(p3 - p0)
    if n.length < 1e-6:
        return
    n.normalize()
    if n.z < 0:
        p1, p3 = p3, p1
        n = -n
    off = Vector((0.0, 0.0, -thick))
    t = [mb.bm.verts.new(p) for p in (p0, p1, p2, p3)]
    b = [mb.bm.verts.new(p + off) for p in (p0, p1, p2, p3)]
    faces = []
    for verts in (
        (t[0], t[1], t[2], t[3]),
        (b[3], b[2], b[1], b[0]),
        (b[0], b[1], t[1], t[0]),
        (b[1], b[2], t[2], t[1]),
        (b[2], b[3], t[3], t[2]),
        (b[3], b[0], t[0], t[3]),
    ):
        try:
            faces.append(mb.bm.faces.new(verts))
        except ValueError:
            pass
    for f in faces:
        f.material_index = mi


def add_kirizuma_roof(
    mb: MeshBuilder,
    cx: float,
    cy: float,
    z_eave: float,
    width: float,
    depth: float,
    pitch: float,
    mat_roof: str,
    mat_gable: str,
    mat_trim: str = "wood_dark",
    overhang_x: float = 0.62,
    overhang_y: float = 0.68,
    ridge_along_x: bool = True,
    tile_ribs: bool = True,
    gutter_mat: str | None = "metal_dark",
) -> float:
    """Build a solid Japanese kirizuma (gable) roof with kawara tile strips,
    thick eaves, bargeboards, ridge beam, onigawara finials, and rain gutters.
    Returns peak Z height.
    """
    if not ridge_along_x:
        # Build in rotated space by creating helper transform? Simpler: support both orientations
        span_r = depth  # along Y
        span_s = width  # across X
    else:
        span_r = width  # along X
        span_s = depth  # across Y

    half_r = span_r * 0.5
    half_s = span_s * 0.5
    rise = half_s * math.tan(math.radians(pitch))
    eave_r = half_r + overhang_x
    eave_s = half_s + overhang_y
    drop = overhang_y * math.tan(math.radians(pitch))
    z_peak = z_eave + rise
    z_edge = z_eave - drop
    slab_t = 0.16

    def pt(r: float, s: float, z: float) -> Vector:
        if ridge_along_x:
            return Vector((cx + r, cy + s, z))
        return Vector((cx + s, cy + r, z))

    # Solid triangular gable infill walls (flush with building walls)
    mi_g = mb.mat_idx(mat_gable)
    for side in (-1.0, 1.0):
        r_out = side * half_r
        r_in = side * (half_r - 0.16)
        v_a0 = mb.bm.verts.new(pt(r_out, -half_s, z_eave - 0.05))
        v_b0 = mb.bm.verts.new(pt(r_out, half_s, z_eave - 0.05))
        v_c0 = mb.bm.verts.new(pt(r_out, 0.0, z_peak - 0.04))
        v_a1 = mb.bm.verts.new(pt(r_in, -half_s, z_eave - 0.05))
        v_b1 = mb.bm.verts.new(pt(r_in, half_s, z_eave - 0.05))
        v_c1 = mb.bm.verts.new(pt(r_in, 0.0, z_peak - 0.04))
        for vs in (
            (v_a0, v_b0, v_c0),
            (v_c1, v_b1, v_a1),
            (v_a0, v_a1, v_b1, v_b0),
            (v_b0, v_b1, v_c1, v_c0),
            (v_c0, v_c1, v_a1, v_a0),
        ):
            try:
                f = mb.bm.faces.new(vs)
                f.material_index = mi_g
            except ValueError:
                pass

    # Two roof slopes (solid thick slabs)
    for sgn in (-1.0, 1.0):
        p0 = pt(-eave_r, 0.0, z_peak)
        p1 = pt(eave_r, 0.0, z_peak)
        p2 = pt(eave_r, sgn * eave_s, z_edge)
        p3 = pt(-eave_r, sgn * eave_s, z_edge)
        _add_sloped_slab(mb, p0, p1, p2, p3, slab_t, mat_roof)

        # Fascia / eave trim beam
        p_e0 = pt(-eave_r, sgn * (eave_s - 0.04), z_edge - slab_t * 0.55)
        p_e1 = pt(eave_r, sgn * (eave_s - 0.04), z_edge - slab_t * 0.55)
        mb.tube([p_e0, p_e1], radius=0.055, mat=mat_trim, segs=4)

        # Rain gutter
        if gutter_mat:
            g0 = pt(-eave_r + 0.04, sgn * (eave_s + 0.06), z_edge - slab_t * 0.65)
            g1 = pt(eave_r - 0.04, sgn * (eave_s + 0.06), z_edge - slab_t * 0.65)
            mb.tube([g0, g1], radius=0.042, mat=gutter_mat, segs=6)

        # Kawara tile ridge strips running down the slope
        if tile_ribs:
            n_ribs = max(5, int((2.0 * eave_r) / 0.65))
            for i in range(n_ribs + 1):
                r_pos = -eave_r + 0.14 + (2.0 * eave_r - 0.28) * (i / max(1, n_ribs))
                q0 = pt(r_pos, sgn * 0.08, z_peak + 0.015)
                q1 = pt(r_pos, sgn * (eave_s - 0.04), z_edge + 0.025)
                mb.tube([q0, q1], radius=0.038, mat=mat_roof, segs=4)

    # Bargeboards (hafu) at both gable ends
    for side in (-1.0, 1.0):
        r_b = side * (eave_r - 0.05)
        for sgn in (-1.0, 1.0):
            mb.tube(
                [pt(r_b, 0.0, z_peak - 0.03), pt(r_b, sgn * eave_s, z_edge - 0.03)],
                radius=0.075,
                mat=mat_trim,
                segs=4,
            )

    # Prominent kawara ridge beam (mune) + onigawara end tiles
    ridge_len = 2.0 * eave_r + 0.12
    ridge_sz = (ridge_len, 0.24, 0.22) if ridge_along_x else (0.24, ridge_len, 0.22)
    mb.box((cx, cy, z_peak + 0.08), ridge_sz, mat_roof, bevel=0.03)
    for side in (-1.0, 1.0):
        pos_o = pt(side * (eave_r + 0.03), 0.0, z_peak + 0.14)
        o_sz = (0.12, 0.30, 0.32) if ridge_along_x else (0.30, 0.12, 0.32)
        mb.box(pos_o, o_sz, mat_roof, bevel=0.02)

    return z_peak + 0.22


def add_irimoya_roof(
    mb: MeshBuilder,
    cx: float,
    cy: float,
    z_eave: float,
    width: float,
    depth: float,
    pitch: float,
    mat_roof: str,
    mat_gable: str,
    mat_trim: str = "wood_dark",
    overhang: float = 0.68,
    tile_ribs: bool = True,
    gutter_mat: str | None = "metal_dark",
) -> float:
    """Build a traditional Japanese irimoya (hip-and-gable) roof.
    Lower hipped skirt on all 4 sides + recessed upper gable along X.
    Returns peak Z height.
    """
    half_x = width * 0.5
    half_y = depth * 0.5
    ex = half_x + overhang
    ey = half_y + overhang
    tan_p = math.tan(math.radians(pitch))

    # Skirt rises from outer eave inward to upper gable level
    skirt_z0 = z_eave - overhang * tan_p * 0.85
    mid_in = min(half_x * 0.42, half_y * 0.55)
    ux = max(0.8, half_x - mid_in * 0.55)
    uy = max(0.9, half_y * 0.62)
    z_mid = z_eave + (half_y - uy) * tan_p * 0.92
    z_peak = z_mid + uy * tan_p * 1.15
    slab_t = 0.16

    # Solid core ceiling cap seated strictly INSIDE the hipped skirt footprint
    mb.box(
        (cx, cy, (z_eave + z_mid) * 0.5 - 0.14),
        (max(0.5, ux * 2.0 - 0.16), max(0.5, uy * 2.0 - 0.16), max(0.2, z_mid - z_eave + 0.08)),
        mat_gable,
    )

    # 4 hipped skirt trapezoidal slabs (front -Y, back +Y, left -X, right +X)
    _add_sloped_slab(
        mb,
        Vector((cx - ux, cy - uy, z_mid)),
        Vector((cx + ux, cy - uy, z_mid)),
        Vector((cx + ex, cy - ey, skirt_z0)),
        Vector((cx - ex, cy - ey, skirt_z0)),
        slab_t,
        mat_roof,
    )
    _add_sloped_slab(
        mb,
        Vector((cx + ux, cy + uy, z_mid)),
        Vector((cx - ux, cy + uy, z_mid)),
        Vector((cx - ex, cy + ey, skirt_z0)),
        Vector((cx + ex, cy + ey, skirt_z0)),
        slab_t,
        mat_roof,
    )
    _add_sloped_slab(
        mb,
        Vector((cx - ux, cy + uy, z_mid)),
        Vector((cx - ux, cy - uy, z_mid)),
        Vector((cx - ex, cy - ey, skirt_z0)),
        Vector((cx - ex, cy + ey, skirt_z0)),
        slab_t,
        mat_roof,
    )
    _add_sloped_slab(
        mb,
        Vector((cx + ux, cy - uy, z_mid)),
        Vector((cx + ux, cy + uy, z_mid)),
        Vector((cx + ex, cy + ey, skirt_z0)),
        Vector((cx + ex, cy - ey, skirt_z0)),
        slab_t,
        mat_roof,
    )

    # 4 hip corner ridges (kudari-mune)
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            mb.tube(
                [
                    Vector((cx + sx * ux, cy + sy * uy, z_mid + 0.06)),
                    Vector((cx + sx * ex, cy + sy * ey, skirt_z0 + 0.05)),
                ],
                radius=0.075,
                mat=mat_roof,
                segs=5,
            )

    # Rain gutters around perimeter
    if gutter_mat:
        gz = skirt_z0 - slab_t * 0.65
        for sy in (-1.0, 1.0):
            mb.tube(
                [Vector((cx - ex, cy + sy * (ey + 0.06), gz)), Vector((cx + ex, cy + sy * (ey + 0.06), gz))],
                radius=0.04,
                mat=gutter_mat,
                segs=5,
            )
        for sx in (-1.0, 1.0):
            mb.tube(
                [Vector((cx + sx * (ex + 0.06), cy - ey, gz)), Vector((cx + sx * (ex + 0.06), cy + ey, gz))],
                radius=0.04,
                mat=gutter_mat,
                segs=5,
            )

    # Tile ribs on front & back skirts
    if tile_ribs:
        n_ribs = max(5, int((2.0 * ex) / 0.74))
        for sy in (-1.0, 1.0):
            for i in range(1, n_ribs):
                t = i / n_ribs
                x_top = cx - ux + 2.0 * ux * t
                x_bot = cx - ex + 2.0 * ex * t
                mb.tube(
                    [Vector((x_top, cy + sy * uy, z_mid + 0.02)), Vector((x_bot, cy + sy * ey, skirt_z0 + 0.02))],
                    radius=0.032,
                    mat=mat_roof,
                    segs=4,
                )

    # Upper gable section (kirizuma seated cleanly on top of the hipped skirt)
    add_kirizuma_roof(
        mb,
        cx=cx,
        cy=cy,
        z_eave=z_mid - 0.04,
        width=ux * 2.0,
        depth=uy * 2.0,
        pitch=pitch + 5.0,
        mat_roof=mat_roof,
        mat_gable=mat_gable,
        mat_trim=mat_trim,
        overhang_x=0.38,
        overhang_y=0.22,
        ridge_along_x=True,
        tile_ribs=tile_ribs,
        gutter_mat=None,
    )
    return z_peak + 0.25


def add_ac_unit(mb: MeshBuilder, wall_pos, facing: str) -> None:
    """Japanese outdoor AC compressor box mounted flush on wall or brackets."""
    cx, cy, cz = wall_pos
    ang = {"-Y": 0.0, "+X": math.pi * 0.5, "+Y": math.pi, "-X": -math.pi * 0.5}[facing]
    rm = Matrix.Rotation(ang, 4, "Z")

    def place(lx, ly, lz, sx, sy, sz, mat, bev=0.0):
        p = Vector((cx, cy, cz)) + (rm @ Vector((lx, ly, lz)))
        mb.box(p, (sx, sy, sz), mat, bevel=bev, rot_euler=(0.0, 0.0, ang))

    place(0.0, -0.19, 0.0, 0.72, 0.30, 0.52, "wall_white", bev=0.02)
    # Fan grille cylinder on front face
    fan_p = Vector((cx, cy, cz)) + (rm @ Vector((-0.11, -0.34, 0.0)))
    mb.cylinder(fan_p, 0.18, 0.03, "metal_dark", segs=12, rot_euler=(math.pi * 0.5, 0.0, ang))
    # Brackets & feet
    for sx in (-0.24, 0.24):
        place(sx, -0.16, -0.28, 0.06, 0.34, 0.05, "metal_grey")
    # Pipe conduit going vertically into wall
    place(0.39, -0.05, 0.35, 0.06, 0.08, 0.90, "concrete")


def add_balcony(
    mb: MeshBuilder,
    wall_center,
    width: float,
    depth: float,
    facing: str,
    mat_floor: str = "concrete",
    mat_rail: str = "metal_dark",
    mat_wall: str | None = None,
) -> None:
    """Cantilevered 2F Japanese balcony with slab, railing balusters, and handrail."""
    cx, cy, cz = wall_center
    ang = {"-Y": 0.0, "+X": math.pi * 0.5, "+Y": math.pi, "-X": -math.pi * 0.5}[facing]
    rm = Matrix.Rotation(ang, 4, "Z")

    def place(lx, ly, lz, sx, sy, sz, mat, bev=0.0):
        p = Vector((cx, cy, cz)) + (rm @ Vector((lx, ly, lz)))
        mb.box(p, (sx, sy, sz), mat, bevel=bev, rot_euler=(0.0, 0.0, ang))

    # Solid deck slab penetrating +0.12 into wall
    place(0.0, -depth * 0.5 + 0.06, -0.08, width, depth + 0.12, 0.16, mat_floor, bev=0.02)
    rh = 1.02
    if mat_wall:
        # Solid low parapet wall + top rail
        place(0.0, -depth + 0.06, rh * 0.38, width, 0.12, rh * 0.76, mat_wall, bev=0.015)
        for sx in (-1.0, 1.0):
            place(sx * (width * 0.5 - 0.06), -depth * 0.5, rh * 0.38, 0.12, depth, rh * 0.76, mat_wall, bev=0.015)
        place(0.0, -depth + 0.06, rh, width + 0.04, 0.07, 0.05, mat_rail, bev=0.01)
    else:
        # Open steel/wood railing with balusters
        place(0.0, -depth + 0.04, rh, width, 0.06, 0.05, mat_rail, bev=0.01)
        place(0.0, -depth + 0.04, 0.14, width, 0.04, 0.04, mat_rail)
        for sx in (-1.0, 1.0):
            place(sx * (width * 0.5 - 0.03), -depth * 0.5, rh, 0.06, depth, 0.05, mat_rail)
            place(sx * (width * 0.5 - 0.03), -depth + 0.04, rh * 0.5, 0.06, 0.06, rh, mat_rail)
        n_bal = max(4, int(width / 0.34))
        for i in range(n_bal + 1):
            lx = -width * 0.5 + 0.06 + (width - 0.12) * (i / n_bal)
            place(lx, -depth + 0.04, rh * 0.52, 0.026, 0.026, rh - 0.12, mat_rail)
        for sx in (-1.0, 1.0):
            for k in (0.33, 0.66):
                place(sx * (width * 0.5 - 0.03), -depth * k, rh * 0.52, 0.026, 0.026, rh - 0.12, mat_rail)
