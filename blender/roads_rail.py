"""Coastal road, winding hillside lanes, grand shrine stone stairway,
single-track coastal railway, level crossing, Shiomi Station, and vintage coastal tram.
"""

import math
import bpy
from mathutils import Vector
from lib.geo import MeshBuilder
from lib.roofs import add_kirizuma_roof
from terrain import get_height, ROAD_Y, RAIL_Y, RAIL_Z


def _add_path_strip(
    mb: MeshBuilder,
    pts: list[tuple[float, float]],
    width: float,
    mat: str,
    z_off: float = 0.08,
    thick: float = 0.32,
    subdiv: int = 1,
    curb_mat: str | None = None,
) -> None:
    """Lay overlapping terrain-hugging sloped segments along a 2D polyline."""
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        seg_dist = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(seg_dist / 3.8))
        for k in range(n):
            t0, t1 = k / n, (k + 1) / n
            ax, ay = x0 + (x1 - x0) * t0, y0 + (y1 - y0) * t0
            bx, by = x0 + (x1 - x0) * t1, y0 + (y1 - y0) * t1
            za, zb = get_height(ax, ay) + z_off, get_height(bx, by) + z_off
            xm, ym, zm = 0.5 * (ax + bx), 0.5 * (ay + by), 0.5 * (za + zb)
            dx, dy, dz = bx - ax, by - ay, zb - za
            horiz = math.hypot(dx, dy)
            length = math.hypot(horiz, dz) + 0.35
            yaw = math.atan2(dy, dx)
            pitch = -math.atan2(dz, max(1e-4, horiz))
            mb.box(
                (xm, ym, zm - thick * 0.45),
                (length, width, thick),
                mat,
                bevel=0.02,
                rot_euler=(0.0, pitch, yaw),
                subdiv_cuts=subdiv,
            )
            if curb_mat:
                nx_v, ny_v = -math.sin(yaw), math.cos(yaw)
                for sgn in (-1.0, 1.0):
                    cx = xm + nx_v * sgn * (width * 0.5 + 0.12)
                    cy = ym + ny_v * sgn * (width * 0.5 + 0.12)
                    mb.box(
                        (cx, cy, zm - thick * 0.25 + 0.06),
                        (length, 0.22, thick + 0.10),
                        curb_mat,
                        bevel=0.02,
                        rot_euler=(0.0, pitch, yaw),
                    )


