"""필드 바닥 채움 배치표 만들기(순수 파이썬, 블렌더 불필요). 실행: python3 tools/art3d/field_cover.py
입력: 땅 섞기 그림(splat_a/b), 높이표, field_5x5.json(타일), 유니티 field.json(이미 놓인 소품·건물)
산출: assets3d/layouts/field_cover.json (+ previews/field_cover_density.png : 소품 밀도 전후 비교 지도)
왜 이렇게: 나무·덤불만 6천 개 있고 땅은 비어 있었다. 구역마다 '무엇이 어울리는지'를 땅 종류(흙·풀·자갈·논·낙엽·젖은 땅)로 판단해 작은 것들을 얹는다.
  - 보릿들: 지형 이랑(칸마다 남북 7줄, 1.04m 간격)과 같은 자리에 3D 보리 줄을 세워 평평한 그림이 아니라 '자라는 밭'으로 보이게 한다. 밭머리엔 돌담·볏단·말뚝·호미 소쿠리.
  - 길가: 흙길 가장자리 풀밭에 돌탑·짚 흩어짐·돌. 길 위(흙)에는 아무것도 얹지 않는다(걷는 길 보호).
  - 강변: 물 가까이 부들·짧은 갈대·자갈밭·유목·상사화(저승 꽃). 물속(높이 낮은 곳)에는 두지 않는다.
  - 숲·폐당집: 낙엽·이끼·젖은 흙·돌, 무덤 곁 상사화.
같은 씨앗이면 같은 결과(재현 가능). 좌표는 field_5x5.json 과 같다(x=동, y=북, 원점=남서 모서리, 단위 m).
각 항목 tier: 1=필수(밭·강변·길가 소품) / 2=풀·꽃(저사양에서 코드가 줄여도 되는 것). 소품은 충돌 없는 장식이다."""
import os, json, math, random, collections
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); A3 = os.path.join(HERE, "..", "..", "assets3d")
RES = os.path.join(HERE, "..", "..", "unity", "Assets", "Resources")
NM, T = 640, 8.0; WATER_Z = 0.18
WATER_SURF = 0.12   # 이 높이 아래를 '물'로 본다(땅 굴곡이 0.13~0.47m 라 물면 0.18 로 자르면 평지 움푹이 물로 오인된다)
rnd = random.Random(20261025)

# ── 입력 읽기
sa = np.asarray(Image.open(os.path.join(A3, "terrain", "splat_a.png"))).astype(np.float32) / 255     # R=흙 G=풀 B=자갈 A=논. 행0=남쪽
sb = np.asarray(Image.open(os.path.join(A3, "terrain", "splat_b.png"))).astype(np.float32) / 255     # R=낙엽 G=거품 B=젖은 땅
hp = np.asarray(Image.open(os.path.join(A3, "terrain", "terrain_height_2m.png"))).astype(np.float32)
if hp.ndim == 3: hp = hp[..., 0] * 256 + hp[..., 1] if hp.shape[2] >= 2 and hp[..., 1].max() > 0 else hp[..., 0]
hh = hp / 65535.0 * 8 - 1; HN = hh.shape[0]
F = json.load(open(os.path.join(A3, "layouts", "field_5x5.json"), encoding="utf-8"))
FD = json.load(open(os.path.join(RES, "Data", "field.json"), encoding="utf-8"))
Z = json.load(open(os.path.join(A3, "layouts", "field_5x5_zones.json"), encoding="utf-8"))["zones"]
BOSS_CLEAR = [(580.0, 521.0, 12.0), (46.0, 453.0, 10.0)]   # build_field_data.py 와 같은 보스 마당(여유 +2m)

def px(a, x, y): return float(a[min(max(int(y), 0), NM - 1), min(max(int(x), 0), NM - 1)])
def H(x, y):
    """높이표(2m 격자, 쌍선형)에서 땅 높이 m."""
    gx, gy = min(max(x / 2, 0), HN - 1.001), min(max(y / 2, 0), HN - 1.001); i, j = int(gx), int(gy); fx, fy = gx - i, gy - j
    return float(hh[j, i] * (1 - fx) * (1 - fy) + hh[j, i + 1] * fx * (1 - fy) + hh[j + 1, i] * (1 - fx) * fy + hh[j + 1, i + 1] * fx * fy)
