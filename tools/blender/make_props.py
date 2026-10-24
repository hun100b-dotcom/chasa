"""
차사 한옥 소품 절차적 생성 스크립트 (Blender Python).
- 사람이 모델링하지 않고 "코드로" 도형을 쌓아서 소품을 만든다 (절차적 생성).
- 단위는 미터(m). Unity에서 1 = 1m로 읽히므로 크기를 그대로 맞췄다.
- 실행: python -I tools/blender/make_props.py  (bpy 모듈 설치 필요)
- 결과: assets/props/*.glb (게임용) + assets/props/render/*.png (미리보기)
"""
import bpy, bmesh, math, random, os, sys
from mathutils import Vector

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "props"))
os.makedirs(os.path.join(OUT, "render"), exist_ok=True)

# ── 차사 팔레트(밤 남청·먹·한지·붉은 인). 단색 재질만 쓴다(텍스처 없음 → 용량·크레딧 0) ──
PAL = {
    "stone":  (0.17, 0.20, 0.26),   # 청회색 돌
    "stone2": (0.12, 0.14, 0.19),   # 더 어두운 돌(변화용)
    "gi":     (0.11, 0.13, 0.18),   # 먹빛 남청 기와
    "wood":   (0.28, 0.18, 0.11),   # 어두운 갈색 나무
    "straw":  (0.55, 0.47, 0.30),   # 한지/짚 색
    "ink":    (0.05, 0.05, 0.07),   # 먹
    "red":    (0.62, 0.10, 0.12),   # 붉은 인
    "clay":   (0.20, 0.13, 0.10),   # 옹기 흙색
    "hanji":  (0.85, 0.80, 0.66),   # 한지(등불 창호)
}

def srgb(c):  # 색을 Blender 선형 값으로 (보기 좋게 그대로 사용)
    return (*c, 1)