def _add_coastal_road(mb: MeshBuilder) -> None:
    road_pts = [(x, ROAD_Y) for x in range(-128, 122, 10)]
    _add_path_strip(mb, road_pts, width=5.2, mat="asphalt", z_off=0.07, thick=0.35, subdiv=1, curb_mat="concrete")

    # White edge stripes & dashed center line
    for x in range(-122, 114, 6):
        z = get_height(x + 2.0, ROAD_Y) + 0.105
        mb.box((x + 2.0, ROAD_Y, z), (2.8, 0.13, 0.03), "road_line")
        for dy in (-2.25, 2.25):
            mb.box((x + 2.5, ROAD_Y + dy, z), (5.8, 0.11, 0.03), "road_line")

    # Crosswalk stripes at level crossing (-25) and station forecourt (10)
    for cx in (-25.0, 10.0):
        z = get_height(cx, ROAD_Y) + 0.11
        for k in range(-2, 3):
            mb.box((cx + k * 0.65, ROAD_Y, z), (0.34, 4.1, 0.03), "road_line")

    # Sea-side coastal guardrails (leave openings at piers & crossing)
    rail_spans = [(-112, -62), (-52, -31), (-18, 2), (20, 48), (58, 90)]
    for x0, x1 in rail_spans:
        n_posts = max(2, int((x1 - x0) / 3.0))
        pts_top = []
        for i in range(n_posts + 1):
            px = x0 + (x1 - x0) * (i / n_posts)
            py = ROAD_Y - 2.75
            pz = get_height(px, py) + 0.05
            mb.cylinder((px, py, pz + 0.42), 0.045, 0.88, "metal_grey", segs=6)
            pts_top.append(Vector((px, py, pz + 0.68)))
        mb.tube(pts_top, radius=0.055, mat="trim_white", segs=6)
        mb.tube([p - Vector((0, 0, 0.24)) for p in pts_top], radius=0.038, mat="trim_white", segs=6)

    # Flush junction pad connecting coastal road cleanly to level-crossing street
    mb.box((-25.0, ROAD_Y + 2.4, get_height(-25.0, ROAD_Y) - 0.08), (4.2, 3.2, 0.32), "asphalt")
    # Short south approach strip stopping cleanly at crossing deck (no curb cutting tracks!)
    _add_path_strip(mb, [(-25.0, ROAD_Y + 2.6), (-25.0, 11.4)], width=3.4, mat="asphalt", z_off=0.06, thick=0.32, subdiv=0, curb_mat=None)

    # Winding hillside lanes (switchback from north side of level crossing up to shrine)
    switchback = [
        (-25.0, 14.8), (-25.0, 23.0), (-24.0, 34.0),
        (-6.0, 40.0), (22.0, 44.0), (42.0, 56.0), (28.0, 74.0),
        (2.0, 82.0), (-28.0, 88.0), (-48.0, 100.0), (-42.0, 118.0), (-28.0, 128.0),
    ]
    _add_path_strip(mb, switchback, width=3.4, mat="asphalt", z_off=0.08, thick=0.38, subdiv=0, curb_mat="stone")

    east_lane = [(32.0, 20.0), (50.0, 32.0), (54.0, 48.0), (42.0, 56.0)]
    _add_path_strip(mb, east_lane, width=2.8, mat="stone", z_off=0.08, thick=0.35, curb_mat="stone_dark")

    west_lane = [(-25.0, 22.0), (-52.0, 26.0), (-64.0, 46.0), (-56.0, 70.0), (-28.0, 88.0)]
    _add_path_strip(mb, west_lane, width=2.6, mat="stone", z_off=0.08, thick=0.35, curb_mat="stone_dark")

    # Add downhill tubular railings & low stone parapets along mid-slope switchbacks
    _add_lane_railings(mb, switchback[2:], half_w=1.82)
    _add_lane_railings(mb, east_lane, half_w=1.50)
    _add_lane_railings(mb, west_lane, half_w=1.42)

    # Add charming Onomichi side-alley stone stair flights linking hillside terraces
    side_stairs = [
        # Hero alley stairs visible in close-up shot 04 (-42, 41.5 -> 49.0)
        ((-42.0, 41.2), (-42.0, 49.2), 2.2),
        # Lower-west terrace connector
        ((-54.0, 27.5), (-55.0, 39.0), 2.0),
        # Mid-east terrace connector up toward school
        ((18.0, 25.5), (19.5, 39.5), 2.1),
        ((38.0, 58.0), (35.5, 72.0), 2.0),
        # Mid-west upper connector
        ((-32.0, 62.0), (-31.0, 77.5), 2.0),
        # Upper-east connector toward school & water tower
        ((27.5, 74.5), (27.5, 80.5), 2.6),
    ]
    for p0, p1, sw in side_stairs:
        _add_stair_flight(mb, p0, p1, width=sw)


