"""첫 필드 5×5칸(640m) 땅 배치표. 솔고개 마을 → 보릿들 → 물막이 골 → 폐당집을 한 길로 잇는다.
순수 파이썬(블렌더 불필요). 산출: assets3d/layouts/field_5x5.json, assets3d/previews/field_5x5_map.png
왜 이렇게: 땅 조각(8m)을 칸 80×80개로 놓는 '지도'만 만들고 모델은 이미 있는 조각을 그대로 쓴다. 코드팀은 이 JSON만 읽어 땅을 깐다.

좌표: x=동쪽(m), y=북쪽(m), 원점=필드 남서쪽 모서리. 타일 (ix,iy) 중심은 (ix*8+4, iy*8+4). 128m 칸 (cx,cy)=(ix//16, iy//16).
높이 level: 0=평지, 1=고지(+2m). 고지 가장자리는 비탈 타일이 오르내림을 맡는다.
rot: 반시계 도(0이면 정면이 남쪽). 비탈은 rot 0이 '북쪽으로 오름', 길 직선은 rot 0이 '동서'."""
import os, json, math, random
from PIL import Image, ImageDraw
ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")
N, T = 80, 8.0
rnd = random.Random(640)
tile = {}   # (ix,iy) -> dict(t=타일, rot, lv)
def setT(ix, iy, t, rot=0, lv=0):
    if 0 <= ix < N and 0 <= iy < N: tile[(ix, iy)] = {"t": t, "rot": rot, "lv": lv}
def getT(ix, iy): return tile.get((ix, iy), {"t": "grass", "rot": 0, "lv": 0})
def lv(ix, iy): return getT(ix, iy)["lv"]

# ── 1) 땅 높이: 고지(고원) 사각형들 ─────────────────────────────────────────
PLATEAUS = {   # 이름: (x0,y0,x1,y1) 타일 범위(포함)
    "물막이 서쪽 벼랑": (33, 38, 40, 58), "물막이 동쪽 벼랑": (54, 36, 62, 60), "폐당집 터": (68, 64, 76, 74)}
def plateau(name, x0, y0, x1, y1, ramp=None):
    for ix in range(x0, x1 + 1):
        for iy in range(y0, y1 + 1): setT(ix, iy, "grass", 0, 1)
    for ix in range(x0, x1 + 1):
        setT(ix, y0 - 1, "slope_straight", 0); setT(ix, y1 + 1, "slope_straight", 180)
    for iy in range(y0, y1 + 1):
        setT(x0 - 1, iy, "slope_straight", -90); setT(x1 + 1, iy, "slope_straight", 90)
    setT(x0 - 1, y0 - 1, "slope_corner_out", 0); setT(x1 + 1, y0 - 1, "slope_corner_out", 90)
    setT(x1 + 1, y1 + 1, "slope_corner_out", 180); setT(x0 - 1, y1 + 1, "slope_corner_out", -90)
for k, v in PLATEAUS.items(): plateau(k, *v)

# ── 2) 길: 마을 → 보릿들 → 물막이 골 → 폐당집 (타일 좌표 꺾은선) ───────────────
ROUTE = [(24, 3), (24, 14), (44, 14), (44, 46), (48, 46), (48, 62), (72, 62)]   # 큰 길
BRANCH = {"보릿들 샛길": [(36, 14), (36, 22), (46, 22)], "굴 가는 길": [(44, 40), (41, 40)], "검은여울 가는 길": [(44, 36), (14, 36), (14, 56), (5, 56)]}
BRIDGE_COLS = (9, 10, 11); BRIDGE_ROW = 56   # 돌다리가 놓일 칸(길 타일 대신 다리 모델)
road = set()
def line(a, b):
    (x0, y0), (x1, y1) = a, b
    if x0 == x1:
        for y in range(min(y0, y1), max(y0, y1) + 1): road.add((x0, y))
    else:
        for x in range(min(x0, x1), max(x0, x1) + 1): road.add((x0 + 0 if False else x, y0))
for path in [ROUTE] + list(BRANCH.values()):
    for a, b in zip(path, path[1:]): line(a, b)
road.add((72, 63)); road.add((72, 64)) ; road.discard((72, 64))
virtual = {(x, BRIDGE_ROW) for x in BRIDGE_COLS}; road -= virtual   # 다리 자리는 길 타일을 깔지 않고, 이웃 계산에서만 길로 친다   # 폐당집 계단 앞까지만

