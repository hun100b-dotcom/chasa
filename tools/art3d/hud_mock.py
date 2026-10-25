"""표준 명세 배치(1920×1080)대로 HUD 그림을 얹어 본 시안: 겹침·가독성·여백(24px) 확인용 + 갤러리용."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from ui_lib import *
import grading

PRE = os.path.join(A3, "previews"); W, H = 1920, 1080
def L(sub, name): return Image.open(os.path.join(UI, sub, name + ".png")).convert("RGBA")
def ns(im, w, h, b):
    """9칸 늘이기(Unity 의 9-slice 와 같은 방식): 모서리는 그대로, 변은 늘이고, 가운데는 채운다"""
    W0, H0 = im.size; out = Image.new("RGBA", (w, h), (0, 0, 0, 0)); xs0 = [0, b, W0 - b, W0]; ys0 = [0, b, H0 - b, H0]; xs1 = [0, b, w - b, w]; ys1 = [0, b, h - b, h]
    for i in range(3):
        for j in range(3):
            p = im.crop((xs0[i], ys0[j], xs0[i + 1], ys0[j + 1])); sz = (xs1[i + 1] - xs1[i], ys1[j + 1] - ys1[j])
            if sz[0] > 0 and sz[1] > 0: out.alpha_composite(p.resize(sz, Image.LANCZOS), (xs1[i], ys1[j]))
    return out
def txt(d, xy, s, sz, fill=(255, 255, 255, 255), anchor="la", bold=True):
    f = font(sz); x, y = xy
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (1, -1), (-1, 1)): d.text((x + dx, y + dy), s, font=f, fill=(10, 14, 28, 230), anchor=anchor)
    d.text(xy, s, font=f, fill=fill, anchor=anchor)

def base_scene():
    im = Image.open(os.path.join(PRE, "scene_tendo.png")).convert("RGB").resize((W, H), Image.LANCZOS); return grading.post(im, "night", "clear").convert("RGBA")

def desktop():
    bg = base_scene(); d = ImageDraw.Draw(bg)
    # 좌상: 초상 + 체력/기력 + 품계 + 버프
    bg.alpha_composite(L("hud", "portrait_frame"), (24, 24)); pf = Image.new("RGBA", (72, 72), (28, 40, 72, 255)); ImageDraw.Draw(pf).ellipse([18, 8, 54, 44], fill=(52, 60, 88, 255)); ImageDraw.Draw(pf).polygon([(10, 72), (36, 40), (62, 72)], fill=(32, 34, 52, 255)); ImageDraw.Draw(pf).polygon([(24, 12), (48, 12), (54, 6), (18, 6)], fill=(20, 20, 30, 255)); ImageDraw.Draw(pf).rectangle([24, 38, 48, 42], fill=RED + (255,))
    bg.alpha_composite(pf, (24 + 8, 24 + 8)); bg.alpha_composite(L("hud", "portrait_frame"), (24, 24))
    x0 = 24 + 88 + 8
    hp = L("hud", "hp_fill").crop((0, 0, int(280 * 0.78), 18)); bg.alpha_composite(hp, (x0 + 4, 28 + 4)); bg.alpha_composite(L("hud", "hp_frame"), (x0, 28))
    mp = L("hud", "mp_fill").crop((0, 0, int(280 * 0.55), 12)); bg.alpha_composite(mp, (x0 + 4, 60 + 4)); bg.alpha_composite(L("hud", "mp_frame"), (x0, 60)); d = ImageDraw.Draw(bg)
    txt(d, (x0 + 4, 84), "품계 7", 16, GOLD + (255,)); txt(d, (x0 + 144, 29), "156 / 200", 14, anchor="ma"); 
    for i, k in enumerate(("buff", "buff", "debuff")): bg.alpha_composite(L("hud", f"{k}_frame"), (24 + i * 36, 24 + 88 + 8)); 
    # 우상: 미니맵(260) + 지역명·시각 + 퀘스트
    m = Image.open(os.path.join(UI, "map", "map_field.png")).convert("RGBA"); S_ = 3.2; px, py = 108, 452
    crop = m.crop((int((px - 40) * S_), int((640 - py - 40) * S_), int((px + 40) * S_), int((640 - py + 40) * S_))).resize((260, 260), Image.LANCZOS)
    mk = L("map", "minimap_mask_260"); lay = Image.new("RGBA", (300, 300), (0, 0, 0, 0)); lay.paste(crop, (20, 20)); lay.putalpha(mk.split()[3])
    mm = Image.new("RGBA", (300, 300), (0, 0, 0, 0)); mm.alpha_composite(lay); ic = lambda n, s: L("map/icons", "icon_" + n).resize((s, s), Image.LANCZOS)
    for n, s, (x, y) in (("enemy", 10, (188, 120)), ("enemy", 10, (210, 160)), ("soul_named", 18, (130, 200)), ("npc", 12, (90, 150)), ("seonang", 22, (228, 214)), ("quest", 22, (160, 70)), ("me", 20, (150, 150))): mm.alpha_composite(ic(n, s), (x - s // 2, y - s // 2))
    mm.alpha_composite(L("map", "minimap_frame_round_pc")); bg.alpha_composite(mm, (W - 24 - 280, 24 - 20 + 0)) if False else bg.alpha_composite(mm, (W - 24 - 300 + 20, 24 - 20 + 20))
    bar = L("hud", "region_time_bar"); bx = W - 24 - 260 - 0; by = 24 + 260 + 8 + 14; bg.alpha_composite(bar, (bx - 0, by)); d = ImageDraw.Draw(bg)
    d.text((bx + 14, by + 14), "검은여울 어귀", font=font(18), fill=INK + (255,), anchor="lm"); bg.alpha_composite(L("hud/time", "time_moon").resize((20, 20), Image.LANCZOS), (bx + 190, by + 4)); d.text((bx + 214, by + 14), "21:40", font=font(15), fill=INK + (255,), anchor="lm")
    qp = ns(L("hud", "panel_hanji_small"), 300, 136, 16); qx = W - 24 - 300; qy = by + 28 + 16; bg.alpha_composite(qp, (qx, qy)); d = ImageDraw.Draw(bg)
    d.text((qx + 26, qy + 16), "나루 영감의 부탁", font=font(18), fill=(150, 108, 30, 255)); d.text((qx + 26, qy + 46), "혼 천도하기   2/5", font=font(16), fill=INK + (255,)); d.text((qx + 26, qy + 70), "서낭당에 닿기", font=font(16), fill=(120, 120, 130, 255)); d.text((qx + 26, qy + 98), "넋 모으기   31/50", font=font(16), fill=INK + (255,))
    # 하단 스킬바
    sx = (W - 568) // 2; sy = H - 40 - 64; keys = "QWERASDF"
    for i in range(8):
        st = "ready" if i in (0, 1) else ("disabled" if i > 3 else "normal"); bg.alpha_composite(L("hud", f"slot_{st}"), (sx + i * 72 - 4, sy - 4)); bg.alpha_composite(L("hud", "keycap_small"), (sx + i * 72 + 2, sy + 2)); d = ImageDraw.Draw(bg); d.text((sx + i * 72 + 11, sy + 11), keys[i], font=font(14), fill=INK + (255,), anchor="mm")
    cd = L("hud", "slot_cooldown_shade").crop((0, 0, 64, 40)); bg.alpha_composite(cd, (sx + 2 * 72, sy)); txt(ImageDraw.Draw(bg), (sx + 2 * 72 + 32, sy + 32), "3", 20, anchor="mm")
    for i, k in enumerate(("full", "full", "empty")): bg.alpha_composite(L("hud", f"dodge_pip_{k}"), (W // 2 - 24 + i * 18, sy - 22))
    ex = (W - 768) // 2; bg.alpha_composite(L("hud", "exp_fill").crop((0, 0, 460, 6)), (ex, H - 16 - 6)); bg.alpha_composite(L("hud", "exp_frame"), (ex - 3, H - 16 - 9))
    # 알림 로그
    ly = H - 140 - 28 * 3
    for i, t in enumerate(("넋 +12", "엽전 +3", "오래된 혼을 천도했다")): bg.alpha_composite(L("hud", "log_row_bg"), (24, ly + i * 30)); txt(ImageDraw.Draw(bg), (36, ly + i * 30 + 4), t, 16)
    return bg

def boss_dialog():
    bg = base_scene(); bg.alpha_composite(Image.new("RGBA", (W, 40), (0, 0, 0, 255)), (0, 0)); bg.alpha_composite(Image.new("RGBA", (W, 40), (0, 0, 0, 255)), (0, H - 40))
    bx = (W - 970) // 2; by = 64; bg.alpha_composite(L("hud", "boss_hp_fill").crop((0, 0, 680, 20)), (bx + 5, by + 5)); bg.alpha_composite(L("hud", "boss_hp_loss").crop((680, 0, 760, 20)), (bx + 5 + 680, by + 5)); bg.alpha_composite(L("hud", "boss_phase_ticks"), (bx + 5, by + 5)); bg.alpha_composite(L("hud", "boss_hp_frame"), (bx, by)); d = ImageDraw.Draw(bg)
    txt(d, (W // 2, by - 8), "나루 영감", 24, anchor="mm")
    dl = ns(L("hud", "dialog_box"), 1152, 220, 28); dx = (W - 1152) // 2; dy = H - 80 - 220; bg.alpha_composite(dl, (dx, dy)); nt = ns(L("hud", "dialog_name_tab"), 220, 44, 12); bg.alpha_composite(nt, (dx + 24, dy - 22)); d = ImageDraw.Draw(bg)
    d.text((dx + 24 + 110, dy - 22 + 22), "나루 영감", font=font(24), fill=HANJI + (255,), anchor="mm"); d.text((dx + 40, dy + 36), "강을 건너려거든 뱃삯부터 내거라. 산 사람의 삯은 엽전이요, 죽은 이의 삯은 이름이니라.", font=font(20), fill=INK + (255,))
    bg.alpha_composite(L("hud", "dialog_next_arrow"), (dx + 1152 - 52, dy + 220 - 44))
    for i, t in enumerate(("이름을 내어 준다", "엽전으로 치른다")):
        c = ns(L("hud", "choice_selected" if i == 0 else "choice_normal"), 1000, 44, 12); bg.alpha_composite(c, (dx + 76, dy + 82 + i * 52)); ImageDraw.Draw(bg).text((dx + 100, dy + 92 + i * 52), t, font=font(20), fill=INK + (255,))
    return bg

def phone():
    bg = base_scene(); 
    jb = L("hud", "joystick_base"); bg.alpha_composite(jb, (200 - 120, H - 200 - 120)); bg.alpha_composite(L("hud", "joystick_knob").resize((112, 112)), (200 - 56, H - 200 - 56))
    ax, ay = W - 64 - 80, H - 64 - 80; bg.alpha_composite(L("hud", "btn_attack"), (ax - 88, ay - 88))
    for k, (ang) in enumerate((175, 143, 111, 85)):  # 공격 버튼 주위 부채꼴 9시→12시
        import math; a = math.radians(ang + 0); sx = ax + math.cos(a) * 230; sy = ay - math.sin(a) * 230; bg.alpha_composite(L("hud", "btn_skill_blank"), (int(sx - 60), int(sy - 60)))
    bg.alpha_composite(L("hud", "btn_dodge"), (ax - 150 - 60, ay + 70 - 60)); bg.alpha_composite(L("hud", "btn_interact"), (ax - 60, ay - 160 - 60))
    mm = Image.open(os.path.join(UI, "map", "map_field.png")).convert("RGBA"); S_ = 3.2; px, py = 108, 452
    crop = mm.crop((int((px - 40) * S_), int((640 - py - 40) * S_), int((px + 40) * S_), int((640 - py + 40) * S_))).resize((200, 200), Image.LANCZOS)
    mk = L("map", "minimap_mask_200"); lay = Image.new("RGBA", (240, 240), (0, 0, 0, 0)); lay.paste(crop, (20, 20)); lay.putalpha(mk.split()[3]); lay.alpha_composite(L("map", "minimap_frame_round_phone")); bg.alpha_composite(lay, (W - 16 - 240 + 20, 16 - 20 + 20))
    bg.alpha_composite(L("hud", "portrait_frame"), (24, 24)); bg.alpha_composite(L("hud", "hp_frame"), (24 + 96, 28)); bg.alpha_composite(L("hud", "hp_fill").crop((0, 0, 220, 18)), (24 + 100, 32))
    return bg

if __name__ == "__main__":
    for n, f in (("desktop", desktop), ("boss_dialog", boss_dialog), ("phone", phone)): f().convert("RGB").save(os.path.join(PRE, f"hud_mock_{n}.jpg"), quality=90)
    print("시안 완료")
