"""1막 동쪽 틈(x 640~768, y 0~640) 땅 메우기. 실행: python3 terrain_gap.py → assets3d/terrain_gap/ + assets3d/layouts/gap_layout.json
왜: 1막 땅(0~640)과 ⑤ 갯마을 땅(768~) 사이 128 m가 비어 있었다(코드팀 발견). 서쪽 가장자리는 1막 동쪽 열(0.2~0.4 m), 동쪽 가장자리는 ⑤ 서쪽 열 높이를 그대로 이어받아 이음매 없이 부드럽게 섞는다.
강둑길(R3-1)이 지나는 y≈305~312 에는 ⑤ 갯골(바닥 -0.35)로 이어지는 얕은 물길을 판다(서쪽 끝에서 사라지게). 남쪽은 ⑤처럼 바다로 내려간다.
땅 색은 ⑤의 층을 쓴다(dirt 마른 흙, grass 갯풀, gravel 바위). 소품(소나무·덤불·풀)은 이웃 밀도와 비슷하게 흩뿌렸다(길 3 m·물길 비움)."""
import os, json, math
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
OUT = os.path.join(ROOT, "assets3d", "terrain_gap")
MAP = json.load(open("/mnt/project-files/planning/openworld/act3/act3_map.json", encoding="utf-8")) if os.path.exists("/mnt/project-files/planning/openworld/act3/act3_map.json") else json.load(open(os.path.join(ROOT, "data", "art", "act3_map.json"), encoding="utf-8"))
X0, Y0, W, H = 640, 0, 128, 640      # 월드 원점(남서 모서리)과 크기(m)
HMIN, HMAX = -7.0, 10.0
xs = np.arange(W + 1, dtype=np.float64) + X0; ys = np.arange(H + 1, dtype=np.float64) + Y0
X, Y = np.meshgrid(xs, ys)           # 모양 (641, 769), 행 0 = 남쪽

def sstep(a, b, x): t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
def vnoise(x, y, cell, seed):
    """값 노이즈(격자 위 무작위 값을 부드럽게 이은 것). cell=한 칸의 길이(m)."""
    rs = np.random.RandomState(seed); n = int(max(W, H) / cell) + 4; g = rs.rand(n, n)
    fx, fy = x / cell, y / cell; ix, iy = np.floor(fx).astype(int), np.floor(fy).astype(int); tx, ty = fx - ix, fy - iy
    tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty); ix, iy = ix % n, iy % n
    return (g[iy, ix] * (1 - tx) + g[iy, (ix + 1) % n] * tx) * (1 - ty) + (g[(iy + 1) % n, ix] * (1 - tx) + g[(iy + 1) % n, (ix + 1) % n] * tx) * ty
def fbm(x, y, cells, seed, w=None):
    w = w or [1.0 / (2 ** i) for i in range(len(cells))]; s = sum(w)
    return sum(wi * vnoise(x, y, c, seed + i * 7) for i, (c, wi) in enumerate(zip(cells, w))) / s
def blur(a, sigma):
    r = int(sigma * 3) + 1; k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2); k /= k.sum()
    p = np.pad(a, ((0, 0), (r, r)), mode="edge"); a = sum(k[i] * p[:, i:i + a.shape[1]] for i in range(2 * r + 1))
    p = np.pad(a, ((r, r), (0, 0)), mode="edge"); return sum(k[i] * p[i:i + a.shape[0], :] for i in range(2 * r + 1))
def rect(x0, x1, y0, y1, m):
    """안쪽은 1, 가장자리 m 미터에 걸쳐 0으로 부드럽게 내려가는 마스크(구역 직사각형)."""
    return sstep(x0 - m, x0, X) * (1 - sstep(x1, x1 + m, X)) * sstep(y0 - m, y0, Y) * (1 - sstep(y1, y1 + m, Y))
def disc(cx, cy, r, m): return 1 - sstep(r, r + m, np.hypot(X - cx, Y - cy))
def poly_dist(pts):
    """폴리라인까지 최단 거리 d와 가장 가까운 점의 누적 길이 s."""
    best = np.full(X.shape, 1e9); bs = np.zeros(X.shape); acc = 0.0
    for a, b in zip(pts, pts[1:]):
        ax, ay, bx, by = a[0], a[1], b[0], b[1]; dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy; L = math.sqrt(L2)
        t = np.clip(((X - ax) * dx + (Y - ay) * dy) / L2, 0, 1); d = np.hypot(X - (ax + t * dx), Y - (ay + t * dy))
        upd = d < best; best = np.where(upd, d, best); bs = np.where(upd, acc + t * L, bs); acc += L
    return best, bs, acc
