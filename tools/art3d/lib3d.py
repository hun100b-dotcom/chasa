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
    "soul_fresh": "#BFE8FF", "soul_day": "#FFCC55", "soul_old": "#6E5446", "soul_lump": "#9A5CFF",
    "ground": "#6F7B5B", "dead": "#6B5E50", "reed_top": "#8A6B4A", "silver": "#D8D0C0", "pine": "#2F5A44", "pine_light": "#3F7455", "zelkova": "#6E9B4F", "zelkova_dark": "#4F7A3B", "bamboo": "#6F9A4A", "bamboo_leaf": "#4F7F3A", "reed": "#B4A66A", "berry": "#B53A4A", "iron": "#3A3A44", "slope_top": "#9CC25F", "slope_side": "#5A4630", "slope_line": "#3E5A2C", "cliff_light": "#B4B2BC", "cliff_dark": "#4E5264", "robe": "#586080", "sagat": "#8A7448", "old_skin": "#B58E70", "hull": "#3B3F52", "beard": "#D8D0C0", "hat": "#14141F", "face": "#0A0A12", "cloth": "#232338", "road": "#A8946B", "skin": "#D9B79B", "blue_cloth": "#3E64B0", "yellow_cloth": "#E8C15A",
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
    # 합칠 때 첫 오브젝트에 UV 칸이 없으면 다른 조각(물면 등)의 UV가 버려진다 → 하나라도 UV가 있으면 모두에 빈 UV 칸을 만들어 둔다
    if any(len(o.data.uv_layers) for o in objs):
        for o in objs:
            if not len(o.data.uv_layers): o.data.uv_layers.new(name="UVMap")
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
    for c in o.children_recursive: c.select_set(True)   # 빈 오브젝트(광원 위치)도 함께 내보낸다
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_apply=apply, export_yup=True,
                              export_materials="EXPORT", export_cameras=False, export_lights=False, export_extras=True)

def setup_render(ortho, center, elev=50, size=(720, 540), sun_dir=(0.5, -0.4, -1), ground=True, ground_size=40, night=False):
    """50° 내려다보는 원근 카메라(a안) 미리보기. 정면(-Y 쪽)에서 본다."""
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE" if False else "CYCLES"
    sc.cycles.samples = 24; sc.cycles.device = "CPU"; sc.cycles.use_denoising = False
    sc.render.resolution_x, sc.render.resolution_y = size
    sc.render.film_transparent = False
    w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.05, 0.07, 0.16, 1) if night else (0.32, 0.38, 0.55, 1); bg.inputs[1].default_value = 1.0
    if ground:
        g = box("ground", (ground_size, ground_size, 0.1), (center[0], center[1], -0.05), "ground")
    cam = bpy.data.cameras.new("cam"); cam.type = "ORTHO"; cam.ortho_scale = ortho
    co = bpy.data.objects.new("cam", cam); bpy.context.collection.objects.link(co)
    e = math.radians(elev); d = 60
    co.location = (center[0], center[1] - d * math.cos(e), center[2] + d * math.sin(e))
    co.rotation_euler = (math.radians(90 - elev), 0, 0)
    cam.clip_end = 300
    sc.camera = co
    sun = bpy.data.lights.new("sun", "SUN"); sun.energy = 1.2 if night else 4.5; sun.angle = math.radians(18)
    so = bpy.data.objects.new("sun", sun); bpy.context.collection.objects.link(so)
    so.rotation_euler = Euler((math.radians(52), 0, math.radians(-28)))
    if night:
        for ob in list(bpy.context.scene.objects):
            if ob.type == 'EMPTY' and ob.name.startswith('Light_'):
                ld = bpy.data.lights.new(ob.name + '_L', 'POINT'); ld.energy = 600; ld.color = hex2rgb(ob['color'])[:3]; ld.shadow_soft_size = 0.2
                lo = bpy.data.objects.new(ob.name + '_L', ld); bpy.context.collection.objects.link(lo); lo.parent = ob
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


def light_empty(parent, name, pos, color, intensity=1.0, range_m=8.0, flicker=False, kind="point"):
    """광원 위치를 빈 오브젝트로 표시한다. 이름과 추가 속성(extras)으로 코드팀이 광원을 만든다."""
    e = bpy.data.objects.new(name, None); e.empty_display_type = "SPHERE"; e.empty_display_size = 0.1
    bpy.context.collection.objects.link(e)
    e.location = pos; e.parent = parent
    e["light_type"] = kind; e["color"] = color; e["intensity"] = intensity; e["range_m"] = range_m; e["flicker"] = 1 if flicker else 0
    return e


