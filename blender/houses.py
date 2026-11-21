"""Deterministic dense shoulder-to-shoulder placement of ~125 Japanese houses,
shops, apartments, warehouses, and town landmarks across Shiomi-cho.
"""

import math
import random
from terrain import get_height, QUAY_Z, SHRINE_CENTER
from lib.geo import MeshBuilder
from house_archetypes import (
    build_minka,
    build_stucco_house,
    build_shop_house,
    build_apartment,
    build_warehouse,
    build_cottage,
)
from landmarks import (
    build_fish_market,
    build_school_clock_hall,
    build_water_tower,
    build_yard_details,
)

SHOP_NAMES = [
    "汐見食堂", "かもめ書店", "潮風珈琲", "波音ベーカリー", "たばこ・雑貨",
    "みなと鮮魚", "海辺の薬局", "青空文具店", "浜茶屋しおみ", "みかん青果",
    "海星和菓子", "潮騒クリーニング", "港町ラーメン", "汐見民芸品", "うみねこ喫茶",
    "いそ風豆腐店", "みなと理容室", "さざなみ酒販", "潮見時計店", "波止場うどん",
    "かもめ乾物", "海風写真館", "あじさい生花", "夕凪食堂",
]

WALL_PALETTE_STUCCO = ["wall_cream", "wall_white", "wall_peach", "wall_mint", "wall_sky"]
WALL_PALETTE_MINKA = ["wall_cream", "wall_white", "wall_peach"]
ROOF_PALETTE = ["roof_blue", "roof_teal", "roof_terracotta", "roof_charcoal"]

# Populated when specs are generated so nature/props avoid building footprints
HOUSE_FOOTPRINTS: list[tuple[float, float, float]] = []

# Road/lane polylines matching roads_rail.py for exact collision clearance
_ROAD_POLYS = [
    [(-25.0, 6.8), (-25.0, 15.5), (-25.0, 23.0), (-24.0, 34.0), (-6.0, 40.0),
     (22.0, 44.0), (42.0, 56.0), (28.0, 74.0), (2.0, 82.0), (-28.0, 88.0),
     (-48.0, 100.0), (-42.0, 118.0), (-28.0, 128.0)],
    [(32.0, 20.0), (50.0, 32.0), (54.0, 48.0), (42.0, 56.0)],
    [(-25.0, 22.0), (-52.0, 26.0), (-64.0, 46.0), (-56.0, 70.0), (-28.0, 88.0)],
]
_STAIR_POLY = [(4.0, 18.0), (0.0, 36.0), (-6.0, 56.0), (-12.0, 78.0), (-18.0, 102.0), (-26.0, 132.5)]


