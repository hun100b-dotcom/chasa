"""3막 ⑥ 도성 아랫마을 땅 자료 만들기. 실행: python3 terrain_act3_west.py   (블렌더 불필요)
땅: 월드 x −640~0, y 0~640 (640×640 m), origin_m [-640,0], 높이맵 641×641, 행 0 = 남쪽. 산출: assets3d/terrain_act3_west/ + 미리보기 act3_west_terrain_map.png
높이 약속: 마른땅 1.0, 큰내(x≈−380) 바닥 −0.6(물판 z −0.1), 다리 밑 둔치 0.3(B-11 마당, 마른 바닥), 움막촌은 성벽 쪽으로 1.2→3.5 오르는 비탈, 성벽(x=−560) 안쪽은 못 들어가는 도성 터 6 m(절벽처럼 막힘), 성문 밖 눈밭 1.0.
층 뜻(⑥): dirt=흙길·마른 흙, grass=마른 풀, gravel=자갈·성벽 돌·바위, paddy(A)=장터 다진 마당(밝은 흙), splat_b R=눈(성문 밖), G=물가 거품, B=젖은 둔치.
남쪽 가장자리는 해안 띠로 이어진다(해안 띠 높이는 terrain_act3_coast.py 가 맞춘다)."""
import os, json, math
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
OUT = os.path.join(ROOT, "assets3d", "terrain_act3_west")
MAP = json.load(open("/mnt/project-files/planning/openworld/act3/act3_map.json", encoding="utf-8")) if os.path.exists("/mnt/project-files/planning/openworld/act3/act3_map.json") else json.load(open(os.path.join(ROOT, "data", "art", "act3_map.json"), encoding="utf-8"))
X0, Y0, W, H = -640, 0, 640, 640      # 월드 원점(남서 모서리)과 크기(m)
HMIN, HMAX = -7.0, 9.0
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



R = {r["id"]: r["points"] for r in MAP["roads"]}
Z = {z["code"]: z for z in MAP["zones"]}
def zr(code, m): x0, x1, y0, y1 = Z[code]["rect_m"][0], Z[code]["rect_m"][2], Z[code]["rect_m"][1], Z[code]["rect_m"][3]; return rect(x0, x1, y0, y1, m)
RIVER = [(-380, 640), (-382, 520), (-376, 440), (-380, 410), (-384, 330), (-378, 220), (-382, 120), (-380, 0)]
WALL_X = -560

