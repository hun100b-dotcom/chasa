"""첫인상 자산: 《차사》 로고(붓글씨 + 붉은 인), 웹 아이콘(favicon), 로딩 막대 틀, 타이틀·로딩 화면 합성.
산출(assets3d/title/): logo_chasa.png(밤 화면용 한지색) · logo_chasa_ink.png(밝은 바탕용 먹색) · seal_chasa.png · favicon.svg/.ico/_16~512.png · apple-touch-icon.png
  loading_bar_frame.png / loading_bar_fill.png · title_screen.png(로고 합성) · title_bg.png(로고 없음) · loading_1_solgogae.jpg · loading_2_mulmagi.jpg · loading_3_pyedang.jpg · title_manifest.json
글꼴: 나눔 붓글씨(Nanum Brush Script, SIL OFL 1.1 — 상업 사용·수정 허용, https://github.com/google/fonts/tree/main/ofl/nanumbrushscript). 없으면 내려받는다. 인(도장)의 한자는 문천 정흑체(WenQuanYi Zen Hei).
IP 규칙: 기존 작품의 로고·캐릭터·고유 이름을 쓰지 않는다. 상표성 문구 없이 제목 두 글자와 직접 그린 도장만 쓴다.
실행: python3 title_assets.py [logo|icon|compose|all]  (compose는 field_scene.py가 렌더한 scene_title/load_*.png가 먼저 있어야 한다)"""
import os, sys, json, math, urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__)); A3 = os.path.join(HERE, "..", "..", "assets3d"); OUT = os.path.join(A3, "title"); PRE = os.path.join(A3, "previews")
os.makedirs(OUT, exist_ok=True)
FONT_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/nanumbrushscript/NanumBrushScript-Regular.ttf"
FONT = "/tmp/fonts/NanumBrushScript-Regular.ttf"; HANJA = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
RED = (196, 52, 40); HANJI = (243, 231, 211); INK = (30, 26, 30)
if not os.path.exists(FONT):
    os.makedirs(os.path.dirname(FONT), exist_ok=True); urllib.request.urlretrieve(FONT_URL, FONT)

def noise(w, h, cell, seed):
    r = np.random.RandomState(seed); g = r.rand(h // cell + 2, w // cell + 2)
    return np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255

def brush_text(txt, size, pad=60):
    """글자 마스크(L)에 붓맛을 낸다: 살짝 번짐 + 가장자리가 갈라지는 마른 붓"""
    f = ImageFont.truetype(FONT, size); bb = f.getbbox(txt); w, h = bb[2] - bb[0] + pad * 2, bb[3] - bb[1] + pad * 2
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).text((pad - bb[0], pad - bb[1]), txt, font=f, fill=255)
    m = m.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(1.6))        # 획을 살짝 굵고 둥글게
    a = np.asarray(m, np.float32) / 255
    fib = noise(w, h, 3, 1) * 0.6 + noise(w, h, 9, 2) * 0.4                                 # 붓털 결(가로로 긴 노이즈)
    fib = np.asarray(Image.fromarray((fib * 255).astype(np.uint8)).resize((w, h)).filter(ImageFilter.GaussianBlur(0.6)), np.float32) / 255
    edge = np.clip(1 - np.abs(a - 0.5) * 2, 0, 1)                                           # 획 가장자리일수록 1
    a = np.clip(a - edge * np.clip(fib - 0.45, 0, 1) * 1.9, 0, 1)                           # 가장자리만 갈라짐
    a = np.clip((a - 0.35) * 2.3, 0, 1)
    return Image.fromarray((a * 255).astype(np.uint8))

def seal(size=260, text="差使", seed=3):
    """붉은 도장(음각): 붉은 정사각에 한자 두 자를 세로로 흰 글씨(파낸 자리). 가장자리는 닳아 불규칙하고 잉크가 고르지 않게 번진다."""
    S = size * 2; im = Image.new("L", (S, S), 0); d = ImageDraw.Draw(im); d.rounded_rectangle([8, 8, S - 8, S - 8], radius=int(S * 0.04), fill=255)
    f = ImageFont.truetype(HANJA, int(S * 0.44), index=0)
    for i, ch in enumerate(text):
        bb = f.getbbox(ch); cx = S / 2; cy = S * (0.27 + 0.46 * i); d.text((cx - (bb[0] + bb[2]) / 2, cy - (bb[1] + bb[3]) / 2), ch, font=f, fill=0)
    inner = Image.new("L", (S, S), 0); ImageDraw.Draw(inner).rounded_rectangle([S * 0.07, S * 0.07, S * 0.93, S * 0.93], radius=int(S * 0.03), outline=0, width=int(S * 0.018))   # 안쪽 테두리 선(흰)
    a = np.asarray(ImageChops.subtract(im, inner), np.float32) / 255
    wear = noise(S, S, 6, 11) * 0.6 + noise(S, S, 18, 12) * 0.4
    a = np.clip(a - np.clip(wear - 0.62, 0, 1) * 2.4, 0, 1)                                  # 닳은 구멍
    a = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.1)), np.float32) / 255
    col = np.array(RED, np.float32)[None, None, :] * (0.88 + 0.2 * noise(S, S, 14, 13))[..., None]
    outer = Image.new('L', (S, S), 0); ImageDraw.Draw(outer).rounded_rectangle([8, 8, S - 8, S - 8], radius=int(S * 0.04), fill=255); shape = np.asarray(outer, np.float32) / 255; shape = np.asarray(Image.fromarray((shape * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.1)), np.float32) / 255
    cream = np.array(HANJI, np.float32)[None, None, :]; col = cream * (1 - a[..., None]) + col * a[..., None]      # 파낸 글자는 한지색으로 채워 어떤 바탕에서도 같게 보이게
    rgba = np.dstack([col, shape * 255]).astype(np.uint8); return Image.fromarray(rgba, "RGBA").resize((size, size), Image.LANCZOS)