def _add_lane_railings(mb: MeshBuilder, pts: list[tuple[float, float]], half_w: float) -> None:
    """Add downhill metal safety railings & low stone curb walls along hillside switchbacks."""
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        dist = math.hypot(x1 - x0, y1 - y0)
        if dist < 4.5:
            continue
        yaw = math.atan2(y1 - y0, x1 - x0)
        # Pick the downhill (south-facing, lower Z) normal side
        nx, ny = -math.sin(yaw), math.cos(yaw)
        xm, ym = 0.5 * (x0 + x1), 0.5 * (y0 + y1)
        if get_height(xm + nx * 2.0, ym + ny * 2.0) > get_height(xm - nx * 2.0, ym - ny * 2.0):
            nx, ny = -nx, -ny
        n_posts = max(3, int(dist / 3.4))
        rail_top: list[Vector] = []
        rail_mid: list[Vector] = []
        for k in range(n_posts + 1):
            t = 0.08 + 0.84 * (k / n_posts)
            px = x0 + (x1 - x0) * t + nx * half_w
            py = y0 + (y1 - y0) * t + ny * half_w
            pz = get_height(px, py) + 0.10
            mb.cylinder((px, py, pz + 0.45), 0.036, 0.92, "metal_dark", segs=6)
            rail_top.append(Vector((px, py, pz + 0.86)))
            rail_mid.append(Vector((px, py, pz + 0.46)))
        if len(rail_top) >= 2:
            mb.tube(rail_top, radius=0.038, mat="trim_white", segs=5)
            mb.tube(rail_mid, radius=0.026, mat="metal_grey", segs=5)


def _add_stair_flight(mb: MeshBuilder, p0: tuple[float, float], p1: tuple[float, float], width: float = 2.1) -> None:
    """Build a crisp stone staircase flight with low stone side walls & dark iron handrails."""
    x0, y0 = p0
    x1, y1 = p1
    dist = math.hypot(x1 - x0, y1 - y0)
    yaw = math.atan2(y1 - y0, x1 - x0)
    nx_v, ny_v = -math.sin(yaw), math.cos(yaw)
    n_steps = max(8, int(dist / 0.40))
    rail_l: list[Vector] = []
    rail_r: list[Vector] = []
    for s in range(n_steps):
        t = (s + 0.5) / n_steps
        sx = x0 + (x1 - x0) * t
        sy = y0 + (y1 - y0) * t
        sz = get_height(sx, sy) + 0.14
        mb.box((sx, sy, sz - 0.34), (0.48, width, 0.82), "stone", bevel=0.015, rot_euler=(0.0, 0.0, yaw))
        for sgn in (-1.0, 1.0):
            wx = sx + nx_v * sgn * (width * 0.5 + 0.18)
            wy = sy + ny_v * sgn * (width * 0.5 + 0.18)
            mb.box((wx, wy, sz - 0.06), (0.50, 0.28, 0.96), "stone_dark", bevel=0.015, rot_euler=(0.0, 0.0, yaw))
        if s % 4 == 0 or s == n_steps - 1:
            for sgn, rlist in ((-1.0, rail_l), (1.0, rail_r)):
                rx = sx + nx_v * sgn * (width * 0.5 + 0.18)
                ry = sy + ny_v * sgn * (width * 0.5 + 0.18)
                mb.cylinder((rx, ry, sz + 0.72), 0.028, 0.68, "metal_dark", segs=5)
                rlist.append(Vector((rx, ry, sz + 1.04)))
    if len(rail_l) >= 2:
        mb.tube(rail_l, radius=0.032, mat="metal_dark", segs=5)
        mb.tube(rail_r, radius=0.032, mat="metal_dark", segs=5)


