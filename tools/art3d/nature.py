"""자연물 키트 17종 + 밤 조명 소품 5종(광원 위치는 빈 오브젝트 Light_*). 실행: python3 nature.py
규약: GLB, 1유닛=1m, 원점=바닥 한가운데, 재질 베이스컬러만(불빛 면만 발광), 정면 +Z.
광원 빈 오브젝트: 이름 Light_*, 추가 속성 light_type/color/intensity/range_m/flicker(glTF extras)."""
import sys, os, math, json, random
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")
TAU = math.tau

def crowns(spec, mats, scale=(1.0, 1.0, 0.7), segs=7, rings=4):
    return [sphere(f"crown{i}", r, (x, y, z), mats[i % len(mats)], segs, rings, (scale[0], scale[1], scale[2])) for i, (x, y, z, r) in enumerate(spec)]

def trunk(pts, rs, mat="bark", segs=6):
    p = []
    for i in range(len(pts) - 1):
        p.append(limb(f"trunk{i}", pts[i], pts[i + 1], rs[i], rs[i + 1], mat, segs))
    return p

def pine_a(): return trunk([(0, 0, 0), (0.1, 0, 2.0), (-0.1, 0.1, 4.0), (0.1, 0, 5.6)], [0.28, 0.2, 0.14, 0.06]) + crowns([(0.9, 0.2, 4.6, 1.2), (-1.0, -0.2, 3.9, 1.0), (0.1, 0.8, 5.6, 1.1), (-0.5, -0.6, 5.3, 0.9)], ["pine", "pine_light"], (1.5, 1.5, 0.5))
def pine_b(): return trunk([(0, 0, 0), (0, 0, 1.6), (0.1, 0, 3.0)], [0.2, 0.13, 0.05]) + crowns([(0, 0, 2.9, 1.0), (0.5, 0.3, 2.3, 0.7)], ["pine", "pine_light"], (1.5, 1.5, 0.55))
def pine_c(): return trunk([(0, 0, 0), (0.4, 0, 1.4), (1.3, 0.1, 2.4), (2.3, 0.1, 3.0)], [0.3, 0.22, 0.15, 0.07]) + crowns([(2.4, 0.1, 3.4, 1.2), (1.2, 0.3, 3.0, 0.9), (2.8, -0.4, 2.8, 0.8)], ["pine", "pine_light"], (1.5, 1.5, 0.5))
def zelkova_a(): return trunk([(0, 0, 0), (0, 0, 2.2), (0.1, 0, 3.6)], [0.55, 0.4, 0.25], segs=7) + [cyl("root", 0.8, 0.55, 0.5, (0, 0, 0), "bark", 7)] + crowns([(0, 0, 5.3, 2.4), (1.8, 0.6, 4.5, 1.7), (-1.8, -0.4, 4.6, 1.8), (0.4, -1.6, 4.4, 1.5), (-0.3, 1.5, 4.6, 1.6)], ["zelkova", "zelkova_dark"], (1, 1, 0.85), 8, 5)
def zelkova_b(): return trunk([(0, 0, 0), (0, 0, 1.5), (0, 0, 2.4)], [0.25, 0.18, 0.1]) + crowns([(0, 0, 3.4, 1.5), (1.0, 0.3, 2.9, 1.0), (-1.0, -0.2, 3.0, 1.1)], ["zelkova", "zelkova_dark"], (1, 1, 0.85), 7, 4)

def bamboo(n, h, seed, spread):
    r = random.Random(seed); p = []
    for i in range(n):
        a = r.random() * TAU; d = r.random() * spread; x, y = math.cos(a) * d, math.sin(a) * d
        hh = h * (0.8 + r.random() * 0.3); tilt = (r.random() - .5) * 0.15
        top = (x + tilt * hh, y, hh)
        p.append(limb(f"stalk{i}", (x, y, 0), top, 0.065, 0.045, "bamboo", 5))
        for k in range(1, int(hh)):
            p.append(box(f"node{i}_{k}", (0.14, 0.14, 0.04), (x + tilt * k, y, k), "bamboo_leaf"))
        for k in range(2):
            p.append(sphere(f"leaf{i}_{k}", 0.55, (top[0] + (k - .5) * 0.5, y, hh - 0.2 - k * 0.5), "bamboo_leaf", 5, 3, (1, 1, 0.35)))
    return p
