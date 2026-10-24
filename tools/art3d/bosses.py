"""보스 6원형 로우폴리 (② 의식·③ 기록·④ 무리·⑤ 기다림·⑥ 차사·⑦ 덩어리). ①은 boss_naru.py.
왜 하나로 모으나: 6종이 같은 뼈대 규칙(Root/Hips/Chest/Head/UpperArm.L·R/Prop)을 쓰면 코드팀이 애니메이션 연결을 한 번만 하면 된다.
규약: GLB, 1유닛=1m, 원점=발밑 한가운데, 정면 +Z(블렌더에서는 -Y). 삼각형 2천 이하. 재질은 베이스컬러만.
"""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
from characters import to_group, rig
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")

def bones(h):
    """키 h(m) 기준 뼈대. 모든 보스가 같은 이름을 쓰고 키만 다르다."""
    s = h / 2.0
    return [("Root", None, (0, 0, 0), (0, 0, 0.2 * s)), ("Hips", "Root", (0, 0, 0.9 * s), (0, 0, 1.0 * s)), ("Chest", "Hips", (0, 0, 1.0 * s), (0, 0, 1.4 * s)),
            ("Head", "Chest", (0, 0, 1.4 * s), (0, 0, 1.9 * s)), ("UpperArm.L", "Chest", (0.3 * s, 0, 1.35 * s), (0.7 * s, 0, 0.9 * s)),
            ("UpperArm.R", "Chest", (-0.3 * s, 0, 1.35 * s), (-0.7 * s, 0, 0.9 * s)), ("Prop", "Root", (0, 0, 1.0 * s), (0, 0, 1.2 * s))]

def face(x, y, z, dx=0.07, s=0.035, c="face"):
    # 눈 두 개(정면 -Y 방향 면에 붙인다)
    return [box("eyeL", (s, 0.02, s * 1.5), (x + dx, y, z), c), box("eyeR", (s, 0.02, s * 1.5), (x - dx, y, z), c)]

def wolhwa():
    """② 월화(의식): 흰 무복에 넓은 소매, 높은 화관, 허공에 도는 요령 고리. 키 2.1m."""
    p = {k: [] for k in ("Root", "Hips", "Chest", "Head", "UpperArm.L", "UpperArm.R", "Prop")}
    p["Hips"] += [cyl("skirt", 0.62, 0.26, 1.0, (0, 0, 0.0), "hanji", 9)]
    p["Chest"] += [cyl("torso", 0.26, 0.22, 0.5, (0, 0, 1.0), "hanji", 8), box("sash", (0.5, 0.34, 0.09), (0, 0, 1.05), "red"), box("collar", (0.3, 0.3, 0.05), (0, 0, 1.45), "red")]
    p["Head"] += [sphere("head", 0.15, (0, 0, 1.66), "skin", 7, 5), cyl("crown", 0.2, 0.12, 0.3, (0, 0, 1.74), "gold", 6), cyl("hair", 0.17, 0.1, 0.5, (0, 0.12, 1.2), "hat", 6)] + face(0, -0.14, 1.68, 0.06, 0.03, "ink")
    for sx, n in ((1, "UpperArm.L"), (-1, "UpperArm.R")):  # 넓은 소매를 활짝 편 모습
        p[n] += [limb("sleeve", (sx * 0.24, 0, 1.4), (sx * 0.95, -0.15, 1.15), 0.08, 0.2, "hanji", 6), sphere("hand", 0.07, (sx * 1.0, -0.17, 1.1), "skin", 5, 4)]
    # 허공에 도는 요령(방울) 6개 고리 — 의식의 상징
    for i in range(6):
        a = i / 6 * math.tau
        p["Prop"] += [sphere(f"bell{i}", 0.1, (math.cos(a) * 0.95, math.sin(a) * 0.95, 1.1), "gold", 5, 4), cyl(f"rope{i}", 0.015, 0.015, 0.3, (math.cos(a) * 0.95, math.sin(a) * 0.95, 1.2), "red", 4)]
    p["Root"] += [cyl("ring", 1.1, 1.1, 0.03, (0, 0, 0.0), mat("chain", 0.4), 14)]
    return p, 2.1

