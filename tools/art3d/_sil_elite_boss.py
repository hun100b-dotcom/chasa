"""거센 혼(정예)·1막 보스가 50° 카메라에서 일반 혼과 '그림자(실루엣)'만으로 구분되는지 잰다.
왜: 쿼터뷰에서는 색보다 키·어깨폭·머리 위 모양이 먼저 보인다. 정예를 보고 "저건 일반 혼이 아니다"를 0.5초 안에 알아야 하고,
 보스는 정예·일반 혼과 헷갈려선 안 된다. 모델마다 같은 카메라로 까맣게 찍어 키·폭·넓이·'일반 혼과 겹치는 비율(IoU)'을 잰다.
 IoU(겹침 비율) = 두 그림자가 겹친 넓이 ÷ 합친 넓이. 1에 가까우면 같은 모양, 0.5 아래면 다른 모양이다.
 키·폭 차이가 큰 건 IoU가 작아 당연히 달라 보이므로, '같은 키로 맞춰 놓고' 겹침(IoU_n)도 함께 재서 모양 자체의 차이를 본다.
실행: python3 _sil_elite_boss.py  → previews/sil_elite_boss.png, souls/_sil_elite_boss.json"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image, ImageDraw
from lib3d import *
from npc_silhouette import black_everything
A = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")

# (이름, 파일, 그림 속 표시 이름)
MODELS = [("basic", "souls/soul_day.glb", "일반 혼(해 넘긴)"), ("elite", "souls/soul_elite_day.glb", "거센 혼"),
          ("b01", "boss/boss_naru.glb", "B-01 나루 영감"), ("b02", "boss/boss_b02_wolhwa.glb", "B-02 월화"), ("b03", "boss/boss_b03_seo.glb", "B-03 서 의원"),
          ("b04", "boss/boss_b04_heugwol.glb", "B-04 흑월"), ("b05", "boss/boss_b05_daedol2.glb", "B-05 대돌"), ("b06", "boss/boss_b06_jangsu.glb", "B-06 장수")]
SCALE = 8.0          # 카메라가 담는 세로폭(m) — 게임 화면에서 키 1.4m 혼이 약 100px이 되는 크기와 같은 비율로 모두 동일하게
PX = 400              # 한 장 크기(정사각)

def drop_ground_discs():
    """바닥에 깔린 안개·물 원판(z 0.08 미만에 납작하게 깔린 큰 면)은 몸이 아니라 바닥 효과이므로 그림자에서 뺀다(B-01은 이 원판이 반경 3m라 몸이 가려졌었다)."""
    import bmesh
    for o in [o for o in bpy.context.scene.objects if o.type == "MESH"]:
        bm = bmesh.new(); bm.from_mesh(o.data); mw = o.matrix_world
        bad = [f for f in bm.faces if max((mw @ v.co).z for v in f.verts) < 0.08 and f.calc_area() > 0.4]
        bmesh.ops.delete(bm, geom=bad, context="FACES"); bm.to_mesh(o.data); bm.free()

def shot(rel, yaw=0):
    reset()
    bpy.ops.import_scene.gltf(filepath=os.path.join(A, rel))
    for o in bpy.context.scene.objects:
        if o.parent is None and o.type != "MESH" and o.type != "CAMERA": o.rotation_euler[2] = math.radians(yaw)
        elif o.parent is None: o.rotation_euler[2] = math.radians(yaw)
    drop_ground_discs()
    setup_render(SCALE, (0, 0, 1.6), size=(PX, PX), ground_size=40); black_everything()
    bpy.context.scene.cycles.samples = 4
    p = os.path.join(A, "previews", "_sil.png"); bpy.context.scene.render.filepath = p; bpy.ops.render.render(write_still=True)
    return np.asarray(Image.open(p).convert("L"), np.float32) < 128

def box_of(m):
    ys, xs = np.where(m)
    return (xs.min(), ys.min(), xs.max(), ys.max()) if len(xs) else (0, 0, 0, 0)

def normalized(m, h=340):
    """키(세로)를 h로 맞추고 가로는 가운데 정렬 — 크기 차이를 지우고 모양만 비교"""
    x0, y0, x1, y1 = box_of(m); c = Image.fromarray((m[y0:y1 + 1, x0:x1 + 1] * 255).astype(np.uint8))
    w = max(1, int(c.width * h / c.height)); c = c.resize((w, h)); out = Image.new("L", (PX, PX), 0); out.paste(c, ((PX - w) // 2, (PX - h) // 2)); return np.asarray(out) > 127

def iou(a, b): return float(np.logical_and(a, b).sum() / max(1, np.logical_or(a, b).sum()))

def run():
    res = {}; masks = {}
    for k, rel, nm in MODELS:
        m = shot(rel); masks[k] = m; x0, y0, x1, y1 = box_of(m); ppm = PX / SCALE   # 1m당 픽셀(대략, 세로는 50°라 cos 보정 안 함 — 모델 사이 비교용)
        res[k] = {"name": nm, "h_px": int(y1 - y0 + 1), "w_px": int(x1 - x0 + 1), "area": int(m.sum())}
    for k in masks:
        if k == "basic": continue
        res[k]["iou_basic"] = round(iou(masks[k], masks["basic"]), 3)                       # 같은 자리 겹침(발 위치 기준이 아님 — 가운데 정렬 상태)
        res[k]["iou_basic_norm"] = round(iou(normalized(masks[k]), normalized(masks["basic"])), 3)   # 키를 맞춘 모양 비교
        if k != "elite":
            res[k]["iou_elite_norm"] = round(iou(normalized(masks[k]), normalized(masks["elite"])), 3)
            res[k]["h_vs_elite"] = round(res[k]["h_px"] / res["elite"]["h_px"], 2)
        res[k]["h_vs_basic"] = round(res[k]["h_px"] / res["basic"]["h_px"], 2); res[k]["area_vs_basic"] = round(res[k]["area"] / res["basic"]["area"], 2)
    # 비교 그림: 윗줄 = 실제 비율 그대로(같은 카메라), 아랫줄 = 키를 맞춰 모양만 비교
    from PIL import ImageFont
    f = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 18)
    W = Image.new("RGB", (PX * len(MODELS), PX * 2 + 60), (237, 235, 224)); d = ImageDraw.Draw(W)
    for i, (k, rel, nm) in enumerate(MODELS):
        im = Image.fromarray(np.where(masks[k], 20, 237).astype(np.uint8)).convert("RGB"); W.paste(im, (i * PX, 30))
        nm_im = Image.fromarray(np.where(normalized(masks[k]), 20, 237).astype(np.uint8)).convert("RGB"); W.paste(nm_im, (i * PX, PX + 60))
        d.text((i * PX + 8, 4), nm, fill=(40, 40, 40), font=f)
    d.text((8, PX + 34), "아랫줄: 키를 같게 맞춘 모양", fill=(90, 40, 40), font=f)
    W.save(os.path.join(A, "previews", "sil_elite_boss.png"))
    json.dump(res, open(os.path.join(A, "souls", "_sil_elite_boss.json"), "w"), ensure_ascii=False, indent=1)
    try: os.remove(os.path.join(A, "previews", "_sil.png"))
    except OSError: pass
    return res

if __name__ == "__main__":
    for k, v in run().items(): print(k, v)
