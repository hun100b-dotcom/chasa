"""3막 ⑤ 갯마을 땅 자료 만들기. 실행: python3 terrain_act3.py   (블렌더 불필요, numpy·PIL만)
입력: planning/openworld/act3/act3_map.json. 산출: assets3d/terrain_act3_east/ (terrain.json, heightmap.png, splat_a/b.png, layer_*.png, 미리보기 act3_east_terrain_map.png)
땅: 월드 x 768~1280, y 0~1024 (512×1024 m). origin_m [768,0]. 행 0 = 남쪽(y 0), 2막과 같은 약속.
높이 약속(코드·물판이 알아야 함): 썰물 물높이 -0.5, 밀물 물높이 +0.6(tide_water 를 25분 주기로 오르내림). 깊은 바다 바닥 -2.5, 갯벌·여울 바닥 0.0(썰물에 드러나고 밀물에 잠김), 포구·염전 마른땅 1.2~1.4, 곶 3.5.
층 뜻(3막): dirt=흙길·마른 흙, grass=갯풀, gravel=자갈·바위, paddy(A)=소금(염전 흰색), splat_b R=눈(⑥ 성문 밖용, ⑤는 0), G=물거품(물가 띠), B=젖은 갯벌(밀물에 젖는 높이).
좌표: 월드 x=동, y=북.""",
import os, json, math
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
OUT = os.path.join(ROOT, "assets3d", "terrain_act3_east")
MAP = json.load(open("/mnt/project-files/planning/openworld/act3/act3_map.json", encoding="utf-8")) if os.path.exists("/mnt/project-files/planning/openworld/act3/act3_map.json") else json.load(open(os.path.join(ROOT, "data", "art", "act3_map.json"), encoding="utf-8"))
X0, Y0, W, H = 768, 0, 512, 1024      # 월드 원점(남서 모서리)과 크기(m)
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


R = {r["id"]: r["points"] for r in MAP["roads"]}
Z = {z["code"]: z for z in MAP["zones"]}
def zr(code, m): x0, x1, y0, y1 = Z[code]["rect_m"][0], Z[code]["rect_m"][2], Z[code]["rect_m"][1], Z[code]["rect_m"][3]; return rect(x0, x1, y0, y1, m)
LOW, HIGH, SEA = -0.5, 0.6, -2.5

def build_height():
    n1 = fbm(X, Y, [120, 45, 15], 21) - 0.5
    # 바다: 동쪽(x>1110, 곶 구역은 1250까지 땅) · 남쪽(y<40). 해안선은 노이즈로 구불거리게
    wob = 14 * (fbm(X, Y, [90, 30], 8) - 0.5)
    cape = disc(1170, 680, 0, 1) * 0 + (1 - sstep(0.8, 1.05, np.hypot((X - 1170) / 95.0, (Y - 680) / 78.0) + 0.12 * (fbm(X, Y, [40, 14], 9) - 0.5)))        # 곶: 구불구불한 타원
    east_sea = sstep(-6, 6, X - (1112 + wob)) * (1 - cape)        # 곶은 동쪽으로 튀어나온다
    south_sea = sstep(-6, 6, (40 + wob) - Y) * (1 - disc(1135, 100, 70, 30) * 0.0)
    sea = np.clip(np.maximum(east_sea, south_sea), 0, 1)
    # 육지: 서쪽·북쪽으로 갈수록 높은 구릉, 해안 가까이는 낮은 모래·갯벌
    d_sea = np.minimum(np.where(X < 1112, 1112 - X, 0) + 0.0, 1e9); d_sea = np.minimum(1112 - X, Y - 40)
    inland = np.clip(d_sea / 90.0, 0, 1)
    hills = 3.6 * (fbm(X, Y, [200, 80], 17) - 0.5) + 1.2 * n1 + 3.0 * sstep(1000, 1024, Y) + 3.5 * (1 - sstep(768, 860, X)) * sstep(560, 640, Y)
    h = 1.3 + inland * (1.6 + hills)
    h = mix(h, sea, SEA + 0.15 * n1)
    # 해안 비탈: 바다 가장자리 12m 안에서 -2.5로 내려간다(모래톱)
    # 구역 평지
    h = mix(h, zr("Harbor", 14), 1.25 + 0.04 * n1)
    h = mix(h, zr("SaltField", 14), 1.4 + 0.03 * n1)
    h = mix(h, cape, 3.5 + 0.3 * n1); h = mix(h, disc(1215, 690, 20, 6), 3.0)    # 곶과 보스 B-09 마당
    h = mix(h, zr("WreckShoal", 20), 0.0 + 0.04 * n1); h = mix(h, disc(1135, 100, 20, 8), 0.0)       # 난파 여울: 썰물에 드러나는 바닥(B-10 마당)
    # 서쪽 아랫부분은 2막 갱도 출구 내리막과 이어져 높다(R3-9 시작 쪽)
    # 해안 띠(planning 답): 남쪽 가장자리는 해안 길 바닥 -6.5m와 이어진다 → 남쪽 40m 안은 깊은 만으로 내려가고, 해안 길(R3-6)은 여울 바닥 0.0에서 -6.5로 비탈을 내려간다
    h = mix(h, (1 - sstep(0, 55, Y)) * sea, -6.5)
    ramp = [(1040, 110), (1014, 60), (988, 0)]; dr, sr, Lr = poly_dist(ramp)
    h = mix(h, (1 - sstep(4.0, 9.0, dr)) * (Y < 112), -6.5 + 6.5 * (1 - sstep(0, 1, sr / Lr)) + 0.03 * n1)
    # 갯골(강어귀 물길): 물막이 골 강이 바다로 나간다. 바닥은 썰물에도 얕게 잠긴다
    def chan(h, pts, wf, ww, floor):
        d, s, L = poly_dist(pts); return mix(h, 1 - sstep(wf, wf + ww, d), floor + 0.05 * n1)
    h = chan(h, [(768, 305), (860, 306), (940, 330), (1030, 352), (1112, 362)], 4.0, 9.0, -0.35)
    # 해안 길(물때 길)은 곶 쪽에서 남쪽으로 시작해 썰물에만 걷는 바닥(0.0)
    d, _, _ = poly_dist(R["R3-6"][:3]); h = mix(h, 1 - sstep(5.0, 10.0, d), 0.0 + 0.03 * n1)
    h = mix(h, 1 - sstep(4.0, 9.0, poly_dist(R["R3-5"])[0]), 0.35)                                       # 갯벌 길도 낮은 바닥
    # 길 평탄화(바다·갯골 건너는 길 외)
    hb = blur(h, 9.0)
    def hat(p): return float(hb[int(np.clip(p[1] - Y0, 0, H)), int(np.clip(p[0] - X0, 0, W))])
    for rid, pts in R.items():
        if rid in ("R3-2", "R3-6", "R3-7", "R3-8", "R3-5"): continue
        inside = [p for p in pts if X0 - 1 <= p[0] <= X0 + W + 1 and Y0 - 1 <= p[1] <= Y0 + H + 1]
        if len(inside) < 2: continue
        d, s, L = poly_dist(inside); cum = [0.0]
        for a, b in zip(inside, inside[1:]): cum.append(cum[-1] + math.dist(a, b))
        prof = np.interp(s, cum, [max(hat(p), 1.0) for p in inside])
        h = mix(h, 1 - sstep(2.6, 7.5, d), prof + 0.03 * n1)
    for sx, sy in [(962, 395), (1215, 690), (1135, 100)]:
        c = float(hb[int(sy - Y0), int(sx - X0)]) if (sx, sy) == (962, 395) else (3.0 if sy == 690 else 0.0)
        h = mix(h, disc(sx, sy, 5.0, 5.0), max(c, 1.2) if (sx, sy) == (962, 395) else c)
    return np.clip(h, HMIN + 0.01, HMAX - 0.01)