def bamboo_a(): return bamboo(9, 5.0, 1, 1.4)
def bamboo_b(): return bamboo(5, 4.0, 2, 0.9)

def blades(n, h, spread, mat, seed, bend=0.35, top=None, top_mat=None):
    r = random.Random(seed); p = []
    for i in range(n):
        a = r.random() * TAU; d = r.random() * spread; x, y = math.cos(a) * d, math.sin(a) * d
        hh = h * (0.7 + r.random() * 0.5); b = bend * (0.5 + r.random())
        tip = (x + math.cos(a) * b * hh * 0.6, y + math.sin(a) * b * hh * 0.6, hh)
        p.append(limb(f"blade{i}", (x, y, 0.04), tip, 0.045, 0.0, mat, 3))
        if top and i % 2 == 0:
            p.append(box(f"top{i}", (0.07, 0.07, top), (tip[0], tip[1], hh + top * 0.4), top_mat or mat, rot=(math.sin(a) * 0.4, -math.cos(a) * 0.4, 0)))
    return p
def reed_a(): return blades(30, 1.8, 0.7, "reed", 11, 0.25, 0.3, "reed_top")
def reed_b(): return blades(45, 2.5, 1.0, "reed", 12, 0.3, 0.35, "reed_top")
def silver_a(): return blades(26, 1.4, 0.6, "reed", 13, 0.55, 0.4, "silver")
def silver_b(): return blades(40, 1.7, 0.9, "reed", 14, 0.6, 0.45, "silver")

def bush(kind):
    r = random.Random(5); p = []
    for i, (x, y, z, rr) in enumerate([(0, 0, 0.5, 0.7), (0.6, 0.2, 0.4, 0.5), (-0.55, 0.1, 0.4, 0.55), (0.1, -0.5, 0.35, 0.45), (0.2, 0.5, 0.45, 0.5)]):
        p.append(sphere(f"b{i}", rr, (x, y, rr * 0.85 if kind != "a" else rr * 0.9), "leaf" if i % 2 else "leaf_dark", 6, 4, (1, 1, 0.85)))
    if kind == "b":
        for i in range(14):
            a = r.random() * TAU; d = 0.5 + r.random() * 0.4
            p.append(cyl(f"thorn{i}", 0.03, 0.0, 0.3, (math.cos(a) * d, math.sin(a) * d, 0.6 + r.random() * 0.4), "bark", 3, rot=(math.sin(a) * 1.1, -math.cos(a) * 1.1, 0)))
    if kind == "c":
        for i in range(10):
            a = r.random() * TAU; d = 0.5 + r.random() * 0.3
            p.append(sphere(f"berry{i}", 0.06, (math.cos(a) * d, math.sin(a) * d, 0.5 + r.random() * 0.5), "berry", 4, 3))
    return p
def dead_a(): return trunk([(0, 0, 0), (0.05, 0, 1.6), (-0.05, 0.1, 3.0)], [0.22, 0.14, 0.05], "dead") + [limb(f"br{i}", (0, 0, 1.6 + i * 0.5), (math.cos(i * 2.1) * 1.1, math.sin(i * 2.1) * 1.1, 2.3 + i * 0.5), 0.07, 0.015, "dead", 4) for i in range(4)]
def dead_b(): return [cyl("stump", 0.42, 0.35, 0.55, (0, 0, 0), "dead", 7), cyl("top", 0.35, 0.3, 0.06, (0, 0, 0.55), "wood", 7)] + [limb(f"root{i}", (0, 0, 0.3), (math.cos(i * 1.6) * 0.9, math.sin(i * 1.6) * 0.9, 0.0), 0.12, 0.03, "dead", 4) for i in range(4)]
def dead_c(): return trunk([(0, 0, 0), (0.3, 0, 1.2), (1.0, 0, 2.0)], [0.25, 0.17, 0.06], "dead") + [limb("br0", (0.6, 0, 1.5), (-0.6, 0.4, 2.3), 0.07, 0.015, "dead", 4), limb("br1", (0.9, 0, 1.9), (1.7, -0.6, 2.7), 0.06, 0.015, "dead", 4), limb("br2", (0.2, 0, 0.9), (-0.7, -0.3, 1.5), 0.06, 0.015, "dead", 4)]

