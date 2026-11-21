import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix

# Clear scene
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
col = scene.collection
rng = random.Random(42)

PALETTE = {
    'wall_cream': 0xF3E6CC, 'wall_white': 0xF6F2EA, 'wall_peach': 0xF2CBB0,
    'wall_mint': 0xCFE6D6, 'wall_sky': 0xC9DDF0, 'wood_dark': 0x6B4A36,
    'wood_light': 0xB88A5E, 'roof_blue': 0x3F5F8C, 'roof_teal': 0x3E7D7A,
    'roof_terracotta': 0xB5583F, 'roof_charcoal': 0x4A4E58, 'trim_white': 0xFAFAF5,
    'window_glass': 0x8FB8D9, 'window_frame': 0xE9E3D6, 'door_wood': 0x7A5233,
    'grass': 0x8CC56A, 'grass_dark': 0x5E9E55, 'stone': 0xBDB6A8,
    'stone_dark': 0x8C877E, 'asphalt': 0x7C8088, 'road_line': 0xF5F2E8,
    'concrete': 0xCFCAC0, 'sand': 0xEADBB2, 'cliff_rock': 0xA99C88,
    'leaf_green': 0x6FB04F, 'leaf_light': 0xA6D46A, 'leaf_dark': 0x3F7E43,
    'sakura': 0xF7C6D4, 'bark': 0x6E5444, 'torii_red': 0xD8443A,
    'lighthouse_white': 0xF7F7F2, 'lighthouse_red': 0xD84B3E,
    'boat_white': 0xF4F4EF, 'boat_blue': 0x3C76B8, 'boat_red': 0xC9503F,
    'metal_grey': 0x9AA1AA, 'rail_steel': 0x6E737A, 'pole_wood': 0x7D6A55,
    'noren_indigo': 0x2F4A7A, 'noren_red': 0xB8443C, 'awning_stripe': 0xE46F5F,
    'sign_yellow': 0xF2C84B, 'crossing_yellow': 0xF2C230, 'crossing_black': 0x2B2B2B,
    'vending_red': 0xD94A44, 'lamp_glow': 0xFFF3C4,
}

def srgb_to_lin(c):
    return ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92

MATS = {}
for name, hx in PALETTE.items():
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    r, g, b = ((hx >> 16) & 255) / 255.0, ((hx >> 8) & 255) / 255.0, (hx & 255) / 255.0
    bsdf.inputs["Base Color"].default_value = (srgb_to_lin(r), srgb_to_lin(g), srgb_to_lin(b), 1.0)
    MATS[name] = m

def hill_z(x, y):
    if y < -8:
        return max(-14.0, (y + 8.0) * 0.14 - 0.5)
    if y < 18:
        return 1.2 + max(0.0, (y + 5.0) * 0.07)
    t = min(1.0, (y - 18.0) / 135.0)
    dx = (x + 30.0) / 150.0
    ridge = math.exp(-dx * dx * 1.4)
    return 2.8 + (t ** 1.25) * 52.0 * (0.55 + 0.45 * ridge)

def add_ao_color(mesh, base_ao=0.88, bottom_ao=0.52):
    ca = mesh.color_attributes.new(name="Color", type='BYTE_COLOR', domain='CORNER')
    zs = [v.co.z for v in mesh.vertices]
    zmin, zmax = (min(zs), max(zs)) if zs else (0.0, 1.0)
    span = max(0.01, zmax - zmin)
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            v = mesh.vertices[mesh.loops[li].vertex_index]
            f = max(0.0, min(1.0, (v.co.z - zmin) / span))
            ao = bottom_ao + (base_ao - bottom_ao) * (f ** 0.6)
            ca.data[li].color = (ao, ao, ao, 1.0)

def mk_obj(name, bm, mat_name, loc=(0, 0, 0), rot=(0, 0, 0), extras=None, ao=(0.96, 0.62)):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(MATS[mat_name])
    add_ao_color(mesh, ao[0], ao[1])
    obj = bpy.data.objects.new(name, mesh)
    obj.location = loc
    obj.rotation_euler = rot
    if extras:
        for k, v in extras.items():
            obj[k] = v
    col.objects.link(obj)
    return obj

def box_bm(sx, sy, sz, z0=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0, 0, z0 + sz * 0.5)) @ Matrix.Diagonal((sx, sy, sz, 1)))
    return bm

def cyl_bm(r1, r2, h, segs=12, z0=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs, radius1=r1, radius2=r2, depth=h,
                          matrix=Matrix.Translation((0, 0, z0 + h * 0.5)))
    return bm

