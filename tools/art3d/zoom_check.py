"""카메라 줌 13/19/24 m(기획 점검 v1.6)에서 주인공·혼·처결 대기 고리·맺힘 막대가 얼마나 크게 보이는지 실제 카메라로 찍어 잰다.
왜: 줌이 멀어지면(16→19, 20→24 m) 같은 몸이 화면에서 15~20% 작아진다. 폰은 화면 높이가 같은 1080 픽셀이어도 물리 크기가 PC 모니터의 1/4이라 눈에는 더 작게 보인다.
방법: 게임 카메라와 같은 값(세로 FOV 35°, 내려다보는 각도 46/52/58°)으로 주인공 + 처결 대기 혼 둘 + 거센 혼을 찍고, 코드가 얹는 화면 고정 크기 요소(맺힘 막대 64/80px, 안내 아이콘 32px)를 같은 픽셀로 붙인다.
산출: assets3d/previews/zoom_check_{13,19,24}.png(PC 1920×1080 원본), zoom_check_sheet.png(비교판), assets3d/ui/_zoom_check.json(화면에서 차지하는 픽셀)
실행: python3 zoom_check.py"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
from PIL import Image, ImageDraw, ImageFont
from bpy_extras.object_utils import world_to_camera_view
A = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")
STEPS = [(13, 46), (19, 52), (24, 58)]       # (거리 m, 내려다보는 각도°)
W, H = 1920, 1080

def imp(rel, loc, yaw=0, scale=1.0):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=os.path.join(A, rel)); new = [o for o in bpy.data.objects if o not in before]
    roots = [o for o in new if o.parent is None]
    for o in roots: o.location = loc; o.rotation_euler[2] = math.radians(yaw); o.scale = (scale,) * 3
    return roots, new

def head_of(new, root_loc, dz):
    return Vector((root_loc[0], root_loc[1], dz))

def shot(dist, pitch):
    reset(); setup_render(10, (0, 0, 0.9), size=(W, H), ground_size=80); sc = bpy.context.scene; sc.cycles.samples = 20
    items = []
    imp("characters/hero_chasa.glb", (0, 0, 0), 0)
    for rel, loc, yaw, hz, nm in (("souls/soul_day.glb", (3.2, 3.5, 0), 200, 1.5, "soul"), ("souls/soul_fresh.glb", (-3.6, 4.6, 0), 160, 1.5, "soul"), ("souls/soul_elite_day.glb", (5.0, 7.0, 0), 190, 2.6, "elite")):
        imp(rel, loc, yaw)
        if nm == "soul": imp("fx/fx_wait_ring_day.glb", (loc[0], loc[1], 0.04), 0, 0.9 * 2 / 2.12)
        items.append({"kind": nm, "head": (loc[0], loc[1], hz), "foot": (loc[0], loc[1], 0)})
    imp("boss/boss_b03_seo.glb", (-6.2, 9.0, 0), 180); items.append({"kind": "boss", "head": (-6.2, 9.0, 2.3), "foot": (-6.2, 9.0, 0)})
    cam = sc.camera; cd = cam.data; cd.type = "PERSP"; cd.sensor_fit = "VERTICAL"; cd.angle = math.radians(35); p = math.radians(pitch)
    tgt = Vector((0, 0.6, 0.0)); cam.location = tgt + Vector((0, -math.cos(p) * dist, math.sin(p) * dist)); cam.rotation_euler = (math.radians(90 - pitch), 0, 0)
    sc.render.filepath = os.path.join(A, "previews", f"_zc_{dist}.png"); sc.render.resolution_x, sc.render.resolution_y = W, H; bpy.ops.render.render(write_still=True)
    out = []
    for it in items:
        h = world_to_camera_view(sc, cam, Vector(it["head"])); f = world_to_camera_view(sc, cam, Vector(it["foot"]))
        out.append({"kind": it["kind"], "head_px": (h.x * W, (1 - h.y) * H), "foot_px": (f.x * W, (1 - f.y) * H)})
    # 1m 당 픽셀(화면 가운데 땅 기준)과 주인공 몸 높이
    a = world_to_camera_view(sc, cam, Vector((-0.5, 0.6, 0))); b = world_to_camera_view(sc, cam, Vector((0.5, 0.6, 0))); ppm = abs(b.x - a.x) * W
    hero_h = world_to_camera_view(sc, cam, Vector((0, 0, 0))); hero_t = world_to_camera_view(sc, cam, Vector((0, 0, 1.8)))
    return out, ppm, abs(hero_t.y - hero_h.y) * H

def overlay(path, marks, k_bar=1.0, k_icon=1.0):
    """코드가 화면 고정 크기로 얹는 것: 맺힘 막대(일반 64px·이름 있는 80px) + 안내 아이콘 32px. L판(홈 14px) 기준으로 붙인다."""
    im = Image.open(path).convert("RGBA"); B = os.path.join(A, "ui", "bars_L"); U = os.path.join(A, "ui", "first10")
    frame = Image.open(os.path.join(B, "ui_bar_gyeol_frame_L.png")).convert("RGBA"); gold = Image.open(os.path.join(B, "ui_bar_gyeol_frame_gold_L.png")).convert("RGBA"); fill = Image.open(os.path.join(B, "ui_bar_gyeol_fill_L.png")).convert("RGBA")
    ic = Image.open(os.path.join(U, "prompt_tendo.png")).convert("RGBA")
    for m in marks:
        hx, hy = m["head_px"]; named = m["kind"] in ("boss", "elite"); k = (80 if named else 64) / 96 * k_bar
        fr = (gold if m["kind"] == "boss" else frame); fw, fh = int(96 * k), int(fr.height * k); im.alpha_composite(fr.resize((fw, fh), Image.LANCZOS), (int(hx - fw / 2), int(hy - 18 - fh / 2)))
        s = fill.resize((int(88 * k * 0.6), max(1, int(14 * k))), Image.LANCZOS); im.alpha_composite(s, (int(hx - fw / 2 + 4 * k), int(hy - 18 - fh / 2 + 4 * k)))
        if m["kind"] == "soul":
            s32 = int(32 * k_icon); im.alpha_composite(ic.resize((s32, s32), Image.LANCZOS), (int(hx - s32 / 2), int(hy - 18 - fh - s32 - 4)))
    im.convert("RGB").save(path)

if __name__ == "__main__":
    res = {}; sheet = []
    for dist, pitch in STEPS:
        marks, ppm, hero_px = shot(dist, pitch); p = os.path.join(A, "previews", f"_zc_{dist}.png"); overlay(p, marks)
        im = Image.open(p); im.save(os.path.join(A, "previews", f"zoom_check_{dist}.png")); os.remove(p); sheet.append((dist, im))
        res[str(dist)] = {"pitch": pitch, "px_per_m_center": round(ppm, 1), "hero_px_tall": round(hero_px, 1)}
        print(dist, res[str(dist)])
    json.dump(res, open(os.path.join(A, "ui", "_zoom_check.json"), "w"), ensure_ascii=False, indent=1)
    f = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttf" if os.path.exists("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttf") else "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 26)
    # 비교판: 위 = PC 화면 가운데 960×540 원본 크기, 아래 = 폰에서 보이는 크기 흉내(PC 모니터와 같은 거리에서 볼 때의 41%: 폰 픽셀 하나가 눈에 주는 각이 PC의 0.41배)
    cw, ch = 960, 540; S = Image.new("RGB", (cw * 3, ch + 450), (30, 30, 36)); d = ImageDraw.Draw(S)
    for i, (dist, im) in enumerate(sheet):
        S.paste(im.crop((480, 240, 1440, 780)), (i * cw, 0)); d.text((i * cw + 10, 6), f"줌 {dist} m — PC 원본 픽셀(가운데 960×540)", fill=(255, 240, 200), font=f)
        sm = im.resize((int(W * 0.41), int(H * 0.41)), Image.LANCZOS); S.paste(sm, (i * cw + (cw - sm.width) // 2, ch + 4)); d.text((i * cw + 10, ch + 4), f"폰에서 보이는 크기(전체 화면 ×0.41)", fill=(200, 230, 255), font=f)
    S.save(os.path.join(A, "previews", "zoom_check_sheet.png"))
