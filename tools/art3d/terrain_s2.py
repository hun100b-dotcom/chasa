"""시즌 2 저승 ⑦~⑩ 땅 자료 만들기. 실행: python3 terrain_s2.py [7 8 9 10]  (블렌더 불필요, numpy·PIL만)
입력: planning/openworld/act4/r7_map.json, r8_r10_map.json (저승 좌표계 하나: x=동, y=북, ⑦ 0~640×0~560 · ⑧ 560~1200×560~1120 · ⑨ -80~560×600~1160 · ⑩ 200~840×-640~0).
산출: assets3d/terrain_s2_r7 ~ r10/ (terrain.json, heightmap.png(16비트 R·G), splat_a/b.png, layer_*.png), 미리보기 assets3d/previews/s2_r7_terrain_map.png 등.
높이 약속: 기준 땅 0.3, 물 표면 0.0(강·먹물), 강바닥 -1.4. 높이 범위 -3.0~8.0. 행 0 = 남쪽(2·3막과 같음). 가장자리 14 m는 이웃 땅과 이어지게 0.3으로 맞춘다.
층 뜻(저승): dirt=재 섞인 흙(회갈), grass=은빛 마른 풀, gravel=먹돌·바위, paddy(splat_a A)=먹(검게 물든 바닥, 먹방·여울), splat_b R=종이 가루(흰 먼지), G=물거품, B=젖음.
보스 마당은 반경 + 6 m 까지 완전 평평(기울기 0)으로 눌러 둔다. 이 약속은 기획(s2-bosses-openworld.md)의 '바닥 평평'."""
import os, sys, json, math
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PL = "/mnt/project-files/planning/openworld/act4/"
M7 = json.load(open(PL + "r7_map.json", encoding="utf-8")); M8 = json.load(open(PL + "r8_r10_map.json", encoding="utf-8"))
REG = {7: dict(name="⑦ 삼도천 기슭", rect=M7["field"]["rect_m"], zones=M7["zones"], arenas=M7["boss_arenas"], roads=M7["roads"]),
       8: dict(name="⑧ 명부전 담장 밖", rect=M8["regions"]["8"]["field_rect_m"], zones=M8["regions"]["8"]["zones"], arenas=M8["regions"]["8"]["boss_arenas"], roads=[]),
       9: dict(name="⑨ 빈 관할", rect=M8["regions"]["9"]["field_rect_m"], zones=M8["regions"]["9"]["zones"], arenas=M8["regions"]["9"]["boss_arenas"], roads=[]),
       10: dict(name="⑩ 열째 관할", rect=M8["regions"]["10"]["field_rect_m"], zones=M8["regions"]["10"]["zones"], arenas=M8["regions"]["10"]["boss_arenas"], roads=[])}
HMIN, HMAX, BASE = -3.0, 8.0, 0.3
RIVER7 = [(600, 520), (540, 450), (470, 390), (438, 320), (434, 250), (446, 180), (470, 130), (468, 126)]   # 강 중심선(⑦). 나루 앞(y 250)은 기획 x428을 동쪽으로 6 m 밀어 B-13 마당(반경 14, 동쪽 끝 419)이 물가에서 끝나게 함

def setup(rid):
    global X0, Y0, W, H, X, Y, OUT, R
    R = REG[rid]; x0, y0, x1, y1 = R["rect"]; X0, Y0, W, H = x0, y0, x1 - x0, y1 - y0
    xs = np.arange(W + 1, dtype=np.float64) + X0; ys = np.arange(H + 1, dtype=np.float64) + Y0; X, Y = np.meshgrid(xs, ys)
    OUT = os.path.join(ROOT, "assets3d", f"terrain_s2_r{rid}")
def sstep(a, b, x): t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
def vnoise(x, y, cell, seed):
    rs = np.random.RandomState(seed); n = int(max(W, H) / cell) + 4; g = rs.rand(n, n)
    fx, fy = x / cell, y / cell; ix, iy = np.floor(fx).astype(int), np.floor(fy).astype(int); tx, ty = fx - ix, fy - iy
    tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty); ix, iy = ix % n, iy % n
    return (g[iy, ix] * (1 - tx) + g[iy, (ix + 1) % n] * tx) * (1 - ty) + (g[(iy + 1) % n, ix] * (1 - tx) + g[(iy + 1) % n, (ix + 1) % n] * tx) * ty
def fbm(x, y, cells, seed):
    w = [1.0 / (2 ** i) for i in range(len(cells))]; s = sum(w); return sum(wi * vnoise(x, y, c, seed + i * 7) for i, (c, wi) in enumerate(zip(cells, w))) / s
