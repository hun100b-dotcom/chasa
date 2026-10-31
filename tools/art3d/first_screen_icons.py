"""처음 10분 첫 화면 요소 보강(hud-controls-spec v1.4 §9-2 '천도▲ 실선 / 파혼✕ 점선·톱니' 규칙 + 50° 카메라 점검 결과).
점검에서 비어 있던 것: ① 무릎 꿇은 혼 머리 위 월드 안내의 천도/파혼 모양 아이콘 ② 처결 선택 카드 둘(280×96) ③ 일반 혼 머리 위 맺힘 막대(거센 혼 화면 막대만 있었음, 덩어리는 두 줄)
 ④ 미니맵: 처결 대기 중인 혼 표시 ⑤ 넋길 닫힘(낮)·열림(밤) 구분 ⑥ 넋길 안내 아이콘.
규칙: 한지·먹·단청 금 언어. 주황(#E8683A)은 파혼 전용. 천도=청록 ▲ + 실선 테두리 / 파혼=주황 ✕ 조각 + 점선·톱니 테두리 — 색을 못 봐도 모양으로 갈린다. 두 카드는 평균 밝기를 맞췄다. 글자는 그림에 없다(코드가 얹음).
산출(assets3d/ui/first10/, 1배+@2x): prompt_tendo·prompt_pahon(48²) · exec_card_tendo·exec_card_pahon(280×96) · bind_world_frame(96×12)·bind_world_frame2(96×22)·bind_world_fill(88×6) · prompt_soulpath(48²)
 + assets3d/ui/map/icons/icon_soul_wait·icon_soulpath_off(64²). 실행: python3 first_screen_icons.py"""
import os, math, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import ui_lib as U
from ui_lib import HANJI, INK, NAVY, ABYSS, GOLD, TEAL, VIOLET, save
from first10_art import new, glow_layer, over, S, ORANGE, PURPLE, SUB

DEEP_TEAL = (38, 150, 126); DEEP_OR = (176, 70, 32)
def flame(d, cx, cy, h, fill, outline=None, ow=0):
    """위로 오르는 불꽃(▲ 꼴): 아래가 둥글게 넓고 끝이 한쪽으로 휜 물방울. 끝이 뾰족해 쿼터뷰·작은 크기에서도 ▲로 읽힌다."""
    w = h * 0.7; pts = []
    for i in range(0, 21):          # 왼쪽 가장자리 아래→위
        t = i / 20; half = (w / 2) * math.sin(math.pi * min(1, t ** 0.62)) * (1 - t) ** 0.25; pts.append((cx - half + w * 0.16 * t * t, cy + h / 2 - t * h))
    for i in range(20, -1, -1):     # 오른쪽 위→아래
        t = i / 20; half = (w / 2) * math.sin(math.pi * min(1, t ** 0.62)) * (1 - t) ** 0.25; pts.append((cx + half + w * 0.16 * t * t, cy + h / 2 - t * h))
    if outline: d.polygon(pts, fill=outline, outline=outline, width=int(ow * 2))
    d.polygon(pts, fill=fill)
def dashed_ring(d, c, r, w, color, n=14, gap=0.45):
    """점선 고리(파혼): n개 호 사이를 비운다."""
    for k in range(n):
        a0 = k / n * 360; a1 = a0 + 360 / n * (1 - gap)
        d.arc([c - r, c - r, c + r, c + r], a0, a1, fill=color, width=int(w))
def saw_ring(d, c, r, color):
    """톱니 테두리(파혼): 바깥으로 삐죽한 삼각 이빨."""
    n = 16
    for k in range(n):
        a = k / n * math.tau; b = (k + 0.5) / n * math.tau; a2 = (k + 1) / n * math.tau
        d.polygon([(c + math.cos(a) * r, c + math.sin(a) * r), (c + math.cos(b) * (r + 3.4 * S), c + math.sin(b) * (r + 3.4 * S)), (c + math.cos(a2) * r, c + math.sin(a2) * r)], fill=color)
