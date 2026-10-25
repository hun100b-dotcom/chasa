"""장비 아이콘 3종(갓·띠·신) + 오방색 넋 아이콘 5종 + 인 15종 아이콘. 한지·먹 UI 스타일(코디 요청 2026-10-25, 지금은 노리개 그림을 빌려 쓰는 중).
규칙: 배경 투명(칸 틀은 코드가 slot_*.png로 깐다), 글자 없음, 먹 외곽선 + 한지·단청 금 포인트. 모든 PNG는 64px(1배)+@2x(128px). 512 캔버스에 그려 줄인다(가장자리 매끈).
인 15종: 두 넋 빛깔이 도장 윗면 왼·오른쪽 반쪽 색이 되고, 빛깔마다 작은 문양(청 잎·적 불꽃·황 산·백 초승달·흑 물결)을 반쪽에 새겼다. 같은 빛깔 둘이면 한 가지 색에 문양이 겹쳐 둘. 색맹을 위해 문양으로도 구분된다.
출력: assets3d/ui/icons/{equip,nok,in}/*.png, 목록 assets3d/ui/icons/icons_manifest.json, 한눈에 보기 assets3d/previews/icons_item_sheet.png. 실행: python3 tools/art3d/icons_item.py"""
import os, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); UI = os.path.join(HERE, "..", "..", "assets3d", "ui", "icons"); PV = os.path.join(HERE, "..", "..", "assets3d", "previews")
S = 512
INK = (38, 36, 48, 255); INK2 = (66, 62, 78, 255); HANJI = (243, 231, 211, 255); GOLD = (212, 169, 78, 255); GOLD_D = (160, 122, 48, 255); RED = (200, 70, 52, 255)
OB = {"청": (74, 140, 200), "적": (206, 78, 58), "황": (222, 174, 62), "백": (238, 234, 222), "흑": (46, 44, 60)}   # 오방색(청=푸른, 적=붉은, 황=누런, 백=흰, 흑=검은)
OBN = {"청": "푸른", "적": "붉은", "황": "누런", "백": "흰", "흑": "검은"}
def canvas(): im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); return im, ImageDraw.Draw(im)
def finish(im, shadow=True):
    if shadow:
        a = im.split()[3].filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.45)); sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sh.paste(Image.new("RGBA", im.size, (8, 10, 20, 255)), (0, 10), a); sh.alpha_composite(im); im = sh
    return im
def save(im, sub, name):
    d = os.path.join(UI, sub); os.makedirs(d, exist_ok=True); b = im.resize((128, 128), Image.LANCZOS)
    b.resize((64, 64), Image.LANCZOS).save(os.path.join(d, name + ".png"), optimize=True); b.save(os.path.join(d, name + "@2x.png"), optimize=True); return b
def lerp(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
def shade(c, k): return tuple(max(0, min(255, int(v * k))) for v in c[:3]) + (255,)
def ellipse(d, cx, cy, rx, ry, fill, outline=INK, w=9): d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=fill, outline=outline, width=w)

def gat():
    """흑립: 둥근 차양, 높은 원통 모자집, 말총 결, 양옆 갓끈(붉은 끈에 금 구슬)."""
    im, d = canvas()
    ellipse(d, 256, 330, 220, 96, INK, INK2, 10); ellipse(d, 256, 316, 200, 80, (30, 28, 38, 255), INK2, 6)
    for k in range(9): d.arc([256 - 190 + k * 8, 316 - 76 + k * 3, 256 + 190 - k * 8, 316 + 76 - k * 3], 200, 340, fill=(80, 76, 94, 255), width=3)   # 차양 말총 결
    d.polygon([(166, 300), (176, 150), (336, 150), (346, 300)], fill=INK, outline=INK2); ellipse(d, 256, 150, 80, 26, (52, 50, 66, 255), INK2, 7)
    d.rounded_rectangle([172, 250, 340, 278], radius=6, fill=(90, 70, 40, 255), outline=GOLD_D, width=4)                                         # 갓 밑 띠
    for sx in (-1, 1):
        x0 = 256 + sx * 170; d.line([(x0, 330), (256 + sx * 118, 408)], fill=RED, width=10)
        for i in range(4): ellipse(d, 256 + sx * (150 - i * 10), 352 + i * 18, 9, 9, GOLD, GOLD_D, 3)
    d.line([(190, 160), (204, 270)], fill=(120, 116, 140, 255), width=7)                                                                      # 윤기
    return finish(im)
