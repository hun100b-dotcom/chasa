"""하늘·날씨 그림 재료. 실행: python3 sky_weather.py  → assets3d/sky/ 에 PNG 여러 장 + sky_clock.json + 미리보기 sheet.
쓰임: 하루 40분(=게임 24시간, 1게임시 100초) 시계에 맞춰 유니티가 시간 → 하늘색·빛 색을 읽고, 구름·달·별·비·안개 그림을 얹는다.
50° 내려다보는 시점은 지평선이 거의 안 보이므로 하늘의 실제 쓰임은 ①빛·안개·그림자 색(sky_clock.json) ②땅에 지나가는 구름 그림자(cloud_shadow.png) ③화면 가장자리 하늘(sky_gradient) ④밤 달·별(위로 틸트하는 컷신·보스 연출) ⑤비·안개 겹이다.
모든 반복 그림은 이음매가 없다(terrain_detail의 주기 노이즈). 씨앗 고정이라 다시 만들어도 같다."""
import os, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from terrain_detail import pnoise, fb, worley

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets3d", "sky")
os.makedirs(OUT, exist_ok=True)
def hexc(h): h = h.lstrip("#"); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)
def smooth(a, b, x): t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
def save(name, arr, mode=None): Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode).save(os.path.join(OUT, name), optimize=True)

# ───────────────────────── 하루 시계(키프레임) ─────────────────────────
# 시각(게임 시) → 하늘 꼭대기·중간·지평선 색, 해/달 빛 색·세기, 그늘(앰비언트) 색, 안개 색·짙기, 별·달 보임
K = [
 # h   zenith     mid        horizon    light      lux  ambient    fog        fogd  stars moon
 (0.0, "#0B1226", "#121C38", "#1C2A4A", "#8FA8E8", 0.35, "#16213E", "#1A2644", 1.0, 1.0, 1.0),
 (4.0, "#0E1730", "#1E2950", "#3A3F66", "#8FA0D8", 0.30, "#1A2444", "#2A3252", 1.0, 0.8, 0.8),
 (5.5, "#2C3A6B", "#7A6A8A", "#D9946B", "#FFC49A", 0.60, "#3A3F66", "#9A8296", 0.9, 0.3, 0.2),   # 새벽: 보랏빛 → 지평선 살구색
 (7.0, "#5E86B8", "#9DB8CC", "#E8CFA8", "#FFE6C0", 1.05, "#6A7A94", "#B8C4C8", 0.7, 0.0, 0.0),
 (10.0, "#5B8FC4", "#9CC0DA", "#D4E2E8", "#FFF4DC", 1.35, "#7A8BA4", "#C4D2D8", 0.5, 0.0, 0.0),
 (12.5, "#4F86C2", "#92BADA", "#CFE0EA", "#FFFFFF", 1.5, "#8294AC", "#C8D8E0", 0.45, 0.0, 0.0),
 (16.0, "#5683B8", "#A0B8CC", "#E6D6B4", "#FFEBC4", 1.25, "#7C879C", "#CCC8B8", 0.55, 0.0, 0.0),
 (18.0, "#46598E", "#B98E8C", "#E39A62", "#FFB070", 0.85, "#5A5470", "#B89080", 0.8, 0.1, 0.1),   # 저녁놀: 탁한 주황(파혼 주황과 구분되게 낮은 채도)
 (19.5, "#26305C", "#5A4A7A", "#A9606A", "#C88898", 0.5, "#3A3258", "#6A4E66", 1.0, 0.5, 0.6),
 (21.0, "#101A38", "#1C2646", "#33375A", "#8FA6E4", 0.38, "#18223F", "#202A4A", 1.0, 0.95, 1.0),
 (24.0, "#0B1226", "#121C38", "#1C2A4A", "#8FA8E8", 0.35, "#16213E", "#1A2644", 1.0, 1.0, 1.0),
]
def interp(h, i):
    for a, b in zip(K, K[1:]):
        if a[0] <= h <= b[0]:
            t = (h - a[0]) / (b[0] - a[0]); t = t * t * (3 - 2 * t)
            va, vb = a[i], b[i]
            if isinstance(va, str): return hexc(va) * (1 - t) + hexc(vb) * t
            return va * (1 - t) + vb * t
    return hexc(K[-1][i]) if isinstance(K[-1][i], str) else K[-1][i]