def dirt(x, y): return px(sa[..., 0], x, y)
def grass(x, y): return px(sa[..., 1], x, y)
def gravel(x, y): return px(sa[..., 2], x, y)
def paddy(x, y): return px(sa[..., 3], x, y)
def leaf(x, y): return px(sb[..., 0], x, y)
def wet(x, y): return px(sb[..., 2], x, y)
def zone_of(x, y):
    for z in Z:
        x0, y0, x1, y1 = z["rect_m"]
        if x0 <= x <= x1 and y0 <= y <= y1: return z["name"]
    return "들"

# 물까지의 거리(m): 높이표에서 물면보다 낮은 칸을 1m 격자로 만들고 가까운 물을 찾는다(바깥으로 6m까지만)
wat = np.zeros((NM, NM), bool)
for j in range(NM):
    for i in range(NM): wat[j, i] = H(i + 0.5, j + 0.5) < WATER_SURF
# 검은여울 강 조각(br_deep·br_rapids·br_shore, 8m 칸)은 땅에 구멍이 나 있고 조각이 따로 놓인다 → 높이표엔 물이 없다. 칸 위치로 물·점유를 만든다.
brt = {(t["ix"], t["iy"]): t["tile"] for t in F["tiles"] if t["tile"].startswith("br_")}
for (ix, iy), nm in brt.items():
    if nm in ("br_deep", "br_rapids"): wat[int(iy * T):int(iy * T + T), int(ix * T):int(ix * T + T)] = True
for (ix, iy), nm in brt.items(): wat[int(iy * T):int(iy * T + T), int(ix * T):int(ix * T + T)] = True   # 물가 타일(풀 둑 포함)도 '물 쪽'으로 쳐서, 그 바깥 가장자리부터 강변 식생이 시작되게 한다
def _chamfer(mask):
    """물 칸까지의 거리(m) 지도: 두 번 훑는 근사 거리 변환(대각 1.414). scipy 없이 numpy·파이썬만 쓴다."""
    D = np.where(mask, 0.0, 1e9).astype(np.float32); R = 1.4142
    for j in range(NM):
        for i in range(NM):
            v = D[j, i]
            if i: v = min(v, D[j, i - 1] + 1)
            if j:
                v = min(v, D[j - 1, i] + 1)
                if i: v = min(v, D[j - 1, i - 1] + R)
                if i < NM - 1: v = min(v, D[j - 1, i + 1] + R)
            D[j, i] = v
    for j in range(NM - 1, -1, -1):
        for i in range(NM - 1, -1, -1):
            v = D[j, i]
            if i < NM - 1: v = min(v, D[j, i + 1] + 1)
            if j < NM - 1:
                v = min(v, D[j + 1, i] + 1)
                if i < NM - 1: v = min(v, D[j + 1, i + 1] + R)
                if i: v = min(v, D[j + 1, i - 1] + R)
            D[j, i] = v
    return D
WD = _chamfer(wat)
def water_dist(x, y, rmax=7): return float(WD[min(max(int(y), 0), NM - 1), min(max(int(x), 0), NM - 1)])

# ── 이미 놓인 것들(점유): 1m 칸에 '반지름'을 기록해 겹치지 않게 한다
BIG = ("hanok", "giwa", "choga", "hut", "shrine", "mill", "forge", "dock", "boat", "bridge", "wall", "gate", "seonang", "stall", "cart", "house", "br_", "tomb", "grave")
occ = np.zeros((NM, NM), np.float32)
graves = []
def stamp(x, y, r):
    i0, i1, j0, j1 = int(x - r), int(x + r) + 1, int(y - r), int(y + r) + 1
    for j in range(max(j0, 0), min(j1, NM)):
        for i in range(max(i0, 0), min(i1, NM)):
            if (i + 0.5 - x) ** 2 + (j + 0.5 - y) ** 2 <= r * r: occ[j, i] = 1
for it in FD["items"]:
    if it["t"]: continue
    n = it["n"]
    r = 4.0 if any(k in n for k in BIG) else (1.1 if n.startswith(("nature_pine", "nature_zelkova", "nature_dead")) else 0.8 if n.startswith(("nature_", "terrain_")) else 1.8)
    stamp(it["x"], it["z"], r)
    if "grave" in n or "tomb" in n: graves.append((it["x"], it["z"]))
for (ix, iy) in brt: occ[int(iy * T):int(iy * T + T), int(ix * T):int(ix * T + T)] = 1   # 강 조각 칸 위에는 아무것도 얹지 않는다
def free(x, y, r=0.35):
    if not (1 <= x < NM - 1 and 1 <= y < NM - 1): return False
    if any((x - cx) ** 2 + (y - cy) ** 2 < rr * rr for cx, cy, rr in BOSS_CLEAR): return False
    i0, i1, j0, j1 = int(x - r), int(x + r) + 1, int(y - r), int(y + r) + 1
    return not occ[max(j0, 0):j1, max(i0, 0):i1].any()
