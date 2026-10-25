"""화면 분위기(색보정표 LUT·블룸·비네트·천도 시야 축소) 값과 미리보기를 만든다.
기준: 아트 디렉션 '고딕 호러 + 단청 원색'.
  - 어둠은 검정이 아니라 남청(#0F1729·#16213E). 화면 80%는 낮은 채도.
  - 색은 '의미'에만: 붉은색(차사·위험), 금(단청·장비), 청록(천도), 보라(원념·기억)는 살리고 풀빛·흙빛은 죽인다.
출력(assets3d/grading/):
  lut_<시간>_<날씨>.png 20장 + lut_neutral.png + lut_tendo.png  (Unity 32³ 가로 띠, 1024×32)
  grading_params.json (코드팀이 읽는 값 전부)
  vision_noise.png / vision_pattern.png (천도 시야 축소 셰이더용)
  /previews/grading_*.jpg (전후 비교)
사용: python3 grading.py [luts|preview|vision|all]
LUT 규칙(Unity '색 조회 표' 가로 띠): 칸 32개가 가로로 이어지고 칸 번호 = 파랑값, 칸 안 가로 = 빨강, 세로(그림 위가 큰 값) = 초록."""
import os, sys, json, math
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
A3 = os.path.join(HERE, "..", "..", "assets3d")
OUT = os.path.join(A3, "grading"); PRE = os.path.join(A3, "previews")
os.makedirs(OUT, exist_ok=True)
N = 32

def hx(h):
    h = h.lstrip("#"); return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)

# ── 1) 시간대 4종 기본값(맑은 날) ─────────────────────────────────────────────
# exposure=노출(단계) / contrast=대비 / sat=전체 채도 / shadow=그늘에 섞는 색(+양) / high=밝은 곳에 섞는 색
# lift=검정을 띄우는 양(남청으로) / accent=단청 원색(붉·금·청록·파랑) 채도를 더 올리는 정도 / mute=풀빛·황록을 죽이는 정도
TIMES = {
    "day":  dict(label="낮",     hours=[7.0, 16.0],  exposure=-0.04, contrast=1.14, sat=0.78, shadow=(0.05, 0.09, 0.18), shadow_amt=0.80, high=(0.020, 0.010, -0.020), mid=(-0.010, 0.0, 0.020), lift=0.025, accent=0.42, mute=0.65),
    "dusk": dict(label="저녁놀", hours=[16.0, 19.5], exposure=-0.10, contrast=1.18, sat=0.88, shadow=(0.10, 0.04, 0.18), shadow_amt=0.85, high=(0.050, 0.012, -0.030), mid=(0.008, -0.015, -0.005), lift=0.030, accent=0.45, mute=0.65),
    "night": dict(label="밤",    hours=[19.5, 28.5], exposure=-0.06, contrast=1.24, sat=0.74, shadow=(0.04, 0.09, 0.22), shadow_amt=1.00, high=(-0.010, 0.015, 0.045), mid=(-0.050, -0.005, 0.090), lift=0.035, accent=0.60, mute=0.70),
    "dawn": dict(label="새벽",   hours=[4.5, 7.0],   exposure=0.02, contrast=1.10, sat=0.68, shadow=(0.08, 0.07, 0.20), shadow_amt=0.90, high=(0.050, 0.005, 0.000), mid=(-0.010, -0.005, 0.055), lift=0.080, accent=0.40, mute=0.60),
}
# ── 2) 날씨 5종: 시간대 값 위에 곱하거나 더한다 ──────────────────────────────
WEATHER = {
    "clear":  dict(label="맑음",  exposure=0.00, contrast=1.00, sat=1.00, lift=0.000, shadow=(0, 0, 0), accent=0.00, mute=0.00, grey=(0, 0, 0), mid=(0, 0, 0)),
    "cloudy": dict(label="흐림",  exposure=-0.12, contrast=0.94, sat=0.86, lift=0.010, shadow=(0.01, 0.02, 0.03), accent=0.00, mute=0.05, grey=(-0.01, 0.0, 0.015), mid=(-0.005, 0.0, 0.015)),
    "rain":   dict(label="비",    exposure=-0.28, contrast=0.96, sat=0.72, lift=0.035, shadow=(0.00, 0.04, 0.06), accent=-0.05, mute=0.10, grey=(-0.02, 0.005, 0.025), mid=(-0.02, 0.005, 0.03)),
    "fog":    dict(label="안개",  exposure=-0.10, contrast=0.80, sat=0.62, lift=0.085, shadow=(0.03, 0.05, 0.06), accent=-0.10, mute=0.10, grey=(0.00, 0.01, 0.02), mid=(0.0, 0.01, 0.03)),
    "plague": dict(label="역병",  exposure=-0.20, contrast=1.04, sat=0.68, lift=0.050, shadow=(-0.01, 0.07, 0.04), accent=0.15, mute=-0.15, grey=(-0.02, 0.035, 0.01), mid=(-0.03, 0.04, 0.0)),
}

