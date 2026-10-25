"""코드팀(유니티) 형식의 땅 자료를 만든다. 약속: docs/TERRAIN-FORMAT.md (브랜치 claude/project-thread-ozfksa).
실행: python3 terrain_unity.py   → assets3d/terrain/ 에 terrain.json, heightmap.png(16비트=R·G), splat_a.png(흙·풀·자갈·논), splat_b.png(낙엽), layer_*.png(이음매 없는 512²)
왜 두 가지(청크 GLB + 이 자료)인가: 유니티 땅 시스템은 높이 지도와 섞기 지도를 받는다. 같은 규칙(terrain_ground.chunk_maps)에서 뽑아 두 길이 같은 땅을 보이게 한다.
행 0 = y 0(남쪽), 위쪽 줄이 남쪽이다(코드팀 약속)."""
import os, json, numpy as np
from PIL import Image
import terrain_ground as tg
from terrain_ground import vnoise, fbm, sstep, mix, C

OUT = os.path.join(tg.A3, "terrain")
HMIN, HMAX = -1.0, 8.0          # 높이 범위(m). 개울 바닥 0.04, 강 조각 안쪽 -0.1, 비탈 위 2.3 정도라 넉넉
RES = 640

def height_grid():
    """1m 간격 641×641 높이. 강 조각 칸(br_*) 안쪽은 살짝 낮춰 물길이 파인 느낌을 준다(조각 모델은 따로 놓임)."""
    xs = np.arange(RES + 1, dtype=np.float64); X, Y = np.meshgrid(xs, xs)
    h = tg.height_at(X, Y).astype(np.float64)
    # 강 조각 칸 안쪽(둘레 2m 안은 둑과 이어지게 그대로 둔다)
    brd = np.full(X.shape, 99.0)
    for iy, ix in zip(*np.nonzero(tg.is_br)):
        cx, cy = ix * tg.T + 4, iy * tg.T + 4; brd = np.minimum(brd, np.maximum(np.abs(X - cx), np.abs(Y - cy)) - 4)
    inner = tg.sstep(0.0, -2.0, brd)
    h = h * (1 - inner) + (-0.1) * inner
    return h

def write_height(h):
    v = np.clip((h - HMIN) / (HMAX - HMIN), 0, 1) * 65535; v = np.round(v).astype(np.uint32)
    rgba = np.zeros(h.shape + (4,), np.uint8); rgba[..., 0] = v >> 8; rgba[..., 1] = v & 255; rgba[..., 3] = 255
    Image.fromarray(rgba, "RGBA").save(os.path.join(OUT, "heightmap.png"))

def write_splats():
    m = tg.chunk_maps(0, 0, s_=1, pad_=0, size_=tg.NM, masks=True)
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
    Image.fromarray(rgba, "RGBA").save(os.path.join(OUT, "water_albedo.png"), optimize=True); Image.fromarray(nrm).save(os.path.join(OUT, "water_normal.png"), optimize=True)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    h = height_grid(); write_height(h); print("heightmap", h.shape, h.min(), h.max())
    m = write_splats(); print("splat 완료")
    make_layers(); print("layer 5장 완료"); write_details(); print("디테일·물 그림 완료")
    json.dump({"size": tg.NM, "height_res": RES + 1, "splat_res": RES, "height_min_m": HMIN, "height_max_m": HMAX, "layer_tile_m": [6, 6, 6, 6, 6],
               "detail": {"tile_m": 1.5, "files": ["detail_dirt.png", "detail_grass.png", "detail_gravel.png", "detail_paddy.png", "detail_leaf.png"], "normals": "detail_<층>_n.png (OpenGL, 초록=위)", "use": "층 색에 곱하거나 가까울 때(~25m 안) 섞고, 노멀은 층 노멀로 쓴다. 층 평균 명도는 layer_*와 비슷하다"},
               "water": {"surface_z_m": 0.18, "flow_dir_xy": [0, -1], "flow_speed_mps": 0.7, "tile_m": 4, "albedo": "water_albedo.png (RGBA, 알파=투명도)", "normal": "water_normal.png", "scroll_uv_per_s": "flow_dir 방향으로 flow_speed/tile_m 만큼 uv 이동. 노멀은 반대 방향으로 한 겹 더 느리게 겹치면 흐름이 살아난다", "roughness": 0.06,
                         "foam": "splat_b.png G채널 = 물가 거품(물높이와 땅이 만나는 선), B채널 = 젖은 땅. 알베도에도 구워져 있다"},
               "note": "아트(Blender) 쪽 같은 규칙에서 뽑은 자료. 행 0 = y 0(남쪽). 강 조각(br_*) 칸 안쪽은 -0.1로 낮춰 물길을 파 둠(물·조각 모델은 따로)."},
              open(os.path.join(OUT, "terrain.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
