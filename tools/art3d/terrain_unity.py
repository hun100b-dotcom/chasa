"""코드팀(유니티) 형식의 땅 자료를 만든다. 약속: docs/TERRAIN-FORMAT.md (브랜치 claude/project-thread-ozfksa).
실행: python3 terrain_unity.py   → assets3d/terrain/ 에 terrain.json, heightmap.png(16비트=R·G), splat_a.png(흙·풀·자갈·논), splat_b.png(낙엽), layer_*.png(이음매 없는 512²)
왜 두 가지(청크 GLB + 이 자료)인가: 유니티 땅 시스템은 높이 지도와 섞기 지도를 받는다. 같은 규칙(terrain_ground.chunk_maps)에서 뽑아 두 길이 같은 땅을 보이게 한다.
행 0 = y 0(남쪽), 위쪽 줄이 남쪽이다(코드팀 약속)."""
import os, sys, json, numpy as np
from PIL import Image
import terrain_ground as tg
from terrain_ground import vnoise, fbm, sstep, mix, C

OUT = os.path.join(tg.A3, "terrain")
HMIN, HMAX = -1.0, 8.0          # 높이 범위(m). 개울 바닥 0.04, 강 조각 안쪽 -0.1, 비탈 위 2.3 정도라 넉넉
RES = 640


# ───────────────────────── 큰 강 물길(검은여울) ─────────────────────────
RIVER_BED_C, RIVER_BED_E, RIVER_LAND = -0.30, -0.10, tg.LAND_Z   # 강 한가운데 바닥, 물가 쪽 바닥, 둑 윗면(m). 물면은 tg.WATER_Z=0.18
def river_geom():
    """br_* 칸에서 강의 뼈대를 읽는다. 물가 칸(br_shore) 둘은 서쪽 둑 칸(rot −90: 물이 동쪽 절반)·동쪽 둑 칸(rot 90: 물이 서쪽 절반)이라 물은 두 칸 중심 사이(x 76~92m)."""
    br = [t for t in tg.F["tiles"] if t["tile"].startswith("br_")]
    xw = min(t["ix"] * tg.T + 4 for t in br if t["tile"] == "br_shore" and int(round(t["rot"])) % 360 == 270)
    xe = max(t["ix"] * tg.T + 4 for t in br if t["tile"] == "br_shore" and int(round(t["rot"])) % 360 == 90)
    return dict(x0=xw, x1=xe, y0=min(t["iy"] for t in br) * tg.T, y1=(max(t["iy"] for t in br) + 1) * tg.T)

def river_field(X, Y):
    """좌표 (X,Y)에서 물길을 판 높이 z, 물길 축에서의 거리 r, 그곳의 물가 반폭 rw를 돌려준다. 단면: 한가운데 깊고(−0.30) → 물가로 갈수록 얕아지다(−0.10) → 물가선(물면보다 살짝 아래) → 둑(0.30).
    물가선은 길이 방향 노이즈로 ±0.5m 구불거리고(안쪽으로만 물러남 = 조각 모델 물판이 둑 밖으로 안 나옴), 남쪽 끝은 둥글게 닫는다. 칸 경계와 무관하게 이어진다."""
    g = river_geom(); xc = (g["x0"] + g["x1"]) / 2; hw = (g["x1"] - g["x0"]) / 2
    wob = tg.fbm(np.full_like(Y, xc), Y, [37.0, 13.0], 71, [1, 0.5])
    rw = hw - 0.25 - 0.55 * wob                                      # 물가선 반폭(≈7.2~7.75m)
    v = np.maximum(0.0, (g["y0"] + hw) - Y)                           # 남쪽 끝 둥근 마감
    r = np.hypot(np.abs(X - xc), v)
    t = np.clip(r / np.maximum(rw - 2.2, 0.1), 0, 1)
    bed = RIVER_BED_C + (RIVER_BED_E - RIVER_BED_C) * t ** 2
    s1 = tg.sstep(rw - 2.2, rw, r); s2 = tg.sstep(rw, rw + 1.8, r)
    bed = bed + (tg.fbm(X, Y, [6.0, 2.2], 73) - 0.5) * 0.06 * (1 - s1)    # 바닥 잔물결
    z = bed * (1 - s1) + (tg.WATER_Z - 0.03) * s1
    z = z * (1 - s2) + RIVER_LAND * s2
    return z, r, rw