# 단청 원색 띠: (색상각 도, 폭 도). 붉은 / 금 / 청록 / 파랑 — 이 근처 색만 채도를 살린다
ACCENT_BANDS = [(8, 24), (44, 20), (165, 24), (215, 22)]

def rgb2hsv(c):
    mx = c.max(-1); mn = c.min(-1); d = mx - mn + 1e-9
    r, g, b = c[..., 0], c[..., 1], c[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    return h % 360, np.where(mx > 1e-6, (mx - mn) / (mx + 1e-9), 0), mx

def hsv2rgb(h, s, v):
    c = v * s; hp = (h % 360) / 60; x = c * (1 - np.abs(hp % 2 - 1)); z = np.zeros_like(h)
    conds = [(hp < 1, (c, x, z)), (hp < 2, (x, c, z)), (hp < 3, (z, c, x)), (hp < 4, (z, x, c)), (hp < 5, (x, z, c)), (hp >= 5, (c, z, x))]
    r = np.select([k for k, _ in conds], [t[0] for _, t in conds]); g = np.select([k for k, _ in conds], [t[1] for _, t in conds]); b = np.select([k for k, _ in conds], [t[2] for _, t in conds])
    m = (v - c)[..., None]
    return np.stack([r, g, b], -1) + m

def band(h, c0, w):
    d = np.abs((h - c0 + 180) % 360 - 180); return np.clip(1 - d / w, 0, 1) ** 0.8

def combine(time, weather):
    """시간대 값 + 날씨 값을 한 벌로 합친다(미리보기·LUT·JSON이 같은 식을 쓴다)."""
    t, w = TIMES[time], WEATHER[weather]
    return dict(exposure=t["exposure"] + w["exposure"], contrast=t["contrast"] * w["contrast"], sat=t["sat"] * w["sat"], lift=t["lift"] + w["lift"],
                shadow=tuple(a + b for a, b in zip(t["shadow"], w["shadow"])), shadow_amt=t["shadow_amt"], high=tuple(a + b for a, b in zip(t["high"], w["grey"])), mid=tuple(a + b for a, b in zip(t["mid"], w["mid"])),
                accent=t["accent"] + w["accent"], mute=t["mute"] + w["mute"])

def grade(c, P):
    """c: (...,3) 0~1 sRGB. 순서: 노출 → 그늘/밝은곳 색 → 색상별 채도(단청 원색 살리기) → 대비(S자) → 검정 띄우기."""
    c = np.clip(c * (2 ** P["exposure"]), 0, 1)
    luma = (c * np.array([0.2126, 0.7152, 0.0722], np.float32)).sum(-1, keepdims=True)
    sm = (1 - luma) ** 2.2; hm = luma ** 2.0
    c = c + np.array(P["shadow"], np.float32) * sm * P["shadow_amt"] + np.array(P["high"], np.float32) * hm + np.array(P.get("mid", (0, 0, 0)), np.float32) * (4 * luma * (1 - luma))
    c = np.clip(c, 0, 1)
    h, s, v = rgb2hsv(c)
    acc = np.zeros_like(h)
    for c0, w in ACCENT_BANDS: acc = np.maximum(acc, band(h, c0, w))
    green = band(h, 100, 45)                               # 풀·이끼 황록 — 죽인다
    mult = P["sat"] * (1 + P["accent"] * acc) * (1 - np.clip(P["mute"], -0.5, 0.9) * green * (1 - acc))
    s = np.clip(s * mult, 0, 1)
    c = hsv2rgb(h, s, v)
    piv = 0.46; x = np.clip(c, 0, 1)
    k = P["contrast"]; c = piv + (x - piv) * k
    sc = 0.5 + 0.5 * np.tanh((c - 0.5) * 2.2) / np.tanh(1.1)   # 끝을 부드럽게 눌러 하얗게 날아가거나 먹통이 되지 않게
    c = np.clip(0.5 * c + 0.5 * sc if k > 1 else c, 0, 1)
    L = P["lift"] * 3.0                                     # 검정을 남청(#16213E)으로 띄운다(순검정 금지). 어두운 곳에만 효과가 가도록 (1-밝기) 가중
    lm = (1 - np.clip(c.mean(-1, keepdims=True), 0, 1)) ** 2
    return np.clip(c * (1 - L * lm) + hx("#16213E") * L * lm, 0, 1)

# 천도 중 색보정(시야 축소와 함께 0→0.6 으로 섞는다): 채도 확 낮추고 청록 하이라이트
TENDO = dict(exposure=-0.12, contrast=1.18, sat=0.45, lift=0.04, shadow=(0.02, 0.07, 0.12), shadow_amt=0.9, high=(-0.02, 0.05, 0.035), accent=0.9, mute=0.7)

def neutral():
    r = np.arange(N) / (N - 1)
    g = np.arange(N) / (N - 1)
    img = np.zeros((N, N * N, 3), np.float32)
    for b in range(N):
        R, G = np.meshgrid(r, g[::-1])               # 그림 위쪽이 초록 큰 값
        img[:, b * N:(b + 1) * N, 0] = R; img[:, b * N:(b + 1) * N, 1] = G; img[:, b * N:(b + 1) * N, 2] = b / (N - 1)
    return img

def save_lut(P, name):
    img = neutral(); out = grade(img, P)
    Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(OUT, name))

