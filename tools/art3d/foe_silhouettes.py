"""천도 캐스팅 중 시야 밖(먹 번짐 속) 혼의 실루엣 표시 그림.
왜: 시야 축소(반경 0.6)의 먹 알파가 0.94라 가장자리 혼이 6%밖에 안 보인다(vision_check). 붉은 호는 '방향'만 알려 주고 '무슨 혼인지'(일반·넋두리·잔넋·덩어리·거센 혼)는 모른다.
 → 먹 속에 있는 혼 자리에 '어두운 붉은 몸 + 밝은 붉은 윤곽선' 실루엣을 그려 주면 모양으로 알아본다(몸은 먹보다 밝고 윤곽은 위험 호와 같은 #E85C41).
방법: 실제 혼 모델을 게임 카메라(52°)로 까맣게 찍어 몸 모양을 따고, 안쪽을 어두운 붉은색, 가장자리 2px를 밝은 붉은색으로 칠한다. 모양이 모델에서 나오므로 모델이 바뀌어도 다시 뽑으면 맞는다.
규격: 192×192 투명 PNG, 모델 발밑 가운데가 그림 가운데 아래(원점 = 가로 가운데·세로 66%), 1 m = 40 px. 코드는 (화면 1 m당 픽셀 ÷ 40)배로 키워 혼 화면 위치에 그린다(19 m·1080p 기준 ×2.25, 13 m ×3.3, 24 m ×1.8).
산출: assets3d/ui/first10/foe_{basic,wail,mote,buried,lump,elite}.png (+ unity Sprites/first10/), 실행: python3 foe_silhouettes.py"""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
from npc_silhouette import black_everything
import numpy as np
from PIL import Image, ImageFilter
A = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d"); UNITY = os.path.join(A, "..", "unity", "Assets", "Resources", "Sprites", "first10")
PX = 192; ORTHO = 4.8       # 1 m = 40 px
FOES = [("basic", "souls/soul_day.glb"), ("wail", "souls/soul_wail_day.glb"), ("mote", "souls/soul_mote_day.glb"), ("buried", "souls/soul_buried_day.glb"), ("lump", "souls/soul_lump.glb"), ("elite", "souls/soul_elite_day.glb")]
FILL = (58, 22, 26, 235); RIM = (232, 92, 65, 255)     # 몸 어두운 붉은색 / 윤곽 #E85C41(위험 호와 같은 색)

def mask_of(rel):
    reset(); bpy.ops.import_scene.gltf(filepath=os.path.join(A, rel))
    drop = [o for o in bpy.context.scene.objects if o.type == "MESH" and max((o.matrix_world @ Vector(c)).z for c in o.bound_box) < 0.06 and "ring" in o.name.lower()]
    setup_render(ORTHO, (0, 0, 0.9), size=(PX, PX), ground_size=40); black_everything(); bpy.context.scene.cycles.samples = 8
    # 발밑이 그림 세로 66% 자리에 오게 카메라 중심을 몸 높이 쪽으로 옮겼다(0.9 m, 쿼터뷰에서 발은 중심보다 아래로 그려짐)
    p = os.path.join(A, "previews", "_foe.png"); bpy.context.scene.render.filepath = p; bpy.ops.render.render(write_still=True)
    m = np.asarray(Image.open(p).convert("L"), np.float32) < 128; os.remove(p); return m

def icon(m):
    mk = Image.fromarray((m * 255).astype(np.uint8)); big = mk.resize((PX * 2, PX * 2), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.2)).point(lambda v: 255 if v > 110 else 0)
    er = big.filter(ImageFilter.MinFilter(9)); body = np.asarray(er) > 0; full = np.asarray(big) > 0; rim = full & ~body
    out = np.zeros((PX * 2, PX * 2, 4), np.uint8); out[full] = FILL; out[rim] = RIM
    return Image.fromarray(out, "RGBA").resize((PX, PX), Image.LANCZOS)

if __name__ == "__main__":
    rep = {}
    for k, rel in FOES:
        m = mask_of(rel); im = icon(m); ys, xs = np.where(m); h = float(ys.max() - ys.min() + 1) / 40; w = float(xs.max() - xs.min() + 1) / 40
        im.save(os.path.join(A, "ui", "first10", f"foe_{k}.png"), optimize=True)
        if os.path.isdir(UNITY): im.save(os.path.join(UNITY, f"foe_{k}.png"), optimize=True)
        rep[k] = {"file": f"foe_{k}.png", "size_px": [PX, PX], "px_per_m": 40, "body_m": [round(w, 2), round(h, 2)], "body_bbox_px": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]}; print(k, rep[k]["body_m"])
    json.dump(rep, open(os.path.join(A, "ui", "first10", "_foe_silhouettes.json"), "w"), ensure_ascii=False, indent=1)