def blur(a, sigma):
    r = int(sigma * 3) + 1; k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2); k /= k.sum()
    p = np.pad(a, ((0, 0), (r, r)), mode="edge"); a = sum(k[i] * p[:, i:i + a.shape[1]] for i in range(2 * r + 1))
    p = np.pad(a, ((r, r), (0, 0)), mode="edge"); return sum(k[i] * p[i:i + a.shape[0], :] for i in range(2 * r + 1))
def rect(x0, x1, y0, y1, m): return sstep(x0 - m, x0, X) * (1 - sstep(x1, x1 + m, X)) * sstep(y0 - m, y0, Y) * (1 - sstep(y1, y1 + m, Y))
def disc(cx, cy, r, m): return 1 - sstep(r, r + m, np.hypot(X - cx, Y - cy))
def poly_dist(pts):
    best = np.full(X.shape, 1e9); bs = np.zeros(X.shape); acc = 0.0
    for a, b in zip(pts, pts[1:]):
        ax, ay, bx, by = a[0], a[1], b[0], b[1]; dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy; L = math.sqrt(L2)
        t = np.clip(((X - ax) * dx + (Y - ay) * dy) / L2, 0, 1); d = np.hypot(X - (ax + t * dx), Y - (ay + t * dy))
        upd = d < best; best = np.where(upd, d, best); bs = np.where(upd, acc + t * L, bs); acc += L
    return best, bs, acc
def mix(h, mask, target): return h * (1 - mask) + target * mask
def zr(code, m):
    for z in R["zones"]:
        if z["code"] == code: x0, y0, x1, y1 = z["rect_m"]; return rect(x0, x1, y0, y1, m)
    raise KeyError(code)

