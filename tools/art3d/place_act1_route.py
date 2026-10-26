"""1막 솔고개 처음 10분 길 소품 배치표. 실행: python3 place_act1_route.py → assets3d/layouts/act1_route.json, act1_route_report.json
왜: 처음 5분 흐름의 걷는 길(시작 위치→우물→보릿들 둑길→대장간, nav_points.json 의 웨이포인트)을 10 m 간격으로 재서, 8 m 안 소품이 6개 아래인 구간('빈 곳')에 소품을 채운다.
 (점검 결과: 시작 길 6, 마을 서쪽 길 0~5, 둑길 동쪽 끝 x 233~297 은 0~2개.)
방식: place_act1_life.py 와 같다 — 막힘(집·담·나무·바위)에서 여유폭 1.0 m 이상, 흙길(splat R>150) 위는 비운다, 같은 종류 최소 간격. 길 한가운데 3 m 안은 항상 비운다(걸을 폭).
구역별 팔레트: 둑길 동쪽(x>225)은 농사 소품(새 a1r_ 9종 + 허수아비·건초·수레), 마을 어귀·서쪽은 생활 소품, 시작 길은 길가 소품.
작성: 아트. 직접 고치지 말고 스크립트를 고친다(시드 고정, 멱등)."""
import os, sys, json, math, random
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import walkcheck as W
from PIL import Image
ROOT = W.ROOT; LAY = W.LAY; rnd = random.Random(20261026)
bl = W.load(); G = W.Grid(bl, 0, 0, 640, 640, 1.0)
splat = np.array(Image.open(os.path.join(ROOT, "assets3d", "terrain", "splat_a.png")))[..., 0]
def road(x, y): return splat[min(639, max(0, int(y))), min(639, max(0, int(x)))] > 150
def clear(x, y):
    j, i = G.idx(x, y); return G.cl[j, i] if 0 <= j < G.h and 0 <= i < G.w else -1
