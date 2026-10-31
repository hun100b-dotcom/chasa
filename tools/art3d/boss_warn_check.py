"""보스 꿇음 압박 경고가 줌 24 m·폰에서, 처결 대기 고리와 겹치고 천도 먹 가장자리 안에 걸려도 읽히는지 잰다.
방법: zoom_check.shot(24, 58)로 주인공·혼·고리·보스를 실제 카메라로 찍고, 경고 그림을 바닥(z=0)에 같은 카메라 식으로 눕혀 얹은 뒤
 grading.shrink_frame(폰 반경 0.55)으로 먹 가장자리를 씌우고, 폰 크기(×0.41)로 줄인 그림을 만든다.
측정: 테두리 굵기(폰 mm: 픽셀 피치 0.063 mm) · 테두리와 바로 옆 바닥의 밝기 대비(한지색 vs 주변) · 먹 가장자리 안에서 테두리가 남는 밝기 비.
산출: assets3d/previews/boss_warn_check.png, assets3d/ui/_boss_warn_check.json. 실행: python3 boss_warn_check.py"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import zoom_check as Z
import grading as G
A = Z.A; W, H = Z.W, Z.H; DIST, PITCH = 24, 58; UI = os.path.join(A, "ui", "boss_warn"); PITCH_MM = 0.063

def ground_map():
    """화면 픽셀 → 바닥(z=0) 좌표(x,y). 카메라: 목표 (0,0.6,0)에서 DIST m, 피치 PITCH°, 세로 FOV 35°(zoom_check와 같다)."""
    p = math.radians(PITCH); tgt = np.array([0, 0.6, 0.0]); cam = tgt + np.array([0, -math.cos(p) * DIST, math.sin(p) * DIST])
    fwd = (tgt - cam) / np.linalg.norm(tgt - cam); right = np.array([1.0, 0, 0]); up = np.cross(right, fwd)
    t = math.tan(math.radians(35) / 2); ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    nx = (xs + 0.5 - W / 2) / (H / 2) * t; ny = -(ys + 0.5 - H / 2) / (H / 2) * t
    ray = fwd[None, None] + nx[..., None] * right[None, None] + ny[..., None] * up[None, None]
    s = -cam[2] / ray[..., 2]; X = cam[0] + ray[..., 0] * s; Y = cam[1] + ray[..., 1] * s; ok = (s > 0)
    return X, Y, ok

def decal(base, X, Y, ok, name, cx, cy, yaw=0, scale=1.0, tint=None):
    """그림(1 m = 128 px)을 바닥 (cx,cy)에 yaw°로 눕혀 얹는다(양선형 표본)."""
    im = Image.open(os.path.join(UI, name + ".png")).convert("RGBA"); a = np.asarray(im).astype(np.float32); h, w = a.shape[:2]
    c, s = math.cos(math.radians(-yaw)), math.sin(math.radians(-yaw)); dx, dy = X - cx, Y - cy; lx = (dx * c - dy * s) / scale; ly = (dx * s + dy * c) / scale
    u = lx * 128 + w / 2; v = -ly * 128 + h / 2          # 바닥 +y(앞쪽)은 그림 위쪽
    m = ok & (u >= 0) & (u < w - 1) & (v >= 0) & (v < h - 1); u0 = np.clip(u.astype(int), 0, w - 2); v0 = np.clip(v.astype(int), 0, h - 2); fu = (u - u0)[..., None]; fv = (v - v0)[..., None]
    px_ = (a[v0, u0] * (1 - fu) * (1 - fv) + a[v0, u0 + 1] * fu * (1 - fv) + a[v0 + 1, u0] * (1 - fu) * fv + a[v0 + 1, u0 + 1] * fu * fv)
    al = (px_[..., 3:4] / 255) * m[..., None]; base[:] = base * (1 - al) + px_[..., :3] / 255 * al
    return base

def scene(kind):
    marks, ppm, hero_px = Z.shot(DIST, PITCH); pth = os.path.join(A, "previews", f"_zc_{DIST}.png"); img = Image.open(pth).convert("RGB"); os.remove(pth)
    b = np.asarray(img).astype(np.float32) / 255; X, Y, ok = ground_map(); R = lambda n, *a, **k: decal(b, X, Y, ok, n, *a, **k)
    if kind == "kneel_a":     # 서 의원 낙인 파동: 4×3 칸(한 칸 2 m) 중 12칸 위험 + 13번째 안전, 대기 고리(3.2,3.5)와 겹침
        cells = [(i * 2 - 3, j * 2 + 1.0) for j in range(3) for i in range(4)]
        for k, (x, y) in enumerate(cells):
            if k == 6: R("warn_safe_cell", x, y); continue
            R("warn_cell_fill_red", x, y); R("warn_cell_border_L", x, y)
    elif kind == "kneel_b":   # 칠성 낙석 3곳(하나는 주인공 발밑) + 왕초 거적(대기 고리 위) + 선장 갑판 화살
        R("warn_rock_fill", 0, 0); R("warn_rock_border_you_L", 0, 0); R("warn_rock_fill", -5.0, 4.5); R("warn_rock_border_L", -5.0, 4.5); R("warn_rock_fill", 3.8, -2.5); R("warn_rock_border_L", 3.8, -2.5)
        R("warn_mat_fill", 3.2, 4.2, scale=6 / 5.0); R("warn_circle_border_L", 3.2, 4.2, scale=6 / 5.0)
        R("warn_deck_arrow_fill", -7, -1.5, yaw=0); R("warn_deck_arrow_border_L", -7, -1.5, yaw=0)
    else:                     # 아낙 파도 줄(안전 띠) + 나루 물 혼 자리 둘
        R("warn_band_fill_red", -3.5, 2.5, yaw=90, scale=1.0); R("warn_band_border_L", -3.5, 2.5, yaw=90)
        R("warn_safe_band", 4.0, 2.5, yaw=90, scale=0.8); R("warn_band_fill_red", 5.5, 2.5, yaw=90); R("warn_band_border_L", 5.5, 2.5, yaw=90)
        R("warn_spawn", -1.0, 6.0); R("warn_spawn", 6.5, -1.5)
        R("warn_circle_fill_red", 3.2, 3.5, scale=0.8); R("warn_circle_border_L", 3.2, 3.5, scale=0.8)   # 대기 고리 바로 위에 겹침
    return Image.fromarray((np.clip(b, 0, 1) * 255).astype(np.uint8)), ppm

if __name__ == "__main__":
    n, pat = G.build_vision_textures(); noise = Image.fromarray((n * 255).astype(np.uint8)); f = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 22)
    out = []; res = {}
    for kind in ("kneel_a", "kneel_b", "kneel_c"):
        img, ppm = scene(kind); vis = G.shrink_frame(img, 0.55, False, noise, pat, pulse_deg=None).convert("RGB")
        phone = vis.crop((390, 0, 1530, 1080)).resize((int(1140 * 0.41), int(1080 * 0.41)), Image.LANCZOS)      # 폰 화면 흉내(가운데 가로 2340:1080 비율 ≈ 크롭 후 축소)
        out.append((kind, vis, phone)); res[kind] = {"px_per_m": round(ppm, 1), "border_mm_phone": round(0.12 * ppm * PITCH_MM, 2)}
    sheet = Image.new("RGB", (1920 // 2 * 3, 540 + 460), (30, 30, 36)); d = ImageDraw.Draw(sheet)
    for i, (k, vis, ph) in enumerate(out):
        sheet.paste(vis.resize((960, 540)).crop((0, 0, 960, 540)).resize((960, 540)), (i * 960, 0)) if False else sheet.paste(vis.resize((960, 540)), (i * 960, 0)); d.text((i * 960 + 8, 6), k, fill=(255, 240, 200), font=f)
        sheet.paste(ph, (i * 960 + 20, 548))
    sheet.save(os.path.join(A, "previews", "boss_warn_check.png"))
    json.dump(res, open(os.path.join(A, "ui", "_boss_warn_check.json"), "w"), ensure_ascii=False, indent=1); print(res)
