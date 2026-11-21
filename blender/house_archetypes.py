"""Six hand-crafted Japanese architectural archetypes for Shiomi-cho.

Every building follows ART_BIBLE Geometry Rules:
- Deep grounded stone/concrete base course (never floats on slopes)
- Structural wall articulation (wainscoting, corner posts, floor belt bands)
- Flush/intersecting window & door assemblies with recessed glass
- Kirizuma / irimoya roofs with >=0.6m overhang, tile strips, ridge, gutters
- Lived-in details: balconies, engawa, AC units, downspouts, vents, flower pots
- Separate animated cloth (noren / laundry) and `sign_*` objects with `text`
"""

import math
import random
from mathutils import Vector, Euler
from lib.geo import MeshBuilder
from lib.roofs import add_kirizuma_roof, add_irimoya_roof, add_ac_unit, add_balcony


def _world_pt(origin: Vector, rot_z: float, local: tuple[float, float, float]) -> Vector:
    return origin + (Euler((0.0, 0.0, rot_z)).to_matrix() @ Vector(local))


def _add_base_and_trim(
    mb: MeshBuilder, w: float, d: float, h: float, wall_mat: str, trim_mat: str, base_mat: str = "stone", wainscot_mat: str | None = None
) -> None:
    """Grounded plinth + main volume + corner posts + floor belt + optional 1F wainscoting."""
    # Deep solid foundation plinth from z=-3.2 to z=0.45
    mb.box((0.0, 0.0, -1.38), (w + 0.24, d + 0.24, 3.66), base_mat, bevel=0.03)
    mb.box((0.0, 0.0, 0.48), (w + 0.30, d + 0.30, 0.12), "concrete")
    # Main wall mass (beveled edges for cel highlights)
    mb.box((0.0, 0.0, 0.50 + h * 0.5), (w, d, h), wall_mat, bevel=0.03)
    # 4 structural corner posts + top frieze cornice band
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            mb.box((sx * (w * 0.5 - 0.04), sy * (d * 0.5 - 0.04), 0.50 + h * 0.5), (0.16, 0.16, h + 0.04), trim_mat)
    mb.box((0.0, 0.0, 0.50 + h - 0.09), (w + 0.14, d + 0.14, 0.14), trim_mat)
    # Optional lower wood wainscoting (1F height) or stucco belt + vertical pilasters
    if wainscot_mat:
        wh = min(2.65, h * 0.50)
        mb.box((0.0, 0.0, 0.50 + wh * 0.5), (w + 0.08, d + 0.08, wh), wainscot_mat)
        mb.box((0.0, 0.0, 0.50 + wh + 0.05), (w + 0.18, d + 0.18, 0.12), trim_mat)
        # Vertical timber battens on upper plaster facade
        for bx in (-w * 0.16, w * 0.16):
            mb.box((bx, -d * 0.5 - 0.01, 0.50 + wh + (h - wh) * 0.5), (0.10, 0.06, h - wh), trim_mat)
    elif h > 4.2:
        # Mid-floor structural belt band + subtle lower stone plinth strip
        mb.box((0.0, 0.0, 3.30), (w + 0.16, d + 0.16, 0.16), trim_mat)
        mb.box((0.0, 0.0, 0.92), (w + 0.10, d + 0.10, 0.84), "stone")


def _add_window_box(mb: MeshBuilder, cx: float, cy: float, cz: float, width: float, rng: random.Random) -> None:
    """Small wooden flower box seated beneath a front (-Y) window sill."""
    mb.box((cx, cy - 0.16, cz), (width, 0.24, 0.20), "wood_light")
    fmat = rng.choice(["flower_red", "flower_yellow", "hydrangea_blue", "hydrangea_pink"])
    for k in (-1, 0, 1):
        mb.icosphere((cx + k * (width * 0.28), cy - 0.16, cz + 0.16), 0.13, "leaf_green" if k == 0 else fmat, subdivisions=1)


