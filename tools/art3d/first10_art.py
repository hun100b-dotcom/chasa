"""처음 10분 그림 묶음(기획 first-10min-benchmark §4의 아트 몫): 품계 승급 인(M6) · 혼불·엽전 흡수(M3) · 장비 등급 이름표(M4, 빛줄기는 drop_pillars.py) ·
첫 도술 카드(M9) · 거센 혼 표시(M10) · 처결 보상 아이콘(M5) · 목표 화살표(M12) · 타이틀 메뉴·안개(M1) · 로딩 안내판(M14).
규칙: 한지·먹·단청 금 언어만 쓴다. 주황은 파혼 전용(엽전·파혼 보상에만). 글자는 그림에 넣지 않는다(코드가 얹음). 모든 그림은 2배로 그려 1배·@2x 두 벌.
산출(assets3d/ui/first10/): 아래 FILES 표와 docs/FIRST10-ART.md 참고. 실행: python3 first10_art.py"""
import os, math, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import ui_lib as U
from ui_lib import HANJI, HANJI_D, INK, NAVY, ABYSS, GOLD, TEAL, VIOLET, BLUE, CHAIN, save, font, hanji_tex, rr_mask, rgba, noise, shadow

SUB = "first10"
SEAL = (196, 52, 40)          # 품계 인·거센 혼의 붉은색(로고 도장과 같은 인주색). 파혼 주황(#E8683A)과 다르다
ORANGE = (232, 104, 58)       # 파혼 전용
PURPLE = (154, 92, 255)       # 덩어리(맺힘)
BRASS = (214, 160, 78)        # 엽전 놋쇠
S = 2                         # 2배 작업

def new(w, h): return Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
def glow_layer(size, draw_fn, color, radius, strength=1.0):
    """모양(draw_fn이 흰색으로 그림)을 번지게 해 빛 번짐 층을 만든다."""
    m = Image.new("L", size, 0); draw_fn(ImageDraw.Draw(m)); m = m.filter(ImageFilter.GaussianBlur(radius)).point(lambda v: min(255, int(v * strength)))
    lay = Image.new("RGBA", size, tuple(color) + (0,)); lay.putalpha(m); return lay
def over(base, lay): base.alpha_composite(lay); return base
def radial(size, color, r0, r1, a=255):
    """가운데 밝고 가장자리로 사라지는 원."""
    w, h = size; y, x = np.mgrid[0:h, 0:w]; d = np.hypot(x - w / 2, y - h / 2); t = np.clip((r1 - d) / max(1e-3, r1 - r0), 0, 1) ** 1.6
    im = Image.new("RGBA", size, tuple(color) + (0,)); im.putalpha(Image.fromarray((t * a).astype(np.uint8))); return im

