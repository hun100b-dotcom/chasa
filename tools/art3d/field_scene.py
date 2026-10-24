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
DIRS = [("terrain_", "terrain"), ("nature_", "nature"), ("br_", "blackrapids"), ("prop_", "props"), ("hanok_", "hanok"), ("night_", "night"), ("fx_", "fx"), ("weapon_", "weapons"), ("boss_", "boss"), ("soul_", "souls"), ("hero_", "characters")]
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
            m = [o for o in new if o.type == "MESH" and o.parent is None][0]
            m.rotation_mode = "XYZ"; m.location = (0, 0, -500); m.hide_render = True
            self.lights[name] = [(Vector(e.location), dict(e)) for e in new if e.type == "EMPTY" and e.name.startswith("Light_")]
            for e in new:
                if e.type == "EMPTY": e.hide_render = True
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
    if scale != 1.0: o.scale = (scale,) * 3
    if lights:
        for off, ex in lib.lights.get(name, []):
            r = Euler((0, 0, math.radians(rot))).to_matrix() @ off
            add_light((x + r.x, y + r.y, z + r.z), ex["color"], ex["intensity"], ex["range_m"], ex["flicker"], name)
    return o

def inwin(x, y, win, m=0.0): return win[0] - m <= x <= win[2] + m and win[1] - m <= y <= win[3] + m

def build(win):
    """win=(x0,y0,x1,y1) m. 창 안 타일·장식·구조물·마을·밤 소품을 조립한다."""
    x0, y0, x1, y1 = win
    box("ground", (x1 - x0 + 40, y1 - y0 + 40, 0.28), ((x0 + x1) / 2, (y0 + y1) / 2, 0.14), "ground")   # 풀밭 기본 바닥(표에 없는 칸)
    for t in FIELD["tiles"]:
        cx, cy = t["ix"] * 8 + 4, t["iy"] * 8 + 4
        if inwin(cx, cy, win, 6): put(t["tile"], cx, cy, t["z"], t["rot"])
    for p in FIELD["props"]:
        if inwin(p["x"], p["y"], win, 4): put(p["prop"], p["x"], p["y"], p.get("z", 0), p["rot"])
    for s in FIELD.get("structures", []):
        if "pieces" in s:
            for q in s["pieces"]:
                if inwin(q["x"], q["y"], win, 6): put(q["piece"], q["x"], q["y"], q["z"], q["rot"])
        elif inwin(s["x"], s["y"], win, 8): put(s["piece"], s["x"], s["y"], s.get("z", 0), s["rot"])
    for b in VIL["buildings"]:
        for q in b["pieces"]:
            if inwin(q["x"] + VX, q["y"] + VY, win, 6): put(q["piece"], q["x"] + VX, q["y"] + VY, q["z"], q["rot"])
    for p in VIL["props"]:
        if inwin(p["x"] + VX, p["y"] + VY, win, 6): put(p["prop"], p["x"] + VX, p["y"] + VY, 0, p["rot"])
    # 마을 길(마을 배치표가 따로 깐 3.4m 길·마당. 필드 길 타일과 같은 색)
    if inwin(VX, VY, win, 60):
        box("v_road", (3.4, 52, 0.04), (VX, VY - 2, 0.32), "road"); box("v_plaza", (7, 5, 0.04), (VX + 3.4, VY - 5.5, 0.325), "road")
    # 밤 소품: 마을 길 양쪽 등롱 기둥, 어귀 석등, 서낭당 횃대, 우물 곁 혼불 받침
    decor = [("night_lantern_pole", VX - 2.6, VY - 18 + 9 * i, 0, 0) for i in range(5)] + [("night_lantern_pole", VX + 2.6, VY - 14 + 9 * i, 0, 180) for i in range(5)]
    decor += [("night_stone_lantern", VX - 4.2, VY - 22, 0, 0), ("night_stone_lantern", VX + 4.2, VY - 22, 0, 0), ("night_torch_stand", VX - 8, VY - 19, 0, 0), ("night_soulfire_pedestal", VX + 6.6, VY - 8.2, 0, 0)]
    decor += [("night_torch_stand", 76.5, FIELD["structures"][0]["y"] - 4.5, 0, 0), ("night_torch_stand", 91.5, FIELD["structures"][0]["y"] + 4.5, 0, 0), ("night_soulfire_pedestal", 404 - 6, 288 + 5, 0.62, 0)]
    for n, x, y, z, r in decor:
        if inwin(x, y, win, 6): put(n, x, y, z, r)