def _add_downspout_and_pots(mb: MeshBuilder, w: float, d: float, h: float, rng: random.Random) -> None:
    # Vertical metal rainwater downspout on front-right corner + copper-dark rain chain on front-left
    mb.cylinder((w * 0.5 + 0.06, -d * 0.5 - 0.06, 0.4 + h * 0.5), 0.04, h + 0.3, "metal_dark", segs=5)
    rcx, rcy = -w * 0.5 - 0.10, -d * 0.5 - 0.10
    mb.cylinder((rcx, rcy, 0.50 + h * 0.5), 0.018, h, "metal_dark", segs=4)
    for cz in range(1, max(2, int(h))):
        mb.cylinder((rcx, rcy, 0.45 + cz * 0.92), 0.055, 0.10, "wood_dark", segs=5, radius_top=0.075)
    mb.cylinder((rcx, rcy, 0.32), 0.18, 0.26, "stone_dark", segs=6)
    # Small metal roof/wall vent pipe
    mb.cylinder((-w * 0.36, d * 0.5 + 0.12, 2.2), 0.065, 2.4, "metal_grey", segs=5)
    # 2 doorstep terracotta potted plants seated firmly on the plinth ledge
    for k in range(2):
        px = -w * 0.38 + k * 0.52
        py = -d * 0.5 - 0.08
        mb.box((px, py, 0.20), (0.38, 0.34, 0.72), "stone")
        mb.cylinder((px, py, 0.68), 0.13, 0.28, "roof_terracotta", segs=6, radius_top=0.17)
        fmat = rng.choice(["leaf_green", "leaf_light", "flower_red", "hydrangea_blue", "flower_yellow"])
        mb.icosphere((px, py, 0.92), 0.19, fmat, subdivisions=1)


def _add_laundry_line(
    col,
    name: str,
    origin: Vector,
    rot_z: float,
    local_pos: tuple[float, float, float],
    width: float,
    rng: random.Random,
    batch_mb: MeshBuilder | None = None,
):
    """Build animated hanging laundry pieces (batched into shared MeshBuilder when provided)."""
    mats = ["laundry_white", "laundry_blue", "laundry_pink", "laundry_white"]
    n_items = max(3, int(width / 0.62))
    if batch_mb is not None:
        for i in range(n_items):
            lx = -width * 0.42 + (width * 0.84) * (i / max(1, n_items - 1))
            ch = rng.uniform(0.55, 0.80)
            cw = rng.uniform(0.32, 0.44)
            wpos = _world_pt(origin, rot_z, (local_pos[0] + lx, local_pos[1], local_pos[2] - ch * 0.5))
            batch_mb.box(wpos, (cw, 0.04, ch), rng.choice(mats), bevel=0.008, rot_euler=(0.0, 0.0, rot_z))
        return None
    fmb = MeshBuilder(name)
    for i in range(n_items):
        lx = -width * 0.42 + (width * 0.84) * (i / max(1, n_items - 1))
        ch = rng.uniform(0.55, 0.82)
        cw = rng.uniform(0.32, 0.44)
        fmb.box((lx, 0.0, -ch * 0.5), (cw, 0.04, ch), rng.choice(mats), bevel=0.008, subdiv_cuts=1)
    wpos = _world_pt(origin, rot_z, local_pos)
    return fmb.to_object(name, collection=col, location=wpos, rot_z=rot_z)


