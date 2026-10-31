"""필드 땅 전체를 '타일 조각 깔기'에서 '이어진 지형 + 구워 낸 땅 그림'으로 바꾼다. 실행: python3 terrain_ground.py [cx cy ...]  (인자 없으면 25청크 전부)
왜 바꾸나(오너 지시): 평평한 8m 타일 위에 소품만 얹은 모양이라 실제 땅처럼 안 보였다. 흙길·바퀴 자국·길섶 풀·밭고랑·논두렁·개울 자갈·마당 다짐흙·숲 바닥이
서로 자연스럽게 섞여야 한다. 타일 조각으로는 경계가 칼같이 갈라지므로, 땅을 하나로 이어 만들고 색은 '월드 좌표로 계산한 그림'(알베도)으로 칠해 섞는다.
산출물(청크 128m, 5×5):
  assets3d/terrain/chunk_{cx}_{cy}.glb  — 2m 격자 지형 메시(높낮이) + 개울 물면 + 알베도·노멀 그림(JPEG 내장). 원점=청크 남서 모서리(x=동, y=북, z=위; GLB에서는 +Y 위).
  assets3d/terrain/terrain_height_2m.png(16비트) + _terrain_manifest.json — 코드가 소품 높이를 읽는 높이표.
좌표 규약: field_5x5.json 과 같다(x=동, y=북, 원점=남서 모서리). 8m 타일 칸 중 br_*(검은여울 강 조각)가 놓인 칸은 지형에 구멍을 낸다(조각이 따로 놓임).
색·높이의 모든 값은 코드 맨 위 상수에 모았다."""
import os, sys, json, math, struct, io
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); A3 = os.path.join(HERE, "..", "..", "assets3d")
F = json.load(open(os.path.join(A3, "layouts", "field_5x5.json"), encoding="utf-8"))
VIL = json.load(open(os.path.join(A3, "layouts", "solgogae_village.json"), encoding="utf-8")); VX, VY = F["village_offset_m"]
NM = 640; T = 8; CH = 128; S = 8; PAD = 6; G = 2          # 지도 크기·타일·청크(m), 그림 해상도(px/m), 그림 가장자리 여유(px), 메시 격자(m)
TEX = CH * S + 2 * PAD                                      # 청크 그림 한 변(px)
ROAD_W = 3.2; WATER_Z = 0.18; BED_Z = 0.04; LAND_Z = 0.3; UNDULATE = 0.17   # 길 폭, 물면, 개울 바닥, 땅 윗면 기준, 자연 굴곡 크기(m)

def hexc(h): h = h.lstrip("#"); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32)
C = {k: hexc(v) for k, v in dict(
    grass_dark="#4B6838", grass_mid="#678546", grass_light="#8AA357", grass_dry="#A09F5C", flower="#E8DDA8", clover="#5A7B3E",
    road="#A8946B", road_dark="#8A7650", rut="#5E4C33", road_light="#BFAA7C", yard="#A08B62", yard_dark="#85714B", pebble="#B7AE98",
    barley_ridge="#A9A058", barley_ear="#C9B764", furrow="#66512F", bund="#7C6A44", bund_grass="#6E7F44",
    litter_pine="#7A5636", litter_leaf="#8B6A34", moss="#3E5E35", ash="#6A645A", rock_grit="#86816F",
    shore="#8D8878", wet="#4A4636", bed="#6A5B45", soil="#7A6648", cliff="#8A8678",
    foam="#E4EEEA", sick="#5B6A55", haze_purple="#5B5163", dead="#8A8456").items()}

# ───────────────────────── 재료: 노이즈·블러·표본 추출 ─────────────────────────
def _h(i, j, seed):
    n = (i.astype(np.int64) * 73856093) ^ (j.astype(np.int64) * 19349663) ^ (seed * 83492791)
    n = (n ^ (n >> 13)) * 1274126177; n = n ^ (n >> 16)
    return (n & 0xFFFF).astype(np.float32) / 65535.0

def vnoise(x, y, cell, seed=1):
    """월드 좌표 값 노이즈(0..1). 청크 경계에서도 끊기지 않는다."""
    gx, gy = x / cell, y / cell; ix, iy = np.floor(gx), np.floor(gy); fx, fy = gx - ix, gy - iy
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b, c, d = _h(ix, iy, seed), _h(ix + 1, iy, seed), _h(ix, iy + 1, seed), _h(ix + 1, iy + 1, seed)
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy

def fbm(x, y, cells, seed=1, w=None):
    w = w or [1 / (2 ** i) for i in range(len(cells))]
    return sum(vnoise(x, y, c, seed + i * 7) * wi for i, (c, wi) in enumerate(zip(cells, w))) / sum(w)

def sstep(a, b, x): t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)

def blur(a, sigma):
    r = int(sigma * 3); k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2); k /= k.sum()
    for ax in (0, 1):
        a = np.apply_along_axis(lambda v: np.convolve(np.pad(v, r, mode="edge"), k, mode="valid"), ax, a)
    return a

def samp(grid, step, x, y):
    """격자(칸 간격 step m, 원점 0,0)를 쌍선형으로 읽는다."""
    gx = np.clip(x / step, 0, grid.shape[1] - 1.001); gy = np.clip(y / step, 0, grid.shape[0] - 1.001)
    ix, iy = gx.astype(int), gy.astype(int); fx, fy = gx - ix, gy - iy
    return (grid[iy, ix] * (1 - fx) + grid[iy, ix + 1] * fx) * (1 - fy) + (grid[iy + 1, ix] * (1 - fx) + grid[iy + 1, ix + 1] * fx) * fy