# 1. Sculpted terrain + seabed
bm = bmesh.new()
nx, ny = 56, 48
verts = []
for j in range(ny):
    row = []
    y = -115.0 + j * (320.0 / (ny - 1))
    for i in range(nx):
        x = -190.0 + i * (380.0 / (nx - 1))
        z = hill_z(x, y)
        if x > 95 and y < 20 and y > -90:
            z = max(z, 6.5 * math.exp(-((x - 130.0) / 36.0) ** 2))
        row.append(bm.verts.new((x, y, z)))
    verts.append(row)
for j in range(ny - 1):
    for i in range(nx - 1):
        bm.faces.new((verts[j][i], verts[j][i + 1], verts[j + 1][i + 1], verts[j + 1][i]))
mk_obj("Terrain_Hill", bm, "grass", ao=(1.0, 0.72))

# West sandy beach & seabed apron
mk_obj("Beach_Sand", box_bm(58, 34, 1.4, -0.7), "sand", loc=(-98, -14, 0), rot=(0, 0, 0.12))
mk_obj("East_Cliff", cyl_bm(28, 16, 14, 10, -2), "cliff_rock", loc=(128, -22, 0))

# 2. Harbor quay, piers, breakwaters, lighthouse
mk_obj("Harbor_Quay", box_bm(160, 12, 3.2, -2.0), "concrete", loc=(15, -5, 0))
for px in (-26, 22, 58):
    mk_obj(f"Pier_{px}", box_bm(4.5, 24, 2.2, -1.2), "wood_light", loc=(px, -22, 0))

# East curved breakwater + red lighthouse at (58, -98)
eb_pts = [(94, -6), (92, -32), (84, -62), (72, -84), (58, -98)]
for k in range(len(eb_pts) - 1):
    p0, p1 = Vector(eb_pts[k]), Vector(eb_pts[k + 1])
    mid = (p0 + p1) * 0.5
    d = p1 - p0
    mk_obj(f"Breakwater_E_{k}", box_bm(d.length + 1.5, 5.2, 4.4, -2.2), "concrete",
           loc=(mid.x, mid.y, 0), rot=(0, 0, math.atan2(d.y, d.x)))
mk_obj("Lighthouse_Base", cyl_bm(4.2, 3.6, 2.4, 14, -0.6), "concrete", loc=(58, -98, 0))
mk_obj("Lighthouse_Tower", cyl_bm(2.2, 1.4, 11.2, 16, 1.8), "lighthouse_red", loc=(58, -98, 0))
mk_obj("Lighthouse_Band", cyl_bm(1.9, 1.7, 2.2, 16, 6.2), "lighthouse_white", loc=(58, -98, 0))
mk_obj("Lighthouse_Roof", cyl_bm(1.7, 0.2, 1.8, 16, 14.0), "lighthouse_red", loc=(58, -98, 0))
mk_obj("lighthouse_lamp", cyl_bm(1.1, 1.1, 1.2, 14, 12.9), "lamp_glow", loc=(58, -98, 0), ao=(1.0, 1.0))

# West breakwater + small white beacon
mk_obj("Breakwater_W", box_bm(64, 4.4, 3.8, -2.0), "concrete", loc=(-57, -40, 0), rot=(0, 0, -1.16))
mk_obj("West_Beacon", cyl_bm(1.3, 0.9, 6.5, 12, 1.5), "lighthouse_white", loc=(-45, -70, 0))
mk_obj("lamp_beacon_w", cyl_bm(0.65, 0.65, 0.8, 10, 8.0), "lamp_glow", loc=(-45, -70, 0), ao=(1.0, 1.0))

# 3. Coastal road, railway, station, level crossing
mk_obj("Coastal_Road", box_bm(210, 6.0, 0.4, 0), "asphalt", loc=(0, 4, 1.45))
mk_obj("Road_CenterLine", box_bm(200, 0.22, 0.44, 0), "road_line", loc=(0, 4, 1.46))
mk_obj("Rail_Ballast", box_bm(220, 3.8, 0.5, 0), "stone_dark", loc=(0, 12, 2.25))
mk_obj("Rail_Track_S", box_bm(220, 0.14, 0.22, 0), "rail_steel", loc=(0, 11.4, 2.75))
mk_obj("Rail_Track_N", box_bm(220, 0.14, 0.22, 0), "rail_steel", loc=(0, 12.6, 2.75))
mk_obj("Station_Platform", box_bm(18, 3.4, 1.1, 0), "concrete", loc=(10, 15.2, 2.4))
mk_obj("Station_Canopy", box_bm(14, 3.2, 0.28, 3.3), "roof_teal", loc=(10, 15.2, 2.4))
mk_obj("sign_station", box_bm(2.8, 0.12, 0.9, 2.1), "trim_white", loc=(10, 13.7, 2.4),
       extras={"text": "しおみ"})