def build_minka(spec: dict, col, rng: random.Random) -> list:
    """2F traditional wooden Japanese minka with kirizuma roof, hisashi eave, engawa & shoji."""
    w, d = spec["w"], spec["d"]
    h = 5.65  # 2 floors x ~2.8m
    pos, rot_z = Vector(spec["pos"]), spec["rot_z"]
    mb = MeshBuilder(spec["name"])

    _add_base_and_trim(mb, w, d, h, spec["wall"], "wood_dark", "stone", wainscot_mat="wood_dark")
    # Traditional 1F projecting eave (hisashi) on front facade
    mb.box((0.0, -d * 0.5 - 0.55, 3.15), (w + 0.60, 1.25, 0.15), spec["roof"], bevel=0.02, rot_euler=(0.24, 0.0, 0.0))
    # Raised wooden engawa veranda on front-left + grounded stilt legs & stone step
    ew = w * 0.48
    mb.box((-w * 0.22, -d * 0.5 - 0.52, 0.62), (ew, 0.98, 0.14), "wood_light", bevel=0.015)
    for sx in (-ew * 0.42, 0.0, ew * 0.42):
        mb.box((-w * 0.22 + sx, -d * 0.5 - 0.86, -0.58), (0.14, 0.14, 2.32), "wood_dark")
    mb.box((-w * 0.22, -d * 0.5 - 1.24, -0.35), (0.95, 0.56, 1.40), "stone", bevel=0.03)
    # Grounded entry stone plinth under front sliding door
    mb.box((w * 0.24, -d * 0.5 - 0.48, -0.45), (1.85, 0.88, 1.88), "stone", bevel=0.03)

    # 1F sliding wooden door + shoji veranda window
    mb.door_unit((w * 0.24, -d * 0.5, 0.52), 1.65, 2.05, "-Y", "wood_dark", "door_wood", "shoji", sliding=True)
    mb.window_unit((-w * 0.22, -d * 0.5, 1.68), ew * 0.84, 1.55, "-Y", "wood_dark", "shoji", "wood_dark", mullions=(2, 2))
    # 2F flush windows with wood frames & shutters
    for fx in (-w * 0.26, w * 0.26):
        mb.window_unit((fx, -d * 0.5, 4.45), 1.45, 1.28, "-Y", "wood_dark", "window_glass", "wood_light", mullions=(1, 1), shutter_mat="wood_weathered")
    # Side & back windows
    for face, sx in (("-X", -w * 0.5), ("+X", w * 0.5)):
        mb.window_unit((sx, 0.0, 4.45), 1.25, 1.15, face, "wood_dark", "window_glass", "wood_light", mullions=(1, 1))
        mb.window_unit((sx, -d * 0.18, 1.85), 1.15, 1.10, face, "wood_dark", "window_glass", "wood_light", mullions=(1, 0))
    mb.window_unit((0.0, d * 0.5, 4.45), 1.50, 1.15, "+Y", "wood_dark", "window_glass", "wood_light")

    add_ac_unit(mb, (w * 0.5, d * 0.24, 1.10), "+X")
    _add_downspout_and_pots(mb, w, d, h, rng)
    add_kirizuma_roof(mb, 0.0, 0.0, 0.50 + h, w, d, 27.0, spec["roof"], spec["wall"], "wood_dark", 0.65, 0.72)

    return [mb.to_object(spec["name"], collection=col, location=pos, rot_z=rot_z)]