def build_height():
    n1 = fbm(X, Y, [120, 45, 15], 71) - 0.5
    h = 1.0 + 0.9 * (fbm(X, Y, [200, 80], 27) - 0.5) + 0.35 * n1
    # 성벽 안쪽 도성 터(못 들어감): 서쪽으로 갈수록 높아져 절벽처럼 막는다
    h = mix(h, sstep(WALL_X + 6, WALL_X - 4, X), 6.0 + 0.2 * n1)
    # 움막촌 비탈: 성벽 쪽으로 오르막
    slope_ = 1.2 + (-450 - X) / 110.0 * 2.3
    h = mix(h, zr("Shacks", 14), slope_ + 0.12 * n1)
    h = mix(h, zr("Market", 12), 1.0 + 0.03 * n1)
    h = mix(h, zr("CityGate", 14) * (X > WALL_X + 8), 1.0 + 0.03 * n1)
    # 큰내: 남북으로 흐르는 물길(다리 둘레는 둔치가 마른 바닥으로 이어진다)
    d, s, L = poly_dist(RIVER); bridge = np.exp(-((Y - 405) / 38.0) ** 2) * (1 - sstep(60, 90, np.abs(X + 382)))
    chan = (1 - sstep(6.0, 15.0, d)); floor = -0.6 + 0.05 * n1
    h = mix(h, chan * (1 - 0.0), floor); h = mix(h, bridge * (1 - sstep(10, 22, np.abs(X + 382)) * 0 ) * (1 - sstep(8.0, 18.0, d) * 0), 0.3)   # 다리 밑 마른 둔치
    h = mix(h, disc(-382, 392, 20, 8), 0.3)                                                          # B-11 마당 r14
    h = mix(h, disc(-500, 185, 24, 8), 1.0)                                                          # B-12 마당 r18
    # 길 평탄화(큰내 건너는 다리 부분은 건드리지 않는다)
    hb = blur(h, 9.0)
    def hat(p): return float(hb[int(np.clip(p[1] - Y0, 0, H)), int(np.clip(p[0] - X0, 0, W))])
    for rid, pts in R.items():
        inside = [p for p in pts if X0 - 1 <= p[0] <= X0 + W + 1 and Y0 - 1 <= p[1] <= Y0 + H + 1]
        if len(inside) < 2 or rid in ("R3-6", "R3-1", "R3-3", "R3-4", "R3-5", "R3-9", "R3-7"): continue
        d2, s2, L2 = poly_dist(inside); cum = [0.0]
        for a, b in zip(inside, inside[1:]): cum.append(cum[-1] + math.dist(a, b))
        prof = np.interp(s2, cum, [max(hat(p), 0.3) for p in inside])
        mask = 1 - sstep(2.6, 7.5, d2)
        if rid == "R3-2": mask = mask * (1 - np.exp(-((X + 382) / 14.0) ** 2) * 0.0)
        h = mix(h, mask, prof + 0.03 * n1)
    # 해안 길 비탈(R3-6의 ⑥ 쪽 끝): y=0 해안 바닥 -6.5m에서 성문 밖 마당 1.0m까지 올라간다. 양쪽은 가파른 벼랑
    ramp = [(-420, 0), (-446, 70), (-470, 140), (-500, 185)]; dr, sr, Lr = poly_dist(ramp)
    h = mix(h, (1 - sstep(4.0, 9.0, dr)) * (Y < 190), -6.5 + 7.5 * sstep(0, 1, sr / Lr) + 0.03 * n1)
    # 큰 다리 둑길: 상판 윗면이 둔치보다 3.6m 높아서 다리 양끝(|dx|≥20)은 3.9m 높이로 올리고 바깥으로 24m에 걸쳐 1.0으로 내린다. 다리 축은 y=400, 상판 폭 6m(둑길 폭 ±7m)
    dx = np.abs(X + 380.0); tt = np.clip((44.0 - dx) / 24.0, 0, 1); gate_ = sstep(14, 18, dx)
    h = mix(h, (1 - sstep(5.0, 11.0, np.abs(Y - 400.0))) * gate_ * (dx < 46), 1.0 + 2.9 * tt)
    # 다리 위 길은 상판(bridge_deck)이 대신하므로 둔치가 파이도록 다리 폭 안의 길 높이를 둔치에 되돌린다
    h = mix(h, bridge * (1 - sstep(4.0, 12.0, np.abs(X + 382))) * (np.abs(X + 380) < 16), 0.3)
    for sx, sy in [(-140, 432), (-335, 415), (-500, 185), (-382, 392)]:
        h = mix(h, disc(sx, sy, 5.0, 5.0), 0.3 if (sx, sy) == (-382, 392) or (sx, sy) == (-335, 415) else (1.0 if sy == 185 else 1.0))
    return np.clip(h, HMIN + 0.01, HMAX - 0.01)

def build_splats(h):
    gy, gx = np.gradient(h); slope = np.hypot(gx, gy)
    n1 = fbm(X, Y, [30, 9, 3], 81); n2 = fbm(X, Y, [60, 18], 91)
    dry = sstep(0.0, 0.5, h) * (1 - sstep(5.0, 6.0, h))
    dirt = 0.4 + 0.4 * sstep(0.4, 0.7, n1)
    grass = 0.7 * (1 - sstep(0.35, 0.6, n2)) * dry
    gravel = 0.1 + 0.9 * sstep(0.5, 1.0, slope * 2.2) + 0.25 * sstep(0.62, 0.8, n1) + sstep(5.0, 6.0, h)
    yard = np.maximum.reduce([zr("Market", 6), disc(-382, 392, 18, 6) * 0.5])
    road = np.zeros(X.shape)
    for rid, pts in R.items():
        d, _, _ = poly_dist(pts); road = np.maximum(road, (1 - sstep(1.6, 3.4, d)) * 0.6)
    road = np.maximum(road, yard * 0.6)
    dirt = np.maximum(dirt * 0.5, road); grass = grass * (1 - road)
    paddy = zr("Market", 4) * 0.8                                                                       # 장터 다진 마당(밝은 흙)
    stack = np.clip(np.stack([dirt, grass, gravel, paddy], -1), 0, 1); tot = stack.sum(-1); stack[..., 1] += np.clip(1 - tot, 0, 1) * dry
    for k in range(4): stack[..., k] = blur(stack[..., k], 0.8)
    snow = zr("CityGate", 8) * (X > WALL_X + 6) * (0.75 + 0.25 * sstep(0.4, 0.7, n1)) * (1 - disc(-470, 265, 14, 6) * 0.9)    # 눈밭, 주막 앞은 눈 녹은 자리
    d, _, _ = poly_dist(RIVER); foam = (1 - sstep(8.0, 13.0, d)) * sstep(3.0, 7.0, d); wet = (1 - sstep(5.0, 11.0, d)) + disc(-382, 392, 14, 6) * 0.5
    return stack, snow, foam, np.clip(wet, 0, 1)