# Level crossing at x=-25, y=12
for sx in (-28.5, -21.5):
    mk_obj(f"Crossing_Post_{sx}", cyl_bm(0.14, 0.14, 3.6, 8, 0), "crossing_yellow", loc=(sx, 9.6, 2.4))
mk_obj("Crossing_Bar", box_bm(6.5, 0.12, 0.14, 1.3), "crossing_black", loc=(-25, 9.6, 2.4))

# 4. House builder (base course, walls, framed recessed windows, pitched gable roof w/ overhang)
def add_house(idx, x, y, w, d, floors, wall_mat, roof_mat, yaw=0.0, shop=False, sign_txt=None):
    z = hill_z(x, y) - 0.4
    h = floors * 2.8
    mk_obj(f"House_{idx}_Base", box_bm(w + 0.3, d + 0.3, 1.4, -0.6), "stone", loc=(x, y, z), rot=(0, 0, yaw))
    mk_obj(f"House_{idx}_Wall", box_bm(w, d, h, 0.8), wall_mat, loc=(x, y, z), rot=(0, 0, yaw))
    # Gable roof prism with overhang
    ov = 0.75
    rh = 2.2 + (w * 0.12)
    bm = bmesh.new()
    hw, hd = w * 0.5 + ov, d * 0.5 + ov
    z0, z1 = 0.75 + h, 0.75 + h + rh
    v0 = bm.verts.new((-hw, -hd, z0)); v1 = bm.verts.new((hw, -hd, z0))
    v2 = bm.verts.new((hw, hd, z0));   v3 = bm.verts.new((-hw, hd, z0))
    v4 = bm.verts.new((-hw, 0, z1));   v5 = bm.verts.new((hw, 0, z1))
    bm.faces.new((v0, v1, v5, v4)); bm.faces.new((v2, v3, v4, v5))
    bm.faces.new((v0, v4, v3)); bm.faces.new((v1, v2, v5)); bm.faces.new((v3, v2, v1, v0))
    mk_obj(f"House_{idx}_Roof", bm, roof_mat, loc=(x, y, z), rot=(0, 0, yaw))
    # Flush window frame + glass on south face (-y)
    for fl in range(floors):
        wz = 1.6 + fl * 2.7
        for wx in (-w * 0.24, w * 0.24):
            p = Vector((wx, -d * 0.5 - 0.03, wz))
            p.rotate(Matrix.Rotation(yaw, 3, 'Z'))
            mk_obj(f"House_{idx}_WinF_{fl}_{wx:.1f}", box_bm(1.45, 0.12, 1.25, 0), "window_frame",
                   loc=(x + p.x, y + p.y, z + p.z), rot=(0, 0, yaw))
            mk_obj(f"House_{idx}_WinG_{fl}_{wx:.1f}", box_bm(1.22, 0.14, 1.02, 0.11), "window_glass",
                   loc=(x + p.x, y + p.y, z + p.z), rot=(0, 0, yaw))
    if shop:
        mk_obj(f"House_{idx}_Awning", box_bm(w * 0.92, 1.4, 0.25, 3.2), "awning_stripe",
               loc=(x, y - d * 0.5 - 0.6, z), rot=(0.25, 0, yaw))
        mk_obj(f"anim_flag_noren_{idx}", box_bm(2.2, 0.08, 1.1, 2.0),
               "noren_indigo" if idx % 2 == 0 else "noren_red", loc=(x, y - d * 0.5 - 0.35, z))
    if sign_txt:
        mk_obj(f"sign_{idx}", box_bm(2.4, 0.14, 0.85, 3.7), "sign_yellow",
               loc=(x, y - d * 0.5 - 0.25, z), extras={"text": sign_txt})

SHOPS = [
    (-42, 9.5, "汐見食堂"), (-29, 9.5, "かもめ書店"), (-15, 9.5, "潮風珈琲"),
    (-2, 9.5, "海辺のパン屋"), (26, 9.5, "さかな市場"), (40, 9.5, "港の甘味処"),
]
WALLS = ["wall_cream", "wall_white", "wall_peach", "wall_mint", "wall_sky", "wood_light"]
ROOFS = ["roof_blue", "roof_teal", "roof_terracotta", "roof_charcoal"]
for i, (sx, sy, txt) in enumerate(SHOPS):
    add_house(i, sx, sy, 8.2, 6.6, 2, WALLS[i % len(WALLS)], ROOFS[i % len(ROOFS)], 0.0, True, txt)

