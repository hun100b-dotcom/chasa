"""차사 로우폴리 3D 공용 도구 (Blender 5.x, 파이썬 bpy).
왜 코드로 만드나: 스크립트 하나로 같은 모델을 언제든 다시 뽑고, 크기·기준점·이름 규칙을 한 곳에서 지키기 위해서다.
규약(코드·QA팀 요청): 형식 GLB, 1유닛=1m, 원점=바닥 한가운데, 정면=+Z, 위=+Y, 재질은 베이스컬러만(텍스처 없음),
소품 하나당 삼각형 2천 이하. Blender 안에서는 Z가 위이고 정면이 -Y이며, 내보낼 때 glTF 규약(+Y 위, +Z 정면)으로 바뀐다.
"""
import bpy, bmesh, math, os, random
from mathutils import Matrix, Euler, Vector

PAL = {  # 팔레트 토큰(docs/art/palette-tokens.json)을 3D용으로 옮긴 것
    "night": "#16213E", "ink": "#2A2A38", "tile": "#2A2A38", "hanji": "#F3E7D3", "red": "#E85C41", "gold": "#D4A94E",
    "teal": "#4FA8A0", "chain": "#BFE8FF", "cheondo": "#5FE3C0", "wood": "#6B4A2E", "wood_dark": "#4A3322",
    "pillar": "#7A3F2C", "mud": "#C9B38A", "thatch": "#B89A55", "stone": "#8A8A82", "stone_dark": "#666660",
    "jar": "#7A4A2E", "leaf": "#3F6B4E", "leaf_dark": "#2F5440", "bark": "#5A3E2A", "water": "#2B3A66",
    "soul_fresh": "#BFE8FF", "soul_day": "#FFCC55", "soul_old": "#A5472E", "soul_lump": "#9A5CFF",
    "ground": "#6F7B5B", "robe": "#586080", "sagat": "#8A7448", "old_skin": "#B58E70", "hull": "#3B3F52", "beard": "#D8D0C0", "hat": "#14141F", "face": "#0A0A12", "cloth": "#232338", "road": "#A8946B", "skin": "#D9B79B", "blue_cloth": "#3E64B0", "yellow_cloth": "#E8C15A",
}
_mats = {}

def hex2rgb(h):
    h = PAL.get(h, h).lstrip("#")
    # sRGB -> 선형(Blender 내부는 선형 색을 쓴다)
    f = lambda c: (c / 255) ** 2.2
    return tuple(f(int(h[i:i + 2], 16)) for i in (0, 2, 4)) + (1,)

def mat(name, emit=0.0):
    key = (name, emit)
    if key in _mats: return _mats[key]
    m = bpy.data.materials.new(f"M_{name}" + ("_glow" if emit else ""))
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = hex2rgb(name)
    b.inputs["Roughness"].default_value = 0.9
    if emit:
        b.inputs["Emission Color"].default_value = hex2rgb(name)
        b.inputs["Emission Strength"].default_value = emit
    _mats[key] = m
    return m

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _mats.clear()

def _obj(name, bm, material, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    mesh = bpy.data.meshes.new(name)
    M = Matrix.Translation(loc) @ Euler(rot).to_matrix().to_4x4() @ Matrix.Diagonal((*scale, 1))
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    bm.to_mesh(mesh); bm.free()
    o = bpy.data.objects.new(name, mesh)
    o.data.materials.append(mat(material) if isinstance(material, str) else material)
    bpy.context.collection.objects.link(o)
    return o

def box(name, size, loc, material, rot=(0, 0, 0)):
    """loc = 상자 중심."""
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1)
    return _obj(name, bm, material, loc, rot, size)

