"""개편 HUD 그림 한 벌(아트, 2026-10-31) — UI·UX 개편안 §4 P0-2·P0-3·P0-5의 아트 몫.
실행: python3 tools/art3d/overhaul_ui.py   (결과: assets3d/ui/overhaul/ + unity/Assets/Resources/Sprites/overhaul/, 목록은 _manifest.json)

무엇을 그리나
 hud/   아래 가운데 한 덩어리: 바탕판 · 체력 막대 · 기술 칸(찬 칸·빈 칸·재사용 대기) · 천도/파혼 큰 칸(같은 크기·같은 밝기) · 피하기 점
 gyeol/ 숫자 대신 '맺힘 금': 막대에 금 가는 3단계 · 맞은 번쩍 · 막대가 쪼개지는 두 조각 · 맞은 자리 금 표식 4종 · 보스 맺힘 줄(2~3줄)
 mark/  혼 머리 위 처결 표식(▲ 천도 / ✕ 파혼, 키 글자 자리) · 연속 천도 사슬선 조각

지킨 규칙(명세 §0·§9, 접근성 결정)
 · 글자는 그림에 안 넣는다(키 글자·이름은 코드). 키 글자 자리는 빈 키캡으로 둔다.
 · 천도 청록 ▲ 실선 / 파혼 주황 ✕ 점선·톱니 — 흑백에서도 모양으로 갈린다. 두 칸의 크기·평균 밝기를 맞춰 '정답 표시'가 되지 않게 한다.
 · 남청 먹판 + 한지 테두리 + 금 모서리(기존 ui 세트와 같은 재료). 금은 '찬 기술 칸'에만."""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from overhaul_lib import *

PLATE = 80  # 기술 칸·천도·파혼 칸 한 변(px, 1080p 기준) — 명세 64에서 키움(개편안: 아래 한 덩어리를 또렷하게)


# ------------------------------------------------------------------ 칸 바탕
def plate_base(w=PLATE, edge=HANJI, edge_a=255, fill_a=235, gold=False, dashed=False):
    """남청 먹판 칸. dashed=True면 '빈 칸'(점선 테두리, 속 투명하게)."""
    im = canvas(w, w); d = ImageDraw.Draw(im)
    if dashed:
        rrect(d, (3, 3, w - 3, w - 3), 12, fill=rgba(ABYSS, 90))
        # 점선 테두리: 둘레를 따라 짧은 선을 띄엄띄엄 — 사각형 4변을 직접 쪼갠다
        pts = []
        def edge_dash(x0, y0, x1, y1, n=7):
            for i in range(n):
                a = i / n + 0.02; b = (i + 0.55) / n
                pts.append(((x0 + (x1 - x0) * a, y0 + (y1 - y0) * a), (x0 + (x1 - x0) * b, y0 + (y1 - y0) * b)))
        m = 14; edge_dash(m, 3, w - m, 3); edge_dash(w - 3, m, w - 3, w - m); edge_dash(w - m, w - 3, m, w - 3); edge_dash(3, w - m, 3, m)
        for p0, p1 in pts: line(d, [p0, p1], rgba(HANJI, 120), 2.2)
        for cx, cy, a0 in ((m, m, 180), (w - m, m, 270), (w - m, w - m, 0), (m, w - m, 90)):   # 네 모서리는 둥근 호 한 도막씩
            d.arc([(cx - 11) * S, (cy - 11) * S, (cx + 11) * S, (cy + 11) * S], a0 + 8, a0 + 82, fill=rgba(HANJI, 120), width=int(2.2 * S))
        return im
    g = grad_v(w, w, (29, 42, 77), (15, 23, 41), fill_a, fill_a)
    m = mask_of(lambda dd: dd.rounded_rectangle([3 * S, 3 * S, (w - 3) * S - 1, (w - 3) * S - 1], radius=12 * S, fill=255), w, w)
    im.paste(g, (0, 0), m)
    rrect(d, (3, 3, w - 3, w - 3), 12, outline=rgba(edge, edge_a), width=3)
    rrect(d, (8, 8, w - 8, w - 8), 8, outline=rgba(LINE, 200), width=1.5)
    if gold:   # 금 모서리(기존 ui_skill_slot_ready와 같은 모양): 찬 기술 칸만
        for (x, y, sx, sy) in ((7, 7, 1, 1), (w - 7, 7, -1, 1), (7, w - 7, 1, -1), (w - 7, w - 7, -1, -1)):
            line(d, [(x + sx * 14, y), (x, y), (x, y + sy * 14)], rgba(GOLD), 3)
    return im


