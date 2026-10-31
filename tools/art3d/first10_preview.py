"""처음 10분 그림 확인판: 실제 그림 파일을 불러와 화면에 놓일 모양으로 합성한다(밤 배경 위). 실행: python3 first10_preview.py
산출: assets3d/previews/first10_sheet_a.jpg(승급·흡수·등급·카드) / first10_sheet_b.jpg(거센 혼·예고·보상·메뉴)"""
import os, math
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); A3 = os.path.join(HERE, "..", "..", "assets3d"); D = os.path.join(A3, "ui", "first10"); OUT = os.path.join(A3, "previews")
FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
def L(n): return Image.open(os.path.join(D, n + ".png")).convert("RGBA")
def frame(strip_im, i, fw): return strip_im.crop((i * fw, 0, (i + 1) * fw, strip_im.height))
def f(sz): return ImageFont.truetype(FONT, sz)
def txt(im, xy, t, sz=16, col=(243, 231, 211), anchor="la"): ImageDraw.Draw(im).text(xy, t, font=f(sz), fill=col, anchor=anchor, stroke_width=1, stroke_fill=(15, 23, 41))
def bg(w, h):
    """밤 서낭당 느낌의 어두운 남청 바닥(그림이 어두운 화면 위에서 읽히는지 보려는 배경)."""
    im = Image.new("RGBA", (w, h), (24, 36, 66, 255)); d = ImageDraw.Draw(im)
    for y in range(h): d.line([(0, y), (w, y)], fill=(int(22 + 14 * y / h), int(32 + 18 * y / h), int(58 + 14 * y / h), 255))
    return im
def nine(img, w, h, m):
    """9칸 늘이기."""
    W, H = img.size; out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    xs = [(0, m), (m, W - m), (W - m, W)]; ys = [(0, m), (m, H - m), (H - m, H)]; ox = [(0, m), (m, w - m), (w - m, w)]; oy = [(0, m), (m, h - m), (h - m, h)]
    for (a, b), (c, d_) in zip(ys, oy):
        for (p, q), (r, s) in zip(xs, ox):
            if r < s and c < d_: out.paste(img.crop((p, a, q, b)).resize((s - r, d_ - c), Image.LANCZOS), (r, c))
    return out
def put(im, sp, xy): im.alpha_composite(sp, (int(xy[0]), int(xy[1])))

