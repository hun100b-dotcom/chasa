"""2막 검은여울 지역 키트: 여울·깊은 물·물가 타일, 돌다리, 나루터(불빛 표시 포함), 버드나무, 갈대밭, 의원 집 소품.
규약: GLB, 1유닛=1m, 원점=바닥 중심(물 타일은 윗면이 풀 타일보다 낮음), 정면 +Z(블렌더 -Y). 타일은 8×8m, 여울은 서→동으로 흐른다(rot로 방향 바꿈).
물 높이: 풀 타일 윗면 z=0.3, 물 윗면 z=0.18(물가가 0.12m 낮게 보이도록). 의원 집은 한옥 키트 조각으로 짓는다(kit_buildings 'uiwon')."""
import sys, os, math, json, random
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")
T = 8.0; WZ = 0.18   # 물 윗면 높이
rnd = lambda s: random.Random(s)

def water_slab(color="#1C2744"): return box("water", (T, T, WZ), (0, 0, WZ / 2), color)

def rapids():
    r = rnd(11); p = [water_slab()]
    for i in range(7):   # 흐름 방향(동서) 거품 줄
        y = -3.2 + i * 1.05 + r.uniform(-0.2, 0.2); x = r.uniform(-1.5, 1.5); L = r.uniform(1.2, 2.6)
        p.append(box(f"foam{i}", (L, 0.09, 0.02), (x, y, WZ + 0.01), "chain"))
    for i in range(5):   # 물살을 가르는 검은 바위
        x, y = r.uniform(-3.2, 3.2), r.uniform(-3.2, 3.2); s = r.uniform(0.35, 0.7)
        p.append(sphere(f"rock{i}", s, (x, y, max(WZ + s * 0.2, s * 0.7)), "stone_dark", 5, 4, (1.2, 1, 0.7)))
        p.append(box(f"wake{i}", (s * 2.2, 0.07, 0.025), (x + s * 1.6, y, WZ + 0.015), "chain"))
    return p

def deep():
    r = rnd(12); p = [water_slab("#0F1626")]
    for i in range(3): p.append(box(f"ripple{i}", (r.uniform(1.5, 3), 0.05, 0.015), (r.uniform(-2, 2), r.uniform(-3, 3), WZ + 0.008), "water"))
    return p

def shore():
    """남쪽 절반은 풀 둑(윗면 0.3), 북쪽 절반은 물. 둑 가장자리 돌."""
    r = rnd(13)
    p = [box("land", (T, T / 2, 0.3), (0, -T / 4, 0.15), "ground"), box("water", (T, T / 2, WZ), (0, T / 4, WZ / 2), "#1C2744"), box("lip", (T, 0.35, 0.34), (0, 0.17, 0.17), "slope_side")]
    for i in range(6):
        x = -3.4 + i * 1.35 + r.uniform(-0.2, 0.2); s = r.uniform(0.2, 0.35)
        p.append(sphere(f"edge{i}", s, (x, r.uniform(0.0, 0.3), 0.26), "stone", 5, 4, (1.3, 1, 0.7)))
    p.append(box("foam", (5, 0.08, 0.02), (0.5, 0.6, WZ + 0.01), "chain"))
    return p

def road_pad():
    """둑 위 길 조각 4×3.2m. 왜: 물가 타일(br_shore)에는 길이 없어서 길이 다리 앞 4m에서 끊겼다."""
    return [box("pad", (4, 3.2, 0.04), (0, 0, 0.32), "road")]

def bridge():
    """돌다리: 길이 8m(동서), 폭 2.4m. 돌기둥 3쌍 위에 널돌 상판, 난간돌 낮게."""
    p = []
    for x in (-2.8, 0, 2.8):
        for y in (-0.8, 0.8): p.append(box(f"pier{x}{y}", (0.8, 0.6, 0.78), (x, y, 0.39), "stone_dark"))
    for i in range(4):
        x = -3.0 + i * 2.0; p.append(box(f"deck{i}", (1.9, 2.4, 0.2), (x, 0, 0.78 + 0.1), "stone"))
    for sy in (-1.15, 1.15):
        for i in range(5):
            x = -3.6 + i * 1.8; p.append(box(f"post{sy}{i}", (0.3, 0.3, 0.45), (x, sy, 1.02 + 0.22), "stone_dark"))
        p.append(box(f"rail{sy}", (7.4, 0.14, 0.12), (0, sy, 1.45), "stone"))
    p += [box("apL", (0.6, 2.0, 0.15), (-4.0, 0, 0.3), "stone"), box("apR", (0.6, 2.0, 0.15), (4.0, 0, 0.3), "stone")]
    return p