# ------------------------------------------------------------------ 천도 ▲ / 파혼 ✕ 글리프
def glyph_tendo(im, cx, cy, col, a=255, k=1.0, small=False):
    """천도 ▲: 솟는 불꽃 + 매끈한 실선 고리. 흑백에서도 '둥글고 닫힌 선'으로 읽힌다."""
    d = ImageDraw.Draw(im); c = rgba(col, a)
    ellipse(d, (cx - 34 * k, cy - 34 * k, cx + 34 * k, cy + 34 * k), outline=c, width=2.6 if not small else 4.4)       # 매끈한 실선 고리(작은 판은 굵게)
    tri = [(cx, cy - 18 * k), (cx + 16.5 * k, cy + 12 * k), (cx - 16.5 * k, cy + 12 * k)]
    poly(d, tri, fill=c)
    line(d, tri + [tri[0]], c, 3.5 * k)                                                           # 모서리를 둥글게 보이게 굵은 외곽
    flame = [(cx, cy - 3 * k), (cx + 6 * k, cy + 8 * k), (cx, cy + 5 * k), (cx - 6 * k, cy + 8 * k)]
    poly(d, flame, fill=rgba(ABYSS, 235))                                                         # 안쪽 불꽃 홈(먹)


def glyph_pahon(im, cx, cy, col, a=255, k=1.0, small=False):
    """파혼 ✕: 가운데가 벌어진 깨진 팔 넷 + 점선 고리 + 바깥 톱니. 흑백에서도 '끊긴 선·톱니'로 읽힌다."""
    d = ImageDraw.Draw(im); c = rgba(col, a)
    n = 20 if not small else 8                                                                  # 작은 판은 점선을 성기게(안 그러면 뭉개진다)
    for i in range(n):                                                                           # 점선 고리
        a0 = 360 * i / n; d.arc([(cx - 34 * k) * S, (cy - 34 * k) * S, (cx + 34 * k) * S, (cy + 34 * k) * S], a0, a0 + 360 / n * 0.55, fill=c, width=int((2.6 if not small else 4.6) * S))
    nt = 12 if not small else 0                                                                  # 작은 판은 톱니를 뺀다(30px에서 뭉개짐)
    for i in range(nt):                                                                          # 바깥 톱니(삼각)
        t = 2 * math.pi * i / nt + math.pi / nt; r0, r1 = (36.5 if not small else 37.5) * k, (42 if not small else 46) * k
        poly(d, [(cx + math.cos(t - .09) * r0, cy + math.sin(t - .09) * r0), (cx + math.cos(t) * r1, cy + math.sin(t) * r1), (cx + math.cos(t + .09) * r0, cy + math.sin(t + .09) * r0)], fill=c)
    for sx, sy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):                                          # 깨진 팔: 가운데 쪽이 벌어진 대각선
        line(d, [(cx + sx * 6 * k, cy + sy * 6 * k), (cx + sx * (19 if not small else 25) * k, cy + sy * (19 if not small else 25) * k)], c, (6.8 if not small else 8) * k)