def build_stucco_house(spec: dict, col, rng: random.Random, laundry_mb: MeshBuilder | None = None) -> list:
    """2F coastal pastel stucco residence with irimoya roof, 2F balcony, flower box & laundry."""
    w, d = spec["w"], spec["d"]
    h = 5.75
    pos, rot_z = Vector(spec["pos"]), spec["rot_z"]
    mb = MeshBuilder(spec["name"])
    objs = []

    _add_base_and_trim(mb, w, d, h, spec["wall"], "trim_white", "concrete")
    # 1F entrance door + grounded stone doorstep + porch hood + living room windows + flower box
    mb.door_unit((-w * 0.26, -d * 0.5, 0.52), 1.15, 2.08, "-Y", "window_frame", "door_wood", "window_glass")
    mb.box((-w * 0.26, -d * 0.5 - 0.42, -0.30), (1.55, 0.78, 1.56), "stone", bevel=0.025)
    mb.box((-w * 0.26, -d * 0.5 - 0.45, 2.75), (1.75, 0.95, 0.12), spec["roof"], bevel=0.02, rot_euler=(0.15, 0.0, 0.0))
    mb.window_unit((w * 0.20, -d * 0.5, 1.80), 1.95, 1.35, "-Y", "window_frame", "window_glass", "trim_white", mullions=(2, 1), shutter_mat="metal_grey")
    _add_window_box(mb, w * 0.20, -d * 0.5, 1.02, 1.45, rng)

    # 2F balcony on front + sliding balcony doors & laundry pole
    bw = w * 0.68
    add_balcony(mb, (w * 0.06, -d * 0.5, 3.45), bw, 1.12, "-Y", "concrete", "metal_dark", mat_wall=spec["wall"] if rng.random() < 0.45 else None)
    mb.window_unit((w * 0.06, -d * 0.5, 4.48), bw * 0.72, 1.75, "-Y", "window_frame", "window_glass", None, mullions=(2, 1))
    # Side & rear windows
    for face, sx in (("-X", -w * 0.5), ("+X", w * 0.5)):
        mb.window_unit((sx, 0.0, 4.48), 1.30, 1.15, face, "window_frame", "window_glass", "trim_white")
        mb.window_unit((sx, 0.1, 1.82), 1.25, 1.10, face, "window_frame", "window_glass", "trim_white")
    mb.window_unit((0.0, d * 0.5, 4.48), 1.60, 1.15, "+Y", "window_frame", "window_glass", "trim_white")

    # Laundry pole across balcony + animated laundry clothes (batched when laundry_mb given)
    mb.cylinder((w * 0.06, -d * 0.5 - 0.72, 4.95), 0.025, bw * 0.92, "metal_grey", segs=6, rot_euler=(0.0, math.pi * 0.5, 0.0))
    if rng.random() < 0.72:
        lo = _add_laundry_line(col, f"anim_flag_laundry_{spec['idx']:02d}", pos, rot_z, (w * 0.06, -d * 0.5 - 0.72, 4.92), bw * 0.78, rng, batch_mb=laundry_mb)
        if lo is not None:
            objs.append(lo)

    add_ac_unit(mb, (-w * 0.5, -d * 0.15, 1.12), "-X")
    _add_downspout_and_pots(mb, w, d, h, rng)
    add_irimoya_roof(mb, 0.0, 0.0, 0.50 + h, w, d, 26.0, spec["roof"], spec["wall"], "wood_dark", 0.72)

    objs.insert(0, mb.to_object(spec["name"], collection=col, location=pos, rot_z=rot_z))
    return objs


