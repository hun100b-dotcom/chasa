"""필드 혼 유형 3종의 바닥 예고·충격 그림(스프라이트). 실행: python3 soul_fx_sprites.py
왜: 넋두리(원거리)·묻힌 혼(매복)·잔넋(무리)은 '무엇이 올지'를 몸짓과 함께 바닥 표시로 읽혀야 한다(명세: 0.5초 이상 읽히는 예고).
코드는 지금 선(teleLine)을 도형으로 그린다. 그림이 있으면 그 자리에 얹어 쓴다. 색은 원념 보라 #B04FD0(주황은 파혼 전용).
산출(둘 다 같은 파일): assets3d/fx/sprites/ 와 unity/Assets/Resources/Sprites/fx/ (.meta 는 유니티가 만든다)
  tele_throw_line.png   64×512 세로 띠. 위(=탄이 날아갈 먼 쪽)로 갈수록 흐려지는 점선 + 끝 화살촉. 폭 1m·길이 8m 로 늘려 깐다(아래=던지는 혼 쪽)
  tele_crack.png        256² 땅 갈라짐 예고. 4m 원(묻힌 혼 솟는 범위 지름 4m = 반지름 2m). 가운데 어두운 흙·보라 틈빛
  fx_dust_ring.png      1024×256, 256² 4프레임. 솟을 때/묻을 때 흙먼지 고리가 퍼짐(0.3초, 프레임당 0.075초)
  fx_wonnyeom_hit.png   1024×256, 256² 4프레임. 원념 탄이 맞았을 때 보라 파문+조각(0.25초)
  mote_leader_mark.png  64² 대장 잔넋 머리 위 표식(천도하면 나머지가 2초 혼란이라는 힌트). 크기 0.35m"""
import os, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
OUTS = [os.path.join(ROOT, "assets3d", "fx", "sprites"), os.path.join(ROOT, "unity", "Assets", "Resources", "Sprites", "fx")]
for o in OUTS: os.makedirs(o, exist_ok=True)
PUR = (176, 79, 208); PUR_L = (214, 160, 240); VIO = (201, 176, 255); SOIL = (74, 54, 38)
def save(im, name):
    for o in OUTS: im.save(os.path.join(o, name), optimize=True)
def blur(im, r): return im.filter(ImageFilter.GaussianBlur(r))

def throw_line():
    W, H = 64, 512; S = 2; im = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for k in range(14):                       # 아래(던지는 쪽)에서 위로 점선. 위로 갈수록 짧고 흐리게
        t = k / 13; y1 = (H - 24 - k * 34) * S; y0 = y1 - (22 - 8 * t) * S; a = int(230 * (1 - t) ** 1.2 + 25)
        w = (13 - 6 * t) * S; d.rounded_rectangle([W * S / 2 - w, y0, W * S / 2 + w, y1], radius=int(w * 0.7), fill=PUR + (a,))
    d.polygon([(W * S / 2, 6 * S), (W * S / 2 - 15 * S, 40 * S), (W * S / 2 + 15 * S, 40 * S)], fill=PUR_L + (95,))   # 끝 화살촉
    glow = blur(im, 5 * S); out = Image.alpha_composite(glow, im)
    return out.resize((W, H), Image.LANCZOS)