def build_splats(h):
    gy, gx = np.gradient(h); slope = np.hypot(gx, gy)
    n1 = fbm(X, Y, [30, 9, 3], 51); n2 = fbm(X, Y, [60, 18], 61)
    dry = sstep(0.8, 1.2, h)                                 # 마른땅
    tidal = sstep(-0.8, -0.4, h) * (1 - sstep(0.6, 1.0, h))  # 밀물에 잠기는 높이(갯벌)
    dirt = dry * (0.35 + 0.4 * sstep(0.4, 0.7, n1)) + tidal * 0.55
    grass = dry * 0.75 * (1 - sstep(0.4, 0.65, n2)) * (1 - sstep(1.4, 1.1, h) * 0)
    gravel = 0.1 + 0.9 * sstep(0.5, 1.0, slope * 2.2) + 0.2 * sstep(0.62, 0.8, n1)
    salt = np.maximum(zr("SaltField", 6) * (0.7 + 0.3 * sstep(0.3, 0.6, n1)), 0) * dry
    road = np.zeros(X.shape)
    for rid, pts in R.items():
        d, _, _ = poly_dist(pts); road = np.maximum(road, (1 - sstep(1.6, 3.4, d)) * 0.6 * (rid not in ("R3-6",)))
    road = np.maximum(road, np.maximum.reduce([zr("Harbor", 4) * 0.45, disc(1215, 690, 18, 6) * 0.5]))
    dirt = np.maximum(dirt, road * dry); grass = grass * (1 - road) * (1 - salt)
    stack = np.clip(np.stack([dirt, grass, gravel, salt], -1), 0, 1)
    tot = stack.sum(-1); stack[..., 1] += np.clip(1 - tot, 0, 1) * dry
    for k in range(4): stack[..., k] = blur(stack[..., k], 0.8)
    foam = (sstep(-0.9, -0.5, h) * (1 - sstep(-0.35, 0.1, h)))      # 썰물선 둘레 물거품 띠
    wet = np.clip(tidal + foam * 0.3, 0, 1)
    return stack, foam, wet