def sky_gradient(variant="clear", W=480, H=128):
    """가로 = 하루(0~24시, 1픽셀=3분), 세로 = 높이(위=꼭대기, 아래=지평선). clear/overcast(비)/fog."""
    img = np.zeros((H, W, 3), np.float32)
    for x in range(W):
        h = x / W * 24.0
        z, m, ho = interp(h, 1), interp(h, 2), interp(h, 3)
        y = np.linspace(0, 1, H)[:, None]
        # 위→아래: 꼭대기 → 중간(0.55) → 지평선, 지평선 가까이에서 밝아짐(대기 두께)
        c = np.where(y < 0.55, z + (m - z) * smooth(0, 0.55, y), m + (ho - m) * smooth(0.55, 1.0, y) ** 1.3)
        img[:, x] = c
    if variant != "clear":
        g = img.mean(2, keepdims=True)
        if variant == "overcast": img = (g + (img - g) * 0.35) * 0.82 + np.array([8, 10, 14], np.float32) * 0.5   # 비 오는 날: 채도 낮고 한 단계 어둡고 푸르스름
        else: img = (g + (img - g) * 0.25) * 0.95 + np.array([40, 46, 52], np.float32) * 0.35                  # 안개: 위아래 구분 없이 뿌옇고 밝게
        if variant == "fog": img = img.mean(0, keepdims=True) * 0.5 + img * 0.5
    save(f"sky_gradient_{variant}.png", img)
    return img

# ───────────────────────── 구름 ─────────────────────────
def cloud_tile(kind, n=1024):
    if kind == "cumulus":
        d = fb(n, 5, 5, 301, 6); thr = 0.5; soft = 0.18
    elif kind == "cirrus":
        d = fb(n, 16, 3, 311, 5) * 0.9 + 0.1 * fb(n, 6, 6, 312, 3); thr = 0.52; soft = 0.2
    else:   # storm: 두껍게 깔림
        d = fb(n, 4, 4, 321, 6) * 0.8 + 0.2; thr = 0.34; soft = 0.28
    a = smooth(thr - soft * 0.2, thr + soft, d)
    # 빛: 왼쪽 위에서 비친다고 보고 밀도를 한 칸 옮겨 뺀 값으로 밝기를 낸다(윗면 밝고 아랫면 푸르게 어둡다)
    sh = np.roll(np.roll(d, -10, 0), -10, 1); lit = np.clip(0.55 + (d - sh) * 7.0, 0, 1) * (0.55 + 0.45 * a)
    if kind == "storm": hi, lo = hexc("#7C8494"), hexc("#2E3442")
    else: hi, lo = hexc("#FFFFFF"), hexc("#8EA0BC")
    col = lo[None, None] * (1 - lit[..., None]) + hi[None, None] * lit[..., None]
    rgba = np.concatenate([col, (a * (0.95 if kind != "cirrus" else 0.6))[..., None] * 255], -1); save(f"cloud_{kind}.png", rgba, "RGBA")
    return d, a

def cloud_shadow(a, n=512):
    """땅에 지나가는 구름 그림자: 흑백(밝음=그림자 없음), 200m마다 반복. 구름 알파를 줄여 쓴다."""
    im = Image.fromarray((a * 255).astype(np.uint8)).resize((n, n), Image.LANCZOS).filter(ImageFilter.GaussianBlur(3)); v = np.asarray(im, np.float32) / 255
    save("cloud_shadow.png", (1 - 0.55 * v) * 255)

