"""Core solid bmesh geometry helpers for Shiomi-cho.

Every helper produces closed, watertight geometry with outward normals,
optional edge bevels for cel-shading highlights, and 30-deg auto-smooth.
"""

import math
import bpy
import bmesh
from mathutils import Matrix, Vector, Euler
from lib.materials import get_mat


def ensure_collection(name: str, parent=None) -> bpy.types.Collection:
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        target = parent if parent is not None else bpy.context.scene.collection
        target.children.link(col)
    return col


def apply_auto_smooth(mesh: bpy.types.Mesh, angle_deg: float = 30.0) -> None:
    if len(mesh.polygons) == 0:
        return
    mesh.shade_smooth()
    mesh.set_sharp_from_angle(angle=math.radians(angle_deg))


def _xform_verts(verts, mat: Matrix) -> None:
    for v in verts:
        v.co = mat @ v.co


class MeshBuilder:
    """Fast multi-material bmesh accumulator for solid architectural geometry."""

    def __init__(self, name: str = "mesh"):
        self.name = name
        self.bm = bmesh.new()
        self.mat_names: list[str] = []
        self._mat_map: dict[str, int] = {}

    def mat_idx(self, mat_name: str) -> int:
        idx = self._mat_map.get(mat_name)
        if idx is None:
            idx = len(self.mat_names)
            self.mat_names.append(mat_name)
            self._mat_map[mat_name] = idx
        return idx

    def _tag_faces(self, geom, mi: int) -> list:
        faces = [g for g in geom if isinstance(g, bmesh.types.BMFace)]
        for f in faces:
            f.material_index = mi
        return faces

    def box(
        self,
        center,
        size,
        mat: str,
        bevel: float = 0.0,
        rot_euler=(0.0, 0.0, 0.0),
        subdiv_cuts: int = 0,
    ) -> None:
        """Add a solid box (center xyz, full dimensions sx,sy,sz)."""
        sx, sy, sz = size
        if sx <= 1e-5 or sy <= 1e-5 or sz <= 1e-5:
            return
        mi = self.mat_idx(mat)
        ret = bmesh.ops.create_cube(self.bm, size=1.0)
        verts = ret["verts"]
        scale_m = Matrix.Diagonal((sx, sy, sz, 1.0))
        _xform_verts(verts, scale_m)

        if bevel > 0.0 and min(sx, sy, sz) >= 0.09:
            max_b = min(sx, sy, sz) * 0.35
            b = min(bevel, max_b)
            edges = list({e for v in verts for e in v.link_edges})
            res = bmesh.ops.bevel(
                self.bm,
                geom=edges,
                offset=b,
                offset_type="OFFSET",
                segments=1,
                profile=0.5,
                affect="EDGES",
                clamp_overlap=True,
            )
            verts = [v for v in (set(verts) | set(res.get("verts", []))) if v.is_valid]
            for f in res.get("faces", []):
                if f.is_valid:
                    f.material_index = mi

        all_faces = list({f for v in verts if v.is_valid for f in v.link_faces if f.is_valid})
        for f in all_faces:
            f.material_index = mi

        # Transform BEFORE subdividing so any newly generated interior vertices
        # are already placed in final coordinates (never stranded at origin).
        rot_m = Euler(rot_euler, "XYZ").to_matrix().to_4x4()
        tr_m = Matrix.Translation(Vector(center)) @ rot_m
        _xform_verts(verts, tr_m)

        if subdiv_cuts > 0:
            edges = list({e for f in all_faces if f.is_valid for e in f.edges if e.is_valid})
            res = bmesh.ops.subdivide_edges(
                self.bm, edges=edges, cuts=subdiv_cuts, use_grid_fill=True
            )
            for key in ("geom", "geom_inner", "geom_split"):
                for g in res.get(key, []):
                    if isinstance(g, bmesh.types.BMFace) and g.is_valid:
                        g.material_index = mi

    def cylinder(
        self,
        center,
        radius: float,
        height: float,
        mat: str,
        segs: int = 12,
        radius_top: float | None = None,
        rot_euler=(0.0, 0.0, 0.0),
    ) -> None:
        r2 = radius if radius_top is None else radius_top
        mi = self.mat_idx(mat)
        ret = bmesh.ops.create_cone(
            self.bm,
            cap_ends=True,
            cap_tris=False,
            segments=segs,
            radius1=radius,
            radius2=r2,
            depth=height,
        )
        verts = ret["verts"]
        for v in verts:
            for f in v.link_faces:
                f.material_index = mi
        rot_m = Euler(rot_euler, "XYZ").to_matrix().to_4x4()
        _xform_verts(verts, Matrix.Translation(Vector(center)) @ rot_m)

    def icosphere(
        self,
        center,
        radius,
        mat: str,
        subdivisions: int = 2,
        scale=(1.0, 1.0, 1.0),
        rot_euler=(0.0, 0.0, 0.0),
    ) -> list:
        mi = self.mat_idx(mat)
        ret = bmesh.ops.create_icosphere(
            self.bm, subdivisions=subdivisions, radius=radius
        )
        verts = ret["verts"]
        for v in verts:
            for f in v.link_faces:
                f.material_index = mi
        m = (
            Matrix.Translation(Vector(center))
            @ Euler(rot_euler, "XYZ").to_matrix().to_4x4()
            @ Matrix.Diagonal((scale[0], scale[1], scale[2], 1.0))
        )
        _xform_verts(verts, m)
        return verts

    def prism(self, pts_2d: list[tuple[float, float]], z0: float, z1: float, mat: str) -> None:
        """Extrude a closed 2D polygon [(x,y), ...] from z0 to z1 as a watertight solid."""
        if len(pts_2d) < 3 or abs(z1 - z0) < 1e-5:
            return
        mi = self.mat_idx(mat)
        lo, hi = (z0, z1) if z0 < z1 else (z1, z0)
        bot = [self.bm.verts.new((x, y, lo)) for x, y in pts_2d]
        top = [self.bm.verts.new((x, y, hi)) for x, y in pts_2d]
        n = len(pts_2d)
        faces = []
        try:
            faces.append(self.bm.faces.new(list(reversed(bot))))
            faces.append(self.bm.faces.new(top))
        except ValueError:
            return
        for i in range(n):
            j = (i + 1) % n
            try:
                faces.append(self.bm.faces.new((bot[i], bot[j], top[j], top[i])))
            except ValueError:
                pass
        for f in faces:
            f.material_index = mi

    def tube(self, points: list[Vector], radius: float, mat: str, segs: int = 6) -> None:
        """Build a watertight capped tube along 3D points."""
        if len(points) < 2:
            return
        mi = self.mat_idx(mat)
        rings = []
        pts = [Vector(p) for p in points]
        for i, p in enumerate(pts):
            if i == 0:
                tang = (pts[1] - pts[0]).normalized()
            elif i == len(pts) - 1:
                tang = (pts[-1] - pts[-2]).normalized()
            else:
                t1 = (pts[i] - pts[i - 1]).normalized()
                t2 = (pts[i + 1] - pts[i]).normalized()
                tang = (t1 + t2)
                tang = tang.normalized() if tang.length > 1e-5 else t2
            up = Vector((0, 0, 1)) if abs(tang.z) < 0.92 else Vector((1, 0, 0))
            side = tang.cross(up).normalized()
            normal = side.cross(tang).normalized()
            ring = []
            for k in range(segs):
                a = 2.0 * math.pi * k / segs
                offset = (side * math.cos(a) + normal * math.sin(a)) * radius
                ring.append(self.bm.verts.new(p + offset))
            rings.append(ring)

        faces = []
        for i in range(len(rings) - 1):
            r0, r1 = rings[i], rings[i + 1]
            for k in range(segs):
                kn = (k + 1) % segs
                try:
                    faces.append(self.bm.faces.new((r0[k], r0[kn], r1[kn], r1[k])))
                except ValueError:
                    pass
        try:
            faces.append(self.bm.faces.new(list(reversed(rings[0]))))
            faces.append(self.bm.faces.new(rings[-1]))
        except ValueError:
            pass
        for f in faces:
            f.material_index = mi

    def catenary(
        self, p0, p1, sag: float, radius: float, mat: str, steps: int = 10, segs: int = 5
    ) -> None:
        v0, v1 = Vector(p0), Vector(p1)
        pts = []
        for i in range(steps + 1):
            t = i / steps
            p = v0.lerp(v1, t)
            p.z -= 4.0 * sag * t * (1.0 - t)
            pts.append(p)
        self.tube(pts, radius=radius, mat=mat, segs=segs)

    def window_unit(
        self,
        center,
        width: float,
        height: float,
        facing: str,
        mat_frame: str = "window_frame",
        mat_glass: str = "window_glass",
        mat_sill: str | None = "trim_white",
        mullions: tuple[int, int] = (1, 1),
        shutter_mat: str | None = None,
    ) -> None:
        """Solid flush window assembly: frame intersects wall; glass recessed 4.5cm inside frame.

        `center` lies directly ON the exterior wall plane.
        `facing` in {'-Y', '+Y', '-X', '+X'} points outward from the wall.
        """
        cx, cy, cz = center
        ang = {"-Y": 0.0, "+X": math.pi * 0.5, "+Y": math.pi, "-X": -math.pi * 0.5}[facing]
        rot_m = Matrix.Rotation(ang, 4, "Z")

        def place(lx, ly, lz, sx, sy, sz, mat, bev=0.0):
            wpos = Vector((cx, cy, cz)) + (rot_m @ Vector((lx, ly, lz)))
            self.box(wpos, (sx, sy, sz), mat, bevel=bev, rot_euler=(0.0, 0.0, ang))

        fw = 0.065  # frame bar width
        # Outer frame spans ly = +0.05 (embedded inside wall) to ly = -0.065 (protruding)
        f_depth = 0.115
        f_cy = -0.0075
        # Glass sits at ly = -0.020 (thickness 0.03 -> +0.005 inside wall to -0.025 out), recessed 4cm from frame lip
        place(0.0, -0.010, 0.0, width - fw * 1.4, 0.030, height - fw * 1.4, mat_glass)
        # 4 outer frame bars
        place(0.0, f_cy, height * 0.5 - fw * 0.5, width, f_depth, fw, mat_frame, bev=0.008)
        place(0.0, f_cy, -height * 0.5 + fw * 0.5, width, f_depth, fw, mat_frame, bev=0.008)
        place(-width * 0.5 + fw * 0.5, f_cy, 0.0, fw, f_depth, height - fw * 1.8, mat_frame, bev=0.008)
        place(width * 0.5 - fw * 0.5, f_cy, 0.0, fw, f_depth, height - fw * 1.8, mat_frame, bev=0.008)
        # Mullions
        mx, mz = mullions
        for i in range(1, mx + 1):
            lx = -width * 0.5 + width * i / (mx + 1)
            place(lx, -0.032, 0.0, 0.032, 0.040, height - fw * 1.8, mat_frame)
        for j in range(1, mz + 1):
            lz = -height * 0.5 + height * j / (mz + 1)
            place(0.0, -0.032, lz, width - fw * 1.8, 0.040, 0.032, mat_frame)
        # Sill & head drip
        if mat_sill:
            place(0.0, -0.052, -height * 0.5 - 0.020, width + 0.10, 0.14, 0.045, mat_sill, bev=0.008)
            place(0.0, -0.042, height * 0.5 + 0.022, width + 0.08, 0.12, 0.040, mat_sill, bev=0.008)
        # Optional traditional Japanese amado shutter box on one side
        if shutter_mat:
            sw = min(0.32, width * 0.28)
            place(width * 0.5 + sw * 0.5 - 0.01, -0.038, 0.0, sw, 0.095, height + 0.04, shutter_mat, bev=0.01)

    def door_unit(
        self,
        bottom_center,
        width: float,
        height: float,
        facing: str,
        mat_frame: str = "wood_dark",
        mat_door: str = "door_wood",
        mat_glass: str | None = "window_glass",
        sliding: bool = False,
    ) -> None:
        """Solid flush doorway intersecting wall plane with recessed leaf & optional upper glass."""
        cx, cy, cz_bot = bottom_center
        cz = cz_bot + height * 0.5
        ang = {"-Y": 0.0, "+X": math.pi * 0.5, "+Y": math.pi, "-X": -math.pi * 0.5}[facing]
        rot_m = Matrix.Rotation(ang, 4, "Z")

        def place(lx, ly, lz, sx, sy, sz, mat, bev=0.0):
            wpos = Vector((cx, cy, cz)) + (rot_m @ Vector((lx, ly, lz)))
            self.box(wpos, (sx, sy, sz), mat, bevel=bev, rot_euler=(0.0, 0.0, ang))

        fw = 0.075
        place(0.0, -0.012, 0.0, width - fw * 1.2, 0.035, height - fw * 0.6, mat_door)
        # Outer frame embedded +0.05 inside wall, out to -0.07
        place(0.0, -0.010, height * 0.5 - fw * 0.5, width + 0.04, 0.12, fw, mat_frame, bev=0.01)
        place(-width * 0.5 + fw * 0.5, -0.010, 0.0, fw, 0.12, height, mat_frame, bev=0.01)
        place(width * 0.5 - fw * 0.5, -0.010, 0.0, fw, 0.12, height, mat_frame, bev=0.01)
        if mat_glass:
            gh = height * (0.48 if sliding else 0.36)
            gz = height * 0.14
            gw = width - fw * 2.8
            place(0.0, -0.026, gz, gw, 0.022, gh, mat_glass)
            if sliding:
                place(0.0, -0.038, 0.0, 0.045, 0.045, height - fw, mat_frame)
                for k in (-0.25, 0.25):
                    place(width * k, -0.036, gz, 0.025, 0.025, gh, mat_frame)
        # Handle
        hx = 0.06 if sliding else width * 0.32
        place(hx, -0.045, -0.06, 0.03, 0.04, 0.16, "metal_dark")

    def to_object(
        self,
        name: str | None = None,
        collection=None,
        location=(0.0, 0.0, 0.0),
        rot_z: float = 0.0,
        auto_smooth_deg: float = 30.0,
    ) -> bpy.types.Object:
        obj_name = name or self.name
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        mesh = bpy.data.meshes.new(obj_name)
        self.bm.to_mesh(mesh)
        self.bm.free()
        for mname in self.mat_names:
            mesh.materials.append(get_mat(mname))
        apply_auto_smooth(mesh, auto_smooth_deg)
        obj = bpy.data.objects.new(obj_name, mesh)
        obj.location = Vector(location)
        obj.rotation_euler = (0.0, 0.0, rot_z)
        target_col = collection if collection is not None else bpy.context.scene.collection
        target_col.objects.link(obj)
        return obj