def tinted(fn, base, col, a, t, dark=1.0):
    """글리프 색을 흰색 쪽으로 t만큼 섞고(밝게) dark배로 곱한다(어둡게) — 두 칸 평균 밝기 맞춤용."""
    mix = tuple(int(min(255, (col[i] * (1 - t) + 255 * t) * dark)) for i in range(3))
    im = base.copy(); fn(im, im.width // S // 2, im.height // S // 2, mix, a); return im


def make_exec_slots():
    """천도·파혼 큰 칸. 크기 80×80 동일. 두 칸 평균 밝기를 ±2.5% 안으로 맞춘다(개편안 '기둥 통과': 한쪽이 기본값처럼 보이면 안 됨).
    파혼 주황은 살짝만(t=0.2) 밝혀 색을 지키고, 나머지 차이는 청록을 어둡게 깎아 맞춘다 — 파혼을 하얗게 밝히면 '주황 = 파혼' 약속이 깨진다."""
    base = plate_base(PLATE, edge=HANJI, edge_a=255)
    T_P = 0.3
    pa = luma(finish(tinted(glyph_pahon, base, ORANGE, 255, T_P), PLATE, PLATE))
    lo, hi = 0.75, 1.0
    for _ in range(14):
        mid = (lo + hi) / 2
        if luma(finish(tinted(glyph_tendo, base, TEAL, 255, 0, mid), PLATE, PLATE)) < pa: lo = mid
        else: hi = mid
    d_t = (lo + hi) / 2
    res = {}
    for name, fn, col, t, dk in (("tendo", glyph_tendo, TEAL, 0.0, d_t), ("pahon", glyph_pahon, ORANGE, T_P, 1.0)):
        on = tinted(fn, base, col, 255, t, dk); res[name] = luma(finish(on, PLATE, PLATE))
        col = tuple(int(min(255, (col[i] * (1 - t) + 255 * t) * dk)) for i in range(3))
        save(on, f"slot_{name}_on", "hud", PLATE, PLATE, f"{'천도 ▲' if name == 'tendo' else '파혼 ✕'} 큰 칸 · 처결할 혼이 있을 때(켜짐). 키 글자는 코드가 칸 왼쪽 위에", nine=None)
        off = base.copy(); fn(off, PLATE // 2, PLATE // 2, col, 70)                                 # 꺼짐: 글리프 27%
        save(off, f"slot_{name}_off", "hud", PLATE, PLATE, "처결할 혼이 없을 때(꺼짐) — 칸은 그대로 두어 자리가 안 움직인다")
        hot = canvas(PLATE + 16, PLATE + 16); glow = Image.new("RGBA", hot.size, (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
        rrect(gd, (8, 8, PLATE + 8, PLATE + 8), 14, outline=rgba(col, 230), width=5)
        glow = glow.filter(ImageFilter.GaussianBlur(5 * S)); hot.alpha_composite(glow); hot.alpha_composite(on, (8 * S, 8 * S))
        save(hot, f"slot_{name}_hot", "hud", PLATE + 16, PLATE + 16, "눌렀을 때·시전 중 겉 빛(사방 8px 번짐) — 칸 가운데는 _on과 같다")
    return res


# ------------------------------------------------------------------ 기술 칸·피하기 점·바탕판·체력
def make_hud():
    ready = plate_base(PLATE, gold=True)
    save(ready, "slot_skill_ready", "hud", PLATE, PLATE, "기술 칸 · 쓸 수 있음(금 모서리). 아이콘은 안쪽 64×64에 얹는다")
    save(plate_base(PLATE, dashed=True), "slot_skill_empty", "hud", PLATE, PLATE, "기술 칸 · 빈 칸(점선) — 처음 5분엔 빈 칸이 점선이라 '아직 없는 것'으로 읽힌다")
    cool = plate_base(PLATE, edge=HANJI, edge_a=140, fill_a=250)
    save(cool, "slot_skill_cool", "hud", PLATE, PLATE, "기술 칸 · 재사용 대기(테두리·바탕 어둡게). 시계 방향 어둠·남은 초는 코드")
    # 피하기 점: 찬 점 = 한지 알갱이, 빈 점 = 속 빈 테두리
    for nm, full in (("full", True), ("empty", False)):
        im = canvas(18, 18); d = ImageDraw.Draw(im)
        if full:
            ellipse(d, (1, 1, 17, 17), fill=rgba(INK, 230)); ellipse(d, (3, 3, 15, 15), fill=rgba(HANJI)); ellipse(d, (6, 5, 10, 8), fill=rgba((255, 255, 255), 180))
        else:
            ellipse(d, (1, 1, 17, 17), fill=rgba(INK, 140)); ellipse(d, (3, 3, 15, 15), outline=rgba(HANJI, 110), width=1.6)
        save(im, f"dodge_pip_{nm}", "hud", 18, 18, "피하기 충전 점(기술 칸 바로 위 가운데, 2개)" + (" · 찬 점" if full else " · 빈 점"))
    # 한 덩어리 바탕판: 9조각, 모서리 24
    im = canvas(64, 64); d = ImageDraw.Draw(im)
    g = grad_v(64, 64, (22, 33, 62), (15, 23, 41), 205, 205); m = mask_of(lambda dd: dd.rounded_rectangle([1 * S, 1 * S, 63 * S - 1, 63 * S - 1], radius=16 * S, fill=255), 64, 64)
    im.paste(g, (0, 0), m); rrect(d, (1, 1, 63, 63), 16, outline=rgba(HANJI, 110), width=1.6)
    save(im, "plate_cluster", "hud", 64, 64, "아래 가운데 한 덩어리 바탕(체력·기술·천도/파혼 뒤). 가운데는 비어 있어도 읽히게 85% 먹판", nine=[24, 24, 24, 24])
    # 체력 막대(붉은 인 계열 — 예고 장판 빨강 #E85C41과 안 섞이게 어둡고 붉은 색)
    W, H = 320, 24
    fr = canvas(W, H); d = ImageDraw.Draw(fr)
    rrect(d, (0, 0, W, H), 8, fill=rgba(ABYSS, 240), outline=rgba(HANJI, 235), width=2)
    save(fr, "vital_frame", "hud", W, H, "체력 막대 틀 320×24. 채움은 틀 안쪽 (4,4) 312×16", nine=[10, 8, 10, 8])
    for nm, top, bot, a in (("fill", (222, 98, 82), (150, 52, 48), 255), ("ghost", (243, 231, 211), (226, 211, 184), 150)):
        im = canvas(312, 16); g = grad_v(312, 16, top, bot, a, a)
        m = mask_of(lambda dd: dd.rounded_rectangle([0, 0, 312 * S - 1, 16 * S - 1], radius=6 * S, fill=255), 312, 16)
        out = canvas(312, 16); out.paste(g, (0, 0), m)
        if nm == "fill": ImageDraw.Draw(out).line([(6 * S, 3 * S), (306 * S, 3 * S)], fill=(255, 255, 255, 70), width=2 * S)
        save(out, f"vital_{nm}", "hud", 312, 16, "체력 채움(붉은 인 계열)" if nm == "fill" else "체력 줄어든 자리 잔상(한지색, 0.4초 뒤 사라짐)")


# ------------------------------------------------------------------ 맺힘 금
GW, GH = 96, 22                   # 일반 혼 머리 위 맺힘 막대 틀(기존 ui_bar_gyeol_frame_L과 같은 크기)
GX, GY, GGW, GGH = 4, 4, 88, 14   # 안쪽 홈 위치·크기

def crack_poly(rng, x, y0, y1, jit, step):
    pts = [(x, y0)]; y = y0
    while y < y1:
        y += step * rng.uniform(.7, 1.3); x += rng.uniform(-jit, jit); pts.append((x, min(y, y1)))
    return pts

def draw_crack(d, pts, w=1.6, a=235, hl=True):
    line(d, pts, rgba((18, 20, 30), a), w + 0.8)                                                  # 먹 선
    if hl: line(d, [(x + 0.7, y) for x, y in pts], rgba(HANJI, int(a * .85)), max(0.6, w * .45))  # 한지색 하이라이트 선(금 틈이 빛나 보이게)

def make_gyeol():
    rng = random.Random(7)
    # 막대 금 3단계: 남은 맺힘 ≤66% / ≤33% / ≤10%에 맞춰 코드가 한 장을 고른다(상태 없이 고르는 방식 — 맞은 횟수를 셀 필요 없음)
    plan = {1: [58], 2: [58, 34, 76], 3: [58, 34, 76, 18, 46, 68]}
    for stage, xs in plan.items():
        im = canvas(GW, GH); d = ImageDraw.Draw(im)
        for i, x in enumerate(xs):
            r = random.Random(100 * stage + i)
            main = crack_poly(r, x, GY - 1, GY + GGH + 1, 2.6, 3.4)
            draw_crack(d, main, 1.9, 245)
            if i % 2 == 0:                                                                        # 곁가지 가는 금
                bx, by = main[len(main) // 2]; draw_crack(d, [(bx, by), (bx + r.choice((-1, 1)) * 5, by + r.uniform(1, 3)), (bx + r.choice((-1, 1)) * 9, by + r.uniform(3, 5))], 0.9, 200, hl=False)
        save(im, f"gyeol_crack_stage{stage}_L", "gyeol", GW, GH, f"맺힘 막대 위에 덮는 금 {stage}단계(투명 96×22, 틀과 같은 크기). 남은 맺힘 " + {1: "66% 이하", 2: "33% 이하", 3: "10% 이하"}[stage] + "일 때 한 장만 켠다")
    # 맞은 번쩍: 홈 모양 흰 판(0.06초)
    im = canvas(GW, GH); d = ImageDraw.Draw(im)
    rrect(d, (GX - 1, GY - 1, GX + GGW + 1, GY + GGH + 1), 6, fill=rgba((255, 250, 235), 235))
    glow = im.filter(ImageFilter.GaussianBlur(3 * S)); out = canvas(GW, GH); out.alpha_composite(glow); out.alpha_composite(im)
    save(out, "gyeol_flash_L", "gyeol", GW, GH, "맞은 흰 번쩍 0.06초(막대 전체 덮기). 막대 흔들림은 코드(좌우 2px 3번)")
    # 막대 쪼개짐: 기존 틀 그림을 들쭉날쭉한 선으로 둘로 가른다
    fr = Image.open(os.path.join(ROOT, "assets3d", "ui", "bars_L", "ui_bar_gyeol_frame_L.png")).convert("RGBA").resize((GW * S, GH * S), Image.LANCZOS)
    fill = Image.open(os.path.join(ROOT, "assets3d", "ui", "bars_L", "ui_bar_gyeol_ghost_L.png")).convert("RGBA").resize((GGW * S, GGH * S), Image.LANCZOS)
    whole = fr.copy(); whole.alpha_composite(fill, (GX * S, GY * S))
    cut = [(GW / 2 + 3, -1), (GW / 2 - 4, 6), (GW / 2 + 5, 11), (GW / 2 - 3, 16), (GW / 2 + 2, GH + 1)]
    lm = Image.new("L", whole.size, 0); ImageDraw.Draw(lm).polygon([(0, 0)] + [(x * S, y * S) for x, y in cut] + [(0, GH * S)], fill=255)
    for nm, m in (("left", lm), ("right", Image.eval(lm, lambda v: 255 - v))):
        piece = Image.new("RGBA", whole.size, (0, 0, 0, 0)); piece.paste(whole, (0, 0), m)
        ImageDraw.Draw(piece).line([(x * S, y * S) for x, y in cut], fill=rgba(HANJI, 200), width=int(1.2 * S))   # 쪼개진 단면 한지색
        save(piece, f"gyeol_break_{nm}_L", "gyeol", GW, GH, f"맺힘 0: 막대가 쪼개져 {'왼' if nm == 'left' else '오른'}쪽 조각(원래 자리에서 겹쳐 놓고, 0.25초 동안 코드가 벌려 떨어뜨림)")
    # 맞은 자리 금 표식 4종(숫자 대신). 약·중·강·치명 = 쓰는 기준은 코드(맞은 세기), 크기도 같이 커진다
    for nm, size, rays, crit in (("s", 56, 4, False), ("m", 84, 6, False), ("l", 120, 8, False), ("crit", 150, 9, True)):
        im = canvas(size, size); d = ImageDraw.Draw(im); c = size / 2; r = random.Random(size)
        base_ang = r.uniform(0, 2 * math.pi)
        for i in range(rays):
            ang = base_ang + 2 * math.pi * i / rays + r.uniform(-.25, .25); length = (size / 2 - 4) * r.uniform(.62, 1.0)
            pts = [(c + math.cos(ang) * 3, c + math.sin(ang) * 3)]; dist = 3
            while dist < length:
                dist += length / 4 * r.uniform(.7, 1.2); ang2 = ang + r.uniform(-.28, .28)
                pts.append((c + math.cos(ang2) * dist, c + math.sin(ang2) * dist))
            line(d, pts, rgba((18, 20, 30), 235), 3.4 if size > 60 else 2.6)                      # 먹 바깥선
            line(d, pts, rgba(HANJI if not crit else (255, 226, 150), 255), 1.6 if size > 60 else 1.2)  # 속 한지(치명은 금빛)
        ellipse(d, (c - 3.5, c - 3.5, c + 3.5, c + 3.5), fill=rgba((18, 20, 30), 240)); ellipse(d, (c - 2, c - 2, c + 2, c + 2), fill=rgba(HANJI))
        if crit: ellipse(d, (c - size * .22, c - size * .22, c + size * .22, c + size * .22), outline=rgba(GOLD, 200), width=1.8)
        save(im, f"hit_crack_{nm}", "gyeol", size, size, "맞은 자리에 0.35초 떠 있다 사라지는 금 표식(데미지 숫자 대체, 설정에서 숫자 켜면 안 씀)" + (" · 치명 = 금빛 속선+금 고리" if crit else ""))
    # 보스 맺힘 줄(2~3줄): 한 줄 틀·채움·잔상·깨진 줄. 맺힘 색(하늘)이라 체력 빨강과 안 섞인다
    BW, BH = 960, 28
    fr = canvas(BW, BH); d = ImageDraw.Draw(fr)
    rrect(d, (0, 0, BW, BH), 10, fill=rgba(ABYSS, 242), outline=rgba(HANJI, 235), width=2.4)
    rrect(d, (3, 3, BW - 3, BH - 3), 8, outline=rgba(LINE, 200), width=1.2)
    for x in (4, BW - 4):   # 양끝 금 마개(귀한 보스 표시)
        line(d, [(x, 7), (x, BH - 7)], rgba(GOLD), 2.4)
    save(fr, "boss_gyeol_row_frame", "gyeol", BW, BH, "보스 맺힘 한 줄 틀 960×28. 2~3줄이면 위아래로 4px 띄워 쌓는다. 채움은 (4,4) 952×20", nine=[14, 10, 14, 10])
    ref = Image.open(os.path.join(ROOT, "assets3d", "ui", "bars_L", "ui_bar_gyeol_fill_L.png")).convert("RGB")
    top = ref.getpixel((40, 3)); bot = ref.getpixel((40, 11))                                      # 일반 혼 맺힘 막대와 같은 색을 그대로 뽑아 쓴다
    for nm, tc, bc, a in (("fill", top, bot, 255), ("ghost", HANJI, (226, 211, 184), 150)):
        g = grad_v(952, 20, tc, bc, a, a); m = mask_of(lambda dd: dd.rounded_rectangle([0, 0, 952 * S - 1, 20 * S - 1], radius=8 * S, fill=255), 952, 20)
        out = canvas(952, 20); out.paste(g, (0, 0), m)
        save(out, f"boss_gyeol_row_{nm}", "gyeol", 952, 20, "보스 맺힘 채움(일반 혼 맺힘과 같은 하늘색)" if nm == "fill" else "보스 맺힘 줄어든 자리 잔상")
    br = canvas(952, 20); d = ImageDraw.Draw(br)
    rrect(d, (0, 0, 952, 20), 8, fill=rgba((10, 14, 26), 255))
    rr = random.Random(5); x = 20
    while x < 940:                                                                                # 깨진 줄: 먹 바닥에 한지색 금이 이어지고, 틈이 빛난다
        pts = crack_poly(rr, x, 1, 19, 3.2, 3.8); draw_crack(d, pts, 1.4, 240); x += rr.uniform(34, 70)
    save(br, "boss_gyeol_row_broken", "gyeol", 952, 20, "한 줄을 깬 뒤 남은 빈 줄(금 간 채 비어 있음). 처결 창 4초 동안 이 줄이 보인다")


# ------------------------------------------------------------------ 처결 표식·사슬선
def keycap(d, x, y, s=20):
    rrect(d, (x, y, x + s, y + s), 5, fill=rgba(HANJI), outline=rgba(INK, 255), width=1.5)
    rrect(d, (x + 2, y + s - 4, x + s - 2, y + s - 2), 1, fill=rgba((200, 186, 160), 255))        # 키 아랫면 두께

def make_marks():
    """혼 머리 위 처결 표식. 내가 겨눈 혼 하나 위에만 뜬다. 꼬리(▼)가 그 혼을 가리킨다."""
    def pill(w, items, name, note):
        h = 56; im = canvas(w, h); d = ImageDraw.Draw(im)
        g = grad_v(w, 44, (29, 42, 77), (15, 23, 41), 240, 240); m = mask_of(lambda dd: dd.rounded_rectangle([0, 0, w * S - 1, 44 * S - 1], radius=14 * S, fill=255), w, 44)
        im.paste(g, (0, 0), m); rrect(d, (0, 0, w, 44), 14, outline=rgba(HANJI, 255), width=2)
        poly(d, [(w / 2 - 7, 43), (w / 2 + 7, 43), (w / 2, 54)], fill=rgba(HANJI, 255))           # 꼬리: 겨눈 혼을 가리킴
        poly(d, [(w / 2 - 5, 42), (w / 2 + 5, 42), (w / 2, 50)], fill=rgba(NAVY, 255))
        for kind, x0 in items:
            sm = canvas(60, 60); (glyph_tendo if kind == "t" else glyph_pahon)(sm, 30, 30, TEAL if kind == "t" else ORANGE, 255, 0.58, small=True)
            sm = sm.resize((30 * S, 30 * S), Image.LANCZOS); im.alpha_composite(sm, (int(x0 * S), int(7 * S)))
            keycap(d, x0 + 33, 12, 20)
        save(im, name, "mark", w, h, note)
    pill(124, [("t", 8), ("p", 66)], "mark_exec_pair", "혼 머리 위 표식: ▲(청록)+키캡 / ✕(주황)+키캡. 키캡 글자(E·R·패드 버튼)는 코드. 꼬리 끝이 혼 머리 위 0.2m")
    pill(66, [("p", 8)], "mark_exec_pahon_only", "덩어리(천도 불가)용: ✕ + 키캡만")

    # 연속 천도 사슬선: 바닥에 눕히는 조각(1 m = 128 px). 가로 반복(period 128). 무늬는 세로 고리·가로 고리가 번갈아
    def chain_tile(dashed):
        w, h = 128, 40; im = canvas(w, h); d = ImageDraw.Draw(im)
        cy = h / 2
        def oval(cx, rx, ry, col, wd):
            for off in (-w, 0, w):
                ellipse(d, (cx + off - rx, cy - ry, cx + off + rx, cy + ry), outline=col, width=wd)
        links = [(16, 15, 7, True), (48, 5, 10, False), (80, 15, 7, True), (112, 5, 10, False)]
        if dashed: links = [links[0], links[2]]                                                   # 약한 사슬: 고리 둘만 남아 끊길 듯
        for cx, rx, ry, flat in links:
            oval(cx, rx, ry, rgba((18, 20, 30), 255), 5.2)                                       # 먹 바깥
        for cx, rx, ry, flat in links:
            oval(cx, rx, ry, rgba(CHAIN, 255 if not dashed else 170), 2.6)                       # 청백 사슬
        return im
    save(chain_tile(False), "chain_seg", "mark", 128, 40, "연속 천도 사슬선 조각 — 바닥에 눕혀 1 m 길이(가로 반복). 두 혼 사이 거리만큼 가로로 반복해 깐다. 0.8초 창이 남아 있을 때")
    save(chain_tile(True), "chain_seg_weak", "mark", 128, 40, "창이 거의 닫힐 때(0.2초 남음) 바꿔 끼우는 약한 사슬(고리 둘·옅게). 끊기면 숨김")
    im = canvas(56, 56); d = ImageDraw.Draw(im)
    ellipse(d, (6, 6, 50, 50), outline=rgba((18, 20, 30), 255), width=6); ellipse(d, (6, 6, 50, 50), outline=rgba(CHAIN, 255), width=3)
    ellipse(d, (20, 20, 36, 36), fill=rgba(CHAIN, 230), outline=rgba((18, 20, 30), 255), width=2)
    save(im, "chain_node", "mark", 56, 56, "사슬선 끝에 얹는 고리(두 혼 발밑 각각). 가운데가 찬 점")


if __name__ == "__main__":
    lum = make_exec_slots(); make_hud(); make_gyeol(); make_marks(); dump_manifest()
    print("천도 칸 평균 밝기", round(lum["tendo"], 1), "파혼 칸", round(lum["pahon"], 1), "차이 %", round(abs(lum["tendo"] - lum["pahon"]) / lum["tendo"] * 100, 2))
    print(len(MANIFEST), "종 저장")