def cyl(name, r1, r2, h, base, material, segs=8, rot=(0, 0, 0)):
    """아래 반지름 r1, 위 반지름 r2, 높이 h. base = 바닥 중심. r2=0이면 원뿔."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs, radius1=r1, radius2=r2, depth=h)
    bmesh.ops.translate(bm, vec=(0, 0, h / 2), verts=bm.verts)
    return _obj(name, bm, material, base, rot)

def sphere(name, r, center, material, segs=7, rings=5, scale=(1, 1, 1), rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=r)
    return _obj(name, bm, material, center, rot, scale)

def prism(name, w, d, h, base, material, rot=(0, 0, 0), ridge_cut=0.0):
    """맞배지붕 모양 삼각기둥. 용마루가 X축을 따라가고 w=길이, d=폭, h=높이. base=바닥 중심."""
    bm = bmesh.new()
    x, y = w / 2, d / 2
    v = [bm.verts.new(p) for p in [(-x, -y, 0), (x, -y, 0), (x, y, 0), (-x, y, 0), (-x, 0, h), (x, 0, h)]]
    for f in [(0, 3, 2, 1), (0, 1, 5, 4), (2, 3, 4, 5), (0, 4, 3), (1, 2, 5)]:
        bm.faces.new([v[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _obj(name, bm, material, base, rot)

def pyramid(name, w, d, h, base, material, rot=(0, 0, 0), top=0.0):
    """사각뿔대(top>0이면 윗면 비율). 우진각 지붕·초가 지붕에 쓴다."""
    bm = bmesh.new()
    x, y = w / 2, d / 2
    tx, ty = x * top, y * top
    pts = [(-x, -y, 0), (x, -y, 0), (x, y, 0), (-x, y, 0), (-tx, -ty, h), (tx, -ty, h), (tx, ty, h), (-tx, ty, h)]
    v = [bm.verts.new(p) for p in pts]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    for f in faces: bm.faces.new([v[i] for i in f])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _obj(name, bm, material, base, rot)

def join(name, objs):
    for o in bpy.context.view_layer.objects: o.select_set(False)
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    o.name = name; o.data.name = name
    return o

def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)

def bounds(o):
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi

def export(o, path, apply=True):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    for x in bpy.context.view_layer.objects: x.select_set(False)
    o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_apply=apply, export_yup=True,
                              export_materials="EXPORT", export_cameras=False, export_lights=False)

def setup_render(ortho, center, elev=50, size=(720, 540), sun_dir=(0.5, -0.4, -1), ground=True, ground_size=40):
    """로스트아크식 50° 내려다보는 직교 카메라 미리보기. 정면(-Y 쪽)에서 본다."""
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE" if False else "CYCLES"
    sc.cycles.samples = 24; sc.cycles.device = "CPU"; sc.cycles.use_denoising = False
    sc.render.resolution_x, sc.render.resolution_y = size
    sc.render.film_transparent = False
    w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.32, 0.38, 0.55, 1); bg.inputs[1].default_value = 1.0
    if ground:
        g = box("ground", (ground_size, ground_size, 0.1), (center[0], center[1], -0.05), "ground")
    cam = bpy.data.cameras.new("cam"); cam.type = "ORTHO"; cam.ortho_scale = ortho
    co = bpy.data.objects.new("cam", cam); bpy.context.collection.objects.link(co)
    e = math.radians(elev); d = 60
    co.location = (center[0], center[1] - d * math.cos(e), center[2] + d * math.sin(e))
    co.rotation_euler = (math.radians(90 - elev), 0, 0)
    cam.clip_end = 300
    sc.camera = co
    sun = bpy.data.lights.new("sun", "SUN"); sun.energy = 4.5; sun.angle = math.radians(18)
    so = bpy.data.objects.new("sun", sun); bpy.context.collection.objects.link(so)
    so.rotation_euler = Euler((math.radians(52), 0, math.radians(-28)))
    bpy.context.view_layer.update()

def render(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def limb(name, a, b, r1, r2, material, segs=6):
    """점 a에서 점 b까지 이어지는 원뿔 기둥(팔·장대). 방향은 Z축을 a→b로 돌려서 맞춘다."""
    a, b = Vector(a), Vector(b); d = b - a
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    return cyl(name, r1, r2, d.length, tuple(a), material, segs, rot=tuple(q.to_euler()))
