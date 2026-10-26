"""천도 캐스팅 중 시야 60% 축소(먹 번짐 가장자리)가 낮·밤, PC(16:9)·폰(가로 2340×1080)에서
 ① '지금 위험하다'가 느껴지는지 ② 바깥에서 다가오는 혼의 실루엣이 보이는지를 같은 카메라로 점검한다.
값: 카메라 19 m·각도 52°·세로 FOV 35°, 반경 0.6(폰 짧은 변 600 미만이면 0.55 — 코드 GradingFx), 가장자리 먹 #0F1729 알파 0.94, 폭 0.12(grading.py shrink_frame과 같은 식).
측정: 가장자리에 있는 혼마다 '가려지는 비율(먹 알파)'을 잰다 = 1 이면 완전히 안 보임.
산출: assets3d/previews/vision_check.png (낮·밤 × PC·폰), assets3d/ui/_vision_check.json. 실행: python3 vision_check.py"""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
from zoom_check import imp, A
import grading as G
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from bpy_extras.object_utils import world_to_camera_view

DIST, PITCH = 19, 52
ENEMIES = [("souls/soul_day.glb", (-8.6, 2.4), "혼"), ("souls/soul_wail_day.glb", (9.8, 1.0), "넋두리"), ("souls/soul_day.glb", (7.4, -4.6), "혼"), ("souls/soul_elite_day.glb", (-10.6, -3.4), "거센 혼"), ("souls/soul_mote_day.glb", (0.5, 10.5), "잔넋")]

def shot(W, H, night):
    reset(); setup_render(10, (0, 0, 0.9), size=(W, H), ground_size=90, night=night); sc = bpy.context.scene; sc.cycles.samples = 16
    imp("characters/hero_chasa.glb", (0, 0, 0), 0); imp("souls/soul_day.glb", (2.6, 3.2, 0), 200); imp("fx/fx_wait_ring_day.glb", (2.6, 3.2, 0.04), 0, 0.9 * 2 / 2.12)
    for rel, (x, y), _ in ENEMIES: imp(rel, (x, y, 0), 180 if x > 0 else 0)
    cam = sc.camera; cd = cam.data; cd.type = "PERSP"; cd.sensor_fit = "VERTICAL"; cd.angle = math.radians(35); p = math.radians(PITCH)
    tgt = Vector((0, 0.0, 0.0)); cam.location = tgt + Vector((0, -math.cos(p) * DIST, math.sin(p) * DIST)); cam.rotation_euler = (math.radians(90 - PITCH), 0, 0)
    pth = os.path.join(A, "previews", "_vc.png"); sc.render.filepath = pth; sc.render.resolution_x, sc.render.resolution_y = W, H; bpy.ops.render.render(write_still=True)
    scr = lambda x, y, z: (lambda v: (v.x * W, (1 - v.y) * H))(world_to_camera_view(sc, cam, Vector((x, y, z))))
    marks = [{"name": "차사", "px": scr(0, 0, 0.9)}, {"name": "대상 혼", "px": scr(2.6, 3.2, 0.7)}] + [{"name": n, "px": scr(x, y, 0.8)} for _, (x, y), n in ENEMIES]
    img = Image.open(pth).convert("RGB"); os.remove(pth); return img, marks

def alpha_at(px, center, R, wd=0.12):
    d = math.hypot(px[0] - center[0], px[1] - center[1]) / R; a = min(1, max(0, (d - (1 - wd)) / (wd * 2))); return a * a * (3 - 2 * a) * 0.94, d

FOE = {"혼": "basic", "넋두리": "wail", "잔넋": "mote", "거센 혼": "elite"}
def lum(a): return float((np.asarray(a.convert("L"), np.float32) / 255).mean())
def inout(img, center, R):
    """안(반경 0.7R 안)과 밖(1.2R 밖) 평균 밝기와 비 — 바깥이 얼마나 확실히 어두운가(= 시야가 좁아졌다는 느낌)"""
    h, w = img.size[1], img.size[0]; ys, xs = np.mgrid[0:h, 0:w]; d = np.hypot(xs - center[0], ys - center[1]) / R; L = np.asarray(img.convert("L"), np.float32) / 255
    i, o = float(L[d < 0.7].mean()), float(L[d > 1.2].mean()); return round(i, 3), round(o, 3), round(i / max(o, 1e-3), 2)