def mat_alpha(name, alpha=0.5, emit=0.0):
    """반투명 재질(혼의 겉껍질 등). 베이스컬러+알파만 쓴다(텍스처 없음). glTF에는 alphaMode BLEND로 나간다.
    발광(emit)이 있으면 같은 색으로 은은히 빛난다. 유니티에서는 투명 정렬이 필요하니 겉껍질 하나만 이 재질을 쓰고 속(핵)은 불투명 발광으로 둔다."""
    key = (name, emit, "alpha", alpha)
    if key in _mats: return _mats[key]
    m = bpy.data.materials.new(f"M_{name}_shell")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = hex2rgb(name)
    b.inputs["Roughness"].default_value = 0.6
    b.inputs["Alpha"].default_value = alpha
    if emit:
        b.inputs["Emission Color"].default_value = hex2rgb(name)
        b.inputs["Emission Strength"].default_value = emit
    for attr, val in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
        try: setattr(m, attr, val)
        except Exception: pass
    m["alpha"] = alpha; m["emit"] = emit; m["hex"] = PAL.get(name, name)
    _mats[key] = m
    return m


def lathe(name, rings, segs, material, scale=(1, 1, 1), loc=(0, 0, 0), rot=(0, 0, 0), fn=None, skip=None, caps=(True, True)):
    """선반으로 깎은 몸체. rings=[(높이 z, 반지름 r), ...] 아래→위. 각 고리를 segs각형으로 둘러 면을 잇는다.
    fn(i, k, th, z, r) -> (r, z): 고리 i의 k번째 점의 반지름·높이를 비틀어 주름·물결을 만든다. skip(i, k): 그 칸의 면을 비워 트임을 낸다.
    각도 th=0은 +X, 앞(-Y)은 th=-90°. 반지름 0인 고리는 한 점으로 모여 뾰족해진다."""
    bm = bmesh.new(); grid = []
    for i, (z, r) in enumerate(rings):
        row = []
        for k in range(segs):
            th = 2 * math.pi * k / segs
            rr, zz = fn(i, k, th, z, r) if fn else (r, z)
            row.append(bm.verts.new((rr * math.cos(th), rr * math.sin(th), zz)))
        grid.append(row)
    for i in range(len(rings) - 1):
        for k in range(segs):
            k2 = (k + 1) % segs
            if skip and skip(i, k): continue
            try: bm.faces.new([grid[i][k], grid[i][k2], grid[i + 1][k2], grid[i + 1][k]])
            except ValueError: pass
    if caps[0] and rings[0][1] > 0:
        try: bm.faces.new(list(reversed(grid[0])))
        except ValueError: pass
    if caps[1] and rings[-1][1] > 0:
        try: bm.faces.new(grid[-1])
        except ValueError: pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _obj(name, bm, material, loc, rot, scale)


def chain_pts(name, pts, r1, r2, material, segs=5):
    """점들을 이은 가는 곡선 줄(갓끈·꼬리·머리카락). 앞 점에서 뒤 점으로 갈수록 r1→r2로 가늘어진다."""
    out = []; n = len(pts) - 1
    for i in range(n):
        a = r1 + (r2 - r1) * i / n; b = r1 + (r2 - r1) * (i + 1) / n
        out.append(limb(f"{name}{i}", pts[i], pts[i + 1], a, b, material, segs))
    return out


def mat_water(deep=False):
    """흐르는 물 재질: 알베도(RGBA 반복 그림)+노멀 그림, 알파 블렌드, 거칠기 0.06. 그림은 assets3d/terrain/water_*.png(개울과 같은 그림, 큰 강은 어둡게 한 _deep).
    glTF로 나가면 baseColorTexture·normalTexture·alphaMode BLEND가 된다(REPEAT 샘플러)."""
    key = ("water_tex", deep)
    if key in _mats: return _mats[key]
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets3d", "terrain")
    m = bpy.data.materials.new("M_water_deep" if deep else "M_water"); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.06
    ta = nt.nodes.new("ShaderNodeTexImage"); ta.image = bpy.data.images.load(os.path.join(d, "water_albedo_deep.png" if deep else "water_albedo.png")); ta.extension = "REPEAT"
    tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = bpy.data.images.load(os.path.join(d, "water_normal.png")); tn.image.colorspace_settings.name = "Non-Color"; tn.extension = "REPEAT"
    nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = 0.8
    nt.links.new(ta.outputs["Color"], b.inputs["Base Color"]); nt.links.new(ta.outputs["Alpha"], b.inputs["Alpha"])
    nt.links.new(tn.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    for attr, val in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
        try: setattr(m, attr, val)
        except Exception: pass
    _mats[key] = m
    return m

def water_plane(name, x0, y0, w, h, z, deep=False, tile_m=4.0):
    """물면 판 하나: 타일 안 좌표 (x0,y0)~(x0+w,y0+h), 높이 z. uv는 월드 미터/tile_m, 흐름은 타일의 서→동(+X)이라 줄무늬가 X로 눕게 u·v를 바꿔 쓴다."""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new("UVMap")
    vs = [bm.verts.new((x0, y0, z)), bm.verts.new((x0 + w, y0, z)), bm.verts.new((x0 + w, y0 + h, z)), bm.verts.new((x0, y0 + h, z))]
    f = bm.faces.new(vs)
    for lp in f.loops: p = lp.vert.co; lp[uvl].uv = (p.y / tile_m, -p.x / tile_m)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _obj(name, bm, mat_water(deep))
