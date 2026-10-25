"""HUD 2차: 도술 아이콘 15종(스킬 칸 64px용 재가공) + 데미지 숫자 그림 글꼴 + 차사 초상.
왜 다시 내나: 기존 도술 아이콘(128px)은 자체 틀이 있어 새 스킬 칸(64px, 금 테두리)과 틀이 겹친다 → 틀을 걷어 내고 칸 안쪽(56px)에 맞게 둥글게 잘라 1배/2배로 낸다.
사용: python3 hud_art2.py"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageFont
from ui_lib import *
import hud_art as H

ROOT = os.path.join(HERE, "..", "..")
TREES = {"bureum": "부름(혼을 불러 모음)", "eolluk": "얼럭(원념 터뜨림)", "jul": "줄(사슬 기술)"}

def skill_icons():
    for t, label in TREES.items():
        for i in range(1, 6):
            src = Image.open(os.path.join(ROOT, "assets", "sprites", "ui", f"icon_skill_{t}_{i}.png")).convert("RGBA")
            inner = src.crop((9, 9, 119, 119)).resize((112, 112), Image.LANCZOS)         # 옛 틀(가장자리 9px) 걷어 냄
            m = rr_mask(112, 112, 10); inner.putalpha(ImageChops.multiply(inner.split()[3], m))
            save(inner, f"icon_{t}_{i}", "hud/skill", note=f"도술 {label} {i}번 — 칸 안쪽 56×56(칸 왼쪽 위에서 +4,+4). {'5번은 궁극기: slot_ultimate 틀과 함께' if i == 5 else ''}")
    ul = H.plate(64, 64, 8, 232, True, 2, glow=GOLD); im = H.canvas(72, 72); im.alpha_composite(shadow(ul, (0, H.S(2)), H.S(4), 0.55), (H.S(4), H.S(4))); save(im, "slot_ultimate", "hud", note="궁극기 칸(금빛 테두리 빛). 도술 5번 아이콘용")

def digits():
    f_path = "/tmp/fonts/BlackHanSans-Regular.ttf"; styles = {
        "normal": dict(size=28, top=(250, 246, 236), bot=(214, 206, 188), out=(14, 18, 36), ow=3, note="일반 피해 28px"),
        "crit":   dict(size=40, top=(255, 238, 120), bot=(244, 184, 40), out=(52, 24, 14), ow=4, note="치명 40px(노랑) — 주황이 아니라 노랑"),
        "taken":  dict(size=30, top=(255, 150, 140), bot=(226, 70, 70), out=(40, 8, 14), ow=3, note="받은 피해(붉음)"),
        "heal":   dict(size=28, top=(190, 255, 232), bot=(80, 216, 176), out=(8, 40, 38), ow=3, note="회복(청록)"),
    }
    chars = "0123456789,.+-"; meta = {}
    for name, st in styles.items():
        K4 = 4; font_ = ImageFont.truetype(f_path, st["size"] * K4); asc, desc = font_.getmetrics(); cell_h = (asc + desc) // K4 + st["ow"] * 2 + 4
        cells = []; x = 0; info = {}
        for ch in chars + "!":
            bb = font_.getbbox(ch); adv = int(font_.getlength(ch)); w = adv // K4 + st["ow"] * 2 + 2
            m = Image.new("L", (w * K4, cell_h * K4), 0); ImageDraw.Draw(m).text((st["ow"] * K4 + K4, st["ow"] * K4), ch, font=font_, fill=255)
            outl = m.filter(ImageFilter.MaxFilter(st["ow"] * 2 * K4 // 2 * 2 + 1)).filter(ImageFilter.GaussianBlur(K4 * 0.6))
            fill = Image.fromarray(np.dstack([H.vgrad(w * K4, cell_h * K4, st["top"], st["bot"]), np.full((cell_h * K4, w * K4), 255)]).astype(np.uint8), "RGBA")
            g = Image.new("RGBA", (w * K4, cell_h * K4), tuple(st["out"]) + (0,)); g.putalpha(outl); g.alpha_composite(Image.composite(fill, Image.new("RGBA", fill.size, (0, 0, 0, 0)), m))
            hi = Image.new("RGBA", g.size, (0, 0, 0, 0)); ImageDraw.Draw(hi).rectangle([0, int(cell_h * K4 * 0.18), w * K4, int(cell_h * K4 * 0.34)], fill=(255, 255, 255, 70)); hi.putalpha(ImageChops.multiply(hi.split()[3], m)); g.alpha_composite(hi)
            g1 = g.resize((w, cell_h), Image.LANCZOS); cells.append((ch, g1, w)); info[ch] = {"x": x, "w": w}; x += w
        atlas = Image.new("RGBA", (x, cell_h), (0, 0, 0, 0))
        for ch, g1, w in cells: atlas.alpha_composite(g1, (info[ch]["x"], 0))
        save(atlas.resize((atlas.width * 2, atlas.height * 2), Image.LANCZOS), f"dmg_{name}", "hud/damage", note=st["note"] + ". 글자 이어 붙인 띠(한 줄 가로 글자 칸, JSON 참고)")
        meta[name] = {"cell_h": cell_h, "glyphs": info, "size_px": st["size"], "note": st["note"]}
    # 글자 낱말(빗나감·회피): 한글은 그림으로
    words = {}
    for key, txt_, col in (("miss", "빗나감", ((235, 235, 240), (170, 176, 196), (14, 18, 36))), ("dodge", "회피", ((190, 255, 232), (80, 216, 176), (8, 40, 38)))):
        K4 = 4; f2 = ImageFont.truetype(f_path, 26 * K4); w4 = int(f2.getlength(txt_)) + 24 * K4; h4 = 40 * K4
        m = Image.new("L", (w4, h4), 0); ImageDraw.Draw(m).text((12 * K4, 4 * K4), txt_, font=f2, fill=255); outl = m.filter(ImageFilter.MaxFilter(25)).filter(ImageFilter.GaussianBlur(2))
        fill = Image.fromarray(np.dstack([H.vgrad(w4, h4, col[0], col[1]), np.full((h4, w4), 255)]).astype(np.uint8), "RGBA"); g = Image.new("RGBA", (w4, h4), col[2] + (0,)); g.putalpha(outl); g.alpha_composite(Image.composite(fill, Image.new("RGBA", fill.size, (0, 0, 0, 0)), m))
        save(g.resize((w4 // 2, h4 // 2), Image.LANCZOS), f"word_{key}", "hud/damage", note=f"'{txt_}' 글자 그림(26px)")
    json.dump({"font_source": "글자 모양: Black Han Sans(SIL OFL 1.1) 로 그림 글꼴을 만듦. 동적 글자가 필요하면 같은 글꼴 TTF 를 assets3d/ui/fonts/ 에 둠", "styles": meta,
               "use": "숫자 한 글자씩 낱장으로 이어 붙여 월드 공간에 띄운다(일반 28px·치명 40px, 0.6초 동안 위로 0.8m 뜨며 흐려짐). 글자 사이 간격은 각 칸 폭 그대로. 쉼표는 3자리마다."}, open(os.path.join(UI, "hud", "damage", "damage_font.json"), "w"), ensure_ascii=False, indent=1)
    os.makedirs(os.path.join(UI, "fonts"), exist_ok=True)
    import shutil; shutil.copy(f_path, os.path.join(UI, "fonts", "BlackHanSans-Regular.ttf")); shutil.copy("/tmp/fonts/OFL.txt", os.path.join(UI, "fonts", "OFL-BlackHanSans.txt"))

def portrait():
    p = os.path.join(A3, "previews", "scene_portrait.png")
    if not os.path.exists(p): print("초상 렌더 없음"); return
    import grading
    im = grading.post(Image.open(p).convert("RGB"), "night", "clear"); W = im.width
    # 정사각 72×72(2배 144) 초상: 얼굴이 가운데 위쪽에 오게 자르기 + 남청 비네트
    c = im.crop((int(W * 0.10), int(W * 0.06), int(W * 0.90), int(W * 0.86))).resize((288, 288), Image.LANCZOS)
    a = np.asarray(c).astype(np.float32) / 255; ys, xs = np.mgrid[0:288, 0:288].astype(np.float32); d = np.sqrt(((xs - 144) / 144) ** 2 + ((ys - 150) / 144) ** 2); v = np.clip((d - 0.55) / 0.5, 0, 1)[..., None] * 0.85
    a = a * (1 - v) + np.array(ABYSS, np.float32) / 255 * v; out = Image.fromarray((a * 255).astype(np.uint8)).resize((144, 144), Image.LANCZOS).convert("RGBA")
    m = rr_mask(144, 144, 14); out.putalpha(m); save(out, "portrait_chasa", "hud", note="차사 초상 72×72(@2x 144). portrait_frame 의 뚫린 가운데 아래에 깐다")
    out.resize((288, 288), Image.LANCZOS).save(os.path.join(UI, "hud", "portrait_chasa_large.png"))

if __name__ == "__main__":
    skill_icons(); digits(); portrait(); dump_manifest("ui_manifest.json"); print("완료", len(MANIFEST))