def shard(d, pts, fill, outline):
    d.polygon(pts, fill=outline); cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
    d.polygon([(cx + (x - cx) * 0.72, cy + (y - cy) * 0.72) for x, y in pts], fill=fill)

def prompt_tendo(size=48):
    im = new(size, size); d = ImageDraw.Draw(im); c = size * S / 2
    d.ellipse([c - 21 * S, c - 21 * S, c + 21 * S, c + 21 * S], fill=ABYSS + (245,)); d.ellipse([c - 21 * S, c - 21 * S, c + 21 * S, c + 21 * S], outline=INK + (255,), width=int(3 * S))
    d.ellipse([c - 19 * S, c - 19 * S, c + 19 * S, c + 19 * S], outline=TEAL + (255,), width=int(3.2 * S))       # 실선 테두리
    im = over(im, glow_layer(im.size, lambda dd: flame(dd, c, c + 1 * S, 24 * S, 255), TEAL, 3 * S, 1.0)); d = ImageDraw.Draw(im)
    flame(d, c, c + 1 * S, 24 * S, TEAL + (255,), INK + (255,), 1.6 * S); flame(d, c, c + 4 * S, 12 * S, (225, 255, 247, 255))
    return im
def prompt_pahon(size=48):
    im = new(size, size); d = ImageDraw.Draw(im); c = size * S / 2
    saw_ring(d, c, 20 * S, INK + (255,)); d.ellipse([c - 21 * S, c - 21 * S, c + 21 * S, c + 21 * S], fill=ABYSS + (245,)); d.ellipse([c - 21 * S, c - 21 * S, c + 21 * S, c + 21 * S], outline=INK + (255,), width=int(3 * S))
    dashed_ring(d, c, 18 * S, 3.2 * S, ORANGE + (255,))                                                           # 점선 테두리
    # ✕ 꼴 깨진 조각 넷(끝이 삐죽, 가운데가 벌어짐)
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        o = 3.0 * S; pts = [(c + sx * o, c + sy * o), (c + sx * 15 * S, c + sy * 5 * S), (c + sx * 14 * S, c + sy * 14 * S), (c + sx * 5 * S, c + sy * 15 * S)]
        shard(d, pts, ORANGE + (255,), INK + (255,))
    return im
def prompt_soulpath(size=48):
    """넋길 안내: 혼불 줄(아래로 늘어진 줄 + 청록 혼불 셋) — 둥근 문 아님. 천도와 달리 작은 불꽃 셋이 줄에 매달린 모양."""
    im = new(size, size); d = ImageDraw.Draw(im); c = size * S / 2
    d.ellipse([c - 21 * S, c - 21 * S, c + 21 * S, c + 21 * S], fill=ABYSS + (245,)); d.ellipse([c - 21 * S, c - 21 * S, c + 21 * S, c + 21 * S], outline=INK + (255,), width=int(3 * S)); d.ellipse([c - 19 * S, c - 19 * S, c + 19 * S, c + 19 * S], outline=GOLD + (255,), width=int(2.4 * S))
    pts = [(c - 16 * S + t * 32 * S / 20, c - 4 * S + math.sin(t / 20 * math.pi) * 6 * S) for t in range(21)]
    d.line(pts, fill=INK + (255,), width=int(4.5 * S)); d.line(pts, fill=(168, 152, 104, 255), width=int(2.4 * S))
    for k, (fx, fy, hh) in enumerate(((c - 11 * S, c + 1 * S, 12), (c, c + 5 * S, 15), (c + 11 * S, c + 1 * S, 12))):
        im = over(im, glow_layer(im.size, lambda dd, fx=fx, fy=fy, hh=hh: flame(dd, fx, fy - hh * S * 0.5, hh * S, 255), VIOLET, 2.4 * S, 1.0)); d = ImageDraw.Draw(im)
        flame(d, fx, fy - hh * S * 0.5, hh * S, (154, 92, 255, 255), INK + (255,), 1.2 * S)
    return im