def build_height(rid):
    n1 = fbm(X, Y, [120, 45, 15], 31 + rid) - 0.5
    hills = 1.4 * (fbm(X, Y, [200, 80], 17 + rid) - 0.5) + 0.5 * n1
    h = BASE + hills
    if rid == 7:
        # 강: 북동에서 남으로. 나루 마을·갈대늪은 낮은 평지, 동쪽(강 건너)은 오르는 능선(건널 수 없는 안개 쪽)
        h = mix(h, zr("Reeds", 12), 0.05 + 0.25 * (fbm(X, Y, [14, 5], 3) - 0.5) + 0.1)
        h = mix(h, zr("Ferrytown", 14), BASE + 0.04 * n1)
        dr, sr, Lr = poly_dist(RIVER7)
        w = 13.0 + 3.0 * np.sin(sr / 40.0)                                     # 강폭 24~32
        rapid = sstep(380, 400, Y) * (1 - sstep(500, 520, Y)) * (X > 440)         # 먹물 여울: 폭 좁고 얕고 빠름
        h = mix(h, 1 - sstep(w * 0.55, w * 0.55 + 10.0, dr), -1.4 + 0.5 * rapid + 0.05 * n1)
        east = sstep(0, 30, (X - 470 - 0.55 * (Y - 90)) + 0.0) * (X > 440) * (1 - sstep(330, 420, Y) * 0)     # 강 건너 능선
        h = h + 3.5 * east * (dr > w) * sstep(0, 1, dr / (w + 14))
        dam = rect(380, 560, 40, 128, 8)                                         # 물안개 둑: 둑 위 평지
        h = mix(h, dam, 1.8 + 0.03 * n1)
        h = mix(h, 1 - sstep(0, 30, Y - 40), 0.3)                                # 둑 남쪽은 안개 속 평지(이웃 ⑩과 높이를 맞춤)
    elif rid == 8:
        h = h * 0.6
        for z in ("ClerkQuarters", "InkRoom", "Archive", "NumberYard"): h = mix(h, zr(z, 14), BASE + 0.02 * n1)
        h = mix(h, rect(560, 1200, 1030, 1050, 6), BASE)                       # 명부전 담장 밑 마당(y 1040 담)
        h = mix(h, rect(850, 950, 960, 1040, 8), BASE)                         # 관아 마당(문 (900,1040) 앞)
    elif rid == 9:
        h = h * 0.6
        for z in ("BlankTown", "NinthGate", "SeallessMarket"): h = mix(h, zr(z, 14), BASE + 0.02 * n1)
        # 인장 굴: 지붕 없는 바위 틈. 바닥(아레나)을 둘러 바위 담이 오르고 동쪽(굴 입구 (80,975))만 열려 있다. 남쪽 담은 1.5 m로 낮춰 쿼터뷰가 가리지 않게
        cx, cy = 30.0, 985.0; ang = np.arctan2(Y - cy, X - cx); rr = np.hypot(X - cx, Y - cy)
        wall = sstep(20, 27, rr) * (1 - sstep(38, 50, rr))
        opening = np.exp(-(((ang - 0.0 + np.pi) % (2 * np.pi) - np.pi) / 0.42) ** 2)             # 동쪽 열림
        south = np.exp(-(((ang + np.pi / 2 + np.pi) % (2 * np.pi) - np.pi) / 0.9) ** 2)            # 남쪽
        hgt = 6.5 - 5.0 * south
        h = mix(h, wall * (1 - opening), BASE + hgt * (0.85 + 0.3 * (fbm(X, Y, [9, 3], 5) - 0.5)))
        h = mix(h, disc(cx, cy, 12, 6), BASE)
    elif rid == 10:
        h = mix(h, zr("FirstVillage", 14), BASE + 0.03 * n1)
        h = mix(h, zr("ChainGraves", 14), BASE + 0.1 * (fbm(X, Y, [12, 4], 7) - 0.5))
        h = mix(h, zr("WellYard", 14), BASE)
        # 물막이 바닥: 가장 낮은 땅. 북쪽에서 큰 그릇처럼 내려가고 바닥(반경 22 + 6 m)은 평평
        bowl = 1 - sstep(30, 110, np.hypot((X - 560) / 1.2, Y + 520))
        h = mix(h, bowl, -1.5 + 0.04 * n1)
    # 길 평탄화(마을·장터 길은 마당과 붙어 있음)
    hb = blur(h, 9.0)
    for r in R["roads"]:
        pts = r["points"]; inside = [p for p in pts if X0 - 1 <= p[0] <= X0 + W + 1 and Y0 - 1 <= p[1] <= Y0 + H + 1]
        if len(inside) < 2: continue
        d, s, L = poly_dist(inside); cum = [0.0]
        for a, b in zip(inside, inside[1:]): cum.append(cum[-1] + math.dist(a, b))
        prof = np.interp(s, cum, [max(float(hb[int(np.clip(p[1] - Y0, 0, H)), int(np.clip(p[0] - X0, 0, W))]), 0.3) for p in inside])
        h = mix(h, (1 - sstep(2.6, 7.5, d)) * (1 - 0.0), prof + 0.03 * n1)
    # 보스 마당: 반경 + 6 m 까지 완전 평평(마당 높이는 그 자리 주변 평균, 최소 0.3)
    for a in R["arenas"]:
        hb2 = blur(h, 6.0); c = max(float(hb2[int(np.clip(a["y"] - Y0, 0, H)), int(np.clip(a["x"] - X0, 0, W))]), 0.3) if rid != 10 or a["boss"] != "B-20" else -1.5
        if rid == 7 and a["boss"] == "B-14": c = 1.8
        h = mix(h, disc(a["x"], a["y"], a["radius_m"] + 3, 7), c)
    # 이웃 땅과 이어지는 가장자리 14 m
    edge = np.minimum.reduce([sstep(0, 14, X - X0), sstep(0, 14, X0 + W - X), sstep(0, 14, Y - Y0), sstep(0, 14, Y0 + H - Y)])
    keep = np.zeros(X.shape)
    if rid == 7: keep = disc(600, 520, 14, 16) * 1.0                      # 강 시작 쪽은 ⑧ 길목(금줄)이라 깎지 않는다
    h = mix(h, (1 - edge) * (1 - keep), BASE)
    return np.clip(h, HMIN + 0.01, HMAX - 0.01)