def write(h, stack, snow, foam, wet):
    os.makedirs(OUT, exist_ok=True)
    v = np.round(np.clip((h - HMIN) / (HMAX - HMIN), 0, 1) * 65535).astype(np.uint32)
    rgba = np.zeros(h.shape + (4,), np.uint8); rgba[..., 0] = v >> 8; rgba[..., 1] = v & 255; rgba[..., 3] = 255
    Image.fromarray(rgba, "RGBA").save(os.path.join(OUT, "heightmap.png"))
    s = (np.clip(stack[:H, :W], 0, 1) * 255).astype(np.uint8); Image.fromarray(s, "RGBA").save(os.path.join(OUT, "splat_a.png"))
    c = lambda a: (np.clip(a[:H, :W], 0, 1) * 255).astype(np.uint8)
    Image.fromarray(np.stack([c(snow), c(foam), c(wet), np.full((H, W), 255, np.uint8)], -1), "RGBA").save(os.path.join(OUT, "splat_b.png"))

def tileable(fn, n=512):
    yy, xx = np.meshgrid(np.arange(n), np.arange(n), indexing="ij")
    def pn(cells, seed):
        g = np.random.RandomState(seed).rand(cells, cells).astype(np.float32); fx = xx / n * cells; fy = yy / n * cells; ix = np.floor(fx).astype(int); iy = np.floor(fy).astype(int); tx = fx - ix; ty = fy - iy
        tx = tx * tx * (3 - 2 * tx); ty = ty * ty * (3 - 2 * ty); a = g[iy % cells, ix % cells]; b = g[iy % cells, (ix + 1) % cells]; c = g[(iy + 1) % cells, ix % cells]; d = g[(iy + 1) % cells, (ix + 1) % cells]
        return (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty
    return fn(pn)
def hexc(h): h = h.lstrip("#"); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)
def lerp(a, b, t): return a * (1 - t[..., None]) + b * t[..., None]
def make_layers():
    def save(name, arr): Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(os.path.join(OUT, f"layer_{name}.png"))
    def lay(c1, c2, c3, seeds, f_seed):
        def fn(pn):
            n1 = 0.5 * pn(4, seeds[0]) + 0.3 * pn(10, seeds[1]) + 0.2 * pn(24, seeds[2]); f = 0.82 + 0.36 * pn(96, f_seed) * (0.6 + 0.4 * pn(160, f_seed + 1))
            base = lerp(np.broadcast_to(hexc(c1), n1.shape + (3,)), np.broadcast_to(hexc(c2), n1.shape + (3,)), np.clip((n1 - 0.3) / 0.4, 0, 1))
            base = lerp(base, np.broadcast_to(hexc(c3), base.shape), np.clip((pn(14, seeds[0] + 3) - 0.62) / 0.2, 0, 1) * 0.5)
            return base * f[..., None]
        return tileable(fn)
    save("dirt", lay("#8A7456", "#6E5C44", "#A08A68", (201, 202, 203), 204))        # 마른 흙·갯벌 흙
    save("grass", lay("#7E8A5A", "#9AA06A", "#6A7650", (211, 212, 213), 214))       # 갯풀
    save("gravel", lay("#8A877E", "#6A675F", "#A5A298", (221, 222, 223), 224))      # 자갈·바위
    save("paddy", lay("#DAD6C8", "#C9C4B2", "#EDEADF", (231, 232, 233), 234))       # 소금(염전 흰색, 1막 '논' 자리)
    save("leaf", lay("#E8EAEE", "#D2D6DE", "#F4F5F8", (241, 242, 243), 244))        # 눈(⑥ 성문 밖용, 1막 '낙엽' 자리)

