"""필드 5×5 실제 3D 조립 + 밤 조명·안개 렌더. field_5x5.json과 solgogae_village.json을 읽어 GLB 모델을 그대로 배치한다.
화면에 보이는 구역만 불러와 조립한다(전체 640m를 한 번에 올리면 느리다). 어긋남이 보이면 JSON(필드/마을 생성 스크립트)을 고치는 쪽이 원칙이다.
좌표: 필드 x=동·y=북·원점=남서 모서리, rot=반시계 도. 마을 배치표는 (196,60)에 놓는다.
사용: python3 field_scene.py [샷이름 ...]   (샷이름 생략 시 6컷 전부)"""
import sys, os, math, json, time
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
import bpy
from mathutils import Vector, Euler
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
A3 = os.path.join(REPO, "assets3d")
DIRS = [("a1r_", "props"), ("terrain_", "terrain"), ("chunk_", "terrain"), ("nature_", "nature"), ("cover_", "nature"), ("br_", "blackrapids"), ("prop_", "props"), ("hanok_", "hanok"), ("night_", "night"), ("fx_", "fx"), ("weapon_", "weapons"), ("boss_", "boss"), ("soul_", "souls"), ("hero_", "characters")]
FIELD = json.load(open(os.path.join(A3, "layouts", "field_5x5.json"), encoding="utf-8"))
VIL = json.load(open(os.path.join(A3, "layouts", "solgogae_village.json"), encoding="utf-8"))
VX, VY = FIELD["village_offset_m"]

def gpath(name):
    for pre, d in DIRS:
        if name.startswith(pre): return os.path.join(A3, d, name + ".glb")
    raise KeyError(name)

class Lib:
    """같은 GLB는 한 번만 불러 두고 복제해서 쓴다(메시 공유라 가볍다)."""
    def __init__(self): self.t = {}; self.lights = {}
    def get(self, name):
        if name not in self.t:
            before = set(bpy.data.objects)
            bpy.ops.import_scene.gltf(filepath=gpath(name))
            new = [o for o in bpy.data.objects if o not in before]
            empties = [e for e in new if e.type == "EMPTY"]; lights_found = [(Vector(e.location), dict(e)) for e in empties if e.name.startswith("Light_")]   # 합치기 전에 먼저 챙긴다(합치면 옛 오브젝트가 사라짐)
            top = [o for o in new if o.type == "MESH" and o.parent is None]
            if top: m = top[0]
            else:   # 노드 이름으로 나뉜 여러 조각 소품(약장·등롱 등): 부모를 풀어 한 메시로 합친다(보기용)
                ms = [o for o in new if o.type == "MESH"]
                for o in bpy.context.view_layer.objects: o.select_set(False)
                for o in ms: o.select_set(True)
                bpy.context.view_layer.objects.active = ms[0]
                bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM"); bpy.ops.object.join(); m = bpy.context.view_layer.objects.active
            m.rotation_mode = "XYZ"; m.location = (0, 0, -500); m.hide_render = True
            self.lights[name] = lights_found
            for e in empties: e.hide_render = True
            self.t[name] = m
        return self.t[name]

lib = Lib(); placed_lights = []; stats = {"objs": 0}
def add_light(pos, col, inten, rng, flicker, tag=""):
    ld = bpy.data.lights.new("L", "POINT"); ld.energy = 900 * inten; ld.color = hex2rgb(col)[:3]; ld.shadow_soft_size = 0.25
    ob = bpy.data.objects.new("L", ld); bpy.context.collection.objects.link(ob); ob.location = pos
    placed_lights.append({"x": round(pos[0], 2), "y": round(pos[1], 2), "z": round(pos[2], 2), "color": col, "intensity": inten, "range_m": rng, "flicker": bool(flicker), "tag": tag})

