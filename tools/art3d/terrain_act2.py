"""2막(③ 붉은재 · ④ 쇳골) 땅 자료 만들기. 실행: python3 terrain_act2.py   (블렌더 불필요, numpy·PIL만)
입력: planning/openworld/act2/act2_map.json (구역·길·서낭당·보스 자리). 산출: assets3d/terrain_act2/
 - terrain.json, heightmap.png(16비트 R·G, 1막 약속과 같은 형식), splat_a.png, splat_b.png, layer_*.png(2막용 5장), act2_terrain_map.png(미리보기)
1막과 다른 점(코드팀이 알아야 함): 지도가 정사각이 아니고 월드 안에서 옮겨 앉는다 → terrain.json에 origin_m [0,640], size_x_m 768, size_z_m 640, height_res_x 769 / height_res_z 641 을 더했다.
층 이름은 1막과 같되 2막에서는 뜻이 다르다(셰이더·코드는 그대로 쓰고 그림만 2막 것을 쓴다):
  dirt=붉은 흙(③ 붉은재), grass=마른 풀, gravel=회색 바위·자갈, paddy(A 채널)=검은 쇠찌꺼기·석탄(④ 쇳골), leaf(splat_b R)=누런 황토(④ 쇳골 흙).
좌표: 월드 x=동, y=북(640~1280). 배열은 행 0 = 남쪽(y 640)이다(1막 약속). 서낭당·보스 마당·구역 중앙은 평평하게 눌러 둔다(기울기 0.3 이하)."""
import os, json, math
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
OUT = os.path.join(ROOT, "assets3d", "terrain_act2")
MAP = json.load(open("/mnt/project-files/planning/openworld/act2/act2_map.json", encoding="utf-8")) if os.path.exists("/mnt/project-files/planning/openworld/act2/act2_map.json") else json.load(open(os.path.join(ROOT, "data", "art", "act2_map.json"), encoding="utf-8"))
X0, Y0, W, H = 0, 640, 768, 640      # 월드 원점(남서 모서리)과 크기(m)
HMIN, HMAX = -1.0, 14.0
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