def build_splats(h, rid):
    gy, gx = np.gradient(h); slope = np.hypot(gx, gy)
    n1 = fbm(X, Y, [30, 9, 3], 51 + rid); n2 = fbm(X, Y, [60, 18], 61 + rid)
    water = sstep(0.0, -0.5, h)                                           # 물 표면(0.0)보다 낮은 곳
    dry = 1 - water
    dirt = dry * (0.3 + 0.45 * sstep(0.4, 0.7, n1))
    grass = dry * 0.7 * (1 - sstep(0.4, 0.65, n2))
    gravel = 0.1 + 0.9 * sstep(0.5, 1.0, slope * 2.2) + 0.2 * sstep(0.62, 0.8, n1)
    ink = np.zeros(X.shape)
    dust = np.zeros(X.shape)
    if rid == 7: ink = np.maximum(sstep(380, 400, Y) * (X > 440) * (1 - sstep(500, 530, Y)) * (water > 0.2), 0) * 0.9; dust = zr("Reeds", 8) * 0.5 * (0.5 + n1)
    if rid == 8: ink = zr("InkRoom", 10) * (0.55 + 0.4 * n1) + disc(880, 700, 8, 8); dust = zr("Archive", 8) * 0.6 + zr("NumberYard", 8) * 0.4
    if rid == 9: ink = disc(30, 985, 14, 8) * 0.3; dust = zr("BlankTown", 8) * 0.5 + zr("SeallessMarket", 8) * 0.4
    if rid == 10: ink = disc(560, -520, 28, 20) * 0.5; dust = zr("FirstVillage", 8) * 0.3
    road = np.zeros(X.shape)
    for r in R["roads"]:
        d, _, _ = poly_dist(r["points"]); road = np.maximum(road, (1 - sstep(1.6, 3.4, d)) * 0.6)
    for z in R["zones"]: x0, y0, x1, y1 = z["rect_m"]; road = np.maximum(road, rect(x0, x1, y0, y1, 4) * 0.25)
    dirt = np.maximum(dirt, road * dry); grass = grass * (1 - road) * (1 - np.clip(ink, 0, 1))
    stack = np.clip(np.stack([dirt, grass, gravel, ink], -1), 0, 1)
    tot = stack.sum(-1); stack[..., 1] += np.clip(1 - tot, 0, 1) * dry
    for k in range(4): stack[..., k] = blur(stack[..., k], 0.8)
    foam = sstep(-0.6, -0.1, h) * (1 - sstep(-0.05, 0.25, h)); wet = np.clip(water + foam * 0.3, 0, 1)
    return stack, np.clip(dust, 0, 1), foam, wet

def write(h, stack, dust, foam, wet):
    os.makedirs(OUT, exist_ok=True)
    v = np.round(np.clip((h - HMIN) / (HMAX - HMIN), 0, 1) * 65535).astype(np.uint32)
    rgba = np.zeros(h.shape + (4,), np.uint8); rgba[..., 0] = v >> 8; rgba[..., 1] = v & 255; rgba[..., 3] = 255
    Image.fromarray(rgba, "RGBA").save(os.path.join(OUT, "heightmap.png"))
    Image.fromarray((np.clip(stack[:H, :W], 0, 1) * 255).astype(np.uint8), "RGBA").save(os.path.join(OUT, "splat_a.png"))
    g = (np.clip(foam[:H, :W], 0, 1) * 255).astype(np.uint8); b = (np.clip(wet[:H, :W], 0, 1) * 255).astype(np.uint8); r = (np.clip(dust[:H, :W], 0, 1) * 255).astype(np.uint8)
    Image.fromarray(np.stack([r, g, b, np.full_like(g, 255)], -1), "RGBA").save(os.path.join(OUT, "splat_b.png"))