# Hillside terraced houses
for j in range(18):
    hx = -72 + (j % 6) * 26 + rng.uniform(-5, 5)
    hy = 28 + (j // 6) * 28 + rng.uniform(-5, 5)
    add_house(10 + j, hx, hy, rng.uniform(7.2, 9.6), rng.uniform(6.0, 8.0),
              rng.choice([1, 2, 2, 3]), rng.choice(WALLS), rng.choice(ROOFS), rng.uniform(-0.18, 0.18))

# 5. Hilltop Shrine at (-30, 145)
sz = hill_z(-30, 145)
for ti, ty in enumerate((126, 138)):
    tz = hill_z(-30, ty)
    mk_obj(f"Torii_{ti}_L", cyl_bm(0.32, 0.26, 6.2, 10, 0), "torii_red", loc=(-32.6, ty, tz))
    mk_obj(f"Torii_{ti}_R", cyl_bm(0.32, 0.26, 6.2, 10, 0), "torii_red", loc=(-27.4, ty, tz))
    mk_obj(f"Torii_{ti}_Top", box_bm(7.6, 0.55, 0.55, 5.9), "torii_red", loc=(-30, ty, tz))
    mk_obj(f"Torii_{ti}_Mid", box_bm(6.2, 0.35, 0.35, 4.7), "torii_red", loc=(-30, ty, tz))
add_house(99, -30, 148, 9.5, 7.5, 1, "wood_dark", "roof_charcoal", 0.0)
mk_obj("lamp_shrine_1", box_bm(0.65, 0.65, 0.75, 2.2), "lamp_glow", loc=(-34, 142, sz), ao=(1.0, 1.0))

# 6. Fishing boats (anim_boat_*)
BOATS = [(-18, -28, 0.2, "boat_blue"), (-4, -36, -0.35, "boat_red"), (14, -26, 0.12, "boat_blue"),
         (34, -42, -0.5, "boat_red"), (48, -30, 0.4, "boat_blue")]
for bi, (bx, by, byaw, bmat) in enumerate(BOATS):
    bm = box_bm(3.2, 8.6, 1.4, -0.3)
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0, -0.6, 1.8)) @ Matrix.Diagonal((2.1, 2.8, 1.8, 1)))
    mk_obj(f"anim_boat_{bi}", bm, "boat_white", loc=(bx, by, 0.0), rot=(0, 0, byaw))
    mk_obj(f"anim_boat_{bi}_trim", box_bm(3.35, 8.7, 0.38, 0.55), bmat, loc=(bx, by, 0.0), rot=(0, 0, byaw))

# 7. Clustered lumpy anime trees (anim_tree_*)
TREE_PTS = [(-52, 24, "sakura"), (-10, 26, "leaf_green"), (34, 24, "sakura"), (68, 22, "leaf_dark"),
            (-58, 62, "leaf_green"), (-18, 64, "leaf_light"), (24, 58, "sakura"), (62, 66, "leaf_green"),
            (-42, 134, "sakura"), (-16, 136, "sakura"), (-30, 158, "leaf_dark"), (12, 110, "leaf_green")]
for ti, (tx, ty, lmat) in enumerate(TREE_PTS):
    tz = hill_z(tx, ty)
    mk_obj(f"Tree_Trunk_{ti}", cyl_bm(0.45, 0.28, 4.2, 8, -0.2), "bark", loc=(tx, ty, tz))
    bm = bmesh.new()
    for ox, oy, oz, r in ((0, 0, 5.4, 2.7), (1.7, 0.8, 4.5, 2.0), (-1.6, -0.6, 4.6, 2.1), (0.3, -1.5, 4.8, 1.9)):
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r, matrix=Matrix.Translation((ox, oy, oz)))
    mk_obj(f"anim_tree_{ti}", bm, lmat, loc=(tx, ty, tz), ao=(1.0, 0.58))

# 8. Background mountains & distant islands
for mi, (mx, my, mw, mh) in enumerate(((-120, 340, 260, 120), (140, 380, 300, 150), (-20, 480, 420, 195))):
    mk_obj(f"Bg_Mountain_{mi}", cyl_bm(mw * 0.65, mw * 0.14, mh, 14, -5), "leaf_dark", loc=(mx, my, 0), ao=(0.95, 0.7))
for ii, (ix, iy, ir, ih) in enumerate(((-380, -560, 95, 46), (290, -720, 115, 58))):
    mk_obj(f"Bg_Island_{ii}", cyl_bm(ir, ir * 0.25, ih, 12, -4), "cliff_rock", loc=(ix, iy, 0), ao=(0.95, 0.75))

os.makedirs("public/models", exist_ok=True)
out_path = os.path.abspath("public/models/stub.glb")
bpy.ops.export_scene.gltf(filepath=out_path, export_format='GLB', export_yup=True, export_extras=True, export_vertex_color='ACTIVE')
print("STUB_EXPORTED:", out_path)
