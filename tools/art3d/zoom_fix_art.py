"""줌이 멀어져(13/19/24 m) 화면 고정 크기 요소가 작아 보이는 문제를 고치는 그림: 맺힘 막대 L판(slot이 8→14px로 굵음).
왜: 코드(JudgeSystem 머리 위 막대)는 틀 96×14·홈 88×8을 일반 혼 64px / 이름 있는 혼 80px로 줄여 그린다 → 홈 높이가 5~6px. PC에서는 겨우 보이고,
 폰(같은 1080 픽셀이지만 화면이 물리적으로 1/4)에서는 0.3mm라 선처럼 보인다. 같은 문법·색으로 홈만 굵게 새로 그린다(이름 끝에 _L).
규격(코드가 읽는 값): 틀 96×22 → 홈 (4,4) 88×14 / 금테 틀 96×22 / 덩어리 두 줄 틀 96×44 → 홈 (4,4)와 (4,26) 각 88×14. fill·ghost 88×14.
저장: assets3d/ui/bars_L/ + unity Sprites/ui/ . 실행: python3 zoom_fix_art.py"""
import os
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "..", "..", "assets3d", "ui", "bars_L"); UNITY = os.path.join(HERE, "..", "..", "unity", "Assets", "Resources", "Sprites", "ui")
os.makedirs(OUT, exist_ok=True); Q = 4
HANJI = (243, 231, 211); GOLD = (212, 169, 78); NAVY = (22, 33, 62); ABYSS = (10, 16, 34)

def frame(h, stroke, slots, sw=2.0):
    W = 96 * Q; H = h * Q; im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([1.5 * Q, 1.5 * Q, W - 1.5 * Q, H - 1.5 * Q], radius=7 * Q, fill=ABYSS + (217,), outline=stroke + (255,), width=int(sw * Q))
    for (x, y) in slots: d.rounded_rectangle([x * Q, y * Q, (x + 88) * Q, (y + 14) * Q], radius=4 * Q, fill=NAVY + (255,))
    return im.resize((96, h), Image.LANCZOS)
def fill():
    W, H = 88 * Q, 14 * Q; g = Image.new("RGBA", (W, H)); px = g.load()
    for y in range(H):
        t = y / (H - 1); c = tuple(int(a + (b - a) * t) for a, b in zip((230, 246, 255), (127, 184, 224)))   # 위 #E6F6FF → 아래 #7FB8E0
        for x in range(W): px[x, y] = c + (255,)
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, W - 1, H - 1], radius=4 * Q, fill=255); g.putalpha(m); return g.resize((88, 14), Image.LANCZOS)
def ghost():
    W, H = 88 * Q, 14 * Q; g = Image.new("RGBA", (W, H), HANJI + (int(255 * 0.65),)); m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, W - 1, H - 1], radius=4 * Q, fill=255)
    a = Image.new("L", (W, H), int(255 * 0.65)); a.paste(0, mask=Image.eval(m, lambda v: 255 - v)); g.putalpha(a); return g.resize((88, 14), Image.LANCZOS)

FILES = {"ui_bar_gyeol_frame_L": frame(22, HANJI, [(4, 4)]), "ui_bar_gyeol_frame_gold_L": frame(22, GOLD, [(4, 4)], 2.4), "ui_bar_gyeol_frame_x2_L": frame(44, HANJI, [(4, 4), (4, 26)]),
         "ui_bar_gyeol_fill_L": fill(), "ui_bar_gyeol_ghost_L": ghost()}
if __name__ == "__main__":
    for n, im in FILES.items():
        im.save(os.path.join(OUT, n + ".png"), optimize=True)
        if os.path.isdir(UNITY): im.save(os.path.join(UNITY, n + ".png"), optimize=True)
        print(n, im.size)