def seo():
    """③ 서 의원(기록): 먹빛 도포, 긴 갓, 몸 앞에 떠 있는 큰 장부, 늘어진 두루마리. 키 2.0m."""
    p = {k: [] for k in ("Root", "Hips", "Chest", "Head", "UpperArm.L", "UpperArm.R", "Prop")}
    p["Hips"] += [cyl("robe", 0.46, 0.25, 1.05, (0, 0, 0.0), "ink", 8)]
    p["Chest"] += [cyl("torso", 0.25, 0.22, 0.5, (0, 0, 1.0), "robe", 8), box("sash", (0.5, 0.32, 0.07), (0, 0, 1.05), "gold")]
    p["Head"] += [sphere("head", 0.14, (0, 0, 1.62), "old_skin", 7, 5), cyl("brim", 0.42, 0.3, 0.04, (0, 0, 1.7), "hat", 10), cyl("crown", 0.15, 0.13, 0.28, (0, 0, 1.72), "hat", 8),
                  box("beard", (0.1, 0.05, 0.3), (0, -0.12, 1.4), "beard")] + face(0, -0.13, 1.64)
    p["UpperArm.L"] += [limb("armL", (0.22, 0, 1.4), (0.35, -0.5, 1.2), 0.06, 0.13, "robe", 6)]
    p["UpperArm.R"] += [limb("armR", (-0.22, 0, 1.4), (-0.35, -0.5, 1.2), 0.06, 0.13, "robe", 6)]
    # 장부: 몸 앞에 비스듬히 떠 있는 책 + 위아래로 늘어진 두루마리 종이띠
    p["Prop"] += [box("book", (0.9, 0.12, 1.1), (0, -0.7, 1.35), "hanji", rot=(0.15, 0, 0)), box("spine", (0.1, 0.16, 1.14), (-0.45, -0.7, 1.35), "red"),
                  box("line1", (0.6, 0.02, 0.05), (0.05, -0.77, 1.5), "ink"), box("line2", (0.6, 0.02, 0.05), (0.05, -0.77, 1.3), "ink"), box("line3", (0.5, 0.02, 0.05), (0.0, -0.77, 1.1), "ink")]
    for i in range(4):
        p["Prop"].append(box(f"strip{i}", (0.16, 0.02, 0.9), (-0.7 + i * 0.47, -0.9, 0.55 + (i % 2) * 0.2), "hanji", rot=(0, 0.1 * (i - 1.5), 0)))
    return p, 2.0

def daedol():
    """④ 대돌(무리): 깃발을 든 거구의 기수와 뒤따르는 작은 병졸 4기(무리의 상징). 키 2.4m."""
    p = {k: [] for k in ("Root", "Hips", "Chest", "Head", "UpperArm.L", "UpperArm.R", "Prop")}
    p["Hips"] += [cyl("legs", 0.42, 0.3, 1.05, (0, 0, 0.0), "blue_cloth", 8)]
    p["Chest"] += [cyl("torso", 0.38, 0.32, 0.65, (0, 0, 1.0), "iron", 8), box("belt", (0.78, 0.5, 0.1), (0, 0, 1.05), "gold"), sphere("padL", 0.2, (0.42, 0, 1.6), "iron", 6, 4), sphere("padR", 0.2, (-0.42, 0, 1.6), "iron", 6, 4)]
    p["Head"] += [sphere("head", 0.17, (0, 0, 1.85), "skin", 7, 5), cyl("helm", 0.22, 0.06, 0.28, (0, 0, 1.9), "iron", 8), box("plume", (0.05, 0.05, 0.3), (0, 0.05, 2.2), "red")] + face(0, -0.16, 1.87, 0.07, 0.04)
    p["UpperArm.L"] += [limb("armL", (0.4, 0, 1.6), (0.55, -0.35, 1.2), 0.1, 0.17, "iron", 6)]
    p["UpperArm.R"] += [limb("armR", (-0.4, 0, 1.6), (-0.45, -0.3, 1.5), 0.1, 0.17, "iron", 6)]
    # 깃대와 큰 깃발(펄럭이는 느낌으로 살짝 비틀림)
    p["Prop"] += [limb("pole", (-0.45, -0.3, 0.0), (-0.45, -0.3, 3.4), 0.05, 0.05, "wood", 5), box("flag", (0.05, 1.1, 0.9), (-0.45, 0.35, 2.85), "red", rot=(0, 0, 0.1)), box("flagMark", (0.06, 0.4, 0.4), (-0.45, 0.35, 2.85), "ink")]
    # 뒤따르는 병졸 4기(작고 같은 모양 — 무리라는 느낌)
    for i, (x, y) in enumerate([(-1.0, 1.0), (0.2, 1.3), (1.2, 0.9), (0.7, 2.0)]):
        p["Root"] += [cyl(f"sBody{i}", 0.2, 0.15, 0.7, (x, y, 0.0), "blue_cloth", 6), sphere(f"sHead{i}", 0.11, (x, y, 0.83), "skin", 5, 4), cyl(f"sHat{i}", 0.17, 0.05, 0.16, (x, y, 0.88), "iron", 6)]
    return p, 2.4