# ── 3) 블룸·비네트 ─────────────────────────────────────────────────────────────
# URP Bloom: threshold(문턱) intensity(세기) scatter(퍼짐 0~1) tint(색)  /  Vignette: intensity smoothness rounded color
BLOOM = {"day": dict(threshold=1.00, intensity=0.22, scatter=0.55, tint="#FFF4DC"), "dusk": dict(threshold=0.90, intensity=0.50, scatter=0.65, tint="#FFB070"),
         "night": dict(threshold=0.80, intensity=0.95, scatter=0.72, tint="#9FDCFF"), "dawn": dict(threshold=0.90, intensity=0.45, scatter=0.70, tint="#FFC49A")}
BLOOM_W = {"clear": (1.0, 0.0, 0.0), "cloudy": (0.85, 0.0, 0.03), "rain": (0.8, 0.05, 0.05), "fog": (1.5, -0.10, 0.12), "plague": (1.2, -0.05, 0.05)}   # (세기 곱, 문턱 더함, 퍼짐 더함)
BLOOM_TINT_W = {"plague": "#8FE0A8", "fog": "#D8E0E4"}
VIG = {"day": dict(intensity=0.20, smoothness=0.55), "dusk": dict(intensity=0.28, smoothness=0.60), "night": dict(intensity=0.36, smoothness=0.65), "dawn": dict(intensity=0.28, smoothness=0.60)}
VIG_W = {"clear": 0.0, "cloudy": 0.02, "rain": 0.04, "fog": 0.06, "plague": 0.10}
VIG_COLOR = {"clear": "#0F1729", "cloudy": "#10192B", "rain": "#0D1826", "fog": "#16202F", "plague": "#0A1511"}
VIG_MAX = 0.45    # 가장자리 적이 안 보이면 안 된다: 천도 시야 축소 말고는 이 값을 넘기지 않는다