def hexc(h): h = h.lstrip("#"); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)
def make_layers():
    n = 512; yy, xx = np.meshgrid(np.arange(n), np.arange(n), indexing="ij")
    def pn(cells, seed):
        g = np.random.RandomState(seed).rand(cells, cells).astype(np.float32); fx = xx / n * cells; fy = yy / n * cells; ix = np.floor(fx).astype(int); iy = np.floor(fy).astype(int); tx = fx - ix; ty = fy - iy
        tx = tx * tx * (3 - 2 * tx); ty = ty * ty * (3 - 2 * ty); a = g[iy % cells, ix % cells]; b = g[iy % cells, (ix + 1) % cells]; c = g[(iy + 1) % cells, ix % cells]; d = g[(iy + 1) % cells, (ix + 1) % cells]
        return (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty
    def lerp(a, b, t): return a * (1 - t[..., None]) + b * t[..., None]
    def lay(name, c1, c2, c3, seeds, fs):
        n1 = 0.5 * pn(4, seeds[0]) + 0.3 * pn(10, seeds[1]) + 0.2 * pn(24, seeds[2]); f = 0.82 + 0.36 * pn(96, fs) * (0.6 + 0.4 * pn(160, fs + 1))
        base = lerp(np.broadcast_to(hexc(c1), n1.shape + (3,)), np.broadcast_to(hexc(c2), n1.shape + (3,)), np.clip((n1 - 0.3) / 0.4, 0, 1))
        base = lerp(base, np.broadcast_to(hexc(c3), base.shape), np.clip((pn(14, seeds[0] + 3) - 0.62) / 0.2, 0, 1) * 0.5)
        Image.fromarray(np.clip(base * f[..., None], 0, 255).astype(np.uint8)).save(os.path.join(OUT, f"layer_{name}.png"))
    lay("dirt", "#6E6A64", "#58554F", "#85807A", (301, 302, 303), 304)        # 재 섞인 흙
    lay("grass", "#8B9490", "#A2ABA6", "#75807C", (311, 312, 313), 314)       # 은빛 마른 풀
    lay("gravel", "#5A5A60", "#46464C", "#74747C", (321, 322, 323), 324)      # 먹돌·바위
    lay("paddy", "#2A2830", "#1E1C24", "#3A3842", (331, 332, 333), 334)       # 먹(검게 물든 바닥, 1막 '논' 자리)
    lay("leaf", "#D8D4CC", "#C6C2BA", "#E8E4DE", (341, 342, 343), 344)        # 종이 가루(1막 '낙엽' 자리)
def preview(h, stack, dust, foam, wet, rid):
    cols = [hexc("#6E6A64"), hexc("#8B9490"), hexc("#5A5A60"), hexc("#2A2830")]
    img = sum(stack[..., i:i + 1] * cols[i] for i in range(4)) / np.maximum(stack.sum(-1), 1e-3)[..., None]
    img = img * (1 - 0.3 * wet[..., None]) + dust[..., None] * 40
    sea = np.clip((0.0 - h) / 0.8, 0, 1)[..., None]; img = img * (1 - sea) + np.array([36, 52, 66], np.float32) * sea
    gy, gx = np.gradient(blur(h, 1.2)); shade = np.clip(0.8 - 0.9 * (gx * 0.6 + gy * 0.8) + 0.01 * h, 0.5, 1.2)
    im = Image.fromarray(np.clip(img * shade[..., None], 0, 255).astype(np.uint8)[::-1]); d = ImageDraw.Draw(im)
    fy = lambda y: H - (y - Y0); fx = lambda x: x - X0
    for r in R["roads"]: d.line([(fx(p[0]), fy(p[1])) for p in r["points"]], fill=(240, 231, 211), width=2)
    for z in R["zones"]: x0, y0, x1, y1 = z["rect_m"]; d.rectangle([fx(x0), fy(y1), fx(x1), fy(y0)], outline=(255, 255, 255)); d.text((fx(x0) + 3, fy(y1) + 3), z["code"], fill=(255, 255, 255))
    for b in R["arenas"]: d.ellipse([fx(b["x"]) - b["radius_m"], fy(b["y"]) - b["radius_m"], fx(b["x"]) + b["radius_m"], fy(b["y"]) + b["radius_m"]], outline=(255, 90, 90), width=2); d.text((fx(b["x"]) - 10, fy(b["y"]) - 5), b["boss"], fill=(255, 140, 140))
    im.save(os.path.join(ROOT, "assets3d", "previews", f"s2_r{rid}_terrain_map.png"))

if __name__ == "__main__":
    for rid in [int(a) for a in sys.argv[1:]] or [7, 8, 9, 10]:
        setup(rid); h = build_height(rid); stack, dust, foam, wet = build_splats(h, rid); write(h, stack, dust, foam, wet); make_layers(); preview(h, stack, dust, foam, wet, rid)
        gy, gx = np.gradient(h); sl = np.hypot(gx, gy)
        flat = {a["boss"]: round(float(sl[int(a["y"] - Y0), int(a["x"] - X0)]), 3) for a in R["arenas"]}
        arena_h = {a["boss"]: round(float(h[int(a["y"] - Y0), int(a["x"] - X0)]), 2) for a in R["arenas"]}
        json.dump({"region": rid, "name": R["name"], "origin_m": [X0, Y0], "size_x_m": W, "size_z_m": H, "size": W, "height_res_x": W + 1, "height_res_z": H + 1, "splat_res_x": W, "splat_res_z": H, "height_min_m": HMIN, "height_max_m": HMAX, "layer_tile_m": [6, 6, 6, 6, 6],
                   "water_surface_m": 0.0, "base_ground_m": BASE, "layers": {"dirt": "재 섞인 흙", "grass": "은빛 마른 풀", "gravel": "먹돌·바위", "paddy": "먹(splat_a A)", "leaf": "종이 가루(splat_b R)", "splat_b.G": "물거품", "splat_b.B": "젖음"},
                   "note": "terrain_s2.py가 만든다. 행 0=남쪽(월드 y=origin_m[1]). 저승 좌표계(⑦~⑩ 공통).", "arena_slope": flat, "arena_ground_m": arena_h}, open(os.path.join(OUT, "terrain.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(rid, R["name"], "높이", round(float(h.min()), 2), round(float(h.max()), 2), "마당 기울기", flat, "마당 높이", arena_h)