def _add_shrine_stairway(mb: MeshBuilder) -> None:
    """Long monumental stone stairway climbing from near Shiomi Station up to the shrine."""
    # Curved spine from (4, 18) up to (-25, 131)
    waypoints = [
        (4.0, 18.0), (0.0, 36.0), (-6.0, 56.0), (-12.0, 78.0),
        (-18.0, 102.0), (-23.0, 122.0), (-26.0, 132.5),
    ]
    stair_w = 3.2
    rail_l: list[Vector] = []
    rail_r: list[Vector] = []

    for i in range(len(waypoints) - 1):
        x0, y0 = waypoints[i]
        x1, y1 = waypoints[i + 1]
        dist = math.hypot(x1 - x0, y1 - y0)
        yaw = math.atan2(y1 - y0, x1 - x0)
        nx_v, ny_v = -math.sin(yaw), math.cos(yaw)
        n_steps = max(10, int(dist / 0.42))
        for s in range(n_steps):
            t = (s + 0.5) / n_steps
            sx = x0 + (x1 - x0) * t
            sy = y0 + (y1 - y0) * t
            sz = get_height(sx, sy) + 0.14
            # Solid stone step embedded deep into terrain
            mb.box((sx, sy, sz - 0.35), (0.50, stair_w, 0.85), "stone", bevel=0.015, rot_euler=(0.0, 0.0, yaw))
            # Side curb walls
            for sgn in (-1.0, 1.0):
                wx = sx + nx_v * sgn * (stair_w * 0.5 + 0.22)
                wy = sy + ny_v * sgn * (stair_w * 0.5 + 0.22)
                mb.box((wx, wy, sz - 0.05), (0.54, 0.36, 1.05), "stone_dark", bevel=0.02, rot_euler=(0.0, 0.0, yaw))
            if s % 6 == 0:
                for sgn, rlist in ((-1.0, rail_l), (1.0, rail_r)):
                    rx = sx + nx_v * sgn * (stair_w * 0.5 + 0.22)
                    ry = sy + ny_v * sgn * (stair_w * 0.5 + 0.22)
                    mb.cylinder((rx, ry, sz + 0.78), 0.032, 0.72, "metal_dark", segs=6)
                    rlist.append(Vector((rx, ry, sz + 1.12)))

    if len(rail_l) >= 2:
        mb.tube(rail_l, radius=0.035, mat="metal_dark", segs=6)
        mb.tube(rail_r, radius=0.035, mat="metal_dark", segs=6)