def build_height():
    n1 = fbm(X, Y, [120, 45, 15], 11) - 0.5
    h = 2.6 + 3.4 * (fbm(X, Y, [200, 80], 5) - 0.5) + 1.4 * n1          # 바탕: 완만한 구릉
    # 가장자리 산(동·서·북쪽 40m와, 두 고개 입구를 뺀 남쪽): 월드 끝을 산으로 막는다
    edge = np.maximum.reduce([1 - sstep(0, 45, X - X0), 1 - sstep(0, 45, (X0 + W) - X), 1 - sstep(0, 45, (Y0 + H) - Y)])
    south = (1 - sstep(0, 70, Y - Y0)) * (1 - np.maximum(disc(105, 640, 55, 45), disc(440, 640, 55, 45)))   # 남쪽 두 입구는 열어 둔다
    h = mix(h, np.clip(np.maximum(edge, south), 0, 1), 9.0 + 3.0 * n1)
    # 구역
    h = mix(h, zr("FortressVillage", 18), 1.8 + 0.15 * n1)
    h = mix(h, zr("Fortress", 30), 9.0 + 0.3 * n1); h = mix(h, disc(125, 1018, 20, 6), 9.0)        # 산성 마당(보스 B-05 반경 16)
    hills = zr("ArrowValley", 25); h = mix(h, hills, 8.0 + 1.2 * n1)
    h = mix(h, rect(320, 410, 860, 990, 30), 6.0 + 0.8 * n1)                                       # 능선 목 둘레 산덩이
    h = mix(h, zr("Camp", 22), 4.5 + 0.1 * n1); h = mix(h, disc(245, 1138, 20, 6), 4.5)             # 군막 터(B-06)
    h = mix(h, zr("BigTomb", 22), 3.0 + 0.15 * n1); h = h + 2.4 * np.exp(-((np.hypot(X - 90, Y - 1185) / 9) ** 2))   # 큰 무덤 봉분
    t = 1.8 + (Y - 800) / 125.0 * 3.0; terr = np.round(t) * 0.7 + t * 0.3                            # 광부촌: 북쪽으로 오르는 계단밭
    h = mix(h, zr("MinerTown", 18), terr + 0.12 * n1)
    h = mix(h, disc(505, 952, 24, 14), 7.0)                                                          # 광산 주인집 터(B-08 반경 14)
    h = mix(h, zr("Sorting", 18), 2.2 + 0.1 * n1)
    h = mix(h, np.maximum(zr("MainShaft", 25), zr("Collapse", 25)), 9.0 + 1.0 * n1)                # 갱도 골을 파기 전의 산
    # 파낸 협곡: 화살골·갱도 골·막장 웅덩이
    def canyon(h, pts, wf, ww, f0, f1):
        d, s, L = poly_dist(pts); floor = f0 + (f1 - f0) * np.clip(s / L, 0, 1); cut = 1 - sstep(wf, wf + ww, d)
        return mix(h, cut, floor + 0.08 * n1)
    h = canyon(h, [(175, 885), (215, 920), (250, 960), (250, 1025), (250, 1075)], 5.0, 10.0, 1.6, 4.2)
    h = canyon(h, [(540, 960), (560, 980), (615, 1055), (660, 1120), (682, 1150), (705, 1190)], 3.6, 7.0, 2.4, 1.0)
    h = mix(h, disc(705, 1192, 14, 11), 1.0)                                                          # 막장 웅덩이(B-07 반경 14)
    # 남쪽 입구는 1막 북쪽 끝 높이(0.3m)와 이어 붙인다
    h = mix(h, (1 - sstep(0, 28, Y - Y0)) * np.maximum(disc(105, 640, 40, 30), disc(440, 640, 40, 30)), 0.3)
    # 길: 노드 높이를 부드럽게 이어 평탄하게 눌러 비탈이 길을 막지 않게 한다
    hb = blur(h, 9.0)
    def hat(p): return float(hb[int(np.clip(p[1] - Y0, 0, H)), int(np.clip(p[0] - X0, 0, W))])
    for rid, pts in R.items():
        if rid == "R2-12": continue
        d, s, L = poly_dist(pts); cum = [0.0]
        for a, b in zip(pts, pts[1:]): cum.append(cum[-1] + math.dist(a, b))
        prof = np.interp(s, cum, [hat(p) for p in pts])
        h = mix(h, 1 - sstep(2.6, 7.5, d), prof + 0.03 * n1)
    for sx, sy in [(s["x"], s["y"]) for s in MAP["shrines"]] + [(b["x"], b["y"]) for b in MAP["boss_arenas"]]:   # 서낭당·보스 자리 둘레는 평평하게
        c = float(hb[int(sy - Y0), int(sx - X0)]); h = mix(h, disc(sx, sy, 5.0, 5.0), c) if all(abs(sx - b["x"]) > 1 or abs(sy - b["y"]) > 1 for b in MAP["boss_arenas"]) else h
    return np.clip(h, HMIN + 0.01, HMAX - 0.01)