def mix(h, mask, target): return h * (1 - mask) + target * mask



import random
LEFT = None
def dec(png, hmin, hmax):
    a = np.array(Image.open(png).convert("RGBA")).astype(np.int64); return ((a[..., 0] << 8) | a[..., 1]) / 65535.0 * (hmax - hmin) + hmin
def build_height():
    a1 = dec(os.path.join(ROOT, "assets3d", "terrain", "heightmap.png"), -1.0, 8.0)[:, -1]            # 1막 동쪽 열(641칸, y 0..640)
    e5 = dec(os.path.join(ROOT, "assets3d", "terrain_act3_east", "heightmap.png"), -7.0, 10.0)[:, 0]      # ⑤ 서쪽 열(1025칸, y 0..1024 중 앞 641칸)
    L = np.repeat(a1[:H + 1, None], W + 1, 1); Rr = np.repeat(e5[:H + 1, None], W + 1, 1)
    t = sstep(0, 1, (X - X0) / W)
    n1 = fbm(X, Y, [60, 20, 7], 91) - 0.5
    h = L * (1 - t) + Rr * t + n1 * 0.5 * np.sin(np.pi * t)
    d, s, Ln = poly_dist([(640, 306), (700, 306), (768, 305)])
    chan = (1 - sstep(4.0, 12.0, d)) * sstep(30, 90, X - X0) * (1 - sstep(96, 128, X - X0))   # 양끝에서 사라지는 얕은 물길(동쪽 끝은 ⑤ 땅과 높이를 맞추려고 메움)
    h = h * (1 - chan) + (-0.35 + 0.05 * n1) * chan
    return np.clip(h, HMIN + 0.01, HMAX - 0.01)
def build_splats(h):
    gy, gx = np.gradient(h); slope = np.hypot(gx, gy); n1 = fbm(X, Y, [30, 9, 3], 93); n2 = fbm(X, Y, [60, 18], 94)
    dry = sstep(0.0, 0.5, h); dirt = dry * (0.25 + 0.3 * sstep(0.4, 0.7, n1)); grass = dry * 0.8 * (1 - sstep(0.35, 0.65, n2)); gravel = 0.1 + 0.9 * sstep(0.5, 1.0, slope * 2.2)
    road = np.zeros(X.shape); d, _, _ = poly_dist([(640, 306), (700, 306), (768, 312)]); road = (1 - sstep(1.6, 3.4, d)) * 0.7 * (h > -0.1)
    dirt = np.maximum(dirt, road); grass = grass * (1 - road)
    stack = np.clip(np.stack([dirt, grass, gravel, np.zeros_like(dirt)], -1), 0, 1); tot = stack.sum(-1); stack[..., 1] += np.clip(1 - tot, 0, 1) * dry
    for k in range(4): stack[..., k] = blur(stack[..., k], 0.8)
    tidal = sstep(-0.8, -0.4, h) * (1 - sstep(0.6, 1.0, h)); foam = sstep(-0.9, -0.5, h) * (1 - sstep(-0.35, 0.1, h))
    return stack, np.clip(foam, 0, 1), np.clip(tidal + foam * 0.3, 0, 1)
def write(h, stack, foam, wet):
    os.makedirs(OUT, exist_ok=True)
    v = np.round(np.clip((h - HMIN) / (HMAX - HMIN), 0, 1) * 65535).astype(np.uint32)
    rgba = np.zeros(h.shape + (4,), np.uint8); rgba[..., 0] = v >> 8; rgba[..., 1] = v & 255; rgba[..., 3] = 255
    Image.fromarray(rgba, "RGBA").save(os.path.join(OUT, "heightmap.png"))
    Image.fromarray((np.clip(stack[:H, :W], 0, 1) * 255).astype(np.uint8), "RGBA").save(os.path.join(OUT, "splat_a.png"))
    z = np.zeros((H, W), np.uint8); g = (np.clip(foam[:H, :W], 0, 1) * 255).astype(np.uint8); b = (np.clip(wet[:H, :W], 0, 1) * 255).astype(np.uint8)
    Image.fromarray(np.stack([z, g, b, np.full_like(z, 255)], -1), "RGBA").save(os.path.join(OUT, "splat_b.png"))