def _add_railway_and_crossing(mb: MeshBuilder, col) -> list:
    objs = []
    # Gravel ballast bed along y = RAIL_Y from x=-170..170
    for x in range(-170, 170, 10):
        mb.box((x + 5.0, RAIL_Y, RAIL_Z - 0.12), (10.1, 3.0, 0.44), "stone_dark", bevel=0.08, subdiv_cuts=1)

    # Wooden sleepers every 0.80m
    x_pos = -168.0
    while x_pos <= 168.0:
        mb.box((x_pos, RAIL_Y, RAIL_Z + 0.12), (0.22, 1.95, 0.12), "wood_dark")
        x_pos += 0.80

    # Dual steel rails (1.067m gauge)
    for dy in (-0.533, 0.533):
        mb.box((0.0, RAIL_Y + dy, RAIL_Z + 0.24), (338.0, 0.08, 0.14), "rail_steel")

    # Overhead railway catenary masts & contact wire
    mast_xs = list(range(-148, 152, 24))
    wire_pts = []
    msg_pts = []
    for mx in mast_xs:
        my = RAIL_Y + 2.05
        mb.box((mx, my, RAIL_Z + 3.0), (0.22, 0.22, 6.2), "metal_grey", bevel=0.02)
        mb.box((mx, RAIL_Y + 0.7, RAIL_Z + 5.65), (0.12, 2.9, 0.12), "metal_grey")
        mb.tube(
            [Vector((mx, my - 0.1, RAIL_Z + 4.7)), Vector((mx, RAIL_Y + 0.1, RAIL_Z + 5.65))],
            radius=0.035, mat="metal_grey", segs=5,
        )
        wire_pts.append(Vector((mx, RAIL_Y, RAIL_Z + 5.15)))
        msg_pts.append(Vector((mx, RAIL_Y, RAIL_Z + 5.72)))
    for i in range(len(wire_pts) - 1):
        mb.catenary(wire_pts[i], wire_pts[i + 1], sag=0.05, radius=0.018, mat="wire_black", steps=6, segs=4)
        mb.catenary(msg_pts[i], msg_pts[i + 1], sag=0.22, radius=0.015, mat="wire_black", steps=6, segs=4)

    # Level crossing at x = -25 (fumikiri: deck, barrier gates, crossbucks, red lamps)
    cx = -25.0
    mb.box((cx, RAIL_Y, RAIL_Z + 0.18), (4.6, 2.8, 0.16), "asphalt", bevel=0.02)
    mb.box((cx, RAIL_Y, RAIL_Z + 0.21), (4.4, 1.0, 0.12), "wood_weathered")

    lamp_mb = MeshBuilder("lamp_crossing")
    for idx, (gx, gy, arm_dir) in enumerate(((cx - 2.6, RAIL_Y - 1.9, 1.0), (cx + 2.6, RAIL_Y + 1.9, -1.0))):
        gz = max(RAIL_Z, get_height(gx, gy) - 0.05)
        # Yellow & black striped signal post
        for k in range(8):
            mat_s = "crossing_yellow" if k % 2 == 0 else "crossing_black"
            mb.cylinder((gx, gy, gz + 0.25 + k * 0.45), 0.085, 0.46, mat_s, segs=8)
        # Crossbuck X sign
        for a in (0.65, -0.65):
            mb.box((gx, gy - arm_dir * 0.12, gz + 3.05), (0.92, 0.05, 0.14), "crossing_yellow", rot_euler=(0.0, a, 0.0))
        # Warning lamp hood + twin red glowing lenses
        mb.box((gx, gy - arm_dir * 0.14, gz + 2.35), (0.76, 0.18, 0.30), "crossing_black", bevel=0.02)
        for dx in (-0.22, 0.22):
            lamp_mb.cylinder((gx + dx, gy - arm_dir * 0.23, gz + 2.35), 0.11, 0.06, "lamp_glow", segs=10, rot_euler=(math.pi * 0.5, 0.0, 0.0))
        # Barrier motor housing + angled striped arm (raised ~58 deg so road feels open & lively)
        bx = gx + arm_dir * 0.55
        mb.box((bx, gy, gz + 0.55), (0.42, 0.36, 1.10), "crossing_yellow", bevel=0.02)
        mb.box((bx, gy, gz + 0.15), (0.50, 0.44, 0.30), "concrete")
        arm_pitch = arm_dir * math.radians(-52.0)
        for seg in range(7):
            dist = 0.35 + seg * 0.52
            ax = bx + arm_dir * dist * math.cos(math.radians(52.0))
            az = gz + 1.02 + dist * math.sin(math.radians(52.0))
            mat_a = "crossing_yellow" if seg % 2 == 0 else "crossing_black"
            mb.box((ax, gy, az), (0.52, 0.065, 0.075), mat_a, rot_euler=(0.0, arm_pitch, 0.0))
    # Relay control cabinet beside crossing
    mb.box((cx - 4.1, RAIL_Y - 2.3, RAIL_Z + 0.65), (0.85, 0.60, 1.30), "metal_grey", bevel=0.02)
    objs.append(lamp_mb.to_object("lamp_crossing_signals", collection=col))
    return objs