def crack():
    N = 256; S = 2; n = N * S; im = Image.new("RGBA", (n, n), (0, 0, 0, 0)); d = ImageDraw.Draw(im); r = random.Random(5); c = n / 2
    yy, xx = np.mgrid[0:n, 0:n]; rad = np.hypot(xx - c, yy - c) / (n / 2)
    soil = np.zeros((n, n, 4), np.uint8); a = np.clip(1 - rad, 0, 1) ** 0.8 * 200 * (rad < 1); soil[..., :3] = SOIL; soil[..., 3] = a.astype(np.uint8)
    im = Image.alpha_composite(im, Image.fromarray(soil, "RGBA")); d = ImageDraw.Draw(im); glow = Image.new("RGBA", (n, n), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
    def crackline(a0, depth):
        x, y, ang = c, c, a0; pts = [(x, y)]
        for i in range(10):
            ang += r.uniform(-0.45, 0.45); st = (n / 2 * 0.9) / 10 * r.uniform(0.8, 1.2); x += math.cos(ang) * st; y += math.sin(ang) * st; pts.append((x, y))
            if depth < 2 and i in (3, 6) and r.random() < 0.8: crackline(ang + r.choice((-1, 1)) * r.uniform(0.5, 0.9), depth + 1)
        w = int((9 - depth * 3) * S * 0.5)
        gd.line(pts, fill=PUR + (255,), width=w + 6 * S, joint="curve"); d.line(pts, fill=(20, 12, 24, 255), width=w + 2 * S, joint="curve"); d.line(pts, fill=PUR_L + (255,), width=max(2, w // 2), joint="curve")
    for k in range(7): crackline(k / 7 * math.tau + r.uniform(-0.2, 0.2), 0)
    gd.ellipse([c - 18 * S, c - 18 * S, c + 18 * S, c + 18 * S], fill=PUR + (200,))
    out = Image.alpha_composite(blur(glow, 7 * S), im)
    m = np.clip(1 - rad, 0, 1)[..., None]; arr = np.asarray(out, np.float32); arr[..., 3] *= np.clip((1 - rad) * 5, 0, 1); out = Image.fromarray(arr.astype(np.uint8), "RGBA")   # 가장자리 부드럽게
    return out.resize((N, N), Image.LANCZOS)

def dust_ring():
    N = 256; sheet = Image.new("RGBA", (N * 4, N), (0, 0, 0, 0)); r = random.Random(9)
    for f in range(4):
        t = (f + 0.5) / 4; fr = Image.new("RGBA", (N * 2, N * 2), (0, 0, 0, 0)); d = ImageDraw.Draw(fr); c = N; rr = N * (0.25 + 0.65 * t) * 0.95; a = int(220 * (1 - t) ** 1.3)
        for k in range(26):
            th = k / 26 * math.tau + r.uniform(-0.1, 0.1); px, py = c + math.cos(th) * rr, c + math.sin(th) * rr * 0.62; s = N * (0.08 + 0.06 * (1 - t)) * r.uniform(0.7, 1.3)
            d.ellipse([px - s, py - s * 0.7, px + s, py + s * 0.7], fill=(150, 130, 105, a))
        fr = blur(fr, 4).resize((N, N), Image.LANCZOS); sheet.paste(fr, (f * N, 0))
    return sheet

def wonnyeom_hit():
    N = 256; sheet = Image.new("RGBA", (N * 4, N), (0, 0, 0, 0)); r = random.Random(13)
    for f in range(4):
        t = (f + 0.4) / 4; fr = Image.new("RGBA", (N * 2, N * 2), (0, 0, 0, 0)); d = ImageDraw.Draw(fr); c = N; rr = N * (0.15 + 0.7 * t); a = int(255 * (1 - t) ** 1.2)
        d.ellipse([c - rr, c - rr * 0.6, c + rr, c + rr * 0.6], outline=PUR + (a,), width=max(3, int(26 * (1 - t))))
        d.ellipse([c - rr * 0.5, c - rr * 0.3, c + rr * 0.5, c + rr * 0.3], fill=PUR_L + (int(a * 0.5),))
        for k in range(8):                     # 튀는 보라 조각
            th = k / 8 * math.tau + r.uniform(0, 0.4); dd = rr * (0.8 + 0.5 * t); h = N * 0.4 * math.sin(math.pi * min(1, t * 1.4)) * 0.5
            px, py = c + math.cos(th) * dd, c + math.sin(th) * dd * 0.6 - h; s = 7 * (1 - t) + 3; d.polygon([(px, py - s), (px + s * 0.7, py), (px, py + s), (px - s * 0.7, py)], fill=VIO + (a,))
        fr = Image.alpha_composite(blur(fr, 6), fr).resize((N, N), Image.LANCZOS); sheet.paste(fr, (f * N, 0))
    return sheet

def leader_mark():
    N = 64; S = 4; im = Image.new("RGBA", (N * S, N * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = N * S / 2
    d.polygon([(c, 6 * S), (c + 17 * S, 26 * S), (c, 46 * S), (c - 17 * S, 26 * S)], fill=VIO + (255,), outline=(42, 42, 56, 255), width=2 * S)   # 마름모
    d.polygon([(c, 17 * S), (c + 8 * S, 26 * S), (c, 35 * S), (c - 8 * S, 26 * S)], fill=PUR + (255,))
    d.polygon([(c - 8 * S, 52 * S), (c + 8 * S, 52 * S), (c, 60 * S)], fill=VIO + (255,))   # 아래 꼬리(머리 위를 가리킴)
    return Image.alpha_composite(blur(im, 2 * S), im).resize((N, N), Image.LANCZOS)

for name, fn in (("tele_throw_line.png", throw_line), ("tele_crack.png", crack), ("fx_dust_ring.png", dust_ring), ("fx_wonnyeom_hit.png", wonnyeom_hit), ("mote_leader_mark.png", leader_mark)):
    im = fn(); save(im, name); print(name, im.size)
# 미리보기 한 장
pv = Image.new("RGB", (1500, 560), (122, 134, 92)); x = 20
for name in ("tele_throw_line.png", "tele_crack.png", "mote_leader_mark.png"):
    im = Image.open(os.path.join(OUTS[0], name)).convert("RGBA"); pv.paste(im, (x, 20), im); x += im.size[0] + 30
for i, name in enumerate(("fx_dust_ring.png", "fx_wonnyeom_hit.png")):
    im = Image.open(os.path.join(OUTS[0], name)).convert("RGBA"); pv.paste(im, (470, 20 + i * 260), im)
pv.save(os.path.join(ROOT, "assets3d", "previews", "soul_fx_sprites.png"))
