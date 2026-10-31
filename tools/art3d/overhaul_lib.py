"""개편 그림 공통 도구(아트, 2026-10-31). 4배로 그려 줄여 저장 → 가장자리가 매끈하고, 1배·@2x 두 벌이 같은 모양이다.
왜 따로 두나: 기존 ui_lib는 한지 창 위주라 '점선 고리·균열·장판' 같은 그림 도형 함수가 없다. 이번 개편(HUD·균열·예고 장판)이 함께 쓴다."""
import os, json, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
OUT = os.path.join(ROOT, "assets3d", "ui", "overhaul")                       # 원본 보관
UNITY = os.path.join(ROOT, "unity", "Assets", "Resources", "Sprites", "overhaul")  # 코드팀이 바로 읽는 자리
S = 4  # 그릴 때 배율

# 색 토큰(docs/art/palette-tokens.json과 같은 값). 파혼 주황은 파혼 표시에만, 위험(예고)은 빨강 계열
HANJI = (243, 231, 211); INK = (42, 42, 56); NAVY = (22, 33, 62); ABYSS = (15, 23, 41); LINE = (59, 76, 122)
GOLD = (212, 169, 78); RED = (232, 92, 65); TEAL = (95, 227, 192); ORANGE = (232, 104, 58); CHAIN = (191, 232, 255)
SEAL = (181, 71, 63)  # 붉은 인 — 체력 막대용(예고 장판 빨강과 구분)

MANIFEST = {}

def canvas(w, h):
    return Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))

def rgba(c, a=255): return tuple(c) + (int(a),)

def rrect(d, box, r, fill=None, outline=None, width=0):
    x0, y0, x1, y1 = [v * S for v in box]
    d.rounded_rectangle([x0, y0, x1 - 1, y1 - 1], radius=r * S, fill=fill, outline=outline, width=int(width * S))

def line(d, pts, fill, width):
    d.line([(x * S, y * S) for x, y in pts], fill=fill, width=max(1, int(width * S)), joint="curve")

def poly(d, pts, fill=None, outline=None, width=0):
    d.polygon([(x * S, y * S) for x, y in pts], fill=fill)
    if outline: d.line([(x * S, y * S) for x, y in pts] + [(pts[0][0] * S, pts[0][1] * S)], fill=outline, width=max(1, int(width * S)), joint="curve")

def ellipse(d, box, fill=None, outline=None, width=0):
    d.ellipse([v * S for v in box], fill=fill, outline=outline, width=int(width * S))

def grad_v(w, h, top, bot, a_top=255, a_bot=255):
    """위→아래로 색이 변하는 판(4배 크기)"""
    t = np.linspace(0, 1, h * S)[:, None, None]
    c = np.array(top, np.float32) * (1 - t) + np.array(bot, np.float32) * t
    a = (a_top * (1 - t) + a_bot * t)
    arr = np.concatenate([np.broadcast_to(c, (h * S, w * S, 3)), np.broadcast_to(a, (h * S, w * S, 1))], axis=2)
    return Image.fromarray(arr.astype(np.uint8), "RGBA")

def mask_of(im_draw_fn, w, h):
    m = Image.new("L", (w * S, h * S), 0); im_draw_fn(ImageDraw.Draw(m)); return m

def finish(im, w, h):
    """4배 그림 → 정확한 w×h 1배"""
    return im.resize((w, h), Image.LANCZOS)

def save(im4, name, folder, w, h, note="", pivot=None, nine=None, scale_note="", x2=True):
    """4배 그림을 1배·@2x로 저장하고 manifest에 적는다. 원본은 assets3d/ui/overhaul/<folder>/, 복사본은 유니티 Resources 아래."""
    for base in (OUT, UNITY):
        os.makedirs(os.path.join(base, folder), exist_ok=True)
        im4.resize((w, h), Image.LANCZOS).save(os.path.join(base, folder, name + ".png"))
        if x2: im4.resize((w * 2, h * 2), Image.LANCZOS).save(os.path.join(base, folder, name + "@2x.png"))
    MANIFEST[f"{folder}/{name}"] = {"size": [w, h], "note": note, **({"pivot": pivot} if pivot else {}), **({"nine_slice": nine} if nine else {}), **({"scale": scale_note} if scale_note else {})}

def dump_manifest(fname="_manifest.json"):
    p = os.path.join(OUT, fname)
    old = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    old.update(MANIFEST)
    json.dump(old, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

def luma(im):
    """알파로 가중한 평균 밝기(0~255). 천도·파혼 칸 밝기 맞춤 검사용"""
    a = np.asarray(im.convert("RGBA"), np.float32); w = a[..., 3:4] / 255
    y = (a[..., 0] * .299 + a[..., 1] * .587 + a[..., 2] * .114)[..., None]
    return float((y * w).sum() / max(1e-6, w.sum()))

def over(bg, fg, xy=(0, 0)):
    bg = bg.copy(); bg.alpha_composite(fg, xy); return bg