def tti():
    """띠: 남색 허리띠가 비스듬히 감겼고 금실 줄무늬, 가운데 매듭과 두 갈래 끝자락."""
    im, d = canvas(); NAVY = (36, 56, 106, 255)
    d.polygon([(70, 190), (190, 120), (440, 300), (330, 400)], fill=NAVY, outline=INK)
    for off in (-34, 0, 34): d.line([(80 + off * 0.35, 220 + off * 0.7 - 20), (400 + off * 0.35, 330 + off * 0.7 - 90)], fill=GOLD, width=9) if False else None
    for k in (0.28, 0.5, 0.72): d.line([(70 + (190 - 70) * 0 + 120 * k, 190 + (120 - 190) * 0 - 70 * k * 0), (0, 0)], fill=NAVY, width=1) if False else None
    for k in (0.3, 0.5, 0.7):
        a = (70 + (330 - 70) * k, 190 + (400 - 190) * k); b = (190 + (440 - 190) * k, 120 + (300 - 120) * k); d.line([a, b], fill=GOLD, width=10)
    ellipse(d, 256, 262, 54, 54, (30, 46, 90, 255), INK, 9); ellipse(d, 256, 262, 24, 24, GOLD, GOLD_D, 5)                                      # 매듭
    d.polygon([(236, 300), (190, 440), (232, 424), (262, 330)], fill=NAVY, outline=INK); d.polygon([(278, 300), (338, 430), (296, 424), (262, 330)], fill=(30, 46, 90, 255), outline=INK)
    d.line([(214, 380), (222, 330)], fill=GOLD, width=6)
    return finish(im)
def sin():
    """신(가죽신): 옆모습, 코가 위로 말려 올라간 검은 신. 흰 바닥 줄과 금 문양, 발목 끈."""
    im, d = canvas()
    d.polygon([(80, 330), (92, 220), (130, 150), (250, 130), (330, 200), (450, 270), (446, 330)], fill=INK, outline=INK2)
    d.polygon([(92, 330), (446, 330), (440, 368), (100, 368)], fill=HANJI, outline=INK)                                                       # 흰 바닥
    d.arc([300, 150, 480, 330], 270, 40, fill=INK2, width=8)
    d.polygon([(120, 160), (240, 138), (256, 190), (130, 214)], fill=(70, 66, 86, 255), outline=INK2)                                         # 발목 덮개
    d.line([(150, 180), (230, 168)], fill=GOLD, width=8); d.line([(100, 260), (330, 250)], fill=(88, 84, 104, 255), width=5)
    for k in range(5): ellipse(d, 160 + k * 46, 292, 8, 8, GOLD, GOLD_D, 3)
    d.line([(100, 330), (446, 330)], fill=INK, width=8)
    return finish(im)
EQUIP = [("equip_gat", gat, "갓(흑립)"), ("equip_tti", tti, "띠"), ("equip_sin", sin, "신")]

