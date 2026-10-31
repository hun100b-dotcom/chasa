"""1막 솔고개 생활 소품 보강(오너 "필드가 텅 빔" 지적, 코디 요청 2026-10-25).
무엇을: ① 마을(집 둘레)에 장독·땔감·가마니·건초·약초단지·연장걸이·절구돌·수레를 놓고 ② 길가에 돌탑·표지·디딤돌 ③ 숲 나무 밑에 덤불·이끼·낙엽·돌·마른 가지로 '밑풀'을 깐다.
왜: 집·나무만 있고 사람 손길(생활 소품)과 숲 바닥 층이 없어 위에서 보면 초록 카펫처럼 비었다. 쿼터뷰는 바닥 가까운 작은 소품이 '사는 곳' 느낌의 대부분이다.
규칙: 기존 막힘(집·담·나무·바위)에서 여유폭 1.0 m 이상 열린 땅에만 놓고, 길(흙 층 R>0.82)은 비운다. 같은 종류가 서로 가깝지 않게 최소 간격을 둔다.
출력: assets3d/layouts/act1_life.json (build_field_data.py가 합침). 실행: python3 tools/art3d/place_act1_life.py (멱등: 시드 고정)"""
import os, sys, json, math, random
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import walkcheck as W
from PIL import Image
ROOT = W.ROOT; LAY = W.LAY
rnd = random.Random(20261025)
bl = W.load()
f = json.load(open(os.path.join(LAY, "field_5x5.json"), encoding="utf-8"))
splat = np.array(Image.open(os.path.join(ROOT, "assets3d", "terrain", "splat_a.png")))[..., 0]   # R=흙길(행0=남쪽)
def road(x, y): return splat[min(639, max(0, int(y))), min(639, max(0, int(x)))] > 150
G = W.Grid(bl, 0, 0, 640, 640, 1.0)
def clear(x, y):
    j, i = G.idx(x, y); return G.cl[j, i] if 0 <= j < G.h and 0 <= i < G.w else -1
placed = []   # (x, y, 간격)
def free(x, y, gap): return all((x - a) ** 2 + (y - b) ** 2 >= (gap + g) ** 2 for a, b, g in placed)
props = []
def put(name, x, y, rot, folder="props", gap=1.0, note=""):
    props.append({"prop": name, "file": f"assets3d/{folder}/{name}.glb", "x": round(x, 2), "y": round(y, 2), "rot": rot, "z": 0.0, "note": note}); placed.append((x, y, gap))

# ① 마을: 집 벽 조각에서 1.8~4.5 m 떨어진 열린 땅
ox, oy = f["village_offset_m"]
walls = [(x, y) for x, y, r, n in bl if n.startswith("hanok_")]   # 마을 말고도 보릿들 마을·장터·폐당집 둘레까지 전부
V = [("prop_jangdok", 3, 1.2, "장독"), ("prop_firewood", 5, 1.4, "땔감 쌓기"), ("prop_log_pile", 3, 1.8, "통나무 더미"), ("prop_sacks", 5, 1.2, "가마니"),
     ("prop_haystack", 4, 2.0, "건초 더미"), ("prop_herb_pot", 4, 1.0, "약초 단지"), ("prop_tool_rack", 3, 1.6, "연장걸이"), ("prop_millstone", 2, 1.6, "맷돌"),
     ("prop_cart", 2, 2.4, "수레"), ("prop_stepstones", 6, 1.0, "디딤돌")]
for name, n, gap, note in [(a, b * 8, c, d) for a, b, c, d in V]:
    tries = 0; k = 0
    while k < n and tries < 4000:
        tries += 1
        wx, wy = rnd.choice(walls); x = wx + rnd.uniform(-6, 6); y = wy + rnd.uniform(-6, 6)
        d = min(math.hypot(x - a, y - b) for a, b in walls if abs(a - x) < 8 and abs(b - y) < 8) if any(abs(a - x) < 8 and abs(b - y) < 8 for a, b in walls) else 99
        if not (1.8 <= d <= 5.5): continue
        if clear(x, y) < 1.0 or road(x, y) or not free(x, y, gap): continue
        put(name, x, y, rnd.choice([0, 90, 180, 270]), gap=gap, note="마을 생활 소품: " + note); k += 1
# ② 길가: 길 가장자리(흙 층 경계)에 돌탑·표지·돌
edge = [(x, y) for y in range(8, 632, 2) for x in range(8, 632, 2) if not road(x, y) and any(road(x + dx, y + dy) for dx, dy in ((3, 0), (-3, 0), (0, 3), (0, -3)))]
rnd.shuffle(edge)
R = [("cover_wayside_cairn", "nature", 40, 6.0), ("cover_stones_a", "nature", 120, 3.0), ("cover_stones_b", "nature", 90, 3.0), ("prop_signpost", "props", 14, 12.0), ("prop_stepstones", "props", 40, 5.0)]
for name, folder, n, gap in R:
    k = 0
    for x, y in edge:
        if k >= n: break
        if clear(x, y) < 1.2 or not free(x, y, gap): continue
        put(name, x + rnd.uniform(-1, 1), y + rnd.uniform(-1, 1), rnd.randrange(360), folder, gap, "길가 소품"); k += 1
# ③ 숲 밑풀: 소나무·느티·마른나무 둘레 1.5~5 m
trees = [(p["x"], p["y"]) for p in f["props"] if p["prop"].startswith(("nature_pine", "nature_zelkova", "nature_dead"))]
U = [("nature_bush_a", 1.8, 0.5), ("nature_bush_b", 1.8, 0.5), ("nature_bush_c", 1.8, 0.5), ("cover_moss_patch", 1.2, 0.5), ("cover_leaf_litter", 1.5, 0.5), ("cover_stones_a", 1.4, 0.5), ("cover_flower_mix", 1.2, 0.5), ("nature_dead_b", 4.0, 0.9)]
rnd.shuffle(trees)
for tx, ty in trees[:2600]:
    name, gap, _ = rnd.choice(U); a = rnd.uniform(0, 6.283); d = rnd.uniform(1.6, 5.0)
    x, y = tx + math.cos(a) * d, ty + math.sin(a) * d
    if not (4 < x < 636 and 4 < y < 636) or clear(x, y) < 1.0 or road(x, y) or not free(x, y, gap): continue
    put(name, x, y, rnd.randrange(360), "nature", gap, "숲 밑풀")
from collections import Counter
json.dump({"units": "m", "axes": "x=동, y=북(필드 절대)", "note": "place_act1_life.py가 만든다. 직접 고치지 말고 스크립트를 고친다", "props": props}, open(os.path.join(LAY, "act1_life.json"), "w"), ensure_ascii=False, indent=1)
print(len(props), Counter(p["prop"] for p in props).most_common())
