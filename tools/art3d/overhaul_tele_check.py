"""예고 장판 확인판(아트): 밝은 낮 풀밭·어두운 밤 바닥 두 배경에서 '잔상 → 절반 차오름 → 가득' 세 단계를 1:1 크기로 놓고,
같은 장면을 흑백·색약(적록) 시뮬로도 보여 준다. 파혼 범위(주황 점선)와 나란히 놓아 '모양으로 갈리는지' 눈으로 확인.
실행: python3 tools/art3d/overhaul_tele_check.py → assets3d/previews/overhaul_tele_check.png (+ 수치 assets3d/ui/overhaul/_tele_check.json)"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from overhaul_lib import *

T = os.path.join(OUT, "tele")
def ld(n): return Image.open(os.path.join(T, n + ".png")).convert("RGBA")
def put(bg, im, cx, cy, anchor="center"):
    bg.alpha_composite(im, (int(cx - im.width * (0.5 if anchor == "center" else 0)), int(cy - im.height / 2)))

def scaled(im, sx, sy, pivot):
    """채움을 pivot 기준으로 sx,sy 배 키웠을 때의 그림과 놓을 위치 보정(코드가 하는 일을 흉내)."""
    w, h = im.size; nw, nh = max(1, int(w * sx)), max(1, int(h * sy)); r = im.resize((nw, nh), Image.LANCZOS)
    return r, (pivot[0] * w - pivot[0] * nw, pivot[1] * h - pivot[1] * nh)

def scene(bg_col, ground_noise):
    """절반 크기(0.5배)로 줄여 한 판에 담는다. 위 줄: 원 r2.5 잔상만 / 절반 / 가득 + 파혼 r3.0. 아래 줄: 부채꼴 · 띠 · 선."""
    W, H = 1700, 620; bg = Image.new("RGBA", (W, H), bg_col + (255,))
    rng = np.random.RandomState(3); n = (rng.rand(H // 8, W // 8) * 2 - 1) * ground_noise
    nn = np.asarray(Image.fromarray(((n + 1) * 127).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) / 127 - 1
    a = np.asarray(bg, np.float32); a[..., :3] += nn[..., None] * 22; bg = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
    K = 0.5
    def L(n):
        im = ld(n); return im.resize((max(1, int(im.width * K)), max(1, int(im.height * K))), Image.LANCZOS)
    def grow(layer, cx, cy, sx, sy, pivot):
        """채움을 pivot 기준으로 sx,sy배 해서 (cx,cy)=그림 중심이 놓일 자리에 맞춰 얹기"""
        w, h = layer.size; nw, nh = max(1, int(w * sx)), max(1, int(h * sy)); r = layer.resize((nw, nh), Image.LANCZOS)
        px, py = cx - w / 2 + pivot[0] * w, cy - h / 2 + pivot[1] * h          # 기준점의 화면 위치(고정)
        bg.alpha_composite(r, (int(px - pivot[0] * nw), int(py - pivot[1] * nh)))
    d = ImageDraw.Draw(bg); y = 170
    for i, prog in enumerate((0.0, 0.5, 1.0)):
        cx = 190 + i * 400
        g = L("tele2_circle_r2_5_ghost"); bg.alpha_composite(g, (int(cx - g.width / 2), int(y - g.height / 2)))
        if prog > 0: grow(L("tele2_circle_r2_5_fill"), cx, y, prog, prog, (.5, .5))
        bd = L("tele2_circle_r2_5_border"); bg.alpha_composite(bd, (int(cx - bd.width / 2), int(y - bd.height / 2)))
        d.ellipse([cx - 9, y - 9, cx + 9, y + 9], fill=(40, 60, 90, 255), outline=(240, 240, 255, 255), width=2)
    p = L("tele2_pahon_r3_0"); bg.alpha_composite(p, (int(1440 - p.width / 2), int(y - p.height / 2)))
    d.ellipse([1431, y - 9, 1449, y + 9], fill=(40, 60, 90, 255), outline=(240, 240, 255, 255), width=2)
    y2 = 470
    for name, x0, prog in (("tele2_cone90_r2_2", 40, .6), ("tele2_band_6x1_6", 250, .55), ("tele2_line_14x0_6", 640, 1.0)):
        g = L(name + "_ghost"); bg.alpha_composite(g, (x0, int(y2 - g.height / 2)))
        f = L(name + "_fill"); pv_x = 14 * K / f.width
        sx = prog; grow(f, x0 + f.width / 2, y2, sx, sx if "cone" in name else 1.0, (pv_x, .5))
        bd = L(name + "_border"); bg.alpha_composite(bd, (x0, int(y2 - bd.height / 2)))
        d.ellipse([x0 + 7 * K - 9, y2 - 9, x0 + 7 * K + 9, y2 + 9], fill=(40, 60, 90, 255), outline=(240, 240, 255, 255), width=2)
    return bg

def gray(im): return im.convert("L").convert("RGB")
def deut(im):
    """적록 색약(제1형) 시뮬: Machado 2009 행렬(severity 1.0)"""
    M = np.array([[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]], np.float32)
    a = np.asarray(im.convert("RGB"), np.float32) / 255; lin = np.where(a <= .04045, a / 12.92, ((a + .055) / 1.055) ** 2.4)
    o = np.clip(lin @ M.T, 0, 1); s = np.where(o <= .0031308, o * 12.92, 1.055 * o ** (1 / 2.4) - .055)
    return Image.fromarray((np.clip(s, 0, 1) * 255).astype(np.uint8))

def contrast_ratio(a, b):
    f = lambda c: sum(w * (v / 255 if v / 255 <= .03928 else ((v / 255 + .055) / 1.055) ** 2.4) for w, v in zip((.2126, .7152, .0722), c))
    la, lb = f(a), f(b); hi, lo = max(la, lb), min(la, lb); return (hi + .05) / (lo + .05)

if __name__ == "__main__":
    day = scene((118, 150, 84), 1.0); night = scene((26, 34, 58), 0.6)
    rows = [day, night, gray(day), deut(day)]
    W = rows[0].width; H = sum(r.height for r in rows)
    sheet = Image.new("RGB", (W, H)); y = 0
    for r in rows: sheet.paste(r.convert("RGB"), (0, y)); y += r.height
    sheet = sheet.resize((W * 7 // 10, H * 7 // 10), Image.LANCZOS)
    os.makedirs(os.path.join(ROOT, "assets3d", "previews"), exist_ok=True)
    sheet.save(os.path.join(ROOT, "assets3d", "previews", "overhaul_tele_check.png"))
    # 수치: 테두리(한지색) 대 배경 대비비 — 낮 풀밭·밤 바닥·위험 채움 위
    res = {"border_vs_day_grass": round(contrast_ratio(HANJI, (118, 150, 84)), 2), "border_vs_night_floor": round(contrast_ratio(HANJI, (26, 34, 58)), 2),
           "border_ink_outline_vs_day_grass": round(contrast_ratio((18, 20, 30), (118, 150, 84)), 2),
           "pahon_orange_vs_day_grass": round(contrast_ratio(ORANGE, (118, 150, 84)), 2), "pahon_orange_vs_night_floor": round(contrast_ratio(ORANGE, (26, 34, 58)), 2)}
    json.dump(res, open(os.path.join(OUT, "_tele_check.json"), "w"), ensure_ascii=False, indent=1); print(res)
