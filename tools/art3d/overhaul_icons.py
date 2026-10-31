"""개편 폰 버튼 그림(아트, 2026-10-31) — PR #56(개편 P1 3차)에서 임시 원 버튼이던 것들의 그림.
실행: python3 tools/art3d/overhaul_icons.py   (결과: assets3d/ui/overhaul/btn/ + unity/Assets/Resources/Sprites/overhaul/btn/, 목록은 _manifest.json)

무엇을 그리나 (이름 = 코드가 읽는 이름)
 물약     potion_on(약이 있음) · potion_off(약 없음 · 점선) · potion_hot(누른 순간 겉 빛) · potion_count(남은 수 글자판)
 메뉴     menu_badge — 왼쪽 위 초상 옆에 붙는 '책 등' 쪽지. 초상을 톡 치면 창이 열린다는 단서(판정은 코드의 눈에 안 보이는 원)
 공격     atk · atk_hot — 붉은 인 고리 + 사슬 벤 자국(철삭). 글자("공격")는 코드가 아래에
 피하기   dodge — 남청 고리 + 스치는 바람. 글자는 코드
 기술 칸  skill_ring_ready(금 고리) · skill_ring_cool(재사용 대기, 어둡게) — 안쪽 비움에 도술 아이콘 64×64를 얹는다
 무기 교체 안내  swap_hint — 위로 끌어올리라는 겹쳐진 화살표 둘(글자는 코드)

지킨 규칙(기존 개편 한 벌과 같음)
 · 글자·숫자는 그림에 안 넣는다(코드가 얹음). 한글 문구는 명세 용어표 그대로 코드에서.
 · 색: 천도 청록·파혼 주황은 그 두 버튼 전용, 예고 장판 빨강과 헷갈리지 않게 물약은 한지 고리 + 붉은 인(체력과 같은 계열).
 · 모양으로도 갈림(색약): 물약 = 호리병, 공격 = 사슬 벤 자국, 피하기 = 스치는 선.
 · IP: 특정 작품의 약병·아이콘을 따라 그리지 않았다. 호리병·사슬·바람은 설화·일상 도상."""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from overhaul_lib import *

FOLDER = "btn"
GREEN = (126, 170, 120)   # 호리병 끈·약초 포인트(한지 위 먹물 약 느낌) — 파랑/청록과 안 섞이게 누런 풀색


def disc(w, ring, ring_a=255, ring_w=4, fill_a=235, inset=3):
    """남청 먹판 원 + 색 고리 + 안쪽 가는 선. 기존 천도·파혼 버튼과 같은 재료."""
    im = canvas(w, w); d = ImageDraw.Draw(im)
    g = grad_v(w, w, (29, 42, 77), (15, 23, 41), fill_a, fill_a)
    m = mask_of(lambda dd: dd.ellipse([inset * S, inset * S, (w - inset) * S - 1, (w - inset) * S - 1], fill=255), w, w)
    im.paste(g, (0, 0), m)
    ellipse(d, (inset, inset, w - inset, w - inset), outline=rgba(ring, ring_a), width=ring_w)
    ellipse(d, (inset + ring_w + 3, inset + ring_w + 3, w - inset - ring_w - 3, w - inset - ring_w - 3), outline=rgba(LINE, 170), width=1.4)
    return im


def hot_of(base_fn, w, col, pad=8):
    """눌렀을 때·시전 중 겉 빛: 사방 pad 만큼 번지는 고리 + 같은 가운데"""
    big = canvas(w + pad * 2, w + pad * 2); glow = canvas(w + pad * 2, w + pad * 2); gd = ImageDraw.Draw(glow)
    ellipse(gd, (pad, pad, pad + w, pad + w), outline=rgba(col, 230), width=5)
    glow = glow.filter(ImageFilter.GaussianBlur(5 * S)); big.alpha_composite(glow); big.alpha_composite(base_fn(), (pad * S, pad * S))
    return big