def near_grave(x, y, d=7): return any((x - gx) ** 2 + (y - gy) ** 2 < d * d for gx, gy in graves)

out = []
# 새로 놓은 것끼리도 서로 겹치지 않게(작은 반지름으로 점유 기록)
def put(prop, x, y, rot=None, tier=2, r=0.3, force=False):
    if not force and not free(x, y, r): return False
    if H(x, y) < WATER_SURF + 0.01 and not prop.endswith(("cattail", "wet_boulder")): return False
    out.append({"prop": prop, "x": round(x, 2), "y": round(y, 2), "rot": int(rnd.random() * 360) if rot is None else int(rot) % 360, "z": 0.0, "zone": zone_of(x, y), "tier": tier})
    if r > 0.3: stamp(x, y, min(r, 0.9))
    return True

def vn(x, y, cell, seed):
    """값 노이즈 0..1 (field_cover 전용 간단판)."""
    gx, gy = x / cell, y / cell; ix, iy = math.floor(gx), math.floor(gy); fx, fy = gx - ix, gy - iy; fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    def h(i, j):
        n = (i * 73856093) ^ (j * 19349663) ^ (seed * 83492791); n = (n ^ (n >> 13)) * 1274126177; n ^= n >> 16
        return (n & 0xFFFF) / 65535.0
    return (h(ix, iy) * (1 - fx) + h(ix + 1, iy) * fx) * (1 - fy) + (h(ix, iy + 1) * (1 - fx) + h(ix + 1, iy + 1) * fx) * fy

# ── 1) 보리 이랑 3D 줄 (보릿들 밭 칸)
tiles = {(t["ix"], t["iy"]): t["tile"] for t in F["tiles"]}
BAR = {k for k, v in tiles.items() if v == "terrain_tile_barley"}
nbar = collections.Counter()
for (ix, iy) in sorted(BAR):
    tx, ty = ix * T, iy * T
    west = (ix - 1, iy) not in BAR; east = (ix + 1, iy) not in BAR; south = (ix, iy - 1) not in BAR; north = (ix, iy + 1) not in BAR
    ripe_tile = vn(tx + 4, ty + 4, 40, 3) > 0.52     # 넓은 구역 단위로 익은 정도가 다르다(한 밭이 얼룩덜룩하지 않게)
    for i in range(7):
        if (i == 0 and west) or (i == 6 and east): continue      # 밭 가장자리는 논두렁(흙둑) 자리라 비운다
        x = tx + 0.88 + 1.04 * i
        for k, cy in enumerate((ty + 2.0, ty + 6.0)):
            if rnd.random() < 0.07: continue                    # 가끔 비어 있는 이랑(사람 손으로 가꾼 느낌)
            if (k == 0 and south and False): continue
            ripe = ripe_tile if rnd.random() < 0.85 else not ripe_tile
            if put("cover_barley_row_ripe" if ripe else "cover_barley_row", x + (rnd.random() - .5) * 0.06, cy + (rnd.random() - .5) * 0.25, rot=rnd.choice((0, 180)), tier=1, r=0.2):
                nbar[ripe] += 1
# 밭머리 소품: 가장자리 칸 바깥쪽 1.6m. 돌담은 밭 둘레 일부, 말뚝은 모서리, 볏단·소쿠리는 드문드문
for (ix, iy) in sorted(BAR):
    tx, ty = ix * T, iy * T
    sides = {"W": (ix - 1, iy) not in BAR, "E": (ix + 1, iy) not in BAR, "S": (ix, iy - 1) not in BAR, "N": (ix, iy + 1) not in BAR}
    for s, edge in sides.items():
        if not edge: continue
        if s in "WE": ex, ey, along, rot = (tx - 1.7 if s == "W" else tx + T + 1.7), ty + rnd.uniform(1.5, 6.5), (0, 1), 90
        else: ex, ey, along, rot = tx + rnd.uniform(1.5, 6.5), (ty - 1.7 if s == "S" else ty + T + 1.7), (1, 0), 0
        if dirt(ex, ey) > 0.45: continue                         # 길 위에는 두지 않는다
        r_ = rnd.random()
        if r_ < 0.16: put("cover_stone_wall", ex, ey, rot=rot + rnd.choice((0, 180)) + rnd.uniform(-6, 6), tier=1, r=1.0)
        elif r_ < 0.24: put("cover_straw_stand", ex, ey, tier=1, r=0.5)
        elif r_ < 0.29: put("cover_hoe_basket", ex, ey, tier=1, r=0.5)
        elif r_ < 0.33: put("cover_hay_scatter", ex, ey, tier=2)
    for cx, cy, a, b in ((tx, ty, "W", "S"), (tx + T, ty, "E", "S"), (tx, ty + T, "W", "N"), (tx + T, ty + T, "E", "N")):
        if sides[a] and sides[b]: put("cover_boundary_stake", cx + (-0.9 if a == "W" else 0.9), cy + (-0.9 if b == "S" else 0.9), tier=1)