def write(h, stack, foam, wet):
    os.makedirs(OUT, exist_ok=True)
    v = np.round(np.clip((h - HMIN) / (HMAX - HMIN), 0, 1) * 65535).astype(np.uint32)
    rgba = np.zeros(h.shape + (4,), np.uint8); rgba[..., 0] = v >> 8; rgba[..., 1] = v & 255; rgba[..., 3] = 255
    Image.fromarray(rgba, "RGBA").save(os.path.join(OUT, "heightmap.png"))
    s = (np.clip(stack[:H, :W], 0, 1) * 255).astype(np.uint8); Image.fromarray(s, "RGBA").save(os.path.join(OUT, "splat_a.png"))
    z = np.zeros((H, W), np.uint8); g = (np.clip(foam[:H, :W], 0, 1) * 255).astype(np.uint8); b = (np.clip(wet[:H, :W], 0, 1) * 255).astype(np.uint8)
    Image.fromarray(np.stack([z, g, b, np.full_like(z, 255)], -1), "RGBA").save(os.path.join(OUT, "splat_b.png"))

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

def preview(h, stack, foam, wet):
    cols = {"dirt": hexc("#8A7456"), "grass": hexc("#7E8A5A"), "gravel": hexc("#8A877E"), "salt": hexc("#DAD6C8")}
    img = stack[..., 0:1] * cols["dirt"] + stack[..., 1:2] * cols["grass"] + stack[..., 2:3] * cols["gravel"] + stack[..., 3:4] * cols["salt"]
    img = img / np.maximum(stack.sum(-1), 1e-3)[..., None]
    img = img * (1 - 0.35 * wet[..., None])
    sea = np.clip((-h + LOW) / 1.2, 0, 1)[..., None]; img = img * (1 - sea) + np.array([40, 74, 96], np.float32) * sea       # 썰물선 아래는 바다색
    gy, gx = np.gradient(blur(h, 1.2)); shade = np.clip(0.8 - 0.9 * (gx * 0.6 + gy * 0.8) + 0.01 * h, 0.5, 1.2)
    img = np.clip(img * shade[..., None], 0, 255).astype(np.uint8)[::-1]
    im = Image.fromarray(img); from PIL import ImageDraw; d = ImageDraw.Draw(im)
    fy = lambda y: H - (y - Y0); fx = lambda x: x - X0
    for r in MAP["roads"]: d.line([(fx(p[0]), fy(p[1])) for p in r["points"]], fill=(240, 231, 211), width=2)
    for z in MAP["zones"]:
        x0, y0, x1, y1 = z["rect_m"]
        if x0 >= X0: d.rectangle([fx(x0), fy(y1), fx(x1), fy(y0)], outline=(255, 255, 255)); d.text((fx(x0) + 3, fy(y1) + 3), z["code"], fill=(255, 255, 255))
    for b in MAP["boss_arenas"]:
        if b["x"] >= X0: d.ellipse([fx(b["x"]) - b["radius_m"], fy(b["y"]) - b["radius_m"], fx(b["x"]) + b["radius_m"], fy(b["y"]) + b["radius_m"]], outline=(255, 90, 90), width=2)
    for s in MAP["shrines"]:
        if s["x"] >= X0: d.ellipse([fx(s["x"]) - 4, fy(s["y"]) - 4, fx(s["x"]) + 4, fy(s["y"]) + 4], fill=(255, 220, 120))
    im.resize((W, H), Image.LANCZOS).save(os.path.join(ROOT, "assets3d", "previews", "act3_east_terrain_map.png"))

if __name__ == "__main__":
    h = build_height(); print("height", h.shape, round(float(h.min()), 2), round(float(h.max()), 2))
    stack, foam, wet = build_splats(h); write(h, stack, foam, wet); make_layers(); preview(h, stack, foam, wet)
    gy, gx = np.gradient(h); sl = np.hypot(gx, gy)
    flat = {s["id"]: round(float(sl[int(s["y"] - Y0), int(s["x"] - X0)]), 3) for s in MAP["shrines"] if s["x"] >= X0}
    for b in MAP["boss_arenas"]:
        if b["x"] >= X0: flat[b["boss"]] = round(float(sl[int(b["y"] - Y0), int(b["x"] - X0)]), 3)
    json.dump({"origin_m": [X0, Y0], "size_x_m": W, "size_z_m": H, "size": W, "height_res_x": W + 1, "height_res_z": H + 1, "splat_res_x": W, "splat_res_z": H, "height_min_m": HMIN, "height_max_m": HMAX, "layer_tile_m": [6, 6, 6, 6, 6],
               "tide_low_m": LOW, "tide_high_m": HIGH, "sea_floor_m": SEA, "south_bay_floor_m": -6.5, "coast_ramp_points": [[1040, 110], [1014, 60], [988, 0]],
               "layers": {"dirt": "마른 흙·갯벌 흙", "grass": "갯풀", "gravel": "자갈·바위", "paddy": "소금(splat_a A)", "leaf": "눈(⑥용, splat_b R, ⑤는 0)", "splat_b.G": "물거품", "splat_b.B": "젖은 갯벌"},
               "note": "아트 terrain_act3.py가 만든다. 행 0=남쪽(월드 y 0). 썰물 물높이 -0.5, 밀물 +0.6.", "slope_at_shrines_and_arenas": flat}, open(os.path.join(OUT, "terrain.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("기울기", flat)