def build_shop_house(spec: dict, col, rng: random.Random) -> list:
    """2F coastal shopping-street machiya with awning, noren, signs & lattice 2F."""
    w, d = spec["w"], spec["d"]
    h = 5.65
    pos, rot_z = Vector(spec["pos"]), spec["rot_z"]
    mb = MeshBuilder(spec["name"])
    objs = []

    _add_base_and_trim(mb, w, d, h, spec["wall"], "wood_dark", "concrete", wainscot_mat="wood_light" if rng.random() < 0.5 else None)
    # Wide 1F shopfront: glass display window + wooden sliding entrance
    mb.door_unit((-w * 0.24, -d * 0.5, 0.52), 1.80, 2.15, "-Y", "wood_dark", "door_wood", "window_glass", sliding=True)
    mb.window_unit((w * 0.22, -d * 0.5, 1.65), w * 0.42, 1.55, "-Y", "wood_dark", "window_glass", "wood_dark", mullions=(2, 1))

    # Striped fabric awning over shopfront with steel side brackets
    aw_mat = rng.choice(["awning_stripe", "noren_indigo", "tram_green"])
    mb.box((0.0, -d * 0.5 - 0.62, 3.05), (w - 0.20, 1.38, 0.14), aw_mat, bevel=0.02, rot_euler=(0.32, 0.0, 0.0))
    # Valance scalloped front lip + stripe ribs
    mb.box((0.0, -d * 0.5 - 1.26, 2.76), (w - 0.20, 0.08, 0.24), "trim_white", bevel=0.01)
    n_stripes = max(4, int(w / 0.72))
    for i in range(0, n_stripes, 2):
        sx = -w * 0.5 + 0.25 + (w - 0.50) * (i / max(1, n_stripes - 1))
        mb.box((sx, -d * 0.5 - 0.62, 3.10), (0.28, 1.36, 0.06), "trim_white", rot_euler=(0.32, 0.0, 0.0))

    # 2F traditional wooden lattice (koshi) windows
    for fx in (-w * 0.24, w * 0.24):
        mb.window_unit((fx, -d * 0.5, 4.45), 1.50, 1.25, "-Y", "wood_dark", "shoji" if rng.random() < 0.4 else "window_glass", "wood_dark", mullions=(3, 1))
    for face, sx in (("-X", -w * 0.5), ("+X", w * 0.5)):
        mb.window_unit((sx, 0.0, 4.45), 1.15, 1.05, face, "wood_dark", "window_glass", "trim_white")

    # Separate animated split noren curtain hanging across shop doorway
    noren_mat = rng.choice(["noren_indigo", "noren_red"])
    nmb = MeshBuilder(f"anim_flag_noren_{spec['idx']:02d}")
    for k in range(3):
        nx = -0.54 + k * 0.54
        nmb.box((nx, 0.0, -0.34), (0.48, 0.035, 0.68), noren_mat, bevel=0.008, subdiv_cuts=1)
    n_wpos = _world_pt(pos, rot_z, (-w * 0.24, -d * 0.5 - 0.14, 2.52))
    objs.append(nmb.to_object(f"anim_flag_noren_{spec['idx']:02d}", collection=col, location=n_wpos, rot_z=rot_z))

    # Shop sign plane (`sign_<idx>`) with fictional Japanese shop text custom property
    shop_text = spec.get("shop_text", "汐見商店")
    smb = MeshBuilder(f"sign_{spec['idx']:02d}")
    sign_mat = rng.choice(["trim_white", "sign_yellow", "wall_cream"])
    smb.box((0.0, 0.0, 0.0), (min(2.6, w * 0.48), 0.09, 0.62), sign_mat, bevel=0.015)
    s_wpos = _world_pt(pos, rot_z, (0.0, -d * 0.5 - 0.12, 3.48))
    sobj = smb.to_object(f"sign_{spec['idx']:02d}", collection=col, location=s_wpos, rot_z=rot_z)
    sobj["text"] = shop_text
    objs.append(sobj)

    # Projecting small vertical side sign bracket (adds super authentic 商店街 depth!)
    mb.box((w * 0.5 + 0.36, -d * 0.5 + 0.12, 4.15), (0.58, 0.10, 1.55), rng.choice(["sign_yellow", "vending_red", "vending_blue"]), bevel=0.02)
    add_ac_unit(mb, (w * 0.5, d * 0.22, 3.55), "+X")
    _add_downspout_and_pots(mb, w, d, h, rng)
    add_kirizuma_roof(mb, 0.0, 0.0, 0.50 + h, w, d, 25.0, spec["roof"], spec["wall"], "wood_dark", 0.58, 0.65)

    objs.insert(0, mb.to_object(spec["name"], collection=col, location=pos, rot_z=rot_z))
    return objs