def height_grid():
    """1m 간격 641×641 높이. 강 조각 칸(br_*) 안쪽은 살짝 낮춰 물길이 파인 느낌을 준다(조각 모델은 따로 놓임)."""
    xs = np.arange(RES + 1, dtype=np.float64); X, Y = np.meshgrid(xs, xs)
    h = tg.height_at(X, Y).astype(np.float64)
    # 큰 강(검은여울): 8m 칸 단위가 아니라 강 전체를 하나의 연속 물길로 판다(칸 경계에 둑이 남아 웅덩이 격자로 보이던 문제 해결)
    z, r, rw = river_field(X, Y)
    h = np.where(r < rw + 1.9, np.minimum(h, z), h)
    return h

def write_height(h):
    v = np.clip((h - HMIN) / (HMAX - HMIN), 0, 1) * 65535; v = np.round(v).astype(np.uint32)
    rgba = np.zeros(h.shape + (4,), np.uint8); rgba[..., 0] = v >> 8; rgba[..., 1] = v & 255; rgba[..., 3] = 255
    Image.fromarray(rgba, "RGBA").save(os.path.join(OUT, "heightmap.png"))

def write_splats():
    m = tg.chunk_maps(0, 0, s_=1, pad_=0, size_=tg.NM, masks=True)
    z_, r_, rw_ = river_field(m["X"], m["Y"])   # 강 안쪽·둑은 자갈과 젖은 땅, 물가선에는 길게 이어진 거품(물이 땅과 만나는 선)
    gr = 1 - tg.sstep(rw_ + 0.6, rw_ + 2.6, r_); wetr = 1 - tg.sstep(rw_ - 0.1, rw_ + 1.6, r_)
    line = np.exp(-(((r_ - rw_) / 0.4) ** 2)) * tg.sstep(0.3, 0.6, tg.vnoise(m["X"] * 0.5, m["Y"] * 2.2, 1.0, 66) * 0.7 + tg.vnoise(m["X"], m["Y"], 0.4, 67) * 0.4)
    m["gravel"] = np.maximum(m["gravel"], gr); m["dirt"] = m["dirt"] * (1 - gr); m["paddy"] = m["paddy"] * (1 - gr); m["leaf"] = m["leaf"] * (1 - gr)
    m["foam"] = np.clip(np.maximum(m["foam"], line), 0, 1); m["wet"] = np.maximum(m["wet"], wetr)
    m["grass"] = np.clip(1 - (m["dirt"] + m["gravel"] + m["paddy"] + m["leaf"]), 0, 1)
    a = np.stack([m["dirt"], m["grass"], m["gravel"], m["paddy"]], -1); b = m["leaf"]; fo = tg.blur(m["foam"], 0.5); wt = tg.blur(m["wet"], 0.8)
    # 칸 경계를 부드럽게: 논·흙 가장자리가 1m 격자에서 들쭉날쭉하지 않도록 아주 약하게 번지게 한다
    for k in range(4): a[..., k] = tg.blur(a[..., k], 0.6)
    b = tg.blur(b, 0.8)
    # 위쪽 줄 = 남쪽(y=0)이 되도록 뒤집는다(chunk_maps는 영상 위=북쪽)
    A = (np.clip(a, 0, 1)[::-1] * 255).astype(np.uint8); B = (np.clip(b, 0, 1)[::-1] * 255).astype(np.uint8)
    Image.fromarray(A, "RGBA").save(os.path.join(OUT, "splat_a.png"))
    FO = (np.clip(fo, 0, 1)[::-1] * 255).astype(np.uint8); WT = (np.clip(wt, 0, 1)[::-1] * 255).astype(np.uint8)
    # splat_b: R=낙엽(약속), G=물가 거품, B=젖은 땅(약속 밖 덤. 유니티 셰이더가 원하면 읽고 아니면 무시)
    Image.fromarray(np.stack([B, FO, WT, np.full_like(B, 255)], -1), "RGBA").save(os.path.join(OUT, "splat_b.png"))
    return m