def _add_station_and_tram(mb: MeshBuilder, col) -> list:
    objs = []
    sx = 10.0
    # Raised platform on north side of track (x=-2..24, y=14.4..17.8)
    mb.box((sx + 1.0, RAIL_Y + 3.0, RAIL_Z + 0.52), (26.0, 3.4, 1.15), "concrete", bevel=0.03, subdiv_cuts=1)
    mb.box((sx + 1.0, RAIL_Y + 1.48, RAIL_Z + 1.11), (25.6, 0.26, 0.04), "sign_yellow")
    # Platform shelter roof & wooden posts
    for px in (2.0, 7.5, 13.0, 18.5):
        mb.box((px, RAIL_Y + 3.55, RAIL_Z + 2.55), (0.18, 0.18, 3.0), "wood_dark", bevel=0.015)
    mb.box((10.25, RAIL_Y + 3.15, RAIL_Z + 4.10), (18.2, 2.9, 0.16), "roof_teal", bevel=0.02, rot_euler=(0.10, 0.0, 0.0))
    # Platform benches
    for bx in (5.0, 15.5):
        mb.box((bx, RAIL_Y + 3.9, RAIL_Z + 1.55), (2.2, 0.52, 0.10), "wood_light", bevel=0.015)
        mb.box((bx, RAIL_Y + 4.12, RAIL_Z + 1.92), (2.2, 0.08, 0.44), "wood_light", bevel=0.01)
        for dx in (-0.85, 0.85):
            mb.box((bx + dx, RAIL_Y + 3.9, RAIL_Z + 1.30), (0.10, 0.44, 0.42), "metal_dark")
    # Back fence along platform
    mb.box((sx + 1.0, RAIL_Y + 4.62, RAIL_Z + 1.70), (25.6, 0.10, 1.20), "wood_dark", bevel=0.01)

    # Distinctive Retro Wooden Shiomi Station Building facing coastal road (x=10, y=9.0)
    bz = get_height(sx, 9.0)
    # Stone paved forecourt apron + raised foundation
    mb.box((sx, 7.6, bz - 0.06), (11.2, 4.6, 0.22), "stone", bevel=0.02)
    mb.box((sx, 9.0, bz + 0.16), (9.4, 4.3, 0.48), "stone", bevel=0.025)
    mb.box((sx, 9.0, bz + 2.15), (9.0, 4.0, 3.65), "wall_cream", bevel=0.03, subdiv_cuts=1)
    mb.box((sx, 9.0, bz + 0.95), (9.08, 4.08, 1.25), "wood_light", bevel=0.02)
    for px in (sx - 4.45, sx - 1.65, sx + 1.65, sx + 4.45):
        mb.box((px, 6.96, bz + 2.15), (0.18, 0.18, 3.65), "wood_dark", bevel=0.01)
    mb.door_unit((sx, 7.00, bz + 0.40), 2.3, 2.35, "-Y", "wood_dark", "door_wood", "window_glass", sliding=True)
    for dx in (-3.0, 3.0):
        mb.window_unit((sx + dx, 7.00, bz + 2.15), 1.85, 1.38, "-Y", "wood_dark", "window_glass", "trim_white", mullions=(2, 1))
    z_st_pk = add_kirizuma_roof(mb, sx, 9.0, bz + 3.95, 9.0, 4.0, 28.0, "roof_teal", "wall_cream", "wood_dark", 0.80, 0.85)
    # Small roof ridge ventilation turret so station reads instantly as a landmark
    mb.box((sx, 9.0, z_st_pk + 0.28), (2.4, 0.95, 0.62), "trim_white", bevel=0.015)
    add_kirizuma_roof(mb, sx, 9.0, z_st_pk + 0.56, 2.4, 0.95, 22.0, "roof_teal", "wall_cream", "wood_dark", 0.22, 0.22, tile_ribs=False, gutter_mat=None)
    # Grand projecting gabled entrance portico + round station clock over front door
    mb.box((sx, 6.25, bz + 3.10), (3.8, 1.85, 0.16), "trim_white", bevel=0.02)
    add_kirizuma_roof(mb, sx, 6.25, bz + 3.18, 3.8, 1.85, 30.0, "roof_teal", "wall_cream", "wood_dark", 0.35, 0.35, ridge_along_x=False, tile_ribs=False, gutter_mat=None)
    for dx in (-1.65, 1.65):
        mb.box((sx + dx, 5.50, bz + 1.62), (0.18, 0.18, 2.95), "wood_dark", bevel=0.015)
    # Round station clock on portico gable
    mb.cylinder((sx, 5.26, bz + 3.88), 0.42, 0.12, "metal_dark", segs=14, rot_euler=(math.pi * 0.5, 0.0, 0.0))
    mb.cylinder((sx, 5.21, bz + 3.88), 0.34, 0.08, "trim_white", segs=14, rot_euler=(math.pi * 0.5, 0.0, 0.0))

    # Station sign planes with custom property `text`
    for sname, pos, size, text in (
        ("sign_station_platform", (10.2, RAIL_Y + 3.2, RAIL_Z + 3.45), (2.1, 0.08, 0.60), "しおみ"),
        ("sign_station_front", (sx, 5.22, bz + 3.12), (2.6, 0.09, 0.66), "汐見駅"),
    ):
        smb = MeshBuilder(sname)
        smb.box((0.0, 0.0, 0.0), size, "trim_white", bevel=0.01)
        sobj = smb.to_object(sname, collection=col, location=pos)
        sobj["text"] = text
        objs.append(sobj)

    # Charming Enoden-style 1-car coastal tram stopped at Shiomi Station (x=11, y=RAIL_Y)
    tx, ty, tz = 11.5, RAIL_Y, RAIL_Z + 0.30
    mb.box((tx, ty, tz + 0.42), (11.8, 2.25, 0.55), "metal_dark", bevel=0.04)  # bogie frame
    for wx in (-4.0, -2.6, 2.6, 4.0):
        for wy in (-0.56, 0.56):
            mb.cylinder((tx + wx, ty + wy, tz + 0.25), 0.34, 0.12, "rail_steel", segs=12, rot_euler=(math.pi * 0.5, 0.0, 0.0))
    mb.box((tx, ty, tz + 1.30), (12.6, 2.48, 1.35), "tram_green", bevel=0.08)   # lower body
    mb.box((tx, ty, tz + 2.45), (12.5, 2.44, 1.05), "tram_cream", bevel=0.08)   # upper window band
    mb.box((tx, ty, tz + 3.05), (12.4, 2.30, 0.32), "concrete", bevel=0.10)     # rounded roof
    # Windows along both sides & front/back
    for wx in (-4.4, -2.6, -0.8, 0.8, 2.6, 4.4):
        for face, wy in (("-Y", ty - 1.22), ("+Y", ty + 1.22)):
            mb.window_unit((tx + wx, wy, tz + 2.38), 1.15, 0.88, face, "metal_dark", "window_glass", None, mullions=(0, 0))
    for face, ex in (("-X", tx - 6.26), ("+X", tx + 6.26)):
        mb.window_unit((ex, ty, tz + 2.40), 1.65, 0.85, face, "metal_dark", "window_glass", None, mullions=(1, 0))
    # Roof diamond pantograph reaching overhead contact wire
    mb.tube([Vector((tx - 0.5, ty, tz + 3.22)), Vector((tx - 0.9, ty, tz + 4.1)), Vector((tx, ty, tz + 4.82))], 0.03, "metal_dark", 5)
    mb.tube([Vector((tx + 0.5, ty, tz + 3.22)), Vector((tx + 0.9, ty, tz + 4.1)), Vector((tx, ty, tz + 4.82))], 0.03, "metal_dark", 5)
    mb.box((tx, ty, tz + 4.84), (0.14, 1.25, 0.05), "metal_grey")
    # Warm glowing tram headlights
    hl_mb = MeshBuilder("lamp_tram_headlights")
    for ex in (tx - 6.32, tx + 6.32):
        hl_mb.cylinder((ex, ty, tz + 1.35), 0.16, 0.08, "lamp_glow", segs=10, rot_euler=(0.0, math.pi * 0.5, 0.0))
    objs.append(hl_mb.to_object("lamp_tram_headlights", collection=col))
    return objs


def build_roads_and_rail(col) -> list:
    mb = MeshBuilder("roads_and_rail")
    _add_coastal_road(mb)
    _add_shrine_stairway(mb)
    extra_objs = _add_railway_and_crossing(mb, col)
    extra_objs.extend(_add_station_and_tram(mb, col))
    main_obj = mb.to_object("roads_and_rail", collection=col)
    return [main_obj] + extra_objs