def improved(base, radius, center, marks, ppm, night, noise, pat):
    """개선판: ① 밤에는 안쪽을 밝게(+30%)·청록 글로우 강하게 → 안팎 밝기 차를 낮과 비슷하게 ② 먹 알파 0.94→0.90 ③ 먹 속 혼 자리에 붉은 윤곽 실루엣(foe_*.png)"""
    W, H = base.size; im = base
    if night:     # 안쪽 들어올림: 가운데에서 멀어질수록 사라지는 마스크
        c = np.asarray(base).astype(np.float32) / 255; ys, xs = np.mgrid[0:H, 0:W]; R = math.hypot(W, H) * 0.5 * radius; d = np.hypot(xs - center[0], ys - center[1]) / R
        k = np.clip(1 - d, 0, 1)[..., None] ** 0.7 * 0.30; c = np.clip(c * (1 + k) + k * 0.05, 0, 1); im = Image.fromarray((c * 255).astype(np.uint8))
    out = G.shrink_frame(im, radius, False, noise, pat, pulse_deg=None)
    # 알파 0.90: 먹 위에 원래 화면을 4% 다시 섞는다(0.94→0.90에 해당)
    r = G.shrink_frame(im, None, False, noise, pat); a = np.asarray(out).astype(np.float32); b = np.asarray(r).astype(np.float32); out = Image.fromarray(np.clip(a * 0.957 + b * 0.043, 0, 255).astype(np.uint8)).convert("RGBA")
    R = math.hypot(W, H) * 0.5 * radius
    for m in marks:
        k = FOE.get(m["name"])
        if not k: continue
        a_, d_ = alpha_at(m["px"], center, R)
        if a_ < 0.5: continue          # 시야 안(먹이 옅은 곳)은 실제 몸이 보이니 그리지 않는다
        sp = Image.open(os.path.join(A, "ui", "first10", f"foe_{k}.png")).convert("RGBA"); sc_ = ppm / 40; sp = sp.resize((int(sp.width * sc_), int(sp.height * sc_)), Image.LANCZOS)
        foot_y = m["px"][1] + 0.8 * ppm * math.cos(math.radians(PITCH))   # 측정점은 몸 높이 0.8 m → 발밑 화면 위치로 내린다(코드는 WorldToScreen(e.Pos) 그대로 쓰면 된다)
        out.alpha_composite(sp, (int(m["px"][0] - sp.width / 2), int(foot_y - sp.height * 0.66)))
    return out.convert("RGB")

def main():
    n, pat = G.build_vision_textures(); noise = Image.fromarray((n * 255).astype(np.uint8)); f = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 26); res = {}; panels = []; panels_after = []
    for dev, (W, H, radius) in (("PC 1920×1080", (1920, 1080, 0.6)), ("폰 2340×1080", (2340, 1080, 0.55))):
        for tm, night in (("day", False), ("night", True)):
            img, marks = shot(W, H, night); base = G.post(img, tm, "clear"); cen = ((marks[0]["px"][0] + marks[1]["px"][0]) / 2, (marks[0]["px"][1] + marks[1]["px"][1]) / 2)
            R = math.hypot(W, H) * 0.5 * radius; out = G.shrink_frame(base, radius, False, noise, pat, pulse_deg=None); ppm = H / (2 * DIST * math.tan(math.radians(17.5)))
            after = improved(base, radius, cen, marks[2:], ppm, night, noise, pat); res[f'{dev}|{tm}|밝기(안,밖,비) 지금'] = inout(out, cen, R); res[f'{dev}|{tm}|밝기(안,밖,비) 개선'] = inout(after, cen, R)
            rows = []
            for m in marks[2:]:
                a, d = alpha_at(m["px"], cen, R); rows.append({"name": m["name"], "px": [round(m["px"][0]), round(m["px"][1])], "dist_over_R": round(d, 2), "ink_alpha": round(a, 2), "visible_pct": round((1 - a) * 100)})
            res[f"{dev}|{tm}"] = rows
            d = ImageDraw.Draw(out)
            for m, r in zip(marks[2:], rows): d.text((m["px"][0] - 30, m["px"][1] - 120), f'{r["name"]} {r["visible_pct"]}%', fill=(255, 235, 140), font=f)
            panels.append((dev, tm, out.resize((960, int(960 * H / W))))); panels_after.append((dev, tm, after.resize((960, int(960 * H / W)))))
    SW = 960 * 2; Hs = max(p[2].height for p in panels) * 2 + 70; S = Image.new("RGB", (SW, Hs), (20, 20, 26)); d = ImageDraw.Draw(S); y = 0
    for r in range(2):
        for c in range(2):
            dev, tm, im = panels[r * 2 + c]; S.paste(im, (c * 960, 35 + y)); d.text((c * 960 + 8, y + 2), f"{dev} · {'낮' if tm == 'day' else '밤'}", fill=(255, 240, 200), font=f)
        y += panels[r * 2][2].height + 35
    S.save(os.path.join(A, "previews", "vision_check.png"))
    S2 = Image.new("RGB", (SW, Hs), (20, 20, 26)); d2 = ImageDraw.Draw(S2); y = 0
    for r in range(2):
        for c in range(2):
            dev, tm, im = panels_after[r * 2 + c]; S2.paste(im, (c * 960, 35 + y)); d2.text((c * 960 + 8, y + 2), f"개선 · {dev} · {'낮' if tm == 'day' else '밤'}", fill=(255, 240, 200), font=f)
        y += panels_after[r * 2][2].height + 35
    S2.save(os.path.join(A, "previews", "vision_check_after.png")); json.dump(res, open(os.path.join(A, "ui", "_vision_check.json"), "w"), ensure_ascii=False, indent=1)
    for k, v in res.items(): print(k, v if isinstance(v, tuple) else [(x["name"], x["visible_pct"]) for x in v])
main()
