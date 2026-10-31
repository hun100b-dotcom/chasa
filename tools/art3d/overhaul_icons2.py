"""개편 폰 버튼 그림 2차(아트, 2026-10-31) — PR #57 에서 남은 세 가지: 도술 아이콘 본체 · Q 버튼 무기별 그림 · 상호작용(F) 버튼.
실행: python3 tools/art3d/overhaul_icons2.py   (결과: assets3d/ui/overhaul/{skill,btn}/ + unity/Assets/Resources/Sprites/overhaul/{skill,btn}/, 목록은 _manifest.json)

이름 = 코드가 읽는 이름. 한글 기술 이름 → 그림 이름 연결표는 코드(Core/DosulIcons.cs)에 있다.
 도술(skill/, 64×64)  부름 5: call_grab·call_wisp·call_light·call_path·call_seven
                       줄 5:   chain_coil·chain_haul·chain_dash·chain_thread·chain_fence
                       얼룩 5: stain_burst·stain_aura·stain_ride·stain_shard·stain_shadow
                       갈래 쪽지 3(패시브·그림 없는 도술의 대신): branch_call·branch_chain·branch_stain
 Q 버튼(btn/, 104×104) q_chain(끌기)·q_mace(땅울림)·q_bell(부르기)·q_trident(꽂기)·q_brush(이름)·q_slash(베기, 무기 기술 없는 무기)
 상호작용(btn/)        use(한지 고리 + 손) · use_hot(누른 순간)

지킨 규칙(#51·#57 과 같음)
 · 글자·숫자는 그림에 안 넣는다(코드가 얹음). Q·F 는 그림을 위 78% 에 모아 아래 22% 는 코드가 글자("끌기" 등)를 쓴다.
 · 천도 청록·파혼 주황은 그 두 칸 전용 → 쓰지 않았다(옛 F 버튼의 청록 고리도 한지 고리로 바꿈).
 · 갈래는 색 + 모양 + 모서리 표식으로 셋 다 갈린다(색약): 부름 = 금 + ↑ 삼각 / 줄 = 은청 + ● 점 / 얼룩 = 먹자주 + × .
 · IP: 특정 작품의 기술 아이콘을 참조하지 않음. 사슬·호리병·붓·방울·삼지창·손은 설화·일상 도상.
"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from overhaul_lib import *
from overhaul_icons import disc, hot_of

PURPLE = (176, 132, 206)    # 얼룩 갈래 색 — 먹이 번진 자줏빛. 파혼 주황·예고 빨강과 거리를 둠
WOOD = (160, 114, 74)       # 방망이·붓대
STEEL = (206, 214, 232)     # 날·쇠
SK = 64                     # 도술 아이콘 크기(기술 칸 고리 안쪽 64×64)


# ------------------------------------------------------------------ 공용 붓
def gline(d, pts, col, w, edge=INK):
    """먹 테두리 + 색 선: 어두운 남청 바탕에서도, 한지 색 위에서도 모양이 또렷하게 읽힌다"""
    line(d, pts, rgba(edge, 235), w + 2.6); line(d, pts, rgba(col), w)


def gpoly(d, pts, col, edge=INK, ew=1.8):
    poly(d, pts, fill=rgba(col)); line(d, list(pts) + [pts[0]], rgba(edge, 235), ew)


def gell(d, box, col, edge=INK, ew=1.8):
    ellipse(d, box, fill=rgba(col), outline=rgba(edge, 235), width=ew)


def gring(d, cx, cy, r, col, w, edge=INK):
    ellipse(d, (cx - r - w / 2 - 1.3, cy - r - w / 2 - 1.3, cx + r + w / 2 + 1.3, cy + r + w / 2 + 1.3), outline=rgba(edge, 235), width=w + 2.6)
    ellipse(d, (cx - r - w / 2, cy - r - w / 2, cx + r + w / 2, cy + r + w / 2), outline=rgba(col), width=w)


def arc_pts(cx, cy, r, a0, a1, n=14):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def link(d, x, y, ang, col, rx=6.0, ry=3.6, w=2.4):
    """사슬 고리 하나(타원 테두리)"""
    t = math.radians(ang); pts = []
    for i in range(0, 361, 15):
        u = math.radians(i); px, py = rx * math.cos(u), ry * math.sin(u)
        pts.append((x + px * math.cos(t) - py * math.sin(t), y + px * math.sin(t) + py * math.cos(t)))
    gline(d, pts, col, w)


def arrow_head(d, x, y, ang, col, size=7):
    t = math.radians(ang)
    p = [(x, y), (x - size * math.cos(t - 0.5), y - size * math.sin(t - 0.5)), (x - size * math.cos(t + 0.5), y - size * math.sin(t + 0.5))]
    gpoly(d, p, col)


def corner_mark(d, kind, col):
    """왼쪽 위 모서리 표식 — 색을 못 구분해도 갈래가 읽힌다: 부름 ↑ 삼각 · 줄 ● · 얼룩 ×"""
    cx, cy = 9, 9
    if kind == "call": gpoly(d, [(cx, cy - 6), (cx + 6, cy + 5), (cx - 6, cy + 5)], col)
    elif kind == "chain": gell(d, (cx - 5, cy - 5, cx + 5, cy + 5), col)
    else:
        gline(d, [(cx - 5, cy - 5), (cx + 5, cy + 5)], col, 2.8); gline(d, [(cx + 5, cy - 5), (cx - 5, cy + 5)], col, 2.8)


# ------------------------------------------------------------------ 도술 15 (+ 갈래 쪽지 3)
def sk_call(name, note, body):
    im = canvas(SK, SK); d = ImageDraw.Draw(im)
    body(d, GOLD, HANJI); corner_mark(d, "call", GOLD)
    save(im, name, "skill", SK, SK, note)


def sk_chain(name, note, body):
    im = canvas(SK, SK); d = ImageDraw.Draw(im)
    body(d, CHAIN, HANJI); corner_mark(d, "chain", CHAIN)
    save(im, name, "skill", SK, SK, note)


def sk_stain(name, note, body):
    im = canvas(SK, SK); d = ImageDraw.Draw(im)
    body(d, PURPLE, HANJI); corner_mark(d, "stain", PURPLE)
    save(im, name, "skill", SK, SK, note)


def make_call():
    c = SK / 2 + 2

    def grab(d, m, h):   # 붙잡아 부르기: 한가운데 혼(한지 원)으로 세 방향에서 모이는 금 화살
        for ang in (90, 210, 330):
            t = math.radians(ang); x0, y0 = c + 26 * math.cos(t), c + 26 * math.sin(t); x1, y1 = c + 11 * math.cos(t), c + 11 * math.sin(t)
            gline(d, [(x0, y0), (x1, y1)], m, 3.6); arrow_head(d, c + 8 * math.cos(t), c + 8 * math.sin(t), ang + 180, m, 7)
        gell(d, (c - 6, c - 6, c + 6, c + 6), h)
    sk_call("call_grab", "붙잡아 부르기 — 가운데 혼으로 모이는 금 화살 셋", grab)

    def wisp(d, m, h):   # 혼불 날리기: 오른쪽 위로 날아가는 눈물꼴 혼불 + 꼬리줄
        pts = [(c + 18, c - 16), (c + 5, c - 14), (c - 8, c - 4), (c - 6, c + 8), (c + 4, c + 10), (c + 14, c + 2), (c + 22, c - 10)]
        gpoly(d, [(c + 22, c - 22), (c + 8, c - 18), (c - 4, c - 6), (c - 4, c + 8), (c + 6, c + 12), (c + 16, c + 4), (c + 20, c - 8)], h)
        gline(d, [(c - 14, c + 14), (c - 4, c + 4)], m, 3.0); gline(d, [(c - 22, c + 8), (c - 12, c + 0)], m, 2.4); gline(d, [(c - 8, c + 22), (c + 0, c + 14)], m, 2.4)
        gell(d, (c + 7, c - 2, c + 13, c + 4), m)
    sk_call("call_wisp", "혼불 날리기 — 날아가는 혼불(눈물꼴 한지) + 금 꼬리줄", wisp)

    def light(d, m, h):  # 이름 비추기: 가운데 둥근 등 + 사방 빛살
        for i in range(8):
            t = math.radians(i * 45); r0, r1 = 14, 24 if i % 2 == 0 else 20
            gline(d, [(c + r0 * math.cos(t), c + r0 * math.sin(t)), (c + r1 * math.cos(t), c + r1 * math.sin(t))], m, 3.0)
        gell(d, (c - 10, c - 10, c + 10, c + 10), h); gell(d, (c - 4, c - 4, c + 4, c + 4), m)
    sk_call("call_light", "이름 비추기 — 둥근 등 + 빛살 여덟", light)

    def path(d, m, h):   # 배웅길: 멀어지며 좁아지는 두 길선 + 가운데 점선 + 위 작은 문(혼이 가는 곳)
        gline(d, [(c - 22, c + 24), (c - 5, c - 8)], m, 3.6); gline(d, [(c + 22, c + 24), (c + 5, c - 8)], m, 3.6)
        for y, hw in ((c + 20, 1.6), (c + 10, 1.3), (c + 2, 1.0)): gline(d, [(c, y - 3), (c, y + 2)], h, hw * 2)
        gpoly(d, [(c - 7, c - 8), (c - 7, c - 20), (c, c - 26), (c + 7, c - 20), (c + 7, c - 8)], h)
    sk_call("call_path", "배웅길 — 좁아지는 길 + 끝의 작은 문", path)

    def seven(d, m, h):  # 일곱 이름(깊은 도술): 일곱 점이 국자 꼴(북두) + 이은 금선
        pts = [(c - 24, c - 8), (c - 14, c - 12), (c - 4, c - 10), (c + 5, c - 2), (c + 8, c + 10), (c + 20, c + 14), (c + 24, c + 2)]
        gline(d, pts, m, 2.0)
        for p in pts: gell(d, (p[0] - 3.8, p[1] - 3.8, p[0] + 3.8, p[1] + 3.8), h)
    sk_call("call_seven", "일곱 이름(깊은 도술) — 국자 꼴로 이어진 일곱 점", seven)


def make_chain():
    c = SK / 2 + 2

    def coil(d, m, h):   # 휘감기: 한가운데 점을 두 바퀴 감은 사슬 고리
        gring(d, c, c, 17, m, 3.4)
        for i in range(8):
            t = math.radians(i * 45 + 22); link(d, c + 17 * math.cos(t), c + 17 * math.sin(t), math.degrees(t) + 90, m, 5.0, 3.0, 2.2)
        gell(d, (c - 6, c - 6, c + 6, c + 6), h)
    sk_chain("chain_coil", "휘감기 — 가운데 혼을 둥글게 감은 사슬 고리", coil)

    def haul(d, m, h):   # 여럿 끌기: 위 세 점이 아래 한 갈고리로 끌려옴
        for x in (c - 18, c, c + 18):
            gell(d, (x - 5, c - 26, x + 5, c - 16), h); gline(d, [(x, c - 14), (c, c + 10)], m, 2.8)
        gline(d, [(c, c + 10), (c, c + 18)], m, 3.6); gline(d, [(c - 7, c + 20), (c, c + 26), (c + 7, c + 20)], m, 3.6)
        arrow_head(d, c, c + 6, 90, m, 6)
    sk_chain("chain_haul", "여럿 끌기 — 세 혼이 한 갈고리로 끌려옴", haul)

    def dash(d, m, h):   # 매듭 걸음: 사슬을 걸고 가는 돌진 — 가로 속도선 + 앞 고리 둘 + 화살촉
        for y in (c - 12, c + 12): gline(d, [(c - 28, y), (c - 12, y)], m, 3.0)
        gline(d, [(c - 28, c), (c - 4, c)], m, 3.6)
        link(d, c + 4, c, 0, m, 8.0, 5.0, 3.0); link(d, c + 17, c, 0, m, 8.0, 5.0, 3.0)
        arrow_head(d, c + 29, c, 0, h, 8)
    sk_chain("chain_dash", "매듭 걸음 — 속도선과 앞서 나가는 사슬 고리·화살촉", dash)

    def thread(d, m, h):  # 한 줄 꿰기: 두 혼(원)을 한 사슬이 꿰뚫음
        gline(d, [(c - 28, c), (c + 28, c)], m, 3.0)
        for x in (c - 13, c + 13): gring(d, x, c, 8, h, 3.2)
        link(d, c - 26, c, 0, m, 4.6, 2.8, 2.0); link(d, c + 26, c, 0, m, 4.6, 2.8, 2.0)
    sk_chain("chain_thread", "한 줄 꿰기 — 두 고리(혼)를 한 줄로 꿴 사슬", thread)

    def fence(d, m, h):   # 쇠사슬 울(깊은 도술): 네모 울타리 + 네 모서리 말뚝 + 가운데 점
        pts = [(c - 20, c - 20), (c + 20, c - 20), (c + 20, c + 20), (c - 20, c + 20), (c - 20, c - 20)]
        gline(d, pts, m, 3.4)
        for x, y in pts[:4]: gpoly(d, [(x - 4.5, y - 4.5), (x + 4.5, y - 4.5), (x + 4.5, y + 4.5), (x - 4.5, y + 4.5)], h)
        gell(d, (c - 5, c - 5, c + 5, c + 5), h)
    sk_chain("chain_fence", "쇠사슬 울(깊은 도술) — 네 말뚝과 사슬 울타리, 가운데 혼", fence)


def make_stain():
    c = SK / 2 + 2

    def burst(d, m, h):  # 터뜨리기: 얼룩 한가운데서 사방으로 터지는 뾰족한 별
        pts = []
        for i in range(16):
            r = 26 if i % 2 == 0 else 12; t = math.radians(i * 22.5 - 90); pts.append((c + r * math.cos(t), c + r * math.sin(t)))
        gpoly(d, pts, m); gell(d, (c - 6, c - 6, c + 6, c + 6), h)
    sk_stain("stain_burst", "터뜨리기 — 얼룩이 터지는 뾰족한 별", burst)

    def aura(d, m, h):   # 원념 두르기: 몸(둥근 머리+어깨) 둘레를 도는 세 줄 불꽃 곡선
        gell(d, (c - 6, c - 14, c + 6, c - 2), h); gpoly(d, [(c - 12, c + 14), (c - 9, c + 2), (c + 9, c + 2), (c + 12, c + 14)], h)
        for a0 in (200, 320, 80): gline(d, arc_pts(c, c, 23, a0, a0 + 80), m, 3.6)
        for a0 in (200, 320, 80): arrow_head(d, c + 23 * math.cos(math.radians(a0 + 80)), c + 23 * math.sin(math.radians(a0 + 80)), a0 + 80 + 90, m, 6)
    sk_stain("stain_aura", "원념 두르기 — 몸을 도는 세 줄 곡선", aura)

    def ride(d, m, h):   # 얼룩 타기: 납작한 얼룩 위로 위쪽 화살표(빨라짐) 둘 + 속도선
        gell(d, (c - 26, c + 8, c + 26, c + 24), m)
        for dx in (-8, 8): gline(d, [(c + dx - 8, c + 2), (c + dx, c - 8), (c + dx + 8, c + 2)], h, 3.6)
        gline(d, [(c - 24, c - 2), (c - 16, c - 2)], h, 2.4); gline(d, [(c + 16, c - 2), (c + 24, c - 2)], h, 2.4)
    sk_stain("stain_ride", "얼룩 타기 — 납작한 얼룩 위 빠름 화살표", ride)

    def shard(d, m, h):  # 깨진 이름 던지기: 들쭉날쭉한 깨진 조각이 날아감 + 꼬리줄
        gpoly(d, [(c + 22, c - 22), (c + 4, c - 14), (c + 10, c - 4), (c - 6, c + 6), (c + 4, c + 8), (c - 12, c + 22), (c + 16, c + 2), (c + 8, c - 2), (c + 24, c - 12)], m)
        gline(d, [(c - 24, c + 24), (c - 12, c + 14)], h, 2.8); gline(d, [(c - 26, c + 12), (c - 18, c + 6)], h, 2.2); gline(d, [(c - 14, c + 26), (c - 6, c + 20)], h, 2.2)
    sk_stain("stain_shard", "깨진 이름 던지기 — 날아가는 들쭉날쭉 조각 + 꼬리", shard)

    def shadow(d, m, h):  # 금 간 그림자(깊은 도술): 어두운 사람 그림자 + 번개꼴 금
        gpoly(d, [(c - 18, c + 24), (c - 16, c + 6), (c - 6, c + 0), (c + 6, c + 0), (c + 16, c + 6), (c + 18, c + 24)], m)
        gell(d, (c - 8, c - 22, c + 8, c - 4), m)
        gline(d, [(c + 3, c - 24), (c - 3, c - 10), (c + 5, c - 2), (c - 4, c + 10), (c + 2, c + 26)], h, 3.0)
    sk_stain("stain_shadow", "금 간 그림자(깊은 도술) — 사람 그림자를 가르는 금", shadow)


def make_branch():
    """갈래 쪽지: 패시브·그림이 아직 없는 도술의 대신. 갈래 색 큰 표식 하나."""
    c = SK / 2
    for kind, col in (("call", GOLD), ("chain", CHAIN), ("stain", PURPLE)):
        im = canvas(SK, SK); d = ImageDraw.Draw(im)
        if kind == "call": gpoly(d, [(c, c - 22), (c + 20, c + 16), (c - 20, c + 16)], col, ew=2.4); gline(d, [(c, c + 16), (c, c + 26)], col, 4)
        elif kind == "chain": gring(d, c, c, 15, col, 5)
        else:
            gline(d, [(c - 17, c - 17), (c + 17, c + 17)], col, 6); gline(d, [(c + 17, c - 17), (c - 17, c + 17)], col, 6)
        save(im, f"branch_{kind}", "skill", SK, SK, f"갈래 쪽지({kind}) — 패시브·그림 없는 도술의 대신")


# ------------------------------------------------------------------ Q 버튼 (무기별)
QW = 104


def q_disc(name, note, body):
    """금 고리 원판(기술 칸과 한 벌) + 위 78% 에 무기 도상. 아래 22% 는 코드가 '끌기' 같은 글자"""
    im = disc(QW, GOLD, 255, 4)
    layer = canvas(QW, QW); body(ImageDraw.Draw(layer), QW / 2, QW / 2)   # 도상은 따로 그려 그대로 두고 위 78% 쪽에 앉힌다(작아 보이던 것 보정)
    k = 1.0; big = layer.resize((int(layer.width * k), int(layer.height * k)), Image.LANCZOS)
    im.alpha_composite(big, (int((layer.width - big.width) / 2), int((layer.height - big.height) / 2 - 6 * S)))
    save(im, name, "btn", QW, QW, note)


def make_q():
    def chain(d, cx, cy):   # 끌기(철삭): 사슬 세 고리가 갈고리에서 아래 왼쪽으로 끌려옴
        for i, (x, y) in enumerate(((cx + 14, cy - 18), (cx + 4, cy - 8), (cx - 6, cy + 2))):
            link(d, x, y, 40, CHAIN, 9.0, 5.4, 3.0)
        gline(d, [(cx - 14, cy + 12), (cx - 24, cy + 20)], CHAIN, 3.0)
        arrow_head(d, cx - 24, cy + 20, 135, HANJI, 9)
        gline(d, [(cx + 22, cy - 28), (cx + 30, cy - 22), (cx + 28, cy - 14)], GOLD, 3.6)   # 갈고리
    q_disc("q_chain", "Q 끌기(철삭) — 사슬 고리 셋이 갈고리에서 끌려옴 + 끄는 화살", chain)

    def mace(d, cx, cy):    # 땅울림(육모방망이): 내리친 방망이 + 바닥 퍼지는 물결 둘
        t = math.radians(-60)
        gline(d, [(cx - 14, cy + 10), (cx + 14, cy - 22)], WOOD, 7.0)
        gpoly(d, [(cx + 6, cy - 14), (cx + 20, cy - 30), (cx + 26, cy - 24), (cx + 12, cy - 8)], WOOD)
        for rx, ry, a in ((15, 5, 255), (24, 8, 170)): ellipse(d, (cx - 16 - rx, cy + 20 - ry, cx - 16 + rx, cy + 20 + ry), outline=rgba(HANJI, a), width=3)
        gline(d, [(cx - 30, cy + 12), (cx - 36, cy + 4)], HANJI, 2.4); gline(d, [(cx + 6, cy + 14), (cx + 12, cy + 6)], HANJI, 2.4)
    q_disc("q_mace", "Q 땅울림(육모방망이) — 내리친 방망이 + 바닥 물결", mace)

    def bell(d, cx, cy):    # 부르기(요령방울): 방울 + 양옆 소리 호
        gpoly(d, [(cx - 18, cy + 14), (cx - 14, cy - 4), (cx - 6, cy - 16), (cx + 6, cy - 16), (cx + 14, cy - 4), (cx + 18, cy + 14)], GOLD)
        gline(d, [(cx - 20, cy + 15), (cx + 20, cy + 15)], GOLD, 4.0); gell(d, (cx - 4, cy + 18, cx + 4, cy + 26), HANJI)
        gline(d, [(cx, cy - 16), (cx, cy - 24)], HANJI, 3.0)
        for s in (-1, 1):
            for r in (23, 30): gline(d, arc_pts(cx, cy, r, 330 if s > 0 else 150, 390 if s > 0 else 210, 8), HANJI, 2.6)
    q_disc("q_bell", "Q 부르기(요령방울) — 방울 + 퍼지는 소리 호", bell)

    def trident(d, cx, cy):   # 꽂기(삼지창): 세 갈래 창이 바닥(가로선)에 꽂힘
        gline(d, [(cx, cy - 30), (cx, cy + 14)], WOOD, 5.0)
        gline(d, [(cx - 14, cy + 4), (cx - 14, cy - 18)], STEEL, 3.6); gline(d, [(cx + 14, cy + 4), (cx + 14, cy - 18)], STEEL, 3.6)
        gline(d, [(cx - 14, cy + 4), (cx + 14, cy + 4)], STEEL, 3.6); gline(d, [(cx, cy + 14), (cx, cy + 24)], STEEL, 4.4)
        for x in (cx - 14, cx, cx + 14): gpoly(d, [(x - 4, cy - 18 - (6 if x == cx else 0)), (x + 4, cy - 18 - (6 if x == cx else 0)), (x, cy - 28 - (10 if x == cx else 0))], STEEL)
        gline(d, [(cx - 24, cy + 24), (cx + 24, cy + 24)], HANJI, 3.0)
    q_disc("q_trident", "Q 꽂기(삼지창) — 세 갈래 창이 땅(가로선)에 꽂힘", trident)

    def brush(d, cx, cy):     # 이름(명부 붓): 붓대 + 붓끝에서 흐르는 붉은 인 먹 + 둥근 획
        gline(d, [(cx + 22, cy - 26), (cx - 4, cy + 4)], WOOD, 5.0)
        gpoly(d, [(cx - 4, cy + 4), (cx - 12, cy + 16), (cx - 18, cy + 16), (cx - 10, cy + 2)], HANJI)
        gline(d, arc_pts(cx - 6, cy + 18, 14, 150, 330, 12), SEAL, 4.2)
        gell(d, (cx - 22, cy + 6, cx - 16, cy + 14), SEAL)
    q_disc("q_brush", "Q 이름(명부 붓) — 붓 + 붉은 인 먹으로 그은 둥근 획", brush)

    def slash(d, cx, cy):     # 베기(Q 기술 없는 무기): 굵은 한 줄 벤 자국(공격 버튼의 셋 벤 자국과 구분되게 하나·곡선)
        pts = arc_pts(cx - 18, cy + 30, 40, -80, -20, 12)
        gline(d, pts, HANJI, 7.0)
        gpoly(d, [(pts[-1][0] + 2, pts[-1][1] - 6), (pts[-1][0] + 12, pts[-1][1] + 8), (pts[-1][0] - 6, pts[-1][1] + 6)], HANJI)
    q_disc("q_slash", "Q 베기(Q 기술 없는 무기) — 곡선 한 줄 벤 자국", slash)


# ------------------------------------------------------------------ 상호작용(F)
def make_use():
    """한지 고리 + 손바닥(손 대기). 옛 F 버튼 청록 고리는 천도 칸과 같은 색이라 한지 색으로 바꿨다. 글자는 코드(아래 22%)"""
    def build():
        im = disc(QW, HANJI, 255, 4); d = ImageDraw.Draw(im)
        cx, cy = QW / 2, QW / 2 - 6
        # 손: 네 손가락 + 엄지 + 손바닥(둥근 사각) — 한지 색, 먹 테두리
        for i, (dx, top) in enumerate(((-14, -22), (-5, -30), (4, -30), (13, -22))):
            rrect(d, (cx + dx - 4.2, cy + top, cx + dx + 4.2, cy + 4), 4, fill=rgba(HANJI), outline=rgba(INK, 235), width=1.8)
        rrect(d, (cx - 19, cy - 6, cx + 19, cy + 24), 9, fill=rgba(HANJI), outline=rgba(INK, 235), width=1.8)
        gpoly(d, [(cx - 19, cy + 6), (cx - 30, cy - 2), (cx - 26, cy + 12), (cx - 19, cy + 16)], HANJI)
        for dx in (-9, 0, 9): line(d, [(cx + dx, cy - 2), (cx + dx, cy + 6)], rgba(INK, 90), 1.4)   # 손가락 마디 줄
        gline(d, arc_pts(cx, cy - 36, 8, 200, 340, 6), GOLD, 2.6)                                    # 손끝에서 번지는 금 파문
        return im
    im = build()
    save(im, "use", "btn", QW, QW, "상호작용(F) 버튼 — 한지 고리 + 손바닥. 그림은 위 78%, 아래 22% 는 코드가 대상 이름 글자(예: 서낭당)")
    save(hot_of(build, QW, HANJI), "use_hot", "btn", QW + 16, QW + 16, "상호작용 누른 순간 겉 빛(사방 8px)")


# ------------------------------------------------------------------ 확인판
def make_check():
    """사람이 한눈에 보는 판(글자는 안 넣음). 어두운 바탕 + 기술 칸 고리 위에 도술을 얹은 모습"""
    import json
    names = [n[len("skill/"):] for n in MANIFEST if n.startswith("skill/") and not n.startswith("skill/branch")]
    ring = Image.open(os.path.join(OUT, "btn", "skill_ring_ready@2x.png")).convert("RGBA")
    W = 5 * 220 + 20; H = 3 * 220 + 3 * 220 + 40 + 220
    sheet = Image.new("RGBA", (W, 4 * 220 + 20), (36, 36, 48, 255))
    for i, n in enumerate(names):
        x, y = 10 + (i % 5) * 220, 10 + (i // 5) * 220
        sheet.alpha_composite(ring, (x, y))
        ic = Image.open(os.path.join(OUT, "skill", n + "@2x.png")).convert("RGBA"); sheet.alpha_composite(ic, (x + 40, y + 40))
    row = 3
    qs = ["q_chain", "q_mace", "q_bell", "q_trident", "q_brush", "q_slash", "use"]
    sheet2 = Image.new("RGBA", (len(qs) * 220 + 10 + 3 * 130, 230), (36, 36, 48, 255))
    for i, n in enumerate(qs):
        sheet2.alpha_composite(Image.open(os.path.join(OUT, "btn", n + "@2x.png")).convert("RGBA"), (10 + i * 220, 10))
    for j, k in enumerate(("call", "chain", "stain")):
        sheet2.alpha_composite(Image.open(os.path.join(OUT, "skill", f"branch_{k}@2x.png")).convert("RGBA"), (10 + len(qs) * 220 + j * 130, 40))
    total = Image.new("RGBA", (max(sheet.width, sheet2.width), sheet.height + sheet2.height), (36, 36, 48, 255))
    total.alpha_composite(sheet, (0, 0)); total.alpha_composite(sheet2, (0, sheet.height))
    os.makedirs(os.path.join(ROOT, "assets3d", "previews"), exist_ok=True)
    total.convert("RGB").save(os.path.join(ROOT, "assets3d", "previews", "overhaul_icons2_check.png"))


if __name__ == "__main__":
    make_call(); make_chain(); make_stain(); make_branch(); make_q(); make_use(); dump_manifest(); make_check()
    print(len(MANIFEST), "종 저장")