def shore_pass():
    """강변 전용 촘촘한 패스(1.2m 격자): 강·개울 둘레 6m 안을 물가 식생으로 채운다. 물 가까울수록 부들·갈대, 멀수록 자갈·상사화·풀."""
    st = 1.2; x0 = 0.0
    while x0 < NM:
        y0 = 0.0
        while y0 < NM:
            x, y = x0 + rnd.uniform(0, st), y0 + rnd.uniform(0, st); y0 += st
            if not (1 <= x < NM - 1 and 1 <= y < NM - 1): continue
            if dirt(x, y) > 0.5: continue
            wd = water_dist(x, y, 6); h = H(x, y)
            if wd > 6 or h < WATER_SURF: continue
            gr_, wt = gravel(x, y), wet(x, y); r_ = rnd.random()
            if wd <= 2.4 and r_ < 0.34: put("cover_cattail", x, y, tier=1, r=0.4)
            elif wd <= 4.2 and r_ < 0.46: put("cover_reed_short", x, y, tier=1, r=0.5)
            elif gr_ > 0.3 and r_ < 0.62: put(rnd.choice(("cover_stones_shore", "cover_stones_a", "cover_stones_shore")), x, y, tier=1, r=0.6)
            elif wd <= 5.5 and r_ < 0.68: put("cover_lily_red", x, y, tier=2, r=0.3)
            elif wt > 0.4 and r_ < 0.80: put("cover_mud_patch", x, y, tier=1, r=0.7)
            elif r_ < 0.803: put("cover_driftwood", x, y, tier=1, r=0.9)
            elif r_ < 0.83 and h > 0.2: put("cover_wet_boulder", x, y, tier=1, r=0.8)
            elif r_ < 0.9: put("cover_grass_a", x, y, tier=2)
        x0 += st
shore_pass()