NATURE = {"pine_a": pine_a, "pine_b": pine_b, "pine_c": pine_c, "zelkova_a": zelkova_a, "zelkova_b": zelkova_b, "bamboo_a": bamboo_a, "bamboo_b": bamboo_b,
          "reed_a": reed_a, "reed_b": reed_b, "silvergrass_a": silver_a, "silvergrass_b": silver_b, "bush_a": lambda: bush("a"), "bush_b": lambda: bush("b"), "bush_c": lambda: bush("c"),
          "dead_a": dead_a, "dead_b": dead_b, "dead_c": dead_c}

# ---- 밤 조명 소품: (부품 만드는 함수, [광원 빈 오브젝트])
WARM = "#FFB066"
def stone_lantern():
    glow = mat(WARM, 2.5)
    p = [box("base", (0.9, 0.9, 0.15), (0, 0, 0.075), "stone_dark"), cyl("pillar", 0.14, 0.12, 0.8, (0, 0, 0.15), "stone", 8), cyl("disc", 0.45, 0.4, 0.12, (0, 0, 0.95), "stone", 8),
         box("fire", (0.5, 0.5, 0.5), (0, 0, 1.31), "stone_dark")] + [box(f"win{i}", (0.28, 0.02, 0.3) if i % 2 == 0 else (0.02, 0.28, 0.3), ((0, -0.26, 1.31), (0.26, 0, 1.31), (0, 0.26, 1.31), (-0.26, 0, 1.31))[i], glow) for i in range(4)] + [
         pyramid("roof", 1.05, 1.05, 0.4, (0, 0, 1.56), "stone", top=0.15), sphere("jewel", 0.09, (0, 0, 2.05), "stone_dark", 5, 3)]
    return p, [("Light_stone_lantern", (0, 0, 1.31), WARM, 1.0, 7.0, False)]
def lantern_stand():
    glow = mat(WARM, 2.2)
    p = [box("frame", (0.5, 0.5, 0.06), (0, 0, 0.8), "wood_dark"), box("foot", (0.4, 0.4, 0.05), (0, 0, 0.03), "wood_dark")] + [box(f"leg{i}", (0.06, 0.06, 0.8), (x, y, 0.4), "wood_dark") for i, (x, y) in enumerate([(-0.2, -0.2), (0.2, -0.2), (0.2, 0.2), (-0.2, 0.2)])] + [
         box("box", (0.42, 0.42, 0.5), (0, 0, 1.08), glow), box("top", (0.54, 0.54, 0.07), (0, 0, 1.36), "red"), box("capL", (0.06, 0.06, 0.2), (0, 0, 1.45), "wood_dark"), pyramid("hat", 0.6, 0.6, 0.18, (0, 0, 1.38), "tile", top=0.2)]
    return p, [("Light_lantern_stand", (0, 0, 1.08), WARM, 0.8, 6.0, True)]
def lantern_pole():
    glow = mat(WARM, 2.2)
    p = [cyl("post", 0.07, 0.06, 2.6, (0, 0, 0), "wood", 6), cyl("foot", 0.25, 0.2, 0.2, (0, 0, 0), "stone", 6), box("arm", (0.8, 0.07, 0.07), (0.4, 0, 2.5), "wood"),
         limb("hook", (0.8, 0, 2.5), (0.8, 0, 2.3), 0.015, 0.015, "iron", 4), sphere("lamp", 0.2, (0.8, 0, 2.05), glow, 7, 5, (1, 1, 1.25)), cyl("capT", 0.1, 0.1, 0.05, (0.8, 0, 2.32), "red", 6), cyl("capB", 0.08, 0.08, 0.05, (0.8, 0, 1.76), "red", 6)]
    return p, [("Light_lantern_pole", (0.8, 0, 2.05), WARM, 0.9, 7.0, True)]
