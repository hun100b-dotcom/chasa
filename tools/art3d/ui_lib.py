"""HUD·지도 그림 공통 도구(한지·먹·단청 금). 모든 그림은 2배로 그려 줄여 저장하고(가장자리 매끈), 1배·2배 두 벌을 낸다.
색은 docs/art/palette-tokens.json 의 토큰을 그대로 쓴다."""
import os, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)); A3 = os.path.join(HERE, "..", "..", "assets3d")
UI = os.path.join(A3, "ui"); os.makedirs(UI, exist_ok=True)
FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
# 색 토큰
HANJI = (243, 231, 211); HANJI_D = (226, 211, 184); INK = (42, 42, 56); NAVY = (22, 33, 62); ABYSS = (15, 23, 41)
GOLD = (212, 169, 78); RED = (232, 92, 65); TEAL = (95, 227, 192); VIOLET = (201, 176, 255); BLUE = (79, 134, 194); CHAIN = (191, 232, 255)
MANIFEST = {}

def font(sz): return ImageFont.truetype(FONT, sz)
def noise(w, h, cell, seed):
    r = np.random.RandomState(seed); g = r.rand(max(2, h // cell + 2), max(2, w // cell + 2)).astype(np.float32)
    return np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255

def hanji_tex(w, h, seed=1, tone=1.0):
    """한지 질감 RGB 배열(0~1): 큰 얼룩 + 가는 섬유"""
    base = np.array(HANJI, np.float32) / 255 * tone
    n = noise(w, h, max(8, w // 6), seed) * 0.5 + noise(w, h, max(4, w // 18), seed + 1) * 0.3 + noise(w, h, 3, seed + 2) * 0.2
    return np.clip(base[None, None, :] * (0.92 + 0.14 * n[..., None]), 0, 1)

def rr_mask(w, h, r, inset=0):
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([inset, inset, w - 1 - inset, h - 1 - inset], radius=r, fill=255); return m

def rgba(arr, mask):
    a = np.asarray(mask, np.float32)[..., None] / 255 if not isinstance(mask, np.ndarray) else mask[..., None]
    return Image.fromarray(np.dstack([np.clip(arr, 0, 1) * 255, a[..., 0] * 255]).astype(np.uint8), "RGBA")

def stroke(im, shape_fn, color, width, alpha=255):
    """shape_fn(draw, fill, width) 로 도형을 그려 im 위에 알파 합성"""
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); shape_fn(ImageDraw.Draw(lay), tuple(color) + (alpha,), width); im.alpha_composite(lay); return im

def shadow(im, off=(0, 3), blur=5, alpha=0.5, pad=0):
    a = im.split()[3].filter(ImageFilter.GaussianBlur(blur)); a = a.point(lambda v: int(v * alpha))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sh.paste(Image.new("RGBA", im.size, (8, 10, 20, 255)), off, a); sh.alpha_composite(im); return sh

def save(img, name, sub="", nine=None, note=""):
    """img: 2배 크기로 그린 RGBA. 1배(절반)와 2배 두 벌 저장, 매니페스트에 기록"""
    d = os.path.join(UI, sub); os.makedirs(d, exist_ok=True)
    w, h = img.size[0] // 2, img.size[1] // 2
    img.resize((w, h), Image.LANCZOS).save(os.path.join(d, name + ".png"), optimize=True)
    img.save(os.path.join(d, name + "@2x.png"), optimize=True)
    MANIFEST[(sub + "/" if sub else "") + name] = {"size_px": [w, h], "x2": name + "@2x.png", **({"nine_slice_px": nine} if nine else {}), **({"note": note} if note else {})}

def dump_manifest(fn):
    p = os.path.join(UI, fn); old = json.load(open(p)) if os.path.exists(p) else {}
    old.update(MANIFEST); json.dump(old, open(p, "w"), ensure_ascii=False, indent=1)

def ink_line(d, pts, color, width):
    d.line(pts, fill=color, width=width, joint="curve")

def corner_marks(d, box, color, ln, w, gap=0):
    x0, y0, x1, y1 = box
    for (cx, cy, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        d.line([(cx, cy + sy * ln), (cx, cy), (cx + sx * ln, cy)], fill=color, width=w)

def seal_mark(size, ch="印", color=RED, ink=None, seed=3):
    """작은 붉은 도장(두 배 크기로 그림). 글자는 한지색으로 파낸 모양."""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(im); d.rounded_rectangle([1, 1, size - 2, size - 2], radius=max(2, size // 12), fill=tuple(color) + (255,))
    f = font(int(size * 0.7)); bb = f.getbbox(ch); d.text(((size - (bb[0] + bb[2])) / 2, (size - (bb[1] + bb[3])) / 2), ch, font=f, fill=HANJI + (255,))
    return im