def dock():
    """나루터: 물가에 뻗은 널 부두 6×2.4m(앞=-Y 쪽이 물), 말뚝과 밧줄, 등불 기둥(불빛 위치 표시)."""
    p = [box("plank%d" % i, (2.4, 0.38, 0.1), (0, -0.2 - i * 0.42, 0.45), "wood" if i % 2 else "wood_dark") for i in range(14)]
    for sx in (-1.2, 1.2):
        for i in range(4): p.append(cyl(f"post{sx}{i}", 0.09, 0.08, 0.95, (sx, -0.4 - i * 1.7, 0.0), "wood_dark", 5))
        p.append(box(f"beam{sx}", (0.1, 6.0, 0.1), (sx, -3.0, 0.4), "wood_dark"))
    p += [cyl("mooring", 0.08, 0.1, 0.5, (0.9, -5.6, 0.5), "wood", 5), box("rope", (0.04, 0.9, 0.04), (0.9, -5.2, 0.6), "thatch", rot=(0.5, 0, 0)),
          cyl("lampPole", 0.05, 0.05, 1.8, (-1.0, -0.6, 0.5), "wood_dark", 5), box("lampArm", (0.4, 0.05, 0.05), (-0.8, -0.6, 2.25), "wood_dark"), sphere("lamp", 0.14, (-0.6, -0.6, 2.1), mat("gold", 1.6), 6, 4)]
    return p

def willow(var):
    r = rnd(20 + var); h = 3.8 + var * 0.7
    p = [cyl("trunk", 0.28, 0.17, h * 0.55, (0, 0, 0), "bark", 6), cyl("limb1", 0.12, 0.07, 1.2, (0.1, 0, h * 0.45), "bark", 5, rot=(0.0, 0.7, 0)), cyl("limb2", 0.12, 0.07, 1.2, (-0.1, 0, h * 0.45), "bark", 5, rot=(0.0, -0.7, 0))]
    p.append(sphere("crown", 1.3 + var * 0.2, (0, 0, h * 0.62), "zelkova_dark", 7, 5, (1.2, 1.2, 0.7)))
    for i in range(14 + var * 4):   # 늘어진 가지(끝이 가는 원뿔을 거꾸로)
        a = i / (14 + var * 4) * math.tau; rr = r.uniform(1.0, 1.6) + var * 0.15; L = r.uniform(1.6, 2.6)
        p.append(cyl(f"str{i}", 0.0, 0.05, L, (math.cos(a) * rr, math.sin(a) * rr, h * 0.62 - L + 0.3), "zelkova", 4))
    return p

def reeds():
    """갈대밭 8×8m: 갈대 줄기 무더기 40개(삼각 기둥)와 갈색 이삭."""
    r = rnd(31); p = []
    for i in range(40):
        x, y = r.uniform(-3.7, 3.7), r.uniform(-3.7, 3.7); h = r.uniform(1.6, 2.6); t = r.uniform(-0.15, 0.15)
        p.append(cyl(f"b{i}", 0.04, 0.0, h, (x, y, 0.05), "reed", 3, rot=(t, r.uniform(-0.15, 0.15), 0)))
        if i % 3 == 0: p.append(cyl(f"h{i}", 0.05, 0.02, 0.35, (x + t * h * 0.9, y, h * 0.85), "reed_top", 4))
    p.append(box("mud", (T, T, 0.16), (0, 0, 0.08), "slope_side"))
    return p

def herb_rack():
    """의원집 약초 건조대: 두 기둥 + 가로대 + 매달린 약초 묶음 6개."""
    p = [cyl(f"leg{s}", 0.05, 0.05, 1.9, (s * 1.0, 0, 0), "wood_dark", 5) for s in (-1, 1)] + [box("bar", (2.2, 0.06, 0.06), (0, 0, 1.8), "wood_dark"), box("bar2", (2.2, 0.06, 0.06), (0, 0, 1.1), "wood_dark")]
    for i in range(6): p.append(cyl(f"herb{i}", 0.12, 0.03, 0.55, (-0.85 + i * 0.34, 0, 1.2 if i % 2 else 0.55), "leaf" if i % 2 else "thatch", 5, rot=(math.pi, 0, 0)))
    return p

def med_sign():
    """약방 깃대: 긴 장대에 붉은 천(글자 없이 흰 원 표식)."""
    return [cyl("pole", 0.05, 0.05, 3.4, (0, 0, 0), "wood_dark", 5), box("cloth", (0.04, 0.8, 1.4), (0.0, 0.42, 2.5), "red"), cyl("dot", 0.22, 0.22, 0.02, (0.03, 0.42, 2.5), "hanji", 8, rot=(0, math.pi / 2, 0))]