def exec_card(kind):
    """처결 선택 카드(첫 처결만 화면 하단 큰 카드 둘): 280×96. 왼쪽 큰 모양 아이콘 + 오른쪽은 코드가 글자('[E] 천도 — 보낸다')를 얹는 자리. 테두리: 천도 실선 / 파혼 점선."""
    w, h = 280, 96; im = new(w, h); d = ImageDraw.Draw(im); W, H = w * S, h * S
    col = TEAL if kind == "tendo" else ORANGE
    d.rounded_rectangle([0, 0, W - 1, H - 1], radius=14 * S, fill=NAVY + (238,), outline=INK + (255,), width=int(4 * S))
    if kind == "tendo": d.rounded_rectangle([4 * S, 4 * S, W - 5 * S, H - 5 * S], radius=11 * S, outline=col + (255,), width=int(3.4 * S))
    else:   # 점선 테두리: 변마다 짧은 선분
        def seg(x0, y0, x1, y1):
            L = math.hypot(x1 - x0, y1 - y0); n = int(L / (11 * S))
            for k in range(n):
                a, b = k / n, (k + 0.62) / n; d.line([(x0 + (x1 - x0) * a, y0 + (y1 - y0) * a), (x0 + (x1 - x0) * b, y0 + (y1 - y0) * b)], fill=col + (255,), width=int(3.4 * S))
        m = 4 * S; seg(m + 12 * S, m, W - m - 12 * S, m); seg(m + 12 * S, H - m, W - m - 12 * S, H - m); seg(m, m + 12 * S, m, H - m - 12 * S); seg(W - m, m + 12 * S, W - m, H - m - 12 * S)
    ic = prompt_tendo(48) if kind == "tendo" else prompt_pahon(48); ic = ic.resize((int(64 * S), int(64 * S)), Image.LANCZOS); im.alpha_composite(ic, (int(14 * S), int(16 * S)))
    d = ImageDraw.Draw(im); d.line([(88 * S, 18 * S), (88 * S, H - 18 * S)], fill=INK + (255,), width=int(2 * S))
    d.rounded_rectangle([98 * S, 14 * S, 134 * S, 38 * S], radius=5 * S, fill=HANJI + (255,), outline=INK + (255,), width=int(2 * S))   # 키 칸(코드가 E/R 글자)
    return im

def bind_world(rows=1):
    """일반 혼 머리 위 맺힘 막대(월드, 빌보드): 틀 96×12(덩어리는 두 줄 96×22) + 채움 88×6 보라. 1배 그대로 쓰면 50° 화면에서 폭 약 90px."""
    w, h = 96, 12 if rows == 1 else 22; im = new(w, h); d = ImageDraw.Draw(im); W, H = w * S, h * S
    d.rounded_rectangle([0, 0, W - 1, H - 1], radius=5 * S, fill=ABYSS + (235,), outline=INK + (255,), width=int(2 * S)); d.rounded_rectangle([2 * S, 2 * S, W - 3 * S, H - 3 * S], radius=3.5 * S, outline=HANJI + (150,), width=int(1 * S))
    if rows == 2: d.line([(5 * S, H / 2), (W - 5 * S, H / 2)], fill=INK + (255,), width=int(2 * S))
    return im
