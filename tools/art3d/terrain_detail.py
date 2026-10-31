"""가까이 볼 때 쓰는 이음매 없는 디테일 그림(흙·풀·자갈·이랑·낙엽)과 개울물 그림(흐름·반사·거품 흩뿌림)을 만든다.
왜: 청크 땅 그림은 8픽셀/m라 50° 가까이 보면 뭉개진다. 땅 종류마다 1.5m마다 반복되는 고해상도 알갱이 그림(약 340픽셀/m)을 곱해 주면 가까이서도 흙 알갱이·풀결·자갈·낙엽이 보인다.
모든 그림은 가로·세로로 이어 붙여도 이음매가 없다(노이즈 격자를 주기적으로 감쌌다). 값은 numpy 난수 씨앗 고정이라 다시 만들어도 같다."""
import numpy as np

def _smooth(t): return t * t * (3 - 2 * t)

def pnoise(n, cx, cy, seed):
    """주기 값 노이즈(0..1): 가로 cx칸·세로 cy칸 격자가 n픽셀을 정확히 한 바퀴 돈다. cx≠cy면 한쪽으로 길쭉한 결이 된다."""
    g = np.random.RandomState(seed).rand(cy, cx).astype(np.float32)
    yy, xx = np.meshgrid(np.arange(n), np.arange(n), indexing="ij")
    fx = xx / n * cx; fy = yy / n * cy; ix = np.floor(fx).astype(int); iy = np.floor(fy).astype(int); tx = _smooth(fx - ix); ty = _smooth(fy - iy)
    a = g[iy % cy, ix % cx]; b = g[iy % cy, (ix + 1) % cx]; c = g[(iy + 1) % cy, ix % cx]; d = g[(iy + 1) % cy, (ix + 1) % cx]
    return (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty

def fb(n, cx, cy, seed, octs=4):
    """여러 겹 노이즈 합(0..1)."""
    tot = 0; w = 1.0; ws = 0
    for o in range(octs):
        tot = tot + pnoise(n, cx * 2 ** o, cy * 2 ** o, seed + o * 11) * w; ws += w; w *= 0.5
    return tot / ws

def worley(n, cells, seed, jitter=0.9):
    """주기 세포 노이즈: 가장 가까운 씨앗까지의 거리(0..1 정규화)와 씨앗 번호값. 자갈·돌 모양에 쓴다."""
    rs = np.random.RandomState(seed); pts = (rs.rand(cells, cells, 2) - 0.5) * jitter + 0.5; val = rs.rand(cells, cells)
    yy, xx = np.meshgrid((np.arange(n) + 0.5) / n * cells, (np.arange(n) + 0.5) / n * cells, indexing="ij")
    d1 = np.full((n, n), 9.0, np.float32); d2 = np.full((n, n), 9.0, np.float32); v = np.zeros((n, n), np.float32)
    ci = np.floor(xx).astype(int); cj = np.floor(yy).astype(int)
    for dj in (-1, 0, 1):
        for di in (-1, 0, 1):
            ii = (ci + di); jj = (cj + dj)
            px = ii + pts[jj % cells, ii % cells, 0]; py = jj + pts[jj % cells, ii % cells, 1]
            d = np.hypot(xx - px, yy - py)
            closer = d < d1; d2 = np.where(closer, d1, np.minimum(d2, d)); v = np.where(closer, val[jj % cells, ii % cells], v); d1 = np.where(closer, d, d1)
    return d1, d2 - d1, v

def normal_from_height(h, strength, px_per_unit=1.0):
    """높이(0..1) → 접선공간 노멀(OpenGL, 초록=위). 주기 이웃(np.roll)을 써서 이음매가 안 생긴다."""
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5 * strength; dy = (np.roll(h, 1, 0) - np.roll(h, -1, 0)) * 0.5 * strength   # 영상 위=북쪽=+y
    nx, ny, nz = -dx, -dy, np.ones_like(h); L = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack([nx / L * 0.5 + 0.5, ny / L * 0.5 + 0.5, nz / L * 0.5 + 0.5], -1)

def _mixc(a, b, t): return a * (1 - t[..., None]) + b * t[..., None]
def _col(c): return np.asarray(c, np.float32)[None, None, :]

def detail_tiles(C, n=512):
    """5층 디테일. 반환 {이름: (색 RGB uint8, 노멀 RGB uint8)}. 색은 층 평균색 둘레의 알갱이·결·돌·낙엽이라 땅 그림에 곱하거나 섞어 쓴다(평균 명도≈원래 층 색)."""
    out = {}
    # 풀: 가는 풀잎 결(세로로 긴 가는 노이즈 여러 방향) + 잎 끝 밝은 점 + 그늘진 뿌리
    h = 0.45 * fb(n, 64, 40, 101, 3) + 0.35 * fb(n, 40, 64, 102, 3) + 0.25 * pnoise(n, 160, 100, 103) + 0.25 * pnoise(n, 100, 160, 104)
    h = (h - h.min()) / (h.max() - h.min())
    base = _mixc(_col(C["grass_dark"]), _col(C["grass_light"]), np.clip((h - 0.25) * 1.6, 0, 1))
    base = _mixc(base, _col(C["grass_dry"]), np.clip((fb(n, 5, 5, 105, 3) - 0.62) * 3, 0, 1) * 0.4)
    base = base * (0.78 + 0.45 * h)[..., None]
    out["grass"] = (base, normal_from_height(h, 5.0))
    # 흙: 알갱이 + 작은 흙덩이 + 드문 작은 돌 + 가는 금
    d1, edge, v = worley(n, 28, 111); clod = np.clip(1 - d1 * 1.6, 0, 1)
    peb_d, _, pv = worley(n, 9, 112, 0.8); peb = np.clip(1 - peb_d * 5.5, 0, 1) ** 0.4 * (pv > 0.7)
    h = 0.5 * fb(n, 70, 70, 113, 3) + 0.35 * clod + 0.5 * peb + 0.2 * pnoise(n, 240, 240, 114)
    h = (h - h.min()) / (h.max() - h.min())
    base = _mixc(_col(C["road_dark"]), _col(C["road_light"]), np.clip(h * 1.2 - 0.1, 0, 1)) * (0.85 + 0.25 * fb(n, 6, 6, 115, 3))[..., None]
    base = _mixc(base, _col(C["pebble"]) * 0.9, np.clip(peb * 1.4, 0, 1) * 0.45)
    base = base * np.clip(1 - 0.35 * (edge < 0.04) * clod, 0, 1)[..., None]
    out["dirt"] = (base, normal_from_height(h, 6.0))
    # 자갈: 둥글둥글한 돌들(세포 노이즈), 돌마다 색이 다르고 틈은 어둡고 젖음
    d1, edge, v = worley(n, 14, 121, 0.7)
    dome = np.clip(1 - d1 * 1.5, 0, 1) ** 0.6; gap = np.clip(edge * 7, 0, 1) ** 0.7
    h = dome * gap * (0.7 + 0.3 * v) + 0.06 * pnoise(n, 200, 200, 122)
    h = (h - h.min()) / (h.max() - h.min())
    stone = _mixc(_col(C["shore"]), _col(C["pebble"]), v.astype(np.float32)) * (0.75 + 0.35 * v)[..., None]
    stone = _mixc(stone, _col(C["bed"]), np.clip((pnoise(n, 9, 9, 123) - 0.6) * 3, 0, 1) * 0.5)
    base = _mixc(_col(C["wet"]) * 1.15, stone, np.clip(gap * dome * 1.3, 0, 1)) * (0.8 + 0.3 * h)[..., None]
    out["gravel"] = (base, normal_from_height(h, 9.0))
    # 논·밭: 세로 이랑(주기 6줄) + 이랑 위 보리 줄기 결 + 고랑 흙덩이
    xs = (np.arange(n)[None, :] / n * 6 + 0.5) % 1.0 * np.ones((n, 1))
    ridge = np.clip(np.sin(np.pi * xs) ** 0.8, 0, 1) * (0.85 + 0.15 * pnoise(n, 3, 12, 131))
    stalk = pnoise(n, 120, 30, 132) * 0.5 + pnoise(n, 240, 40, 133) * 0.5
    h = ridge * (0.55 + 0.45 * stalk) + 0.15 * fb(n, 60, 60, 134, 3) * (1 - ridge)
    h = (h - h.min()) / (h.max() - h.min())
    base = _mixc(_col(C["furrow"]) * (0.85 + 0.3 * fb(n, 40, 40, 135, 3))[..., None], _col(C["barley_ridge"]) * (0.8 + 0.4 * stalk)[..., None], np.clip(ridge * 1.25 - 0.1, 0, 1))
    base = _mixc(base, _col(C["barley_ear"]), np.clip((stalk - 0.6) * 2.5, 0, 1) * ridge * 0.6)
    out["paddy"] = (base, normal_from_height(h, 7.0))
    # 낙엽: 길쭉한 잎 조각을 여러 방향으로 겹쳐 쌓고(테두리가 이어지게 가로·세로로 감아 그림), 이끼 얼룩, 솔잎 가는 줄
    from PIL import Image, ImageDraw
    rs = np.random.RandomState(141); canvas = Image.new("RGB", (n, n), tuple(int(x * 0.55) for x in C["litter_pine"])); hm = Image.new("L", (n, n), 60)
    dr = ImageDraw.Draw(canvas); dh = ImageDraw.Draw(hm)
    pal = [C["litter_pine"], C["litter_leaf"], C["litter_leaf"] * 0.8, C["moss"], C["ash"] * 0.9]
    for k in range(900):
        cx_, cy_ = rs.rand(2) * n; ang = rs.rand() * np.pi; L = 14 + rs.rand() * 26; W = 4 + rs.rand() * 8; c = pal[rs.randint(len(pal))] * (0.75 + 0.5 * rs.rand()); hh_ = 90 + int(rs.rand() * 150)
        pts = []
        for t in np.linspace(0, 2 * np.pi, 10, endpoint=False):
            lx = np.cos(t) * L / 2; ly = np.sin(t) * W / 2 * (1 - 0.25 * np.cos(t)); pts.append((lx * np.cos(ang) - ly * np.sin(ang), lx * np.sin(ang) + ly * np.cos(ang)))
        for ox in (-n, 0, n):
            for oy in (-n, 0, n):
                poly = [(cx_ + px + ox, cy_ + py + oy) for px, py in pts]
                dr.polygon(poly, fill=tuple(int(max(0, min(255, v))) for v in c)); dh.polygon(poly, fill=hh_)
                if k % 3 == 0:   # 잎맥
                    dr.line([(cx_ - np.cos(ang) * L / 2 + ox, cy_ - np.sin(ang) * L / 2 + oy), (cx_ + np.cos(ang) * L / 2 + ox, cy_ + np.sin(ang) * L / 2 + oy)], fill=tuple(int(max(0, v * 0.6)) for v in c), width=1)
    for k in range(300):   # 솔잎 가는 줄
        x0, y0 = rs.rand(2) * n; ang = rs.rand() * np.pi; L = 20 + rs.rand() * 24
        for ox in (-n, 0, n):
            for oy in (-n, 0, n):
                dr.line([(x0 + ox, y0 + oy), (x0 + np.cos(ang) * L + ox, y0 + np.sin(ang) * L + oy)], fill=tuple(int(v * 0.9) for v in C["litter_pine"]), width=1)
    h = np.asarray(hm, np.float32) / 255; h = h + 0.05 * pnoise(n, 120, 120, 142)
    base = np.asarray(canvas, np.float32) * (0.85 + 0.3 * fb(n, 5, 5, 143, 3))[..., None]
    out["leaf"] = (base, normal_from_height(h, 4.0))
    return {k: (np.clip(c, 0, 255).astype(np.uint8), np.clip(nm * 255, 0, 255).astype(np.uint8)) for k, (c, nm) in out.items()}

def water_tiles(n=256, dark=False):
    """개울물 4m 타일: 흐름 방향이 세로(남북)로 길게 늘어진 잔물결·반사 줄 + 흩어진 거품 알갱이. RGBA(알파=투명도)와 노멀.
    Unity에서는 uv를 흐름 방향으로 흘리면 흐르는 물이 되고, Blender 정지 장면에서는 줄무늬가 흐름을 암시한다."""
    h = 0.5 * fb(n, 12, 2, 201, 4) + 0.3 * fb(n, 20, 3, 202, 3) + 0.2 * pnoise(n, 36, 6, 203)   # 가로 칸 많고 세로 칸 적음 = 세로(남북)로 길고 부드러운 줄(2026-10-25: 비 내리듯 짧은 줄 → 흐르는 긴 결로)
    h = (h - h.min()) / (h.max() - h.min())
    streak = np.clip((h - 0.55) * 3.2, 0, 1)                           # 반사가 맺히는 가는 줄(물결 마루)
    deep = np.array([0.07, 0.20, 0.27], np.float32); mid = np.array([0.15, 0.36, 0.42], np.float32); sky = np.array([0.70, 0.84, 0.90], np.float32)   # 흙탕 갈색이 비치던 어두운 물 → 맑은 청록
    col = _mixc(np.broadcast_to(deep, (n, n, 3)), np.broadcast_to(mid, (n, n, 3)), np.clip(h * 1.3, 0, 1))
    col = _mixc(col, np.broadcast_to(sky, (n, n, 3)), streak * 0.42)                               # 하늘빛 반사 줄
    d1, edge, v = worley(n, 14, 204, 0.9)
    bub = (np.clip(1 - d1 * 2.6, 0, 1) ** 2.0) * (v > 0.93) * (pnoise(n, 8, 3, 205) > 0.5)        # 드문 거품 알갱이
    col = _mixc(col, np.broadcast_to(np.array([0.92, 0.96, 0.95], np.float32), (n, n, 3)), np.clip(bub * 1.2, 0, 1) * 0.8)
    alpha = np.clip(0.68 + 0.12 * h + 0.15 * streak + 0.3 * bub, 0, 0.95)   # 바닥 흙이 덜 비치게 불투명도 올림
    if dark:   # 큰 강: 더 깊고 어둡고 덜 비침
        col = col * np.array([0.85, 0.92, 1.0], np.float32); alpha = np.clip(alpha + 0.1, 0, 0.95)
    rgba = np.concatenate([col, alpha[..., None]], -1)
    return (np.clip(rgba, 0, 1) * 255).astype(np.uint8), (normal_from_height(h + 0.3 * pnoise(n, 90, 30, 206), 7.0) * 255).astype(np.uint8)
