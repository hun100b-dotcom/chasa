"""HUD 그림 세트(표준 명세 hud-controls-spec.md 크기). 한지·먹 + 단청 금 + 남청 먹판.
원칙: 게임 화면 위에 얹히는 것은 어두운 먹판(남청 85%)에 금 테두리 — 밝은 한지는 글을 읽는 곳(대화·퀘스트·알림)에만.
색 의미: 체력=붉음, 도력=파랑, 경험=금, 천도·준비됨=청록, 위험=붉음. 주황은 파혼 전용이라 쓰지 않는다.
사용: python3 hud_art.py"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from ui_lib import *

K = 2   # 그리기 배율(저장은 1배+2배)
def S(v): return int(round(v * K))
def canvas(w, h): return Image.new("RGBA", (S(w), S(h)), (0, 0, 0, 0))
def vgrad(w, h, c0, c1):
    t = np.linspace(0, 1, h)[:, None, None]; a = np.array(c0, np.float32) * (1 - t) + np.array(c1, np.float32) * t; return np.repeat(a, w, axis=1)
def hgrad(w, h, c0, c1):
    t = np.linspace(0, 1, w)[None, :, None]; a = np.array(c0, np.float32) * (1 - t) + np.array(c1, np.float32) * t; return np.repeat(a, h, axis=0)
def gold_fill(w, h):   # 금박 세로 그라데이션
    return Image.fromarray(np.dstack([vgrad(w, h, (240, 208, 126), (176, 132, 50)), np.full((h, w), 255)]).astype(np.uint8), "RGBA")

def plate(w, h, r, alpha=222, border=True, gold_w=2, glow=None):
    """먹판: 남청 판 + 금 이중 테두리 + 안쪽 은은한 위쪽 빛. w,h 는 1배 px"""
    im = canvas(w, h); d = ImageDraw.Draw(im)
    body = vgrad(S(w), S(h), (34, 48, 86), (16, 24, 46)); m = rr_mask(S(w), S(h), S(r)); a = np.asarray(m, np.float32) / 255 * alpha
    im.alpha_composite(Image.fromarray(np.dstack([body, a]).astype(np.uint8), "RGBA"))
    if border:
        gf = gold_fill(S(w), S(h)); mo = rr_mask(S(w), S(h), S(r)); mi = rr_mask(S(w), S(h), max(1, S(r) - S(gold_w)), S(gold_w)); ring = ImageChops.subtract(mo, mi)
        im.alpha_composite(Image.composite(gf, Image.new("RGBA", gf.size, (0, 0, 0, 0)), ring))
        d.rounded_rectangle([S(gold_w + 2), S(gold_w + 2), S(w - gold_w - 3), S(h - gold_w - 3)], radius=max(1, S(r - gold_w - 2)), outline=(212, 169, 78, 110), width=1)
    if glow:
        gl = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(gl).rounded_rectangle([0, 0, S(w) - 1, S(h) - 1], radius=S(r), outline=tuple(glow) + (255,), width=S(3)); im.alpha_composite(gl.filter(ImageFilter.GaussianBlur(S(2.5))))
    return im

def hanji_card(w, h, r=8, seed=5, ink_w=2, gold=True):
    """한지 카드: 한지 질감 + 먹 테두리 + 금 안쪽선 + 모서리 금 꺾쇠"""
    im = canvas(w, h); m = rr_mask(S(w), S(h), S(r)); im.alpha_composite(rgba(hanji_tex(S(w), S(h), seed, 0.985), m)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([1, 1, S(w) - 2, S(h) - 2], radius=S(r), outline=INK + (255,), width=S(ink_w))
    if gold:
        d.rounded_rectangle([S(ink_w + 3), S(ink_w + 3), S(w - ink_w - 4), S(h - ink_w - 4)], radius=max(1, S(r - 2)), outline=GOLD + (210,), width=max(1, S(1)))
    return im

# ── 막대류 ──────────────────────────────────────────────────────────────────
def bar_frame(w, h, pad=4, name="", note=""):
    """w×h 는 '채움 영역' 크기. 캔버스는 사방 pad 만큼 크다. 안쪽은 투명(채움 그림을 아래 깔고 틀을 위에 얹는다)."""
    W, H = w + pad * 2, h + pad * 2; im = canvas(W, H); d = ImageDraw.Draw(im)
    r = max(3, h // 2 + 1)
    d.rounded_rectangle([0, 0, S(W) - 1, S(H) - 1], radius=S(r + pad), fill=(14, 20, 38, 255)); d.rounded_rectangle([S(1), S(1), S(W) - S(1) - 1, S(H) - S(1) - 1], radius=S(r + pad - 1), outline=GOLD + (255,), width=S(1.5))
    hole = Image.new("L", im.size, 0); ImageDraw.Draw(hole).rounded_rectangle([S(pad), S(pad), S(W - pad) - 1, S(H - pad) - 1], radius=S(r), fill=255)
    a = np.asarray(im.split()[3], np.float32) * (1 - np.asarray(hole, np.float32) / 255); im.putalpha(Image.fromarray(a.astype(np.uint8)))
    d = ImageDraw.Draw(im); d.rounded_rectangle([S(pad) - 1, S(pad) - 1, S(W - pad), S(H - pad)], radius=S(r), outline=(10, 14, 28, 255), width=S(1))
    return im

def bar_fill(w, h, c0, c1, shine=True):
    im = Image.fromarray(np.dstack([vgrad(S(w), S(h), c0, c1), np.full((S(h), S(w)), 255)]).astype(np.uint8), "RGBA")
    if shine:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle([0, S(h * 0.12), S(w), S(h * 0.38)], fill=(255, 255, 255, 60)); im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(S(h * 0.08))))
    m = rr_mask(S(w), S(h), S(max(2, h // 2))); im.putalpha(m); return im

def ticks(w, h, n, color=(10, 14, 28, 160)):
    im = canvas(w, h); d = ImageDraw.Draw(im)
    for i in range(1, n): x = S(w * i / n); d.line([(x, 0), (x, S(h))], fill=color, width=max(1, S(1)))
    return im

# ── 스킬 칸 ────────────────────────────────────────────────────────────────
def slot(state="normal"):
    w = 64; im = canvas(72, 72); p = plate(64, 64, 8, 232, True, 2, glow=TEAL if state == "ready" else (VIOLET if state == "selected" else None)); im.alpha_composite(shadow(p, (0, S(2)), S(4), 0.55), (S(4), S(4)))
    if state == "disabled":
        a = np.asarray(im).astype(np.float32); g = a[..., :3].mean(-1, keepdims=True); a[..., :3] = g * 0.8; im = Image.fromarray(a.astype(np.uint8), "RGBA")
    return im

def keycap(label_w=18):
    im = canvas(18, 18); d = ImageDraw.Draw(im); d.rounded_rectangle([0, 0, S(18) - 1, S(18) - 1], radius=S(4), fill=HANJI + (255,), outline=INK + (255,), width=S(1.5)); d.rounded_rectangle([S(2), S(2), S(16), S(16)], radius=S(3), outline=(212, 169, 78, 160), width=1); return im

def round_btn(d_px, icon=None, ring=GOLD):
    """둥근 버튼 판: 지름 d_px(1배), 남청 판+금 테두리+안쪽 그림자. icon 은 draw(dr, c, r) 함수"""
    im = canvas(d_px + 16, d_px + 16); c = S((d_px + 16) / 2); r = S(d_px / 2); d = ImageDraw.Draw(im)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).ellipse([c - r, c - r + S(4), c + r, c + r + S(4)], fill=(6, 8, 18, 170)); im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(S(4))))
    body = Image.fromarray(np.dstack([vgrad(2 * r, 2 * r, (40, 56, 98), (14, 22, 42)), np.full((2 * r, 2 * r), 255)]).astype(np.uint8), "RGBA"); mk = Image.new("L", (2 * r, 2 * r), 0); ImageDraw.Draw(mk).ellipse([0, 0, 2 * r - 1, 2 * r - 1], fill=255); body.putalpha(mk); im.alpha_composite(body, (c - r, c - r))
    d.ellipse([c - r, c - r, c + r, c + r], outline=tuple(ring) + (255,), width=S(3)); d.ellipse([c - r + S(6), c - r + S(6), c + r - S(6), c + r - S(6)], outline=(212, 169, 78, 100), width=1)
    if icon: icon(d, c, r)
    return im

def ic_slash(d, c, r):   # 공격: 붉은 붓 획 두 줄
    for off in (-0.16, 0.12):
        d.line([(c - r * 0.5, c + r * (0.5 + off)), (c + r * 0.5, c - r * (0.5 - off))], fill=RED + (255,), width=int(r * 0.2));
    d.line([(c - r * 0.45, c - r * 0.5), (c + r * 0.45, c + r * 0.5)], fill=CHAIN + (255,), width=int(r * 0.1))
def ic_dash(d, c, r):    # 회피: 가로 속도선 + 화살촉
    for k, y in enumerate((-0.28, 0.0, 0.28)): d.line([(c - r * 0.6, c + r * y), (c + r * (0.1 + 0.1 * k), c + r * y)], fill=CHAIN + (255,), width=int(r * 0.1))
    d.polygon([(c + r * 0.62, c), (c + r * 0.2, c - r * 0.34), (c + r * 0.2, c + r * 0.34)], fill=TEAL + (255,))
def ic_talk(d, c, r):    # 상호작용: 말풍선
    d.rounded_rectangle([c - r * 0.55, c - r * 0.42, c + r * 0.55, c + r * 0.28], radius=int(r * 0.2), fill=HANJI + (255,)); d.polygon([(c - r * 0.2, c + r * 0.25), (c - r * 0.1, c + r * 0.55), (c + r * 0.1, c + r * 0.25)], fill=HANJI + (255,))
    for k in (-1, 0, 1): d.ellipse([c + k * r * 0.28 - r * 0.07, c - r * 0.14 - r * 0.07, c + k * r * 0.28 + r * 0.07, c - r * 0.14 + r * 0.07], fill=INK + (255,))
def ic_plus(d, c, r): d.line([(c - r * 0.4, c), (c + r * 0.4, c)], fill=GOLD + (255,), width=int(r * 0.16)); d.line([(c, c - r * 0.4), (c, c + r * 0.4)], fill=GOLD + (255,), width=int(r * 0.16))
def ic_minus(d, c, r): d.line([(c - r * 0.4, c), (c + r * 0.4, c)], fill=GOLD + (255,), width=int(r * 0.16))
def ic_close(d, c, r): d.line([(c - r * 0.36, c - r * 0.36), (c + r * 0.36, c + r * 0.36)], fill=RED + (255,), width=int(r * 0.16)); d.line([(c - r * 0.36, c + r * 0.36), (c + r * 0.36, c - r * 0.36)], fill=RED + (255,), width=int(r * 0.16))

# ── 커서 ───────────────────────────────────────────────────────────────────
def cursor(kind):
    im = canvas(32, 32); d = ImageDraw.Draw(im)
    if kind == "default":
        pts = [(2, 2), (2, 24), (8, 18), (13, 29), (17, 27), (12, 17), (21, 17)]; d.polygon([(S(x), S(y)) for x, y in pts], fill=(240, 232, 214, 255), outline=INK + (255,)); d.line([(S(x), S(y)) for x, y in pts + [pts[0]]], fill=INK + (255,), width=S(1.6))
    elif kind == "attack":   # 칼날(붉은 테두리)
        d.line([(S(5), S(27)), (S(24), S(6))], fill=INK + (255,), width=S(7)); d.line([(S(5), S(27)), (S(24), S(6))], fill=(236, 240, 248, 255), width=S(4)); d.line([(S(8), S(20)), (S(14), S(26))], fill=INK + (255,), width=S(5)); d.line([(S(9), S(21)), (S(13), S(25))], fill=GOLD + (255,), width=S(2.5)); d.polygon([(S(24), S(6)), (S(29), S(2)), (S(26), S(9))], fill=RED + (255,))
    else:                    # 말풍선
        d.rounded_rectangle([S(2), S(3), S(28), S(21)], radius=S(6), fill=HANJI + (255,), outline=INK + (255,), width=S(1.8)); d.polygon([(S(8), S(20)), (S(7), S(28)), (S(15), S(21))], fill=HANJI + (255,), outline=INK + (255,))
        for x in (9, 15, 21): d.ellipse([S(x - 1.7), S(10.3), S(x + 1.7), S(13.7)], fill=INK + (255,))
    return im

def divider(w, h):
    im = canvas(w, h); d = ImageDraw.Draw(im); cy = S(h / 2)
    for i in range(S(w)):
        t = abs(i - S(w) / 2) / (S(w) / 2); a = int(255 * (1 - t) ** 0.8); d.line([(i, cy), (i, cy)], fill=GOLD + (a,), width=S(2))
    d.polygon([(S(w / 2) - S(8), cy), (S(w / 2), cy - S(6)), (S(w / 2) + S(8), cy), (S(w / 2), cy + S(6))], fill=RED + (255,), outline=GOLD + (255,)); return im

def streak(w, h):
    """지역 진입 알림 뒤 먹 번짐 띠: 가운데 진하고 양끝·위아래로 사라짐"""
    ys, xs = np.mgrid[0:S(h), 0:S(w)].astype(np.float32); ax = np.clip(1 - np.abs(xs / S(w) - 0.5) * 2, 0, 1) ** 0.5; ay = np.clip(1 - np.abs(ys / S(h) - 0.5) * 2, 0, 1) ** 0.8
    a = ax * ay * 0.78 * 255; col = np.array(ABYSS, np.float32); return Image.fromarray(np.dstack([np.broadcast_to(col, (S(h), S(w), 3)), a]).astype(np.uint8), "RGBA")

if __name__ == "__main__":
    # 체력·기력·경험 막대 ────────────────────────────────
    save(bar_frame(280, 18, 4), "hp_frame", "hud", note="체력 틀. 채움 영역 280×18, 사방 4px 틀이라 캔버스 288×26. 채움을 아래 깔고 이 틀을 위에")
    save(bar_fill(280, 18, (236, 96, 72), (150, 30, 36)), "hp_fill", "hud", note="체력 채움 280×18(가로로 잘라서 씀)")
    save(bar_fill(280, 18, (255, 150, 140), (200, 70, 70)), "hp_fill_loss", "hud", note="최근 깎인 양 잔상(옅은 붉음)")
    save(bar_frame(280, 12, 4), "mp_frame", "hud", note="기력(도력) 틀. 채움 280×12, 캔버스 288×20")
    save(bar_fill(280, 12, (110, 170, 232), (44, 84, 160)), "mp_fill", "hud", note="도력 채움 280×12")
    save(bar_frame(768, 6, 3), "exp_frame", "hud", note="경험치 막대 틀. 채움 768×6, 캔버스 774×12")
    save(bar_fill(768, 6, (240, 214, 130), (190, 140, 56), False), "exp_fill", "hud", note="경험 채움 768×6(금)")
    save(bar_frame(960, 20, 5), "boss_hp_frame", "hud", note="보스 체력 틀. 채움 960×20, 캔버스 970×30. 이름은 바 위에 24px")
    save(bar_fill(960, 20, (232, 70, 66), (130, 20, 34)), "boss_hp_fill", "hud", note="보스 채움 960×20")
    save(bar_fill(960, 20, (255, 214, 214), (230, 160, 160), False), "boss_hp_loss", "hud", note="보스 깎인 잔상")
    save(ticks(960, 20, 4), "boss_phase_ticks", "hud", note="단계 구분선(25%마다 4칸). 단계 수가 다르면 코드가 위치만 바꿔 그릴 것")
    # 초상 틀 + 버프 틀 ───────────────────────────────────
    p = canvas(88, 88); pl = plate(88, 88, 14, 0, True, 3); d = ImageDraw.Draw(pl); m = Image.new("L", pl.size, 255); ImageDraw.Draw(m).rounded_rectangle([S(8), S(8), S(80), S(80)], radius=S(8), fill=0)
    pl.putalpha(ImageChops.multiply(pl.split()[3], m)); save(shadow(pl, (0, S(2)), S(3), 0.5), "portrait_frame", "hud", note="초상 틀 88×88, 가운데 72×72 가 뚫림. 아래 초상 그림을 깔 것(차사 얼굴)")
    for kind, col in (("buff", GOLD), ("debuff", (214, 56, 56))):
        im = canvas(32, 32); d = ImageDraw.Draw(im); d.rounded_rectangle([0, 0, S(32) - 1, S(32) - 1], radius=S(5), fill=(14, 20, 38, 235), outline=tuple(col) + (255,), width=S(2)); save(im, f"{kind}_frame", "hud", note="버프/디버프 틀 32×32. 남은 시간은 아래에 12px 글자")
    # 스킬 칸 ───────────────────────────────────────────
    for st in ("normal", "ready", "selected", "disabled"): save(slot(st), f"slot_{st}", "hud", note="스킬 칸 64×64(캔버스 72, 그림자 포함). ready=청록 테두리(쓸 수 있음), selected=보라(선택)")
    cd = canvas(64, 64); ImageDraw.Draw(cd).rounded_rectangle([0, 0, S(64) - 1, S(64) - 1], radius=S(8), fill=(6, 10, 22, 190)); save(cd, "slot_cooldown_shade", "hud", note="쿨타임 어둠 판(코드가 시계방향으로 잘라 씀)")
    save(keycap(), "keycap_small", "hud", note="칸 왼쪽 위 단축키 배지 18×18(글자 14px)")
    for nm, fillc in (("full", (255, 255, 255)), ("empty", (120, 126, 140))):
        im = canvas(12, 12); d = ImageDraw.Draw(im); d.ellipse([0, 0, S(12) - 1, S(12) - 1], fill=(16, 22, 40, 255), outline=(212, 169, 78, 255), width=S(1.2)); d.ellipse([S(3), S(3), S(9), S(9)], fill=tuple(fillc) + (255,)); save(im, f"dodge_pip_{nm}", "hud", note="회피 충전 점 12×12 (찬 점 흰색·빈 점 회색)")
    # 한지 판들 ────────────────────────────────────────
    save(hanji_card(64, 64, 8, 11), "panel_hanji_small", "hud", nine=[16, 16, 16, 16], note="한지 카드 9칸 늘이기 64×64(테두리 16). 퀘스트 추적·알림 등")
    save(hanji_card(128, 128, 10, 12), "panel_hanji", "hud", nine=[24, 24, 24, 24], note="한지 패널 9칸 늘이기 128×128(테두리 24). 명부·인벤토리 같은 큰 패널의 바탕")
    dlg = hanji_card(96, 96, 10, 21); save(dlg, "dialog_box", "hud", nine=[28, 28, 28, 28], note="대화창 바탕 9칸 늘이기. 1152×220 로 늘려 씀. 글 20px 본문")
    nt = plate(220, 44, 8, 240, True, 2); save(nt, "dialog_name_tab", "hud", nine=[16, 12, 16, 12], note="대화창 왼쪽 위 이름 탭(가로로 늘림, 높이 44, 이름 24px 한지색 글씨)")
    ar = canvas(24, 24); ImageDraw.Draw(ar).polygon([(S(4), S(6)), (S(20), S(6)), (S(12), S(19))], fill=GOLD + (255,), outline=INK + (255,)); save(ar, "dialog_next_arrow", "hud", note="다음 글로 넘김 ▼ 24×24(위아래로 까딱이게)")
    for nm, a in (("normal", 0), ("selected", 1)):
        c = canvas(96, 44); d = ImageDraw.Draw(c); d.rounded_rectangle([0, 0, S(96) - 1, S(44) - 1], radius=S(6), fill=((255, 244, 214, 255) if a else (232, 218, 192, 255)), outline=(INK if not a else RED) + (255,), width=S(2)); save(c, f"choice_{nm}", "hud", nine=[12, 12, 12, 12], note="대화 선택지 줄(최대 4개). selected=붉은 테두리")
    save(plate(96, 60, 10, 200, True, 2), "quest_title_bar", "hud", nine=[14, 14, 14, 14], note="퀘스트 추적 제목 줄(금색 18px 제목)")
    row = canvas(420, 28); rr = hgrad(S(420), S(28), (14, 20, 38), (14, 20, 38)); a = np.linspace(0.78, 0, S(420))[None, :].repeat(S(28), 0) * 255; row.alpha_composite(Image.fromarray(np.dstack([rr, a]).astype(np.uint8), "RGBA")); save(row, "log_row_bg", "hud", note="알림 로그 한 줄 420×28(오른쪽으로 사라지는 먹)")
    save(divider(640, 16), "region_divider", "hud", note="지역 진입 알림 지역명 40px 아래 장식선 640×16")
    save(streak(1000, 160), "region_streak", "hud", note="지역 진입 알림 뒤 먹 번짐 1000×160(글 가독성)")
    # 버튼류 ───────────────────────────────────────────
    save(round_btn(56, ic_plus), "btn_zoom_in", "hud", note="큰 지도 확대 56")
    save(round_btn(56, ic_minus), "btn_zoom_out", "hud", note="큰 지도 축소 56"); save(round_btn(56, ic_close), "btn_close", "hud", note="닫기 56")
    # 키 아이콘(상호작용 안내) ────────────────────────────
    for nm, w in (("key_small", 32), ("key_wide", 56)):
        im = canvas(w, 32); d = ImageDraw.Draw(im); d.rounded_rectangle([S(1), S(1), S(w - 1), S(30)], radius=S(6), fill=HANJI + (255,), outline=INK + (255,), width=S(2)); d.rounded_rectangle([S(4), S(4), S(w - 4), S(26)], radius=S(4), outline=(212, 169, 78, 170), width=S(1)); save(im, nm, "hud", note="키 아이콘 32×32 / 56×32 (글자는 코드가 18px 먹색으로)")
    # 폰 조작 ──────────────────────────────────────────
    jb = canvas(240, 240); d = ImageDraw.Draw(jb); c = S(120); d.ellipse([0, 0, S(240) - 1, S(240) - 1], fill=(14, 20, 38, 120), outline=GOLD + (190,), width=S(3)); d.ellipse([S(14), S(14), S(226), S(226)], outline=(212, 169, 78, 70), width=S(1.5))
    for k in range(4):
        a = math.radians(k * 90 - 90); d.polygon([(c + math.cos(a) * S(104) + math.cos(a + 1.57) * S(8), c + math.sin(a) * S(104) + math.sin(a + 1.57) * S(8)), (c + math.cos(a) * S(88), c + math.sin(a) * S(88)), (c + math.cos(a) * S(104) - math.cos(a + 1.57) * S(8), c + math.sin(a) * S(104) - math.sin(a + 1.57) * S(8))], fill=(212, 169, 78, 150))
    save(jb, "joystick_base", "hud", note="폰 이동 조이스틱 바깥 원 240(반지름 120), 반투명")
    kn = round_btn(96, None); save(kn, "joystick_knob", "hud", note="손잡이(지름 96+그림자)");
    save(round_btn(160, ic_slash, RED), "btn_attack", "hud", note="폰 공격 버튼 지름 160(+그림자 16)"); save(round_btn(104, ic_dash), "btn_dodge", "hud", note="폰 회피 104"); save(round_btn(104, ic_talk, TEAL), "btn_interact", "hud", note="폰 상호작용 104")
    save(round_btn(104, None), "btn_skill_blank", "hud", note="폰 스킬 버튼 바탕 104(가운데에 스킬 아이콘)")
    # 커서 ────────────────────────────────────────────
    for k, hot in (("default", (2, 2)), ("attack", (24, 6)), ("talk", (8, 28))): save(cursor(k), f"cursor_{k}", "hud/cursor", note=f"마우스 커서 32×32, 눌리는 점(hotspot) x={hot[0]} y={hot[1]}")
    dump_manifest("ui_manifest.json"); print("HUD 완료", len(MANIFEST))