def build_splats(h):
    gy, gx = np.gradient(h); slope = np.hypot(gx, gy)
    n1 = fbm(X, Y, [30, 9, 3], 31); n2 = fbm(X, Y, [60, 18], 41)
    west = 1 - sstep(330, 400, X)          # ③ 붉은재(서쪽) ↔ ④ 쇳골(동쪽)
    dirt = west * (0.55 + 0.45 * sstep(0.4, 0.7, n1)); grass = west * (0.7 * (1 - sstep(0.35, 0.6, n2))) * (1 - dirt * 0.4)
    gravel = np.full(X.shape, 0.12) + 0.9 * sstep(0.55, 1.0, slope * 2.2) + 0.25 * sstep(0.62, 0.8, n1)
    slag = (1 - west) * 0.1 + np.zeros(X.shape); loam = (1 - west) * (0.55 + 0.4 * sstep(0.4, 0.75, n1))
    # 쇳골 광부촌·선탄장·갱도 골은 쇠찌꺼기가 깔린다
    pit = np.maximum.reduce([zr("Sorting", 8), zr("MainShaft", 3) * (h < 3.5), zr("Collapse", 3) * (h < 3.5), zr("MinerTown", 6) * 0.45])
    d89, _, _ = poly_dist(R["R2-9"]); pit = np.maximum(pit, 1 - sstep(4.0, 9.0, d89))
    slag = np.maximum(slag, pit * (0.5 + 0.5 * sstep(0.3, 0.7, n1))); loam = loam * (1 - slag * 0.8)
    # 길과 마당: 밟혀서 맨흙(붉은 흙) — 쇳골 길은 황토
    road = np.zeros(X.shape)
    for rid, pts in R.items():
        d, _, _ = poly_dist(pts); road = np.maximum(road, (1 - sstep(1.6, 3.4, d)) * (0.6 if rid != "R2-12" else 0.0))
    yard = np.maximum.reduce([zr("FortressVillage", 6) * 0.5, disc(125, 1018, 22, 6), disc(245, 1138, 22, 6), disc(505, 952, 18, 6), zr("MinerTown", 5) * 0.4])
    road = np.maximum(road, yard)
    dirt = np.where(west > 0.5, np.maximum(dirt, road), dirt); loam = np.where(west > 0.5, loam, np.maximum(loam, road)); grass = grass * (1 - road)
    # 산성 마당·큰 무덤 풀
    grass = np.maximum(grass, disc(90, 1185, 30, 20) * 0.9); gravel = np.maximum(gravel, disc(125, 1018, 22, 10) * 0.35)
    stack = np.stack([dirt, grass, gravel, slag], -1); stack = np.clip(stack, 0, 1)
    # 합이 1에 가깝게(코드가 다시 1로 맞춘다). 풀이 모자라면 서쪽은 풀, 동쪽은 황토로 채운다
    tot = stack.sum(-1) + loam; fill = np.clip(1 - tot, 0, 1)
    stack[..., 1] += fill * west; loam = loam + fill * (1 - west)
    for k in range(4): stack[..., k] = blur(stack[..., k], 0.8)
    loam = blur(np.clip(loam, 0, 1), 0.8)
    return stack, loam

def write(h, stack, loam):
    os.makedirs(OUT, exist_ok=True)
    v = np.round(np.clip((h - HMIN) / (HMAX - HMIN), 0, 1) * 65535).astype(np.uint32)
    rgba = np.zeros(h.shape + (4,), np.uint8); rgba[..., 0] = v >> 8; rgba[..., 1] = v & 255; rgba[..., 3] = 255
    Image.fromarray(rgba, "RGBA").save(os.path.join(OUT, "heightmap.png"))   # 행 0 = 남쪽(y 640), 위쪽 줄이 남쪽
    s = stack[:H, :W]; a = (np.clip(s, 0, 1) * 255).astype(np.uint8); Image.fromarray(a, "RGBA").save(os.path.join(OUT, "splat_a.png"))
    lf = (np.clip(loam[:H, :W], 0, 1) * 255).astype(np.uint8); z = np.zeros_like(lf)
    Image.fromarray(np.stack([lf, z, z, np.full_like(lf, 255)], -1), "RGBA").save(os.path.join(OUT, "splat_b.png"))   # R = 황토(1막의 낙엽 자리), G·B 안 씀

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
    save("dirt", lay("#9A5A3E", "#7C4630", "#B4744E", (101, 102, 103), 104))        # 붉은 흙
    save("grass", lay("#6F7A48", "#8A8450", "#A29A5E", (111, 112, 113), 114))       # 마른 풀
    save("gravel", lay("#7A776F", "#5E5A54", "#9A968C", (121, 122, 123), 124))      # 회색 바위·자갈
    def slag(pn):
        n1 = 0.5 * pn(5, 131) + 0.5 * pn(14, 132); f = 0.8 + 0.4 * pn(110, 133)
        base = lerp(np.broadcast_to(hexc("#2E2C30"), n1.shape + (3,)), np.broadcast_to(hexc("#444048"), n1.shape + (3,)), np.clip((n1 - 0.35) / 0.35, 0, 1))
        glint = np.clip((pn(120, 134) - 0.8) / 0.1, 0, 1); base = lerp(base, np.broadcast_to(hexc("#6A3A2A"), base.shape), np.clip((pn(18, 135) - 0.7) / 0.15, 0, 1) * 0.5)
        return lerp(base, np.broadcast_to(hexc("#8A8A9A"), base.shape), glint * 0.5) * f[..., None]
    save("paddy", tileable(slag))                                                    # 검은 쇠찌꺼기·석탄(1막 '논' 자리)
    save("leaf", lay("#A8864E", "#8E6E3E", "#C0A064", (141, 142, 143), 144))        # 누런 황토(1막 '낙엽' 자리)