def mix(a, b, t): return a * (1 - t[..., None]) + b * t[..., None]

# ───────────────────────── 지도 읽기: 칸 종류, 길 뼈대, 마당, 숲 밀도 ─────────────────────────
NC = NM // T
cell_t = np.full((NC, NC), "", dtype=object); cell_r = np.zeros((NC, NC)); cell_z = np.zeros((NC, NC))
for t in F["tiles"]: cell_t[t["iy"], t["ix"]] = t["tile"]; cell_r[t["iy"], t["ix"]] = t["rot"]; cell_z[t["iy"], t["ix"]] = t["z"]
is_br = np.vectorize(lambda s: s.startswith("br_"))(cell_t)

def rot_dirs(dirs, rot):
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot)); return [(round(dx * c - dy * s), round(dx * s + dy * c)) for dx, dy in dirs]

ROADS = []; YARDS = []          # 길 뼈대 (x0,y0,x1,y1), 마당 (cx,cy,rx,ry)
for t in F["tiles"]:
    n = t["tile"]
    if not n.startswith("terrain_tile_road"): continue
    cx, cy = t["ix"] * T + 4, t["iy"] * T + 4
    dirs = {"straight": [(1, 0), (-1, 0)], "corner": [(1, 0), (0, -1)], "t": [(1, 0), (-1, 0), (0, -1)], "end": [(1, 0)]}[n.split("_")[-1]]
    for dx, dy in rot_dirs(dirs, t["rot"]): ROADS.append((cx, cy, cx + dx * 4, cy + dy * 4))
    if n.endswith("end"):
        c, s = math.cos(math.radians(t["rot"])), math.sin(math.radians(t["rot"])); YARDS.append((cx - 0.4 * c, cy - 0.4 * s, 2.6, 2.6, "round"))
ROADS.append((VX, VY - 28, VX, VY + 24)); YARDS.append((VX + 3.4, VY - 5.5, 3.6, 2.7, "rect"))   # 마을 길(필드 길 타일과 같은 폭)
VIL_ROAD_W = 3.4
# 건물 마당: 건물(조각 모음) 둘레의 다짐흙. 필드 구조물·마을 건물 모두
FOOT = []
for s in F.get("structures", []):
    ps = s.get("pieces") or []
    if ps and not s["pieces"][0]["piece"].startswith("br_"):
        xs = [q["x"] for q in ps]; ys = [q["y"] for q in ps]; FOOT.append(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (max(xs) - min(xs)) / 2 + 1.8, (max(ys) - min(ys)) / 2 + 1.8))
for b in VIL["buildings"]:
    xs = [q["x"] + VX for q in b["pieces"]]; ys = [q["y"] + VY for q in b["pieces"]]; FOOT.append(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (max(xs) - min(xs)) / 2 + 1.6, (max(ys) - min(ys)) / 2 + 1.6))
# 평탄해야 하는 곳(건물·마을): 자연 굴곡을 죽인다
FLAT = [(x, y, max(rx, ry) + 2.0) for x, y, rx, ry in FOOT] + [(VX, VY - 2, 30.0)]
for s in F.get("structures", []):
    if "pieces" not in s and "x" in s: FLAT.append((s["x"], s["y"], 4.5))
    for q in s.get("pieces") or []:
        if not q["piece"].startswith("br_"): FLAT.append((q["x"], q["y"], 3.0))

def density(kinds, sigma, wt=None):
    g = np.zeros((NM, NM), np.float32)
    for p in F["props"]:
        if any(p["prop"].startswith(k) for k in kinds):
            ix, iy = int(min(max(p["x"], 0), NM - 1)), int(min(max(p["y"], 0), NM - 1)); g[iy, ix] += (wt or 1.0)
    return blur(g, sigma) * (2 * math.pi * sigma * sigma * 0.12)   # 블러만 하면 값이 너무 작아(나무 1그루=0.02) 숲 바닥이 안 생긴다. 번짐 면적을 곱해 '근처 나무 수'에 비례하게
D_PINE = density(["nature_pine"], 2.6); D_LEAF = density(["nature_zelkova", "nature_bamboo"], 2.6); D_DEAD = density(["nature_dead"], 2.4)
D_BUSH = density(["nature_bush", "terrain_bush"], 1.8); D_ROCK = density(["terrain_rock", "prop_big_rock", "prop_cairn", "prop_pass_cairn"], 1.4)
D_GRAVE = density(["prop_grave", "prop_tomb"], 2.0)

# ───────────────────────── 높이: 2m 격자 ─────────────────────────
NV = NM // G + 1
def tile_height(tt, rot, z, lx, ly):
    """칸 안 좌표(lx,ly: 0..8)에서 그 칸 모양의 높이. 타일 모델의 식과 같다(비탈 2m, 개울 둑)."""
    base = z + LAND_Z
    if tt in ("terrain_tile_slope_straight", "terrain_tile_slope_corner_out", "terrain_tile_slope_corner_in"):
        r = math.radians(rot); cx, cy = lx - 4, ly - 4
        u = (cx * math.cos(r) + cy * math.sin(r)) / T + 0.5; v = (-cx * math.sin(r) + cy * math.cos(r)) / T + 0.5
        h = v if tt.endswith("straight") else (min(u, v) if tt.endswith("out") else max(u, v))
        return base + 2.0 * h
    if tt == "terrain_tile_stream":
        d = lx if int(round(rot)) % 360 == 0 else T - lx      # 둑까지 거리(둑은 서쪽 가장자리 1.6m)
        return base - (LAND_Z - BED_Z) * sstep(1.4, 3.0, np.float64(d))
    return base