def jars():
    p = []
    for i, (x, y, s) in enumerate([(0, 0, 1), (0.5, 0.1, 0.8), (0.2, 0.55, 0.9)]):
        p += [sphere(f"jar{i}", 0.25 * s, (x, y, 0.3 * s), "jar", 7, 5, (1, 1, 1.15)), cyl(f"lid{i}", 0.12 * s, 0.1 * s, 0.07, (x, y, 0.52 * s), "wood_dark", 6)]
    return p

KIT = [("br_rapids", rapids, "여울 타일 8×8m(서→동 흐름, 물 윗면 z0.18)"), ("br_deep", deep, "깊은 물 타일 8×8m"), ("br_shore", shore, "물가 타일(남쪽=풀 둑, 북쪽=물)"), ("br_road_pad", road_pad, "둑 위 길 조각 4×3.2m(다리 양끝에 이어 붙임, 중심 원점)"), ("br_stone_bridge", bridge, "돌다리 8×2.4m(동서), 상판 z0.88"),
       ("br_ferry_dock", dock, "나루터 부두(앞=-Y가 물 쪽, 등불 위치 Light_ 표시)"), ("br_willow_a", lambda: willow(0), "버드나무 키 약 3.8m"), ("br_willow_b", lambda: willow(1), "버드나무 키 약 4.5m"),
       ("br_reed_field", reeds, "갈대밭 8×8m"), ("br_herb_rack", herb_rack, "의원집 약초 건조대"), ("br_med_sign", med_sign, "약방 깃대"), ("br_jars", jars, "약 항아리 세 개")]

def make(key, fn):
    reset(); o = join(key, fn())
    if key == "br_ferry_dock": light_empty(o, "Light_ferry_dock", (-0.6, -0.6, 2.1), "#FFB066", intensity=1.0, range_m=8.0, flicker=True)
    return o

if __name__ == "__main__":
    rep = []
    for key, fn, note in KIT:
        o = make(key, fn); lo, hi = bounds(o)
        rep.append({"name": key, "note": note, "tris": tris(o), "size_m": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)], "min_z": round(lo.z, 3)})
        export(o, os.path.join(OUT, "blackrapids", f"{key}.glb"))
    # 시험 조립: 위 물가-여울-아래 물가를 가로질러 돌다리, 부두, 버드나무, 갈대, 의원 집
    reset()
    def put(fn, x, y, rot=0, z=0, name="p"):
        o = join(name, fn()); o.location = (x, y, z); o.rotation_euler = (0, 0, math.radians(rot)); return o
    for i in range(-2, 3):
        put(rapids if i % 2 else deep, i * T, 0, 0)
        put(shore, i * T, T, 180); put(shore, i * T, -T, 0)
        for j in (2, -2):
            g = box("g", (T, T, 0.3), (i * T, j * T + (0 if j > 0 else 0), 0.15), "ground")
    put(bridge, 0, 0); put(dock, -T * 1.5 + 2, T - 2.5, 180); put(lambda: willow(0), -12, 11.5, 0, 0, "w1"); put(lambda: willow(1), 11, -10.5); put(reeds, 20, -12); put(reeds, -22, 12)
    put(herb_rack, 6, -12, 0); put(med_sign, 4, -9); put(jars, 8.5, -10)
    from kit_buildings import place_building
    import bpy
    kit = {}
    for p in place_building("giwa8", 0, -17, 0, gate=False):
        if p["file"] not in kit:
            bpy.ops.import_scene.gltf(filepath=os.path.join(OUT, "..", p["file"])); m = [o for o in bpy.context.selected_objects if o.type == "MESH"][0]
            for e in bpy.context.selected_objects:
                if e is not m and e.type != "MESH": bpy.data.objects.remove(e)
            m.parent = None; m.rotation_mode = "XYZ"; m.location = (999, 999, -50); kit[p["file"]] = m
        o = kit[p["file"]].copy(); bpy.context.collection.objects.link(o); o.location = (p["x"], p["y"], p["z"]); o.rotation_euler = (0, 0, math.radians(p["rot"]))
    setup_render(44, (0, 0, 0), size=(1300, 760), ground_size=100)
    render(os.path.join(OUT, "previews", "blackrapids_kit_50deg.png"))
    json.dump({"tile_m": T, "water_top_z": WZ, "land_top_z": 0.3, "pieces": rep, "house": "의원 집 = kit_buildings 'giwa8'(기와집 8×4m)를 쓰고 약초 건조대·약방 깃대·항아리를 곁에 놓는다"}, open(os.path.join(OUT, "blackrapids", "_blackrapids_manifest.json"), "w"), ensure_ascii=False, indent=1)
    for r in rep: print(r["name"], r["tris"], r["min_z"])