def make_logo():
    # 점검(타이틀): 한 줄로 쓰면 ㅊ·ㅏ·ㅅ·ㅏ 네 덩이가 같은 간격으로 놓여 'ネトイト'(가타카나)처럼 보였다. 글자(음절)마다 따로 그려 음절 사이만 넓힌다 → 자음+모음이 한 글자로 묶여 보임.
    ma, mb = brush_text("차", 900, pad=30), brush_text("사", 900, pad=30); GAP = 120
    w, h = ma.width + mb.width + GAP, max(ma.height, mb.height); m = Image.new("L", (w, h), 0)
    m.paste(ma, (0, (h - ma.height) // 2)); m.paste(mb, (ma.width + GAP, (h - mb.height) // 2), mb); m = m.crop(m.getbbox()); m = ImageOps.expand(m, 60, 0); w, h = m.size
    for name, col in (("logo_chasa.png", HANJI), ("logo_chasa_ink.png", INK)):
        c = Image.new("RGBA", (w, h), col + (0,)); c.putalpha(m)
        sh = Image.new("RGBA", (w, h), (0, 0, 0, 0)); s = Image.new("RGBA", (w, h), (10, 8, 14, 140)); s.putalpha(m.filter(ImageFilter.GaussianBlur(10))); sh.alpha_composite(s, (8, 12))
        out = Image.new("RGBA", (w + 220, h + 80), (0, 0, 0, 0))
        if name == "logo_chasa.png": out.alpha_composite(sh, (20, 20))                       # 밤 화면용만 은은한 그림자
        out.alpha_composite(c, (20, 20))
        sl = seal(300); sl = sl.rotate(-4, expand=True, resample=Image.BICUBIC); out.alpha_composite(sl, (out.width - sl.width - 6, out.height - sl.height - 70))
        bb = out.getbbox(); out = out.crop((max(bb[0] - 20, 0), max(bb[1] - 20, 0), min(bb[2] + 20, out.width), min(bb[3] + 20, out.height))); out.save(os.path.join(OUT, name)); sz = out.size
    seal(512).save(os.path.join(OUT, "seal_chasa.png")); return sz

def make_icons():
    """웹 아이콘: 붉은 도장 사각에 '差'(차) 한 글자. 작은 크기(16px)에서도 읽히도록 글자를 크게, 모서리를 둥글게. 모양은 favicon.svg와 같은 설계."""
    def icon(n):
        S = n * 4; im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im); d.rounded_rectangle([0, 0, S - 1, S - 1], radius=int(S * 0.2), fill=RED + (255,))
        f = ImageFont.truetype(HANJA, int(S * 0.78), index=0); bb = f.getbbox("差"); d.text((S / 2 - (bb[0] + bb[2]) / 2, S / 2 - (bb[1] + bb[3]) / 2 + S * 0.01), "差", font=f, fill=HANJI + (255,))
        return im.resize((n, n), Image.LANCZOS)
    for n in (16, 32, 48, 64, 180, 192, 512): icon(n).save(os.path.join(OUT, f"favicon_{n}.png") if n != 180 else os.path.join(OUT, "apple-touch-icon.png"))
    icon(256).save(os.path.join(OUT, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (256, 256)])
    # SVG: 한자 글리프는 글꼴 없이도 그려지게 텍스트로 두되, 글꼴이 없는 환경에선 png/ico가 대신 쓰인다.
    open(os.path.join(OUT, "favicon.svg"), "w", encoding="utf-8").write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="13" fill="#C43428"/><text x="32" y="49" font-size="50" text-anchor="middle" font-family="\'Noto Serif CJK KR\',\'Noto Sans CJK KR\',\'Malgun Gothic\',\'Apple SD Gothic Neo\',serif" font-weight="700" fill="#F3E7D3">差</text></svg>')

def make_bar():
    """로딩 막대: 붓으로 그은 가로 틀(먹색 띠 + 한지 테두리)과 채움(붉은 붓줄). 틀 1024×64, 채움 1024×40 — 채움은 코드가 왼쪽부터 잘라 보여 주면 된다."""
    W, H = 1024, 64; fr = Image.new("RGBA", (W, H), (0, 0, 0, 0)); a = np.zeros((H, W), np.float32); yy, xx = np.mgrid[0:H, 0:W]
    a = np.clip(1 - np.maximum(np.abs(yy - H / 2) - (H / 2 - 12 - 2.5 * np.sin(xx / 70.0)), 0) / 3, 0, 1); a *= np.clip((xx - 6) / 20, 0, 1) * np.clip((W - 6 - xx) / 20, 0, 1)
    wear = noise(W, H, 4, 21); a = np.clip(a - np.clip(wear - 0.72, 0, 1) * 2, 0, 1)
    body = np.zeros((H, W, 4), np.float32); body[..., :3] = np.array((22, 18, 24)); body[..., 3] = a * 215
    frame = Image.fromarray(body.astype(np.uint8), "RGBA"); ImageDraw.Draw(frame).line([(10, 6), (W - 10, 6)], fill=HANJI + (150,), width=2); ImageDraw.Draw(frame).line([(10, H - 7), (W - 10, H - 7)], fill=HANJI + (150,), width=2)
    frame.save(os.path.join(OUT, "loading_bar_frame.png"))
    H2 = 40; yy, xx = np.mgrid[0:H2, 0:W]; a = np.clip(1 - np.maximum(np.abs(yy - H2 / 2) - (H2 / 2 - 5 - 2 * np.sin(xx / 53.0 + 1)), 0) / 2.5, 0, 1)
    fib = noise(W, H2, 2, 22) * 0.7 + noise(W, H2, 7, 23) * 0.3; a = np.clip(a - np.clip(fib - 0.8, 0, 1) * 3 * (xx / W) ** 0.3, 0, 1)
    col = np.zeros((H2, W, 4), np.float32); col[..., 0] = RED[0] * (0.85 + 0.25 * fib); col[..., 1] = RED[1] * (0.85 + 0.25 * fib); col[..., 2] = RED[2]; col[..., 3] = a * 255
    Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGBA").save(os.path.join(OUT, "loading_bar_fill.png"))

def grade(im, strength=0.55):
    """밤 화면 마무리: 가장자리 어둡게 + 아래쪽 어둡게(막대·글자 자리)."""
    a = np.asarray(im.convert("RGB"), np.float32) / 255; h, w, _ = a.shape; ys = np.linspace(0, 1, h)[:, None]; xs = np.linspace(-1, 1, w)[None, :]
    v = 1 - strength * np.clip((xs ** 2 * 0.9 + (ys * 2 - 1) ** 2 * 0.7) / 1.7, 0, 1); bot = 1 - 0.55 * np.clip((ys - 0.72) / 0.28, 0, 1) ** 1.5
    return Image.fromarray((np.clip(a * (v * bot)[..., None], 0, 1) * 255).astype(np.uint8))

def compose():
    man = {}
    logo = Image.open(os.path.join(OUT, "logo_chasa.png"))
    bg = grade(Image.open(os.path.join(PRE, "scene_title.png")), 0.5); bg.save(os.path.join(OUT, "title_bg.png"), optimize=True)
    t = bg.convert("RGBA"); lw = int(t.width * 0.27); lg = logo.resize((lw, int(logo.height * lw / logo.width)), Image.LANCZOS)
    t.alpha_composite(lg, (int(t.width * 0.035), int(t.height * 0.06))); t.convert("RGB").save(os.path.join(OUT, "title_screen.png"), optimize=True); man["title"] = {"size": bg.size, "logo_rect_norm": [0.035, 0.06, 0.035 + lg.width / t.width, 0.06 + lg.height / t.height]}
    for k, n in (("load_a", "loading_1_solgogae"), ("load_b", "loading_2_mulmagi"), ("load_c", "loading_3_pyedang")):
        g = grade(Image.open(os.path.join(PRE, f"scene_{k}.png")), 0.55); g.save(os.path.join(OUT, n + ".jpg"), quality=88); man[n] = {"size": g.size, "bar_y_norm": 0.90}
    json.dump({"note": "타이틀·로딩 화면 자산. 로고는 title_screen.png처럼 왼쪽 위에, 로딩 막대는 아래쪽(화면 높이의 90% 근처)에 얹는다. 로딩 막대 틀 1024×64·채움 1024×40.", "files": man}, open(os.path.join(OUT, "title_manifest.json"), "w"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    w = sys.argv[1] if len(sys.argv) > 1 else "all"
    if w in ("logo", "all"): print("logo", make_logo())
    if w in ("icon", "all"): make_icons(); make_bar(); print("icons/bar")
    if w in ("compose", "all"): compose(); print("compose")