def strip(frames, name, fps=None, note=""):
    """프레임들을 가로로 이어 붙여 저장(1배·@2x). frames는 2배 크기 RGBA 목록."""
    w, h = frames[0].size; W = Image.new("RGBA", (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames): W.paste(f, (i * w, 0))
    save(W, name, SUB, note=note + f" 프레임 {len(frames)}장 가로로 이어 붙임, 칸 {w // S}×{h // S}" + (f", {fps}fps" if fps else "")); return W

# ── ① 품계 승급: 명부 종이 + 붉은 인 찍히는 1.0초(12프레임 12fps) ────────────────────────────
def rank_paper():
    w, h = 640, 400; W, H = w * S, h * S
    tex = hanji_tex(W, H, seed=11, tone=0.98); edge = noise(W, H, 6, 5)
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rounded_rectangle([16, 16, W - 17, H - 17], radius=14, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(1.2)); a = np.asarray(m, np.float32) / 255 * np.clip(0.75 + edge * 0.7, 0, 1) ** 0.3
    im = rgba(tex, np.clip(a, 0, 1)); d = ImageDraw.Draw(im)
    for k, c in ((34, INK + (255,)), (46, INK + (110,))): d.rounded_rectangle([k, k, W - 1 - k, H - 1 - k], radius=10, outline=c, width=3)
    for i in range(1, 6): d.line([(W * i / 6, 70), (W * i / 6, H - 70)], fill=INK + (28,), width=2)        # 명부 세로 줄(희미)
    d.rectangle([60, 64, W - 60, 120], outline=INK + (120,), width=2)                                        # 위 현판 자리(계급명)
    U.corner_marks(d, (22, 22, W - 23, H - 23), GOLD + (255,), 40, 5)
    return shadow(im, (0, 10), 14, 0.55)

def stamp_img(size, scale=1.0, press=1.0, seed=2):
    """붉은 品 인(정사각). press<1이면 인주가 덜 묻은 연한 모양."""
    s = int(size * scale); im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([2, 2, s - 3, s - 3], radius=s // 14, fill=SEAL + (255,)); d.rounded_rectangle([s // 11, s // 11, s - 1 - s // 11, s - 1 - s // 11], radius=s // 20, outline=HANJI + (170,), width=max(2, s // 40))
    f = font(int(s * 0.62)); bb = f.getbbox("品"); d.text(((s - (bb[0] + bb[2])) / 2, (s - (bb[1] + bb[3])) / 2 - s * 0.02), "品", font=f, fill=HANJI + (255,))
    n = noise(s, s, 4, seed) * 0.6 + noise(s, s, 11, seed + 1) * 0.4; a = np.asarray(im.split()[3], np.float32) / 255
    a = a * np.clip(1.15 - (1 - press) * 1.6 * n - (1 - press) * 0.2, 0, 1)                                    # 인주 얼룩(마른 자리)
    im.putalpha(Image.fromarray((a * 255).astype(np.uint8))); return im

def rank_stamp_frames():
    """12프레임(1.0초): 0~3 인이 크게 떠서 내려옴 → 4 찍힘(충격 고리) → 5~11 번짐·가라앉음. 칸 256²."""
    F = []; C = 128 * S; N = 12
    for i in range(N):
        fr = new(256, 256); cx = cy = C
        if i <= 3:
            t = i / 3; sc = 1.9 - 0.9 * t ** 1.5; al = 0.25 + 0.75 * t; im = stamp_img(int(150 * S), sc, 1.0); im.putalpha(im.split()[3].point(lambda v: int(v * al)))
            sh = Image.new("RGBA", fr.size, (0, 0, 0, 0)); sd = Image.new("L", fr.size, 0); ImageDraw.Draw(sd).ellipse([cx - 60 * S, cy + 40 * S, cx + 60 * S, cy + 70 * S], fill=int(70 * t)); sh.putalpha(sd.filter(ImageFilter.GaussianBlur(8 * S))); fr = over(fr, sh)
            fr.alpha_composite(im, (cx - im.width // 2, cy - im.height // 2 - int((1 - t) * 20 * S)))
        else:
            t = (i - 4) / (N - 5); im = stamp_img(int(150 * S), 1.0 - 0.015 * (1 - t), 0.8 + 0.2 * t)
            blt = glow_layer(fr.size, lambda dd: dd.rounded_rectangle([cx - 78 * S, cy - 78 * S, cx + 78 * S, cy + 78 * S], radius=10 * S, fill=255), SEAL, 7 * S, 0.55 * (1 - t) + 0.25)
            fr = over(fr, blt); fr.alpha_composite(im, (cx - im.width // 2, cy - im.height // 2))
            if t < 0.6:                                                                                           # 충격 고리(먹물이 튀는 모양)
                rr = (80 + 120 * t) * S; ring = Image.new("RGBA", fr.size, (0, 0, 0, 0)); rd = ImageDraw.Draw(ring)
                rd.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=HANJI + (int(210 * (1 - t / 0.6)),), width=int(5 * S * (1 - t / 0.6)) + 1); fr = over(fr, ring)
                rng = np.random.RandomState(7)
                for k in range(14):
                    a = rng.uniform(0, math.tau); r1 = (84 + 70 * t) * S; r2 = r1 + rng.uniform(6, 20) * S * (1 - t)
                    ImageDraw.Draw(fr).line([(cx + math.cos(a) * r1, cy + math.sin(a) * r1), (cx + math.cos(a) * r2, cy + math.sin(a) * r2)], fill=SEAL + (int(230 * (1 - t / 0.6)),), width=int(3 * S))
        F.append(fr)
    return F

def craft_flash_frames():
    """손보기 성공: 장비 이름 위로 금빛이 훑고 지나감(8프레임, 칸 512×96). 이름 글자는 코드가 위에 얹는다."""
    F = []; W, H = 512 * S, 96 * S
    for i in range(8):
        t = i / 7; x = -80 * S + (W + 160 * S) * t; lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        bar = glow_layer((W, H), lambda d: d.polygon([(x - 26 * S, H), (x + 6 * S, 0), (x + 40 * S, 0), (x + 8 * S, H)], fill=255), GOLD, 7 * S, 1.6)
        lay = over(lay, bar); core = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(core).polygon([(x - 8 * S, H), (x + 14 * S, 0), (x + 26 * S, 0), (x + 4 * S, H)], fill=(255, 244, 214, 220)); lay = over(lay, core)
        base = glow_layer((W, H), lambda d: d.rounded_rectangle([8 * S, 20 * S, W - 8 * S, H - 20 * S], radius=14 * S, fill=int(90 * math.sin(math.pi * t))), GOLD, 14 * S, 1.0); F.append(over(base, lay))
    return F

def rank_dot():
    im = new(12, 12); d = ImageDraw.Draw(im); d.ellipse([1, 1, 22, 22], fill=SEAL + (255,), outline=HANJI + (255,), width=2); d.ellipse([6, 5, 12, 11], fill=(255, 190, 170, 230)); return shadow(im, (0, 1), 1, 0.5)

# ── ② 혼불 흡수·엽전 튐(같은 길이·크기) ───────────────────────────────────────────────────────
def orb_frames(n=4):
    """날아가는 혼불 4프레임(깜빡임, 48²). 곡선 이동은 코드가 한다."""
    F = []
    for i in range(n):
        fr = new(48, 48); s = 1 + 0.12 * math.sin(i / n * math.tau)
        for rad, col, a in ((22, TEAL, 70), (15, TEAL, 140), (9, (210, 255, 240), 255)):
            r = rad * s * S; ImageDraw.Draw(fr).ellipse([24 * S - r, 24 * S - r, 24 * S + r, 24 * S + r], fill=tuple(col) + (a,))
        fr = fr.filter(ImageFilter.GaussianBlur(1.2 * S)); F.append(fr)
    return F

def coin_img(w=48, squash=1.0, lit=1.0):
    """엽전(놋쇠 동전, 가운데 네모 구멍). squash<1이면 도는 중."""
    im = new(48, 48); d = ImageDraw.Draw(im); R = 17 * S; rx = max(2 * S, R * squash)
    d.ellipse([24 * S - rx, 24 * S - R, 24 * S + rx, 24 * S + R], fill=tuple(int(c * lit) for c in BRASS) + (255,), outline=(90, 56, 28, 255), width=int(2 * S))
    d.ellipse([24 * S - rx * 0.8, 24 * S - R * 0.8, 24 * S + rx * 0.8, 24 * S + R * 0.8], outline=(240, 205, 130, 200), width=int(1.4 * S))
    q = 5 * S; d.rectangle([24 * S - q * squash, 24 * S - q, 24 * S + q * squash, 24 * S + q], fill=(40, 28, 20, 255)); return im

def coin_frames(n=6):
    return [coin_img(48, max(0.18, abs(math.cos(i / n * math.pi))), 1.0 - 0.15 * abs(math.sin(i / n * math.pi))) for i in range(n)]

def burst_frames(color, kind, n=6):
    """가슴/발밑에서 흡수되는 순간 6프레임(128², 0.3초). kind='hon'은 안으로 모이는 청록 불티, 'coin'은 바깥으로 튀는 주황 파편(모양이 달라 색 없이도 구분)."""
    F = []; C = 64 * S; rng = np.random.RandomState(4 if kind == "hon" else 9)
    ang = [rng.uniform(0, math.tau) for _ in range(10)]
    for i in range(n):
        t = i / (n - 1); fr = new(128, 128)
        fr = over(fr, radial(fr.size, color, 0, int(46 * S * (0.7 + 0.5 * math.sin(math.pi * t))), int(190 * (1 - t) ** 0.8)))
        d = ImageDraw.Draw(fr)
        for a in ang:
            if kind == "hon":     # 바깥에서 가운데로 가는 짧은 불티
                r1 = (54 - 44 * t) * S; r2 = r1 + 14 * S * (1 - t); d.line([(C + math.cos(a) * r1, C + math.sin(a) * r1), (C + math.cos(a) * r2, C + math.sin(a) * r2)], fill=(220, 255, 244, int(255 * (1 - t * 0.6))), width=int(3 * S))
            else:                 # 가운데에서 바깥으로 가는 삐죽 파편(삼각)
                r1 = (8 + 40 * t) * S; r2 = r1 + 12 * S * (1 - t * 0.5); p = (C + math.cos(a) * r2, C + math.sin(a) * r2)
                d.polygon([p, (C + math.cos(a + 0.18) * r1, C + math.sin(a + 0.18) * r1), (C + math.cos(a - 0.18) * r1, C + math.sin(a - 0.18) * r1)], fill=(255, 190, 120, int(255 * (1 - t))))
        F.append(fr)
    return F

# ── ③ 장비 등급 표시: 이름표 판 + 꼭대기 모양(색약 대응: 모양이 등급마다 다르다) ──────────────────────
TIERS = [("common", "흔한", (243, 231, 211)), ("refined", "손본", (79, 168, 160)), ("rare", "귀한", (212, 169, 78)), ("antique", "옛 차사", (59, 74, 122)), ("named", "이름 있는", (232, 92, 65)), ("set", "한 벌", (95, 227, 192))]
def tier_mark(i, size=32, col=None):
    """등급 꼭대기 모양: 0 동그라미 · 1 마름모 · 2 붓 한 획 · 3 도장 네모(속 빈) · 4 세 뿔 관 · 5 겹 고리(◎). 먹 테두리를 두르고 색으로 채운다(어두운 옛 차사 남색만 한지색 테두리)."""
    col = col or TIERS[i][2]; im = new(size, size); d = ImageDraw.Draw(im); c = size * S / 2; r = size * S * 0.36
    def shape(dd, fill, grow=0):
        rr = r + grow
        if i == 0: dd.ellipse([c - rr, c - rr, c + rr, c + rr], fill=fill)
        elif i == 1: dd.polygon([(c, c - rr * 1.15), (c + rr, c), (c, c + rr * 1.15), (c - rr, c)], fill=fill)
        elif i == 2:
            # 붓 한 획(IP 점검: 별 꾸밈 금지): 가로로 굵게 시작해 끝이 가늘어지는 획 + 위쪽 점 하나
            dd.polygon([(c - rr * 1.25, c - rr * 0.1), (c - rr * 1.05, c + rr * 0.55), (c + rr * 0.4, c + rr * 0.45), (c + rr * 1.3, c + rr * 0.05), (c + rr * 0.4, c - rr * 0.3)], fill=fill)
            dd.polygon([(c - rr * 0.1, c - rr * 1.0), (c + rr * 0.35, c - rr * 0.6), (c - rr * 0.1, c - rr * 0.2), (c - rr * 0.55, c - rr * 0.6)], fill=fill)
        elif i == 3: dd.rectangle([c - rr, c - rr, c + rr, c + rr], fill=fill)
        elif i == 5: dd.ellipse([c - rr * 1.15, c - rr * 1.15, c + rr * 1.15, c + rr * 1.15], fill=fill)
        else: dd.polygon([(c - rr * 1.1, c + rr * 0.9), (c - rr * 1.1, c - rr * 0.5), (c - rr * 0.55, c + rr * 0.15), (c, c - rr * 1.25), (c + rr * 0.55, c + rr * 0.15), (c + rr * 1.1, c - rr * 0.5), (c + rr * 1.1, c + rr * 0.9)], fill=fill)
    shape(d, (HANJI if i == 3 else INK) + (255,), 3.2 * S); shape(d, tuple(col) + (255,))
    if i == 3: d.rectangle([c - r * 0.45, c - r * 0.45, c + r * 0.45, c + r * 0.45], fill=HANJI + (255,))        # 속 빈 도장 네모
    if i == 5: d.ellipse([c - r * 0.5, c - r * 0.5, c + r * 0.5, c + r * 0.5], fill=INK + (255,)); d.ellipse([c - r * 0.25, c - r * 0.25, c + r * 0.25, c + r * 0.25], fill=tuple(col) + (255,))
    return im

def tag_plate(i):
    """바닥 이름표 판(9칸): 먹판 + 등급색 테두리. 왼쪽 28px는 등급 모양 자리(분리 그림 tier_mark_*)."""
    w, h = 220, 40; col = TIERS[i][2]; im = new(w, h); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * S - 1, h * S - 1], radius=10 * S, fill=NAVY + (222,), outline=(col if i != 3 else (118, 138, 205)) + (255,), width=int(3 * S)); d.rounded_rectangle([5 * S, 5 * S, w * S - 6 * S, h * S - 6 * S], radius=7 * S, outline=(col if i != 3 else (118, 138, 205)) + (90,), width=S)
    return im

# ── ④ 첫 도술 카드 3장 ────────────────────────────────────────────────────────────────────────
def card_frame(hover=False):
    """첫 도술 카드 틀 320×440(기획 명세). 위 가운데 큰 갈래 모양 자리(원 배지, 지름 80), 그 아래 삽화 창 288×130, 이름 띠, 한 줄 효과 자리. 등급 테두리 없음(도술은 등급이 아니다)."""
    w, h = 320, 440; W, H = w * S, h * S; tex = hanji_tex(W, H, seed=21)
    im = rgba(tex, rr_mask(W, H, 20 * S)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, W - 1, H - 1], radius=20 * S, outline=INK + (255,), width=int(5 * S)); d.rounded_rectangle([9 * S, 9 * S, W - 10 * S, H - 10 * S], radius=14 * S, outline=INK + (110,), width=int(2 * S))
    d.rounded_rectangle([16 * S, 66 * S, W - 17 * S, 196 * S], radius=8 * S, fill=NAVY + (255,), outline=INK + (255,), width=int(2 * S))        # 삽화 창 288×130 at (16,66)
    d.rectangle([16 * S, 208 * S, W - 17 * S, 252 * S], fill=HANJI_D + (255,), outline=INK + (200,), width=S)                                         # 이름 띠 288×44 at (16,208)
    d.line([(24 * S, 372 * S), (W - 24 * S, 372 * S)], fill=INK + (90,), width=S)                                                                      # 효과 글(262~362) 끝선
    c = (160 * S, 44 * S); d.ellipse([c[0] - 42 * S, c[1] - 42 * S, c[0] + 42 * S, c[1] + 42 * S], fill=HANJI + (255,), outline=INK + (255,), width=int(4 * S))   # 갈래 배지 자리(지름 84)
    im = shadow(im, (0, 8), 12, 0.6)
    if hover: im = over(im, glow_layer(im.size, lambda dd: dd.rounded_rectangle([2 * S, 2 * S, W - 3 * S, H - 3 * S], radius=20 * S, outline=255, width=int(8 * S)), GOLD, 7 * S, 2.4))
    return im

def branch_emblem(kind, size=40):
    """갈래 표시. 기획 명세 v1.5: ◎ 부름(청록 겹원) · ∞ 줄(청백 사슬 고리 둘) · 번진 먹점 얼룩(보라, 가장자리가 물결진 채운 점). 색을 못 봐도 모양으로 구분.
    왜 바꿨나: 옛 ▲·✕는 처결(천도 ▲·파혼 ✕)과 같은 모양이라 첫 10분에 둘 다 나오면 헷갈려서 → 천도·파혼 전용으로 비움.
    size=40(카드 아래/도술 창) 또는 80(카드 위 배지). 바깥에 먹 테두리를 둘러 어느 바탕에서도 읽힌다."""
    im = new(size, size); d = ImageDraw.Draw(im); c = size * S / 2; r = size * S * 0.36; ink_g = size * S * 0.07
    def blot(rr):
        pts = []
        for k in range(72):
            a = k / 72 * math.tau; w = 1 + 0.10 * math.sin(5 * a + 0.6) + 0.06 * math.sin(9 * a + 2.0); pts.append((c + math.cos(a) * rr * w, c + math.sin(a) * rr * w))
        return pts
    def ring(cx, rad, wd, fill): d.ellipse([cx - rad, c - rad, cx + rad, c + rad], outline=fill, width=max(1, int(wd)))
    if kind == "bureum":                                 # ◎
        d.ellipse([c - r - ink_g, c - r - ink_g, c + r + ink_g, c + r + ink_g], fill=INK + (255,))
        ring(c, r, r * 0.26, TEAL + (255,)); d.ellipse([c - r * 0.4, c - r * 0.4, c + r * 0.4, c + r * 0.4], fill=TEAL + (255,))
    elif kind == "jul":                                  # ∞ (사슬 고리 둘이 맞물림)
        rad = r * 0.58; dx = r * 0.52
        for sx in (-1, 1): d.ellipse([c + sx * dx - rad - ink_g, c - rad - ink_g, c + sx * dx + rad + ink_g, c + rad + ink_g], fill=INK + (255,))
        for sx in (-1, 1): ring(c + sx * dx, rad, r * 0.25, CHAIN + (255,))
        ring(c - dx, rad, r * 0.25, CHAIN + (255,))      # 왼쪽 고리를 한 번 더 그려 겹친 곳에서 한쪽이 위로 가게(맞물림)
        d.arc([c + dx - rad, c - rad, c + dx + rad, c + rad], 200, 340, fill=CHAIN + (255,), width=max(1, int(r * 0.25)))
    else:                                                # 번진 먹점
        d.polygon(blot(r + ink_g), fill=INK + (255,)); d.polygon(blot(r), fill=PURPLE + (255,))
        d.polygon(blot(r * 0.5), fill=tuple(int(v * 0.7) for v in PURPLE) + (255,))     # 가운데 더 짙게(먹이 고인 곳)
    return im

def card_art(kind):
    """카드 그림 창 228×210 안쪽 삽화. 부름=사슬 갈고리가 혼불을 끌어옴 / 줄=사슬이 감겨 도는 고리 / 얼룩=보라 번짐이 터짐."""
    w, h = 288, 130; im = Image.new("RGBA", (w * S, h * S), NAVY + (255,)); d = ImageDraw.Draw(im); c = (w * S / 2, h * S / 2)
    bgn = noise(w * S, h * S, 18, 5); im = Image.fromarray(np.clip(np.asarray(im, np.float32) * (0.85 + 0.3 * bgn[..., None]), 0, 255).astype(np.uint8), "RGBA"); d = ImageDraw.Draw(im)
    if kind == "bureum":
        for k in range(1, 6): d.ellipse([c[0] + 40 * S - k * 20 * S, c[1] - k * 14 * S, c[0] + 40 * S + k * 20 * S, c[1] + k * 14 * S], outline=TEAL + (int(90 / k),), width=S)    # 끌려오는 파문
        for k in range(9): x = 20 * S + k * 24 * S; y = c[1] - 30 * S + 22 * S * math.sin(k * 0.9); d.rounded_rectangle([x, y, x + 24 * S, y + 14 * S], radius=6 * S, outline=CHAIN + (255,), width=int(3.5 * S))
        im = over(im, glow_layer(im.size, lambda dd: dd.ellipse([c[0] + 30 * S, c[1] - 6 * S, c[0] + 82 * S, c[1] + 46 * S], fill=255), TEAL, 14 * S, 1.6)); d = ImageDraw.Draw(im)
        d.ellipse([c[0] + 42 * S, c[1] + 6 * S, c[0] + 70 * S, c[1] + 34 * S], fill=(215, 255, 244, 255))
    elif kind == "jul":
        for k in range(18):
            a = k / 18 * math.tau; r = 62 * S + 6 * S * math.sin(k); x = c[0] + math.cos(a) * r; y = c[1] + math.sin(a) * r * 0.78
            d.ellipse([x - 12 * S, y - 9 * S, x + 12 * S, y + 9 * S], outline=CHAIN + (255,), width=int(3.5 * S))
        for k in range(12):
            a = k / 12 * math.tau + 0.2; r = 34 * S; x = c[0] + math.cos(a) * r; y = c[1] + math.sin(a) * r * 0.78
            d.ellipse([x - 9 * S, y - 7 * S, x + 9 * S, y + 7 * S], outline=BLUE + (255,), width=int(3 * S))
        im = over(im, glow_layer(im.size, lambda dd: dd.ellipse([c[0] - 14 * S, c[1] - 12 * S, c[0] + 14 * S, c[1] + 12 * S], fill=255), TEAL, 8 * S, 1.8))
    else:
        rng = np.random.RandomState(8); pts = []
        for k in range(26): a = k / 26 * math.tau; q = (74 if k % 2 == 0 else 38 + rng.uniform(0, 16)) * S; pts.append((c[0] + math.cos(a) * q, c[1] + math.sin(a) * q * 0.85))
        im = over(im, glow_layer(im.size, lambda dd: dd.polygon(pts, fill=255), PURPLE, 14 * S, 1.4)); d = ImageDraw.Draw(im); d.polygon(pts, fill=PURPLE + (255,)); d.polygon([(c[0] + (p[0] - c[0]) * 0.55, c[1] + (p[1] - c[1]) * 0.55) for p in pts], fill=(60, 30, 130, 255))
        for k in range(10): a = rng.uniform(0, math.tau); r = rng.uniform(80, 100) * S; x, y = c[0] + math.cos(a) * r, c[1] + math.sin(a) * r * 0.85; d.ellipse([x - 5 * S, y - 5 * S, x + 5 * S, y + 5 * S], fill=PURPLE + (255,))
    m = rr_mask(w * S, h * S, 8 * S); im.putalpha(m); return im

# ── ⑤ 거센 혼: 머리 위 붉은 테 + 이름 띠 + 맺힘 막대 ───────────────────────────────────────────
def elite_ring_frames(n=4):
    """머리 위에 뜨는 붉은 가시 고리(쿼터뷰라 납작한 타원 256×128). 가시가 12개라 색을 못 봐도 일반 혼과 구분된다. 4프레임은 맥동."""
    F = []
    for i in range(n):
        t = i / n; pulse = 0.5 + 0.5 * math.sin(t * math.tau); fr = new(256, 128); d = ImageDraw.Draw(fr); cx, cy = 128 * S, 64 * S
        rx, ry = (86 + 5 * pulse) * S, (30 + 2 * pulse) * S
        fr = over(fr, glow_layer(fr.size, lambda dd: dd.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=255, width=int(8 * S)), SEAL, 8 * S, 1.2 + 0.5 * pulse)); d = ImageDraw.Draw(fr)
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=INK + (255,), width=int(9 * S)); d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=SEAL + (255,), width=int(5 * S))
        for k in range(12):
            a = k / 12 * math.tau + 0.13; px, py = cx + math.cos(a) * rx, cy + math.sin(a) * ry; L = (30 + 8 * pulse) * S
            qx, qy = cx + math.cos(a) * (rx + L), cy + math.sin(a) * (ry + L * 0.45); nx, ny = -math.sin(a) * 6 * S, math.cos(a) * 3 * S
            d.polygon([(px + nx, py + ny), (qx, qy), (px - nx, py - ny)], fill=INK + (255,)); d.polygon([(px + nx * 0.55, py + ny * 0.55), (cx + math.cos(a) * (rx + L * 0.72), cy + math.sin(a) * (ry + L * 0.33)), (px - nx * 0.55, py - ny * 0.55)], fill=SEAL + (255,))
        F.append(fr)
    return F