# ───────────────────────── 달·해·별 ─────────────────────────
def moon(phase, n=256):
    """phase: 초승(crescent)/상현(first_quarter)/보름(full)/하현(last_quarter). 구체 조명을 해 방향 각도로 돌려 어두운 쪽은 희미하게(지구빛)."""
    ang = {"crescent": math.radians(140), "first_quarter": math.radians(90), "full": 0.0, "last_quarter": math.radians(-90)}[phase]
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32); cx = cy = n / 2; R = n * 0.36
    u = (xx - cx) / R; v = -(yy - cy) / R; r2 = u * u + v * v; inside = r2 <= 1
    w = np.sqrt(np.clip(1 - r2, 0, 1)); nx, ny, nz = u, v, w
    sx, sz = math.sin(ang), math.cos(ang); lit = np.clip(nx * sx + nz * sz, 0, 1)
    if phase == "last_quarter": lit = np.clip(nx * -1 * 1.0, 0, 1) if False else np.clip(-nx, 0, 1)
    if phase == "first_quarter": lit = np.clip(nx, 0, 1)
    lit = smooth(0.0, 0.18, lit) if phase != "full" else np.ones_like(lit)
    # 바다 무늬와 분화구(고정 씨앗, 모든 위상이 같은 달면)
    mar = fb(n, 4, 4, 401, 4); maria = smooth(0.46, 0.6, mar) * 0.32
    d1, _, _ = worley(n, 18, 402, 0.9); crater = np.clip(1 - d1 * 3.4, 0, 1) ** 2 * 0.1 * (fb(n, 6, 6, 403, 2) > 0.5)
    albedo = np.clip(0.93 - maria - crater + (fb(n, 40, 40, 404, 2) - 0.5) * 0.08, 0, 1)
    col0 = hexc("#E9E4D4") * albedo[..., None]; shade = (0.13 + 0.87 * lit)[..., None]
    col = col0 * shade * (1 + 0.1 * (nz[..., None] * 0))
    col = col * np.array([1.0, 1.0, 1.04], np.float32)
    edge = smooth(1.0, 0.97, np.sqrt(r2))
    rgba = np.concatenate([col, (inside * edge)[..., None] * 255], -1); save(f"moon_{phase}.png", rgba, "RGBA")
    return rgba

def glow(name, color, n=256, power=2.2, strength=0.9):
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32); r = np.hypot(xx - n / 2, yy - n / 2) / (n / 2); a = np.clip(1 - r, 0, 1) ** power * strength
    col = np.ones((n, n, 3), np.float32) * hexc(color)
    save(name, np.concatenate([col, a[..., None] * 255], -1), "RGBA")

def sun_disc(n=256):
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32); r = np.hypot(xx - n / 2, yy - n / 2) / (n / 2)
    core = smooth(0.2, 0.17, r); halo = np.clip(1 - r, 0, 1) ** 2.6 * 0.6
    a = np.clip(core + halo, 0, 1); col = np.ones((n, n, 3), np.float32) * hexc("#FFF2D0"); col = col * (0.85 + 0.15 * core[..., None]) + hexc("#FFC080") * (1 - core[..., None]) * 0.2
    save("sun_disc.png", np.concatenate([col, a[..., None] * 255], -1), "RGBA")

def stars(n=1024):
    rs = np.random.RandomState(501); img = np.zeros((n, n, 4), np.float32)
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    for k in range(1500):   # 작은 별
        x, y = rs.rand(2) * n; b = 0.25 + rs.rand() ** 3 * 0.75; c = hexc(["#FFFFFF", "#CFE0FF", "#FFE9C8"][rs.randint(3)]); s = 0.6 + rs.rand() * 0.6
        x0, y0 = int(x) - 3, int(y) - 3
        for dy in range(7):
            for dx in range(7):
                px, py = (x0 + dx) % n, (y0 + dy) % n; a = b * math.exp(-(((x0 + dx) - x) ** 2 + ((y0 + dy) - y) ** 2) / (2 * s * s))
                if a > 0.02:
                    img[py, px, :3] = np.maximum(img[py, px, :3], c); img[py, px, 3] = max(img[py, px, 3], a * 255)
    # 은하수 띠: 대각선으로 흐르는 옅은 안개
    band = np.exp(-(((xx - yy * 0.6 + 200) % n - n / 2) / (n * 0.09)) ** 2) * fb(n, 6, 6, 502, 4); band = smooth(0.35, 0.9, band) * 0.22
    img[..., :3] = np.where(band[..., None] > img[..., 3:4] / 255, hexc("#A9B8E8")[None, None], img[..., :3]); img[..., 3] = np.maximum(img[..., 3], band * 255)
    save("stars.png", img, "RGBA")
    tw = fb(n, 16, 16, 503, 3); save("stars_twinkle.png", tw * 255)

