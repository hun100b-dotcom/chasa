"""미니맵 틀·미니맵 아이콘·큰 지도 틀·범례. 표준 명세(hud-controls-spec.md §2) 크기에 맞춘다.
미니맵 260×260(폰 200), 보이는 반경 30/40/60m, 아이콘 크기: 플레이어 14·일반 적 6·정예 8·보스 16·NPC 6·서낭당 14.
사용: python3 map_ui.py"""
import sys, os, math, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ui_lib as U
from ui_lib import *

def ring_gradient(size2, r_in, r_out, c0, c1):
    """원고리 안쪽→바깥으로 색이 바뀌는 띠(RGBA 레이어)"""
    ys, xs = np.mgrid[0:size2, 0:size2].astype(np.float32); c = (size2 - 1) / 2; d = np.sqrt((xs - c) ** 2 + (ys - c) ** 2)
    t = np.clip((d - r_in) / (r_out - r_in), 0, 1)[..., None]; col = np.array(c0, np.float32) * (1 - t) + np.array(c1, np.float32) * t
    a = ((d >= r_in) & (d <= r_out)).astype(np.float32); a = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)), np.float32) / 255
    return Image.fromarray(np.dstack([col, a * 255]).astype(np.uint8), "RGBA")

def minimap_frame(inner, shape="round"):
    """inner = 안쪽 구멍 지름(px, 1배). 캔버스 = inner + 40. 구멍은 완전 투명, 띠는 바깥으로 갈수록 먹→금→한지."""
    can = inner + 40; S2 = can * 2; R = inner  # 2배 그림에서 구멍 반지름 = 1배 지름(inner)
    im = Image.new("RGBA", (S2, S2), (0, 0, 0, 0)); c = S2 / 2
    if shape == "round":
        sh = Image.new("RGBA", (S2, S2), (0, 0, 0, 0)); ImageDraw.Draw(sh).ellipse([c - R - 40, c - R - 30, c + R + 40, c + R + 50], fill=(6, 8, 18, 150)); sh = sh.filter(ImageFilter.GaussianBlur(10)); hole0 = Image.new('L', (S2, S2), 255); ImageDraw.Draw(hole0).ellipse([c - R, c - R, c + R, c + R], fill=0); sh.putalpha(ImageChops.multiply(sh.split()[3], hole0)); im.alpha_composite(sh)
        # 띠: 바깥 먹(검정 아님, 도포 먹) → 금 → 한지 안쪽선
        im.alpha_composite(ring_gradient(S2, R, R + 8, HANJI, HANJI_D))                    # 안쪽 한지 선
        im.alpha_composite(ring_gradient(S2, R + 8, R + 26, (232, 196, 108), (180, 138, 52)))   # 금 띠
        im.alpha_composite(ring_gradient(S2, R + 26, R + 32, INK, (20, 20, 30)))              # 바깥 먹 테
        # 금 띠 위 눈금(15° 마다 짧게, 90° 마다 길게)
        tk = Image.new("RGBA", (S2, S2), (0, 0, 0, 0)); td = ImageDraw.Draw(tk)
        for k in range(24):
            a = math.radians(k * 15 - 90); long_ = k % 6 == 0; r0 = R + 10; r1 = R + (24 if long_ else 18)
            td.line([(c + math.cos(a) * r0, c + math.sin(a) * r0), (c + math.cos(a) * r1, c + math.sin(a) * r1)], fill=(110, 78, 24, 230), width=3 if long_ else 2)
        im.alpha_composite(tk)
        # 안쪽 그늘(지도 가장자리가 틀과 자연스럽게 붙게)
        ys, xs = np.mgrid[0:S2, 0:S2].astype(np.float32); d = np.sqrt((xs - c + 0.5) ** 2 + (ys - c + 0.5) ** 2)
        inner_sh = np.clip((d - (R - 26)) / 26, 0, 1) ** 1.6 * 0.55 * (d <= R)
        lay = np.dstack([np.ones_like(d) * ABYSS[0], np.ones_like(d) * ABYSS[1], np.ones_like(d) * ABYSS[2], inner_sh * 255]).astype(np.uint8); im.alpha_composite(Image.fromarray(lay, "RGBA"))
        # 방위: 북쪽에 붉은 도장(北), 동·남·서 작은 금 마름모
        sl = seal_mark(44, "北", RED); im.alpha_composite(sl, (int(c - 22), int(c - R - 32 - 6)))
        for ang in (0, 90, 180):
            a = math.radians(ang); x = c + math.cos(a) * (R + 17); y = c + math.sin(a) * (R + 17)
            ImageDraw.Draw(im).polygon([(x, y - 8), (x + 7, y), (x, y + 8), (x - 7, y)], fill=INK + (255,), outline=(255, 226, 150, 255))
    else:   # 모서리 둥근 사각
        rad = 40; x0 = 40; x1 = S2 - 40
        sh = Image.new("RGBA", (S2, S2), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([x0 - 6, x0 + 2, x1 + 6, x1 + 14], radius=rad + 8, fill=(6, 8, 18, 150)); im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([x0 - 32, x0 - 32, x1 + 32, x1 + 32], radius=rad + 32, fill=INK + (255,))
        d.rounded_rectangle([x0 - 26, x0 - 26, x1 + 26, x1 + 26], radius=rad + 26, fill=(190, 148, 62, 255))
        d.rounded_rectangle([x0 - 8, x0 - 8, x1 + 8, x1 + 8], radius=rad + 8, fill=HANJI + (255,))
        hole = Image.new("L", (S2, S2), 0); ImageDraw.Draw(hole).rounded_rectangle([x0, x0, x1, x1], radius=rad, fill=255); a = np.asarray(im.split()[3], np.float32) * (1 - np.asarray(hole, np.float32) / 255); im.putalpha(Image.fromarray(a.astype(np.uint8)))
        sl = seal_mark(34, "北", RED); im.alpha_composite(sl, (int(c - 17), 3))
    return im

def circle_mask(inner):
    can = inner + 40; S2 = can * 2; m = Image.new("RGBA", (S2, S2), (0, 0, 0, 0)); c = S2 / 2; ImageDraw.Draw(m).ellipse([c - inner, c - inner, c + inner, c + inner], fill=(255, 255, 255, 255)); return m

# ── 아이콘(2배 128px 칸에 그림) ─────────────────────────────────────────────
OUT = (16, 20, 38, 255)
def icon_canvas(): im = Image.new("RGBA", (128, 128), (0, 0, 0, 0)); return im, ImageDraw.Draw(im)

def ic_me():
    im, d = icon_canvas(); pts = [(64, 12), (104, 108), (64, 86), (24, 108)]
    d.polygon(pts, fill=OUT); d.polygon([(64, 24), (94, 98), (64, 80), (34, 98)], fill=(255, 255, 255, 255)); d.polygon([(64, 80), (94, 98), (64, 92), (34, 98)], fill=RED + (255,)); d.polygon([(64, 24), (64, 80), (34, 98)], fill=(228, 232, 240, 255)); return im
def ic_dot(col, r=34, ring=False, spikes=False):
    im, d = icon_canvas(); c = 64
    if spikes:
        for k in range(8):
            a = math.radians(k * 45); d.polygon([(c + math.cos(a - .22) * 40, c + math.sin(a - .22) * 40), (c + math.cos(a) * 58, c + math.sin(a) * 58), (c + math.cos(a + .22) * 40, c + math.sin(a + .22) * 40)], fill=OUT)
    d.ellipse([c - r - 8, c - r - 8, c + r + 8, c + r + 8], fill=OUT); d.ellipse([c - r, c - r, c + r, c + r], fill=col + (255,))
    if ring: d.ellipse([c - r + 14, c - r + 14, c + r - 14, c + r - 14], outline=(255, 232, 220, 255), width=6)
    return im
def ic_boss():
    im = seal_mark(112, "魁", (190, 44, 38)); out = Image.new("RGBA", (128, 128), (0, 0, 0, 0)); bg = Image.new("RGBA", (128, 128), (0, 0, 0, 0)); ImageDraw.Draw(bg).rounded_rectangle([4, 4, 123, 123], radius=14, fill=OUT)
    out.alpha_composite(bg); out.alpha_composite(im, (8, 8)); return out
def ic_soul(col, named=False):
    im, d = icon_canvas()
    def drop(off, fill):
        pts = [];
        for k in range(0, 360, 12):
            a = math.radians(k); r = 30 + off; pts.append((64 + math.cos(a) * r, 78 + math.sin(a) * r))
        d.polygon(pts, fill=fill); d.polygon([(64, 12 - off), (64 + 26 + off, 66), (64 - 26 - off, 66)], fill=fill)
    drop(7, OUT); drop(0, col + (255,)); d.ellipse([52, 70, 62, 80], fill=OUT); d.ellipse([68, 70, 78, 80], fill=OUT)
    if named: d.ellipse([20, 28, 108, 116], outline=GOLD + (255,), width=7); d.polygon([(64, 4), (70, 16), (58, 16)], fill=GOLD + (255,))
    return im
def ic_npc():
    im, d = icon_canvas(); g = (255, 214, 96, 255)
    d.ellipse([14, 68, 114, 98], fill=OUT); d.ellipse([34, 18, 94, 88], fill=OUT); d.ellipse([20, 72, 108, 94], fill=g); d.ellipse([40, 24, 88, 82], fill=g); d.rectangle([40, 70, 88, 80], fill=(150, 108, 30, 255)); d.ellipse([54, 94, 74, 112], fill=OUT); return im
def ic_quest(gold=True):
    im, d = icon_canvas(); d.ellipse([8, 8, 120, 120], fill=OUT); d.ellipse([18, 18, 110, 110], fill=GOLD + (255,)); d.rounded_rectangle([57, 32, 71, 72], radius=6, fill=OUT); d.ellipse([56, 82, 72, 98], fill=OUT); return im
def ic_arrow(col, double=False):
    im, d = icon_canvas()
    for k in ((0, 14) if double else (0,)):
        d.polygon([(64, 14 + k), (112, 70 + k), (92, 70 + k), (64, 38 + k), (36, 70 + k), (16, 70 + k)], fill=OUT)
        d.polygon([(64, 28 + k), (98, 66 + k), (88, 66 + k), (64, 46 + k), (40, 66 + k), (30, 66 + k)], fill=col + (255,))
    return im
def ic_seonang():
    im, d = icon_canvas(); gr = (150, 150, 158, 255)
    d.polygon([(64, 8), (120, 110), (8, 110)], fill=OUT)
    for (x0, y0, x1, y1) in ((26, 78, 102, 106), (40, 52, 88, 80), (52, 28, 76, 54)): d.rounded_rectangle([x0, y0, x1, y1], radius=10, fill=gr, outline=OUT, width=5)
    d.polygon([(60, 24), (76, 24), (88, 62), (76, 58)], fill=RED + (255,)); d.polygon([(64, 28), (72, 28), (80, 40), (68, 42)], fill=(255, 226, 150, 255)); return im
def ic_cave():
    im, d = icon_canvas(); d.pieslice([8, 22, 120, 134], 180, 360, fill=OUT); d.rectangle([8, 78, 120, 108], fill=OUT); d.pieslice([24, 38, 104, 118], 180, 360, fill=(70, 62, 78, 255)); d.rectangle([24, 78, 104, 104], fill=(70, 62, 78, 255)); d.pieslice([40, 52, 88, 100], 180, 360, fill=(14, 12, 24, 255)); d.rectangle([40, 76, 88, 104], fill=(14, 12, 24, 255)); return im
def ic_bridge():
    im, d = icon_canvas(); d.rounded_rectangle([6, 44, 122, 84], radius=14, fill=OUT); d.rounded_rectangle([14, 52, 114, 76], radius=8, fill=(190, 184, 170, 255)); d.arc([26, 70, 102, 118], 180, 360, fill=OUT, width=9); d.line([(30, 56), (30, 74), (64, 74), (98, 74), (98, 56)], fill=(110, 104, 94, 255), width=3); return im
def ic_ferry():
    im, d = icon_canvas(); d.polygon([(8, 74), (120, 74), (100, 108), (28, 108)], fill=OUT); d.polygon([(18, 78), (110, 78), (94, 100), (34, 100)], fill=(140, 98, 58, 255)); d.rectangle([60, 18, 68, 78], fill=OUT); d.polygon([(68, 22), (104, 62), (68, 62)], fill=(240, 232, 214, 255), outline=OUT); return im
def ic_herb():
    im, d = icon_canvas(); d.ellipse([14, 44, 114, 120], fill=OUT); d.ellipse([22, 52, 106, 112], fill=(120, 84, 58, 255)); d.rounded_rectangle([34, 40, 94, 56], radius=8, fill=OUT); d.rounded_rectangle([40, 44, 88, 54], radius=6, fill=(160, 120, 86, 255))
    d.rectangle([100, 70, 124, 80], fill=OUT)
    for x in (50, 64, 78): d.arc([x - 8, 6, x + 8, 40], 90, 270, fill=(120, 214, 140, 255), width=6)
    return im
def ic_soulpath():
    """넋길 표식: 서낭당 혼불 줄(IP 점검: 둥근 문·돌 고리 금지). 가로 새끼줄에 보랏빛 혼불 셋이 매달린다. 먹 테두리로 작게 줄여도 읽힘."""
    im, d = icon_canvas()
    d.line([(6, 44), (122, 44)], fill=OUT, width=14); d.line([(6, 44), (122, 44)], fill=(214, 190, 140, 255), width=6)   # 새끼줄
    for x in (26, 64, 102):   # 혼불: 물방울 모양(위가 뾰족)
        d.polygon([(x, 54), (x - 18, 92), (x - 12, 112), (x + 12, 112), (x + 18, 92)], fill=OUT)
        d.polygon([(x, 62), (x - 12, 92), (x - 8, 106), (x + 8, 106), (x + 12, 92)], fill=(154, 92, 255, 255))
        d.polygon([(x, 78), (x - 5, 94), (x, 102), (x + 5, 94)], fill=(236, 220, 255, 255))
    return im

ICONS = [("me", ic_me(), "플레이어(차사). 화살표만 돌아간다", 14), ("enemy", ic_dot((214, 48, 52)), "일반 적(붉은 점)", 6), ("elite", ic_dot((200, 40, 40), 30, True, True), "정예 적(붉은 점 + 둘레 가시). 주황은 파혼 전용이라 쓰지 않음", 8), ("boss", ic_boss(), "보스(붉은 도장 魁). 해골 대신 도장", 16),
         ("soul_fresh", ic_soul((191, 232, 255)), "혼: 갓 죽은", 8), ("soul_day", ic_soul((255, 204, 85)), "혼: 해 넘긴", 8), ("soul_old", ic_soul((140, 106, 90)), "혼: 오래된(갈회색)", 8), ("soul_lump", ic_soul((154, 92, 255)), "혼: 덩어리", 8),
         ("soul_named", ic_soul((191, 232, 255), True), "이름혼(금 고리·별)", 14), ("npc", ic_npc(), "NPC(갓 쓴 노란 점)", 8), ("quest", ic_quest(), "퀘스트 목표 !", 14), ("quest_arrow", ic_arrow(GOLD), "범위 밖 퀘스트 방향(테두리에 붙임)", 14),
         ("seonang", ic_seonang(), "서낭당·쉼터", 14), ("exit", ic_arrow(TEAL, True), "지역 출입구 화살표", 14), ("cave", ic_cave(), "굴 입구", 14), ("bridge", ic_bridge(), "다리", 14),
         ("ferry", ic_ferry(), "나루터", 14), ("herb", ic_herb(), "의원·약방", 14), ("soulpath", ic_soulpath(), "넋길 표식", 14)]

def build_icons():
    n = len(ICONS); cols = 5; rows = (n + cols - 1) // cols; atlas = Image.new("RGBA", (cols * 128, rows * 128), (0, 0, 0, 0)); meta = {}
    for i, (name, im, desc, px) in enumerate(ICONS):
        save(im, "icon_" + name, "map/icons", note=desc)
        x, y = (i % cols) * 128, (i // cols) * 128; atlas.alpha_composite(im, (x, y))
        meta[name] = {"uv_px": [x // 2, y // 2, 64, 64], "spec_size_px": px, "desc": desc}
    save(atlas, "minimap_icons_atlas", "map", note="64px 칸, 5열. icons/ 는 낱장 64px")
    json.dump({"cell_px": 64, "cols": cols, "atlas": "map/minimap_icons_atlas.png", "icons": meta, "note": "표준 명세 §2 크기(spec_size_px)로 줄여 쓴다. 64px 원본이라 작게 줄여도 가장자리 먹 테두리로 읽힘. 정예는 주황이 아니라 붉은+가시(주황=파혼 전용)."}, open(os.path.join(UI, "map", "minimap_icons.json"), "w"), ensure_ascii=False, indent=1)

# ── 큰 지도 틀 ─────────────────────────────────────────────────────────────
def bigmap_frame():
    W, H = 1536, 864; S2 = 2; im = Image.new("RGBA", (W * S2, H * S2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    def sc(v): return int(v * S2)
    # 한지 두루마리 몸통 + 먹 테두리
    body = hanji_tex(W * S2, H * S2, 31, 0.98); mask = Image.new("L", (W * S2, H * S2), 0); ImageDraw.Draw(mask).rounded_rectangle([sc(30), sc(30), sc(W - 30), sc(H - 30)], radius=sc(10), fill=255)
    paper = rgba(body, mask); im.alpha_composite(shadow(paper, (0, 8 * S2), 14 * S2, 0.55))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([sc(40), sc(40), sc(W - 40), sc(H - 40)], radius=sc(8), outline=INK + (255,), width=sc(2))
    d.rounded_rectangle([sc(46), sc(46), sc(W - 46), sc(H - 46)], radius=sc(6), outline=GOLD + (255,), width=sc(1.5))
    # 지도 창(투명) : 왼쪽 큰 창 + 오른쪽 범례 자리
    win = (sc(64), sc(96), sc(64 + 1104), sc(96 + 700))                          # 1104×700
    hole = Image.new("L", im.size, 0); ImageDraw.Draw(hole).rectangle(win, fill=255)
    # 창 테두리(먹 두 겹 + 안쪽 금선)
    for off, col, w in ((6, INK, 4), (2, GOLD, 3), (-2, INK, 2)):
        d.rectangle([win[0] - sc(off), win[1] - sc(off), win[2] + sc(off), win[3] + sc(off)], outline=col + (255,), width=sc(w) // 2 if w > 2 else sc(w))
    corner_marks(d, (win[0] - sc(10), win[1] - sc(10), win[2] + sc(10), win[3] + sc(10)), RED + (255,), sc(22), sc(4))
    # 위·아래 두루마리 축
    for y in (sc(14), sc(H - 14 - 26)):
        rod = Image.new("RGBA", (sc(W - 20), sc(26)), (0, 0, 0, 0)); rd = ImageDraw.Draw(rod)
        rd.rounded_rectangle([sc(26), 0, sc(W - 46), sc(26)], radius=sc(10), fill=(86, 52, 34, 255)); rd.rounded_rectangle([sc(26), sc(4), sc(W - 46), sc(10)], radius=sc(3), fill=(140, 94, 62, 255))
        for x in (sc(6), sc(W - 46)): rd.rounded_rectangle([x, sc(-2), x + sc(26), sc(28)], radius=sc(8), fill=GOLD + (255,), outline=(120, 86, 28, 255), width=sc(2))
        im.alpha_composite(rod, (sc(10), y))
    # 범례 칸 테두리
    lg = (sc(1196), sc(96), sc(1496), sc(96 + 700)); d.rectangle(lg, outline=INK + (255,), width=sc(1.5)); d.rectangle([lg[0] + sc(5), lg[1] + sc(5), lg[2] - sc(5), lg[3] - sc(5)], outline=GOLD + (200,), width=sc(1))
    # 제목 현판(글자는 따로)
    pl = Image.new("RGBA", (sc(300), sc(54)), (0, 0, 0, 0)); pd = ImageDraw.Draw(pl); pd.rounded_rectangle([0, 0, sc(300) - 1, sc(54) - 1], radius=sc(6), fill=NAVY + (255,), outline=GOLD + (255,), width=sc(2)); pd.rounded_rectangle([sc(6), sc(6), sc(294), sc(48)], radius=sc(4), outline=(212, 169, 78, 120), width=sc(1))
    for x in (sc(14), sc(286)): pd.ellipse([x - sc(4), sc(27) - sc(4), x + sc(4), sc(27) + sc(4)], fill=GOLD + (255,))
    im.alpha_composite(shadow(pl, (0, 4 * S2), 6 * S2, 0.5), (sc(W / 2 - 150) - 4, sc(36) - 0))
    a = np.asarray(im.split()[3], np.float32) * (1 - np.asarray(hole, np.float32) / 255); im.putalpha(Image.fromarray(a.astype(np.uint8)))   # 지도 창을 완전히 뚫음
    return im

def title_plate():
    from title_assets import brush_text
    W, H = 300, 54; im = Image.new("RGBA", (W * 2, H * 2), (0, 0, 0, 0)); m = brush_text("지도", 150, pad=8); m = m.resize((int(m.width * 0.5), int(m.height * 0.5)), Image.LANCZOS)
    col = Image.new("RGBA", m.size, HANJI + (255,)); col.putalpha(m); im.alpha_composite(col, ((W * 2 - m.width) // 2, (H * 2 - m.height) // 2)); return im

def legend_card():
    W, H = 300, 700; im = Image.new("RGBA", (W * 2, H * 2), (0, 0, 0, 0))
    body = hanji_tex(W * 2, H * 2, 55, 1.0); mk = rr_mask(W * 2, H * 2, 16); im.alpha_composite(rgba(body, mk)); d = ImageDraw.Draw(im)
    d.text((24 * 2, 18 * 2), "범례", font=font(30 * 2 // 2 + 6), fill=INK + (255,))
    d.line([(24 * 2, 62 * 2), ((W - 24) * 2, 62 * 2)], fill=GOLD + (255,), width=3)
    rows = [("me", "차사(나)"), ("enemy", "혼(적)"), ("elite", "독한 혼"), ("boss", "보스"), ("soul_named", "이름혼"), ("npc", "사람"), ("quest", "맡은 일"), ("seonang", "서낭당·쉼터"), ("herb", "의원"), ("cave", "굴 입구"), ("bridge", "다리"), ("ferry", "나루터"), ("exit", "고을 어귀")]
    ic = {n: im_ for n, im_, _, _ in ICONS}
    for i, (k, t) in enumerate(rows):
        y = (76 + i * 44) * 2; im.alpha_composite(ic[k].resize((64, 64), Image.LANCZOS), (24 * 2, y - 4)); d.text((72 * 2, y + 10), t, font=font(34), fill=INK + (255,))
    return im

def region_time_bar():
    """지역명·시각 줄: 폭 260×28 한지 띠 + 낮밤 아이콘 4개(20px 낱장)"""
    W, H = 260, 28; im = Image.new("RGBA", (W * 2, H * 2), (0, 0, 0, 0)); mk = rr_mask(W * 2, H * 2, 10); im.alpha_composite(rgba(hanji_tex(W * 2, H * 2, 71, 0.97), mk)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([1, 1, W * 2 - 2, H * 2 - 2], radius=10, outline=INK + (255,), width=3); d.rounded_rectangle([6, 6, W * 2 - 7, H * 2 - 7], radius=7, outline=GOLD + (200,), width=1)
    save(im, "region_time_bar", "hud", nine=[12, 12, 12, 12], note="지역명(18px, 왼쪽)·오른쪽에 낮밤 아이콘+시각. 폭 260×28")
    def sun(c):
        i = Image.new("RGBA", (40, 40), (0, 0, 0, 0)); dd = ImageDraw.Draw(i)
        for k in range(8): a = math.radians(k * 45); dd.line([(20 + math.cos(a) * 12, 20 + math.sin(a) * 12), (20 + math.cos(a) * 18, 20 + math.sin(a) * 18)], fill=c + (255,), width=3)
        dd.ellipse([10, 10, 30, 30], fill=c + (255,), outline=INK + (255,), width=2); return i
    def moon():
        i = Image.new("RGBA", (40, 40), (0, 0, 0, 0)); dd = ImageDraw.Draw(i); dd.ellipse([8, 6, 34, 32], fill=(210, 224, 255, 255), outline=INK + (255,), width=2); dd.ellipse([16, 2, 40, 28], fill=(0, 0, 0, 0));
        a = np.asarray(i).copy(); cut = Image.new("L", (40, 40), 0); ImageDraw.Draw(cut).ellipse([16, 2, 40, 28], fill=255); a[..., 3] = np.minimum(a[..., 3], 255 - np.asarray(cut)); return Image.fromarray(a, "RGBA")
    def horizon(c, up):
        i = Image.new("RGBA", (40, 40), (0, 0, 0, 0)); dd = ImageDraw.Draw(i); dd.pieslice([8, 14, 32, 38], 180, 360, fill=c + (255,), outline=INK + (255,), width=2); dd.line([(4, 26), (36, 26)], fill=INK + (255,), width=3)
        for k in (-1, 0, 1): dd.line([(20 + k * 9, 10), (20 + k * 13, 4)], fill=c + (255,), width=2)
        if not up: dd.polygon([(30, 6), (36, 12), (24, 12)], fill=INK + (255,))
        return i
    for nm, ic in (("sun", sun((255, 204, 85))), ("dusk", horizon((232, 130, 80), False)), ("moon", moon()), ("dawn", horizon((236, 168, 160), True))):
        save(ic.resize((80, 80), Image.LANCZOS), "time_" + nm, "hud/time", note="낮 7~16·저녁놀 16~19.5·밤 19.5~4.5·새벽 4.5~7 (grading hour_map 과 같음) 20px")

if __name__ == "__main__":
    for inner, nm in ((260, "pc"), (200, "phone")):
        save(minimap_frame(inner, "round"), f"minimap_frame_round_{nm}", "map", note=f"구멍 지름 {inner}px(캔버스 {inner+40}). 구멍은 투명 → 뒤에 지도 RenderTexture 를 깐다. 북쪽 붉은 도장이 위")
        save(circle_mask(inner), f"minimap_mask_{inner}", "map", note="지도를 둥글게 자르는 마스크(흰 원)")
    save(minimap_frame(260, "square"), "minimap_frame_square_pc", "map", note="모서리 둥근 사각형 대안(구멍 260)")
    build_icons()
    save(bigmap_frame(), "bigmap_frame", "map", note="1536×864(화면의 80%). 지도 창 1104×700 이 투명하게 뚫림(왼쪽 위 64,96). 오른쪽 범례 칸(1196,96, 300×700). 제목 현판 위치 가운데 위(618,36)")
    save(title_plate(), "bigmap_title", "map", note="현판 위 '지도' 붓글씨(300×54)"); save(legend_card(), "bigmap_legend", "map", note="범례 카드 300×700(한지+아이콘+글씨)")
    region_time_bar(); dump_manifest("ui_manifest.json"); print("완료", len(MANIFEST))