def preview(h, stack, snow, foam, wet):
    cols = [hexc("#8A7456"), hexc("#7E8A5A"), hexc("#8A877E"), hexc("#B8AA8A")]
    img = sum(stack[..., k:k + 1] * cols[k] for k in range(4)) / np.maximum(stack.sum(-1), 1e-3)[..., None]
    img = img * (1 - 0.35 * wet[..., None]); img = img * (1 - snow[..., None]) + np.array([232, 234, 238], np.float32) * snow[..., None]
    gy, gx = np.gradient(blur(h, 1.2)); shade = np.clip(0.8 - 0.9 * (gx * 0.6 + gy * 0.8) + 0.01 * h, 0.5, 1.2)
    img = np.clip(img * shade[..., None], 0, 255).astype(np.uint8)[::-1]
    im = Image.fromarray(img); from PIL import ImageDraw; d = ImageDraw.Draw(im)
    fy = lambda y: H - (y - Y0); fx = lambda x: x - X0
    for r in MAP["roads"]: d.line([(fx(p[0]), fy(p[1])) for p in r["points"]], fill=(240, 231, 211), width=2)
    for z in MAP["zones"]:
        x0, y0, x1, y1 = z["rect_m"]
        if x1 <= 0: d.rectangle([fx(x0), fy(y1), fx(x1), fy(y0)], outline=(255, 255, 255)); d.text((fx(x0) + 3, fy(y1) + 3), z["code"], fill=(255, 255, 255))
    for b in MAP["boss_arenas"]:
        if b["x"] < 0: d.ellipse([fx(b["x"]) - b["radius_m"], fy(b["y"]) - b["radius_m"], fx(b["x"]) + b["radius_m"], fy(b["y"]) + b["radius_m"]], outline=(255, 90, 90), width=2)
    for s in MAP["shrines"]:
        if s["x"] < 0: d.ellipse([fx(s["x"]) - 4, fy(s["y"]) - 4, fx(s["x"]) + 4, fy(s["y"]) + 4], fill=(255, 220, 120))
    im.save(os.path.join(ROOT, "assets3d", "previews", "act3_west_terrain_map.png"))

if __name__ == "__main__":
    h = build_height(); print("height", h.shape, round(float(h.min()), 2), round(float(h.max()), 2))
    stack, snow, foam, wet = build_splats(h); write(h, stack, snow, foam, wet); make_layers(); preview(h, stack, snow, foam, wet)
    gy, gx = np.gradient(h); sl = np.hypot(gx, gy)
    flat = {s["id"]: round(float(sl[int(s["y"] - Y0), int(s["x"] - X0)]), 3) for s in MAP["shrines"] if s["x"] < 0}
    for b in MAP["boss_arenas"]:
        if b["x"] < 0: flat[b["boss"]] = round(float(sl[int(b["y"] - Y0), int(b["x"] - X0)]), 3)
    json.dump({"origin_m": [X0, Y0], "size_x_m": W, "size_z_m": H, "size": W, "height_res_x": W + 1, "height_res_z": H + 1, "splat_res_x": W, "splat_res_z": H, "height_min_m": HMIN, "height_max_m": HMAX, "layer_tile_m": [6, 6, 6, 6, 6],
               "river_floor_m": -0.6, "coast_ramp_points": [[-420, 0], [-446, 70], [-470, 140], [-500, 185]], "bridge_axis_y_m": 400, "bridge_deck_top_m": 3.9, "dry_bank_under_bridge_m": 0.3, "wall_x_m": WALL_X,
               "layers": {"dirt": "흙길·마른 흙", "grass": "마른 풀", "gravel": "자갈·성벽 돌", "paddy": "장터 다진 마당(splat_a A)", "leaf": "눈(splat_b R, 성문 밖)", "splat_b.G": "물가 거품", "splat_b.B": "젖은 둔치"},
               "note": "아트 terrain_act3_west.py가 만든다. 행 0=남쪽(월드 y 0). 큰내 물판은 tide_water 말고 1막 river_water 같은 물을 x≈-380 따라 폭 14m로 깐다(물높이 -0.1).", "slope_at_shrines_and_arenas": flat}, open(os.path.join(OUT, "terrain.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("기울기", flat)