def _seg_dist(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
    dx, dy = bx - ax, by - ay
    l2 = dx * dx + dy * dy
    if l2 < 1e-6:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / l2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def _poly_dist(px: float, py: float, poly: list[tuple[float, float]]) -> float:
    return min(_seg_dist(px, py, poly[i][0], poly[i][1], poly[i + 1][0], poly[i + 1][1]) for i in range(len(poly) - 1))


def _min_plot_z(x: float, y: float, w: float, d: float) -> float:
    """Use downhill edge terrain height so front doors meet terrace grade cleanly."""
    z_c = get_height(x, y)
    z_f = get_height(x, y - d * 0.45)
    z_l = get_height(x - w * 0.35, y - d * 0.30)
    z_r = get_height(x + w * 0.35, y - d * 0.30)
    return min(z_c, 0.5 * (z_c + min(z_f, z_l, z_r))) - 0.15


def get_house_specs(seed: int = 4207) -> list[dict]:
    """Generate deterministic, shoulder-to-shoulder specs for ~125–135 buildings."""
    rng = random.Random(seed + 303)
    specs: list[dict] = []
    placed_boxes: list[tuple[float, float, float, float]] = []  # (x, y, half_w, half_d)
    idx = 1
    shop_i = 0

    def overlaps_existing(x: float, y: float, w: float, d: float, gap_x: float = 0.85, gap_y: float = 1.6) -> bool:
        hw, hd = w * 0.5 + gap_x * 0.5, d * 0.5 + gap_y * 0.5
        for ox, oy, ohw, ohd in placed_boxes:
            if abs(x - ox) < (hw + ohw) and abs(y - oy) < (hd + ohd):
                return True
        return False

    def clears_infrastructure(x: float, y: float, w: float, d: float) -> bool:
        rad = 0.48 * max(w, d)
        # Shrine plateau clearance
        if math.hypot(x - SHRINE_CENTER[0], y - SHRINE_CENTER[1]) < 17.5 + rad * 0.5:
            return False
        # Main shrine stairway clearance
        if _poly_dist(x, y, _STAIR_POLY) < 2.6 + rad * 0.85:
            return False
        # Switchback and side lanes clearance
        for poly in _ROAD_POLYS:
            if _poly_dist(x, y, poly) < 2.25 + rad * 0.82:
                return False
        # Level crossing corridor clearance
        if abs(x + 25.0) < 3.6 + w * 0.45 and y < 28.0:
            return False
        # Shiomi Station platform clearance (y = 14..18, x = -2..24)
        if -3.5 - w * 0.45 < x < 25.5 + w * 0.45 and y < 20.5 + d * 0.45:
            return False
        # Keep Camera 04 lens (-42, 39.2) and immediate sightline unobstructed
        if -45.6 < x < -38.4 and 36.2 < y < 48.8:
            return False
        return True

    def add_spec(kind: str, x: float, y: float, w: float, d: float, rot_z: float,
                 z_override: float | None = None, shop_text: str | None = None, roof_override: str | None = None):
        nonlocal idx
        z = z_override if z_override is not None else _min_plot_z(x, y, w, d)
        if kind == "minka":
            wall = rng.choice(WALL_PALETTE_MINKA)
            roof = rng.choice(["roof_charcoal", "roof_blue", "roof_teal"])
        elif kind == "stucco":
            wall = rng.choice(WALL_PALETTE_STUCCO)
            roof = rng.choice(ROOF_PALETTE)
        elif kind == "shop":
            wall = rng.choice(["wall_cream", "wall_white", "wall_peach", "wall_mint", "wall_sky"])
            roof = rng.choice(["roof_blue", "roof_teal", "roof_charcoal", "roof_terracotta"])
        elif kind == "apartment":
            wall = rng.choice(["wall_white", "wall_cream", "wall_sky", "wall_mint", "wall_peach"])
            roof = rng.choice(["roof_charcoal", "roof_blue", "roof_tin_red", "roof_teal"])
        elif kind in ("warehouse", "fish_market"):
            wall, roof = "wall_cream", "roof_tin_red"
        elif kind == "school":
            wall, roof = "wall_white", "roof_terracotta"
        elif kind == "water_tower":
            wall, roof = "wall_white", "roof_blue"
        else:
            wall = rng.choice(WALL_PALETTE_STUCCO)
            roof = rng.choice(ROOF_PALETTE)
        if roof_override:
            roof = roof_override

        specs.append({
            "idx": idx, "name": f"house_{kind}_{idx:03d}", "kind": kind,
            "pos": (x, y, z), "w": w, "d": d, "rot_z": rot_z,
            "wall": wall, "roof": roof, "shop_text": shop_text,
        })
        placed_boxes.append((x, y, w * 0.5, d * 0.5))
        idx += 1

    # 1. Harbor Fish Market Hall (enlarged landmark) + 4 Quay Warehouses/Gear Sheds
    add_spec("fish_market", 64.0, -0.85, 16.0, 4.3, 0.0, z_override=QUAY_Z - 0.12, shop_text="汐見魚市場")
    add_spec("warehouse", 81.2, -0.95, 10.6, 4.3, 0.0, z_override=QUAY_Z - 0.12, shop_text="海風水産")
    add_spec("warehouse", 34.5, -0.95, 7.6, 4.1, 0.0, z_override=QUAY_Z - 0.12, shop_text="港湾倉庫")
    add_spec("warehouse", -49.8, -0.95, 8.8, 4.3, 0.0, z_override=QUAY_Z - 0.12, shop_text="かもめ船具")
    add_spec("warehouse", -38.8, -0.95, 6.8, 4.0, 0.0, z_override=QUAY_Z - 0.12, shop_text="汐見網小屋")

    # 2. Continuous Coastal Shopping Street (21 buildings, shoulder-to-shoulder ~1.0-1.5m gap)
    # Gaps ONLY at level crossing (x=-25) and Shiomi Station (x=10)
    coastal_plan = [
        (-74.5, 6.0, "shop"), (-67.4, 6.2, "shop"), (-60.0, 6.8, "apartment"), (-52.4, 6.2, "shop"),
        (-45.2, 6.0, "shop"), (-38.2, 6.1, "shop"), (-31.6, 5.6, "shop"),
        (-18.2, 5.8, "shop"), (-11.3, 6.2, "shop"), (-4.2, 6.6, "apartment"), (2.3, 5.2, "shop"),
        (18.0, 5.8, "shop"), (25.0, 6.8, "apartment"), (32.2, 6.0, "shop"), (39.2, 6.2, "shop"),
        (46.2, 6.0, "shop"), (53.4, 6.8, "apartment"), (60.6, 6.0, "shop"), (67.8, 6.1, "shop"),
        (75.0, 6.0, "shop"), (82.0, 5.8, "shop"),
    ]
    for cx, cw, kind in coastal_plan:
        cd = 3.95 if kind == "apartment" else rng.uniform(3.95, 4.25)
        cy = 9.30 if kind == "apartment" else 9.15
        stext = SHOP_NAMES[shop_i % len(SHOP_NAMES)] if kind == "shop" else None
        if kind == "shop":
            shop_i += 1
        add_spec(kind, cx, cy, cw, cd, rng.uniform(-0.03, 0.03), z_override=1.42, shop_text=stext)

    # 3. Prominent Hillside Landmarks: Elementary Clock School + Municipal Water Tower
    add_spec("school", 27.5, 84.5, 15.0, 6.4, -0.06, shop_text="汐見小学校", roof_override="roof_terracotta")
    add_spec("water_tower", 50.5, 102.5, 6.0, 6.0, 0.0)

    # 4. Curated Hero Close-up Cluster around Camera 04 (-42, 39.2 looking north)
    # Packs houses tightly along a charming hillside courtyard/alley without blocking camera
    cam04_hero = [
        (-49.2, 44.8, 6.4, 5.2, "minka", 0.05),
        (-34.8, 45.2, 6.4, 5.2, "stucco", -0.06),
        (-42.0, 52.8, 6.8, 5.4, "stucco", 0.02),
        (-50.2, 53.5, 6.2, 5.0, "minka", 0.08),
        (-33.8, 54.0, 6.4, 5.2, "cottage", -0.05),
    ]
    for hx, hy, hw, hd, hk, hrot in cam04_hero:
        add_spec(hk, hx, hy, hw, hd, hrot)

    # 5. Dense Shoulder-to-Shoulder Hillside Terrace Rows (9 stepped tiers filling the slope!)
    # (y_center, x_min, x_max, weights for [minka, stucco, cottage, apartment, shop])
    terrace_bands = [
        (22.2, -76.0, 76.0, [0.34, 0.30, 0.14, 0.12, 0.10]),
        (32.2, -74.0, 72.0, [0.34, 0.34, 0.22, 0.10, 0.00]),
        (43.2, -70.0, 68.0, [0.34, 0.36, 0.22, 0.08, 0.00]),
        (54.2, -66.0, 64.0, [0.35, 0.35, 0.24, 0.06, 0.00]),
        (65.5, -64.0, 60.0, [0.36, 0.34, 0.26, 0.04, 0.00]),
        (77.0, -60.0, 54.0, [0.36, 0.34, 0.30, 0.00, 0.00]),
        (89.5, -56.0, 48.0, [0.35, 0.33, 0.32, 0.00, 0.00]),
        (102.5, -52.0, 38.0, [0.34, 0.30, 0.36, 0.00, 0.00]),
        (114.5, -48.0, 28.0, [0.32, 0.28, 0.40, 0.00, 0.00]),
    ]
    kind_pool = ["minka", "stucco", "cottage", "apartment", "shop"]

    for y_base, x_lo, x_hi, weights in terrace_bands:
        x = x_lo + rng.uniform(0.0, 1.8)
        while x <= x_hi:
            kind = rng.choices(kind_pool, weights=weights, k=1)[0]
            if kind == "apartment":
                w, d = rng.uniform(7.2, 8.2), rng.uniform(5.2, 5.8)
            elif kind == "cottage":
                w, d = rng.uniform(5.4, 6.6), rng.uniform(4.6, 5.4)
            else:
                w, d = rng.uniform(5.6, 7.0), rng.uniform(4.8, 5.8)
            # Gentle contour wave matching retaining walls
            cy = y_base + 1.6 * math.sin(x * 0.045 + y_base * 0.1) + rng.uniform(-1.1, 1.1)
            # Try tiny y nudges if road just clips edge
            placed = False
            for dy_try in (0.0, 1.8, -1.8, 3.2):
                ty = cy + dy_try
                if ty < 20.0 or ty > 122.0:
                    continue
                if clears_infrastructure(x, ty, w, d) and not overlaps_existing(x, ty, w, d, gap_x=1.05, gap_y=1.7):
                    rot = rng.uniform(-0.14, 0.14) - x * 0.0018
                    st = SHOP_NAMES[shop_i % len(SHOP_NAMES)] if kind == "shop" else None
                    if kind == "shop":
                        shop_i += 1
                    add_spec(kind, x, ty, w, d, rot, shop_text=st)
                    x += w + rng.uniform(1.15, 2.15)  # shoulder-to-shoulder!
                    placed = True
                    break
            if not placed:
                x += 3.2

    HOUSE_FOOTPRINTS.clear()
    for sp in specs:
        px, py, _ = sp["pos"]
        rad = 0.55 * math.hypot(sp["w"], sp["d"]) + 1.2
        HOUSE_FOOTPRINTS.append((px, py, rad))
    return specs


def build_houses(col, seed: int = 4207) -> list:
    rng = random.Random(seed + 404)
    specs = get_house_specs(seed)
    print(f"[houses] Placing {len(specs)} buildings across harbor, coastal street & hillside terraces...")
    builders = {
        "minka": build_minka,
        "stucco": build_stucco_house,
        "shop": build_shop_house,
        "apartment": build_apartment,
        "warehouse": build_warehouse,
        "cottage": build_cottage,
        "fish_market": build_fish_market,
        "school": build_school_clock_hall,
        "water_tower": build_water_tower,
    }
    objs = []
    balcony_laundry_mb = MeshBuilder("anim_flag_laundry_balconies")

    for sp in specs:
        k = sp["kind"]
        if k in ("stucco", "apartment"):
            objs.extend(builders[k](sp, col, rng, laundry_mb=balcony_laundry_mb))
        else:
            objs.extend(builders[k](sp, col, rng))

    if len(balcony_laundry_mb.bm.verts) > 0:
        objs.append(balcony_laundry_mb.to_object("anim_flag_laundry_balconies", collection=col))
    else:
        balcony_laundry_mb.bm.free()

    objs.extend(build_yard_details(specs, col, rng))
    return objs