def put(name, x, y, z=0.0, rot=0.0, lights=True, scale=1.0):
    t = lib.get(name); o = t.copy(); bpy.context.collection.objects.link(o); o.hide_render = False
    o.location = (x, y, z); o.rotation_euler = (0, 0, math.radians(rot)); stats["objs"] += 1
    if scale != 1.0: o.scale = scale if isinstance(scale, tuple) else (scale,) * 3
    if lights:
        for off, ex in lib.lights.get(name, []):
            r = Euler((0, 0, math.radians(rot))).to_matrix() @ off
            add_light((x + r.x, y + r.y, z + r.z), ex["color"], ex["intensity"], ex["range_m"], ex["flicker"], name)
    return o

def inwin(x, y, win, m=0.0): return win[0] - m <= x <= win[2] + m and win[1] - m <= y <= win[3] + m

COVER_ON = os.environ.get("FS_COVER", "1") == "1"   # 바닥 채움 소품(field_cover.json). 전후 비교용으로 FS_COVER=0 이면 끈다
COVER = json.load(open(os.path.join(A3, "layouts", "field_cover.json"), encoding="utf-8"))["props"] if os.path.exists(os.path.join(A3, "layouts", "field_cover.json")) else []

LIFE_ON = os.environ.get("FS_LIFE", "1") == "1"
LIFE = json.load(open(os.path.join(A3, "layouts", "act1_life.json"), encoding="utf-8"))["props"] if os.path.exists(os.path.join(A3, "layouts", "act1_life.json")) else []

ROUTE_ON = os.environ.get("FS_ROUTE", "1") == "1"   # 처음 10분 길 소품(act1_route.json)·1막 추가 소품(act1_extra.json). 게임에는 build_field_data.py가 field.json에 합쳐 넣는다
ROUTE = [p for n in ("act1_route", "act1_extra") for p in (json.load(open(os.path.join(A3, "layouts", n + ".json"), encoding="utf-8"))["props"] if os.path.exists(os.path.join(A3, "layouts", n + ".json")) else [])]