ROUTES = {"우물": [(193, 28.5), (198, 47.5), (198, 59)], "둑길": [(193, 28), (163, 36), (190, 112), (288, 152)], "보릿들길": [(288, 152), (355, 250), (362, 286), (399, 283)], "대장간": [(193, 28.5), (220, 45), (217, 57.5)]}
def sample(poly, step):
    pts = []
    for a, b in zip(poly[:-1], poly[1:]):
        n = max(1, int(math.dist(a, b) / step)); pts += [(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(n)]
    pts.append(poly[-1]); return pts
def dist_route(x, y): return min(math.dist((x, y), p) for poly in ROUTES.values() for p in sample(poly, 2))
# 이미 있는 모든 소품(점검용): 필드 + 1막 보강 두 파일 + 마을
allp = []
f = json.load(open(os.path.join(LAY, "field_5x5.json"), encoding="utf-8")); allp += [(p["x"], p["y"]) for p in f["props"]]
for n in ("act1_extra", "act1_life"): allp += [(p["x"], p["y"]) for p in json.load(open(os.path.join(LAY, n + ".json")))["props"]]
v = json.load(open(os.path.join(LAY, "solgogae_village.json"))); ox, oy = f["village_offset_m"]; allp += [(p["x"] + ox, p["y"] + oy) for p in v["props"] if "x" in p]
placed = []; props = []; rep = {"before": {}, "after": {}}
def count(x, y, r=8.0, extra=()): return sum(1 for a, b in allp if math.hypot(a - x, b - y) < r) + sum(1 for a, b, _ in extra if math.hypot(a - x, b - y) < r)
def free(x, y, gap): return all((x - a) ** 2 + (y - b) ** 2 >= (gap + g) ** 2 for a, b, g in placed)
def put(name, x, y, rot, folder, gap, note):
    props.append({"prop": name, "file": f"assets3d/{folder}/{name}.glb", "x": round(x, 2), "y": round(y, 2), "rot": rot, "z": 0.0, "note": note}); placed.append((x, y, gap))
FARM = [("a1r_sheaf_stack", "props", 2.2, "보릿단 말림"), ("a1r_ridge_marker", "props", 3.0, "두렁 말뚝"), ("a1r_water_gate", "props", 2.0, "물꼬"), ("a1r_bird_line", "props", 3.0, "새 쫓는 줄"), ("a1r_lean_to", "props", 4.0, "원두막"),
        ("a1r_manure_heap", "props", 2.0, "두엄 더미"), ("prop_scarecrow", "props", 2.0, "허수아비"), ("prop_haystack", "props", 2.0, "건초 더미"), ("cover_stones_a", "nature", 2.5, "밭 돌"), ("nature_bush_b", "nature", 2.0, "밭둑 덤불"), ("cover_flower_mix", "nature", 2.5, "둑 들꽃")]
LIFE = [("a1r_gourd_trellis", "props", 2.0, "박 시렁"), ("a1r_drink_jars", "props", 2.0, "길가 물독"), ("a1r_wayside_rest", "props", 2.5, "길가 쉼터"), ("prop_jangdok", "props", 1.5, "장독"), ("prop_firewood", "props", 1.5, "땔감"), ("prop_log_pile", "props", 1.8, "통나무 더미"),
        ("prop_sacks", "props", 1.5, "가마니"), ("nature_bush_a", "nature", 2.0, "길섶 덤불"), ("cover_stones_b", "nature", 2.5, "길가 돌"), ("prop_stepstones", "props", 1.5, "디딤돌")]
DENS = {"둑길": (12.0, 40), "보릿들길": (10.0, 28)}      # 24 m 점검: 화면에 담기는 땅이 넓어(반경 약 20 m) 반경 8 m·8개로는 빈 풀밭으로 보임 → 이 두 길은 반경 10 m 안 14~16개
def pick(x, y):
    # 둑길 동쪽 끝(보릿들)은 농사, 그 밖은 생활 소품
    return FARM if x > 215 and y > 95 else LIFE
for name, poly in ROUTES.items():
    for x, y in sample(poly, 10):
        c0 = count(x, y); rep["before"].setdefault(name, []).append([round(x), round(y), c0])
# 둑길 동쪽 한가운데에 원두막 하나는 먼저 고정(첫 '둘러싸임' 싸움판의 눈에 띄는 표지)
for cx, cy in ((262, 122), (270, 124), (255, 121), (275, 120), (262, 98), (270, 96)):
    if clear(cx, cy) >= 2.0 and not road(cx, cy) and dist_route(cx, cy) >= 6.0: put("a1r_lean_to", cx, cy, 0, "props", 4.0, "처음 10분 길 보강: 원두막(둑길 표지)"); break
for name, poly in ROUTES.items():
    for x, y in sample(poly, 10):
        R_, T_ = DENS.get(name, (8.0, 8)); need = T_ - count(x, y, r=R_, extra=placed); tries = 0
        while need > 0 and tries < 1500:
            tries += 1; a = rnd.uniform(0, math.tau); d = rnd.uniform(3.5, 12.0); px, py = x + math.cos(a) * d, y + math.sin(a) * d
            nm, folder, gap, note = rnd.choice(pick(px, py))
            if not (4 < px < 636 and 4 < py < 636) or clear(px, py) < 1.0 or road(px, py) or dist_route(px, py) < 3.0 or not free(px, py, gap): continue
            if sum(1 for p in props if p["prop"] == nm) >= {"a1r_lean_to": 3, "a1r_bird_line": 4, "prop_scarecrow": 3, "a1r_wayside_rest": 4, "a1r_manure_heap": 3, "prop_haystack": 6, "a1r_water_gate": 4}.get(nm, 999) * 6: continue
            put(nm, px, py, rnd.choice([0, 90, 180, 270]) if nm not in ("a1r_bird_line", "a1r_water_gate") else rnd.choice([0, 180]), folder, gap, "처음 10분 길 보강: " + note); need -= 1
            if name in DENS and rnd.random() < 0.6:      # 한 덩어리로 읽히게 곁에 풀꽃·돌·덤불 1~2개를 붙인다(홀로 떨어진 소품은 점처럼 보임)
                for _ in range(rnd.choice([1, 2])):
                    cn, cf, cg = rnd.choice([("cover_flower_mix", "nature", 1.0), ("cover_stones_a", "nature", 1.2), ("nature_bush_a", "nature", 1.6)]); a2 = rnd.uniform(0, math.tau); d2 = rnd.uniform(1.8, 3.2); qx, qy = px + math.cos(a2) * d2, py + math.sin(a2) * d2
                    if 4 < qx < 636 and 4 < qy < 636 and clear(qx, qy) >= 1.0 and not road(qx, qy) and dist_route(qx, qy) >= 3.0 and free(qx, qy, cg): put(cn, qx, qy, rnd.choice([0, 90, 180, 270]), cf, cg, "처음 10분 길 보강: 곁붙임"); need -= 1
for name, poly in ROUTES.items():
    for x, y in sample(poly, 10): rep["after"].setdefault(name, []).append([round(x), round(y), count(x, y, extra=placed)])
from collections import Counter
rep["count"] = len(props); rep["per_model"] = dict(Counter(p["prop"] for p in props))
json.dump({"units": "m", "axes": "x=동, y=북(필드 절대)", "note": "place_act1_route.py가 만든다. 직접 고치지 말고 스크립트를 고친다. act1_life.json 옆에 같이 읽는다. z=0(1막 땅은 평평)", "props": props}, open(os.path.join(LAY, "act1_route.json"), "w"), ensure_ascii=False, indent=1)
json.dump(rep, open(os.path.join(LAY, "act1_route_report.json"), "w"), ensure_ascii=False, indent=1)
print(len(props), rep["per_model"])
for k in rep["before"]: print(k, "전", [c for *_, c in rep["before"][k]], "후", [c for *_, c in rep["after"][k]])
