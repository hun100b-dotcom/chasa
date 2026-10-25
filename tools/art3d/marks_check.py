"""무기 표식 3종이 24 m 폰 크기에서 읽히는지, 처결 대기 고리와 헷갈리지 않는지 같은 카메라로 점검한다(zoom_check.py와 같은 값).
배치: 처결 대기 중인 혼(고리 있음)과 표식 붙은 혼을 나란히 → 표식 없는 대기 혼 / 고정 / 둔화 / 붓 표식 1·3개 / 표식 + 대기 고리가 한 혼에 같이 있는 경우.
산출: assets3d/previews/marks_check_sheet.png (위: PC 원본 가운데, 아래: 폰에서 보이는 크기 ×0.41)  실행: python3 marks_check.py"""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
from zoom_check import *

def shot_marks(dist, pitch):
    reset(); setup_render(10, (0, 0, 0.9), size=(W, H), ground_size=80); sc = bpy.context.scene; sc.cycles.samples = 20
    imp("characters/hero_chasa.glb", (0, -1.5, 0), 0)
    row = [("souls/soul_day.glb", None, True, -6.0), ("souls/soul_day.glb", "fx_mark_pin", False, -3.0), ("souls/soul_fresh.glb", "fx_mark_slow", False, 0.0), ("souls/soul_day.glb", "fx_mark_ink_1", False, 3.0),
           ("souls/soul_old.glb", "fx_mark_ink_3", False, 6.0), ("souls/soul_day.glb", "fx_mark_pin", True, 9.0)]
    for rel, mk, ring, x in row:
        imp(rel, (x, 4.0, 0), 190)
        if ring: imp("fx/fx_wait_ring_day.glb", (x, 4.0, 0.04), 0, 0.9 * 2 / 2.12)
        if mk: imp(f"fx/{mk}.glb", (x, 4.0, 0), 0)
    cam = sc.camera; cd = cam.data; cd.type = "PERSP"; cd.sensor_fit = "VERTICAL"; cd.angle = math.radians(35); p = math.radians(pitch)
    tgt = Vector((1.5, 3.2, 0.0)); cam.location = tgt + Vector((0, -math.cos(p) * dist, math.sin(p) * dist)); cam.rotation_euler = (math.radians(90 - pitch), 0, 0)
    pth = os.path.join(A, "previews", f"_mk_{dist}.png"); sc.render.filepath = pth; sc.render.resolution_x, sc.render.resolution_y = W, H; bpy.ops.render.render(write_still=True); return pth

if __name__ == "__main__":
    f = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 24); ims = []
    for dist, pitch in ((19, 52), (24, 58)):
        p = shot_marks(dist, pitch); im = Image.open(p).convert("RGB"); os.remove(p); ims.append((dist, im))
    S = Image.new("RGB", (1920, 2 * 560 + 2 * 240), (30, 30, 36)); d = ImageDraw.Draw(S); y = 0
    for dist, im in ims:
        S.paste(im.crop((0, 300, 1920, 860)), (0, y)); d.text((10, y + 6), f"줌 {dist} m — PC 원본 픽셀", fill=(255, 240, 200), font=f); y += 560
        sm = im.resize((int(1920 * 0.41), int(1080 * 0.41)), Image.LANCZOS).crop((0, 125, int(1920 * 0.41), 125 + 240)); S.paste(sm, (0, y)); d.text((10, y + 4), f"줌 {dist} m — 폰에서 보이는 크기(×0.41)", fill=(200, 230, 255), font=f)
        big = im.crop((560, 380, 1360, 860)).resize((960 - 0, 288)) if False else None; y += 240
    S.save(os.path.join(A, "previews", "marks_check_sheet.png")); print("ok")