def build(win):
    """win=(x0,y0,x1,y1) m. 창 안 타일·장식·구조물·마을·밤 소품을 조립한다."""
    x0, y0, x1, y1 = win
    # 땅: 이어진 지형 청크(128m)를 불러 깐다(타일 조각 대신). 강 조각 br_* 칸만 옛 타일 모델을 그대로 놓는다
    for cx in range(max(0, int((x0 - 6) // 128)), min(4, int((x1 + 6) // 128)) + 1):
        for cy in range(max(0, int((y0 - 6) // 128)), min(4, int((y1 + 6) // 128)) + 1):
            put(f"chunk_{cx}_{cy}", cx * 128, cy * 128, 0, 0)
    for t in FIELD["tiles"]:
        if not t["tile"].startswith("br_"): continue
        cx, cy = t["ix"] * 8 + 4, t["iy"] * 8 + 4
        if inwin(cx, cy, win, 6): put(t["tile"], cx, cy, t["z"], t["rot"])
    for p in FIELD["props"]:
        if inwin(p["x"], p["y"], win, 4): put(p["prop"], p["x"], p["y"], p.get("gz", p.get("z", 0) + 0.3), p["rot"])
    if COVER_ON:
        for p in COVER:
            if inwin(p["x"], p["y"], win, 1): put(p["prop"], p["x"], p["y"], 0.3, p["rot"], lights=False)
    if LIFE_ON:   # 1막 생활 소품(act1_life.json): 전후 비교용으로 FS_LIFE=0 이면 끈다
        for p in LIFE:
            if inwin(p["x"], p["y"], win, 1): put(p["prop"], p["x"], p["y"], 0.3, p["rot"], lights=False)
    if ROUTE_ON:
        for p in ROUTE:
            if inwin(p["x"], p["y"], win, 1): put(p["prop"], p["x"], p["y"], 0.3 + p.get("z", 0.0), p.get("rot", 0), lights=False)
    for s in FIELD.get("structures", []):
        if "pieces" in s:
            for q in s["pieces"]:
                if inwin(q["x"], q["y"], win, 6): put(q["piece"], q["x"], q["y"], q["z"] + (0 if q["piece"].startswith("br_") else 0.3), q["rot"])
        elif inwin(s["x"], s["y"], win, 8): put(s["piece"], s["x"], s["y"], s.get("z", 0) + (0 if s["piece"].startswith("br_") else 0.3), s["rot"])
    for b in VIL["buildings"]:
        for q in b["pieces"]:
            if inwin(q["x"] + VX, q["y"] + VY, win, 6): put(q["piece"], q["x"] + VX, q["y"] + VY, q["z"] + 0.3, q["rot"])
    for p in VIL["props"]:
        if inwin(p["x"] + VX, p["y"] + VY, win, 6): put(p["prop"], p["x"] + VX, p["y"] + VY, 0.3, p["rot"])
    # 마을 길(마을 배치표가 따로 깐 3.4m 길·마당. 필드 길 타일과 같은 색)
    if inwin(VX, VY, win, 60):
        box("v_road", (3.4, 52, 0.04), (VX, VY - 2, 0.32), "road"); box("v_plaza", (7, 5, 0.04), (VX + 3.4, VY - 5.5, 0.325), "road")
    # 밤 소품: 마을 길 양쪽 등롱 기둥, 어귀 석등, 서낭당 횃대, 우물 곁 혼불 받침
    decor = [("night_lantern_pole", VX - 2.6, VY - 18 + 9 * i, 0, 0) for i in range(5)] + [("night_lantern_pole", VX + 2.6, VY - 14 + 9 * i, 0, 180) for i in range(5)]
    decor += [("night_stone_lantern", VX - 4.2, VY - 22, 0, 0), ("night_stone_lantern", VX + 4.2, VY - 22, 0, 0), ("night_torch_stand", VX - 8, VY - 19, 0, 0), ("night_soulfire_pedestal", VX + 6.6, VY - 8.2, 0, 0)]
    decor += [("night_torch_stand", 76.5, FIELD["structures"][0]["y"] - 4.5, 0, 0), ("night_torch_stand", 91.5, FIELD["structures"][0]["y"] + 4.5, 0, 0), ("night_soulfire_pedestal", 404 - 6, 288 + 5, 0.62, 0)]
    for n, x, y, z, r in decor:
        if inwin(x, y, win, 6): put(n, x, y, z + 0.3, r)

def world_night():
    sc = bpy.context.scene; w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
    nt = w.node_tree; bg = nt.nodes["Background"]; bg.inputs[0].default_value = (0.03, 0.045, 0.11, 1); bg.inputs[1].default_value = 2.5
    out = nt.nodes["World Output"]
    vs = nt.nodes.new("ShaderNodeVolumeScatter"); vs.inputs["Color"].default_value = (0.55, 0.65, 0.95, 1); vs.inputs["Density"].default_value = float(os.environ.get("FS_FOG","0")); vs.inputs["Anisotropy"].default_value = 0.35
    nt.links.new(vs.outputs[0], out.inputs["Volume"])
    sun = bpy.data.lights.new("moon", "SUN"); sun.energy = float(os.environ.get("FS_MOON","1.3")); sun.color = (0.62, 0.74, 1.0); sun.angle = math.radians(6)
    so = bpy.data.objects.new("moon", sun); bpy.context.collection.objects.link(so); so.rotation_euler = Euler((math.radians(58), 0, math.radians(-35)))

DAY = bool(os.environ.get("FS_DAY"))

def world_day():
    """낮 장면: 파란 하늘빛 + 따뜻한 해(그림자 길이는 밤 달과 비슷한 방향). 점광(등롱)은 그대로 두되 낮에는 거의 안 보인다."""
    sc = bpy.context.scene; w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.42, 0.58, 0.85, 1); bg.inputs[1].default_value = 1.1
    sun = bpy.data.lights.new("sun", "SUN"); sun.energy = 4.2; sun.color = (1.0, 0.95, 0.84); sun.angle = math.radians(4)
    so = bpy.data.objects.new("sun", sun); bpy.context.collection.objects.link(so); so.rotation_euler = Euler((math.radians(50), 0, math.radians(-35)))
    for ob in list(bpy.data.objects):
        if ob.type == "LIGHT" and ob.data.type == "POINT": ob.data.energy *= 0.12

HOUR = os.environ.get("FS_HOUR")   # 게임 시(예: 12.5·18.0·5.5). 있으면 sky_clock.json 키프레임 색으로 낮·저녁놀·새벽 장면을 만든다(색보정 전후 비교용)

def world_hour(h):
    """sky_clock.json 키프레임(아트 하늘 값)에서 그 시각의 빛 색·세기·그늘 색을 읽어 Blender 해와 하늘빛으로 옮긴다.
    왜: 색보정표(LUT)는 '원본 렌더'에 걸어 보아야 전후가 의미 있다 → 시간대별 원본을 같은 장면에서 뽑는다."""
    import json
    ks = json.load(open(os.path.join(A3, "sky", "sky_clock.json")))["keyframes"]; k = min(ks, key=lambda q: abs(q["hour"] - h))
    sc = bpy.context.scene; w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = hex2rgb(k["sky_mid"]); bg.inputs[1].default_value = 0.9 if k["light_intensity"] > 0.8 else 0.6
    sun = bpy.data.lights.new("sun", "SUN"); sun.energy = k["light_intensity"] * 2.8; sun.color = hex2rgb(k["light_color"])[:3]; sun.angle = math.radians(4)
    so = bpy.data.objects.new("sun", sun); bpy.context.collection.objects.link(so)
    low = h < 7 or h > 17     # 새벽·저녁놀은 해가 낮아 그림자가 길다(새벽은 동쪽, 저녁은 서쪽에서)
    so.rotation_euler = Euler((math.radians(76 if low else 50), 0, math.radians(125 if h < 12 else -35)))
    for ob in list(bpy.data.objects):
        if ob.type == "LIGHT" and ob.data.type == "POINT": ob.data.energy *= (0.55 if low else 0.12)

def camera(center, ortho, size, elev=50):
    sc = bpy.context.scene; sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 64
    try: sc.cycles.use_denoising = True; sc.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception: pass
    sc.render.resolution_x, sc.render.resolution_y = size
    cam = bpy.data.cameras.new("cam"); cam.type = "ORTHO"; cam.ortho_scale = ortho; cam.clip_end = 600
    co = bpy.data.objects.new("cam", cam); bpy.context.collection.objects.link(co); e = math.radians(elev); d = 120
    co.location = (center[0], center[1] - d * math.cos(e), center[2] + d * math.sin(e)); co.rotation_euler = (math.radians(90 - elev), 0, 0); sc.camera = co

def camera_persp(loc, target, lens, size):
    """원근 카메라(타이틀·로딩 일러스트용). loc에서 target을 바라본다. 쿼터뷰 게임 화면과 달리 낮게 깔아 극적으로."""
    sc = bpy.context.scene; sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = int(os.environ.get("FS_SAMPLES", "96"))
    try: sc.cycles.use_denoising = True; sc.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception: pass
    sc.render.resolution_x, sc.render.resolution_y = size
    cam = bpy.data.cameras.new("cam"); cam.lens = lens; cam.clip_end = 900; cam.sensor_width = 36
    co = bpy.data.objects.new("cam", cam); bpy.context.collection.objects.link(co); co.location = loc
    d = Vector(target) - Vector(loc); co.rotation_euler = d.to_track_quat("-Z", "Y").to_euler(); sc.camera = co

def orbs(pts, col="#BFE8FF"):
    """떠도는 넋불(작은 발광 구 + 은은한 점광)."""
    for i, (x, y, z) in enumerate(pts):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.07 + 0.02 * (i % 3), location=(x, y, z), segments=12, ring_count=8); o = bpy.context.active_object; o.data.materials.append(mat(col, 6.0))
        add_light((x, y, z), col, 0.18, 4.0, False, "넋불")

def pose(name, x, y, z, rot, action, frame, scale=1.0):
    """리깅된 GLB를 불러 동작의 한 프레임을 굳혀 둔다(여러 캐릭터가 서로 다른 프레임을 쓸 수 있게)."""
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=gpath(name)); new = [o for o in bpy.data.objects if o not in before]
    arm = [o for o in new if o.type == "ARMATURE"][0]; top = arm
    while top.parent: top = top.parent
    ad = arm.animation_data; act = [a for a in bpy.data.actions if a.name == action or a.name.endswith("|" + action) or a.name.startswith(action + ".")]
    if not act: print("동작 없음", action, [a.name for a in bpy.data.actions][:12]); act = []
    if act and ad:
        ad.action = [a for a in act if a.users][0] if any(a.users for a in act) else act[0]
        for t in ad.nla_tracks: t.mute = True
        bpy.context.scene.frame_set(frame); bpy.context.view_layer.update()
        saved = {pb.name: (pb.rotation_quaternion.copy(), pb.location.copy(), pb.scale.copy()) for pb in arm.pose.bones}
        ad.action = None
        for pb in arm.pose.bones: pb.rotation_quaternion, pb.location, pb.scale = saved[pb.name]
    top.rotation_mode = "XYZ"; top.location = (x, y, z); top.rotation_euler = (0, 0, math.radians(rot))
    if scale != 1.0: top.scale = (scale,) * 3
    return top

SHOTS = {
  "cover_field": dict(win=(300, 110, 360, 160), cam=((330, 96, 14), (330, 126, 0.3), 36), size=(1920, 1080), title="보릿들 바닥 채움(쿼터뷰에 가까운 시점)"),
  "cover_q": dict(win=(280, 100, 350, 150), center=(315, 124, 0.3), ortho=34, title="보릿들 바닥 채움(쿼터뷰 50°)"),
  "cover_river": dict(win=(70, 520, 130, 580), center=(98, 548, 0.2), ortho=34, title="검은여울 강변 채움(쿼터뷰 50°)"),
  "cover_road": dict(win=(200, 120, 260, 175), center=(228, 146, 0.3), ortho=34, title="길가·밭머리 채움(쿼터뷰 50°)"),
  "market":  dict(win=(0, 360, 80, 420), center=(36, 390, 0), ortho=46, title="읍터 장터(밤)"),
  "donghun": dict(win=(0, 300, 80, 370), center=(34, 336, 0), ortho=52, title="동헌 터·옥·객사(밤)"),
  "smithy":  dict(win=(200, 38, 250, 84), center=(221, 59, 0), ortho=26, title="대장간(밤)"),
  "jeongja": dict(win=(170, 28, 215, 62), center=(192, 44, 0), ortho=26, title="마을 어귀 정자(밤)"),
  "jumak":   dict(win=(385, 295, 445, 350), center=(414, 322, 0), ortho=40, title="물막이 골 주막(밤)"),
  "gate":   dict(win=(150, 0, 245, 80), center=(196, 42, 0), ortho=50, title="솔고개 어귀(밤)"),
  "village": dict(win=(150, 20, 245, 110), center=(196, 62, 0), ortho=60, title="마을 안(밤)"),
  "barley": dict(win=(250, 70, 470, 220), center=(352, 134, 0), ortho=150, title="보릿들(밤)"),
  "hamlet": dict(win=(280, 100, 370, 200), center=(324, 148, 0), ortho=56, title="보릿들 한가운데 마을(밤)"),
  "stream": dict(win=(380, 325, 430, 360), center=(405, 342, 0), ortho=15, title="개울(가까이)"),
  "mill": dict(win=(370, 310, 430, 372), center=(402, 340, 0), ortho=30, title="개울가 방앗간(밤)"),
  "ruin": dict(win=(540, 500, 630, 620), center=(584, 545, 2.0), ortho=50, title="폐당집 무덤 터(밤)"),
  "plague": dict(win=(60, 410, 140, 500), center=(94, 452, 0), ortho=40, title="검은여울 역병 분위기(밤)"),
  "landmark": dict(win=(300, 100, 390, 180), center=(340, 138, 0), ortho=40, title="길목 랜드마크(밤)"),
  "bridge": dict(win=(40, 410, 130, 500), center=(84, 452, 0), ortho=48, title="검은여울 돌다리(밤)"),
  "naru":   dict(win=(340, 230, 470, 340), center=(404, 290, 0.6), ortho=40, title="나루 영감 보스 자리(밤)"),
  "arena1": dict(win=(360, 245, 450, 335), center=(404, 288, 0.3), ortho=46, title="보스 싸움터 ① 나루 영감 · 나루터(밤)"),
  "arena2": dict(win=(550, 490, 612, 552), center=(580, 521, 2.3), ortho=30, title="보스 싸움터 ② 월화 · 폐당집 굿판(밤)"),
  "arena3": dict(win=(20, 428, 72, 480), center=(46, 453, 0.35), ortho=26, title="보스 싸움터 ③ 서 의원 · 역병막 마당(밤)"),
  "arena1t": dict(win=(360, 245, 450, 335), center=(404, 288, 0.3), ortho=46, title="패턴 예고 ① 삿대 휩쓸기 + 내려찍기"),
  "arena2t": dict(win=(550, 490, 612, 552), center=(580, 521, 2.3), ortho=30, title="패턴 예고 ② 잔이 열린다(3칸)"),
  "arena3t": dict(win=(20, 428, 72, 480), center=(46, 453, 0.35), ortho=26, title="패턴 예고 ③ 번호 낙인(16칸)"),
  "title":  dict(win=(150, 0, 240, 80), cam=((194.0, 29.4, 1.2), (187.0, 38.4, 2.3), 27), size=(1920, 1080), title="타이틀 배경: 밤 서낭당 앞의 차사"),
  "portrait": dict(win=(180, 38, 212, 60), cam=((196.0, 45.7, 1.62), (196.0, 48.0, 1.52), 85), size=(768, 768), title="HUD 초상(차사 가슴 위)"),
  "load_a": dict(win=(160, 10, 240, 100), cam=((196, 16, 3.2), (196, 52, 2.6), 28), size=(1920, 1080), title="로딩 ① 솔고개 마을 어귀"),
  "load_b": dict(win=(370, 255, 450, 335), cam=((388, 262, 2.6), (404, 292, 1.2), 30), size=(1920, 1080), title="로딩 ② 물막이 골 나루"),
  "load_c": dict(win=(540, 490, 625, 590), cam=((571, 514, 4.6), (581, 537, 3.2), 27), size=(1920, 1080), title="로딩 ③ 폐당집 터"),
  "tendo":  dict(win=(170, 30, 230, 90), center=(196, 51, 0), ortho=18, title="천도 이펙트(밤)"),
}


def decal(png, x, y, z, size, tint=None, rot=0.0, w=None, h=None, emit=0.0):
    """그림(알파) 한 장을 땅 위 판(plane)으로 깐다. 보스 싸움터 바닥 무늬·예고 장판용. tint=(r,g,b)면 흰 예고 그림에 색을 입힌다."""
    w = w or size; h = h or size
    bpy.ops.mesh.primitive_plane_add(size=1, location=(x, y, z)); o = bpy.context.active_object; o.scale = (w, h, 1); o.rotation_euler = (0, 0, math.radians(rot))
    m = bpy.data.materials.new("decal"); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(A3, "boss", png)); t.interpolation = "Linear"; t.extension = "CLIP"
    nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"]); b.inputs["Roughness"].default_value = 0.95
    if tint:
        b.inputs["Base Color"].default_value = (*tint, 1); b.inputs["Emission Color"].default_value = (*tint, 1); b.inputs["Emission Strength"].default_value = emit or 2.0
    else:
        nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
        if emit: nt.links.new(t.outputs["Color"], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = emit
    o.data.materials.append(m); return o

ARENA = json.load(open(os.path.join(A3, "layouts", "boss_arenas.json"), encoding="utf-8"))["arenas"]
def arena_scene(key):
    """보스 싸움터 하나를 꾸민다: 바닥 무늬 + 둘레 소품(배치표) + 조명 + 보스. key 끝에 t가 붙으면 패턴 예고 장판도 켠다."""
    tele = key.endswith("t"); aid = {"1": "B01", "2": "B02", "3": "B03"}[key[5]]; a = ARENA[aid]; bx, by = a["boss_pos"]["x"], a["boss_pos"]["y"]; gz = a["ground_z"]
    d = a["decal"]; dz = (0.42 if aid == "B01" else gz) + 0.05
    decal(os.path.basename(d["file"]), bx, by, dz, d["size_m"])
    for p in a["props"]:
        put(p["prop"], p["x"], p["y"], (0.3 if aid == "B01" else 0.0) + (gz if aid != "B01" else 0.0) + (0.0 if aid != "B03" else 0.0), p["rot"])
    for l in a["lights"]:
        if l["tag"].startswith("약장"): continue
        add_light((l["x"], l["y"], l["z"] + (gz if aid != "B01" else 0)), l["color"], l["intensity"], l["range_m"], l["flicker"], l["tag"])
    if aid == "B01": pose("boss_naru", bx, by, 0.55, 0, "Windup", 56)
    if aid == "B02": pose("boss_b02_wolhwa", bx, by, gz, 270, "Idle", 20)
    if aid == "B03": pose("boss_b03_seo", bx, by, gz, 270, "Idle", 20)
    if tele:
        RED = (0.95, 0.18, 0.1); z = dz + 0.03
        if aid == "B01":   # 삿대 휩쓸기(부채꼴 120° 반경 4m, 동쪽으로) + 내려찍기(직선 6×1.5 북쪽으로) + 안쪽 경계는 이미 바닥 무늬
            z = 0.64   # 보스 배 바닥(0.55)보다 위에 얹어야 가려지지 않는다
            decal("tele_sector120.png", bx, by, z, 8.0, RED, rot=-60, emit=1.6)
            decal("tele_line.png", bx - 3.0, by, z, 1.5, RED, rot=90, w=1.5, h=6.0, emit=1.6)
        if aid == "B02":   # 잔 3칸(i=1,2,3): 그 잔 방향 30° 부채꼴 반경 8m. 열두째(11)는 안전
            for i in (2, 3, 4): decal("tele_sector30.png", bx, by, z, 16.0, RED, rot=i * 30, emit=1.6)
        if aid == "B03":   # 번호 칸 16개(약장 쪽 몇 줄을 비운 안전 9칸은 이어 붙게)
            safe = {(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1), (0, 2), (1, 2), (3, 0)}
            for i in range(5):
                for j in range(5):
                    if (i, j) in safe: continue
                    decal("tele_cell.png", bx + (i - 2) * 2.0, by + (j - 2) * 2.0, z, 1.9, RED, emit=1.6)

def run(key):
    cfg = SHOTS[key]; reset(); lib.t.clear(); lib.lights.clear(); placed_lights.clear(); stats["objs"] = 0; t0 = time.time()
    build(cfg["win"])
    if key == "naru":
        pose("boss_naru", 404, 288, 0.55, 0, "Windup", 56)
        put("fx_wait_ring_old", 404, 281, 0.4, 0, scale=1.0); 
    if key.startswith("arena"): arena_scene(key)
    if key == "portrait":   # 초상: 정면에서 가슴 위. 청록 테두리빛(왼쪽 뒤)과 따뜻한 등불빛(오른쪽 앞)
        pose("hero_chasa", 196.0, 48.0, 0, 0, "Idle", 20)
        for nm, loc, col, en in (("rimL", (194.2, 49.6, 2.2), (0.37, 0.89, 0.75), 260), ("warmR", (197.4, 45.4, 1.9), (1.0, 0.62, 0.38), 90)):
            ld = bpy.data.lights.new(nm, "POINT"); ld.energy = en; ld.color = col; ld.shadow_soft_size = 0.5; lo = bpy.data.objects.new(nm, ld); bpy.context.collection.objects.link(lo); lo.location = loc
    if key == "title":   # 서낭당 앞에 선 차사(서낭당을 마주 봄) + 둘레에 떠도는 넋
        pose("hero_chasa", 189.2, 34.6, 0.3, 215, "Idle", 20)
        orbs(((184.4, 33.6, 1.3), (191.0, 37.2, 1.9), (183.0, 40.0, 2.4), (187.6, 31.6, 0.9), (190.6, 41.5, 2.8)))
    if key == "load_b": put("night_soulfire_pedestal", 400.5, 276.0, 0.62 + 0.3, 0)
    for ex in cfg.get("extras", []): ex()      # 처음 10분 길 스틸(field_route_stills.py)이 주인공·혼을 얹는 자리
    if key == "tendo":
        # 마을 길 한가운데(집 지붕이 기둥을 가리지 않게 길 폭 안쪽에 모은다)
        pose("hero_chasa", 195.8, 49.5, 0, 0, "Cast", 30)
        put("fx_tendo_ring", 195.8, 49.5, 0.36, 0)
        pose("soul_fresh", 197.0, 54.3, 0, 200, "Kneel", 36); put("fx_wait_ring_fresh", 197.0, 54.3, 0.36, 0); put("fx_tendo_pillar", 197.0, 54.3, 0.36, 0)
        pose("soul_day", 194.4, 56.8, 0, 160, "Kneel", 36); put("fx_wait_ring_day", 194.4, 56.8, 0.36, 0)
        pose("soul_old", 197.6, 46.2, 0, 20, "Windup", 33)
        put("fx_pahon_shards_a", 193.8, 46.8, 0.36, 0, scale=0.8)
        put("fx_stain_decal", 196.4, 43.6, 0.37, 30)
    (lambda: world_hour(float(HOUR)))() if HOUR else (world_day if DAY else world_night)()
    sz = cfg.get("size", (1280, 720)); sz = (sz[0] // 3, sz[1] // 3) if os.environ.get("FS_TEST") else sz
    if os.environ.get("FS_CAM"): v = [float(t) for t in os.environ["FS_CAM"].split(",")]; cfg["cam"] = (tuple(v[:3]), tuple(v[3:6]), v[6])   # 카메라 시험용
    if "cam" in cfg: camera_persp(*cfg["cam"][:2], cfg["cam"][2], sz)
    else: camera(cfg["center"], cfg["ortho"], sz)
    if os.environ.get("FS_TEST"): bpy.context.scene.cycles.samples = 16
    path = os.path.join(A3, "previews", f"scene_{key}{('_h' + HOUR) if HOUR else ('_day' if DAY else '')}{os.environ.get('FS_TAG', '')}.png"); render(path)
    print(key, "객체", stats["objs"], "조명", len(placed_lights), "초", round(time.time() - t0)); return path

if __name__ == "__main__":
    keys = sys.argv[1:] or list(SHOTS)
    for k in keys: run(k)
    json.dump({k: SHOTS[k]["title"] for k in SHOTS}, open(os.path.join(A3, "previews", "_scene_titles.json"), "w"), ensure_ascii=False)