def mangbu():
    """⑤ 망부석 아낙(기다림): 돌로 굳어 가는 여인. 한곳을 향해 선 채 머리카락이 늘어지고 이끼가 돋음. 키 2.2m."""
    p = {k: [] for k in ("Root", "Hips", "Chest", "Head", "UpperArm.L", "UpperArm.R", "Prop")}
    p["Root"] += [box("base", (1.1, 1.1, 0.25), (0, 0, 0.125), "stone_dark")]
    p["Hips"] += [cyl("skirt", 0.5, 0.27, 1.0, (0, 0, 0.25), "stone", 7)]
    p["Chest"] += [cyl("torso", 0.27, 0.23, 0.5, (0, 0, 1.1), "stone", 7), box("moss", (0.36, 0.3, 0.1), (0.05, 0, 1.45), "leaf_dark")]
    p["Head"] += [sphere("head", 0.16, (0, 0, 1.78), "stone", 6, 4), cyl("hair", 0.2, 0.15, 0.95, (0, 0.1, 1.0), "stone_dark", 6)] + face(0, -0.15, 1.8, 0.06, 0.03, "ink")
    # 두 손을 가슴 앞에 모은 자세(기다림)
    p["UpperArm.L"] += [limb("armL", (0.22, 0, 1.5), (0.05, -0.28, 1.3), 0.07, 0.11, "stone", 5)]
    p["UpperArm.R"] += [limb("armR", (-0.22, 0, 1.5), (-0.05, -0.28, 1.3), 0.07, 0.11, "stone", 5)]
    # 손에 쥔 것: 오래된 편지(기다림의 물건)와 발치의 이끼 뭉치
    p["Prop"] += [box("letter", (0.14, 0.02, 0.2), (0, -0.32, 1.25), "hanji"), sphere("mossA", 0.18, (0.4, -0.3, 0.3), "leaf", 5, 4, (1, 1, 0.6)), sphere("mossB", 0.14, (-0.45, 0.2, 0.3), "leaf_dark", 5, 4, (1, 1, 0.6))]
    return p, 2.2

def heugwol():
    """⑥ 흑월(차사): 검은 도포와 넓은 갓, 사슬을 두른 '또 하나의 차사'. 영웅과 같은 실루엣을 일부러 닮게 했다. 키 1.95m."""
    p = {k: [] for k in ("Root", "Hips", "Chest", "Head", "UpperArm.L", "UpperArm.R", "Prop")}
    p["Hips"] += [cyl("skirt", 0.42, 0.25, 1.0, (0, 0, 0.0), "hat", 8)]
    p["Chest"] += [cyl("torso", 0.24, 0.22, 0.5, (0, 0, 1.0), "cloth", 8), box("band", (0.5, 0.34, 0.08), (0, 0, 1.05), "red")]
    p["Head"] += [sphere("head", 0.12, (0, 0, 1.6), "face", 7, 5), cyl("brim", 0.48, 0.34, 0.05, (0, 0, 1.66), "hat", 10), cyl("crown", 0.15, 0.12, 0.26, (0, 0, 1.68), "hat", 8),
                  box("eyeL", (0.04, 0.02, 0.02), (0.05, -0.12, 1.62), mat("red", 1.0)), box("eyeR", (0.04, 0.02, 0.02), (-0.05, -0.12, 1.62), mat("red", 1.0))]
    for sx, n in ((1, "UpperArm.L"), (-1, "UpperArm.R")):
        p[n] += [limb("sleeve", (sx * 0.22, 0, 1.4), (sx * 0.6, -0.3, 1.0), 0.07, 0.17, "cloth", 6), sphere("hand", 0.06, (sx * 0.62, -0.32, 0.95), "face", 5, 4)]
    # 몸을 감은 붉은 사슬 고리 3개 + 늘어진 사슬 끝의 갈고리
    for i, z in enumerate((0.5, 0.9, 1.3)):
        p["Prop"].append(cyl(f"chain{i}", 0.5 - i * 0.04, 0.5 - i * 0.04, 0.05, (0, 0, z), mat("red", 0.5), 10))
    p["Prop"] += [limb("drop", (0.55, -0.35, 1.0), (0.75, -0.9, 0.1), 0.03, 0.03, mat("red", 0.5), 4), cyl("hook", 0.12, 0.0, 0.25, (0.75, -0.9, 0.0), "iron", 5)]
    return p, 1.95