def build_apartment(spec: dict, col, rng: random.Random, laundry_mb: MeshBuilder | None = None) -> list:
    """3F seaside Japanese apato with exterior steel stairs, walkway railings & laundry."""
    w, d = spec["w"], spec["d"]
    h = 8.45  # 3 storeys
    pos, rot_z = Vector(spec["pos"]), spec["rot_z"]
    mb = MeshBuilder(spec["name"])
    objs = []

    _add_base_and_trim(mb, w, d, h, spec["wall"], "concrete", "concrete")
    # 3 floors of doors/windows + exterior cantilevered walkways on 2F & 3F
    for fl in range(3):
        zf = 0.52 + fl * 2.80
        if fl >= 1:
            add_balcony(mb, (0.0, -d * 0.5, zf), w - 0.20, 1.15, "-Y", "concrete", "metal_dark")
        for u in (-1, 1):
            ux = u * (w * 0.26)
            mb.door_unit((ux - 0.95, -d * 0.5, zf), 0.92, 2.02, "-Y", "metal_dark", "door_wood", None)
            mb.window_unit((ux + 0.68, -d * 0.5, zf + 1.32), 1.48, 1.18, "-Y", "window_frame", "window_glass", "concrete", mullions=(1, 0))
            mb.window_unit((ux, d * 0.5, zf + 1.32), 1.40, 1.15, "+Y", "window_frame", "window_glass", "concrete")
        add_ac_unit(mb, (w * 0.5, -d * 0.12, zf + 0.65), "+X")

    # Exterior steel staircase on left (-X) side climbing 1F -> 2F -> 3F
    for fl in range(2):
        z0 = 0.52 + fl * 2.80
        n_st = 11
        for s in range(n_st):
            t = s / n_st
            sy = -d * 0.42 + t * (d * 0.78)
            sz = z0 + t * 2.80
            mb.box((-w * 0.5 - 0.62, sy, sz), (1.10, 0.30, 0.08), "metal_grey")
        mb.box((-w * 0.5 - 0.62, d * 0.40, z0 + 2.76), (1.20, 1.05, 0.12), "metal_grey")
        mb.tube(
            [Vector((-w * 0.5 - 1.15, -d * 0.42, z0 + 0.95)), Vector((-w * 0.5 - 1.15, d * 0.40, z0 + 3.72))],
            0.032, "metal_dark", 5,
        )

    # Low-pitched roof with parapet + rooftop water tank
    mb.box((0.0, 0.0, 0.50 + h + 0.30), (w + 0.25, d + 0.25, 0.65), "concrete", bevel=0.03)
    add_kirizuma_roof(mb, 0.0, 0.0, 0.50 + h + 0.45, w - 0.3, d - 0.3, 14.0, spec["roof"], spec["wall"], "metal_dark", 0.52, 0.55, tile_ribs=False)
    mb.cylinder((w * 0.32, d * 0.24, 0.50 + h + 1.45), 0.68, 1.35, "wall_sky", segs=12)

    # Hanging laundry on 2F/3F railings (batched when laundry_mb given)
    lo = _add_laundry_line(col, f"anim_flag_laundry_{spec['idx']:02d}", pos, rot_z, (w * 0.22, -d * 0.5 - 0.85, 4.45), w * 0.36, rng, batch_mb=laundry_mb)
    if lo is not None:
        objs.append(lo)
    objs.insert(0, mb.to_object(spec["name"], collection=col, location=pos, rot_z=rot_z))
    return objs


def build_warehouse(spec: dict, col, rng: random.Random) -> list:
    """Harbor fish market / tin-roof warehouse with loading dock, barn doors & vents."""
    w, d = spec["w"], spec["d"]
    h = 4.65
    pos, rot_z = Vector(spec["pos"]), spec["rot_z"]
    mb = MeshBuilder(spec["name"])
    objs = []

    _add_base_and_trim(mb, w, d, h, "wall_cream", "wood_weathered", "concrete", wainscot_mat="wood_weathered")
    # Loading apron dock in front
    mb.box((0.0, -d * 0.5 - 0.85, 0.28), (w + 0.4, 1.65, 0.55), "concrete", bevel=0.03)
    # Wide twin sliding cargo doors + clerestory high windows
    mb.door_unit((-w * 0.18, -d * 0.5, 0.55), 3.1, 2.85, "-Y", "metal_dark", "wood_dark", None, sliding=True)
    mb.door_unit((w * 0.28, -d * 0.5, 0.55), 1.4, 2.25, "-Y", "metal_dark", "door_wood", "window_glass")
    for wx in (-w * 0.30, 0.0, w * 0.30):
        mb.window_unit((wx, -d * 0.5, 4.15), 1.65, 0.68, "-Y", "metal_dark", "window_glass", None, mullions=(2, 0))
    # Corrugated red tin gable roof + 2 roof vents
    z_pk = add_kirizuma_roof(mb, 0.0, 0.0, 0.50 + h, w, d, 21.0, "roof_tin_red", "wood_weathered", "metal_dark", 0.72, 0.85, tile_ribs=True)
    for vx in (-w * 0.24, w * 0.24):
        mb.cylinder((vx, 0.0, z_pk + 0.25), 0.28, 0.65, "metal_grey", segs=10)
        mb.cylinder((vx, 0.0, z_pk + 0.62), 0.40, 0.18, "metal_dark", segs=10, radius_top=0.12)
    # Stacked fish crates on loading dock
    for k, (cx, cy, cm) in enumerate(((-w * 0.38, -d * 0.5 - 0.75, "vending_blue"), (-w * 0.38, -d * 0.5 - 0.75, "sign_yellow"), (w * 0.40, -d * 0.5 - 0.80, "wood_light"))):
        cz = 0.76 + (0.44 if k == 1 else 0.0)
        mb.box((cx, cy, cz), (0.72, 0.52, 0.42), cm, bevel=0.015)
    # Fish market sign board if specified
    if spec.get("shop_text"):
        smb = MeshBuilder(f"sign_{spec['idx']:02d}")
        smb.box((0.0, 0.0, 0.0), (3.4, 0.10, 0.75), "wall_cream", bevel=0.015)
        sobj = smb.to_object(f"sign_{spec['idx']:02d}", collection=col, location=_world_pt(pos, rot_z, (0.0, -d * 0.5 - 0.14, 4.88)), rot_z=rot_z)
        sobj["text"] = spec["shop_text"]
        objs.append(sobj)

    objs.insert(0, mb.to_object(spec["name"], collection=col, location=pos, rot_z=rot_z))
    return objs