# ───────────────────────── 비·안개 ─────────────────────────
def rain_layer(name, n, count, length, width, slant, alpha, seed):
    rs = np.random.RandomState(seed); im = Image.new("RGBA", (n, n), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    for _ in range(count):
        x, y = rs.rand(2) * n; L = length * (0.7 + 0.6 * rs.rand()); a = int(255 * alpha * (0.5 + 0.5 * rs.rand()))
        for ox in (-n, 0, n):
            for oy in (-n, 0, n):
                dr.line([(x + ox, y + oy), (x + slant * L + ox, y + L + oy)], fill=(214, 226, 240, a), width=width)
    im.save(os.path.join(OUT, name), optimize=True)

def splash_sheet(frames=8, fs=96):
    """비 물방울이 땅에 떨어지는 파문: 가로 8장(작은 고리가 퍼지며 사라짐 + 튀는 물방울 점). 한 장 96px."""
    im = Image.new("RGBA", (fs * frames, fs), (0, 0, 0, 0))
    for f in range(frames):
        t = f / (frames - 1); fr = Image.new("RGBA", (fs * 4, fs * 4), (0, 0, 0, 0)); d = ImageDraw.Draw(fr); c = fs * 2; r = fs * 4 * (0.05 + 0.36 * t) * 0.5 * 2
        a = int(230 * (1 - t) ** 1.4)
        d.ellipse([c - r, c - r * 0.55, c + r, c + r * 0.55], outline=(225, 235, 245, a), width=max(3, int(10 * (1 - t) + 3)))
        if t < 0.55:
            for k in range(6):
                th = k / 6 * math.tau + 0.4; rr = r * 0.8 + fs * 0.1 * t * 4; hh = fs * 1.2 * math.sin(math.pi * t / 0.55) * 0.5
                d.ellipse([c + math.cos(th) * rr - 4, c + math.sin(th) * rr * 0.55 - hh - 4, c + math.cos(th) * rr + 4, c + math.sin(th) * rr * 0.55 - hh + 4], fill=(235, 242, 250, int(a * 0.9)))
        fr = fr.filter(ImageFilter.GaussianBlur(1.2)).resize((fs, fs), Image.LANCZOS); im.paste(fr, (f * fs, 0))
    im.save(os.path.join(OUT, "rain_splash_sheet.png"), optimize=True)

def fog_tiles():
    n = 512; d = fb(n, 4, 4, 601, 6); d = smooth(0.25, 0.8, d); save("fog_noise.png", d * 255)    # 안개 흐름: 흑백 반복(밝음=짙음), 두 겹을 서로 다른 속도로 흘림
    S = 256; im = Image.new("RGBA", (S * 4, S), (0, 0, 0, 0))
    for k in range(4):   # 안개 덩이 스프라이트 4종(바닥에 깔린 낮은 덩이, 가장자리 부드럽게)
        yy, xx = np.mgrid[0:S, 0:S].astype(np.float32); r = np.hypot((xx - S / 2) / (S / 2), (yy - S / 2) / (S / 2.6)); nz = fb(S, 4, 3, 610 + k, 4)
        a = np.clip(1 - r, 0, 1) ** 1.3 * (0.4 + 0.9 * nz); a = np.clip(a, 0, 1) * 0.8
        col = np.ones((S, S, 3), np.float32) * hexc("#C8D2D8") * (0.9 + 0.1 * nz[..., None])
        im.paste(Image.fromarray(np.concatenate([col, a[..., None] * 255], -1).astype(np.uint8), "RGBA"), (k * S, 0))
    im.save(os.path.join(OUT, "mist_puffs.png"), optimize=True)

# ───────────────────────── 시계·날씨 표 ─────────────────────────
def clock_json():
    keys = []
    for k in K[:-1]:
        keys.append({"hour": k[0], "sky_zenith": k[1], "sky_mid": k[2], "sky_horizon": k[3], "light_color": k[4], "light_intensity": k[5], "ambient_color": k[6], "fog_color": k[7], "fog_density_mult": k[8], "star_alpha": k[9], "moon_alpha": k[10]})
    j = {"note": "하루 40분(2400초) = 게임 24시간. 1게임시 = 100초. hour는 게임 시(0~24). 키프레임 사이는 부드럽게(smoothstep) 보간. 0시=24시로 이어짐.",
         "day_seconds": 2400, "seconds_per_game_hour": 100,
         "sky_gradient": {"clear": "sky_gradient_clear.png", "overcast": "sky_gradient_overcast.png", "fog": "sky_gradient_fog.png", "layout": "가로=하루 0~24시(480px, 1px=3분), 세로=위(꼭대기)→아래(지평선) 128px"},
         "sun": {"rise_hour": 5.5, "set_hour": 18.5, "disc": "sun_disc.png", "note": "5.5시 지평선에서 떠 12.5시 가장 높고 18.5시 진다. 방위는 코드 자유(그림자는 동서로 길게)"},
         "moon": {"phases": ["moon_crescent.png", "moon_first_quarter.png", "moon_full.png", "moon_last_quarter.png"], "halo": "moon_halo.png",
                  "schedule": "게임 하루마다 한 단계씩(하루 40분 → 4일 160분이 한 달 주기): 초승 → 상현 → 보름 → 하현. 보름밤에 빛 세기 ×1.25, 초승밤 ×0.8 권장(값은 코드가 조절)", "visible_hours": "19.5~5.5, 보름은 18.5~6.0"},
         "stars": {"texture": "stars.png", "twinkle": "stars_twinkle.png", "tile": "1024² 반복", "visible": "star_alpha 키프레임, 구름 많으면 ×0.3"},
         "clouds": {"cumulus": "cloud_cumulus.png", "cirrus": "cloud_cirrus.png", "storm": "cloud_storm.png", "shadow": "cloud_shadow.png", "tile_m": 200, "wind_mps": [1.2, 0.4],
                    "note": "구름 그림은 1024² RGBA 반복. 그림자(cloud_shadow, 흑백 512² 반복)를 땅 빛에 곱해 천천히 흘리면 구름이 지나가는 그림자가 된다"},
         "weather_presets": {
             "clear": {"sky": "clear", "cloud": "cumulus", "cloud_cover": 0.25, "light_mult": 1.0, "fog_mult": 1.0, "rain": 0.0, "ambient_tint": "#FFFFFF"},
             "cloudy": {"sky": "clear", "cloud": "cumulus", "cloud_cover": 0.7, "light_mult": 0.8, "fog_mult": 1.2, "rain": 0.0, "ambient_tint": "#E6ECF4"},
             "rain": {"sky": "overcast", "cloud": "storm", "cloud_cover": 0.95, "light_mult": 0.55, "fog_mult": 1.6, "rain": 1.0, "ground_wet": 1.0, "ambient_tint": "#C8D2E0", "rain_layers": [{"texture": "rain_streaks_far.png", "scroll_uv_per_s": [0.05, -1.3], "tile_m": 40}, {"texture": "rain_streaks_near.png", "scroll_uv_per_s": [0.12, -2.4], "tile_m": 12}], "splash": "rain_splash_sheet.png (8프레임, 초당 14프레임, 땅 위 무작위 점)"},
             "fog": {"sky": "fog", "cloud": "cirrus", "cloud_cover": 0.4, "light_mult": 0.7, "fog_mult": 3.0, "rain": 0.0, "ambient_tint": "#D8E0E4", "fog_layers": [{"texture": "fog_noise.png", "scroll_uv_per_s": [0.01, 0.004], "tile_m": 90}, {"texture": "fog_noise.png", "scroll_uv_per_s": [-0.006, 0.007], "tile_m": 55}], "puffs": "mist_puffs.png (4종, 바닥 가까이 띄움)"},
             "plague_mist": {"sky": "fog", "cloud": "cirrus", "cloud_cover": 0.5, "light_mult": 0.6, "fog_mult": 2.5, "rain": 0.0, "ambient_tint": "#B8C8BC", "fog_color_override": "#46564F", "note": "검은여울 구역 전용. 안개 색은 layouts/field_5x5_zones.json fog와 같게"}},
         "keyframes": keys}
    json.dump(j, open(os.path.join(OUT, "sky_clock.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    for v in ("clear", "overcast", "fog"): sky_gradient(v)
    d, a = cloud_tile("cumulus"); cloud_tile("cirrus"); cloud_tile("storm"); cloud_shadow(a)
    for ph in ("crescent", "first_quarter", "full", "last_quarter"): moon(ph)
    glow("moon_halo.png", "#B8CBF2", 256, 2.4, 0.55); sun_disc(); stars()
    rain_layer("rain_streaks_far.png", 512, 700, 26, 1, 0.07, 0.35, 701); rain_layer("rain_streaks_near.png", 512, 150, 78, 2, 0.07, 0.6, 702); splash_sheet(); fog_tiles(); clock_json()
    print("완료", sorted(os.listdir(OUT)))