def ground(h, x, y):
    fx = min(max(x - X0, 0), W - 1e-6); fy = min(max(y - Y0, 0), H - 1e-6); i, j = int(fx), int(fy); tx, ty = fx - i, fy - j
    a = h[j, i] * (1 - tx) + h[j, i + 1] * tx; b = h[j + 1, i] * (1 - tx) + h[j + 1, i + 1] * tx; return float(a * (1 - ty) + b * ty)
def scatter(h):
    rng = random.Random(640); out = []
    road = [(640 + k * 4, 306) for k in range(33)]
    def ok(x, y, rad):
        z = ground(h, x, y)
        if z < 0.15: return False
        if abs(y - 306) < 3 + rad and x < 780: return False                  # 강둑길
        return True
    spec = [("nature_pine_a", 180, 1.6), ("nature_pine_b", 180, 1.6), ("nature_pine_c", 172, 1.6), ("nature_bush_a", 110, 0.8), ("nature_bush_b", 110, 0.8), ("nature_bush_c", 107, 0.8),
            ("cover_grass_a", 900, 0.2), ("cover_grass_b", 600, 0.2), ("cover_grass_c", 800, 0.2), ("cover_flower_white", 220, 0.2), ("cover_flower_mix", 150, 0.2), ("cover_stones_a", 70, 0.4)]
    placed = []
    for name, n, rad in spec:
        got = 0
        for _ in range(n * 6):
            if got >= n: break
            x, y = rng.uniform(X0 + 3, X0 + W - 3), rng.uniform(Y0 + 40, Y0 + H - 3)
            if not ok(x, y, rad): continue
            if rad >= 0.8 and any(math.hypot(x - q[0], y - q[1]) < rad + q[2] + 0.3 for q in placed if q[2] >= 0.8): continue
            if rad >= 0.8: placed.append((x, y, rad))
            folder = "nature"
            out.append({"prop": name, "file": f"assets3d/{folder}/{name}.glb", "x": round(x, 2), "y": round(y, 2), "rot": rng.randrange(360), "z": round(ground(h, x, y), 2)}); got += 1
    return out
if __name__ == "__main__":
    h = build_height(); stack, foam, wet = build_splats(h); write(h, stack, foam, wet)
    import shutil
    for n in ("layer_dirt", "layer_grass", "layer_gravel", "layer_paddy", "layer_leaf"): shutil.copy(os.path.join(ROOT, "assets3d", "terrain_act3_east", n + ".png"), os.path.join(OUT, n + ".png"))
    props = scatter(h)
    json.dump({"units": "m", "axes": "x=동, y=북(필드 절대)", "note": "terrain_gap.py가 만든다", "props": props}, open(os.path.join(ROOT, "assets3d", "layouts", "gap_layout.json"), "w"), ensure_ascii=False, indent=1)
    json.dump({"origin_m": [X0, Y0], "size_x_m": W, "size_z_m": H, "size": W, "height_res_x": W + 1, "height_res_z": H + 1, "splat_res_x": W, "splat_res_z": H, "height_min_m": HMIN, "height_max_m": HMAX, "layer_tile_m": [6, 6, 6, 6, 6],
               "layers": "⑤ 갯마을과 같은 층 뜻(dirt 마른 흙, grass 갯풀, gravel 바위, splat_b G 거품·B 젖은 갯벌)", "note": "1막 동쪽 열과 ⑤ 서쪽 열을 이어 주는 128 m 틈. 행 0=남쪽(월드 y 0)."}, open(os.path.join(OUT, "terrain.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("높이", round(float(h.min()), 2), round(float(h.max()), 2), "소품", len(props), "서쪽 열 차이", round(float(np.abs(h[:, 0] - dec(os.path.join(ROOT, "assets3d", "terrain", "heightmap.png"), -1.0, 8.0)[:, -1]).max()), 3), "동쪽 열 차이", round(float(np.abs(h[:, -1] - dec(os.path.join(ROOT, "assets3d", "terrain_act3_east", "heightmap.png"), -7.0, 10.0)[:H + 1, 0]).max()), 3))