def build_cottage(spec: dict, col, rng: random.Random) -> list:
    """Cozy 1F Japanese hilltop cottage with deep kawara roof, engawa & stovepipe."""
    w, d = spec["w"], spec["d"]
    h = 3.05
    pos, rot_z = Vector(spec["pos"]), spec["rot_z"]
    mb = MeshBuilder(spec["name"])

    _add_base_and_trim(mb, w, d, h, spec["wall"], "wood_dark", "stone", wainscot_mat="wood_light" if rng.random() < 0.5 else None)
    mb.door_unit((-w * 0.24, -d * 0.5, 0.52), 1.30, 2.02, "-Y", "wood_dark", "door_wood", "shoji", sliding=True)
    mb.box((-w * 0.24, -d * 0.5 - 0.42, -0.30), (1.55, 0.78, 1.56), "stone", bevel=0.025)
    mb.window_unit((w * 0.18, -d * 0.5, 1.82), 1.85, 1.28, "-Y", "wood_dark", "window_glass", "wood_light", mullions=(2, 1))
    _add_window_box(mb, w * 0.18, -d * 0.5, 1.08, 1.35, rng)
    for face, sx in (("-X", -w * 0.5), ("+X", w * 0.5)):
        mb.window_unit((sx, 0.0, 1.82), 1.20, 1.05, face, "wood_dark", "window_glass", "wood_light")
    # Front wooden engawa bench (grounded on timber stilts) + small chimney pipe
    mb.box((w * 0.18, -d * 0.5 - 0.45, 0.58), (2.4, 0.85, 0.14), "wood_light", bevel=0.015)
    for sx in (-0.95, 0.95):
        mb.box((w * 0.18 + sx, -d * 0.5 - 0.74, -0.58), (0.14, 0.14, 2.26), "wood_dark")
    mb.cylinder((w * 0.34, d * 0.25, 4.65), 0.11, 2.2, "metal_dark", segs=8)
    add_ac_unit(mb, (-w * 0.5, d * 0.18, 1.05), "-X")
    _add_downspout_and_pots(mb, w, d, h, rng)
    if rng.random() < 0.5:
        add_irimoya_roof(mb, 0.0, 0.0, 0.50 + h, w, d, 27.0, spec["roof"], spec["wall"], "wood_dark", 0.68)
    else:
        add_kirizuma_roof(mb, 0.0, 0.0, 0.50 + h, w, d, 28.0, spec["roof"], spec["wall"], "wood_dark", 0.65, 0.70)

    return [mb.to_object(spec["name"], collection=col, location=pos, rot_z=rot_z)]