_mats = {}
def mat(name, emit=0.0):
    if name in _mats: return _mats[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = srgb(PAL[name])
    b.inputs["Roughness"].default_value = 0.85
    if emit:
        b.inputs["Emission Color"].default_value = srgb(PAL[name])
        b.inputs["Emission Strength"].default_value = emit
    _mats[name] = m; return m

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _mats.clear()

def finish(objs, mname_list=None):
    """조각들을 하나로 합치고 면을 각지게(로우폴리 느낌) 만든다."""
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.active_object
    for p in o.data.polygons: p.use_smooth = False
    return o

def add(kind, loc, size=(1,1,1), m="stone", rot=(0,0,0), **kw):
    """기본 도형을 만들어 위치·크기·재질을 지정한다. size는 가로·세로·높이(m)."""
    if kind == "cube":   bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    elif kind == "cyl":  bpy.ops.mesh.primitive_cylinder_add(vertices=kw.get("v",8), radius=0.5, depth=1, location=loc)
    elif kind == "cone": bpy.ops.mesh.primitive_cone_add(vertices=kw.get("v",8), radius1=0.5, radius2=kw.get("r2",0), depth=1, location=loc)
    elif kind == "sph":  bpy.ops.mesh.primitive_uv_sphere_add(segments=kw.get("v",10), ring_count=kw.get("rings",6), radius=0.5, location=loc)
    o = bpy.context.active_object
    o.scale = size; o.rotation_euler = [math.radians(a) for a in rot]
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    o.data.materials.append(mat(m))
    return o

def jitter(o, amt, seed):
    """꼭짓점을 살짝 흔들어 손으로 깎은 듯한 불규칙함을 준다."""
    r = random.Random(seed)
    for v in o.data.vertices:
        v.co += Vector((r.uniform(-amt,amt), r.uniform(-amt,amt), r.uniform(-amt,amt)*0.6))

# ───────────────────────── 소품 6종 ─────────────────────────
def stone_wall():          # 돌담 한 칸: 2.0 x 0.5 x 1.0
    r = random.Random(7); parts = []
    y = 0.0; row = 0
    while y < 0.95:
        h = r.uniform(0.2, 0.3); x = -1.0
        while x < 0.99:
            w = r.uniform(0.28, 0.5)
            if row % 2 == 1 and x == -1.0: w *= 0.5      # 홀수 줄은 반 칸 어긋나게 쌓는다(벽돌 쌓기처럼 튼튼해 보임)
            w = min(w, 1.0 - x)
            if 1.0 - (x + w) < 0.2: w = 1.0 - x          # 끝에 자투리가 남으면 마지막 돌이 먹는다
            o = add("cube",(x + w/2, 0, y+h/2),(w-0.03, r.uniform(0.42,0.5), h-0.03),
                    "stone" if r.random()<0.6 else "stone2")
            jitter(o, 0.02, r.randint(0,999)); parts.append(o); x += w
        y += h; row += 1
    # 윗면에 얹은 갓돌
    parts.append(jitter(add("cube",(0,0,1.0),(2.0,0.55,0.12),"stone2"),0.015,3) or bpy.context.active_object)
    return finish(parts)

def jar():                 # 장독: 지름 0.6 x 높이 0.75
    prof = [(0.00,0),(0.20,0),(0.27,0.12),(0.31,0.35),(0.27,0.58),(0.17,0.68),(0.19,0.72),(0.00,0.72)]
    bm = bmesh.new()
    verts_prev = None
    ring_pts = prof
    bpy.ops.mesh.primitive_circle_add(vertices=1)  # 더미 방지
    bpy.ops.object.delete()
    me = bpy.data.meshes.new("jar"); o = bpy.data.objects.new("jar", me)
    bpy.context.collection.objects.link(o)
    N = 12; rings = []
    for (r, z) in prof:
        rings.append([bm.verts.new((r*math.cos(2*math.pi*i/N), r*math.sin(2*math.pi*i/N), z)) for i in range(N)])
    for a, b in zip(rings, rings[1:]):
        for i in range(N):
            try: bm.faces.new((a[i], a[(i+1)%N], b[(i+1)%N], b[i]))
            except ValueError: pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free(); me.materials.append(mat("clay"))
    lid = add("cone",(0,0,0.77),(0.34,0.34,0.1),"ink",v=12,r2=0.3)  # 뚜껑
    return finish([o, lid])

def roof():                # 기와 지붕 조각: 약 2.0 x 1.5 x 0.7 (경사 26°)
    # 먼저 "평평하게" 만든 뒤 마지막에 통째로 기울인다 → 조각끼리 어긋나지 않는다.
    parts = []
    for i in range(7):                       # 7개의 골(암키와 줄)
        x = -0.9 + i*0.3
        for j in range(4):                   # 위아래로 4장씩 겹쳐 놓는다(기와는 처마 쪽이 위로 덮임)
            y = -0.6 + j*0.4
            parts.append(add("cube",(x, y, 0.04 + j*0.02),(0.24, 0.44, 0.05),"gi"))
        parts.append(add("cyl",(x+0.15, 0, 0.1),(0.11, 1.6, 0.11),"gi",rot=(90,0,0),v=6))  # 수키와(볼록한 덮개)
    parts.append(add("cube",(0,0,-0.03),(2.1,1.7,0.06),"wood"))                        # 밑판(서까래 느낌)
    o = finish(parts)
    o.rotation_euler = (math.radians(26),0,0); bpy.ops.object.transform_apply(rotation=True)
    o.location.z = -min(v.co.z for v in o.data.vertices); bpy.ops.object.transform_apply(location=True)
    return o

def lantern():             # 석등: 높이 1.6, 바닥 0.6
    p = [add("cube",(0,0,0.07),(0.6,0.6,0.14),"stone2"),
         add("cyl",(0,0,0.45),(0.2,0.2,0.62),"stone",v=8),
         add("cyl",(0,0,0.82),(0.5,0.5,0.1),"stone2",v=8),
         add("cube",(0,0,1.07),(0.34,0.34,0.4),"hanji"),             # 불 밝히는 화창
         add("cone",(0,0,1.43),(0.78,0.78,0.3),"stone2",v=8),        # 지붕돌
         add("sph",(0,0,1.62),(0.14,0.14,0.14),"stone",v=8,rings=4)] # 보주
    m = mat("hanji", emit=3.0)                                       # 불빛 부분은 스스로 빛남
    p[3].data.materials.clear(); p[3].data.materials.append(m)
    return finish(p)

def fence():               # 싸리 울타리: 2.0 x 0.1 x 1.1 (세로 가지 + 가로대 2)
    r = random.Random(11); p = []
    n = 14
    for i in range(n):
        x = -0.95 + i*(1.9/(n-1)); h = 1.05 + r.uniform(-0.1,0.08)
        p.append(add("cyl",(x,0,h/2),(0.045,0.045,h),"straw",rot=(r.uniform(-3,3),r.uniform(-3,3),0),v=5))
    for z in (0.35, 0.8):
        p.append(add("cyl",(0,0.05,z),(0.05,0.05,2.0),"wood",rot=(0,90,0),v=5))
    return finish(p)

def jangseung():           # 장승: 높이 2.2, 굵기 0.35, 얼굴·붉은 모자
    p = [add("cyl",(0,0,1.0),(0.34,0.34,2.0),"wood",v=8),
         add("cone",(0,0,2.05),(0.42,0.42,0.3),"ink",v=8,r2=0.2),      # 머리 모자
         add("cube",(-0.09,-0.17,1.55),(0.1,0.04,0.06),"hanji"),       # 왼 눈
         add("cube",( 0.09,-0.17,1.55),(0.1,0.04,0.06),"hanji"),       # 오른 눈
         add("cube",(0,-0.17,1.32),(0.12,0.05,0.12),"wood"),           # 코
         add("cube",(0,-0.175,1.1),(0.22,0.04,0.07),"red"),            # 붉은 입
         add("cube",(0,-0.17,0.75),(0.2,0.04,0.45),"red")]            # 붉은 글씨띠(인)
    p.append(add("cube",(0,0,0.05),(0.5,0.5,0.1),"stone2"))           # 받침돌
    return finish(p)

PROPS = {"stone_wall": (stone_wall,"돌담 조각"), "jar": (jar,"장독"), "roof_tile": (roof,"기와 지붕 조각"),
         "stone_lantern": (lantern,"석등"), "wicker_fence": (fence,"싸리 울타리"), "jangseung": (jangseung,"장승")}

# ───────────────────────── 렌더(밤 쿼터뷰) ─────────────────────────
def setup_render(path, size):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"   # 서버엔 그래픽카드가 없어 CPU 렌더(Cycles)를 쓴다
    sc.cycles.samples = 24; sc.cycles.use_denoising = False
    sc.render.resolution_x, sc.render.resolution_y = 640, 640
    sc.render.film_transparent = False
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.03,0.045,0.09,1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    # 바닥(어두운 흙)
    bpy.ops.mesh.primitive_plane_add(size=12, location=(0,0,-0.001))
    g = bpy.context.active_object; g.data.materials.append(mat("ink"))
    # 달빛(차가운 남청) + 따뜻한 보조등
    bpy.ops.object.light_add(type="SUN", rotation=(math.radians(50),0,math.radians(-35)))
    s = bpy.context.active_object; s.data.energy = 3.0; s.data.color = (0.55,0.65,1.0)
    bpy.ops.object.light_add(type="POINT", location=(1.6,-2.0,1.6))
    l = bpy.context.active_object; l.data.energy = 300; l.data.color = (1.0,0.6,0.3)
    # 쿼터뷰 카메라: 고도 50°, 방위 45°, 원근
    bpy.ops.object.camera_add()
    c = bpy.context.active_object; bpy.context.scene.camera = c
    c.data.lens = 50
    el, az, dist = math.radians(50), math.radians(45), max(2.2, max(size)*2.4)
    tz = size[2]*0.45
    c.location = (dist*math.cos(el)*math.sin(az), -dist*math.cos(el)*math.cos(az), dist*math.sin(el)+tz)
    d = Vector((0,0,tz)) - c.location
    c.rotation_euler = d.to_track_quat("-Z","Y").to_euler()
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)

if __name__ == "__main__":
    only = sys.argv[1:] 
    for key,(fn,label) in PROPS.items():
        if only and key not in only: continue
        reset(); o = fn(); o.name = key
        d = o.dimensions; print(f"{key} {label}: {d.x:.2f} x {d.y:.2f} x {d.z:.2f} m, 면 {len(o.data.polygons)}개")
        bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,key+".glb"), export_format="GLB", use_selection=True)
        setup_render(os.path.join(OUT,"render",key+".png"), tuple(d))