def world_night():
    sc = bpy.context.scene; w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
    nt = w.node_tree; bg = nt.nodes["Background"]; bg.inputs[0].default_value = (0.03, 0.045, 0.11, 1); bg.inputs[1].default_value = 2.5
    out = nt.nodes["World Output"]
    vs = nt.nodes.new("ShaderNodeVolumeScatter"); vs.inputs["Color"].default_value = (0.55, 0.65, 0.95, 1); vs.inputs["Density"].default_value = float(os.environ.get("FS_FOG","0")); vs.inputs["Anisotropy"].default_value = 0.35
    nt.links.new(vs.outputs[0], out.inputs["Volume"])
    sun = bpy.data.lights.new("moon", "SUN"); sun.energy = float(os.environ.get("FS_MOON","1.3")); sun.color = (0.62, 0.74, 1.0); sun.angle = math.radians(6)
    so = bpy.data.objects.new("moon", sun); bpy.context.collection.objects.link(so); so.rotation_euler = Euler((math.radians(58), 0, math.radians(-35)))

def camera(center, ortho, size, elev=50):
    sc = bpy.context.scene; sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 64
    try: sc.cycles.use_denoising = True; sc.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception: pass
    sc.render.resolution_x, sc.render.resolution_y = size
    cam = bpy.data.cameras.new("cam"); cam.type = "ORTHO"; cam.ortho_scale = ortho; cam.clip_end = 600
    co = bpy.data.objects.new("cam", cam); bpy.context.collection.objects.link(co); e = math.radians(elev); d = 120
    co.location = (center[0], center[1] - d * math.cos(e), center[2] + d * math.sin(e)); co.rotation_euler = (math.radians(90 - elev), 0, 0); sc.camera = co

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
  "gate":   dict(win=(150, 0, 245, 80), center=(196, 36, 0), ortho=62, title="솔고개 어귀(밤)"),
  "village": dict(win=(150, 20, 245, 110), center=(196, 62, 0), ortho=60, title="마을 안(밤)"),
  "barley": dict(win=(250, 70, 470, 220), center=(352, 134, 0), ortho=150, title="보릿들(밤)"),
  "bridge": dict(win=(40, 410, 130, 500), center=(84, 452, 0), ortho=48, title="검은여울 돌다리(밤)"),
  "naru":   dict(win=(340, 230, 470, 340), center=(404, 290, 0.6), ortho=40, title="나루 영감 보스 자리(밤)"),
  "tendo":  dict(win=(170, 30, 230, 90), center=(200, 52, 0), ortho=20, title="천도 이펙트(밤)"),
}

def run(key):
    cfg = SHOTS[key]; reset(); lib.t.clear(); lib.lights.clear(); placed_lights.clear(); stats["objs"] = 0; t0 = time.time()
    build(cfg["win"])
    if key == "naru":
        pose("boss_naru", 404, 288, 0.55, 0, "Windup", 56)
        put("fx_wait_ring_old", 404, 281, 0.3, 0, scale=1.0); 
    if key == "tendo":
        pose("hero_chasa", 197.0, 50.5, 0, 0, "Cast", 30)
        put("fx_tendo_ring", 197.0, 50.5, 0.32, 0)
        pose("soul_fresh", 204.5, 53.5, 0, 200, "Kneel", 36); put("fx_wait_ring_fresh", 204.5, 53.5, 0.32, 0); put("fx_tendo_pillar", 204.5, 53.5, 0.32, 0)
        pose("soul_day", 192.0, 55.5, 0, 160, "Kneel", 36); put("fx_wait_ring_day", 192.0, 55.5, 0.32, 0)
        pose("soul_old", 201.0, 47.0, 0, 20, "Windup", 33)
        put("fx_pahon_shards_a", 207.5, 49.0, 0.3, 0, scale=0.8)
        put("fx_stain_decal", 195.0, 46.0, 0.33, 30)
    world_night(); camera(cfg["center"], cfg["ortho"], (1280, 720) if not os.environ.get("FS_TEST") else (640, 360))
    if os.environ.get("FS_TEST"): bpy.context.scene.cycles.samples = 16
    path = os.path.join(A3, "previews", f"scene_{key}.png"); render(path)
    print(key, "객체", stats["objs"], "조명", len(placed_lights), "초", round(time.time() - t0)); return path

if __name__ == "__main__":
    keys = sys.argv[1:] or list(SHOTS)
    for k in keys: run(k)
    json.dump({k: SHOTS[k]["title"] for k in SHOTS}, open(os.path.join(A3, "previews", "_scene_titles.json"), "w"), ensure_ascii=False)