def lump():
    """⑦ 돌아선 혼들의 덩어리: 서로 등을 보이고 뭉친 혼 열한 개. 얼굴 없이 뒤통수만 보이게 했다. 키 2.8m."""
    p = {k: [] for k in ("Root", "Hips", "Chest", "Head", "UpperArm.L", "UpperArm.R", "Prop")}
    m = lambda c: mat(c, 0.5)
    spots = [(0, 0, 0.9, 0.7, "soul_lump"), (0.55, 0.1, 0.8, 0.5, "soul_old"), (-0.55, 0, 0.8, 0.5, "soul_day"), (0.2, 0.5, 1.1, 0.45, "soul_fresh"), (-0.3, 0.45, 1.2, 0.4, "soul_lump")]
    for i, (x, y, z, r, c) in enumerate(spots):
        p["Hips"].append(sphere(f"b{i}", r, (x, y, z), m(c), 7, 5, (1, 1, 1.15)))
    for i, (x, y, z, r, c) in enumerate([(0.1, 0.1, 1.75, 0.45, "soul_lump"), (0.5, 0.0, 1.5, 0.35, "soul_day"), (-0.45, 0.15, 1.6, 0.38, "soul_old"), (0.0, 0.5, 2.1, 0.32, "soul_fresh"), (0.3, 0.3, 2.35, 0.25, "soul_lump"), (-0.2, 0.2, 2.4, 0.22, "soul_day")]):
        p["Chest"].append(sphere(f"t{i}", r, (x, y, z), m(c), 7, 5))
    # 앞(-Y) 쪽은 매끈하고, 뒤쪽(+Y)에 작은 눈들이 바깥을 향해 뜬다 → 돌아선 느낌
    for i in range(5):
        a = i * 0.7
        p["Head"].append(box(f"eye{i}", (0.07, 0.02, 0.1), (math.cos(a) * 0.35 - 0.3, 0.75 + 0.05 * i, 1.0 + 0.3 * i), "face"))
    p["UpperArm.L"] += [limb("armL", (0.6, 0, 1.2), (0.95, -0.2, 0.5), 0.07, 0.12, mat("soul_old", 0.5), 5)]
    p["UpperArm.R"] += [limb("armR", (-0.6, 0, 1.2), (-0.95, -0.2, 0.5), 0.07, 0.12, mat("soul_day", 0.5), 5)]
    p["Root"] += [cyl("shadow", 1.1, 1.1, 0.03, (0, 0.2, 0.0), mat("night", 0.0), 10)]
    return p, 2.8

BOSSES = [("boss_b02_wolhwa", wolhwa), ("boss_b03_seo", seo), ("boss_b05_daedol", daedol), ("boss_b09_mangbu", mangbu), ("boss_b04_heugwol", heugwol), ("boss_b14_lump", lump)]

def build(fn):
    p, h = fn()
    parts = []
    for bone, objs in p.items(): parts += to_group(objs, bone)
    return parts, h

if __name__ == "__main__":
    rep = []
    for name, fn in BOSSES:
        reset(); parts, h = build(fn); o = join(name, parts); rig(o, bones(h))
        lo, hi = bounds(o)
        rep.append({"name": name, "tris": tris(o), "size_m": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)], "min_z": round(lo.z, 3), "bones": 7})
        export(o, os.path.join(OUT, "boss", f"{name}.glb"), apply=False)
    # 미리보기: 6종을 가로로 나란히(영웅 키 비교용 1.94m 기둥도 하나)
    reset()
    for i, (name, fn) in enumerate(BOSSES):
        parts, h = build(fn); o = join(name, parts); o.location = ((i - 2.5) * 4.2, 0, 0)
    setup_render(24, (0, 0, 1.2), size=(1500, 560), ground_size=40)
    render(os.path.join(OUT, "previews", "bosses_6_50deg.png"))
    json.dump(rep, open(os.path.join(OUT, "boss", "_report_bosses.json"), "w"), ensure_ascii=False, indent=1)
    for r in rep: print(r)
