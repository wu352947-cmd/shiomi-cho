"""Distant layered coastal mountain ranges (north/NE, y = 240..620)
and 2 scenic sea islands (~(-400,-600) and ~(300,-800)) plus east sea stack.
"""

import math
import bpy
import bmesh
from lib.geo import apply_auto_smooth
from lib.materials import get_mat


def _make_ridge_layer(
    name: str,
    x_min: float,
    x_max: float,
    y_center: float,
    y_depth: float,
    peaks: list[tuple[float, float, float]],
    mat_name: str,
    col,
    nx: int = 56,
    ny: int = 12,
) -> bpy.types.Object:
    """Build a watertight sculpted mountain range silhouette mesh."""
    bm = bmesh.new()
    z_base = -8.0

    def ridge_z(x: float, tx: float, ty: float) -> float:
        # Smooth organic taper along both Y depth and X ends so mountains slope gently to the sea
        profile = (math.sin(ty * math.pi) ** 1.25) * (math.sin(tx * math.pi) ** 0.65)
        h = 0.0
        for px, ph, pw in peaks:
            d = (x - px) / pw
            h += ph * math.exp(-0.5 * d * d)
        ripple = 5.0 * math.sin(x * 0.017) + 2.8 * math.cos(x * 0.037 + y_center * 0.02)
        return max(z_base, z_base + (max(10.0, h) + ripple) * profile)

    grid = []
    for iy in range(ny + 1):
        ty = iy / ny
        y = y_center - y_depth * 0.5 + y_depth * ty
        row = []
        for ix in range(nx + 1):
            tx = ix / nx
            x = x_min + (x_max - x_min) * tx
            z = z_base if (iy == 0 or iy == ny or ix == 0 or ix == nx) else ridge_z(x, tx, ty)
            row.append(bm.verts.new((x, y, z)))
        grid.append(row)

    for iy in range(ny):
        for ix in range(nx):
            bm.faces.new((grid[iy][ix], grid[iy][ix + 1], grid[iy + 1][ix + 1], grid[iy + 1][ix]))

    # Cap flat base underneath so mesh is closed
    loop = (
        grid[0][:-1]
        + [grid[iy][nx] for iy in range(ny)]
        + list(reversed(grid[ny][1:]))
        + [grid[iy][0] for iy in range(ny, 0, -1)]
    )
    bm.faces.new(list(reversed(loop)))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(get_mat(mat_name))
    apply_auto_smooth(mesh, 65.0)
    obj = bpy.data.objects.new(name, mesh)
    col.objects.link(obj)
    return obj


def _make_sea_island(
    name: str,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    height: float,
    mat_name: str,
    col,
    rings: int = 8,
    segs: int = 24,
) -> bpy.types.Object:
    """Build a smooth closed low-poly coastal island rising out of the sea."""
    bm = bmesh.new()
    z_base = -8.0
    ring_verts = []
    for r in range(rings):
        t = (r + 1) / rings  # 1/rings -> 1.0 (outer skirt)
        row = []
        for s in range(segs):
            a = 2.0 * math.pi * s / segs
            wobble = 1.0 + 0.16 * math.sin(a * 2.0 + cx * 0.01) + 0.09 * math.cos(a * 3.0 - cy * 0.01)
            px = cx + rx * t * wobble * math.cos(a)
            py = cy + ry * t * wobble * math.sin(a)
            if r == rings - 1:
                pz = z_base
            else:
                dome = math.cos(t * math.pi * 0.5) ** 1.35
                twin = 1.0 + 0.25 * math.sin(a + 0.6) * (1.0 - t)
                pz = z_base + (height - z_base) * dome * twin
            row.append(bm.verts.new((px, py, pz)))
        ring_verts.append(row)

    top_v = bm.verts.new((cx, cy, height * 1.04))
    bot_v = bm.verts.new((cx, cy, z_base))
    for s in range(segs):
        sn = (s + 1) % segs
        bm.faces.new((top_v, ring_verts[0][s], ring_verts[0][sn]))
        bm.faces.new((bot_v, ring_verts[-1][sn], ring_verts[-1][s]))
    for r in range(rings - 1):
        for s in range(segs):
            sn = (s + 1) % segs
            bm.faces.new((ring_verts[r][s], ring_verts[r + 1][s], ring_verts[r + 1][sn], ring_verts[r][sn]))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(get_mat(mat_name))
    apply_auto_smooth(mesh, 65.0)
    obj = bpy.data.objects.new(name, mesh)
    col.objects.link(obj)
    return obj


def build_background(col) -> list:
    objs = []
    # Layer 1: Closer gentle forested hills (north / NE, y ~ 345) — matte silhouettes
    objs.append(
        _make_ridge_layer(
            "bg_mountains_near",
            x_min=-440.0,
            x_max=500.0,
            y_center=355.0,
            y_depth=155.0,
            peaks=[(-310, 56, 72), (-155, 66, 68), (-15, 52, 65), (125, 72, 74), (275, 58, 70), (410, 64, 72)],
            mat_name="grass_dark",
            col=col,
        )
    )
    # Layer 2: Mid coastal ridge (y ~ 525) — matte cliff/mist silhouette (tinted sky-blue by web fog)
    objs.append(
        _make_ridge_layer(
            "bg_mountains_mid",
            x_min=-620.0,
            x_max=680.0,
            y_center=525.0,
            y_depth=185.0,
            peaks=[(-460, 86, 100), (-250, 108, 92), (-40, 92, 88), (185, 118, 98), (390, 96, 92), (560, 88, 95)],
            mat_name="cliff_rock",
            col=col,
        )
    )
    # Layer 3: Far pale sky-blue mountain silhouettes (y ~ 710)
    objs.append(
        _make_ridge_layer(
            "bg_mountains_far",
            x_min=-800.0,
            x_max=850.0,
            y_center=710.0,
            y_depth=205.0,
            peaks=[(-580, 118, 125), (-310, 138, 115), (-40, 122, 115), (245, 146, 125), (520, 132, 120), (720, 115, 115)],
            mat_name="wall_sky",
            col=col,
        )
    )

    # 2 distant scenic islands in the sea per ART_BIBLE layout contract (matte silhouettes)
    objs.append(_make_sea_island("bg_island_sw", -400.0, -600.0, 125.0, 78.0, 52.0, "wall_sky", col))
    objs.append(_make_sea_island("bg_island_se", 300.0, -800.0, 155.0, 92.0, 62.0, "wall_sky", col))
    # Small rocky coastal sea stack off east headland
    objs.append(_make_sea_island("bg_seastack_east", 148.0, -76.0, 13.0, 10.0, 11.5, "cliff_rock", col, rings=5, segs=12))
    return objs
