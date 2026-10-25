"""폰(터치) 버튼 그림 — 화면 명세 v1.8 §5 새 배치(천도 ▲·파혼 ✕ 136 px, 무기 기술 Q 104 px, F 자리 등잔, ✕ 테두리 1초 연쇄 고리, 삼지창 직선 미리보기).
왜 새로: 지금 있는 폰 버튼 그림은 공격·회피·상호작용·빈 도술 칸뿐이라 처결 버튼 둘·Q·등잔이 없었다.
규칙(접근성 v1.4 §9-2, 흑백에서도 구별): ▲(천도)=청록 불꽃 + **실선** 테두리 / ✕(파혼)=주황 깨진 조각 + **점선 + 톱니** 테두리. 같은 밝기·같은 크기(정답 표시 금지).
 색을 빼도 ① 글리프 모양(위로 솟는 불꽃 ↔ 사방으로 벌어진 조각) ② 테두리 질감(매끈한 고리 ↔ 톱니 이빨) 두 가지로 갈린다. 점검: 흑백으로 바꾼 비교판과 밝기 차를 같이 낸다.
크기: 지름은 1080p 기준 픽셀(1배 = 그 크기, @2x = 두 배). 손가락 판정은 코드가 1.2배(최소 96 px).
산출(assets3d/ui/phone/ + unity Sprites/ui/phone/, 1배+@2x) — 파일 표는 docs/PHONE-BUTTONS.md.
실행: python3 phone_buttons.py"""
import os, sys, math, json, shutil
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image, ImageDraw
import ui_lib as U
from ui_lib import INK, NAVY, ABYSS, GOLD, TEAL, CHAIN, save
from first10_art import new, glow_layer, over, S, ORANGE
from first_screen_icons import flame, dashed_ring, saw_ring, shard
SUB = "phone"; CREAM = (243, 231, 211); STEEL = (220, 230, 242); BRASS = (214, 160, 78); LAMP = (255, 216, 115); PRESS = (44, 58, 104)
FILES = {}
def put(im, name, note):
    save(im, name, SUB, note=note); FILES[name] = {"size_px": [im.size[0] // 2, im.size[1] // 2], "note": note}

def disc(d, c, r, fill=ABYSS + (250,)):
    d.ellipse([c - r, c - r, c + r, c + r], fill=fill)

# ── 천도 ▲ 136 ───────────────────────────────────────────────────────────────
def tendo(pressed=False):
    n = 136; im = new(n, n); d = ImageDraw.Draw(im); c = n * S / 2; R = (n / 2 - 1) * S
    disc(d, c, R, (PRESS if pressed else ABYSS) + (250,)); d.ellipse([c - R, c - R, c + R, c + R], outline=INK + (255,), width=int(4 * S))
    rw = 9 if pressed else 7; d.ellipse([c - R + 4 * S, c - R + 4 * S, c + R - 4 * S, c + R - 4 * S], outline=TEAL + (255,), width=int(rw * S))              # 매끈한 실선 고리
    d.ellipse([c - R + (4 + rw + 1) * S, c - R + (4 + rw + 1) * S, c + R - (4 + rw + 1) * S, c + R - (4 + rw + 1) * S], outline=INK + (150,), width=int(2 * S))   # 안쪽 먹 가는 선
    h = 74 if pressed else 68
    im = over(im, glow_layer(im.size, lambda dd: flame(dd, c, c + 3 * S, h * S, 255), TEAL, 6 * S, 1.2 if pressed else 0.9)); d = ImageDraw.Draw(im)
    flame(d, c, c + 3 * S, h * S, TEAL + (255,), INK + (255,), 3 * S); flame(d, c, c + 12 * S, h * 0.5 * S, (225, 255, 247, 255)); return im

# ── 파혼 ✕ 136 ───────────────────────────────────────────────────────────────
def pahon(pressed=False):
    n = 136; im = new(n, n); d = ImageDraw.Draw(im); c = n * S / 2; R = (n / 2 - 5) * S
    for k in range(18):   # 톱니 이빨(바깥, 지름 안쪽에 들어가게 5 px)
        a = k / 18 * math.tau; b = (k + 0.5) / 18 * math.tau; a2 = (k + 1) / 18 * math.tau; t = 5 * S
        d.polygon([(c + math.cos(a) * R, c + math.sin(a) * R), (c + math.cos(b) * (R + t), c + math.sin(b) * (R + t)), (c + math.cos(a2) * R, c + math.sin(a2) * R)], fill=INK + (255,))
    disc(d, c, R, (PRESS if pressed else ABYSS) + (250,)); d.ellipse([c - R, c - R, c + R, c + R], outline=INK + (255,), width=int(4 * S))
    dashed_ring(d, c, R - 8 * S, (9 if pressed else 7) * S, ORANGE + (255,), n=14, gap=0.4)                                                             # 점선 고리
    sc = 1.38 * (1.08 if pressed else 1.0)
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):    # ✕ = 가운데가 벌어진 굵은 팔 넷(끝이 삐죽 갈라짐). 점 사각이 아니라 '×' 모양으로 읽히게 길게 뻗는다
        pts = [(sx * 7, sy * 2.5), (sx * 22, sy * 14), (sx * 31, sy * 16), (sx * 26, sy * 21), (sx * 16, sy * 31), (sx * 14, sy * 22), (sx * 2.5, sy * 7)]
        P = [(c + x * S * sc, c + y * S * sc) for x, y in pts]; shard(d, P, ORANGE + (255,), INK + (255,))
        core = [(c + sx * S * sc * x, c + sy * S * sc * y) for x, y in ((9, 5), (21, 15), (17, 19), (14, 11), (8, 8))]; d.polygon(core, fill=(255, 196, 140, 255))      # 밝은 속살: 흑백에서도 ▲와 비슷한 무게
    return im

def ring(n, r_in, r_out, color, seg=None):
    """진행 고리(채움 방식 Radial360용): r_in~r_out 두께 고리. seg=(개수, 간격비)면 사슬 마디처럼 끊어서."""
    im = new(n, n); d = ImageDraw.Draw(im); c = n * S / 2
    if seg is None: d.ellipse([c - r_out * S, c - r_out * S, c + r_out * S, c + r_out * S], outline=color + (255,), width=int((r_out - r_in) * S))
    else:
        cnt, gap = seg
        for k in range(cnt):     # 둥근 사슬 마디 하나씩: 타원 마디(먹 테두리 + 연한 청색)
            a = k / cnt * math.tau; rm = (r_in + r_out) / 2 * S; x = c + math.cos(a) * rm; y = c + math.sin(a) * rm; L = (r_out - r_in) * 1.7 * S; W = (r_out - r_in) * S
            link = Image.new("RGBA", (int(L * 2.4), int(L * 2.4)), (0, 0, 0, 0)); ld = ImageDraw.Draw(link); m = link.size[0] / 2
            ld.rounded_rectangle([m - L / 2, m - W / 2, m + L / 2, m + W / 2], radius=int(W / 2), fill=INK + (255,)); ld.rounded_rectangle([m - L / 2 + 3 * S, m - W / 2 + 3 * S, m + L / 2 - 3 * S, m + W / 2 - 3 * S], radius=int(W / 2), fill=color + (255,))
            link = link.rotate(-math.degrees(a) - 90, resample=Image.BICUBIC); im.alpha_composite(link, (int(x - m), int(y - m)))
    return im

def chain_mark(n=48):
    """연쇄 대상 머리 위 표시: 맞물린 사슬 두 마디 + 아래로 향한 ▼. 4 m 안 다음 꿇은 혼에 띄운다(파혼 주황 점선 테두리는 쓰지 않음 — 이건 '이어질 곳' 표시)."""
    im = new(n, n); d = ImageDraw.Draw(im); c = n * S / 2
    for k, (dx, dy, rot) in enumerate(((-6, -4, 40), (6, 4, -40))):
        link = Image.new("RGBA", (30 * S, 30 * S), (0, 0, 0, 0)); ld = ImageDraw.Draw(link); ld.rounded_rectangle([3 * S, 8 * S, 27 * S, 22 * S], radius=7 * S, fill=INK + (255,)); ld.rounded_rectangle([6 * S, 11 * S, 24 * S, 19 * S], radius=4 * S, fill=(0, 0, 0, 0))
        ld.rounded_rectangle([6 * S, 11 * S, 24 * S, 19 * S], radius=4 * S, outline=CHAIN + (255,), width=int(2.4 * S))
        link = link.rotate(rot, resample=Image.BICUBIC); im.alpha_composite(link, (int(c - 15 * S + dx * S), int(c - 19 * S + dy * S)))
    d = ImageDraw.Draw(im); tri = [(c - 9 * S, c + 12 * S), (c + 9 * S, c + 12 * S), (c, c + 22 * S)]; d.polygon(tri, fill=CHAIN + (255,), outline=INK + (255,)); d.line(tri + [tri[0]], fill=INK + (255,), width=int(2 * S)); return im

# ── Q 무기 기술 104 ─────────────────────────────────────────────────────────
def q_frame(color=GOLD):
    n = 104; im = new(n, n); d = ImageDraw.Draw(im); c = n * S / 2; R = (n / 2 - 1) * S
    disc(d, c, R); d.ellipse([c - R, c - R, c + R, c + R], outline=INK + (255,), width=int(3 * S)); d.ellipse([c - R + 3 * S, c - R + 3 * S, c + R - 3 * S, c + R - 3 * S], outline=color + (255,), width=int(5 * S)); return im
def glyph(kind, n=64):
    im = new(n, n); d = ImageDraw.Draw(im); c = n * S / 2; P = lambda x, y: (c + x * S, c + y * S)
    def poly(pts, fill, w=2): q = [P(*p) for p in pts]; d.polygon(q, fill=INK + (255,)); d.line(q + [q[0]], fill=INK + (255,), width=int(w * 2 * S)); d.polygon(q, fill=fill)
    if kind == "pin":       # 삼지창 꽂아 버티기: 자루 위 + 세 갈래가 땅 선에 박힘
        poly([(-2, -28), (2, -28), (2, 6), (-2, 6)], (138, 106, 68, 255)); poly([(-14, 4), (14, 4), (14, 8), (-14, 8)], STEEL + (255,))
        for x in (-12, 0, 12): poly([(x - 2, 8), (x + 2, 8), (x + 2, 22), (x, 28), (x - 2, 22)], STEEL + (255,))
        d.line([P(-26, 24), P(26, 24)], fill=CREAM + (255,), width=int(3 * S))
    elif kind == "call":    # 요령 불러 세우기: 방울 + 소리 호
        pts = [(-14, 14), (-12, -2), (-6, -14), (0, -17), (6, -14), (12, -2), (14, 14)]; poly(pts, BRASS + (255,)); d.ellipse([c - 4 * S, c + 14 * S, c + 4 * S, c + 22 * S], fill=INK + (255,)); d.ellipse([c - 2.5 * S, c + 15 * S, c + 2.5 * S, c + 20 * S], fill=BRASS + (255,))
        for r in (22, 29): d.arc([c - r * S, c - r * S - 4 * S, c + r * S, c + r * S - 4 * S], 215, 255, fill=CREAM + (255,), width=int(3 * S)); d.arc([c - r * S, c - r * S - 4 * S, c + r * S, c + r * S - 4 * S], 285, 325, fill=CREAM + (255,), width=int(3 * S))
    elif kind == "brush":   # 붓 이름 쓰기: 비스듬 붓 + 먹 획
        poly([(-22, 22), (-26, 18), (10, -18), (14, -14)], (138, 106, 68, 255)); poly([(10, -18), (14, -14), (24, -24), (18, -30)], CREAM + (255,))
        pts = [P(-24 + t * 2.1, 26 - math.sin(t / 8 * math.pi) * 5 - t * 0.2) for t in range(0, 17)]; d.line(pts, fill=INK + (255,), width=int(8 * S)); d.line(pts, fill=(120, 96, 168, 255), width=int(4 * S))
    elif kind == "chain":   # 철삭: 비스듬 사슬 마디 셋 + 끝 갈고리
        for k in range(3):
            lk = Image.new("RGBA", (30 * S, 30 * S), (0, 0, 0, 0)); ld = ImageDraw.Draw(lk); ld.rounded_rectangle([3 * S, 8 * S, 27 * S, 22 * S], radius=7 * S, fill=INK + (255,)); ld.rounded_rectangle([6 * S, 11 * S, 24 * S, 19 * S], radius=4 * S, fill=(0, 0, 0, 0)); ld.rounded_rectangle([6 * S, 11 * S, 24 * S, 19 * S], radius=4 * S, outline=CHAIN + (255,), width=int(2.6 * S))
            lk = lk.rotate(45 if k % 2 == 0 else -45 + 90, resample=Image.BICUBIC); im.alpha_composite(lk, (int(c - 15 * S - 14 * S + k * 14 * S), int(c - 15 * S + 12 * S - k * 12 * S)))
    elif kind == "club":    # 육모방망이: 여섯 모 나무 방망이(비스듬, 위가 굵음) + 손잡이 끈 고리 + 맞은 곳 별 모양 충격선
        poly([(-26, 20), (-20, 26), (8, -2), (4, -8)], (150, 112, 70, 255)); poly([(4, -8), (8, -2), (24, -18), (14, -28)], (178, 138, 88, 255))
        d.line([P(5, -5), P(11, -1)], fill=INK + (255,), width=int(2 * S)); d.line([P(-1, 2), P(5, 6)], fill=INK + (255,), width=int(2 * S))       # 여섯 모를 나누는 마디 선
        d.arc([c - 34 * S, c + 6 * S, c - 14 * S, c + 34 * S], 90, 270, fill=(205, 70, 55, 255), width=int(3 * S))                                      # 손잡이 끈
        for (x, y, r) in ((22, -26, 7), (30, -12, 5), (14, -34, 5)):          # 충격 별(기절): 네 갈래 반짝
            q = [P(x, y - r), P(x + r * 0.3, y - r * 0.3), P(x + r, y), P(x + r * 0.3, y + r * 0.3), P(x, y + r), P(x - r * 0.3, y + r * 0.3), P(x - r, y), P(x - r * 0.3, y - r * 0.3)]
            d.polygon(q, fill=CREAM + (255,), outline=INK + (255,))
    elif kind == "lamp":    # 등잔: 받침 + 기름 접시 + 작은 불꽃 + 빛무리
        im = over(im, glow_layer(im.size, lambda dd: dd.ellipse([c - 16 * S, c - 24 * S, c + 16 * S, c + 8 * S], fill=255), LAMP, 8 * S, 0.8)); d = ImageDraw.Draw(im)
        poly([(-4, 10), (4, 10), (7, 24), (-7, 24)], BRASS + (255,)); poly([(-18, 6), (18, 6), (12, 14), (-12, 14)], BRASS + (255,)); flame(d, c, c - 8 * S, 24 * S, LAMP + (255,), INK + (255,), 1.6 * S); flame(d, c, c - 4 * S, 11 * S, (255, 250, 225, 255))
    return im
def f_frame():
    n = 104; im = new(n, n); d = ImageDraw.Draw(im); c = n * S / 2; R = (n / 2 - 1) * S
    disc(d, c, R); d.ellipse([c - R, c - R, c + R, c + R], outline=INK + (255,), width=int(3 * S)); d.ellipse([c - R + 3 * S, c - R + 3 * S, c + R - 3 * S, c + R - 3 * S], outline=(95, 227, 192, 255), width=int(5 * S)); return im
def comp(frame, g, gs=64):
    im = frame.copy(); gg = g.resize((gs * S, gs * S), Image.LANCZOS) if g.size[0] != gs * S else g; im.alpha_composite(gg, ((im.size[0] - gg.size[0]) // 2, (im.size[1] - gg.size[1]) // 2)); return im
def dot(on):
    n = 16; im = new(n, n); d = ImageDraw.Draw(im); c = n * S / 2; d.ellipse([c - 7 * S, c - 7 * S, c + 7 * S, c + 7 * S], fill=INK + (255,))
    if on: d.ellipse([c - 5 * S, c - 5 * S, c + 5 * S, c + 5 * S], fill=CREAM + (255,))
    else: d.ellipse([c - 5 * S, c - 5 * S, c + 5 * S, c + 5 * S], outline=(120, 110, 100, 255), width=int(1.6 * S))
    return im

# ── 삼지창 직선 미리보기 6 m × 2 m(바닥에 깐다, 1 m = 128 px) ──────────────────
def line_preview():
    w, h = 768, 256; im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im); W, H = w * S, h * S; b = 16 * S; o = 5 * S; i = 8 * S
    def dashed(col, wd):
        for (x0, y0, x1, y1) in ((i, i, W - i - 70 * S, i), (i, H - i, W - i - 70 * S, H - i)):
            n = int((x1 - x0) / (60 * S))
            for k in range(0, n, 2): d.line([(x0 + (x1 - x0) * k / n, y0), (x0 + (x1 - x0) * (k + 1) / n, y0)], fill=col, width=wd)
        d.line([(i, i), (i, H - i)], fill=col, width=wd)
        d.line([(W - i - 70 * S, i), (W - i, H / 2), (W - i - 70 * S, H - i)], fill=col, width=wd, joint="curve")        # 끝은 화살촉
    dashed(INK + (210,), b + 2 * o); dashed(ORANGE + (255,), b)
    for k in range(5):      # 가운데 방향 화살표(앞쪽 +x)
        x = 120 * S + k * 110 * S; pts = [(x, H / 2 - 30 * S), (x + 34 * S, H / 2), (x, H / 2 + 30 * S)]
        d.line(pts, fill=INK + (200,), width=int(15 * S), joint="curve"); d.line(pts, fill=ORANGE + (230,), width=int(8 * S), joint="curve")
    return im

def run():
    put(tendo(), "btn_tendo_136", "천도 ▲ 버튼 136: 청록 불꽃 + 매끈한 실선 고리. 처결할 혼이 있을 때만 0.15초에 뜸. 누르고 있기 = 시전")
    put(tendo(True), "btn_tendo_136_pressed", "천도 ▲ 눌린 모양(바탕 밝아지고 고리 굵어짐)")
    put(pahon(), "btn_pahon_136", "파혼 ✕ 버튼 136: 주황 깨진 조각 넷 + 점선 고리 + 바깥 톱니. 톡 = 즉시 파혼, 끌기 = 방향 조준(삼지창)")
    put(pahon(True), "btn_pahon_136_pressed", "파혼 ✕ 눌린 모양")
    put(ring(136, 61, 68, TEAL), "btn_tendo_ring_fill", "천도 시전 진행 고리(흰·청록, Image Filled Radial360, 12시부터 시계 방향). 지름 136, 두께 7. 연속 천도(0.8초)면 절반 찬 채로 시작. 맞아 끊기면 코드가 한 번 붉게 틴트(#E85C41)")
    put(ring(136, 61, 68, INK), "btn_tendo_ring_track", "천도 시전 고리 바닥(먹색 트랙)")
    put(ring(152, 62, 72, CHAIN, seg=(16, 0)), "btn_pahon_chain_ring", "파혼 연쇄 고리(업 30): ✕ 테두리를 두른 사슬 마디 16개. 파혼 직후 1초 동안 Filled Radial360이 시계 반대로 줄어든다. 연쇄 대상이 없으면 안 띄움")
    put(chain_mark(), "mark_chain_target", "연쇄 대상 표시(4 m 안 다음 꿇은 혼 머리 위): 맞물린 사슬 둘 + ▼. 화면 48 px")
    fr = q_frame(); put(fr, "btn_q_frame_104", "무기 기술 Q 버튼 틀 104(금 고리). 재사용 중엔 코드가 어둡게 + 남은 초")
    for k, nm in (("pin", "삼지창: 꽂아 버티기"), ("call", "요령: 불러 세우기"), ("brush", "붓: 이름 쓰기"), ("chain", "철삭: 사슬(끌기)"), ("club", "육모방망이: 손에 익음(맞은 적 기절)")):
        put(glyph(k), f"q_glyph_{k}", f"Q 무기 기술 그림({nm}) 64. btn_q_frame_104 위 가운데에 얹는다"); put(comp(fr, glyph(k)), f"btn_q_{k}_104", f"Q 버튼 완성본({nm}) 104")
    put(dot(True), "q_dot_on", "붓 표식 먹점 켜짐 16(Q 버튼 위 ●●●)"); put(dot(False), "q_dot_off", "붓 표식 먹점 꺼짐 16")
    ff = f_frame(); put(ff, "btn_f_frame_104", "상호작용 F 버튼 틀 104(청록 고리)"); put(glyph("lamp"), "f_glyph_lamp", "등잔 그림 64"); put(comp(ff, glyph("lamp")), "btn_f_lamp_104", "F 자리 등잔 버튼(밤·오늘 안 켰고 둘레 대상 없을 때). 길게 0.5초 = 켜짐")
    put(ring(104, 47, 52, (255, 216, 115)), "btn_f_hold_ring", "F 길게 누르기 0.5초 진행 고리(Filled Radial360) 104")
    im = line_preview(); U.save(im, "preview_line_6x2", SUB, note="삼지창 ✕ 끌기 6 m×2 m 직선 미리보기(바닥 눕힘, 1 m=128 px). 주황 점선 테두리 + 앞(+x) 화살 — 위험 예고(빨강 실선)와 구별. 채움 없음"); FILES["preview_line_6x2"] = {"size_px": [768, 256], "note": "삼지창 직선 미리보기 6×2 m, 1 m=128 px, +x가 앞"}
    json.dump(FILES, open(os.path.join(U.UI, "_phone_buttons.json"), "w"), ensure_ascii=False, indent=1); U.dump_manifest("ui_manifest.json")
    dst = os.path.join(os.path.dirname(__file__), "..", "..", "unity", "Assets", "Resources", "Sprites", "ui", SUB); os.makedirs(dst, exist_ok=True)
    for f in os.listdir(os.path.join(U.UI, SUB)): shutil.copy(os.path.join(U.UI, SUB, f), os.path.join(dst, f))
    print(len(FILES), "장")

def check():
    """흑백 점검: ▲·✕ 버튼을 회색으로 바꿔 나란히 + 밝기 차 + 글리프 모양 차이(색을 지운 뒤 먹 테두리 바깥 면적)."""
    from PIL import ImageFont
    t = Image.open(os.path.join(U.UI, SUB, "btn_tendo_136@2x.png")).convert("RGBA"); p = Image.open(os.path.join(U.UI, SUB, "btn_pahon_136@2x.png")).convert("RGBA")
    ds = [Image.open(os.path.join(U.UI, SUB, f"btn_{k}_104@2x.png")).convert("RGBA") for k in ("q_pin", "q_call", "q_brush", "q_chain", "q_club", "f_lamp")]
    W = Image.new("RGB", (272 * 2 + 40 + 208 * 6 + 70, 272 * 2 + 40), (110, 120, 100))
    for row, gray in ((0, False), (1, True)):
        x = 10
        for im in [t, p] + ds:
            bg = Image.new("RGBA", im.size, (110, 120, 100, 255)); bg.alpha_composite(im); b = bg.convert("L").convert("RGB") if gray else bg.convert("RGB"); W.paste(b, (x, 10 + row * 282)); x += im.size[0] + 10
    W.save(os.path.join(U.UI, SUB, "_phone_buttons_check.png"))
    def L(im): a = np.asarray(im.convert("RGBA"), np.float32); m = a[..., 3] > 128; g = (a[..., :3] @ np.array([0.2126, 0.7152, 0.0722])); return g, m
    gt, mt = L(t); gp, mp = L(p); c = 136; yy, xx = np.mgrid[0:272, 0:272]; inner = np.hypot(xx - c, yy - c) < 52     # 글리프 영역
    glyph_t = (gt > 120) & inner & mt; glyph_p = (gp > 120) & inner & mp
    iou = float((glyph_t & glyph_p).sum() / max(1, (glyph_t | glyph_p).sum()))
    ring_t = float(gt[(np.hypot(xx - c, yy - c) > 104) & (np.hypot(xx - c, yy - c) < 116) & mt].std()); ring_p = float(gp[(np.hypot(xx - c, yy - c) > 104) & (np.hypot(xx - c, yy - c) < 116) & mp].std())
    res = {"glyph_mean_luma_tendo": round(float(gt[glyph_t].mean()), 1), "glyph_mean_luma_pahon": round(float(gp[glyph_p].mean()), 1), "glyph_shape_IoU_tendo_vs_pahon": round(iou, 3), "border_luma_std_tendo(매끈할수록 작음)": round(ring_t, 1), "border_luma_std_pahon(톱니·점선이라 큼)": round(ring_p, 1)}
    json.dump(res, open(os.path.join(U.UI, "_phone_buttons_check.json"), "w"), ensure_ascii=False, indent=1); print(res)

if __name__ == "__main__":
    run(); check()