def bloom_vig(time, weather):
    b = dict(BLOOM[time]); k, dt, ds = BLOOM_W[weather]
    b["intensity"] = round(b["intensity"] * k, 3); b["threshold"] = round(b["threshold"] + dt, 3); b["scatter"] = round(min(0.95, b["scatter"] + ds), 3)
    if weather in BLOOM_TINT_W: b["tint"] = BLOOM_TINT_W[weather]
    v = dict(VIG[time]); v["intensity"] = round(min(VIG_MAX, v["intensity"] + VIG_W[weather]), 3); v["color"] = VIG_COLOR[weather]; v["rounded"] = False
    return b, v

def build_luts():
    params = {}
    for t in TIMES:
        for w in WEATHER:
            P = combine(t, w); name = f"lut_{t}_{w}.png"; save_lut(P, name)
            b, v = bloom_vig(t, w)
            params[f"{t}_{w}"] = dict(lut=name, label=f"{TIMES[t]['label']}·{WEATHER[w]['label']}", grade={k: (list(x) if isinstance(x, tuple) else round(x, 3)) for k, x in P.items()}, bloom=b, vignette=v)
    Image.fromarray((neutral() * 255 + 0.5).astype(np.uint8)).save(os.path.join(OUT, "lut_neutral.png"))
    save_lut(TENDO, "lut_tendo.png")
    return params

def build_json(params):
    J = {
        "_설명": "화면 분위기 값(아트). 색보정표(LUT) 20장 = 시간대 4 × 날씨 5. 코드는 지금 시각의 LUT 둘을 골라 섞고(아래 hour_map), 날씨 LUT는 날씨 바뀔 때 1.5초 교차. 블룸·비네트는 같은 키의 값을 보간. 확정은 Unity 실제 화면에서 튜닝.",
        "lut_format": {"size": 32, "file": "1024x32 가로 띠", "unity": "Color Lookup(Texture=띠, Contribution=1.0). 가져오기: sRGB 끔, 압축 없음, Mip 끔, Wrap Clamp, Filter Bilinear", "order": "칸=파랑, 칸 안 가로=빨강, 위쪽=초록 큰 값"},
        "hour_map": {"_설명": "게임 시(0~24)별 기본 시간대. 경계 앞뒤 0.5시간(약 50초)은 두 LUT를 smoothstep 으로 섞는다", "dawn": [4.5, 7.0], "day": [7.0, 16.0], "dusk": [16.0, 19.5], "night": [19.5, 28.5], "crossfade_hours": 0.5,
                     "note": "sky_clock.json 키프레임과 같은 시각 기준. 밤은 19.5~다음날 4.5시"},
        "weather_blend_s": 1.5, "weather_lut_keys": {"Clear": "clear", "Cloudy": "cloudy", "Rain": "rain", "Fog": "fog", "Plague": "plague"},
        "vignette_max_except_tendo": VIG_MAX,
        "presets": params,
        "tendo": {
            "lut": "lut_tendo.png", "lut_contribution": [0.0, 0.6], "lut_enter_s": 0.25, "lut_exit_s": 0.15,
            "radius": {"normal": "끔(셰이더 건너뜀, 안 켜면 값 1.25 이상)", "casting": 0.6, "min_on_small_screen": 0.55, "enter_s": 0.25, "exit_s": 0.15, "enter_ease": "easeOutCubic(빠르게 조이고 끝에서 천천히)", "exit_ease": "easeInQuad(천천히 열렸다가 빠르게)", "unit": "화면 대각선의 절반(모서리까지)=1.0. 0.6이면 16:9 화면에서 위아래는 거의 다 보이고 좌우 가장자리와 모서리가 먹힌다"},
            "edge": {"color": "#0F1729", "alpha_outer": 0.94, "alpha_inner": 0.0, "width_of_radius": 0.12, "noise": "vision_noise.png", "noise_amp": 0.07, "noise_scroll_uv_per_s": [0.012, -0.008], "note": "부드러운 비네트 대신 먹이 번지는 가장자리. 안쪽은 투명→바깥 불투명으로 smoothstep"},
            "pattern": {"texture": "vision_pattern.png", "opacity": 0.14, "opacity_boss": 0.24, "tint": "#D4A94E", "extra_ring_boss": True, "note": "가장자리 띠에 단청 문양(연화·마름모)이 은은히 비침. 보스 천도는 한 겹 더 켜지고 더 진하다"},
            "center_glow": {"color": "#5FE3C0", "radius_m_caster": 2.4, "radius_m_target": 1.6, "intensity": 0.55, "note": "진행도는 글로우 크기가 아니라 대상 혼 윤곽이 선명해지는 정도로. 청록 글로우는 두 곳(차사·대상 혼)만"},
            "danger_pulse": {"color": "#E85C41", "hz": 2.5, "max_hz": 3.0, "alpha": [0.15, 0.55], "width_deg": 28, "note": "시야 밖에서 다가오는 적의 방향만 가장자리에 붉은 호로 맥박. 모습은 안 보인다. 3Hz 이하(광과민 안전)"},
            "success_flash": {"color": "#C9B0FF", "border_px": 18, "duration_s": 0.3, "note": "천도 성공 순간 보라 테두리. 파혼에는 없음(이야기 없음을 색으로 대비)"},
            "bloom_during": {"intensity_mult": 1.25, "tint": "#5FE3C0"},
            "vignette_during": "기본 비네트는 끄고(0) 위 가장자리 셰이더로 대체. 둘이 겹치면 가장자리가 검게 죽는다",
        },
        "forbidden": ["순검정(#000) 가장자리 — 항상 남청 #0F1729", "주황 계열 틴트를 화면 전체에 — 주황(#E8683A)은 파혼 전용 색", "비네트 0.45 초과(천도 제외)", "블룸이 UI를 번지게 하지 말 것: UI는 후처리 뒤 오버레이 카메라/Overlay Canvas"],
    }
    json.dump(J, open(os.path.join(OUT, "grading_params.json"), "w"), ensure_ascii=False, indent=1)
    return J

