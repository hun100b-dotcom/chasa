"""업 칸 0·10·30·60 주인공 겉모습 비교(줌 13 m·24 m, 폰 크기 ×0.41). 산출: assets3d/previews/hero_karma_check.png, assets3d/characters/_hero_karma_check.json
측정: 같은 자리에서 업 0 대비 '바뀐 픽셀' 비율(주인공 둘레 4×4 m 안)과 키·폭 변화."""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
from zoom_check import imp, A
import numpy as np
from PIL import Image, ImageDraw, ImageFont
W, H = 1920, 1080
def shot(tier, dist, pitch):
    reset(); setup_render(10, (0, 0, 0.9), size=(W, H), ground_size=80); sc = bpy.context.scene; sc.cycles.samples = 24
    imp("characters/hero_chasa.glb", (0, 0, 0), 0)
    if tier:
        imp(f"characters/hero_karma_floor_{tier}.glb", (0, 0, 0.0), 0); imp(f"characters/hero_karma_body_{tier}.glb", (0, 0, 0), 0); imp(f"characters/hero_karma_head_{tier}.glb", (0, 0, 1.6), 0)
    cam = sc.camera; cd = cam.data; cd.type = "PERSP"; cd.sensor_fit = "VERTICAL"; cd.angle = math.radians(35); p = math.radians(pitch)
    tgt = Vector((0, 0.3, 0.8 if dist < 16 else 0.4)); cam.location = tgt + Vector((0, -math.cos(p) * dist, math.sin(p) * dist)); cam.rotation_euler = (math.radians(90 - p * 180 / math.pi), 0, 0)
    pth = os.path.join(A, "previews", "_hk.png"); sc.render.filepath = pth; sc.render.resolution_x, sc.render.resolution_y = W, H; bpy.ops.render.render(write_still=True)
    im = Image.open(pth).convert("RGB"); os.remove(pth); return im
if __name__ == "__main__":
    f = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 22); res = {}; rows = []
    for dist, pitch in ((24, 58), (13, 46)):
        base = None; row = []
        for tier in (0, 10, 30, 60):
            im = shot(tier, dist, pitch); a = np.asarray(im).astype(np.float32)
            if tier == 0: base = a
            cx, cy = W // 2, H // 2; reg = (slice(cy - 260, cy + 260), slice(cx - 260, cx + 260)); diff = (np.abs(a[reg] - base[reg]).sum(-1) > 40).mean()
            res[f"{dist}m_업{tier}"] = {"changed_px_ratio_in_520box": round(float(diff), 3)}
            row.append((tier, im.crop((cx - 260, cy - 260 - (60 if dist > 16 else 0), cx + 260, cy + 260 - (60 if dist > 16 else 0)))))
        rows.append((dist, row))
    S = Image.new("RGB", (4 * 520, 520 * 2 + 200), (30, 30, 36)); d = ImageDraw.Draw(S)
    for ri, (dist, row) in enumerate(rows):
        for ci, (tier, im) in enumerate(row):
            S.paste(im, (ci * 520, ri * 520)); d.text((ci * 520 + 8, ri * 520 + 6), f"줌 {dist} m · 업 {tier}", fill=(255, 240, 200), font=f)
            if dist == 24:
                ph = im.resize((int(520 * 0.41), int(520 * 0.41)), Image.LANCZOS); S.paste(ph, (ci * 520 + 150, 1040 + 8)); 
    d.text((8, 1040), "아래줄: 줌 24 m 폰에서 보이는 크기(×0.41)", fill=(200, 230, 255), font=f)
    S.save(os.path.join(A, "previews", "hero_karma_check.png")); json.dump(res, open(os.path.join(A, "characters", "_hero_karma_check.json"), "w"), ensure_ascii=False, indent=1); print(res)