# ── 2) 땅 전체 훑기: 풀·꽃·돌·강변·길가·숲바닥 (2.3m 격자 + 흔들림)
STEP = 2.3
gx = 0.0
while gx < NM:
    gy = 0.0
    while gy < NM:
        x, y = gx + rnd.uniform(0, STEP), gy + rnd.uniform(0, STEP)
        gy += STEP
        if not (1 <= x < NM - 1 and 1 <= y < NM - 1): continue
        h = H(x, y)
        zn = zone_of(x, y); d_ = dirt(x, y); g_ = grass(x, y); gr_ = gravel(x, y); pa_ = paddy(x, y); lf = leaf(x, y); wt = wet(x, y)
        if pa_ > 0.4: continue                                    # 밭 칸은 위 1)에서 처리
        wd = water_dist(x, y, 6) if (gr_ > 0.12 or wt > 0.1 or zn == "검은여울") else 99
        patch = vn(x, y, 14, 9)                                   # 14m 덩어리: 풀이 무성한 곳/성긴 곳
        # (a) 강변: 물 1~5m. 부들·짧은 갈대·자갈·유목·상사화·젖은 흙 (촘촘한 별도 패스에서 처리한다)
        if wd <= 6 and h >= WATER_SURF: continue
        if d_ > 0.5: continue                                     # 길 위(흙)는 비워 둔다. 길섶(0.1~0.5)부터 놓는다
        edge_road = 0.08 < d_ <= 0.5
        r_ = rnd.random()
        if edge_road:                                             # (b) 길가
            if r_ < 0.05: put("cover_wayside_cairn", x, y, tier=1, r=0.5)
            elif r_ < 0.12: put("cover_hay_scatter", x, y, tier=2)
            elif r_ < 0.30: put("cover_stones_a", x, y, tier=1, r=0.5)
            elif r_ < 0.62: put(rnd.choice(("cover_grass_a", "cover_grass_b", "cover_thistle")), x, y, tier=2)
            elif r_ < 0.72: put("cover_flower_white", x, y, tier=2)
            continue
        if lf > 0.35 or zn in ("물막이 골", "폐당집"):             # (c) 숲 바닥·폐당집: 낙엽·이끼·돌·젖은 흙·마른 풀
            p = 0.34 if zn != "폐당집" else 0.26
            if r_ > p: continue
            k = rnd.random()
            if k < 0.30: put("cover_leaf_litter", x, y, tier=2, r=0.7)
            elif k < 0.50: put("cover_moss_patch", x, y, tier=2, r=0.7)
            elif k < 0.66: put("cover_stones_b", x, y, tier=1, r=0.7)
            elif k < 0.78: put("cover_grass_b", x, y, tier=2)
            elif k < 0.86 and near_grave(x, y): put("cover_lily_red", x, y, tier=2, r=0.3)
            elif k < 0.92: put("cover_mud_patch", x, y, tier=2, r=0.7)
            else: put("cover_grass_c", x, y, tier=2)
            continue
        # (d) 풀밭(보릿들 둘레·검은여울 숲 사이·마을 변두리): 덩어리 노이즈로 풀 무성도 조절, 꽃은 따로 덩어리
        lush = 0.08 + 1.0 * patch * patch      # 제곱: 풀이 무성한 덩어리와 성긴 맨땅이 뚜렷이 갈린다
        if zn == "솔고개 마을": lush *= 0.55                       # 마을 안은 마당 흙·집이 주인공이라 풀을 줄인다
        if r_ < lush:
            k = rnd.random()
            dry = zn == "보릿들" and vn(x, y, 30, 5) > 0.55
            if k < 0.42: put("cover_grass_b" if dry else "cover_grass_a", x, y, tier=2)
            elif k < 0.70: put("cover_grass_c", x, y, tier=2)
            elif k < 0.84: put("cover_grass_b", x, y, tier=2)
            elif k < 0.92 and vn(x, y, 20, 7) > 0.5: put("cover_flower_mix", x, y, tier=2)
            elif k < 0.96: put("cover_flower_white", x, y, tier=2)
            elif k < 0.98: put("cover_thistle", x, y, tier=2)
            else: put("cover_stones_a", x, y, tier=1, r=0.5)
    gx += STEP

# ── 저장 + 밀도 비교 지도
cnt = collections.Counter(o["prop"] for o in out); zc = collections.Counter(o["zone"] for o in out); tc = collections.Counter(o["tier"] for o in out)
os.makedirs(os.path.join(A3, "layouts"), exist_ok=True)
json.dump({"note": "바닥 채움 소품(cover_*). 필드 좌표(x=동,y=북,m). z=0(땅 높이는 코드가 높이표로 얹는다). 충돌 없음. tier 1=밭·강변·길가 소품(필수), 2=풀·꽃(저사양에서 줄여도 됨). 1m 칸당 점유 검사를 거쳐 기존 소품·길·물과 안 겹친다.",
           "seed": 20261025, "counts": dict(cnt), "by_zone": dict(zc), "by_tier": {str(k): v for k, v in tc.items()}, "barley_rows": {"green": nbar[False], "ripe": nbar[True]}, "props": out},
          open(os.path.join(A3, "layouts", "field_cover.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("총", len(out), "tier", dict(tc)); print(dict(zc)); print(cnt.most_common())

def density(items, xy):
    g = np.zeros((NM // 8, NM // 8), np.float32)
    for a, b in xy(items): g[min(int(b // 8), 79), min(int(a // 8), 79)] += 1
    return g
before = density(FD["items"], lambda L: [(i["x"], i["z"]) for i in L if not i["t"] and not i["n"].startswith(("hanok", "br_"))])
after = before + density(out, lambda L: [(o["x"], o["y"]) for o in L])
def to_img(g, mx):
    v = np.clip(g / mx, 0, 1); rgb = np.stack([v * 255, 60 + v * 160, 200 - v * 150], -1).astype(np.uint8)[::-1]
    return Image.fromarray(rgb).resize((480, 480), Image.NEAREST)
sheet = Image.new("RGB", (980, 480), (20, 20, 28)); sheet.paste(to_img(before, 40), (0, 0)); sheet.paste(to_img(after, 40), (500, 0))
os.makedirs(os.path.join(A3, "previews"), exist_ok=True); sheet.save(os.path.join(A3, "previews", "field_cover_density.png"))
print("before 평균", round(float(before.mean()), 1), "after 평균", round(float(after.mean()), 1), "(8m 칸당)")