def torch_stand():
    f1, f2 = mat("#FF8A2A", 3.5), mat("#FFD27A", 4.0)
    p = [cyl("post", 0.07, 0.06, 1.5, (0, 0, 0), "wood", 6), cyl("foot", 0.28, 0.2, 0.18, (0, 0, 0), "stone", 6), cyl("bowl", 0.14, 0.24, 0.28, (0, 0, 1.45), "iron", 8), cyl("flame1", 0.2, 0.0, 0.55, (0, 0, 1.7), f1, 6), cyl("flame2", 0.1, 0.0, 0.35, (0, 0, 1.75), f2, 6)]
    return p, [("Light_torch_stand", (0, 0, 1.95), "#FF9A3A", 1.3, 9.0, True)]
def soulfire_pedestal():
    orb = mat("cheondo", 3.0)
    p = [cyl("base", 0.4, 0.3, 0.2, (0, 0, 0), "stone_dark", 8), cyl("stem", 0.18, 0.16, 0.55, (0, 0, 0.2), "stone", 8), cyl("dish", 0.45, 0.2, 0.2, (0, 0, 0.75), "stone", 8),
         sphere("orb", 0.17, (0, 0, 1.25), orb, 7, 5)] + [sphere(f"spark{i}", 0.04, (math.cos(i * 2.1) * 0.3, math.sin(i * 2.1) * 0.3, 1.1 + i * 0.12), orb, 4, 3) for i in range(3)]
    return p, [("Light_soulfire", (0, 0, 1.25), "#5FE3C0", 1.1, 8.0, False)]
NIGHT = {"stone_lantern": stone_lantern, "lantern_stand": lantern_stand, "lantern_pole": lantern_pole, "torch_stand": torch_stand, "soulfire_pedestal": soulfire_pedestal}

def build(group, key):
    if group == "nature":
        parts, lights = NATURE[key](), []
    else:
        parts, lights = NIGHT[key]()
    o = join(f"{group}_{key}", parts)
    es = [light_empty(o, n, pos, c, i, r, f) for n, pos, c, i, r, f in lights]
    return o, es

def run():
    rep = []
    for group, d in (("nature", NATURE), ("night", NIGHT)):
        for key in d:
            reset(); o, es = build(group, key); lo, hi = bounds(o)
            rep.append({"name": f"{group}_{key}", "tris": tris(o), "size_m": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)], "min_z": round(lo.z, 3), "lights": [e.name for e in es]})
            export(o, os.path.join(OUT, group, f"{group}_{key}.glb"))
    json.dump(rep, open(os.path.join(OUT, "nature", "_report_nature.json"), "w"), ensure_ascii=False, indent=1)
    # 미리보기 한 장: 자연물 17 + 조명 5 를 나란히
    reset()
    keys = [("nature", k) for k in NATURE] + [("night", k) for k in NIGHT]
    cols = 6
    for i, (g, k) in enumerate(keys):
        o, es = build(g, k)
        o.location = ((i % cols - 2.5) * 5.0, -(i // cols) * 5.5 + 7.0, 0)
        for e in es: e.parent = o   # 빈 오브젝트는 따라간다
    # 밤 느낌: 어둡게 + 불빛
    setup_render(40, (0, 0, 1.5), size=(1400, 1000), ground_size=60, night=True)
    render(os.path.join(OUT, "previews", "nature_night_kit_50deg.png"))
    return rep

if __name__ == "__main__":
    rep = run()
    print(len(rep), "종, 최대 삼각형", max(r["tris"] for r in rep), "최소 z", min(r["min_z"] for r in rep))
    print([ (r["name"], r["tris"]) for r in rep if r["tris"] > 1200])