H_base = np.zeros((NV, NV), np.float32)
for j in range(NV):
    for i in range(NV):
        x, y = i * G, j * G; vals = []
        for ix in {min(max(int((x - 1e-6) // T), 0), NC - 1), min(int(x // T), NC - 1)}:
            for iy in {min(max(int((y - 1e-6) // T), 0), NC - 1), min(int(y // T), NC - 1)}:
                vals.append(tile_height(cell_t[iy, ix], cell_r[iy, ix], cell_z[iy, ix], min(max(x - ix * T, 0), T), min(max(y - iy * T, 0), T)))
        H_base[j, i] = sum(vals) / len(vals)
H_base = (blur(H_base, 0.9) * 0.55 + H_base * 0.45).astype(np.float32)   # 비탈 꺾임을 살짝 둥글게

def near_mask(points, x, y):
    m = np.zeros_like(x, dtype=np.float32)
    for px, py, r in points:
        m = np.maximum(m, sstep(r + 2.5, r, np.hypot(x - px, y - py)))
    return m
gx_, gy_ = np.meshgrid(np.arange(NV) * G, np.arange(NV) * G)
flat_m = near_mask(FLAT, gx_, gy_)
br_dist = np.full(gx_.shape, 99.0, np.float32)
for iy, ix in zip(*np.nonzero(is_br)):
    cx, cy = ix * T + 4, iy * T + 4; br_dist = np.minimum(br_dist, np.maximum(np.abs(gx_ - cx), np.abs(gy_ - cy)) - 4)
road_m_c = np.zeros(gx_.shape, np.float32)
for x0, y0, x1, y1 in ROADS:
    ddx, ddy = x1 - x0, y1 - y0; L2 = max(ddx * ddx + ddy * ddy, 1e-6); tt = np.clip(((gx_ - x0) * ddx + (gy_ - y0) * ddy) / L2, 0, 1)
    road_m_c = np.maximum(road_m_c, sstep(3.2, 1.6, np.hypot(gx_ - (x0 + tt * ddx), gy_ - (y0 + tt * ddy))))
stream_c = (H_base < LAND_Z - 0.05) & (np.abs(H_base - BED_Z) < 0.2) & (br_dist > 0)   # 개울 칸
amp = UNDULATE * (1 - flat_m) * sstep(0, 6, br_dist) * (1 - 0.65 * road_m_c) * (1 - 0.8 * stream_c)
H = (H_base + (fbm(gx_, gy_, [43, 19, 8], 11, [1, .6, .3]) - 0.5) * 2 * amp + (fbm(gx_, gy_, [90], 5) - 0.5) * 0.14 * amp / UNDULATE * (1 - flat_m)).astype(np.float32)
H[(br_dist < 0.5)] = np.minimum(H[(br_dist < 0.5)], LAND_Z)   # 강 조각 가장자리는 땅 윗면 높이에 맞춘다

def height_at(x, y): return samp(H, G, np.asarray(x, np.float64), np.asarray(y, np.float64))

# ───────────────────────── 그림(알베도·노멀) 한 청크 ─────────────────────────
def chunk_maps(cx, cy, s_=S, pad_=PAD, size_=CH, masks=False):
    """기본은 128m 청크 하나의 그림. s_/pad_/size_를 바꾸면 같은 규칙으로 다른 해상도·범위를 만든다(유니티 지형 섞기 지도용, masks=True면 층 비율도 돌려준다)."""
    tex = int(size_ * s_ + 2 * pad_)
    x0, y0 = cx * size_, cy * size_
    px = (np.arange(tex) - pad_ + 0.5) / s_; py = (np.arange(tex) - pad_ + 0.5) / s_
    X = x0 + px[None, :] * np.ones((tex, 1)); Y = y0 + size_ - py[:, None] * np.ones((1, tex))      # 그림 위쪽 = 북쪽
    X = X.astype(np.float64); Y = Y.astype(np.float64)
    hh = height_at(X, Y)
    gxs = (height_at(X + 1.0, Y) - height_at(X - 1.0, Y)) / 2.0; gys = (height_at(X, Y + 1.0) - height_at(X, Y - 1.0)) / 2.0
    steep = np.hypot(gxs, gys)
    cixx = np.clip((X // T).astype(int), 0, NC - 1); ciy = np.clip((Y // T).astype(int), 0, NC - 1)
    tt = cell_t[ciy, cixx]; rt = cell_r[ciy, cixx]; zz = cell_z[ciy, cixx]
    lx = X - cixx * T; ly = Y - ciy * T
    n1 = fbm(X, Y, [37, 13, 5], 21); n2 = fbm(X, Y, [2.2, 0.9], 22); n3 = vnoise(X, Y, 0.16, 23); n4 = vnoise(X, Y, 0.45, 24)
    # --- 풀바닥: 얼룩덜룩한 초록 + 마른 풀 + 잔풀 점
    g = mix(np.broadcast_to(C["grass_dark"], X.shape + (3,)), np.broadcast_to(C["grass_mid"], X.shape + (3,)), sstep(0.25, 0.6, n1))
    g = mix(g, np.broadcast_to(C["grass_light"], X.shape + (3,)), sstep(0.6, 0.85, n1) * 0.8)
    g = mix(g, np.broadcast_to(C["grass_dry"], X.shape + (3,)), sstep(0.62, 0.9, vnoise(X, Y, 23, 31)) * 0.55)
    g = g * (0.80 + 0.40 * n3[..., None]) * (0.90 + 0.20 * n2[..., None]) * (0.90 + 0.2 * vnoise(X, Y, 5.5, 36)[..., None])
    g = g * (0.9 + 0.2 * vnoise(X * 3.0, Y * 0.5, 0.25, 37)[..., None])   # 가는 풀결(동서로 긴 줄무늬 결)
    g = mix(g, np.broadcast_to(C["clover"], g.shape), sstep(0.62, 0.8, vnoise(X, Y, 3.1, 33)) * 0.4)
    fl = (vnoise(X, Y, 0.2, 34) > 0.96) & (vnoise(X, Y, 11, 35) > 0.6)
    g[fl] = C["flower"] * 0.95
    col = g; D = (n3 - 0.5) * 0.02 + (n4 - 0.5) * 0.015       # 잔 요철(m)
    # --- 구역 색조: 검은여울(병든 회녹), 폐당집(마른 자주 회색)
    def rectm(r, soft=14.0):
        return np.minimum(sstep(0, soft, X - r[0]), 1) * sstep(0, soft, r[2] - X) * sstep(0, soft, Y - r[1]) * sstep(0, soft, r[3] - Y)
    zr = {z["name"]: z["rect_m"] for z in F["zones"]}
    col = mix(col, np.broadcast_to(C["sick"], col.shape) * (0.9 + 0.2 * n2[..., None]), rectm(zr["검은여울"]) * 0.5)
    col = mix(col, np.broadcast_to(C["haze_purple"], col.shape) * (0.85 + 0.3 * n2[..., None]), rectm(zr["폐당집"], 18) * 0.55)
    col = mix(col, np.broadcast_to(C["dead"], col.shape), rectm(zr["폐당집"], 18) * 0.2 * sstep(0.4, 0.7, n1))
    # --- 비탈: 가파를수록 드러난 흙·바위
    sl = sstep(0.10, 0.26, steep) * (1 - 0.0)
    col = mix(col, np.broadcast_to(C["soil"], col.shape) * (0.85 + 0.3 * n4[..., None]), sl * 0.8)
    col = mix(col, np.broadcast_to(C["cliff"], col.shape) * (0.8 + 0.4 * n3[..., None]), sstep(0.2, 0.34, steep) * 0.5)
    # --- 숲 바닥: 솔잎·낙엽·재·이끼
    fp = samp(D_PINE, 1.0, X, Y); fz = samp(D_LEAF, 1.0, X, Y); fd = samp(D_DEAD, 1.0, X, Y); fb = samp(D_BUSH, 1.0, X, Y); fr = samp(D_ROCK, 1.0, X, Y); fg = samp(D_GRAVE, 1.0, X, Y)
    forest = np.clip(fp * 1.6 + fz * 1.4 + fd * 1.2, 0, 1)
    lit = mix(np.broadcast_to(C["litter_pine"], col.shape), np.broadcast_to(C["litter_leaf"], col.shape), np.clip(fz / (fp + fz + 1e-4), 0, 1)) * (0.8 + 0.4 * n3[..., None])
    col = mix(col, lit, sstep(0.15, 0.55, forest) * 0.85 * sstep(0.25, 0.4, vnoise(X, Y, 1.6, 41) + forest * 0.5))
    col = mix(col, np.broadcast_to(C["moss"], col.shape) * (0.8 + 0.4 * n2[..., None]), sstep(0.5, 0.7, vnoise(X, Y, 4.0, 42)) * sstep(0.1, 0.5, forest + fb * 0.4) * 0.8)
    col = mix(col, np.broadcast_to(C["ash"], col.shape), sstep(0.2, 0.7, fd) * 0.55)
    col = mix(col, np.broadcast_to(C["rock_grit"], col.shape) * (0.8 + 0.4 * n3[..., None]), sstep(0.1, 0.5, fr) * 0.8)
    col = mix(col, np.broadcast_to(C["soil"], col.shape) * (0.8 + 0.3 * n3[..., None]), sstep(0.15, 0.5, fg) * 0.6)
    D -= 0.02 * sstep(0.2, 0.6, forest) * vnoise(X, Y, 0.35, 43)
    # --- 보리밭: 이랑 7줄(칸마다 1.04m 간격, 남북으로 뻗음)과 논두렁(밭 가장자리 둑)
    bar = (tt == "terrain_tile_barley")
    if bar.any():
        f = np.mod(lx + 3.12 + 0.52, 1.04) / 1.04      # 이랑 가운데가 칸 안 -3.12 + i*1.04 (칸 중심 기준) → lx-4
        f = np.mod((lx - 4) + 3.12 + 0.52, 1.04) / 1.04
        ridge = sstep(0.12, 0.3, f) * (1 - sstep(0.7, 0.88, f)); ridge *= 1 - 0.12 * vnoise(X, Y, 0.8, 51)
        bcol = mix(np.broadcast_to(C["furrow"], col.shape) * (0.85 + 0.3 * n3[..., None]), np.broadcast_to(C["barley_ridge"], col.shape) * (0.82 + 0.3 * vnoise(X, Y, 0.25, 52)[..., None]), ridge)
        bcol = mix(bcol, np.broadcast_to(C["barley_ear"], col.shape), ridge * sstep(0.55, 0.8, vnoise(X, Y, 0.3, 53)) * 0.7)
        nb = lambda dx, dy: (cell_t[np.clip(ciy + dy, 0, NC - 1), np.clip(cixx + dx, 0, NC - 1)] != "terrain_tile_barley")
        edge = np.minimum.reduce([np.where(nb(-1, 0), lx, 99), np.where(nb(1, 0), T - lx, 99), np.where(nb(0, -1), ly, 99), np.where(nb(0, 1), T - ly, 99)])
        edge = edge + (vnoise(X, Y, 1.7, 54) - 0.5) * 0.35
        bund = sstep(1.15, 0.7, edge)
        bundc = mix(np.broadcast_to(C["bund"], col.shape) * (0.85 + 0.3 * n3[..., None]), np.broadcast_to(C["bund_grass"], col.shape), sstep(0.5, 0.75, vnoise(X, Y, 0.5, 55)) * 0.6)
        m = bar.astype(np.float32)
        col = mix(col, mix(bcol, bundc, bund), m)
        D += m * (0.07 * ridge + 0.09 * bund - 0.03)
    # --- 개울: 바닥, 자갈 둑
    wet_z = hh
    water = sstep(WATER_Z + 0.05, WATER_Z - 0.04, wet_z) * (is_stream := (tt == "terrain_tile_stream")).astype(np.float32)
    shore = sstep(LAND_Z - 0.02, LAND_Z - 0.2, wet_z) * (1 - water) * is_stream
    bedc = mix(np.broadcast_to(C["bed"], col.shape) * (0.8 + 0.4 * n4[..., None]), np.broadcast_to(C["wet"], col.shape), sstep(0.4, 0.7, vnoise(X, Y, 1.3, 61)) * 0.7)
    peb = vnoise(X, Y, 0.28, 62); pebbles = sstep(0.62, 0.74, peb)
    bedc = mix(bedc, np.broadcast_to(C["pebble"], col.shape) * (0.75 + 0.35 * vnoise(X, Y, 0.1, 63)[..., None]), pebbles * 0.8)
    shc = mix(np.broadcast_to(C["shore"], col.shape) * (0.8 + 0.4 * n3[..., None]), np.broadcast_to(C["wet"], col.shape), sstep(0.75, 0.2, shore) * 0.6)
    shc = mix(shc, np.broadcast_to(C["pebble"], col.shape), pebbles * 0.7)
    col = mix(col, shc, shore * 0.95); col = mix(col, bedc, water)
    foam_line = np.exp(-(((wet_z - WATER_Z) / 0.05) ** 2)) * is_stream.astype(np.float32)          # 물높이와 땅이 만나는 선 근처
    foam = foam_line * sstep(0.35, 0.65, vnoise(X * 2.2, Y * 0.45, 0.5, 66) * 0.7 + vnoise(X, Y, 0.18, 67) * 0.4)   # 남북으로 길게 이어지다 끊기는 거품
    foam = np.clip(foam + foam_line * 0.25, 0, 1)
    col = mix(col, np.broadcast_to(C["foam"], col.shape) * (0.9 + 0.1 * n3[..., None]), foam * 0.9)
    D += (shore + water) * (pebbles * 0.035 + (n3 - 0.5) * 0.02) + foam * 0.012
    # --- 길: 흙, 가장자리 풀 번짐, 바퀴 자국
    road = np.zeros(X.shape, np.float32); rut = np.zeros(X.shape, np.float32); fringe = np.zeros(X.shape, np.float32); centerline = np.zeros(X.shape, np.float32)
    wob = (fbm(X, Y, [9, 3.3], 71) - 0.5) * 0.6; wob2 = (vnoise(X, Y, 0.9, 72) - 0.5) * 0.35
    for x0_, y0_, x1_, y1_ in ROADS:
        if max(x0_, x1_) < X.min() - 3 or min(x0_, x1_) > X.max() + 3 or max(y0_, y1_) < Y.min() - 3 or min(y0_, y1_) > Y.max() + 3: continue
        ddx, ddy = x1_ - x0_, y1_ - y0_; L2 = max(ddx * ddx + ddy * ddy, 1e-6); u = np.clip(((X - x0_) * ddx + (Y - y0_) * ddy) / L2, 0, 1)
        d = np.hypot(X - (x0_ + u * ddx), Y - (y0_ + u * ddy))
        lat = (Y - y0_) if abs(ddx) >= abs(ddy) else (X - x0_)          # 길 가운데에서 옆으로 얼마나 떨어졌나(부호 있음)
        hw = (VIL_ROAD_W if x0_ == VX and x1_ == VX else ROAD_W) / 2 + wob + wob2
        road = np.maximum(road, sstep(0.3, -0.25, d - hw)); fringe = np.maximum(fringe, sstep(1.3, 0.2, d - hw) * (1 - sstep(0.2, -0.3, d - hw)))
        al = np.abs(lat + wob * 0.6); rr = np.exp(-(((al - 0.62) / 0.11) ** 2)) * sstep(hw - 0.2, hw - 0.7, al) * (u > -1)
        rut = np.maximum(rut, rr * sstep(0.2, -0.2, d - hw)); centerline = np.maximum(centerline, sstep(0.45, 0.1, al) * sstep(0.2, -0.2, d - hw))
    for ycx, ycy, rx, ry, kind in YARDS:
        if kind == "round": dd = np.hypot((X - ycx) / rx, (Y - ycy) / ry)
        else: dd = np.maximum(np.abs((X - ycx) / rx), np.abs((Y - ycy) / ry))
        yd = sstep(1.1 + (vnoise(X, Y, 1.8, 81) - 0.5) * 0.3, 0.88, dd); road = np.maximum(road, yd)
    # 건물 마당(다짐흙): 건물 둘레 직사각형, 가장자리는 불규칙
    yard = np.zeros(X.shape, np.float32)
    for fx_, fy_, rx, ry in FOOT:
        if abs(X.mean() - fx_) > CH and abs(Y.mean() - fy_) > CH: continue
        dd = np.maximum(np.abs((X - fx_) / rx), np.abs((Y - fy_) / ry)); yard = np.maximum(yard, sstep(1.12 + (vnoise(X, Y, 2.2, 82) - 0.5) * 0.4, 0.82, np.power(np.abs((X - fx_) / rx) ** 3 + np.abs((Y - fy_) / ry) ** 3, 1 / 3)))
    ground_dirt = np.maximum(road, yard * 0.9)
    rc = mix(np.broadcast_to(C["road"], col.shape), np.broadcast_to(C["road_dark"], col.shape), sstep(0.3, 0.7, fbm(X, Y, [6, 1.4], 91)) * 0.6)
    rc = mix(rc, np.broadcast_to(C["road_light"], col.shape), sstep(0.62, 0.85, vnoise(X, Y, 2.6, 92)) * 0.5) * (0.88 + 0.24 * n3[..., None])
    rc = mix(rc, np.broadcast_to(C["pebble"], col.shape) * (0.8 + 0.3 * n3[..., None]), sstep(0.7, 0.78, vnoise(X, Y, 0.14, 93)) * 0.7)
    rc = mix(rc, np.broadcast_to(C["rut"], col.shape), rut * 0.85)
    rc = mix(rc, np.broadcast_to(C["grass_mid"], col.shape) * (0.9 + 0.2 * n3[..., None]), centerline * sstep(0.74, 0.86, vnoise(X, Y, 0.5, 94)) * 0.8)   # 가운데 불룩한 줄에 드문드문 난 풀
    yc = mix(np.broadcast_to(C["yard"], col.shape), np.broadcast_to(C["yard_dark"], col.shape), sstep(0.35, 0.75, fbm(X, Y, [5, 1.2], 95)) * 0.6) * (0.9 + 0.2 * n3[..., None])
    yc = mix(yc, np.broadcast_to(C["pebble"], col.shape) * (0.75 + 0.3 * n3[..., None]), sstep(0.72, 0.8, vnoise(X, Y, 0.16, 96)) * 0.6)
    dirt = mix(rc, yc, np.clip((yard - road * 0.5) * 1.3, 0, 1))
    fr_g = mix(col, np.broadcast_to(C["grass_dark"], col.shape) * (0.8 + 0.4 * n3[..., None]), fringe * sstep(0.45, 0.7, vnoise(X, Y, 0.35, 97)) * 0.7)   # 길섶: 짙은 풀 무더기
    fr_g = mix(fr_g, np.broadcast_to(C["road_dark"], col.shape), fringe * sstep(0.55, 0.8, vnoise(X, Y, 0.6, 98)) * 0.35)
    col = mix(fr_g, dirt, np.clip(ground_dirt, 0, 1) * (1 - water))
    D += -0.045 * rut * (1 - yard * 0 ) + 0.02 * np.clip(ground_dirt, 0, 1) * (vnoise(X, Y, 0.3, 99) - 0.5)
    # --- 굽기: 높낮이에 따른 은은한 명암(오르막 쪽이 밝고 내리막이 어둡다 — 실제 빛은 유니티가 계산하므로 아주 약하게)
    col = col * (1.0 + 0.0 * hh[..., None])
    if masks:   # 유니티 섞기 지도: 흙(길·마당)·풀·자갈(개울 둑·바위 부스러기)·논(보리밭)·낙엽(숲 바닥)
        gd = np.clip(ground_dirt, 0, 1) * (1 - water)
        paddy = bar.astype(np.float32)
        gravel = np.clip(np.maximum(shore * 0.9 + water * 0.7, sstep(0.1, 0.5, fr) * 0.7) + pebbles * (shore + water) * 0.3, 0, 1)
        leaf = sstep(0.15, 0.55, forest) * 0.85
        dirt_w = np.clip(gd + sl * 0.7, 0, 1)
        top = np.clip(dirt_w + gravel + paddy + leaf, 0, 1)
        return dict(foam=foam, wet=np.clip(shore * 0.8 + water, 0, 1), dirt=dirt_w, gravel=gravel, paddy=paddy, leaf=leaf, grass=np.clip(1 - top, 0, 1), steep=steep, X=X, Y=Y)
    return np.clip(col, 0, 255).astype(np.uint8), D.astype(np.float32), X, Y

def normal_map(D):
    k = S / 2.0
    dx = (np.roll(D, -1, 1) - np.roll(D, 1, 1)) * k; dy_img = (np.roll(D, -1, 0) - np.roll(D, 1, 0)) * k    # 영상 아래(남쪽)로의 변화
    dy = -dy_img                                                            # 북쪽(+Y, 영상 위)으로의 변화
    amp = 6.0
    nx, ny, nz = -dx * amp, -dy * amp, np.ones_like(D); L = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack([(nx / L * 0.5 + 0.5), (ny / L * 0.5 + 0.5), (nz / L * 0.5 + 0.5)], -1)

# ───────────────────────── GLB 쓰기 ─────────────────────────
def pad4(b, c=b"\x00"): return b + c * (-len(b) % 4)

def write_glb(path, prims, images):
    """prims: [dict(pos, nrm, uv, idx, material)], images: [jpeg bytes]. 좌표는 (x,y,z=위) → glTF (x, z, -y)."""
    binb = b""; views = []; acc = []; meshp = []
    def add_view(data, target=None):
        nonlocal binb
        off = len(binb); binb += pad4(data); v = {"buffer": 0, "byteOffset": off, "byteLength": len(data)}
        if target: v["target"] = target
        views.append(v); return len(views) - 1
    for p in prims:
        pos = p["pos"].astype(np.float32); g = np.stack([pos[:, 0], pos[:, 2], -pos[:, 1]], 1); n = p["nrm"].astype(np.float32); gn = np.stack([n[:, 0], n[:, 2], -n[:, 1]], 1)
        a = {}
        for key, arr, ty, ct in (("POSITION", g, "VEC3", 5126), ("NORMAL", gn, "VEC3", 5126), ("TEXCOORD_0", p["uv"].astype(np.float32), "VEC2", 5126)):
            vi = add_view(arr.tobytes(), 34962); d = {"bufferView": vi, "componentType": ct, "count": len(arr), "type": ty}
            if key == "POSITION": d["min"] = g.min(0).tolist(); d["max"] = g.max(0).tolist()
            acc.append(d); a[key] = len(acc) - 1
        idx = p["idx"].astype(np.uint16); vi = add_view(idx.tobytes(), 34963); acc.append({"bufferView": vi, "componentType": 5123, "count": len(idx), "type": "SCALAR"})
        meshp.append({"attributes": a, "indices": len(acc) - 1, "material": p["material"], "mode": 4})
    imgv = [add_view(b) for b in images]
    has_w = len(images) > 2      # 3·4번째 그림 = 물 알베도(RGBA PNG)·물 노멀(PNG), 반복 샘플러
    j = {"asset": {"version": "2.0", "generator": "chasa terrain_ground.py"}, "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [{"mesh": 0, "name": os.path.basename(path)[:-4]}],
         "meshes": [{"primitives": meshp}], "accessors": acc, "bufferViews": views, "buffers": [{"byteLength": len(binb)}],
         "images": [{"bufferView": v, "mimeType": "image/jpeg" if k < 2 else "image/png", "name": f"{os.path.basename(path)[:-4]}_{['albedo', 'normal', 'water', 'water_normal'][k]}"} for k, v in enumerate(imgv)],
         "samplers": [{"magFilter": 9729, "minFilter": 9987, "wrapS": 33071, "wrapT": 33071}, {"magFilter": 9729, "minFilter": 9987, "wrapS": 10497, "wrapT": 10497}],
         "textures": [{"source": i, "sampler": 0 if i < 2 else 1} for i in range(len(imgv))],
         "materials": [{"name": "ground_" + os.path.basename(path)[:-4], "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}, "metallicFactor": 0.0, "roughnessFactor": 1.0}, "normalTexture": {"index": 1, "scale": 1.0}},
                       dict({"name": "water_" + os.path.basename(path)[:-4], "pbrMetallicRoughness": dict({"baseColorFactor": [1, 1, 1, 1], "metallicFactor": 0.0, "roughnessFactor": 0.06}, **({"baseColorTexture": {"index": 2}} if has_w else {})), "alphaMode": "BLEND", "doubleSided": True}, **({"normalTexture": {"index": 3, "scale": 0.8}} if has_w else {}))]}
    js = pad4(json.dumps(j, separators=(",", ":")).encode(), b" ")
    out = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(binb)) + struct.pack("<II", len(js), 0x4E4F534A) + js + struct.pack("<II", len(binb), 0x004E4942) + binb
    os.makedirs(os.path.dirname(path), exist_ok=True); open(path, "wb").write(out)

import terrain_detail as TD
WATER_TILE_M = 4.0; WATER_RGBA, WATER_NRM = TD.water_tiles(256)   # 물 그림(4m 타일, 흐름=남북)
def png_bytes(arr):
    b = io.BytesIO(); Image.fromarray(arr).save(b, "PNG", optimize=True); return b.getvalue()

def jpg(arr, q):
    b = io.BytesIO(); Image.fromarray(arr).save(b, "JPEG", quality=q, subsampling=0 if q > 90 else 2); return b.getvalue()

def build_chunk(cx, cy, save_png=False):
    col, D, X, Y = chunk_maps(cx, cy)
    nm = (normal_map(D) * 255).astype(np.uint8)
    # 지형 메시: 청크 안 2m 격자. br_ 칸은 구멍
    n = CH // G + 1; I, J = np.meshgrid(np.arange(n), np.arange(n))
    wx = cx * CH + I * G; wy = cy * CH + J * G; z = height_at(wx, wy)
    pos = np.stack([(I * G).ravel(), (J * G).ravel(), z.ravel()], 1).astype(np.float32)
    gx = (height_at(wx + G, wy) - height_at(wx - G, wy)) / (2 * G); gy = (height_at(wx, wy + G) - height_at(wx, wy - G)) / (2 * G)
    nr = np.stack([-gx.ravel(), -gy.ravel(), np.ones(n * n)], 1); nr /= np.linalg.norm(nr, axis=1, keepdims=True)
    uv = np.stack([(PAD + (I * G).ravel() * S) / TEX, (PAD + (CH - (J * G).ravel()) * S) / TEX], 1)   # glTF의 v는 위(0)→아래(1)라 그림 줄 번호 비율 그대로(뒤집으면 청크마다 남북이 거꾸로 붙는다)
    idx = []; water_cells = []
    for j in range(n - 1):
        for i in range(n - 1):
            mx, my = cx * CH + i * G + G / 2, cy * CH + j * G + G / 2
            if is_br[min(int(my // T), NC - 1), min(int(mx // T), NC - 1)]: continue
            a, b, c, d = j * n + i, j * n + i + 1, (j + 1) * n + i + 1, (j + 1) * n + i
            idx += [a, b, c, a, c, d] if (i + j) % 2 == 0 else [a, b, d, b, c, d]
            if z[j:j + 2, i:i + 2].min() < WATER_Z + 0.02 and cell_t[min(int(my // T), NC - 1), min(int(mx // T), NC - 1)] == "terrain_tile_stream": water_cells.append((i, j))
    prims = [{"pos": pos, "nrm": nr, "uv": uv, "idx": np.array(idx, np.uint16), "material": 0}]
    if water_cells:   # 개울 물면: 격자 칸 단위 평평한 판(지형 아래 부분은 깊이 시험으로 가려진다)
        wp = []; wi = []
        for k, (i, j) in enumerate(water_cells):
            x0, y0 = i * G, j * G; b0 = len(wp)
            wp += [(x0, y0, WATER_Z), (x0 + G, y0, WATER_Z), (x0 + G, y0 + G, WATER_Z), (x0, y0 + G, WATER_Z)]; wi += [b0, b0 + 1, b0 + 2, b0, b0 + 2, b0 + 3]
        wp = np.array(wp, np.float32); prims.append({"pos": wp, "nrm": np.tile([0, 0, 1.0], (len(wp), 1)), "uv": np.stack([(cx * CH + wp[:, 0]) / WATER_TILE_M, -(cy * CH + wp[:, 1]) / WATER_TILE_M], 1), "idx": np.array(wi, np.uint16), "material": 1})
    path = os.path.join(A3, "terrain", f"chunk_{cx}_{cy}.glb")
    imgs = [jpg(col, 80), jpg(nm, 82)]
    if water_cells: imgs += [png_bytes(WATER_RGBA), png_bytes(WATER_NRM)]
    write_glb(path, prims, imgs)
    if save_png: Image.fromarray(col).save(os.path.join("/tmp", f"chunk_{cx}_{cy}_albedo.png")); Image.fromarray(nm).save(os.path.join("/tmp", f"chunk_{cx}_{cy}_normal.png"))
    return {"file": f"assets3d/terrain/chunk_{cx}_{cy}.glb", "origin_m": [cx * CH, cy * CH], "tris": len(idx) // 3, "water_cells": len(water_cells), "size_kb": os.path.getsize(path) // 1024}

if __name__ == "__main__":
    args = [int(a) for a in sys.argv[1:] if a.lstrip("-").isdigit()]
    jobs = [(args[i], args[i + 1]) for i in range(0, len(args) - 1, 2)] or [(cx, cy) for cy in range(5) for cx in range(5)]
    rep = []
    for cx, cy in jobs:
        r = build_chunk(cx, cy, save_png="--png" in sys.argv); rep.append(r); print(r, flush=True)
    if len(jobs) == 25:
        hp = np.clip((H + 1.0) / 8.0, 0, 1); Image.fromarray((hp * 65535).astype(np.uint16)).save(os.path.join(A3, "terrain", "terrain_height_2m.png"))
        json.dump({"note": "땅 지형(타일 조각 대신). 청크 5×5(128m), 각 파일 원점=청크 남서 모서리. 소품 높이는 terrain_height_2m.png로 읽는다.",
                   "height_png": {"file": "terrain_height_2m.png", "size_px": [NV, NV], "step_m": G, "origin": "남서 모서리(x=0,y=0), 행 0=남쪽", "decode": "height_m = value/65535*8 - 1", "bilinear": True},
                   "chunk_m": CH, "grid_m": G, "texture": {"px_per_m": S, "pad_px": PAD, "size_px": TEX, "albedo": "JPEG sRGB", "normal": "JPEG 접선공간(OpenGL, 초록=북쪽 위)"},
                   "water": {"surface_z_m": WATER_Z, "material": "water(알파 블렌드)"}, "holes": "br_* 칸(검은여울 강 조각)은 구멍. 그 칸은 layouts tiles의 br_ 조각이 놓인다.",
                   "chunks": rep}, open(os.path.join(A3, "terrain", "_terrain_manifest.json"), "w"), ensure_ascii=False, indent=1)