def bind_fill():
    im = new(88, 6); d = ImageDraw.Draw(im); W, H = 88 * S, 6 * S
    d.rounded_rectangle([0, 0, W - 1, H - 1], radius=2.5 * S, fill=PURPLE + (255,)); d.rounded_rectangle([0, 0, W - 1, H // 2], radius=2.5 * S, fill=(190, 150, 255, 255)); return im

def map_icon_soul_wait():
    """미니맵: 처결 대기 중인 혼 — 비어 있는 청록 고리 + 가운데 점(채운 점인 일반 혼과 모양이 다름). 고리가 줄어드는 느낌은 코드가 크기로."""
    im = Image.new("RGBA", (128, 128), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([14, 14, 114, 114], outline=INK + (255,), width=22); d.ellipse([24, 24, 104, 104], outline=TEAL + (255,), width=12); d.ellipse([52, 52, 76, 76], fill=INK + (255,)); d.ellipse([56, 56, 72, 72], fill=(225, 255, 247, 255))
    return im
def map_icon_soulpath_off():
    """낮에는 닫힌 넋길: 기존 icon_soulpath를 흐리게(회색 먹 + 반투명)."""
    src = Image.open(os.path.join(U.UI, "map", "icons", "icon_soulpath@2x.png")).convert("RGBA") if os.path.exists(os.path.join(U.UI, "map", "icons", "icon_soulpath@2x.png")) else Image.open(os.path.join(U.UI, "map", "icons", "icon_soulpath.png")).convert("RGBA").resize((128, 128))
    g = src.convert("LA").convert("RGBA"); a = g.split()[3].point(lambda v: int(v * 0.55)); g.putalpha(a); return g

def luma(im):
    a = np.asarray(im, np.float32); w = a[..., 3:4] / 255; return float((a[..., :3] @ np.array([0.2126, 0.7152, 0.0722]) * w[..., 0]).sum() / max(1.0, w.sum()))

def run():
    save(prompt_tendo(), "prompt_tendo", SUB, note="월드 안내·E 버튼 앞 천도 모양(▲ 불꽃 + 실선 테두리) 48², 화면에는 32px로")
    save(prompt_pahon(), "prompt_pahon", SUB, note="월드 안내·R 버튼 앞 파혼 모양(✕ 깨진 조각 + 점선·톱니 테두리) 48², 화면에는 32px로")
    save(prompt_soulpath(), "prompt_soulpath", SUB, note="넋길 안내(서낭당 [F] 앞): 보라 혼불 셋 달린 줄 48² — 3D 넋길 문의 보라 혼불과 같은 말, 둥근 문 모양 아님")
    cards = {k: exec_card(k) for k in ("tendo", "pahon")}; lum = {k: luma(v) for k, v in cards.items()}; tgt = sum(lum.values()) / 2
    for k, im in cards.items():       # 같은 밝기: 청록·주황 색 칸의 평균 밝기를 맞춘다
        a = np.asarray(im, np.float32); f = tgt / lum[k]; a[..., :3] = np.clip(a[..., :3] * f, 0, 255); cards[k] = Image.fromarray(a.astype(np.uint8), "RGBA"); lum[k] = luma(cards[k])
        save(cards[k], f"exec_card_{k}", SUB, note=f"첫 처결 카드({'천도' if k == 'tendo' else '파혼'}) 280×96: 왼쪽 모양 아이콘, 키 칸(98,14,36×24)에 E/R, 오른쪽 글자 자리. 천도 실선 / 파혼 점선 테두리, 두 카드 밝기 맞춤")
    save(bind_world(1), "bind_world_frame", SUB, nine=[6, 6, 6, 6], note="일반 혼 머리 위 맺힘 막대 틀 96×12(월드 빌보드)"); save(bind_world(2), "bind_world_frame2", SUB, nine=[6, 6, 6, 6], note="덩어리 혼 맺힘 막대 틀 96×22(두 줄)"); save(bind_fill(), "bind_world_fill", SUB, note="맺힘 채움 88×6(틀 안쪽 +4,+3). 덩어리는 두 줄 각각")
    for nm, im, note in (("icon_soul_wait", map_icon_soul_wait(), "미니맵 처결 대기 혼(청록 고리+점). 명세 크기 12~14px"), ("icon_soulpath_off", map_icon_soulpath_off(), "낮에 닫힌 넋길(흐림). 밤이 되면 icon_soulpath로 바꾼다")):
        d = os.path.join(U.UI, "map", "icons"); im.resize((64, 64), Image.LANCZOS).save(os.path.join(d, nm + ".png"), optimize=True); im.save(os.path.join(d, nm + "@2x.png"), optimize=True)
        U.MANIFEST[f"map/icons/{nm}"] = {"size_px": [64, 64], "x2": nm + "@2x.png", "note": note}
    U.dump_manifest("ui_manifest.json"); print("카드 평균 밝기", {k: round(v, 1) for k, v in lum.items()})
if __name__ == "__main__":
    run()