def preview(h, stack, loam):
    cols = {"dirt": hexc("#9A5A3E"), "grass": hexc("#7A8048"), "gravel": hexc("#7A776F"), "slag": hexc("#34323A"), "loam": hexc("#A8864E")}
    img = (stack[..., 0:1] * cols["dirt"] + stack[..., 1:2] * cols["grass"] + stack[..., 2:3] * cols["gravel"] + stack[..., 3:4] * cols["slag"] + loam[..., None] * cols["loam"])
    img = img / np.maximum(stack.sum(-1) + loam, 1e-3)[..., None]
    gy, gx = np.gradient(blur(h, 1.2)); shade = np.clip(0.75 + 0.9 * (gx * 0.6 + gy * 0.8) * -1.0 + 0.012 * h, 0.4, 1.25)
    img = np.clip(img * shade[..., None], 0, 255).astype(np.uint8)[::-1]       # 위쪽이 북쪽이 되게 뒤집는다
    im = Image.fromarray(img); from PIL import ImageDraw; d = ImageDraw.Draw(im)
    fy = lambda y: H - (y - Y0)
    for r in MAP["roads"]:
        d.line([(p[0], fy(p[1])) for p in r["points"]], fill=(240, 231, 211), width=2)
    for z in MAP["zones"]: x0, y0, x1, y1 = z["rect_m"]; d.rectangle([x0, fy(y1), x1, fy(y0)], outline=(255, 255, 255)); d.text((x0 + 3, fy(y1) + 3), z["name"], fill=(255, 255, 255))
    for b in MAP["boss_arenas"]: d.ellipse([b["x"] - b["radius_m"], fy(b["y"]) - b["radius_m"], b["x"] + b["radius_m"], fy(b["y"]) + b["radius_m"]], outline=(255, 90, 90), width=2)
    for s in MAP["shrines"]: d.ellipse([s["x"] - 4, fy(s["y"]) - 4, s["x"] + 4, fy(s["y"]) + 4], fill=(255, 220, 120))
    im.resize((W * 2, H * 2), Image.LANCZOS).save(os.path.join(ROOT, "assets3d", "previews", "act2_terrain_map.png"))

if __name__ == "__main__":
    h = build_height(); print("height", h.shape, round(float(h.min()), 2), round(float(h.max()), 2))
    stack, loam = build_splats(h); write(h, stack, loam); make_layers(); preview(h, stack, loam)
    gy, gx = np.gradient(h)
    flat = {}
    for s in MAP["shrines"]: flat[s["id"]] = round(float(np.hypot(gx, gy)[int(s["y"] - Y0), int(s["x"] - X0)]), 3)
    for b in MAP["boss_arenas"]: flat[b["boss"]] = round(float(np.hypot(gx, gy)[int(b["y"] - Y0), int(b["x"] - X0)]), 3)
    json.dump({"origin_m": [X0, Y0], "size_x_m": W, "size_z_m": H, "size": W, "height_res_x": W + 1, "height_res_z": H + 1, "splat_res_x": W, "splat_res_z": H, "height_min_m": HMIN, "height_max_m": HMAX, "layer_tile_m": [6, 6, 6, 6, 6],
               "layers": {"dirt": "붉은 흙(③)", "grass": "마른 풀", "gravel": "회색 바위·자갈(급경사)", "paddy": "검은 쇠찌꺼기·석탄(④, splat_a A 채널)", "leaf": "누런 황토(④, splat_b R 채널)"},
               "detail": "1막 detail_*.png 를 그대로 쓴다(층 이름이 같다)", "note": "아트 terrain_act2.py가 만든다. 행 0=남쪽(월드 y 640). 월드 좌표=origin+픽셀. 코드는 1막 땅과 같은 셰이더에 origin·직사각형 크기만 더해 받는다.",
               "slope_at_shrines_and_arenas": flat, "heights_note": "산성 마당 9m, 군막 터 4.5m, 갱도 골 바닥 2.4→1.0m, 막장 웅덩이 1.0m, 가장자리 산 9~12m"}, open(os.path.join(OUT, "terrain.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("기울기(서낭당·보스 자리)", flat)