def name_band():
    """화면 위 가운데 이름 띠(9칸, 가로 720×64): 먹판 + 붉은 가시 위·아래 테두리 + 양끝 붉은 인."""
    w, h = 720, 64; im = new(w, h); d = ImageDraw.Draw(im); W, H = w * S, h * S
    d.rounded_rectangle([0, 10 * S, W - 1, H - 10 * S], radius=8 * S, fill=NAVY + (232,), outline=INK + (255,), width=int(3 * S))
    for k in range(0, w, 16):
        x = k * S + 8 * S
        d.polygon([(x - 7 * S, 12 * S), (x, 1 * S), (x + 7 * S, 12 * S)], fill=SEAL + (255,)); d.polygon([(x - 7 * S, H - 12 * S), (x, H - 1 * S), (x + 7 * S, H - 12 * S)], fill=SEAL + (255,))
    d.line([(20 * S, 14 * S), (W - 20 * S, 14 * S)], fill=SEAL + (255,), width=int(2 * S)); d.line([(20 * S, H - 14 * S), (W - 20 * S, H - 14 * S)], fill=SEAL + (255,), width=int(2 * S))
    return im

def bind_bar():
    """맺힘 막대(체력 막대 대신): 틀 520×28 + 채움 512×20(보라 덩어리색) + 맺힘 눈금 3칸 덮개. 3칸이 곧 '맺힘 ×3'."""
    w, h = 520, 28; fr = new(w, h); d = ImageDraw.Draw(fr); W, H = w * S, h * S
    d.rounded_rectangle([0, 0, W - 1, H - 1], radius=10 * S, fill=ABYSS + (240,), outline=INK + (255,), width=int(3 * S)); d.rounded_rectangle([3 * S, 3 * S, W - 4 * S, H - 4 * S], radius=8 * S, outline=SEAL + (255,), width=int(2 * S))
    fill = new(512, 20); fd = ImageDraw.Draw(fill); FW, FH = 512 * S, 20 * S
    fd.rounded_rectangle([0, 0, FW - 1, FH - 1], radius=7 * S, fill=PURPLE + (255,)); fd.rounded_rectangle([0, 0, FW - 1, FH // 2], radius=7 * S, fill=(190, 150, 255, 255))
    ticks = new(512, 20); td = ImageDraw.Draw(ticks)
    for k in (1, 2): x = FW * k / 3; td.rectangle([x - 2 * S, 0, x + 2 * S, FH], fill=INK + (255,)); td.rectangle([x - S * 0.7, 0, x + S * 0.7, FH], fill=HANJI + (200,))
    return fr, fill, ticks

# ── ⑥ 처결 보상 아이콘(같은 크기·밝기) ────────────────────────────────────────────────────────
def reward_tendo():
    """천도 보상: 청록 혼불 + 접힌 기억 쪽지(보라 선)."""
    im = new(56, 56); d = ImageDraw.Draw(im)
    im = over(im, glow_layer(im.size, lambda dd: dd.ellipse([8 * S, 4 * S, 40 * S, 44 * S], fill=255), TEAL, 6 * S, 1.3)); d = ImageDraw.Draw(im)
    d.polygon([(24 * S, 4 * S), (38 * S, 26 * S), (24 * S, 46 * S), (10 * S, 26 * S)], fill=INK + (255,)); d.polygon([(24 * S, 8 * S), (35 * S, 26 * S), (24 * S, 42 * S), (13 * S, 26 * S)], fill=TEAL + (255,)); d.polygon([(24 * S, 16 * S), (30 * S, 27 * S), (24 * S, 38 * S), (18 * S, 27 * S)], fill=(225, 255, 247, 255))
    d.rectangle([32 * S, 30 * S, 52 * S, 52 * S], fill=INK + (255,)); d.rectangle([34 * S, 32 * S, 50 * S, 50 * S], fill=HANJI + (255,))
    for k in range(3): d.line([(37 * S, (37 + 4 * k) * S), (47 * S, (37 + 4 * k) * S)], fill=VIOLET + (255,), width=int(1.6 * S))
    return im

def reward_pahon():
    """파혼 보상: 엽전 두 닢 + 얼룩(보라 번짐)."""
    im = new(56, 56); d = ImageDraw.Draw(im)
    pts = []; rng = np.random.RandomState(5)
    for k in range(14): a = k / 14 * math.tau; q = (15 if k % 2 == 0 else 8 + rng.uniform(0, 3)) * S; pts.append((38 * S + math.cos(a) * q, 38 * S + math.sin(a) * q * 0.9))
    d.polygon(pts, fill=INK + (255,)); d.polygon([(38 * S + (p[0] - 38 * S) * 0.78, 38 * S + (p[1] - 38 * S) * 0.78) for p in pts], fill=PURPLE + (255,))
    for (x, y, lit) in ((20, 22, 1.0), (30, 12, 0.92)):
        c = coin_img(48, 1.0, lit).resize((int(28 * S), int(28 * S)), Image.LANCZOS); im.alpha_composite(c, (int((x - 14) * S), int((y - 12) * S)))
    return im

def reward_gold_rim():
    """이름혼 표시: 기억 아이콘 둘레에 겹치는 금테(56²)."""
    im = new(56, 56); d = ImageDraw.Draw(im); d.rounded_rectangle([1 * S, 1 * S, 55 * S, 55 * S], radius=12 * S, outline=INK + (255,), width=int(5 * S)); d.rounded_rectangle([2 * S, 2 * S, 54 * S, 54 * S], radius=11 * S, outline=GOLD + (255,), width=int(3 * S)); return im

# ── ⑦ 목표 화살표(화면 가장자리) ──────────────────────────────────────────────────────────────
def goal_arrow():
    """오른쪽(+X)을 가리키는 금 화살촉 24². 코드가 목표 방향으로 돌린다. 먹 테두리가 있어 밝은 땅·어두운 밤 모두에서 읽힌다."""
    im = new(24, 24); d = ImageDraw.Draw(im); P = [(3, 4), (21, 12), (3, 20), (8, 12)]
    d.polygon([(x * S, y * S) for x, y in P], fill=INK + (255,), outline=INK + (255,), width=int(3.4 * S)); d.polygon([((x * 0.86 + 1.9) * S, (y * 0.86 + 1.7) * S) for x, y in P], fill=GOLD + (255,))
    d.polygon([((x * 0.86 + 1.9) * S, (y * 0.86 + 1.7) * S) for x, y in [(3, 4), (21, 12), (8, 12)]], fill=(244, 214, 128, 255)); return im

def goal_plate():
    """거리 글자 판(9칸 가로 64×22)."""
    w, h = 64, 22; im = new(w, h); d = ImageDraw.Draw(im); d.rounded_rectangle([0, 0, w * S - 1, h * S - 1], radius=9 * S, fill=NAVY + (225,), outline=GOLD + (255,), width=int(2 * S)); return im

# ── ⑧ 타이틀 메뉴·안개 / ⑨ 로딩 안내판 ───────────────────────────────────────────────────────────
def menu_btn(state):
    w, h = 360, 64; im = new(w, h); d = ImageDraw.Draw(im); W, H = w * S, h * S
    base = {"normal": (NAVY, 215, GOLD), "hover": ((30, 46, 86), 240, (244, 214, 128)), "disabled": (ABYSS, 160, (110, 98, 70))}[state]
    d.rounded_rectangle([0, 0, W - 1, H - 1], radius=10 * S, fill=base[0] + (base[1],), outline=base[2] + (255,), width=int(3 * S)); d.rounded_rectangle([6 * S, 6 * S, W - 7 * S, H - 7 * S], radius=7 * S, outline=base[2] + (90,), width=S)
    if state == "hover":
        d.rectangle([14 * S, 14 * S, 22 * S, H - 15 * S], fill=SEAL + (255,)); d.polygon([(W - 22 * S, H / 2 - 8 * S), (W - 12 * S, H / 2), (W - 22 * S, H / 2 + 8 * S)], fill=GOLD + (255,))
        im = over(glow_layer(im.size, lambda dd: dd.rounded_rectangle([0, 0, W - 1, H - 1], radius=10 * S, outline=255, width=int(5 * S)), GOLD, 8 * S, 1.2), im)
    return im

def fog_tile(seed, w=2048, h=512):
    """이어 붙여도 이음매가 없는 안개 띠(좌우 반복). 타이틀 배경 위에 천천히 흘려 쓴다. 흰색 대면적 금지 → 푸른 회색, 가장 짙은 곳도 알파 0.5."""
    r = np.random.RandomState(seed); acc = np.zeros((h, w), np.float32)
    for cell, wt in ((300, 0.5), (140, 0.3), (60, 0.2)):
        gw = max(2, w // cell); gh = max(2, h // cell); g = r.rand(gh + 1, gw).astype(np.float32); g = np.concatenate([g, g[:, :1]], axis=1)         # 가로로 이어지게 첫 열을 끝에 복사
        acc += wt * np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255
    # 이음매 지우기: 첫 열 복사만으로는 값만 이어지고 기울기가 끊겨 x=끝에서 가는 세로 선이 보였다(타이틀 점검). 반폭만큼 굴린 그림과 섞어(가장자리 0 · 가운데 1 창) 양 끝이 원래 그림의 가운데에서 온 값끼리 맞닿게 한다.
    x = np.linspace(0, 1, w, endpoint=False)[None, :]; win = np.sin(np.pi * x) ** 2; acc = acc * win + np.roll(acc, w // 2, axis=1) * (1 - win)
    yy = np.linspace(0, 1, h)[:, None]; band = np.exp(-((yy - 0.55) / 0.28) ** 2) * np.clip((1 - yy) / 0.12, 0, 1) * np.clip(yy / 0.1, 0, 1)   # 위아래 끝은 완전히 투명하게(가로 줄 방지)
    a = np.clip((acc - 0.35) * 2.2, 0, 1) * band * 0.5
    rgb = np.dstack([np.full((h, w), 150, np.float32), np.full((h, w), 168, np.float32), np.full((h, w), 200, np.float32)])
    return Image.fromarray(np.dstack([rgb, a * 255]).astype(np.uint8), "RGBA")

def tip_plate():
    """로딩 팁 판(9칸 가로 960×64): 한지 띠 + 먹 테두리 + 왼쪽 붉은 인 자리. 글은 22자 이내(코드가 22px로 얹음)."""
    w, h = 960, 64; W, H = w * S, h * S; im = rgba(hanji_tex(W, H, seed=31), rr_mask(W, H, 10 * S)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, W - 1, H - 1], radius=10 * S, outline=INK + (255,), width=int(3 * S)); d.rounded_rectangle([5 * S, 5 * S, W - 6 * S, H - 6 * S], radius=7 * S, outline=GOLD + (255,), width=int(2 * S))
    d.rounded_rectangle([14 * S, 16 * S, 46 * S, 48 * S], radius=3 * S, fill=SEAL + (255,)); return shadow(im, (0, 3), 4, 0.4)

# ── 거센 혼 예고 장판(접근성 규칙): 밝은 테두리 #FFF4E0 3px + 빨강 35% 채움이 바깥에서 안으로 차오름. 노랑 #FFE14D 옵션 ──────────
BORDER = (255, 244, 224)
def tele_circle(border=True, color=SEAL, alpha=0.35, n=512):
    """원 예고 n². 채움판(fill)은 코드가 중심까지 안쪽으로 키우는 마스크로 가려 '바깥에서 안으로 차오름'을 만든다(셰이더 반경 컷). 테두리판은 항상 보임."""
    im = Image.new("RGBA", (n * S, n * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = n * S / 2; R = c - 6 * S
    if border:
        d.ellipse([c - R - 2 * S, c - R - 2 * S, c + R + 2 * S, c + R + 2 * S], outline=INK + (200,), width=int(8 * S)); d.ellipse([c - R, c - R, c + R, c + R], outline=BORDER + (255,), width=int(6 * S))      # 3px(@1x) 밝은 테두리 + 먹 바깥선
        for k in range(36): a = k / 36 * math.tau; d.line([(c + math.cos(a) * (R - 12 * S), c + math.sin(a) * (R - 12 * S)), (c + math.cos(a) * (R - 2 * S), c + math.sin(a) * (R - 2 * S))], fill=BORDER + (170,), width=int(3 * S))   # 눈금 틱(가장자리 위치 단서)
    else: d.ellipse([c - R, c - R, c + R, c + R], fill=tuple(color) + (int(255 * alpha),))
    return im

def tele_band(border=True, color=SEAL, alpha=0.35, w=256, h=960):
    """폭 1.6 m × 길이 6 m 띠(256×960 = 1:3.75). 채움은 먼 끝에서 가까운 쪽(덮치는 쪽)으로 차오른다(코드 마스크)."""
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im); W, H = w * S, h * S
    if border:
        d.rectangle([2 * S, 2 * S, W - 3 * S, H - 3 * S], outline=INK + (200,), width=int(8 * S)); d.rectangle([5 * S, 5 * S, W - 6 * S, H - 6 * S], outline=BORDER + (255,), width=int(6 * S))
        for k in range(1, 12): y = H * k / 12; d.line([(5 * S, y), (22 * S, y)], fill=BORDER + (170,), width=int(3 * S)); d.line([(W - 22 * S, y), (W - 5 * S, y)], fill=BORDER + (170,), width=int(3 * S))
        d.polygon([(W / 2 - 22 * S, 40 * S), (W / 2 + 22 * S, 40 * S), (W / 2, 8 * S + 0)], fill=BORDER + (255,)) if False else None
    else: d.rectangle([6 * S, 6 * S, W - 7 * S, H - 7 * S], fill=tuple(color) + (int(255 * alpha),))
    return im

def clear_ring_frames(n=8):
    """천도 뒤 바닥이 맑아지는 연출 8프레임(256², 0.5초): 흰 청록 고리가 번져 나가고 그 안쪽 바닥이 맑게 밝아졌다 사라진다. 위에서 본 모양 → 코드가 바닥에 눕힘."""
    F = []
    for i in range(n):
        t = i / (n - 1); fr = new(256, 256); c = 128 * S; r = (20 + 100 * t ** 0.7) * S
        fr = over(fr, radial(fr.size, (190, 255, 240), 0, int(r), int(120 * (1 - t) ** 1.2))); d = ImageDraw.Draw(fr)
        d.ellipse([c - r, c - r, c + r, c + r], outline=TEAL + (int(255 * (1 - t) ** 0.8),), width=int(6 * S * (1 - 0.6 * t))); d.ellipse([c - r * 0.82, c - r * 0.82, c + r * 0.82, c + r * 0.82], outline=(235, 255, 250, int(150 * (1 - t))), width=int(2 * S))
        F.append(fr)
    return F

def roar_vignette():
    """부르기 울부짖음: 화면 가장자리에 붉은 먹이 번졌다 가시는 틀(1920×1080, 0.8초 동안 알파 맥동). 안쪽은 투명이라 시야를 안 가린다."""
    W, H = 960, 540; y, x = np.mgrid[0:H, 0:W]; dx = np.abs(x - W / 2) / (W / 2); dy = np.abs(y - H / 2) / (H / 2); d = np.maximum(dx, dy * 1.1) ** 3; a = np.clip((d - 0.35) * 1.5, 0, 1) * (0.55 + 0.45 * noise(W, H, 40, 3))
    im = Image.new("RGBA", (W, H), SEAL + (0,)); im.putalpha(Image.fromarray((np.clip(a, 0, 1) * 150).astype(np.uint8))); return im.resize((1920, 1080), Image.BICUBIC)

def run_elite_extras():
    for nm, kw in (("red", dict(color=SEAL)), ("yellow", dict(color=(255, 225, 77)))):
        save(tele_circle(False, **kw), f"tele_circle_fill_{nm}", SUB, note=f"원 예고 채움 512² ({nm} 35%). 바깥에서 안으로 차오르는 마스크는 코드. 반경 2.5 m = 정사각 5 m")
        save(tele_band(False, **kw), f"tele_band_fill_{nm}", SUB, note=f"띠 예고 채움 256×960 ({nm} 35%). 폭 1.6 m × 길이 6 m")
    save(tele_circle(True), "tele_circle_border", SUB, note="원 예고 테두리 512²: 밝은 한지색 #FFF4E0 3px + 먹 바깥선 + 눈금. 항상 보임(채움이 없어도 위치를 알림)")
    save(tele_band(True), "tele_band_border", SUB, note="띠 예고 테두리 256×960")
    strip(clear_ring_frames(), "clear_ring", 16, "천도 뒤 바닥이 맑아지는 번짐 8프레임(0.5초)")
    im = roar_vignette(); im.save(os.path.join(U.UI, SUB, "roar_vignette.png"), optimize=True); U.MANIFEST[f"{SUB}/roar_vignette"] = {"size_px": [1920, 1080], "note": "부르기 울부짖음 화면 가장자리 붉은 먹(알파 0.6초 맥동, 코드가 투명도 0→1→0)"}

def run():
    # ① 품계 승급
    save(rank_paper(), "rank_paper", SUB, note="명부 종이 640×400. 위 현판(60,64~580×56)에 '종9품' 같은 계급명, 아래는 비워 둠. 인은 rank_stamp 띠를 종이 가운데 아래쪽에 겹침")
    strip(rank_stamp_frames(), "rank_stamp", 12, "붉은 品 인 찍힘 1.0초(0~3 내려옴, 4 찍힘, 5~11 번짐). 종소리는 프레임 4에 맞춤.")
    strip(craft_flash_frames(), "craft_flash", 16, "손보기 성공 금빛 훑기 0.5초. 장비 이름 글자 뒤·앞에 깔기")
    save(rank_dot(), "rank_dot", SUB, note="스킬바 도술 칸 모서리에 붙는 붉은 점 12×12")
    # ② 흡수
    strip(orb_frames(), "absorb_hon_fly", 12, "날아가는 혼불(48²), 깜빡임"); strip(coin_frames(), "absorb_coin_spin", 12, "튀는 엽전(48²), 도는 모양")
    strip(burst_frames(TEAL, "hon"), "absorb_hon_burst", 20, "가슴에 흡수되는 순간(128², 0.3초) — 불티가 안으로 모임")
    strip(burst_frames(ORANGE, "coin"), "absorb_coin_burst", 20, "발밑에 빨려 드는 순간(128², 0.3초) — 삐죽 파편이 바깥으로 튐")
    # ③ 등급 표시
    for i, (k, nm, col) in enumerate(TIERS):
        save(tier_mark(i), f"tier_mark_{k}", SUB, note=f"{nm} 등급 꼭대기·이름표 모양 32² (모양 {['동그라미','마름모','붓 한 획','도장 네모','세 뿔 관','겹 고리'][i]})")
        save(tag_plate(i), f"drop_tag_{k}", SUB, nine=[16, 16, 16, 16], note=f"{nm} 등급 바닥 이름표 판 220×40(9칸 16). 왼쪽 28px는 tier_mark 자리")
    # ④ 도술 카드
    save(card_frame(False), "skill_card_frame", SUB, note="첫 도술 카드 틀 320×440. 갈래 배지(지름 84, 중심 160,44), 삽화 창(16,66, 288×130), 이름 띠(16,208, 288×44), 효과 글 y 262~362"); save(card_frame(True), "skill_card_frame_hover", SUB, note="골랐을 때 금빛 테두리 번짐판(같은 크기)")
    for k in ("bureum", "jul", "eolluk"):
        save(card_art(k), f"skill_card_art_{k}", SUB, note=f"카드 삽화 288×130 ({ {'bureum':'붙잡아 부르기','jul':'휘감기','eolluk':'터뜨리기'}[k] }) — 틀의 삽화 창 자리에 깔기"); save(branch_emblem(k, 40), f"branch_{k}", SUB, note="갈래 표시 40²(▲ 부름 ● 줄 ✕ 얼룩, 도술 창·카드 아래)"); save(branch_emblem(k, 80), f"branch_{k}_big", SUB, note="카드 위 가운데 큰 갈래 표시 80²(배지 안에 얹음)")
    # ⑤ 거센 혼
    strip(elite_ring_frames(), "elite_ring", 8, "머리 위 붉은 가시 고리 4프레임 맥동(칸 256×128, 머리 위 0.3 m에 눕혀 놓음)")
    save(name_band(), "elite_name_band", SUB, nine=[24, 24, 24, 24], note="화면 위 가운데 이름 띠 720×64(9칸 24), 이름 글자 24px는 코드")
    fr, fl, tk = bind_bar(); save(fr, "bind_bar_frame", SUB, nine=[12, 12, 12, 12], note="맺힘 막대 틀 520×28"); save(fl, "bind_bar_fill", SUB, note="맺힘 막대 채움 512×20(틀 안쪽 +4,+4)"); save(tk, "bind_bar_ticks", SUB, note="맺힘 3칸 눈금 덮개 512×20(채움 위에 얹음)")
    run_elite_extras()
    # ⑥ 보상 아이콘(밝기를 맞춘다)
    ims = {"reward_tendo": reward_tendo(), "reward_pahon": reward_pahon()}; lum = {}
    for k, im in ims.items():
        a = np.asarray(im, np.float32); w = a[..., 3:4] / 255; lum[k] = float((a[..., :3] @ np.array([0.2126, 0.7152, 0.0722]) * w[..., 0]).sum() / max(1.0, w.sum()))
    tgt = (lum["reward_tendo"] + lum["reward_pahon"]) / 2
    for k, im in ims.items():
        f = tgt / lum[k]; a = np.asarray(im, np.float32); a[..., :3] = np.clip(a[..., :3] * f, 0, 255); ims[k] = Image.fromarray(a.astype(np.uint8), "RGBA"); lum[k] = lum[k] * f
    save(ims["reward_tendo"], "reward_tendo", SUB, note="천도 보상: 혼불+기억 쪽지 56². 파혼 아이콘과 평균 밝기를 맞춤"); save(ims["reward_pahon"], "reward_pahon", SUB, note="파혼 보상: 엽전+얼룩 56². 같은 크기·밝기"); save(reward_gold_rim(), "reward_gold_rim", SUB, note="이름혼이면 기억 아이콘 위에 겹치는 금테 56²")
    # ⑦ 화살표
    save(goal_arrow(), "goal_arrow", SUB, note="화면 가장자리 목표 화살표 24², 오른쪽을 향함(코드가 회전)"); save(goal_plate(), "goal_dist_plate", SUB, nine=[10, 10, 10, 10], note="거리 글자 판 64×22")
    # ⑧ ⑨
    for st in ("normal", "hover", "disabled"): save(menu_btn(st), f"menu_btn_{st}", SUB, nine=[20, 20, 20, 20], note=f"타이틀 메뉴 버튼 360×64 ({st})")
    for sd in (1, 2): fog_tile(sd).save(os.path.join(U.UI, SUB, f"title_fog_{'ab'[sd - 1]}.png"), optimize=True); U.MANIFEST[f"{SUB}/title_fog_{'ab'[sd - 1]}"] = {"size_px": [2048, 512], "note": "이음매 없는 안개 띠. 좌우로 이어 천천히(가장 느린 층 8px/초, 빠른 층 14px/초) 흘림. 밤 서낭당 배경 위"}
    save(tip_plate(), "loading_tip_plate", SUB, nine=[24, 24, 24, 24], note="로딩 팁 판 960×64(9칸 24), 글 22자")
    U.dump_manifest("ui_manifest.json"); json.dump({"reward_mean_luma": lum}, open(os.path.join(U.UI, SUB, "_reward_luma.json"), "w"))
    print("완료", len([k for k in U.MANIFEST if k.startswith(SUB)]), "종, 보상 아이콘 평균 밝기", {k: round(v, 1) for k, v in lum.items()})

if __name__ == "__main__":
    run()