# 폐당집 터로 올라가는 비탈 한 칸(길 끝): 남쪽 비탈 (72,63)이 램프
setT(72, 63, "slope_straight", 0)
road.discard((72, 63))
# 길 타일 고르기: 이웃 4방향을 보고 직선/모서리/T/끝을 정한다
def road_tile(ix, iy):
    nb = {d: (((ix + dx, iy + dy) in road) or ((ix + dx, iy + dy) in virtual)) for d, (dx, dy) in {"E": (1, 0), "N": (0, 1), "W": (-1, 0), "S": (0, -1)}.items()}
    # 램프 위쪽이면 이웃으로 친다
    n = sum(nb.values())
    L = lambda s: (s)
    if n == 4: return "road_t", 0   # 십자는 T로 대신(드묾)
    if n == 3:
        miss = [d for d in "ENWS" if not nb[d]][0]
        return "road_t", {"N": 0, "W": 90, "S": 180, "E": -90}[miss]
    if n == 2:
        if nb["E"] and nb["W"]: return "road_straight", 0
        if nb["N"] and nb["S"]: return "road_straight", 90
        pair = "".join(d for d in "ENWS" if nb[d])
        return "road_corner", {"ES": 0, "EN": 90, "NW": 180, "WS": -90, "SE": 0}.get("".join(sorted(pair, key="ENWS".index)), 0) if True else 0
    if n == 1:
        d = [d for d in "ENWS" if nb[d]][0]
        return "road_end", {"E": 0, "N": 90, "W": 180, "S": -90}[d]
    return "road_straight", 0
for (ix, iy) in sorted(road):
    t, r = road_tile(ix, iy)
    setT(ix, iy, t, r, lv(ix, iy))

# ── 3) 보릿들: 3×2 칸 밭 덩어리를 흩어 놓는다(길·샛길 옆) ───────────────────────
fields = []
for bx in range(28, 56, 4):
    for by in range(6, 30, 3):
        if (bx, by) in road: continue
        if any(((bx + i, by + j) in road) or ((bx + i, by + j) in tile) for i in range(3) for j in range(2)): continue
        if not (26 <= bx <= 54): continue
        if 24 - 3 <= bx <= 24 + 3: continue
        if rnd.random() < 0.75:
            for i in range(3):
                for j in range(2): setT(bx + i, by + j, "barley")
            fields.append((bx, by))

# ── 4) 물막이 골: 계곡 가운데 개울(물 칸) + 둑(보 = 물막이) ─────────────────────
for iy in range(30, 62):
    if (50, iy) not in tile and (50, iy) not in road: setT(50, iy, "stream", 0)     # 개울 서쪽 반(둑은 서쪽)
    if (51, iy) not in tile and (51, iy) not in road: setT(51, iy, "stream", 180)   # 개울 동쪽 반(둑은 동쪽)
WEIR = (50.5 * T, 48 * T)   # 물막이 위치(m)