def nok(c, glow=True):
    """넋 아이콘: 둥근 혼불 덩이에 꼬리 불꽃, 한가운데 밝은 심. 빛깔은 오방색."""
    col = OB[c]; im, d = canvas(); g = Image.new("RGBA", (S, S), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    ex = (230, 230, 240) if c == "흑" else col
    if glow: gd.ellipse([56, 76, 456, 476], fill=tuple(ex) + (120,)); g = g.filter(ImageFilter.GaussianBlur(34)); im.alpha_composite(g)
    d.polygon([(256, 40), (330, 190), (360, 260), (256, 300), (152, 260), (182, 190)], fill=tuple(col) + (255,), outline=INK)                    # 꼬리 불꽃
    ellipse(d, 256, 320, 130, 130, tuple(shade(col, 0.92)), INK, 11)                                                                           # 몸
    ellipse(d, 256, 330, 84, 84, tuple(lerp(col, (255, 255, 255), 0.35)) + (255,), None, 0)
    ellipse(d, 256, 340, 40, 40, (255, 255, 250, 255) if c != "흑" else (150, 150, 180, 255), None, 0)                                          # 심
    d.arc([160, 230, 300, 360], 200, 280, fill=(255, 255, 255, 170), width=10)                                                                   # 윤기
    return finish(im, shadow=False)

def emblem(d, kind, cx, cy, r, col, w=8):
    """문양(반쪽 안에 새김): 청 잎, 적 불꽃, 황 산, 백 초승달, 흑 물결."""
    if kind == "청": d.polygon([(cx, cy - r), (cx + r * 0.6, cy), (cx, cy + r), (cx - r * 0.6, cy)], outline=col, width=w); d.line([(cx, cy - r), (cx, cy + r)], fill=col, width=w - 2)
    elif kind == "적": d.polygon([(cx, cy - r), (cx + r * 0.5, cy), (cx + r * 0.3, cy + r * 0.8), (cx - r * 0.3, cy + r * 0.8), (cx - r * 0.5, cy)], outline=col, width=w); d.polygon([(cx, cy - r * 0.1), (cx + r * 0.2, cy + r * 0.5), (cx - r * 0.2, cy + r * 0.5)], fill=col)
    elif kind == "황": d.polygon([(cx - r * 0.9, cy + r * 0.7), (cx, cy - r * 0.8), (cx + r * 0.9, cy + r * 0.7)], outline=col, width=w); d.line([(cx - r * 0.45, cy + r * 0.1), (cx + r * 0.45, cy + r * 0.1)], fill=col, width=w - 2)
    elif kind == "백": d.arc([cx - r, cy - r, cx + r, cy + r], 40, 320, fill=col, width=w + 2); d.arc([cx - r * 0.55, cy - r * 0.85, cx + r * 1.15, cy + r * 0.85], 60, 300, fill=col, width=w + 2) if False else None
    else:
        for k in (-0.5, 0.1, 0.7): d.arc([cx - r, cy + r * k - r * 0.4, cx - r * 0.1, cy + r * k + r * 0.4], 180, 360, fill=col, width=w); d.arc([cx - r * 0.1, cy + r * k - r * 0.4, cx + r * 0.8, cy + r * k + r * 0.4], 0, 180, fill=col, width=w)
def seal(a, b, big=False):
    """인: 위에서 본 네모 도장. 윗면은 두 빛깔 반쪽(왼 a, 오른 b), 문양은 반쪽마다 한 개. 둘레는 금 테 + 먹 외곽선, 큰 인은 금 테가 두 겹."""
    im, d = canvas(); R = 190
    d.rounded_rectangle([256 - R - 20, 256 - R - 6, 256 + R + 20, 256 + R + 34], radius=40, fill=(70, 62, 52, 255), outline=INK, width=9)        # 도장 옆면(아래쪽에 살짝 보임)
    face = Image.new("RGBA", (S, S), (0, 0, 0, 0)); fd = ImageDraw.Draw(face); ca, cb = OB[a], OB[b]
    fd.rectangle([256 - R, 256 - R, 256, 256 + R], fill=tuple(ca) + (255,)); fd.rectangle([256, 256 - R, 256 + R, 256 + R], fill=tuple(cb) + (255,))
    m = Image.new("L", (S, S), 0); ImageDraw.Draw(m).rounded_rectangle([256 - R, 256 - R, 256 + R, 256 + R], radius=34, fill=255); face.putalpha(m); im.alpha_composite(face); d = ImageDraw.Draw(im)
    d.rounded_rectangle([256 - R, 256 - R, 256 + R, 256 + R], radius=34, outline=INK, width=11); d.rounded_rectangle([256 - R + 16, 256 - R + 16, 256 + R - 16, 256 + R - 16], radius=24, outline=GOLD, width=7)
    if big: d.rounded_rectangle([256 - R + 34, 256 - R + 34, 256 + R - 34, 256 + R - 34], radius=16, outline=GOLD_D, width=5)
    def ink_for(c): return (30, 28, 40, 255) if sum(OB[c]) > 330 else (245, 240, 228, 255)
    if a == b: emblem(d, a, 256 - 78, 256, 66, ink_for(a)); emblem(d, b, 256 + 78, 256, 66, ink_for(b))
    else: emblem(d, a, 256 - 88, 256, 70, ink_for(a)); emblem(d, b, 256 + 88, 256, 70, ink_for(b))
    d.line([(256, 256 - R + 20), (256, 256 + R - 20)], fill=INK, width=7)
    return finish(im)
COMBOS = [("청", "청", "날랜 인"), ("적", "적", "센 인"), ("황", "황", "굳은 인"), ("백", "백", "쇠 인"), ("흑", "흑", "깊은 인"), ("청", "적", "서두름 인"), ("청", "황", "길 인"), ("청", "백", "바람 인"),
          ("청", "흑", "물길 인"), ("적", "황", "불씨 인"), ("적", "백", "칼끝 인"), ("적", "흑", "그을음 인"), ("황", "백", "버팀 인"), ("황", "흑", "무덤 인"), ("백", "흑", "찬 인")]
def main():
    man = {}; tiles = []
    for name, fn, label in EQUIP: b = save(fn(), "equip", name); man["equip/" + name] = {"label": label, "size_px": 64, "x2": name + "@2x.png"}; tiles.append(b)
    for c in "청적황백흑":
        n = {"청": "blue", "적": "red", "황": "yellow", "백": "white", "흑": "black"}[c]; b = save(nok(c), "nok", "nok_" + n); man["nok/nok_" + n] = {"label": OBN[c] + " 넋", "color": "#%02X%02X%02X" % OB[c], "size_px": 64}; tiles.append(b)
    for i, (a, b_, nm) in enumerate(COMBOS, 1):
        fn = f"in_{i:02d}_{a}{b_}"; b = save(seal(a, b_), "in", fn); man["in/" + fn] = {"label": nm, "combo": [OBN[a] + " 넋", OBN[b_] + " 넋"], "size_px": 64, "note": "큰 인은 같은 그림에 금 테 한 겹을 코드가 더 얹거나 in_big/ 를 쓴다"}; tiles.append(b)
        save(seal(a, b_, big=True), "in_big", fn + "_big")
    json.dump(man, open(os.path.join(UI, "icons_manifest.json"), "w"), ensure_ascii=False, indent=1)
    cols = 8; rows = (len(tiles) + cols - 1) // cols; sheet = Image.new("RGBA", (cols * 140, rows * 140), (22, 33, 62, 255))
    for k, t in enumerate(tiles): sheet.alpha_composite(t, ((k % cols) * 140 + 6, (k // cols) * 140 + 6))
    sheet.convert("RGB").save(os.path.join(PV, "icons_item_sheet.png")); print(len(tiles), "개")
if __name__ == "__main__": main()