# ── 4) 미리보기: 블룸·비네트를 합쳐 전후 비교 ─────────────────────────────────
def post(img, time, weather, tendo=False):
    """미리보기용 후처리(Unity와 같은 식은 아님 — 느낌 비교용). 8비트 사진이라 문턱은 0.8배로 낮춰 쓴다."""
    c = np.asarray(img.convert("RGB")).astype(np.float32) / 255
    c = grade(c, combine(time, weather)); b, v = bloom_vig(time, weather)
    luma = (c * np.array([0.2126, 0.7152, 0.0722], np.float32)).sum(-1)
    thr = 0.80 + (b["threshold"] - 0.9) * 0.4      # 8비트 사진에는 HDR 문턱을 그대로 못 쓰므로 0.7~0.9 범위로 옮겨 쓴다
    m = np.clip((luma - thr) / 0.2, 0, 1)[..., None] * c
    mi = Image.fromarray((m * 255).astype(np.uint8)); w = c.shape[1]
    acc = np.zeros_like(c)
    for rad, wt in ((w * 0.006, 0.5), (w * 0.016, 0.3), (w * 0.04, 0.2 + b["scatter"] * 0.3)):
        acc += np.asarray(mi.filter(ImageFilter.GaussianBlur(rad))).astype(np.float32) / 255 * wt
    c = np.clip(c + acc * b["intensity"] * (hx(b["tint"]) * 0.5 + 0.1), 0, 1)
    h, ww, _ = c.shape; ys = np.linspace(-1, 1, h)[:, None]; xs = np.linspace(-1, 1, ww)[None, :] * (ww / h)
    d = np.sqrt(xs ** 2 + ys ** 2) / math.sqrt((ww / h) ** 2 + 1)
    vg = np.clip((d - (1 - v["smoothness"]) * 0.6) / (0.55 * v["smoothness"] + 0.2), 0, 1) ** 1.6 * v["intensity"] * 1.8
    c = c * (1 - vg[..., None]) + hx(v["color"]) * vg[..., None]
    return Image.fromarray((np.clip(c, 0, 1) * 255 + 0.5).astype(np.uint8))