# ── 4-2) 검은여울(2막): 남북으로 흐르는 강, 돌다리, 나루터, 의원 집 ─────────────────────────
RIVER_X = (9, 10, 11); RIVER_Y = (34, 79)
structures = []; br_props = []
import json as _j
VIL_B = _j.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets3d", "layouts", "solgogae_village.json")))["buildings"]
for iy in range(RIVER_Y[0], RIVER_Y[1] + 1):
    setT(9, iy, "br_shore", -90)                       # 서쪽 물가(물은 동쪽 절반)
    setT(10, iy, "br_rapids" if (iy // 3) % 2 == 0 else "br_deep", 90)   # 가운데는 여울과 깊은 물이 번갈아(위쪽으로 흐름)
    setT(11, iy, "br_shore", 90)                       # 동쪽 물가(물은 서쪽 절반)
for k, ix in enumerate((10, 11)):   # 돌다리 두 토막(8m씩, 물 폭 16m)
    structures.append({"piece": "br_stone_bridge", "file": "assets3d/blackrapids/br_stone_bridge.glb", "x": 80.0 + 8 * k, "y": BRIDGE_ROW * T + 4, "z": 0, "rot": 0, "note": "검은여울 돌다리"})
for px in (74.0, 94.0):   # 다리 양끝 둑 위 길 조각(물가 타일에는 길이 없어 길이 끊겨 보이던 이음새)
    structures.append({"piece": "br_road_pad", "file": "assets3d/blackrapids/br_road_pad.glb", "x": px, "y": BRIDGE_ROW * T + 4, "z": 0, "rot": 0, "note": "다리 앞 길 조각(이음새 보정)"})
structures.append({"piece": "br_ferry_dock", "file": "assets3d/blackrapids/br_ferry_dock.glb", "x": 92.4, "y": 68 * T + 4, "z": 0, "rot": -90, "note": "나루터(동쪽 둑에서 서쪽 물로 뻗음). Light_ferry_dock 포함"})
HX, HY = 6 * T + 4, 58 * T + 4   # 의원 집: 서쪽 둑, 동쪽(강·길)을 봄
from kit_buildings import place_building
structures.append({"id": "uiwon_house", "kind": "uiwon", "x": HX, "y": HY, "rot": 90, "note": "의원 집(한옥 키트 조각 목록은 pieces)", "pieces": place_building("uiwon", HX, HY, 90, gate=False)})
structures += [{"piece": "br_herb_rack", "file": "assets3d/blackrapids/br_herb_rack.glb", "x": HX + 7, "y": HY + 5, "z": 0, "rot": 0, "note": "약초 건조대"},
               {"piece": "br_med_sign", "file": "assets3d/blackrapids/br_med_sign.glb", "x": HX + 7, "y": HY - 4, "z": 0, "rot": 0, "note": "약방 깃대"},
               {"piece": "br_jars", "file": "assets3d/blackrapids/br_jars.glb", "x": HX + 5, "y": HY - 6, "z": 0, "rot": 0, "note": "약 항아리"}]
for iy in range(RIVER_Y[0] + 2, RIVER_Y[1] - 1, 4):   # 둑을 따라 버드나무
    br_props.append({"zone": "검은여울", "prop": "br_willow_a" if (iy // 4) % 2 else "br_willow_b", "x": 8 * 8 + rnd.uniform(0, 3), "y": iy * T + 3, "rot": rnd.choice((0, 90, 180)), "z": 0})
    br_props.append({"zone": "검은여울", "prop": "br_willow_b" if (iy // 4) % 2 else "br_willow_a", "x": 12 * 8 + 4 + rnd.uniform(0, 3), "y": iy * T + 5, "rot": rnd.choice((0, 90, 180)), "z": 0})
for iy in (44, 48, 64, 72, 76):   # 갈대밭(강가 바깥쪽 한 칸)
    br_props.append({"zone": "검은여울", "prop": "br_reed_field", "x": 7 * 8 + 4, "y": iy * T + 4, "rot": 0, "z": 0}); br_props.append({"zone": "검은여울", "prop": "br_reed_field", "x": 13 * 8 + 4, "y": iy * T + 4, "rot": 0, "z": 0})

# ── 5) 장식물: 지역별로 규칙에 따라 흩뿌린다 ──────────────────────────────────
props = []
occupied = {(ix, iy) for (ix, iy) in tile if tile[(ix, iy)]["t"] != "grass"}
VILLAGE = (176, 30, 216, 90)   # 마을 배치표가 따로 채우는 사각형(m)
def free(ix, iy): return (ix, iy) not in occupied and not (VILLAGE[0] <= ix * T + 4 <= VILLAGE[2] and VILLAGE[1] <= iy * T + 4 <= VILLAGE[3])
def scatter(zone, rect, kinds, count, avoid_road=True, lvl=None):
    x0, y0, x1, y1 = rect; n = 0; tries = 0
    while n < count and tries < count * 40:
        tries += 1; ix, iy = rnd.randint(x0, x1), rnd.randint(y0, y1)
        if not free(ix, iy): continue
        if lvl is not None and lv(ix, iy) != lvl: continue
        if getT(ix, iy)["t"].startswith("slope"): continue
        k = rnd.choice(kinds); x = ix * T + rnd.uniform(0.5, 7.5); y = iy * T + rnd.uniform(0.5, 7.5)
        props.append({"zone": zone, "prop": k, "x": round(x, 1), "y": round(y, 1), "rot": rnd.choice((0, 45, 90, 135, 180, 225, 270, 315)), "z": lv(ix, iy) * 2.0}); n += 1
PINE = ["nature_pine_a", "nature_pine_b", "nature_pine_c"]; ZEL = ["nature_zelkova_a", "nature_zelkova_b"]; BAM = ["nature_bamboo_a", "nature_bamboo_b"]
REED = ["nature_reed_a", "nature_reed_b", "nature_silvergrass_a", "nature_silvergrass_b"]; BUSH = ["nature_bush_a", "nature_bush_b", "nature_bush_c"]; DEAD = ["nature_dead_a", "nature_dead_b", "nature_dead_c"]
ROCK = ["terrain_rock_small", "terrain_rock_medium", "terrain_rock_cluster"]
scatter("솔고개 마을 둘레", (14, 0, 36, 16), ZEL + BUSH, 26); scatter("솔고개 마을 둘레", (14, 8, 20, 18), BAM, 14)
scatter("보릿들", (26, 5, 56, 30), BUSH + ["terrain_bush_low", "terrain_bush_flower"], 40); scatter("보릿들", (26, 5, 56, 30), ZEL, 8)
scatter("물막이 골 바닥", (42, 30, 58, 62), REED + ["terrain_bush_tall"], 60, lvl=0)
scatter("물막이 골 벼랑", (32, 36, 63, 60), PINE + ROCK, 70, lvl=1)
scatter("산자락", (0, 0, 79, 79), PINE + BUSH + ROCK, 220, lvl=0)
scatter("검은여울 둘레", (0, 34, 24, 79), PINE + BUSH + ["nature_dead_a", "nature_dead_b"], 70)
# 코드팀 요청(2차): 숲은 '군집'으로. 한 덩어리=6~12그루(그루당 약 30㎡), 덩어리 사이는 빈 풀밭, 빽빽한 곳은 덩어리를 촘촘히.
import math as _m
def cluster_grid(zone, rect, kinds, step, per=(6, 12), lvl=None, skip=0.0):
    x0, y0, x1, y1 = [v * T for v in rect]; x1 += T; y1 += T; n = 0
    gx = x0
    while gx < x1:
        gy = y0
        while gy < y1:
            if rnd.random() >= skip:
                cx, cy = gx + rnd.uniform(-step * 0.3, step * 0.3), gy + rnd.uniform(-step * 0.3, step * 0.3); k = rnd.randint(*per); r = _m.sqrt(k * 30 / _m.pi)
                for _ in range(k):
                    a_ = rnd.uniform(0, _m.tau); d_ = r * _m.sqrt(rnd.random()); x = cx + _m.cos(a_) * d_; y = cy + _m.sin(a_) * d_; ix, iy = int(x // T), int(y // T)
                    if not (0 <= ix < N and 0 <= iy < N) or not free(ix, iy) or getT(ix, iy)["t"].startswith("slope"): continue
                    if lvl is not None and lv(ix, iy) != lvl: continue
                    props.append({"zone": zone, "prop": rnd.choice(kinds), "x": round(x, 1), "y": round(y, 1), "rot": rnd.choice((0, 45, 90, 135, 180, 225, 270, 315)), "z": lv(ix, iy) * 2.0}); n += 1
            gy += step
        gx += step
    return n
FOREST = PINE * 3 + ZEL + BUSH * 2 + ROCK[:1]
WILD = PINE * 2 + DEAD * 2 + ROCK + BUSH
cluster_grid("물막이 골 숲(빽빽)", (32, 30, 63, 62), FOREST, 16, per=(8, 12))
cluster_grid("폐당집 둘레 숲(빽빽)", (60, 56, 79, 79), PINE * 3 + DEAD + BUSH, 15, per=(8, 12))
cluster_grid("보릿들 바깥 숲 띠", (24, 2, 58, 6), FOREST, 18); cluster_grid("보릿들 바깥 숲 띠", (24, 30, 58, 33), FOREST, 18); cluster_grid("보릿들 바깥 숲 띠", (24, 6, 27, 30), FOREST, 18); cluster_grid("보릿들 바깥 숲 띠", (56, 6, 59, 30), FOREST, 18)
cluster_grid("북서 숲 군집", (0, 16, 31, 47), FOREST, 30, skip=0.2)
cluster_grid("북쪽 빈 청크 채움", (16, 48, 31, 79), WILD, 28, skip=0.25); cluster_grid("북쪽 빈 청크 채움", (32, 64, 63, 79), WILD, 28, skip=0.25)
cluster_grid("마을~보릿들 길가", (24, 6, 40, 24), ZEL + BUSH + ROCK, 22, per=(4, 8), skip=0.3)

# ── 5-2) 생활감 소품(오너 피드백: 필드가 텅 비어 있다). 마을 마당·밭·갈림길·무덤·야영·가축 ─────────────────────────────
def life(prop, x, y, rot=0, zone="생활감", z=0.0):
    ix, iy = int(x // T), int(y // T)
    if 0 <= ix < N and 0 <= iy < N and getT(ix, iy)["t"].startswith(("slope", "br_", "road", "paddy", "stream")): return
    props.append({"zone": zone, "prop": prop, "x": round(x, 1), "y": round(y, 1), "rot": rot, "z": round(z if z else lv(ix, iy) * 2.0 if 0 <= ix < N and 0 <= iy < N else 0, 2)})
VX_, VY_ = 196.0, 60.0
for b_ in VIL_B:   # 집마다 뒷마당(마을 길 반대쪽): 장작·볏가리·자루·소·울타리
    sd = 1 if b_["x"] > 0 else -1; bx_, by_ = VX_ + b_["x"], VY_ + b_["y"]
    life("prop_firewood", bx_ + sd * 6.2, by_ + 1.6, 90 * sd); life("prop_haystack", bx_ + sd * 8.4, by_ - 2.2, rnd.choice((0, 90)))
    life("prop_sacks", bx_ + sd * 5.2, by_ - 1.8, rnd.choice((0, 180))); life("prop_fence", bx_ + sd * 7.9, by_ + 2.2, 90); life("prop_fence", bx_ + sd * 7.9, by_ - 1.0, 90)
    if rnd.random() < 0.7: life("prop_cow", bx_ + sd * 8.0, by_ + 2.8, rnd.choice((0, 90, 180, 270)), zone="마을 가축")
life("prop_cart", VX_ + 2.9, VY_ + 11.5, 80); life("prop_cart", VX_ - 3.0, VY_ - 17.5, -100); life("prop_millstone", VX_ + 5.0, VY_ - 6.8); life("prop_millstone", VX_ - 5.2, VY_ + 14.0)
life("prop_campfire", VX_ + 6.2, VY_ - 10.5, zone="마을 모닥불"); life("prop_log_pile", VX_ + 8.0, VY_ - 11.5, 20); life("prop_stepstones", VX_ + 5.8, VY_ + 3.2, 90); life("prop_stepstones", VX_ - 5.8, VY_ - 8.2, 90)
for k_ in range(6): life("prop_haystack", VX_ + rnd.choice((-1, 1)) * rnd.uniform(11, 14), VY_ + rnd.uniform(-22, 20), rnd.choice((0, 90)))
# 보릿들: 밭마다 허수아비·원두막·볏가리·소
for n_, (bx, by) in enumerate(fields):
    cx_, cy_ = (bx + 1.5) * T, (by + 1) * T
    if n_ % 2 == 0: life("prop_scarecrow", cx_ + rnd.uniform(-5, 5), cy_ + rnd.uniform(-3, 3), rnd.choice((0, 20, -20)), zone="보릿들 허수아비")
    if n_ % 4 == 1: life("prop_wonduumak", cx_ + 15.5, cy_ + 2.0, 0, zone="보릿들 원두막")
    if n_ % 3 == 0: life("prop_haystack", cx_ - 14.5, cy_ - 3.0, rnd.choice((0, 90)), zone="보릿들 볏가리")
    if n_ % 5 == 2: life("prop_cow", cx_ + 14.0, cy_ - 7.0, rnd.choice((0, 90, 180, 270)), zone="보릿들 가축")
    if n_ % 4 == 0: life("prop_fence", cx_ - 13.0, cy_ + 6.0, 0); life("prop_fence", cx_ - 10.0, cy_ + 6.0, 0)
# 길 갈림 팻말(갈림길 첫 칸 곁)
for pts in BRANCH.values(): life("prop_signpost", pts[0][0] * T + 8.4, pts[0][1] * T + 1.5, -15, zone="이정표")
life("prop_signpost", VX_ + 3.8, 30.0, 10, zone="이정표"); life("prop_signpost", 6 * T + 4.0, 56 * T + 7.5, 0, zone="이정표")
# 무덤: 폐당집 고지 둘레·보릿들 서쪽 언덕·검은여울 둑
for gx_, gy_, n_ in ((66 * T, 62 * T, 9), (70 * T, 68 * T, 7), (22 * T, 10 * T, 6), (20 * T, 14 * T, 5), (12 * T, 62 * T, 5)):
    for g in range(n_): life("prop_grave", gx_ + (g % 3) * 5.5 + rnd.uniform(-1, 1), gy_ + (g // 3) * 7.0 + rnd.uniform(-1, 1), rnd.choice((0, 0, 20, -15)), zone="무덤")
# 숲 속 쓰러진 통나무·그루터기, 숲길 야영 불
# ── 5-3) 2차: 촌락(보릿들 가운데, 마을 변두리 초가 군)과 개울가 방앗간 ─────────────────────────────────────────────
HAMLETS = []
def hamlet(name, cx, cy, houses, extras):
    """초가 여러 채+마당 소품. houses=[(dx,dy,rot,kind)], extras=[(prop,dx,dy,rot)]. 같은 자리의 숲·덤불은 치운다."""
    for dx, dy, rot, kind in houses:
        structures.append({"id": f"{name}_{len(structures)}", "kind": kind, "x": cx + dx, "y": cy + dy, "rot": rot, "note": f"{name}(한옥 키트 초가)", "pieces": place_building(kind, cx + dx, cy + dy, rot, gate=True)})
    for pr, dx, dy, rot in extras: props.append({"zone": "촌락 생활", "prop": pr, "x": round(cx + dx, 1), "y": round(cy + dy, 1), "rot": rot, "z": 0.0})
    HAMLETS.append({"name": name, "x": cx, "y": cy, "r": 20})
hamlet("보릿들 한가운데 마을", 324.0, 148.0, [(-11, 9, 0, "choga4"), (11, 10, 0, "choga8"), (-12, -9, 180, "choga4"), (10, -10, 180, "choga4")],
       [("prop_umul", 0, 0, 0), ("prop_jangdok", -6, 6, 0), ("prop_jangdok", 5, -5, 180), ("prop_campfire", 0, -4, 0), ("prop_haystack", -16, 0, 0), ("prop_haystack", 16, 2, 90), ("prop_cart", 5, 5, 20), ("prop_cow", -6, -2, 90), ("prop_cow", 8, 0, 270),
        ("prop_fence", -4, -14, 0), ("prop_fence", 4, -14, 0), ("prop_firewood", -15, -5, 90), ("prop_sacks", 14, -6, 0), ("prop_scarecrow", -2, 17, 0), ("prop_stepstones", 0, 8, 0)])
hamlet("마을 서쪽 변두리", 160.0, 66.0, [(0, -17, 90, "choga4"), (-1, 0, 90, "choga8"), (1, 16, 90, "choga4")],
       [("prop_haystack", -6, -8, 0), ("prop_firewood", -5, 6, 0), ("prop_cow", -7, 9, 90), ("prop_fence", -9, -14, 90), ("prop_sacks", 5, -8, 0), ("prop_millstone", 5, 8, 0)])
hamlet("마을 동쪽 변두리", 232.0, 66.0, [(0, -16, -90, "choga4"), (1, 1, -90, "choga4"), (-1, 17, -90, "choga8")],
       [("prop_haystack", 6, -6, 0), ("prop_haystack", 7, 10, 90), ("prop_cart", 6, 3, 80), ("prop_cow", 8, -2, 270), ("prop_firewood", 5, 12, 90), ("prop_fence", 9, 6, 90)])
def _clear(): 
    props[:] = [p for p in props if p["zone"] in ("촌락 생활", "생활감", "마을 가축") or not any((p["x"] - h["x"]) ** 2 + (p["y"] - h["y"]) ** 2 < h["r"] ** 2 for h in HAMLETS)]
_clear()
structures.append({"piece": "prop_mill", "file": "assets3d/props/prop_mill.glb", "x": 399.3, "y": 340.0, "z": 0, "rot": 0, "note": "개울가 방앗간(물레방아가 +X=개울 쪽)"})
for pr_, dx_, dy_, rt_ in (("prop_sacks", -3.8, -4.0, 0), ("prop_cart", -5.5, 2.5, 100), ("prop_haystack", -8.0, -1.0, 0), ("prop_stepstones", -4.0, -8.0, 0)): props.append({"zone": "방앗간", "prop": pr_, "x": round(399.3 + dx_, 1), "y": round(340.0 + dy_, 1), "rot": rt_, "z": 0.0})
scatter("통나무", (16, 16, 63, 62), ["prop_log_pile"], 70); scatter("숲 야영", (28, 30, 56, 60), ["prop_campfire"], 4, lvl=0)
life("prop_campfire", 99.5, 548.0, zone="나루터 모닥불"); life("prop_log_pile", 100.8, 551.0, 70, zone="나루터")
scatter("폐당집 터", (66, 62, 78, 76), DEAD + ROCK, 40, lvl=1); scatter("폐당집 둘레", (60, 56, 79, 79), DEAD + PINE, 45, lvl=0)

# ── 6) 표식: 동선·거점(코드팀이 NPC·서낭당·굴 입구·혼 무리 자리로 쓴다) ──────────────
M = lambda x, y, kind, name, z=0: {"kind": kind, "name": name, "x": round(x, 1), "y": round(y, 1), "z": z}
markers = [M(13 * 8 + 4, 56 * 8 + 4, "seonang", "서낭당 ④(검은여울 어귀)"), M(84, 56 * 8 + 4, "bridge", "검은여울 돌다리 한가운데"), M(92.4 - 4, 68 * 8 + 4, "ferry", "나루터(2막 뱃사공 자리 후보)"), M(HX, HY, "doctor", "의원 집(서 의원 집, 보스 ③ 서 의원 무대 후보)"), M(196, 62, "village", "솔고개 마을(원점, 마을 배치표 참조)"), M(188, 36, "seonang", "서낭당·넋길 이동 지점 ①(마을)"), M(196, 30, "spawn", "시작 위치(마을 남쪽 입구)"),
           M(3.5 * 8 * 5 + 20, 22 * 8 + 4, "seonang", "서낭당 ②(보릿들 한가운데)"), M(44 * 8 + 4, 40 * 8 + 4, "seonang", "서낭당 ③(물막이 골 어귀)"),
           M(41 * 8 - 4, 40 * 8 + 4, "cave", "굴 입구(물막이 골 서쪽 벼랑 아래, 안은 늘 밤)"), M(WEIR[0], WEIR[1], "weir", "물막이(개울을 막은 둑, 장소 이름의 유래)"),
           M(72 * 8 + 4, 69 * 8, "ruin", "폐당집 입구(터 위, 보스 ①: 나루 영감은 개울 물가로 따로)", 2.0), M(50.5 * 8, 36 * 8, "boss", "1호 보스 나루 영감 자리(개울 위 나룻배)"),
           M(36 * 8 + 4, 18 * 8, "soulpath", "넋길 시작(마을 → 보릿들, 밤에만)"), M(46 * 8, 44 * 8, "soulpath", "넋길 중간"), M(72 * 8, 62 * 8, "soulpath", "넋길 끝(폐당집)")]
for bx_, by_, bz_, br_, nt_ in ((84.6, 553.0, 0.0, 0, "나루터 곁에 맨 빈 배"), (410.5, 288.0, 0.0, 0, "보스 1호(404,288) 바로 옆 빈 나룻배(나루 영감 모델 안에도 배가 따로 있음)")):
    structures.append({"piece": "br_ferry_boat", "file": "assets3d/blackrapids/br_ferry_boat.glb", "x": bx_, "y": by_, "z": bz_, "rot": br_, "note": nt_})
for m_ in [m for m in markers if m["kind"] == "seonang"]:   # 서낭당 4곳에 실제 모델+양옆 횃대(밤 불빛). 마커만 있고 모델이 비어 있던 빈칸 보정
    structures.append({"piece": "prop_seonangdang", "file": "assets3d/props/prop_seonangdang.glb", "x": m_["x"], "y": m_["y"], "z": 0, "rot": 0, "note": m_["name"]})
    props.append({"zone": "서낭당 돌탑", "prop": "prop_cairn", "x": round(m_["x"] + 4.0, 1), "y": round(m_["y"] + 0.8, 1), "rot": 0, "z": 0})
    for dx_ in (-2.6, 2.6):
        structures.append({"piece": "night_torch_stand", "file": "assets3d/night/night_torch_stand.glb", "x": m_["x"] + dx_, "y": m_["y"] - 1.2, "z": 0, "rot": 0, "note": "서낭당 횃대(Light_ 포함)"})
zones = [{"name": "검은여울", "rect_m": [0, 272, 200, 640]}, {"name": "솔고개 마을", "rect_m": [160, 24, 232, 100]}, {"name": "보릿들", "rect_m": [208, 40, 448, 240]}, {"name": "물막이 골", "rect_m": [264, 240, 504, 500]}, {"name": "폐당집", "rect_m": [520, 500, 620, 620]}]

# ── 7) 내보내기 ─────────────────────────────────────────────────────────────
KIND = {"grass": "terrain_tile_grass", "paddy": "terrain_tile_paddy", "barley": "terrain_tile_barley", "stream": "terrain_tile_stream"}
tiles = [{"ix": ix, "iy": iy, "tile": (v["t"] if v["t"].startswith("br_") else "terrain_tile_" + v["t"]), "rot": v["rot"], "z": v["lv"] * 2.0} for (ix, iy), v in sorted(tile.items(), key=lambda a: (a[0][1], a[0][0]))]
out = {"map": "첫 필드 5×5칸 640m", "units": "m", "axes": "x=동,y=북, 원점=남서쪽 모서리, 타일 중심=(ix*8+4, iy*8+4)", "grid": {"tiles": [N, N], "tile_m": T, "cell_m": 128, "cells": [5, 5]},
       "default_tile": "terrain_tile_grass(표에 없는 칸은 풀밭, z=0)", "rotation": "반시계 도. 비탈 0=북쪽으로 오름, 길 직선 0=동서",
       "provisional": "비탈 모서리(slope_corner_out)의 rot는 추정값. 유니티에서 높이가 어긋나면 rot를 ±90 보정(코드팀 QA).",
       "zones": zones, "tiles": tiles, "props": props + br_props, "structures": structures, "file_dirs": {"terrain_*": "assets3d/terrain/", "nature_*": "assets3d/nature/", "br_*": "assets3d/blackrapids/", "hanok_*": "assets3d/hanok/", "prop_*": "assets3d/props/", "night_*": "assets3d/night/"}, "markers": markers, "village_layout": "assets3d/layouts/solgogae_village.json (원점 = 필드 (196,60)에 놓는다)",
       "village_offset_m": [196, 60], "counts": {"tiles(비풀밭)": len(tiles), "props": len(props) + len(br_props), "structures": len(structures), "paddy": sum(1 for t in tiles if t["tile"].endswith("paddy")), "barley": sum(1 for t in tiles if t["tile"].endswith("barley"))}}
json.dump(out, open(os.path.join(ROOT, "layouts", "field_5x5.json"), "w"), ensure_ascii=False, indent=1)

# 눈으로 보는 지도(타일 1칸=8px)
S = 8; im = Image.new("RGB", (N * S, N * S), "#6F7B5B"); d = ImageDraw.Draw(im)
COL = {"road": "#C9B38A", "paddy": "#4F7A8A", "slope": "#9CC25F"}
for (ix, iy), v in tile.items():
    c = "#1C2744" if v["t"] in ("br_rapids", "br_deep") else "#3E5A7A" if v["t"] == "br_shore" else "#C9B38A" if v["t"].startswith("road") else "#4F7A8A" if v["t"] == "paddy" else "#D2B864" if v["t"] == "barley" else "#2B3A66" if v["t"] == "stream" else "#B7D77A" if v["t"].startswith("slope") else ("#8FA66C" if v["lv"] else "#6F7B5B")
    if v["lv"] and v["t"] == "grass": c = "#8FA66C"
    d.rectangle([ix * S, (N - 1 - iy) * S, ix * S + S - 1, (N - 1 - iy) * S + S - 1], fill=c)
for p in props:
    d.point((p["x"] / T * S, (N - p["y"] / T) * S), fill="#2F5A44" if "pine" in p["prop"] else "#3A3A44" if "dead" in p["prop"] else "#5E7A3C")
d.rectangle([VILLAGE[0] / T * S, (N - VILLAGE[3] / T) * S, VILLAGE[2] / T * S, (N - VILLAGE[1] / T) * S], outline="#E85C41")
for st in structures:
    if "piece" in st and "bridge" in st["piece"]: d.rectangle([st["x"] / T * S - 4, (N - st["y"] / T) * S - 2, st["x"] / T * S + 4, (N - st["y"] / T) * S + 2], fill="#B4B2BC")
for m in markers:
    d.ellipse([m["x"] / T * S - 3, (N - m["y"] / T) * S - 3, m["x"] / T * S + 3, (N - m["y"] / T) * S + 3], fill={"seonang": "#FFFFFF", "cave": "#000000", "ruin": "#9A5CFF", "boss": "#E85C41"}.get(m["kind"], "#FFCC55"))
for i in range(1, 5): d.line([(i * 16 * S, 0), (i * 16 * S, N * S)], fill="#00000055"); d.line([(0, i * 16 * S), (N * S, i * 16 * S)], fill="#00000055")
im = im.resize((N * S * 2, N * S * 2), Image.NEAREST); im.save(os.path.join(ROOT, "previews", "field_5x5_map.png"))
print(out["counts"])