# ------------------------------------------------------------------ 물약 (호리병)
def gourd(im, cx, cy, k=1.0, liquid=True, a=255, outline=HANJI, dashed=False):
    """호리병: 위 작은 공 + 잘록한 허리 + 아래 큰 공을 '한 덩어리 모양판(마스크)'으로 만들고,
    그 판을 부풀려 테두리를 낸다 → 공이 겹치는 자리에 이음 줄이 안 생긴다. liquid=True면 아래 공에 붉은 인 빛 물약이 찬다."""
    from PIL import ImageChops
    W4, H4 = im.size
    def shape(grow=0.0):
        m = Image.new("L", (W4, H4), 0); md = ImageDraw.Draw(m)
        r_t, r_b = (8.5 + grow) * k, (15.5 + grow) * k
        ty, by = cy - 15 * k, cy + 8 * k
        md.ellipse([(cx - r_t) * S, (ty - r_t) * S, (cx + r_t) * S, (ty + r_t) * S], fill=255)
        md.ellipse([(cx - r_b) * S, (by - r_b) * S, (cx + r_b) * S, (by + r_b) * S], fill=255)
        nk = (4.5 + grow) * k
        md.polygon([((cx - nk) * S, (ty + 2 * k) * S), ((cx + nk) * S, (ty + 2 * k) * S), ((cx + nk + 2.5 * k) * S, (by - 9 * k) * S), ((cx - nk - 2.5 * k) * S, (by - 9 * k) * S)], fill=255)
        return m
    d = ImageDraw.Draw(im); col = rgba(outline, a)
    ty, by = cy - 15 * k, cy + 8 * k
    inner, outer = shape(0), shape(2.4)
    if dashed:   # 빈 병: 같은 모양의 점선 윤곽(속 비어 있음)
        ring = ImageChops.subtract(outer, inner)
        # 점선: 위→아래 일정 간격으로 윤곽을 잘라낸다(방사 줄무늬 마스크)
        cut = Image.new("L", (W4, H4), 0); cd = ImageDraw.Draw(cut)
        for i in range(18):
            a0 = 360 * i / 18; cd.pieslice([(cx - 40 * k) * S, (cy - 4 * k - 40 * k) * S, (cx + 40 * k) * S, (cy - 4 * k + 40 * k) * S], a0, a0 + 12, fill=255)
        ring = ImageChops.multiply(ring, cut)
        im.paste(Image.new("RGBA", (W4, H4), col), (0, 0), ring)
        return
    im.paste(Image.new("RGBA", (W4, H4), col), (0, 0), outer)               # 한지 테두리(바깥판)
    im.paste(Image.new("RGBA", (W4, H4), rgba(ABYSS)), (0, 0), inner)       # 먹 속
    if liquid:
        water = Image.new("L", (W4, H4), 0); ImageDraw.Draw(water).rectangle([0, int((by - 7 * k) * S), W4, H4], fill=255)
        wm = ImageChops.multiply(shape(-2.0), water)                          # 아래 공 3/4쯤 찬 물약
        fill = grad_v(W4 // S, H4 // S, (226, 104, 88), (150, 52, 48), 255, 255)
        im.paste(fill, (0, 0), wm)
        d.line([((cx - 9 * k) * S, (by - 7 * k) * S), ((cx + 9 * k) * S, (by - 7 * k) * S)], fill=rgba((255, 190, 170), 200), width=int(1.6 * S))   # 물 윗면 빛
        ellipse(d, (cx - 11 * k, by - 3 * k, cx - 7 * k, by + 3 * k), fill=rgba((255, 255, 255), 150))                                           # 반짝
    rrect(d, (cx - 4.5 * k, ty - 8.5 * k - 6 * k, cx + 4.5 * k, ty - 8.5 * k + 2 * k), 2, fill=rgba(GOLD))          # 금 마개
    line(d, [(cx + 6 * k, ty - 2 * k), (cx + 17 * k, ty + 4 * k), (cx + 15 * k, by - 2 * k)], rgba(GREEN), 2.4 * k)  # 풀색 끈


def make_potion():
    W = 96
    def on():
        im = disc(W, HANJI, 255, 4); gourd(im, W / 2, W / 2 + 1, 1.45); return im
    save(on(), "potion_on", FOLDER, W, W, "물약 버튼 · 약이 있음(한지 고리 + 호리병 + 붉은 인 빛 물약). 남은 수는 potion_count 위에 코드가 글자로")
    off = disc(W, HANJI, 120, 4, fill_a=200); gourd(off, W / 2, W / 2 + 1, 1.45, liquid=False, a=130, dashed=True)
    save(off, "potion_off", FOLDER, W, W, "물약 버튼 · 약 없음(속 빈 점선 호리병, 고리 흐리게) — 누르면 '회복약이 없다' 안내만")
    save(hot_of(on, W, HANJI), "potion_hot", FOLDER, W + 16, W + 16, "물약 누른 순간 겉 빛(사방 8px 번짐) — 가운데는 potion_on과 같다")
    im = canvas(40, 28); d = ImageDraw.Draw(im)
    rrect(d, (1, 1, 39, 27), 11, fill=rgba(ABYSS, 245), outline=rgba(HANJI, 235), width=2)
    save(im, "potion_count", FOLDER, 40, 28, "물약 오른쪽 아래에 걸치는 남은 수 글자판(빈 알약). 숫자는 코드. 중심은 버튼 중심에서 (+30,+30)쯤", pivot=[0.5, 0.5])


# ------------------------------------------------------------------ 메뉴 (책 등 쪽지)
def make_menu():
    W = 56
    im = disc(W, HANJI, 255, 3.2, inset=2)
    d = ImageDraw.Draw(im)
    # 책: 왼쪽 두꺼운 등(먹+금 띠) + 오른쪽 한지 책장 가장자리 줄 — 폰 모양으로 안 읽히게 가로가 넓은 책
    bx0, by0, bx1, by1 = 12, 13, 44, 43
    rrect(d, (bx0 + 3, by0 + 3, bx1 + 1, by1 + 1), 3, fill=rgba(HANJI, 255))                 # 뒤쪽 책장
    for yy in (by0 + 8, by0 + 14, by0 + 20, by0 + 26): line(d, [(bx1 - 4, yy), (bx1 + 0.5, yy)], rgba(INK, 140), 1.2)
    rrect(d, (bx0, by0, bx1 - 4, by1 - 2), 3, fill=rgba(INK, 255), outline=rgba(HANJI), width=2)   # 앞표지
    rrect(d, (bx0, by0, bx0 + 7, by1 - 2), 3, fill=rgba((78, 58, 52), 255))                  # 등
    for y in (by0 + 6, by1 - 9): line(d, [(bx0, y), (bx0 + 7, y)], rgba(GOLD), 2.4)
    ellipse(d, (bx0 + 16, by0 + 9, bx0 + 21, by0 + 14), outline=rgba(SEAL), width=1.8); ellipse(d, (bx0 + 17.4, by0 + 10.4, bx0 + 19.6, by0 + 12.6), fill=rgba(SEAL))   # 표지 붉은 인 도장
    save(im, "menu_badge", FOLDER, W, W, "메뉴 쪽지(책 한 권, 표지에 붉은 인). 왼쪽 위 초상 오른쪽 아래에 걸쳐 붙인다 → 초상을 톡 치면 창. 눈에 안 보이는 눌림 판정(지름 132)은 그대로 코드")
    hot = hot_of(lambda: disc(W, HANJI, 255, 3.2, inset=2), W, HANJI, 6)
    save(hot, "menu_badge_hot", FOLDER, W + 12, W + 12, "메뉴 눌린 순간 겉 빛")


# ------------------------------------------------------------------ 공격 (사슬 벤 자국)
def slash_arc(d, cx, cy, r, a0, a1, col, w):
    d.arc([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], a0, a1, fill=col, width=int(w * S))


def chain_link(d, x, y, ang, col, edge, rx=5.2, ry=3.2, w=2.2):
    """사슬 고리 하나(타원 테두리). ang = 진행 방향(도)"""
    t = math.radians(ang)
    pts = []
    for i in range(0, 361, 15):
        u = math.radians(i); px, py = rx * math.cos(u), ry * math.sin(u)
        pts.append((x + px * math.cos(t) - py * math.sin(t), y + px * math.sin(t) + py * math.cos(t)))
    d.line([(px * S, py * S) for px, py in pts], fill=rgba(edge), width=int((w + 1.8) * S), joint="curve")
    d.line([(px * S, py * S) for px, py in pts], fill=rgba(col), width=int(w * S), joint="curve")


def make_attack():
    W = 160
    def build(bright):
        im = disc(W, RED if bright else SEAL, 255, 5.5, fill_a=235, inset=4)
        d = ImageDraw.Draw(im)
        cx, cy = W / 2, W / 2 - 6   # 글자 자리(아래 22%)를 비우려고 살짝 위
        # 사선 벤 자국 셋(왼쪽 위 → 오른쪽 아래, 끝이 뾰족하게 가늘어짐) — 가운데가 가장 길다
        def stroke(x0, y0, x1, y1, w0, col):
            dx, dy = x1 - x0, y1 - y0; L = math.hypot(dx, dy); nx, ny = -dy / L, dx / L
            mx, my = (x0 + x1) / 2 + nx * 5, (y0 + y1) / 2 + ny * 5            # 살짝 휜 가운데 점
            poly(d, [(x0 + nx * w0, y0 + ny * w0), (mx + nx * w0 * 0.8, my + ny * w0 * 0.8), (x1, y1), (mx - nx * w0 * 0.8, my - ny * w0 * 0.8), (x0 - nx * w0, y0 - ny * w0)], fill=col)
        stroke(cx - 22, cy - 38, cx + 26, cy + 26, 4.2, rgba(HANJI, 170))
        stroke(cx - 36, cy - 30, cx + 10, cy + 38, 5.6, rgba(HANJI))
        stroke(cx - 50, cy - 18, cx - 6, cy + 42, 4.2, rgba(HANJI, 170))
        # 사슬 고리 셋: 자국 시작에서 위로 늘어진 꼬리
        for i, (x, y, ang) in enumerate(((cx + 34, cy - 44, 20), (cx + 44, cy - 38, 30), (cx + 53, cy - 30, 40))):
            chain_link(d, x, y, ang, CHAIN, INK, 5.4 - i * 0.5, 3.3 - i * 0.3)
        return im
    save(build(False), "atk", FOLDER, W, W, "공격 버튼(지름 160): 붉은 인 고리 + 사선 벤 자국 셋 + 사슬 고리. 그림은 위쪽에 모아 아래 22%는 '공격' 글자 자리(코드)")
    def _b(): return build(True)
    save(hot_of(_b, W, RED, 10), "atk_hot", FOLDER, W + 20, W + 20, "공격 누른 순간(고리 밝은 붉은색 + 겉 빛 사방 10px)")


# ------------------------------------------------------------------ 피하기 (바람)
def make_dodge():
    W = 104
    im = disc(W, (106, 130, 196), 255, 4)
    d = ImageDraw.Draw(im)
    cx, cy = W / 2, W / 2 - 5
    # 스치는 바람 선 셋(길이 다르게) + 흩날리는 점
    for i, (y, x0, x1, wd) in enumerate(((-14, -22, 18, 4.2), (0, -34, 30, 5.6), (14, -22, 14, 4.2))):
        pts = [(cx + x0 + t * (x1 - x0) / 20, cy + y + 4 * math.sin(t / 20 * math.pi * 0.9)) for t in range(21)]
        line(d, pts, rgba(HANJI, 255 - i * 25), wd)
        ellipse(d, (cx + x1 - 1.5, cy + y + 2 - 1.5, cx + x1 + 3.5, cy + y + 2 + 3.5), fill=rgba(HANJI, 230))
    ellipse(d, (cx + 24, cy - 24, cx + 28, cy - 20), fill=rgba(HANJI, 170)); ellipse(d, (cx + 31, cy - 12, cx + 34, cy - 9), fill=rgba(HANJI, 130))
    save(im, "dodge", FOLDER, W, W, "피하기 버튼(지름 104): 남청 고리 + 스치는 바람 선. 아래 22%는 '피하기' 글자 자리(코드)")


# ------------------------------------------------------------------ 기술 칸 고리 · 무기 교체 안내
def make_skill_ring():
    W = 104
    for nm, col, a, fa, note in (("ready", GOLD, 255, 220, "기술 칸 · 쓸 수 있음(금 고리)"), ("cool", HANJI, 120, 245, "기술 칸 · 재사용 대기(고리·바탕 어둡게). 남은 초는 코드")):
        im = disc(W, col, a, 4, fill_a=fa)
        save(im, f"skill_ring_{nm}", FOLDER, W, W, note + ". 도술 아이콘은 안쪽 64×64에 얹는다")


def make_swap_hint():
    im = canvas(64, 40); d = ImageDraw.Draw(im)
    for i, y in enumerate((9, 21)):
        pts = [(32 - 16, y + 12), (32, y), (32 + 16, y + 12)]
        line(d, pts, rgba(INK, 200 - i * 60), 7); line(d, pts, rgba(HANJI, 255 - i * 90), 4)
    save(im, "swap_hint", FOLDER, 64, 40, "무기 바꾸기 단서: 겹친 위쪽 화살표 둘(공격 버튼 바로 위, 글자는 코드). 위로 끌어올리라는 뜻")


if __name__ == "__main__":
    make_potion(); make_menu(); make_attack(); make_dodge(); make_skill_ring(); make_swap_hint(); dump_manifest()
    print(len(MANIFEST), "종 저장")