# ── 5) 천도 시야 축소: 셰이더용 질감 + 미리보기 ───────────────────────────────
def build_vision_textures():
    rng = np.random.RandomState(7)
    # 먹 번짐 잡음: 큰 얼룩 + 중간 얼룩 + 잔 번짐을 겹침(가로세로 이어 붙어도 이음매 없게 FFT 필터)
    def tile_noise(size, cut):
        f = np.fft.fft2(rng.randn(size, size)); fx = np.fft.fftfreq(size)[:, None]; fy = np.fft.fftfreq(size)[None, :]
        k = np.sqrt(fx ** 2 + fy ** 2) + 1e-6; f = f / (k ** cut); r = np.real(np.fft.ifft2(f)); r = (r - r.min()) / (r.max() - r.min()); return r
    n = 0.55 * tile_noise(512, 1.6) + 0.3 * tile_noise(512, 1.1) + 0.15 * tile_noise(512, 0.6)
    n = (n - n.min()) / (n.max() - n.min())
    Image.fromarray((n * 255).astype(np.uint8)).save(os.path.join(OUT, "vision_noise.png"))
    # 단청 문양 띠: 가로 1024(=한 바퀴, 가로 반복) × 세로 96. 위=안쪽, 아래=가장자리. 연화 마름모 줄 + 점 줄 + 두 겹 선(금·적·청록)
    W, H = 1024, 96; im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    gold, red, teal = (212, 169, 78, 255), (232, 92, 65, 255), (95, 227, 192, 255)
    d.rectangle([0, 70, W, 73], fill=gold); d.rectangle([0, 80, W, 82], fill=red); d.rectangle([0, 88, W, 90], fill=teal)
    step = 64
    for i in range(W // step):
        cx = i * step + step // 2
        d.polygon([(cx, 12), (cx + 22, 38), (cx, 64), (cx - 22, 38)], outline=gold, width=3)       # 큰 마름모
        d.polygon([(cx, 26), (cx + 10, 38), (cx, 50), (cx - 10, 38)], fill=red)                        # 속 마름모
        d.ellipse([cx - 4 + step // 2, 34, cx + 4 + step // 2, 42], fill=teal)                          # 사이 점
        for a in range(8):                                                                              # 연꽃잎 8장(작은 꽃)
            ang = a * math.pi / 4; px, py = cx + math.cos(ang) * 8, 38 + math.sin(ang) * 8; d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=gold)
    im.save(os.path.join(OUT, "vision_pattern.png"))
    return n, im

def shrink_frame(base, radius, boss=False, noise=None, pat=None, pulse_deg=None, flash=False):
    """천도 시야 축소 한 프레임(미리보기): 반경·먹 번짐 가장자리·단청 문양·붉은 맥박·성공 테두리."""
    c = np.asarray(base.convert("RGB")).astype(np.float32) / 255; h, w, _ = c.shape
    cen = (w * 0.5, h * 0.5); R = math.hypot(w, h) * 0.5 * (radius if radius else 9.0)     # 단위: 화면 대각선의 절반(=모서리까지) 1.0. None 이면 축소 없음
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32); dx, dy = xs - cen[0], ys - cen[1]; d = np.sqrt(dx ** 2 + dy ** 2) / R
    nz = np.asarray(noise.resize((w, h))).astype(np.float32) / 255 if noise is not None else 0.5
    wd = 0.12; dd = d + (nz - 0.5) * 0.14
    a = np.clip((dd - (1 - wd)) / (wd * 2), 0, 1); a = a * a * (3 - 2 * a) * 0.94
    # 채도 낮춤 + 청록 하이라이트(천도 LUT)
    c = grade(c, TENDO) * (1 - np.clip(1 - d, 0, 1)[..., None] * 0) ; c = c * (1 - 0.0)
    ink = hx("#0F1729"); c = c * (1 - a[..., None]) + ink * a[..., None]
    if pat is not None:       # 가장자리 문양: 각도→가로, 안쪽 거리→세로
        ang = (np.arctan2(dy, dx) / (2 * math.pi) + 0.5) % 1.0; pv = np.clip((dd - (1 - wd * 1.8)) / (wd * 1.8), 0, 1)
        p = np.asarray(pat.convert("RGBA")).astype(np.float32) / 255; ph, pw, _ = p.shape
        pu = (ang * pw * 2 % pw).astype(int); pvv = np.clip((pv * (ph - 1)).astype(int), 0, ph - 1); s = p[pvv, pu]
        op = 0.24 if boss else 0.14; m = (s[..., 3] * op * np.clip((a - 0.2) * 4, 0, 1))[..., None]; c = c * (1 - m) + s[..., :3] * m
        if boss:
            pv2 = np.clip((dd - (1 - wd * 3.6)) / (wd * 1.6), 0, 1); pvv2 = np.clip((pv2 * (ph - 1)).astype(int), 0, ph - 1); s2 = p[pvv2, (pu * 2) % pw]
            m2 = (s2[..., 3] * 0.14 * (dd > 1 - wd * 3.2) * (dd < 1 - wd * 1.4))[..., None]; c = c * (1 - m2) + s2[..., :3] * m2
    if pulse_deg is not None:
        ang = np.degrees(np.arctan2(-dy, dx)); da = np.abs((ang - pulse_deg + 180) % 360 - 180); m = (np.clip(1 - da / 28, 0, 1) ** 1.5 * np.clip((dd - (1 - wd * 1.2)) / 0.2, 0, 1) * 0.55)[..., None]
        c = c * (1 - m) + hx("#E85C41") * m
    if flash:
        e = np.minimum(np.minimum(xs, w - xs), np.minimum(ys, h - ys)); m = (np.clip(1 - e / 18, 0, 1) ** 1.3)[..., None]; c = c * (1 - m) + hx("#C9B0FF") * m
    # 중심 청록 글로우(차사 자리)
    g = np.exp(-((dx / (w * 0.09)) ** 2 + (dy / (h * 0.16)) ** 2)) * 0.18 if radius else 0
    c = np.clip(c + (g[..., None] * hx("#5FE3C0") if radius else 0), 0, 1)
    return Image.fromarray((c * 255 + 0.5).astype(np.uint8))

def lut_strip_sheet(params):
    """LUT 20장을 한눈에: 중간 회색 그라데이션+색 막대에 각 LUT를 먹여 본 견본."""
    base = np.zeros((60, 320, 3), np.float32)
    ramp = np.linspace(0, 1, 320)[None, :, None]; base[:20] = ramp
    cols = ["#E85C41", "#D4A94E", "#5FE3C0", "#5B8FC4", "#C9B0FF", "#6E8B4A", "#BFE8FF", "#8A6A4A"]
    for i, cc in enumerate(cols): base[20:60, i * 40:(i + 1) * 40] = hx(cc)
    rows = []
    for t in TIMES:
        rows.append(np.concatenate([grade(base, combine(t, w)) for w in WEATHER], 1))
    sheet = np.concatenate(rows, 0)
    im = Image.fromarray((sheet * 255 + 0.5).astype(np.uint8)); return im

def run_preview():
    from PIL import ImageFont
    font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 26)
    def lab(im, text):
        d = ImageDraw.Draw(im); d.rectangle([0, 0, 8 + 22 * len(text), 36], fill=(0, 0, 0)); d.text((8, 4), text, font=font, fill=(255, 255, 255)); return im
    # (1) 시간대 4 × 전후
    srcs = {"day": "scene_tendo_h12.5.png", "dusk": "scene_tendo_h18.0.png", "night": "scene_tendo.png", "dawn": "scene_tendo_h5.5.png"}
    rows = []
    for t, f in srcs.items():
        p = os.path.join(PRE, f)
        if not os.path.exists(p): print("없음", p); continue
        b = Image.open(p).convert("RGB"); a = post(b, t, "clear")
        W = 800; sz = (W, int(b.height * W / b.width))
        rows.append(np.concatenate([np.asarray(lab(b.resize(sz), f"{TIMES[t]['label']} 전")), np.asarray(lab(a.resize(sz), f"{TIMES[t]['label']} 후"))], 1))
    if rows: Image.fromarray(np.concatenate(rows, 0)).save(os.path.join(PRE, "grading_time.jpg"), quality=86)
    # (2) 날씨 5 (같은 밤 + 낮 장면): 날씨 겉모습(안개 층·비 줄기)은 미리보기용으로 얹음 — 실제는 코드팀 효과
    rng = np.random.RandomState(3)
    for t, f in (("night", "scene_tendo.png"), ("day", "scene_tendo_h12.5.png")):
        p = os.path.join(PRE, f)
        if not os.path.exists(p): continue
        b = Image.open(p).convert("RGB").resize((640, 360)); panels = []
        for w in WEATHER:
            a = post(b, t, w); c = np.asarray(a).astype(np.float32) / 255
            if w in ("fog", "plague"):
                fy = np.linspace(0, 1, 360)[:, None, None]; nz = np.asarray(Image.fromarray((rng.rand(36, 64) * 255).astype(np.uint8)).resize((640, 360), Image.BICUBIC)).astype(np.float32)[..., None] / 255
                fogc = hx("#46564F") if w == "plague" else hx("#8A98A4" if t == "day" else "#2A3548"); k = (0.28 + 0.2 * nz) * (0.6 + 0.4 * fy) * (1.0 if w == "fog" else 0.9)
                c = c * (1 - k) + fogc * k
            if w == "rain":
                im = Image.new("L", (640, 360), 0); dr = ImageDraw.Draw(im)
                for _ in range(260):
                    x = rng.randint(0, 700); y = rng.randint(-40, 360); dr.line([x, y, x - 10, y + 34], fill=int(60 + rng.rand() * 60), width=1)
                c = np.clip(c + np.asarray(im).astype(np.float32)[..., None] / 255 * hx("#BFD0E6"), 0, 1)
            panels.append(np.asarray(lab(Image.fromarray((np.clip(c, 0, 1) * 255).astype(np.uint8)), f"{WEATHER[w]['label']}")))
        ref = np.asarray(lab(Image.fromarray(np.asarray(b)), "원본"))
        top = np.concatenate([ref, panels[0], panels[1]], 1); bot = np.concatenate([panels[2], panels[3], panels[4]], 1)
        Image.fromarray(np.concatenate([top, bot], 0)).save(os.path.join(PRE, f"grading_weather_{t}.jpg"), quality=86)
    # (3) LUT 견본
    lut_strip_sheet(None).resize((1600, 600), Image.NEAREST).save(os.path.join(PRE, "grading_lut_swatch.png"))
    # (4) 천도 시야 축소 4단계
    n, pat = build_vision_textures(); noise = Image.fromarray((n * 255).astype(np.uint8))
    base = Image.open(os.path.join(PRE, "scene_tendo.png")).convert("RGB")
    base = post(base, "night", "clear")
    fr = [("평소", base),
          ("조이는 중 80%", shrink_frame(base, 0.8, False, noise, pat)), ("천도 60%", shrink_frame(base, 0.6, False, noise, pat, pulse_deg=215)),
          ("보스 천도 60%", shrink_frame(base, 0.6, True, noise, pat, pulse_deg=300)), ("성공 순간", shrink_frame(base, None, False, noise, pat, flash=True))]
    pn = [np.asarray(lab(f.resize((640, 360)), t)) for t, f in fr]
    Image.fromarray(np.concatenate([np.concatenate(pn[:3], 1), np.concatenate(pn[3:] + [np.zeros_like(pn[0])], 1)], 0)).save(os.path.join(PRE, "grading_tendo.jpg"), quality=88)
    print("미리보기 완료")

if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("luts", "all"):
        P = build_luts(); build_json(P); print("LUT 22장 + params")
    if what in ("vision", "all"): build_vision_textures(); print("시야 질감")
    if what in ("preview", "all"): run_preview()