def tileable(fn, n=512, cell_m=6.0):
    """이음매 없는 반복 그림: 노이즈 격자를 가로·세로로 감싸게(주기적으로) 만든다."""
    yy, xx = np.meshgrid(np.arange(n), np.arange(n), indexing="ij")
    def pn(cells, seed):   # cells칸 주기 값 노이즈 (n 픽셀이 정확히 cells칸)
        g = np.random.RandomState(seed).rand(cells, cells).astype(np.float32)
        fx = xx / n * cells; fy = yy / n * cells; ix = np.floor(fx).astype(int); iy = np.floor(fy).astype(int); tx = fx - ix; ty = fy - iy
        tx = tx * tx * (3 - 2 * tx); ty = ty * ty * (3 - 2 * ty)
        a = g[iy % cells, ix % cells]; b = g[iy % cells, (ix + 1) % cells]; c = g[(iy + 1) % cells, ix % cells]; d = g[(iy + 1) % cells, (ix + 1) % cells]
        return (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty
    return fn(pn)

def make_layers():
    def save(name, arr): Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(os.path.join(OUT, f"layer_{name}.png"))
    def col(c, f): return np.asarray(c, np.float32)[None, None, :] * f[..., None]
    # 풀: 얼룩 + 가는 결 + 마른 풀
    def grass(pn):
        n1 = 0.5 * pn(4, 1) + 0.3 * pn(8, 2) + 0.2 * pn(16, 3); f = 0.8 + 0.4 * pn(64, 4) * (0.7 + 0.3 * pn(128, 5))
        base = mix(np.broadcast_to(C["grass_dark"], n1.shape + (3,)), np.broadcast_to(C["grass_light"], n1.shape + (3,)), sstep(0.3, 0.7, n1))
        base = mix(base, np.broadcast_to(C["grass_dry"], base.shape), sstep(0.62, 0.85, pn(5, 6)) * 0.5)
        return base * f[..., None]
    def dirt(pn):
        n1 = 0.5 * pn(4, 11) + 0.5 * pn(10, 12); f = 0.85 + 0.3 * pn(64, 13)
        base = mix(np.broadcast_to(C["road"], n1.shape + (3,)), np.broadcast_to(C["road_dark"], n1.shape + (3,)), sstep(0.35, 0.7, n1) * 0.7)
        base = mix(base, np.broadcast_to(C["road_light"], base.shape), sstep(0.62, 0.85, pn(14, 14)) * 0.4)
        peb = sstep(0.74, 0.8, pn(96, 15)); base = mix(base, np.broadcast_to(C["pebble"], base.shape) * 0.9, peb * 0.6)
        return base * f[..., None]
    def gravel(pn):
        p1 = pn(48, 21); p2 = pn(96, 22); f = 0.7 + 0.5 * p1 * (0.6 + 0.4 * p2)
        base = mix(np.broadcast_to(C["shore"], f.shape + (3,)), np.broadcast_to(C["pebble"], f.shape + (3,)), sstep(0.45, 0.8, p1))
        base = mix(base, np.broadcast_to(C["wet"], base.shape), sstep(0.7, 0.9, pn(6, 23)) * 0.5)
        return base * f[..., None]
    def paddy(pn):   # 논/밭: 이랑 줄무늬(세로) + 흙. 512px에 줄 6개(타일 6m, 이랑 1.04m)로 이음매 맞춤
        xs = np.arange(512)[None, :] * np.ones((512, 1)); f = np.mod(xs / 512 * 6 + 0.5, 1.0)
        ridge = sstep(0.12, 0.3, f) * (1 - sstep(0.7, 0.88, f)); ridge *= 1 - 0.15 * pn(32, 31)
        base = mix(np.broadcast_to(C["furrow"], ridge.shape + (3,)) * (0.85 + 0.3 * pn(48, 32))[..., None], np.broadcast_to(C["barley_ridge"], ridge.shape + (3,)) * (0.85 + 0.3 * pn(64, 33))[..., None], ridge)
        return mix(base, np.broadcast_to(C["barley_ear"], base.shape), ridge * sstep(0.55, 0.8, pn(40, 34)) * 0.6)
    def leaf(pn):
        n1 = 0.5 * pn(6, 41) + 0.5 * pn(20, 42); f = 0.75 + 0.5 * pn(96, 43)
        base = mix(np.broadcast_to(C["litter_pine"], n1.shape + (3,)), np.broadcast_to(C["litter_leaf"], n1.shape + (3,)), sstep(0.35, 0.65, n1))
        base = mix(base, np.broadcast_to(C["moss"], base.shape), sstep(0.68, 0.85, pn(8, 44)) * 0.6)
        return base * f[..., None]
    for name, fn in (("grass", grass), ("dirt", dirt), ("gravel", gravel), ("paddy", paddy), ("leaf", leaf)):
        save(name, tileable(fn))

def write_details():
    """가까이 볼 때 곱해 쓰는 디테일(1.5m 반복, 512²): detail_{층}.png(색)·detail_{층}_n.png(노멀). 물: water_albedo.png(RGBA, 4m 반복)·water_normal.png."""
    import terrain_detail as TD
    for name, (c, nm) in TD.detail_tiles(tg.C, 512).items():
        Image.fromarray(c).save(os.path.join(OUT, f"detail_{name}.png"), optimize=True); Image.fromarray(nm).save(os.path.join(OUT, f"detail_{name}_n.png"), optimize=True)
    rgba, nrm = TD.water_tiles(256)
    Image.fromarray(TD.water_tiles(256, True)[0], "RGBA").save(os.path.join(OUT, "water_albedo_deep.png"), optimize=True)   # 큰 강(검은여울)용: 더 어둡고 덜 비침
    Image.fromarray(rgba, "RGBA").save(os.path.join(OUT, "water_albedo.png"), optimize=True); Image.fromarray(nrm).save(os.path.join(OUT, "water_normal.png"), optimize=True)

def river_info():
    g = river_geom(); return {"axis_x_m": (g["x0"] + g["x1"]) / 2, "water_x_m": [g["x0"], g["x1"]], "y_m": [g["y0"], g["y1"]], "surface_z_m": tg.WATER_Z, "bed_center_z_m": RIVER_BED_C, "bed_edge_z_m": RIVER_BED_E, "bank_top_z_m": RIVER_LAND,
            "waterline_halfwidth_m": "7.2~7.75 (길이 방향으로 구불거림)", "south_end": "둥글게 닫힘(반지름 8m, 중심 y=280)", "north_end": "지도 끝(y=640)까지 이어짐",
            "water_mesh": "river_water.glb — 한 장짜리 연속 물판(x 76~92, y 272~640, z 0.18, 4m 반복 uv, 흐름 +남쪽). br_* 조각의 물판 46×3장을 대신한다",
            "note": "높이맵에 칸 경계와 무관한 연속 물길을 팠다(옛: br_ 칸마다 안쪽만 −0.1이라 8m 둑이 남음). br_* 조각 모델을 계속 놓으면 바닥 상자(윗면 0.12)가 물길 위로 얹힌다 — 지형+river_water.glb만 쓰길 권장"}

def write_river_water():
    """강 전체를 덮는 연속 물판 하나(river_water.glb). 개울 물과 같은 그림, 큰 강용 어두운 변형. 월드 좌표 그대로(원점=필드 남서 모서리)라 (0,0,0)에 놓으면 된다."""
    import lib3d as L
    g = river_geom(); L.reset(); o = L.join("river_water", [L.water_plane("water", g["x0"], g["y0"], g["x1"] - g["x0"], g["y1"] - g["y0"], tg.WATER_Z, True, 4.0)])
    L.export(o, os.path.join(OUT, "river_water.glb")); return o

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    river_only = "river" in sys.argv[1:]
    h = height_grid(); write_height(h); print("heightmap", h.shape, h.min(), h.max())
    m = write_splats(); print("splat 완료")
    write_river_water(); print("river_water.glb")
    if river_only:   # 강만 다시 팔 때: 층·디테일 그림은 그대로 두고 terrain.json만 고친다
        tj = json.load(open(os.path.join(OUT, "terrain.json"), encoding="utf-8")); tj["river"] = river_info()
        tj["note"] = "아트(Blender) 쪽 같은 규칙에서 뽑은 자료. 행 0 = y 0(남쪽). 큰 강(검은여울)은 칸 경계 없이 연속 물길로 파 두었다(river 항목)."
        json.dump(tj, open(os.path.join(OUT, "terrain.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1); sys.exit(0)
    make_layers(); print("layer 5장 완료"); write_details(); print("디테일·물 그림 완료")
    json.dump({"size": tg.NM, "height_res": RES + 1, "splat_res": RES, "height_min_m": HMIN, "height_max_m": HMAX, "layer_tile_m": [6, 6, 6, 6, 6],
               "detail": {"tile_m": 1.5, "files": ["detail_dirt.png", "detail_grass.png", "detail_gravel.png", "detail_paddy.png", "detail_leaf.png"], "normals": "detail_<층>_n.png (OpenGL, 초록=위)", "use": "층 색에 곱하거나 가까울 때(~25m 안) 섞고, 노멀은 층 노멀로 쓴다. 층 평균 명도는 layer_*와 비슷하다"},
               "water": {"surface_z_m": 0.18, "flow_dir_xy": [0, -1], "flow_speed_mps": 0.7, "tile_m": 4, "albedo": "water_albedo.png (RGBA, 알파=투명도)", "normal": "water_normal.png", "scroll_uv_per_s": "flow_dir 방향으로 flow_speed/tile_m 만큼 uv 이동. 노멀은 반대 방향으로 한 겹 더 느리게 겹치면 흐름이 살아난다", "roughness": 0.06,
                         "foam": "splat_b.png G채널 = 물가 거품(물높이와 땅이 만나는 선), B채널 = 젖은 땅. 알베도에도 구워져 있다"},
               "river": river_info(), "note": "아트(Blender) 쪽 같은 규칙에서 뽑은 자료. 행 0 = y 0(남쪽). 큰 강(검은여울)은 칸 경계 없이 연속 물길로 파 두었다(river 항목)."},
              open(os.path.join(OUT, "terrain.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