def sheet_a():
    W, H = 1600, 1180; im = bg(W, H)
    # 품계 승급: 종이 + 인(프레임 0·3·4·6·11)
    txt(im, (20, 12), "① 품계 승급 인 (1.0초, 프레임 0 · 3 · 4 · 6 · 11)", 20)
    paper = L("rank_paper"); put(im, paper, (20, 44)); st = L("rank_stamp"); fw = st.width // 12
    for k, fi in enumerate((0, 3, 4, 6, 11)):
        fr = frame(st, fi, fw); put(im, fr, (700 + k * 180, 44)) if False else None
    for k, fi in enumerate((0, 3, 4, 6, 11)):
        bgc = Image.new("RGBA", (256, 256), (35, 45, 75, 255)); bgc.alpha_composite(frame(st, fi, fw)); bgc = bgc.resize((200, 200)); im.alpha_composite(bgc, (680 + k * 205, 50))
    put(im, frame(st, 11, fw), (20 + 320 - 128, 44 + 230 - 128)); txt(im, (180, 84), "종9품 (글자는 코드)", 22, (42, 42, 56), "mm") if False else None
    txt(im, (350, 90), "종 9 품", 30, (42, 42, 56), "mm")
    cf = L("craft_flash"); fw2 = cf.width // 8
    for k in range(0, 8, 2):
        c = Image.new("RGBA", (fw2, cf.height), (35, 45, 75, 255)); c.alpha_composite(frame(cf, k, fw2)); im.alpha_composite(c.resize((256, 48)), (700 + (k // 2) * 262, 270))
    txt(im, (700, 250), "손보기 성공 금빛(프레임 0·2·4·6)", 14); im.alpha_composite(L("rank_dot").resize((24, 24)), (1650 - 40 if False else 1540, 52))
    # 흡수
    txt(im, (20, 470), "② 혼불 흡수(왼쪽, 청록 불티가 안으로) · 엽전 튐(오른쪽, 주황 파편이 바깥으로)", 20)
    hf = L("absorb_hon_fly"); hb = L("absorb_hon_burst"); cs = L("absorb_coin_spin"); cb = L("absorb_coin_burst")
    for k in range(4): put(im, frame(hf, k, 48), (20 + k * 56, 510))
    for k in range(6): put(im, frame(cs, k, 48), (820 + k * 56, 510))
    for k in range(6): put(im, frame(hb, k, 128), (20 + k * 130, 570))
    for k in range(6): put(im, frame(cb, k, 128), (820 + k * 130, 570))
    # 등급 이름표
    txt(im, (20, 720), "③ 등급 이름표·꼭대기 모양", 20)
    names = [("common", "흔한 노리개"), ("refined", "손본 갓"), ("rare", "귀한 도포"), ("antique", "옛 차사의 띠"), ("named", "이름 있는 사슬"), ("set", "상두 한 벌 갓")]
    for k, (n, label) in enumerate(names):
        y = 760 + k * 54; put(im, nine(L("drop_tag_" + n), 260, 40, 16), (60, y)); put(im, L("tier_mark_" + n), (22, y + 4)); txt(im, (110, y + 20), label, 16, anchor="lm")
    # 카드 3장
    txt(im, (700, 720), "④ 첫 도술 카드 (0.5배)", 20)
    fr = L("skill_card_frame"); cards = [("bureum", "붙잡아 부르기", "혼을 사슬로 끌어옵니다"), ("jul", "휘감기", "사슬로 적을 감아 묶습니다"), ("eolluk", "터뜨리기", "원념 얼룩을 터뜨립니다")]
    for k, (n, nm, ef) in enumerate(cards):
        c = fr.copy(); c.alpha_composite(L("skill_card_art_" + n), (16, 66)); b = L(f"branch_{n}_big"); c.alpha_composite(b, (160 - 40, 44 - 40))
        txt(c, (160, 230), nm, 26, (42, 42, 56), "mm"); txt(c, (160, 300), ef, 18, (42, 42, 56), "mm")
        c = c.resize((200, 275), Image.LANCZOS); im.alpha_composite(c, (520 + k * 215, 760))
    hv = L("skill_card_frame_hover").resize((200, 275)); im.alpha_composite(hv, (1170, 760)); txt(im, (1180, 1045), "고른 카드 번짐판", 14)
    for k, n in enumerate(("bureum", "jul", "eolluk")): put(im, L("branch_" + n), (1400 + k * 56, 780))
    im.convert("RGB").save(os.path.join(OUT, "first10_sheet_a.jpg"), quality=88)

def sheet_b():
    W, H = 1600, 1180; im = bg(W, H)
    txt(im, (20, 12), "⑤ 거센 혼: 머리 위 붉은 가시 고리 · 이름 띠 · 맺힘 막대(맺힘 3칸)", 20)
    er = L("elite_ring"); fw = er.width // 4
    for k in range(4): put(im, frame(er, k, 256).resize((200, 100)), (30 + k * 210, 50))
    nb = nine(L("elite_name_band"), 720, 64, 24); put(im, nb, (900, 40)); txt(im, (1260, 72), "거센 혼", 28, anchor="mm")
    bf = nine(L("bind_bar_frame"), 520, 28, 12); bfi = L("bind_bar_fill"); bt = L("bind_bar_ticks"); put(im, bf, (940, 125)); fl = bfi.crop((0, 0, 340, 20)); put(im, fl, (944, 129)); put(im, bt, (944, 129))
    txt(im, (940, 160), "맺힘 막대(예: 2/3 맺힘) — 체력 막대가 아님", 14)
    txt(im, (20, 190), "예고 장판: 밝은 테두리 + 35% 채움 (원 r2.5 m · 띠 1.6×6 m) / 노랑 옵션 / 천도 뒤 바닥 맑아짐", 20)
    cb = L("tele_circle_border").resize((260, 260));
    for k, nm in enumerate(("red", "yellow")):
        cf = L(f"tele_circle_fill_{nm}").resize((260, 260)); c = Image.new("RGBA", (260, 260), (60, 62, 50, 255)); c.alpha_composite(cf); c.alpha_composite(cb); im.alpha_composite(c, (30 + k * 280, 230))
    bb = L("tele_band_border").resize((88, 330))
    for k, nm in enumerate(("red", "yellow")):
        bfl = L(f"tele_band_fill_{nm}").resize((88, 330)); c = Image.new("RGBA", (88, 330), (60, 62, 50, 255)); c.alpha_composite(bfl); c.alpha_composite(bb); im.alpha_composite(c, (620 + k * 110, 230))
    # 차오름 예시: 채움 반경 60%만 보이게(바깥에서 안으로)
    ce = L("tele_circle_fill_red").resize((260, 260)); m = Image.new("L", (260, 260), 0); y, x = None, None
    mm = Image.new("L", (260, 260), 0); ImageDraw.Draw(mm).ellipse([130 - 70, 130 - 70, 130 + 70, 130 + 70], fill=255); ring = Image.new("L", (260, 260), 255); ring.paste(0, mask=mm); ce.putalpha(Image.composite(ce.split()[3], Image.new("L", (260, 260), 0), ring))
    c = Image.new("RGBA", (260, 260), (60, 62, 50, 255)); c.alpha_composite(ce); c.alpha_composite(cb); im.alpha_composite(c, (860, 230)); txt(im, (860, 495), "차오르는 중(바깥→안)", 14)
    cr = L("clear_ring");
    for k in range(0, 8, 2): c = Image.new("RGBA", (256, 256), (50, 56, 44, 255)); c.alpha_composite(frame(cr, k, 256)); im.alpha_composite(c.resize((120, 120)), (1150 + (k // 2) * 124, 230))
    txt(im, (1150, 355), "천도 뒤 맑아짐 0·2·4·6", 14)
    rv = L("roar_vignette").resize((400, 225)); c = Image.new("RGBA", (400, 225), (60, 62, 80, 255)); c.alpha_composite(rv); im.alpha_composite(c, (1150, 380)); txt(im, (1150, 608), "부르기 울부짖음 틀", 14)
    txt(im, (20, 560), "⑥ 보상 미리보기 (같은 크기·밝기) · 이름혼은 금테", 20)
    for k, (n, lab) in enumerate((("reward_tendo", "[E] 천도"), ("reward_pahon", "[R] 파혼"))):
        c = Image.new("RGBA", (200, 110), (22, 33, 62, 235)); ImageDraw.Draw(c).rounded_rectangle([0, 0, 199, 109], radius=10, outline=(212, 169, 78, 255), width=2); c.alpha_composite(L(n).resize((56, 56)), (72, 8)); im.alpha_composite(c, (30 + k * 220, 600))
        txt(im, (130 + k * 220, 90 + 600), lab, 18, anchor="mm")
    c = Image.new("RGBA", (200, 110), (22, 33, 62, 235)); ImageDraw.Draw(c).rounded_rectangle([0, 0, 199, 109], radius=10, outline=(212, 169, 78, 255), width=2); c.alpha_composite(L("reward_tendo").resize((56, 56)), (72, 8)); c.alpha_composite(L("reward_gold_rim").resize((56, 56)), (72, 8)); im.alpha_composite(c, (470, 600)); txt(im, (570, 690), "이름혼(금테)", 16, anchor="mm")
    txt(im, (720, 560), "⑦ 목표 화살표(24px) + 거리", 20)
    ar = L("goal_arrow"); pl = nine(L("goal_dist_plate"), 70, 22, 10)
    for k, a in enumerate((0, 45, 90, 180, 270)):
        r = ar.rotate(-a, expand=True, resample=Image.BICUBIC); im.alpha_composite(r, (730 + k * 90, 620)); im.alpha_composite(pl, (722 + k * 90, 656)); txt(im, (757 + k * 90, 667), "120m", 12, anchor="mm")
    txt(im, (20, 740), "⑧ 타이틀 메뉴 버튼(보통 · 고름 · 막힘) + 안개 · ⑨ 로딩 팁 판", 20)
    ts = Image.open(os.path.join(A3, "title", "title_screen.png")).convert("RGBA").resize((960, 540)); fog = L("title_fog_a"); fg = fog.crop((0, 0, 2048, 512)).resize((960, 240)); ts.alpha_composite(fg, (0, 260))
    for k, (st, lab) in enumerate((("normal", "이어하기"), ("hover", "새로 시작"), ("normal", "설정"), ("normal", "끝내기"))):
        b = nine(L("menu_btn_" + st), 300, 56, 20); ts.alpha_composite(b, (640, 250 + k * 66)); txt(ts, (790, 278 + k * 66), lab, 22, anchor="mm")
    tp = nine(L("loading_tip_plate"), 720, 56, 24); ts.alpha_composite(tp, (120, 470)); txt(ts, (180, 498), "혼은 부르면 오고, 놓으면 멀어집니다", 20, (42, 42, 56), "lm")
    im.alpha_composite(ts, (20, 780)) if False else im.paste(ts.convert("RGB"), (20, 780)) if False else None
    ts2 = ts.resize((640, 360)); im.alpha_composite(ts2, (20, 790))
    b = Image.new("RGBA", (300, 56), (0, 0, 0, 0))
    for k, st in enumerate(("normal", "hover", "disabled")): im.alpha_composite(nine(L("menu_btn_" + st), 300, 56, 20), (700, 800 + k * 66))
    txt(im, (710, 800 + 28), "보통", 20, anchor="lm"); txt(im, (710, 800 + 94), "고름(붉은 막대)", 20, anchor="lm"); txt(im, (710, 800 + 160), "막힘", 20, (150, 140, 110), "lm")
    im.convert("RGB").save(os.path.join(OUT, "first10_sheet_b.jpg"), quality=88)

if __name__ == "__main__":
    sheet_a(); sheet_b(); print("ok")
